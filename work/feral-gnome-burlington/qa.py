"""Read-only browser QA for this run's two static pages."""
import json,sys,re
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
base=sys.argv[1].rstrip('/')+'/'
label=sys.argv[2]
out=Path('work/feral-gnome-burlington')
report={'base':base,'checked_at':datetime.now(timezone.utc).isoformat(),'pages':[]}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for name in ['index.html','credits.html']:
  for view,w,h in [('desktop',1440,1000),('mobile',390,844)]:
   page=b.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
   errors=[];bad=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
   page.on('response',lambda r:bad.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
   r=page.goto(base+name,wait_until='networkidle',timeout=60000)
   text=page.locator('body').inner_text()
   checks=page.evaluate('''() => ({overflow:document.documentElement.scrollWidth>innerWidth+2,brokenImages:[...document.images].filter(x=>!x.complete||x.naturalWidth===0).map(x=>x.src),badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash),forms:document.forms.length,links:[...document.querySelectorAll('a')].map(x=>x.getAttribute('href'))})''')
   if view=='mobile' and name=='index.html':
    page.locator('.navbar-toggler').click();page.wait_for_timeout(100)
    assert page.locator('#site-nav').is_visible()
    assert page.locator('.navbar-toggler').get_attribute('aria-expanded')=='true'
    page.locator('#site-nav a').first.click();page.wait_for_timeout(100)
    assert page.locator('.navbar-toggler').get_attribute('aria-expanded')=='false'
    assert not page.locator('#site-nav').is_visible()
    page.locator('.navbar-toggler').click();page.keyboard.press('Escape')
    assert page.locator('.navbar-toggler').get_attribute('aria-expanded')=='false'
    page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(300)
    checks['menu']='open, close on selection, Escape: passed'
   checks['placeholders']=re.findall(r'lorem ipsum|cool feature|handshake infographic|buy template|your (?:company|business)|123 street',text,re.I)
   checks['identity']='Feral Gnome Bakeshop' in text and 'Developed by MultiMax' in text
   checks['status']=r.status
   checks['errors']=errors;checks['http_failures']=bad;checks['page']=name;checks['viewport']=view
   assert r.status==200 and checks['identity'] and not any([checks['overflow'],checks['brokenImages'],checks['badAnchors'],checks['forms'],checks['placeholders'],errors,bad]),checks
   if name=='index.html':
    assert 'mailto:feralgnomebakeshop@gmail.com' in checks['links']
    page.screenshot(path=str(out/f'{label}-{view}.png'),full_page=True)
   for href in checks['links']:
    if not href.startswith(('http','mailto:','#')):
     response=page.request.get(base+href)
     assert response.status==200,(href,response.status)
   report['pages'].append(checks);page.close()
 b.close()
(out/f'qa-{label}.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'result':'pass','pages_and_viewports':len(report['pages']),'report':str(out/f'qa-{label}.json')}))
