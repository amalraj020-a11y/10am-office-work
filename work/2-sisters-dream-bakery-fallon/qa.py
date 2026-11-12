"""Fresh desktop/mobile verification for this run; outputs public facts only."""
import json,sys,datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
base=sys.argv[1].rstrip('/')+'/'
label=sys.argv[2]
out=Path(__file__).parent
reports=[]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height in [(1440,1000),(390,844)]:
  page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
  errors=[];failed=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  response=page.goto(base,wait_until='networkidle',timeout=60000)
  body=page.locator('body').inner_text()
  broken=page.locator('img').evaluate_all('(els)=>els.filter(e=>!e.complete||!e.naturalWidth).map(e=>e.src)')
  anchors=page.locator('a[href^="#"]').evaluate_all('(els)=>els.map(e=>e.getAttribute("href")).filter(h=>h==="#"||!document.querySelector(h))')
  contacts=page.locator('a[href^="mailto:"],a[href^="tel:"]').evaluate_all('(els)=>els.map(e=>e.href)')
  menu=True
  if width<992:
   button=page.locator('.navbar-toggler');button.click();menu=button.get_attribute('aria-expanded')=='true' and page.locator('#navbarNav').is_visible()
   page.locator('#navbarNav a').first.click();menu=menu and button.get_attribute('aria-expanded')=='false'
   button.click();page.keyboard.press('Escape');menu=menu and button.get_attribute('aria-expanded')=='false'
  page.evaluate('scrollTo(0,0)');page.wait_for_timeout(500)
  overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
  page.screenshot(path=str(out/f'{label}-{width}.png'),full_page=True)
  report={'width':width,'http_status':response.status,'errors':errors,'asset_failures':failed,'broken_images':broken,'broken_anchors':anchors,'horizontal_overflow':overflow,'forms':page.locator('form').count(),'contacts':contacts,'menu_passed':menu,'identity':"2 Sisters Dream Bakery" in body,'footer':'Developed by MultiMax' in body,'concept_label':'Not the bakery’s official website' in body}
  report['passed']=all([response.status==200,not errors,not failed,not broken,not anchors,not overflow,report['forms']==0,menu,report['identity'],report['footer'],report['concept_label'],set(contacts)=={'mailto:2sistersdreambakery@gmail.com','tel:+17753368436'}])
  reports.append(report);page.close()
 browser.close()
result={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':base,'pages':['index.html'],'viewports':reports}
(out/f'qa-{label}.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
if not all(r['passed'] for r in reports):raise SystemExit(1)
