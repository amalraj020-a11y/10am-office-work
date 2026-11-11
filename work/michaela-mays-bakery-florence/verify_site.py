import json,sys,re
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
base=sys.argv[1].rstrip('/')+'/'
label=sys.argv[2]
out=Path(__file__).parent
report={'base':base,'checked_at':datetime.now(timezone.utc).isoformat(),'pages':['index.html'],'viewports':[]}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for w in [1440,390]:
  page=b.new_page(viewport={'width':w,'height':1000 if w==1440 else 844},device_scale_factor=1)
  errors=[];failed=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  response=page.goto(base,wait_until='networkidle',timeout=60000)
  text=page.locator('body').inner_text()
  result=page.evaluate('''() => ({overflow:document.documentElement.scrollWidth>innerWidth+2,images:[...document.images].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0,alt:i.alt})),anchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash),links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href')),forms:document.forms.length})''')
  assert response.status==200
  assert "Michaela May's Bakery" in text and 'Developed by MultiMax' in text
  assert not re.search(r'lorem ipsum|signup|free trial|100,000|pricing table|your company',text,re.I)
  assert not result['overflow'] and not result['anchors'] and not result['forms']
  assert all(i['loaded'] and i['alt'] for i in result['images'])
  assert 'mailto:ricemm602@gmail.com' in result['links'] and 'tel:+19062823027' in result['links']
  assert all(x and x!='#' for x in result['links'])
  if w==390:
   button=page.get_by_role('button',name='Toggle menu');button.click();assert button.get_attribute('aria-expanded')=='true'
   page.locator('#navbarResponsive a').first.click();assert button.get_attribute('aria-expanded')=='false'
   button.click();page.keyboard.press('Escape');assert button.get_attribute('aria-expanded')=='false'
   page.evaluate('scrollTo(0,0)');page.wait_for_timeout(400)
  assert not errors and not failed,(errors,failed)
  if label=='local':page.screenshot(path=f'/tmp/michaela-{w}.png',full_page=True)
  report['viewports'].append({'width':w,'passed':True,'errors':errors,'failed_responses':failed,**result})
  page.close()
 b.close()
(out/f'qa-{label}.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'report':str(out/f'qa-{label}.json'),'passed':len(report['viewports'])}))
