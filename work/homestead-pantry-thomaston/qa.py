"""Run all shipped-page desktop/mobile checks; no network mutations."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,sys,datetime
base=sys.argv[1].rstrip('/')+'/'
label=sys.argv[2]
out=Path(__file__).parent
reports=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 for width,height in [(1440,1000),(390,844)]:
  page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
  errors=[];failed=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('requestfailed',lambda r:failed.append({'url':r.url,'error':r.failure}))
  page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  response=page.goto(base,wait_until='networkidle',timeout=60000)
  checks=page.evaluate('''() => ({title:document.title,overflow:document.documentElement.scrollWidth>innerWidth+2,images:[...document.images].map(i=>({src:i.getAttribute('src'),ok:i.complete&&i.naturalWidth>0})),badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash),links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href')),forms:document.forms.length,text:document.body.innerText})''')
  checks['identity']='Homestead Pantry' in checks.pop('text')
  checks['footer']=page.get_by_text('Developed by MultiMax',exact=True).count()==1
  checks['menu']='desktop navigation visible'
  if width<992:
   toggle=page.locator('#menu-toggle');toggle.click()
   assert toggle.get_attribute('aria-expanded')=='true' and page.locator('#main-menu').is_visible()
   page.locator('#main-menu a[href="#pantry"]').click()
   assert toggle.get_attribute('aria-expanded')=='false' and not page.locator('#main-menu').is_visible()
   toggle.click();page.keyboard.press('Escape');assert toggle.get_attribute('aria-expanded')=='false'
   checks['menu']='open, link close and Escape close passed'
  page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(500)
  page.screenshot(path=str(out/f'{label}-{width}.png'),full_page=True)
  report={'viewport':width,'http':response.status,'errors':errors,'failed_requests':failed,**checks}
  report['passed']=response.status==200 and not errors and not failed and not checks['overflow'] and not checks['badAnchors'] and all(i['ok'] for i in checks['images']) and checks['identity'] and checks['footer'] and checks['forms']==0
  reports.append(report);page.close()
 browser.close()
result={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':base,'pages':['index.html'],'reports':reports,'passed':all(r['passed'] for r in reports)}
(out/f'{label}-qa.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'report':str(out/f'{label}-qa.json'),'errors':[{'viewport':r['viewport'],'errors':r['errors'],'failed':r['failed_requests'],'overflow':r['overflow']} for r in reports]}))
if not result['passed']:sys.exit(1)
