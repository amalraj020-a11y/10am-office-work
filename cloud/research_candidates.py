"""Collect public map leads for Qwen to verify; absence of a tag is not proof.

This helper never sends outreach or declares a business website-free. It stores
small, sourced leads so a Groq Free model turn can inspect them without filling
its context window with raw search HTML.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CITIES = [
    ('Lisbon, Portugal', '38.70,-9.17,38.74,-9.11'),
    ('Kolkata, India', '22.48,88.25,22.66,88.45'),
    ('Melbourne, Australia', '-37.88,144.88,-37.75,145.06'),
    ('Cape Town, South Africa', '-34.03,18.35,-33.85,18.55'),
    ('Mexico City, Mexico', '19.34,-99.24,19.49,-99.08'),
    ('Warsaw, Poland', '52.16,20.90,52.30,21.10'),
    ('Nairobi, Kenya', '-1.35,36.72,-1.20,36.90'),
    ('São Paulo, Brazil', '-23.65,-46.75,-23.48,-46.58'),
]


def prior_names():
    names = set()
    for item in json.loads((ROOT / 'data/prospects.json').read_text()):
        names.add(item['business_name'].casefold().strip())
    for path in (ROOT / 'work').glob('*/run.json'):
        try:
            names.add(json.loads(path.read_text())['business_name'].casefold().strip())
        except (KeyError, ValueError):
            continue
    return names


def candidates(payload, city, excluded):
    found = []
    for element in payload.get('elements', []):
        tags = element.get('tags', {})
        name = tags.get('name', '').strip()
        if not name or name.casefold() in excluded:
            continue
        if any(tags.get(k) for k in ('website', 'contact:website', 'url', 'contact:url')):
            continue
        email = tags.get('email') or tags.get('contact:email') or ''
        phone = tags.get('phone') or tags.get('contact:phone') or ''
        if not email and not phone:
            continue
        if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            email = ''
        if not email and not phone:
            continue
        kind = element['type']
        oid = element['id']
        found.append({
            'business_name': name,
            'city': city,
            'category': tags.get('amenity') or tags.get('shop') or '',
            'email_unverified': email,
            'phone_unverified': phone,
            'source_url': f'https://www.openstreetmap.org/{kind}/{oid}',
            'osm_id': f'{kind}/{oid}',
            'website_tag_absent': True,
            'verification_status': 'needs independent website and contact checks',
        })
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--city-index', type=int, required=True)
    parser.add_argument('--category', choices=('cafe', 'restaurant', 'bakery'), default='cafe')
    args = parser.parse_args()
    if not 0 <= args.city_index < len(CITIES):
        parser.error('city index out of range')
    city, bounds = CITIES[args.city_index]
    tag = 'shop' if args.category == 'bakery' else 'amenity'
    query = (f'[out:json][timeout:25];'
             f'nwr["{tag}"="{args.category}"][~"^(email|contact:email|phone|contact:phone)$"~"."]({bounds});'
             'out tags center 120;')
    payload = None
    failures = []
    for endpoint in ('https://overpass-api.de/api/interpreter',
                     'https://overpass.private.coffee/api/interpreter'):
        request = Request(endpoint, data=urlencode({'data': query}).encode(),
                          headers={'User-Agent': 'MultiMax-AmalaOffice/1.0 (public prospect research)',
                                   'Content-Type': 'application/x-www-form-urlencoded'})
        try:
            with urlopen(request, timeout=40) as response:
                payload = json.load(response)
            break
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            failures.append(f'{endpoint}: {type(exc).__name__}')
    if payload is None:
        raise SystemExit('Public map lookup unavailable: ' + '; '.join(failures))
    leads = candidates(payload, city, prior_names())[:25]
    out = ROOT / 'work' / 'research-candidates.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'city': city, 'category': args.category,
                               'source': 'OpenStreetMap via Overpass API',
                               'queried_at': datetime.now(timezone.utc).isoformat(),
                               'note': 'No website tag is NOT proof a website is absent. Verify independently.',
                               'candidates': leads}, indent=2, ensure_ascii=False))
    print(json.dumps({'saved': str(out.relative_to(ROOT)), 'city': city,
                      'count': len(leads),
                      'preview': [{'name': x['business_name'], 'contact':
                                   'email' if x['email_unverified'] else 'phone'} for x in leads[:5]]},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
