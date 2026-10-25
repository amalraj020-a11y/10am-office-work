"""Bounded OpenClaw/Qwen office steps; no direct model API or credential reads.

The OpenClaw daily command calls --launch and releases its scheduler slot.
This worker calls the disabled step job through the authenticated local gateway.
Each step gets a fresh isolated conversation and a compact persistent handoff.
"""
import argparse
import base64
from datetime import datetime
import fcntl
import json
import os
import shlex
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STATE = Path.home() / '.local/share/amala-office'
MODEL = 'qwen/qwen3.8-27b'


def cli(*args, timeout=240):
    proc = subprocess.run(['openclaw', *args], capture_output=True, text=True,
                          timeout=timeout, cwd=ROOT)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(proc.stderr[-1200:] or 'No structured CLI result')
    if proc.returncode and not result.get('completed'):
        error = result.get('error', {})
        raise RuntimeError(error.get('message', 'CLI failed') if isinstance(error, dict) else str(error))
    return result


def validate_step(result):
    run = result.get('run', {})
    if not result.get('completed'):
        raise RuntimeError('Step completion is unknown; do not redispatch it.')
    if run.get('provider') != 'groq' or run.get('model') != MODEL:
        raise RuntimeError('Unexpected model route; stopped.')
    if run.get('status') != 'ok':
        raise RuntimeError(run.get('error', 'Step failed; inspect recorded effects.'))
    return run


def parse_decision(summary):
    text = summary.strip()
    if text.startswith('```'):
        text = '\n'.join(text.splitlines()[1:-1])
    try:
        decision = json.loads(text)
    except json.JSONDecodeError:
        # Some Qwen responses put a short preamble before the requested object.
        # Accept only a complete, unambiguous JSON object; never execute a
        # partial command cut off by the provider's output limit.
        decoder = json.JSONDecoder()
        candidates = []
        for start, character in enumerate(text):
            if character != '{':
                continue
            try:
                value, end = decoder.raw_decode(text[start:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and {'status', 'command_b64'} <= value.keys():
                candidates.append(value)
        if len(candidates) != 1:
            raise ValueError('Qwen did not return one complete JSON decision')
        decision = candidates[0]
    if decision.get('status') not in {'continue', 'blocked', 'complete'}:
        raise ValueError('Model did not return a valid step status')
    encoded = decision.get('command_b64', '')
    if not isinstance(encoded, str):
        raise ValueError('Invalid encoded command')
    try:
        command = base64.b64decode(encoded, validate=True).decode('utf-8')
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError('Qwen returned an invalid base64 command') from exc
    if len(command) > 1200:
        raise ValueError('Invalid or oversized command')
    if decision['status'] == 'continue' and not command.strip():
        raise ValueError('Continuation has no command')
    decision['command'] = command
    return decision


def execution_script(command):
    # JSON serialization prevents generated shell text from becoming JS code.
    params = {'command': 'cd ' + shlex.quote(str(ROOT)) + ' && (\n' + command + '\n)',
              'timeoutSeconds': 90, 'title': 'Amala Qwen office action'}
    return 'const result = await exec(' + json.dumps(params) + ');\njson({notify:JSON.stringify(result)});\n'


def verify_completion(slug):
    """Require public deployed work and both actual provider send receipts."""
    import re
    if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Completion has no valid business slug')
    record = ROOT / 'work' / slug / 'run.json'
    data = json.loads(record.read_text())
    expected_url = f'https://amalraj020-a11y.github.io/10am-office-work/websites/{slug}/'
    if data.get('live_url') != expected_url:
        raise ValueError('Completion has no correct business-specific live URL')
    if not data.get('business_name') or not data.get('commit'):
        raise ValueError('Completion has no business identity or commit')
    images = data.get('screenshots', [])
    if len(images) != 2 or len(set(images)) != 2:
        raise ValueError('Completion requires two distinct screenshots')
    if any(not (ROOT / image).is_file() for image in images):
        raise ValueError('Completion references a missing screenshot')
    receipts = data.get('send_results', {})
    channels = data.get('contact_channels', [])
    if not isinstance(channels, list) or not channels or any(
            channel not in ('email', 'whatsapp') for channel in channels):
        raise ValueError('Completion has no validated contact channel')
    for channel in channels:
        receipt = receipts.get(channel, {})
        if receipt.get('status') not in ('accepted', 'sent', 'delivered') or not receipt.get('message_id'):
            raise ValueError(f'Completion has no verified {channel} send receipt')
    if subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True,
                      text=True, check=True).stdout.strip():
        raise ValueError('Completion records have unpushed local changes')
    with urlopen(Request(expected_url, headers={'User-Agent': 'AmalaOffice/1.0'}), timeout=25) as response:
        if response.status != 200:
            raise ValueError('Completed website is not live')
        html = response.read(3_000_000).decode('utf-8', errors='replace')
    if data['business_name'].casefold() not in html.casefold() or 'Developed by MultiMax' not in html:
        raise ValueError('Live website does not match the business and MultiMax')
    return expected_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--max-steps', type=int, default=30)
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    STATE.mkdir(parents=True, exist_ok=True)
    if args.launch:
        # The child must outlive the short scheduler command and the user's PC.
        with (STATE / 'worker.log').open('a') as log:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve())],
                             cwd=ROOT, stdout=log, stderr=log,
                             stdin=subprocess.DEVNULL, start_new_session=True)
        print('EC2 office worker started. This is not a completion report.')
        return
    with (STATE / 'worker.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Existing office worker owns this run; no duplicate started.')
            return
        config = json.loads((STATE / 'step-runner.json').read_text())
        day = datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat()
        run_dir = STATE / 'runs' / (day + ('-test-' + str(int(time.time())) if args.test else ''))
        run_dir.mkdir(parents=True, exist_ok=True)
        # A retry may have already sent something. Never silently start over.
        if (run_dir / 'started.json').exists():
            print('Today already attempted. Reconcile recorded outcomes before retrying.')
            return
        (run_dir / 'started.json').write_text(json.dumps({'started': time.time()}))
        deadline = time.monotonic() + 55 * 60
        historic = json.loads((ROOT / 'data/prospects.json').read_text())
        old_names = ', '.join(item['business_name'] for item in historic)
        handoff = ('HISTORICAL PROSPECTS; EXCLUDE every one: ' + old_names +
                   '. Prior run inspected the repo and template registry already. '
                   'Search the web for a genuinely NEW business without an official '
                   'site and verify a current public contact BEFORE choosing a template. '
                   'Use public HTTP listings and Python Playwright where needed; the '
                   'OpenClaw browser failed on this EC2 host. Research a new shop and '
                   'its public contact before any template work. No outreach yet.')
        rules = (ROOT / 'cloud/runtime-rules.md').read_text()
        instructions = (ROOT / 'cloud/office-step.md').read_text()
        total_tokens = 0
        outcome = 'incomplete'
        reason = 'Time or step budget reached; saved work requires continuation.'
        try:
            for index in range(args.max_steps):
                if time.monotonic() + 240 > deadline or total_tokens >= 160000:
                    break
                if args.test:
                    prompt = instructions + '\nRULES:\n' + rules + '\nTEST OVERRIDE:\n' + (
                        'Return status continue and command_b64 '
                        'cHJpbnRmIEFNQUxBX1NURVBfT0s=. '
                        'Do not propose messages or file changes.')
                else:
                    prompt = (instructions + '\nRULES:\n' + rules +
                              '\nLAST HANDOFF:\n' + handoff +
                              '\nReply now with one complete JSON object. No reasoning or preamble.')
                cli('cron', 'edit', config['decision_job'], '--message', prompt, '--disable')
                # Persist intent before dispatch. A timeout never triggers a resend.
                (run_dir / f'{index:02d}-intent.json').write_text(json.dumps({'time': time.time()}))
                result = cli('cron', 'run', config['decision_job'], '--wait',
                             '--wait-timeout', '4m', '--json', timeout=260)
                (run_dir / f'{index:02d}-result.json').write_text(json.dumps(result, indent=2))
                run = validate_step(result)
                total_tokens += run.get('usage', {}).get('total_tokens', 0)
                decision = parse_decision(run.get('summary', ''))
                (run_dir / f'{index:02d}-decision.json').write_text(json.dumps(decision, indent=2))
                if decision['status'] != 'continue':
                    if decision['status'] == 'complete':
                        url = verify_completion(decision.get('slug'))
                        outcome, reason = 'complete', 'Verified deployed site and available-channel sends: ' + url
                    else:
                        reason = 'Agent reports blocked: ' + str(decision.get('handoff', ''))
                    break
                script = run_dir / f'{index:02d}-action.js'
                script.write_text(execution_script(decision['command']))
                cli('cron', 'edit', config['step_job'], '--script', str(script),
                    '--script-tool-budget', '1', '--script-timeout-seconds', '120', '--disable')
                executed = cli('cron', 'run', config['step_job'], '--wait',
                               '--wait-timeout', '3m', '--json', timeout=200)
                (run_dir / f'{index:02d}-execution.json').write_text(json.dumps(executed, indent=2))
                if not executed.get('completed') or executed.get('run', {}).get('status') != 'ok':
                    raise RuntimeError('Action did not finish successfully; reconcile saved execution before retrying.')
                observation = json.loads(executed['run']['summary'])
                if observation.get('status') != 'completed':
                    raise RuntimeError('Action outcome is not final; do not repeat it.')
                handoff = json.dumps({'plan': decision.get('handoff', '')[:180],
                                      'exitCode': observation.get('exitCode'),
                                      'actual_output': observation.get('aggregated', '')[:650]})
                (run_dir / 'handoff.txt').write_text(handoff)
                if args.test:
                    if observation.get('exitCode') != 0 or observation.get('aggregated', '').strip() != 'AMALA_STEP_OK':
                        raise RuntimeError('Probe output did not match')
                    outcome, reason = 'probe_passed', 'Qwen decision and enforced single OpenClaw exec passed.'
                    break
                # Free quota is per minute; avoid immediately starting another step.
                time.sleep(65)
        except Exception as exc:
            reason = str(exc)[:2000]
        report = {'status': outcome, 'reason': reason, 'tokens': total_tokens,
                  'model': 'groq/' + MODEL, 'execution_version': 2, 'finished': time.time()}
        (run_dir / 'result.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report), flush=True)
        if args.test and outcome != 'probe_passed':
            raise SystemExit(1)
        if not args.test:
            message = ('Amala 10 AM EC2 run: ' + outcome + '.\n' + reason +
                       '\nNo completion is claimed without deployment and message evidence.')
            try:
                sent = cli('message', 'send', '--channel', 'whatsapp', '--account', 'amala',
                           '--target', config['owner'], '--message', message, '--json')
            except Exception as exc:
                sent = {'status': 'unknown', 'error': str(exc)[:1000],
                        'retry': 'Do not resend until delivery has been reconciled.'}
            (run_dir / 'owner-report.json').write_text(json.dumps(sent, indent=2))


if __name__ == '__main__':
    main()
