#!/usr/bin/env bash
set -Eeuo pipefail

region='ap-southeast-2'
instance='i-013924c5d699ccf90'
availability_zone='ap-southeast-2c'
security_group='sg-0bd2887d1b7f0acc2'
host='13.210.183.252'
old_rule='sgr-0dc6787dd9fcf9cae'

key_dir="$(mktemp -d)"
key_file="$key_dir/key"
rule_id=''

cleanup() {
  rm -f "$key_file" "$key_file.pub"
  rmdir "$key_dir" 2>/dev/null || true
  if [[ -n "$rule_id" && "$rule_id" != 'None' ]]; then
    aws ec2 revoke-security-group-ingress \
      --region "$region" \
      --group-id "$security_group" \
      --security-group-rule-ids "$rule_id" >/dev/null 2>&1 || true
  fi
  if [[ "$old_rule" != "$rule_id" ]]; then
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
fi

ssh-keygen -t ed25519 -N '' -f "$key_file" -q
aws ec2-instance-connect send-ssh-public-key \
  --region "$region" \
  --instance-id "$instance" \
  --instance-os-user ubuntu \
  --availability-zone "$availability_zone" \
  --ssh-public-key "file://$key_file.pub" >/dev/null

ssh -i "$key_file" \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=accept-new \
  -o ConnectTimeout=15 \
  "ubuntu@$host" \
  'set -e
   cd /home/ubuntu/amala-office-repo
   git pull --ff-only origin main
   python3 -m py_compile cloud/auth_watch.py cloud/install_office_timer.py
   python3 cloud/install_office_timer.py --enable
   systemctl --user start amala-auth-watch.service || true
   systemctl --user is-enabled amala-office.timer amala-auth-watch.timer
   systemctl --user show amala-office.timer amala-auth-watch.timer -p Id -p ActiveState -p NextElapseUSecRealtime --no-pager
   test -f "$HOME/.local/share/amala-office/auth-watch.json" && cat "$HOME/.local/share/amala-office/auth-watch.json" || true'

echo 'EC2 setup finished. Temporary CloudShell SSH access will now be removed.'
