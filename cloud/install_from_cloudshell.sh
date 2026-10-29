#!/usr/bin/env bash
set -Eeuo pipefail

region='ap-southeast-2'
instance='i-013924c5d699ccf90'
security_group='sg-0bd2887d1b7f0acc2'
old_rule='sgr-0dc6787dd9fcf9cae'
export AWS_PAGER=''

instance_details="$(aws ec2 describe-instances \
  --region "$region" --instance-ids "$instance" \
  --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress,Placement.AvailabilityZone]' \
  --output text)"
read -r instance_state host availability_zone <<< "$instance_details"
if [[ "$instance_state" != 'running' || -z "$host" || "$host" == 'None' ]]; then
  echo 'EC2 must be running with a public IPv4 address. No changes made.' >&2
  exit 1
fi
echo "Connecting from CloudShell to EC2 $instance ($host)."

key_dir="$(mktemp -d)"
key_file="$key_dir/key"
rule_id=''
created_rule=''

cleanup() {
  rm -f "$key_file" "$key_file.pub"
  rmdir "$key_dir" 2>/dev/null || true
  if [[ -n "$created_rule" && "$created_rule" != 'None' ]]; then
    aws ec2 revoke-security-group-ingress \
      --region "$region" \
      --group-id "$security_group" \
      --security-group-rule-ids "$created_rule" >/dev/null || echo "WARNING: Remove temporary SSH rule $created_rule manually." >&2
  fi
  if [[ "$old_rule" != "$created_rule" ]]; then
    aws ec2 revoke-security-group-ingress \
      --region "$region" \
      --group-id "$security_group" \
      --security-group-rule-ids "$old_rule" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

cloudshell_ip="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')"
cidr="$cloudshell_ip/32"
export AMALA_TARGET_CIDR="$cidr"

rule_id="$(aws ec2 describe-security-group-rules \
  --region "$region" \
  --filters "Name=group-id,Values=$security_group" \
  --output json | python3 -c '
import json, os, sys
cidr = os.environ["AMALA_TARGET_CIDR"]
rules = json.load(sys.stdin).get("SecurityGroupRules", [])
matches = [r.get("SecurityGroupRuleId", "") for r in rules
           if not r.get("IsEgress") and r.get("IpProtocol") == "tcp"
           and r.get("FromPort") == 22 and r.get("ToPort") == 22
           and r.get("CidrIpv4") == cidr]
print(matches[0] if matches else "")
')"

if [[ -z "$rule_id" ]]; then
  rule_id="$(aws ec2 authorize-security-group-ingress \
    --region "$region" \
    --group-id "$security_group" \
    --protocol tcp \
    --port 22 \
    --cidr "$cidr" \
    --query 'SecurityGroupRules[0].SecurityGroupRuleId' \
    --output text)"
  created_rule="$rule_id"
fi

ssh-keygen -t ed25519 -N '' -f "$key_file" -q
aws ec2-instance-connect send-ssh-public-key \
  --region "$region" \
  --instance-id "$instance" \
  --instance-os-user ubuntu \
  --availability-zone "$availability_zone" \
  --ssh-public-key "file://$key_file.pub" >/dev/null

ssh -n -i "$key_file" \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=accept-new \
  -o ConnectTimeout=15 \
  "ubuntu@$host" \
  'set -e
   export XDG_RUNTIME_DIR="/run/user/$(id -u)"
   export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
   if [ ! -S "$XDG_RUNTIME_DIR/bus" ]; then
     echo "EC2 user service manager is unavailable; timer setup stopped." >&2
     exit 1
   fi
   echo "Checking timers on EC2: $(hostname) as $(whoami)"
   cd /home/ubuntu/amala-office-repo
   git pull --ff-only origin main
   python3 -m py_compile cloud/auth_watch.py cloud/install_office_timer.py
   python3 cloud/install_office_timer.py --enable
   systemctl --user start amala-auth-watch.service
   systemctl --user is-enabled amala-office.timer amala-auth-watch.timer
   systemctl --user is-active amala-office.timer amala-auth-watch.timer
   systemctl --user show amala-office.timer amala-auth-watch.timer -p Id -p ActiveState -p NextElapseUSecRealtime --no-pager
   test -f "$HOME/.local/share/amala-office/auth-watch.json" && cat "$HOME/.local/share/amala-office/auth-watch.json" || true'

echo 'EC2 timers verified. Cleaning up temporary SSH access.'
