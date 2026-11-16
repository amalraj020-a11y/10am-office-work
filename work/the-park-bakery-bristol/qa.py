"""Read-only browser checks for this run's single-page static concept."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
base=sys.argv[1];label=sys.argv[2];out=Path(__file__).parent
report={'base_url':base,'checked_at':datetime.now(timezone.utc).isoformat(),'pages':[]}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 for width,height in [(1440,1000),(390,844)]:
  page=browser.new_page(viewport={'width':width,'height':height});errors=[];failed=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  response=page.goto(base,wait_until='networkidle',timeout=60000)
  checks=page.evaluate('''() => ({title:document.title,overflow:document.documentElement.scrollWidth>innerWidth+2,images:[...document.images].map(i=>({src:i.getAttribute('src'),ok:i.complete&&i.naturalWidth>0})),brokenAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash),links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href')),forms:document.forms.length,text:document.body.innerText})''')
  assert 'the park bakery' in checks['text'].lower() and 'Developed by MultiMax' in checks['text']
  import re
  assert not re.search(r'lorem ipsum|your company|creative agency|testimonials|\$[0-9]|£[0-9]',checks.pop('text'),re.I)
  menu='desktop-visible'
  if width<992:
   toggle=page.locator('.navbar-toggler');toggle.click();page.wait_for_timeout(400);assert toggle.get_attribute('aria-expanded')=='true'
   page.locator('#navigation a[href="#counter"]').click();page.wait_for_timeout(400);assert toggle.get_attribute('aria-expanded')=='false';menu='open and link-close passed';page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(400)
  page.screenshot(path=str(out/f'{label}-{width}.png'),full_page=True)
  row={'viewport':[width,height],'status':response.status,'console_errors':errors,'http_failures':failed,'mobile_menu':menu,**checks};report['pages'].append(row)
  assert response.status==200 and not errors and not failed and not checks['overflow'] and not checks['brokenAnchors'] and checks['forms']==0 and all(i['ok'] for i in checks['images']),row
  page.close()
 browser.close()
(out/f'qa-{label}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'qa':label,'views':len(report['pages']),'result':'passed'}))
