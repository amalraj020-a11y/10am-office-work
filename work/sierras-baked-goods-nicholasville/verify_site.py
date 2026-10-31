"""Run-specific browser verification; no credentials or outbound messaging."""
import argparse,functools,http.server,json,pathlib,threading,datetime
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[2]
SLUG='sierras-baked-goods-nicholasville'
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
if args.live: base=f'https://amalraj020-a11y.github.io/10am-office-work/websites/{SLUG}/'
else:
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a): pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'websites'/SLUG)))
 threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
report={'url':base,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pages':[]}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 for html in sorted((ROOT/'websites'/SLUG).glob('*.html')):
  for width in (1440,768,390,320):
   page=browser.new_page(viewport={'width':width,'height':1000 if width==1440 else 844},device_scale_factor=1)
   errors=[];http_errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('console',lambda e:errors.append(e.text) if e.type=='error' else None)
   page.on('response',lambda r:http_errors.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
   response=page.goto(base+html.name,wait_until='networkidle',timeout=60000)
   data=page.evaluate('''() => ({title:document.title,overflow:document.documentElement.scrollWidth>innerWidth+2,images:[...document.images].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0})),badAnchors:[...document.querySelectorAll('a[href^="#"]')].map(a=>a.getAttribute('href')).filter(h=>h.length<2||!document.getElementById(h.slice(1))),forms:document.forms.length,links:[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'))})''')
   txt=page.locator('body').inner_text();data.update(width=width,page=html.name,status=response.status,console_errors=errors,http_errors=http_errors,identity="Sierra's Baked Goods" in txt,multimax='Developed by MultiMax' in txt,concept_disclosure='NOT THE OFFICIAL BUSINESS WEBSITE' in txt)
   if width<992:
    toggle=page.locator('.navbar-toggler');toggle.click();page.wait_for_function("document.querySelector('#navbarResponsive').classList.contains('show')")
    opened=toggle.get_attribute('aria-expanded')=='true'
    page.locator('#navbarResponsive a[href="#bakes"]').click();page.wait_for_function("!document.querySelector('#navbarResponsive').classList.contains('show')")
    data['mobile_menu']=opened and toggle.get_attribute('aria-expanded')=='false'
   else:data['mobile_menu']='not applicable'
   page.evaluate('scrollTo(0,0)');page.wait_for_timeout(250)
   if width in (1440,390):page.screenshot(path=f'/tmp/{SLUG}-{width}-'+('live' if args.live else 'local')+'.png',full_page=True)
   data['pass']=all([data['status']==200,not errors,not http_errors,not data['overflow'],not data['badAnchors'],all(i['loaded'] for i in data['images']),data['forms']==0,data['identity'],data['multimax'],data['concept_disclosure'],data['mobile_menu'] is not False,all(h.startswith(('#','mailto:','https://')) for h in data['links'])])
   report['pages'].append(data);page.close()
 browser.close()
report['pass']=all(x['pass'] for x in report['pages'])
path=ROOT/'work'/SLUG/('qa-live.json' if args.live else 'qa-local.json');path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(path.relative_to(ROOT)),'pass':report['pass'],'checks':[{k:x[k] for k in ('page','width','pass','console_errors','http_errors','overflow','mobile_menu')} for x in report['pages']]}))
if not args.live:server.shutdown()
raise SystemExit(0 if report['pass'] else 1)
