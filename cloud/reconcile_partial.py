"""Finish recorded office work after the model stops following a confirmed send.

This recovery path never sends messages. It only publishes a receipt that the
agent already wrote to the business record during the current run.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen

from artifacts import tracker
from step_runner import verify_completion

ROOT = Path(__file__).resolve().parents[1]
GOOD_SEND = {'accepted', 'sent', 'delivered'}


def has_expected_route(value):
    if isinstance(value, dict):
        if value.get('provider') == 'openai' and value.get('model') == 'gpt-6-astra':
            return True
        return any(has_expected_route(child) for child in value.values())
    if isinstance(value, list):
        return any(has_expected_route(child) for child in value)
    return False


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout.strip()


def reconcile(started_at, run_dir):
    """Return (slug, URL) only for one unambiguous, already-sent run."""
    candidates = []
    for path in (ROOT / 'work').glob('*/run.json'):
        data = json.loads(path.read_text())
        try:
            recorded = datetime.fromisoformat(data['started_at'].replace('Z', '+00:00'))
            delta = abs(recorded.timestamp() - started_at)
        except (KeyError, TypeError, ValueError):
            continue
        if delta <= 600:
            candidates.append((path, data))
    if len(candidates) != 1:
        raise ValueError('Recovery requires exactly one record from this run')
    record, data = candidates[0]
    slug = record.parent.name
    if data.get('model') != 'openai/gpt-6-astra':
        raise ValueError('Recovery record has an unexpected model')
    agent_output = json.loads((run_dir / 'agent-output.json').read_text())
    if not has_expected_route(agent_output):
        raise ValueError('Recovery has no verified model route')
    channels = data.get('contact_channels')
    receipts = data.get('send_results', {})
    if not isinstance(channels, list) or not channels or any(
            channel not in ('email', 'whatsapp') for channel in channels):
        raise ValueError('Recovery has no validated contact channel')
    for channel in channels:
        receipt = receipts.get(channel, {})
        if receipt.get('status') not in GOOD_SEND or not receipt.get('message_id'):
            raise ValueError('Recovery has no confirmed send for ' + channel)
    if any(receipt.get('status') == 'unknown' for receipt in receipts.values()):
        raise ValueError('Recovery cannot reconcile an uncertain send')
    if data.get('send_status') not in GOOD_SEND:
        raise ValueError('Recovery record is not marked sent')
    if not data.get('outreach_text') or not data.get('template_url', '').startswith('https://themewagon.com/'):
        raise ValueError('Recovery record lacks outreach text or template evidence')
    images = data.get('screenshots', [])
    if len(images) != 2 or len(set(images)) != 2 or any(
            not (ROOT / image).is_file() for image in images):
        raise ValueError('Recovery has no pair of current screenshots')
    expected_url = 'https://amalraj020-a11y.github.io/10am-office-work/websites/' + slug + '/'
    if data.get('live_url') != expected_url:
        raise ValueError('Recovery has an unexpected website URL')
    with urlopen(Request(expected_url, headers={'User-Agent': 'AmalaOffice/1.0'}), timeout=25) as response:
        html = response.read(3_000_000).decode('utf-8', errors='replace')
        if response.status != 200 or data.get('business_name', '').casefold() not in html.casefold() or 'Developed by MultiMax' not in html:
            raise ValueError('Recovery website failed live verification')

    allowed = {str(record.relative_to(ROOT)).replace('\\', '/'),
               'work/office-tracker.xlsx'}
    scoped = ['websites/' + slug, 'work/' + slug,
              'work/screenshots/' + slug + '-desktop.png',
              'work/screenshots/' + slug + '-mobile.png',
              'work/office-tracker.xlsx', 'data/used-templates.json']
    changes = [line[3:].replace('\\', '/') for line in
               git('status', '--porcelain', '--', *scoped).splitlines()]
    if any(path not in allowed for path in changes):
        raise ValueError('Recovery found other unpublished site changes')
    if git('diff', '--cached', '--name-only'):
        raise ValueError('Recovery found unrelated staged changes')
    if git('rev-parse', 'HEAD') != git('rev-parse', 'origin/main'):
        raise ValueError('Recovery requires a pushed site commit')

    data['stage'] = 'outreach receipt published after agent interruption'
    data['updated_at'] = datetime.now(timezone.utc).isoformat()
    record.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tracker()
    git('add', '--', *sorted(allowed))
    git('commit', '-m', 'Record verified outreach for ' + data['business_name'])
    git('push', 'origin', 'main')
    url = verify_completion(slug)
    (run_dir / 'recovery.json').write_text(json.dumps({
        'status': 'complete', 'slug': slug, 'url': url,
        'channels': channels, 'note': 'No messages sent by recovery.'}, indent=2))
    return slug, url
