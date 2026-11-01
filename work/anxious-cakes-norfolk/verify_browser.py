import json,sys,datetime,re
from pathlib import Path
from playwright.sync_api import sync_playwright
base=sys.argv[1];out=Path(sys.argv[2]);results=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for width in [1440,768,390,320]:
  page=b.new_page(viewport={'width':width,'height':1000 if width>760 else 844},device_scale_factor=1)
  errors=[];bad=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('response',lambda r:bad.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  response=page.goto(base,wait_until='networkidle',timeout=60000)
  page.evaluate('Promise.all([...document.images].map(i=>i.decode().catch(()=>null)))')
  data=page.evaluate('''() => ({title:document.title,overflow:document.documentElement.scrollWidth>innerWidth+2,brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),missingAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash),forms:document.forms.length,links:[...document.querySelectorAll('a')].map(a=>({text:a.innerText,href:a.getAttribute('href')}))})''')
  text=page.locator('body').inner_text();data['identity']='Anxious Cakes' in text and 'Developed by MultiMax' in text
  data['placeholder_matches']=re.findall(r'lorem ipsum|your company|buy template|landwind|pricing cards|testimonials here',text,re.I)
  data['menu']='desktop'
  if width<=760:
   toggle=page.locator('.menu-button');toggle.click();assert toggle.get_attribute('aria-expanded')=='true';assert page.locator('#mobile-menu-2').is_visible()
   page.locator('#mobile-menu-2 a[href="#bakes"]').click();assert toggle.get_attribute('aria-expanded')=='false';assert not page.locator('#mobile-menu-2').is_visible()
   toggle.click();page.keyboard.press('Escape');assert toggle.get_attribute('aria-expanded')=='false'
   data['menu']='open, navigate-close and Escape-close passed'
  page.evaluate('scrollTo(0,0)');page.wait_for_timeout(400)
  if width in [1440,390]:page.screenshot(path=f'/tmp/anxious-{width}.png',full_page=True)
  data.update(width=width,http=response.status,console_errors=errors,http_errors=bad)
  data['passed']=response.status==200 and data['identity'] and not any([data['overflow'],data['brokenImages'],data['missingAnchors'],data['forms'],data['placeholder_matches'],errors,bad])
  results.append(data);page.close()
 b.close()
r={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':base,'pages':['index.html'],'results':results,'passed':all(r['passed'] for r in results)}
out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'views':[{k:x[k] for k in ['width','passed','overflow','brokenImages','console_errors','http_errors','menu']} for x in results]}))
if not r['passed']:sys.exit(1)
