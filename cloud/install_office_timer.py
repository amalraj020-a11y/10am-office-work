"""Install the EC2 10 AM user timer, disabled until a complete rehearsal passes."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
UNITS = Path.home() / '.config/systemd/user'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--enable', action='store_true',
                        help='Enable only after one fully verified manual run')
    args = parser.parse_args()
    units = UNITS
    units.mkdir(parents=True, exist_ok=True)
    (units / 'amala-office.service').write_text(f'''[Unit]
Description=Amala daily website office through OpenClaw
After=openclaw-gateway.service
Requires=openclaw-gateway.service

[Service]
Type=exec
WorkingDirectory={ROOT}
Environment=PATH=/home/ubuntu/.npm-global/bin:/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 {ROOT}/cloud/run_office_agent.py
RuntimeMaxSec=58min
KillMode=control-group
Restart=no
UMask=0077
''')
    (units / 'amala-office.timer').write_text('''[Unit]
Description=Run Amala office at 10 AM India time

[Timer]
OnCalendar=*-*-* 10:00:00 Asia/Kolkata
AccuracySec=1s
Persistent=false
Unit=amala-office.service

[Install]
WantedBy=timers.target
''')
    (units / 'amala-auth-watch.service').write_text(f'''[Unit]
Description=Check Amala office model sign-in and alert Raj if needed
After=openclaw-gateway.service
Requires=openclaw-gateway.service

[Service]
Type=oneshot
WorkingDirectory={ROOT}
Environment=PATH=/home/ubuntu/.npm-global/bin:/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 {ROOT}/cloud/auth_watch.py
TimeoutStartSec=3min
UMask=0077
''')
    (units / 'amala-auth-watch.timer').write_text('''[Unit]
Description=Check Amala sign-in each hour

[Timer]
OnCalendar=hourly
AccuracySec=1min
Persistent=false
Unit=amala-auth-watch.service

[Install]
WantedBy=timers.target
''')
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
    subprocess.run(['systemd-analyze', 'calendar', '*-*-* 10:00:00 Asia/Kolkata'],
                   check=True, capture_output=True)
    if args.enable:
        subprocess.run(['systemctl', '--user', 'enable', '--now',
                        'amala-office.timer'], check=True)
        subprocess.run(['systemctl', '--user', 'enable', '--now',
                        'amala-auth-watch.timer'], check=True)
    print('Office timer installed; enabled=' + str(args.enable))


if __name__ == '__main__':
    main()
