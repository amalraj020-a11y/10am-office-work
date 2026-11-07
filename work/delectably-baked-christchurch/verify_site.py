import argparse,json,hashlib,threading,http.server,functools,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]; SLUG='delectably-baked-christchurch'; SITE=ROOT/'websites'/SLUG; OUT=ROOT/'work'/SLUG
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
if args.live:base=f'https://amalraj020-a11y.github.io/10am-office-work/websites/{SLUG}/'
else:
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
 threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 for file in SITE.glob('*.html'):
  for width in [1440,390]:
   page=browser.new_page(viewport={'width':width,'height':1000 if width==1440 else 844});errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
   page.on('response',lambda r:errors.append(f'HTTP {r.status} {r.url}') if r.status>=400 else None)
   response=page.goto(base+file.name,wait_until='networkidle',timeout=45000)
   assert response.status==200
   text=page.locator('body').inner_text();assert 'Delectably Baked' in text and 'Developed by MultiMax' in text
   assert not any(term in text.lower() for term in ['lorem ipsum','your company','product managers','sign up','myspace','casino','123 street'])
   assert page.locator('form').count()==0
   assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
   bad=page.locator('img').evaluate_all('(imgs)=>imgs.filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)');assert not bad,bad
   links=page.locator('a').evaluate_all('(aa)=>aa.map(a=>a.getAttribute("href"))')
   for href in links:
    assert href and href not in ['#','#!']
    if href.startswith('#'):assert page.locator(href).count()>0,href
    elif ':' not in href:assert (SITE/href).is_file(),href
   assert 'mailto:delectablybaked@gmail.com' in links
   menu='not applicable'
   if width==390:
    toggle=page.locator('#menu-toggle');toggle.click();assert toggle.get_attribute('aria-expanded')=='true';assert page.locator('#navigation').is_visible();page.keyboard.press('Escape');assert toggle.get_attribute('aria-expanded')=='false'
    toggle.click();page.locator('#navigation a[href="#bakes"]').click();assert toggle.get_attribute('aria-expanded')=='false';page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(400);menu='open, Escape close, anchor close passed'
   assert not errors,errors
   if not args.live:page.screenshot(path=f'/tmp/{SLUG}-{width}.png',full_page=True)
   results.append({'page':file.name,'width':width,'http':response.status,'images':'decoded','anchors':'valid','forms':0,'overflow':False,'errors':errors,'mobile_menu':menu,'links':links})
   page.close()
 browser.close()
if not args.live:server.shutdown()
report={'checked_at':datetime.now(timezone.utc).isoformat(),'base':base,'result':'passed','tests':results}
(OUT/('qa-live.json' if args.live else 'qa-local.json')).write_text(json.dumps(report,indent=2)+'\n')
if args.live:
 hashes=[]
 for file in SITE.rglob('*'):
  if file.is_file() and (file.suffix in ['.html','.css','.js','.jpg']):
   rel=str(file.relative_to(SITE));r=urllib.request.urlopen(base+rel,timeout=25);remote=r.read();digest=hashlib.sha256(file.read_bytes()).hexdigest();assert hashlib.sha256(remote).hexdigest()==digest,rel;hashes.append({'path':rel,'sha256':digest,'http_status':r.status,'matches':True})
 (OUT/'live-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print(json.dumps({'result':'passed','views':len(results),'live':args.live}))
