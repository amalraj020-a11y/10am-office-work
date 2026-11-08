"""Bounded local/live browser validation for this run; no sending."""
import sys,json,hashlib,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2];slug='how-sweet-bakery-johor';out=root/'work'/slug
base=sys.argv[1].rstrip('/')+'/';mode=sys.argv[2]
reports=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for width in (1440,390):
  page=b.new_page(viewport={'width':width,'height':1000 if width==1440 else 844},device_scale_factor=1)
  errors=[];bad=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('response',lambda r:bad.append([r.status,r.url]) if r.status>=400 else None)
  r=page.goto(base,wait_until='networkidle');assert r.status==200
  assert page.title().startswith('How Sweet Bakery')
  text=page.locator('body').inner_text();assert 'Developed by MultiMax' in text
  assert not any(x in text.lower() for x in ['lorem ipsum','we are titan','your business','testimonials','123 street'])
  assert page.locator('form').count()==0
  assert page.locator('a[href="mailto:howsweetbakery96@gmail.com"]').count()==2
  assert page.locator('a[href="tel:+60137137956"]').count()==1
  assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
  for a in page.locator('a[href^="#"]').all():assert page.locator(a.get_attribute('href')).count()==1
  if width==390:
   button=page.locator('.navbar-toggle');button.click();assert button.get_attribute('aria-expanded')=='true';assert page.locator('#custom-collapse').is_visible()
   page.locator('#custom-collapse a').first.click();assert button.get_attribute('aria-expanded')=='false'
   button.click();page.keyboard.press('Escape');assert button.get_attribute('aria-expanded')=='false'
   page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(500)
  page.screenshot(path=str(out/f'{mode}-{width}.png'),full_page=True)
  assert not errors and not bad,(errors,bad)
  reports.append({'width':width,'passed':True,'console_errors':errors,'http_errors':bad,'images_decoded':True,'anchors':True,'overflow':False,'forms':0,'mobile_menu':'open, link-close, Escape passed' if width==390 else 'desktop links visible'})
  page.close()
 b.close()
hashes=[]
for f in (root/'websites'/slug).rglob('*'):
 if f.is_file():
  rel=str(f.relative_to(root/'websites'/slug));u=base+rel
  with urllib.request.urlopen(u,timeout=25) as r: data=r.read();assert r.status==200
  assert hashlib.sha256(data).digest()==hashlib.sha256(f.read_bytes()).digest(),rel
  hashes.append({'path':rel,'sha256':hashlib.sha256(data).hexdigest()})
d={'checked_at':datetime.now(timezone.utc).isoformat(),'base':base,'pages':1,'reports':reports,'all_file_hashes_match':hashes}
(out/f'qa-{mode}.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'mode':mode,'viewports_passed':len(reports),'files_matched':len(hashes)}))
