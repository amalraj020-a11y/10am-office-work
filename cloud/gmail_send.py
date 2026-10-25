"""Send an approved outreach email from the EC2 Gmail send-only account.

The OAuth token and keyring password live outside this repository on EC2.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--to', required=True)
    parser.add_argument('--subject', required=True)
    parser.add_argument('--body-file', type=Path, required=True)
    parser.add_argument('--attach', type=Path, action='append', default=[])
    args = parser.parse_args()

    secret = Path('/home/ubuntu/.config/amala-office/keyring.pass')
    if not secret.is_file():
        raise SystemExit('EC2 Gmail keyring is not configured')
    if not args.body_file.is_file() or any(not image.is_file() for image in args.attach):
        raise SystemExit('Email body or attachment is missing')

    env = os.environ.copy()
    env['GOG_KEYRING_PASSWORD'] = secret.read_text().strip()
    command = ['/home/ubuntu/.local/bin/gog', 'gmail', 'send',
               '--account', 'amalaraj020@gmail.com', '--to', args.to,
               '--subject', args.subject, '--body-file', str(args.body_file),
               '--json']
    for image in args.attach:
        command += ['--attach', str(image)]
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise SystemExit(result.stderr.strip() or 'Gmail send failed')
    receipt = json.loads(result.stdout)
    if not receipt.get('messageId'):
        raise SystemExit('Gmail returned no message ID; check account before retrying')
    print(json.dumps({'status': 'accepted', 'message_id': receipt['messageId'],
                      'from': receipt.get('from')}))


if __name__ == '__main__':
    main()
