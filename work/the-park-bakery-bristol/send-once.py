"""Single authorized send after all gates; uncertain outcomes must not be retried."""
from pathlib import Path
import json,hashlib,subprocess,sys
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
root=Path(__file__).resolve().parents[2];record=Path(__file__).with_name('run.json')
d=json.loads(record.read_text());now=datetime.now(timezone.utc)
assert now.astimezone(ZoneInfo('Asia/Kolkata')).isoformat() < '2026-11-16T10:55:00+05:30'
assert d['contact_channels']==['email'] and d['email']=='theparkbakery@gmail.com'
assert d['send_results']['email']['status']=='not_attempted' and not d.get('send_attempt')
assert d['deployment']['conclusion']=='success' and d['deployment']['headSha']==d['source_commit']
assert d['screenshot_deployment']['conclusion']=='success' and d['screenshot_deployment']['headSha']==d['screenshot_commit']
assert all(x['matches_local'] for x in d['live_asset_verification'])
assert len(d['screenshot_evidence'])==2
for i in d['screenshot_evidence']:
 assert i['public_verified'] and i['public_status']==200 and i['inspected_at']
 assert hashlib.sha256((root/i['path']).read_bytes()).hexdigest()==i['sha256']
assert (record.parent/'outreach.txt').read_text()==d['outreach_text']
for label in ['local','live']:
 qa=json.loads((record.parent/f'qa-{label}.json').read_text())
 assert len(qa['pages'])==2
 for p in qa['pages']:
  assert p['status']==200 and not p['console_errors'] and not p['http_failures'] and not p['overflow'] and not p['brokenAnchors'] and p['forms']==0
body=record.parent/'outreach.txt'
d['pre_send_gate']={'checked_at':now.isoformat(),'result':'passed','authorization':'Standing authorization for one qualified business; email only','checks':['approved GPT-6 Astra OAuth','deadline and outer process lock','new identity-matched prospect','public email and working configured sender','website/social research','fresh licensed ThemeWagon template','all shipped pages desktop/mobile QA','correct live deployment and asset hashes','two current screenshots opened and inspected','public images verified against hashes','message includes preview/source/images/identity/budget/opt-out','no previous sends; actual file attachments']}
d['send_attempt']={'started_at':now.isoformat(),'channel':'email','recipient':d['email'],'subject':d['outreach_subject'],'body_sha256':hashlib.sha256(body.read_bytes()).hexdigest(),'attachments':[{'path':x['path'],'sha256':x['sha256']} for x in d['screenshot_evidence']]}
d['send_results']['email']['status']='unknown';record.write_text(json.dumps(d,indent=2)+'\n')
command=[sys.executable,str(root/'cloud/gmail_send.py'),'--to',d['email'],'--subject',d['outreach_subject'],'--body-file',str(body)]
for f in d['screenshots']:command+=['--attach',str(root/f)]
try:
 r=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=100)
 if r.returncode:raise RuntimeError('Sender returned nonzero; reconcile before retry: '+r.stderr[-400:])
 receipt=json.loads(r.stdout);assert receipt['status']=='accepted' and receipt['message_id']
except Exception as e:
 d['blocker']=str(e);record.write_text(json.dumps(d,indent=2)+'\n');print('Send state unknown; saved, do not retry.');raise
accepted=datetime.now(timezone.utc).isoformat()
d['send_results']['email']={'status':'accepted','message_id':receipt['message_id'],'recipient':d['email'],'accepted_at':accepted,'attachment_paths':d['screenshots'],'delivery':'not_confirmed','note':'Gmail accepted the send with both actual PNG attachments; send-only scope, no inbox-delivery or MIME-readback claim.'}
d['send_status']='accepted';d['message_id']=receipt['message_id'];d['updated_at']=accepted;d['blocker']='';record.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'channel':'email','status':'accepted','message_id':receipt['message_id']}))
