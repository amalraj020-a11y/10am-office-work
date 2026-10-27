"""Run one bounded EC2 OpenClaw office turn and verify its claimed result.

Private model output and delivery receipts stay under ~/.local/share/amala-office.
The daily start marker prevents an uncertain send from being repeated by a retry.
"""
import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from zoneinfo import ZoneInfo

from step_runner import verify_completion

ROOT = Path(__file__).resolve().parents[1]
STATE = Path.home() / '.local/share/amala-office'
MODEL = ('openai', 'gpt-6-astra')


def find_objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from find_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from find_objects(child)


def final_text(payload):
    for item in find_objects(payload):
        reply = item.get('terminalReply')
        if isinstance(reply, dict) and isinstance(reply.get('text'), str):
            return reply['text']
    raise ValueError('OpenClaw returned no final assistant reply')


def parse_report(text):
    candidate = text.strip()
    if candidate.startswith('```'):
        candidate = '\n'.join(candidate.splitlines()[1:-1]).strip()
    report = json.loads(candidate)
    if not isinstance(report, dict) or report.get('status') not in ('complete', 'blocked'):
        raise ValueError('Office agent returned no valid completion status')
    if not isinstance(report.get('reason'), str) or not report['reason'].strip():
        raise ValueError('Office agent returned no reason')
    return report


def send_owner_report(run_dir, status, reason):
    config = json.loads((STATE / 'step-runner.json').read_text())
    message = ('Amala 10 AM EC2 run: ' + status + '.\n' + reason[:900] +
               '\nCompletion requires a live site and verified send receipts.')
    args = ['openclaw', 'message', 'send', '--channel', 'whatsapp', '--account',
            'amala', '--target', config['owner'], '--message', message, '--json']
    try:
        sent = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                              timeout=45, check=False)
        receipt = {'exit_code': sent.returncode, 'stdout': sent.stdout[-5000:],
                   'stderr': sent.stderr[-1500:]}
    except Exception as exc:
        receipt = {'status': 'unknown', 'error': str(exc)[:500],
                   'note': 'Do not resend without reconciling delivery'}
    (run_dir / 'owner-report.json').write_text(json.dumps(receipt, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manual', action='store_true',
                        help='Create a distinct, one-time test run outside the daily timer')
    args = parser.parse_args()
    os.umask(0o077)
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'office.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('{"status":"already_running"}', flush=True)
            return 1
        day = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d')
        name = day + ('-manual-' + str(int(time.time())) if args.manual else '')
        run_dir = STATE / 'runs' / name
        run_dir.mkdir(parents=True, exist_ok=True)
        marker = run_dir / 'started.json'
        try:
            with marker.open('x') as stream:
                json.dump({'started_at': time.time(), 'model': '/'.join(MODEL)}, stream)
        except FileExistsError:
            print('{"status":"already_attempted"}', flush=True)
            return 1

        command = ['openclaw', 'agent', '--agent', 'amala-office', '--message-file',
                   str(ROOT / 'cloud/office-task.md'), '--thinking', 'low',
                   '--timeout', '3300', '--json']
        status, reason = 'incomplete', 'Agent turn ended without verified completion.'
        try:
            process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True,
                                       start_new_session=True)
            try:
                stdout, stderr = process.communicate(timeout=3350)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    stdout, stderr = process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, stderr = process.communicate()
                (run_dir / 'agent-output.json').write_text(stdout)
                (run_dir / 'agent-stderr.txt').write_text(stderr[-10000:])
                raise RuntimeError('Office deadline reached; effects require reconciliation')
            (run_dir / 'agent-output.json').write_text(stdout)
            (run_dir / 'agent-stderr.txt').write_text(stderr[-10000:])
            if process.returncode:
                raise RuntimeError('OpenClaw agent exit code ' + str(process.returncode))
            payload = json.loads(stdout)
            used_expected = any(item.get('provider') == MODEL[0] and
                                item.get('model') == MODEL[1]
                                for item in find_objects(payload))
            if not used_expected:
                raise RuntimeError('Unexpected model route; no completion claimed')
            report = parse_report(final_text(payload))
            if report['status'] == 'complete':
                slug = report.get('slug', '')
                if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
                    raise ValueError('Agent completed without a valid business slug')
                url = verify_completion(slug)
                status = 'complete'
                reason = report['reason'][:700] + '\nVerified: ' + url
            else:
                status, reason = 'blocked', report['reason'][:1000]
        except Exception as exc:
            reason = (type(exc).__name__ + ': ' + str(exc))[:1000]
        summary = {'status': status, 'reason': reason, 'finished_at': time.time(),
                   'model': '/'.join(MODEL)}
        (run_dir / 'result.json').write_text(json.dumps(summary, indent=2))
        send_owner_report(run_dir, status, reason)
        print(json.dumps(summary), flush=True)
        return 0 if status == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
