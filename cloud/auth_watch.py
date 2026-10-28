"""Check the EC2 office model sign-in and alert Raj through linked WhatsApp.

The routine status check uses no model tokens. A tiny live model call is made
only when the stored OAuth status is bad or close to expiry, so a refreshable
access token does not cause a false sign-in alarm. No credentials are logged.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STATE = Path.home() / '.local/share/amala-office'
STATUS_ARGS = ['openclaw', 'models', 'status', '--agent', 'amala-office', '--json']


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def read_oauth_status():
    env = os.environ.copy()
    # These unused providers have unresolved placeholders in the shared config.
    # Supplying inert values for this read-only command leaves the office route
    # unchanged and avoids OpenClaw failing before it reports OpenAI OAuth.
    env.setdefault('GROQ_API_KEY', 'unused-auth-status-check')
    env.setdefault('GEMINI_API_KEY', 'unused-auth-status-check')
    result = subprocess.run(STATUS_ARGS, cwd=ROOT, env=env, text=True,
                            capture_output=True, timeout=35, check=False)
    payload = json.loads(result.stdout)
    if result.returncode or payload.get('ok') is False:
        raise RuntimeError('OpenClaw could not read the office OAuth status')
    profiles = payload.get('auth', {}).get('oauth', {}).get('profiles', [])
    matches = [profile for profile in profiles
               if isinstance(profile, dict) and profile.get('provider') == 'openai']
    if len(matches) != 1:
        return False, 'The office OpenAI sign-in profile is missing or ambiguous.'
    profile = matches[0]
    expiry = profile.get('expiresAt')
    expiry_near = isinstance(expiry, (int, float)) and expiry <= (time.time() + 3600) * 1000
    if profile.get('status') == 'ok' and not expiry_near:
        return True, 'OpenAI sign-in is active.'
    return False, 'The office OpenAI sign-in is expired, expiring, or unavailable.'


def live_refresh_check():
    session = 'agent:amala-office:auth-watch-' + str(int(time.time()))
    result = subprocess.run([
        'openclaw', 'agent', '--agent', 'amala-office', '--session-key', session,
        '--message', 'Reply exactly AUTH_OK. Do not use tools or take any other action.',
        '--thinking', 'low', '--timeout', '60', '--json'],
        cwd=ROOT, capture_output=True, text=True, timeout=75, check=False)
    if result.returncode:
        return False
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    route = any(item.get('provider') == 'openai' and item.get('model') == 'gpt-6-astra'
                for item in objects(payload))
    reply = any(isinstance(item.get('terminalReply'), dict) and
                item['terminalReply'].get('text', '').strip() == 'AUTH_OK'
                for item in objects(payload))
    return route and reply


def check():
    try:
        good, reason = read_oauth_status()
    except Exception:
        return False, 'Amala could not check her ChatGPT sign-in on EC2.'
    if good:
        return True, reason
    try:
        if live_refresh_check():
            return True, 'OpenAI sign-in refreshed and a live model check passed.'
    except Exception:
        pass
    return False, reason + ' A live refresh check did not pass.'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-only', action='store_true',
                        help='Read current auth health without messaging')
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    good, reason = check()
    print(json.dumps({'healthy': good, 'reason': reason}), flush=True)
    if args.check_only:
        return 0 if good else 1
    day = datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat()
    path = STATE / 'auth-watch.json'
    previous = json.loads(path.read_text()) if path.exists() else {}
    if good:
        path.write_text(json.dumps({'healthy': True, 'checked_at': time.time(),
                                    'last_alert_day': previous.get('last_alert_day')}, indent=2))
        return 0
    if previous.get('last_alert_day') == day:
        return 1
    # Persist intent first. A timeout has unknown delivery; never resend today.
    state = {'healthy': False, 'checked_at': time.time(), 'reason': reason,
             'last_alert_day': day, 'alert': 'attempted; outcome unknown'}
    path.write_text(json.dumps(state, indent=2))
    try:
        config = json.loads((STATE / 'step-runner.json').read_text())
        message = ('Amala EC2 sign-in alert: ' + reason + '\nThe 10 AM website job may stop. '
                   'Please reconnect the ChatGPT/OpenClaw sign-in on EC2 when you can. '
                   'No business outreach was sent by this check.')
        sent = subprocess.run([
            'openclaw', 'message', 'send', '--channel', 'whatsapp', '--account',
            'amala', '--target', config['owner'], '--message', message, '--json'],
            cwd=ROOT, capture_output=True, text=True, timeout=45, check=False)
        state['alert'] = 'command accepted' if sent.returncode == 0 else 'send failed or unknown'
    except Exception:
        state['alert'] = 'send failed or unknown'
    path.write_text(json.dumps(state, indent=2))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
