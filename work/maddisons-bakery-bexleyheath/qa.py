"""Bounded responsive checks for this run's single-page concept."""
import sys,json,datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
base=sys.argv[1];label=sys.argv[2];out=Path(__file__).parent
report={'url':base,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'views':[]}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for width,height in [(1440,1000),(390,844)]:
  page=b.new_page(viewport={'width':width,'height':height});errors=[];failed=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  r=page.goto(base,wait_until='networkidle');text=page.inner_text('body')
  result={'width':width,'status':r.status,'errors':errors,'failed_assets':failed,'identity':'Maddisons Bakery' in text.replace('\n',' '),'footer':'Developed by MultiMax' in text,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth+2'),'broken_images':page.locator('img').evaluate_all('(imgs)=>imgs.filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)'),'broken_anchors':page.locator('a[href^="#"]').evaluate_all('(as)=>as.map(a=>a.getAttribute("href")).filter(h=>!document.querySelector(h))'),'forms':page.locator('form').count(),'contact_links':page.locator('a[href^="mailto:"],a[href^="tel:"]').evaluate_all('(as)=>as.map(a=>a.getAttribute("href"))')}
  if width<992:
   button=page.get_by_role('button',name='Toggle navigation');button.click();result['menu_open']=page.locator('#navbarResponsive').is_visible();page.locator('#navbarResponsive a').last.click();result['menu_close']=not page.locator('#navbarResponsive').is_visible();page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(500)
  page.screenshot(path=str(out/f'{label}-{width}.png'),full_page=True)
  report['views'].append(result);page.close()
 b.close()
(out/f'qa-{label}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
assert all(v['status']==200 and v['identity'] and v['footer'] and not any([v['errors'],v['failed_assets'],v['overflow'],v['broken_images'],v['broken_anchors'],v['forms']]) and v.get('menu_open',True) and v.get('menu_close',True) for v in report['views'])
