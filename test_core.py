
import json,csv,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
artifact=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).with_name('index.html')
scratch=Path(__file__).with_name('test-output');scratch.mkdir(exist_ok=True)
qa={}
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,channel='msedge');ctx=b.new_context(accept_downloads=True,viewport={'width':1440,'height':1050});pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(artifact.as_uri());pg.clock.install()
 for n,name in enumerate(['Silinder pneumatik','Load cell & pad','Timbangan','Regulator E/P','ESP32 + antarmuka','Kompresor','HX711','Rangka reaksi'],1):
  pg.locator('button[data-component-select="'+str(n)+'"]').click();assert pg.locator('#pls-inspector-title').inner_text()==name
 pg.locator('.studio-hotspot[data-component-select="7"]').focus();pg.keyboard.press('Enter');assert pg.locator('#pls-inspector-title').inner_text()=='HX711'
 qa['eight_components']='all selectable; keyboard hotspot works'
 pg.locator('#pls-focus-electronics').click();assert pg.locator('.pls-machine').get_attribute('viewBox')!='0 0 600 385';pg.locator('#pls-focus-all').click();pg.locator('#pls-zoom').click();assert pg.locator('#pls-apparatus-dialog').evaluate('e=>e.open');pg.keyboard.press('Escape');assert pg.locator('.pls-machine-wrap .pls-machine').count()==1
 qa['magnification']='all/mechanical/electronics and dialog return verified'
 pg.fill('#pls-target-number','-4');pg.locator('#pls-target-number').dispatch_event('change');assert pg.locator('#pls-target-number').input_value()=='0';pg.locator('#pls-start').click();assert pg.evaluate('plsApp.getState().mode')=='idle'
 pg.fill('#pls-target-number','25');pg.locator('#pls-target-number').dispatch_event('change');assert pg.locator('#pls-target-number').input_value()=='20';qa['target_validation']='0–20 kg clamps; zero cannot start'
 pg.locator('#pls-start').click();pg.clock.run_for(22000);s=pg.evaluate('plsApp.getState()');assert s['stable'];assert abs(s['mass']-20)<.01;assert abs(s['pressure']-2.43948)<.01;assert abs(s['scale']-20.04)<.01
 qa['target_20kg']={k:s[k] for k in ['mass','scale','pressure','stable']}
 assert pg.locator('#pls-record').is_enabled();pg.locator('#pls-record').click();assert pg.locator('#pls-count').inner_text()=='1';assert pg.locator('#pls-workflow [aria-current="step"]').inner_text().endswith('Simpan')
 pg.locator('#pls-tab-model').click();assert pg.locator('#pls-diameter').is_disabled();pg.locator('#pls-tab-tool').click()
 pg.locator('#pls-emergency').click();assert pg.locator('#pls-record').is_disabled();pg.clock.run_for(5000);s=pg.evaluate('plsApp.getState()');assert s['mass']==0 and s['pressure']==0 and s['emergency'];pg.locator('#pls-start').click();assert not pg.evaluate('plsApp.getState().emergency');assert pg.evaluate('plsApp.getState().mode')=='idle';qa['emergency']='vents zero, save disabled, explicit reset remains idle'
 pg.locator('#pls-tab-model').click();pg.fill('#pls-scale-offset','0.12');pg.locator('#pls-scale-offset').dispatch_event('change');pg.locator('#pls-tab-tool').click();assert abs(pg.evaluate('plsApp.getState().scale')-.12)<1e-9;pg.locator('#pls-tare').click();assert pg.evaluate('plsApp.getState().scale')==0;qa['tare']='unloaded scale offset zeroed'
 pg.locator('#pls-sound').click();assert pg.locator('#pls-sound-label').inner_text()=='Suara mati';pg.locator('#pls-sound').click();assert pg.locator('#pls-sound-label').inner_text()=='Suara aktif';qa['sound_toggle']='passed'
 pg.locator('#pls-tab-results').click()
 with pg.expect_download() as dl:pg.locator('#pls-export').click()
 dl.value.save_as(str(scratch/'qa-export.csv'));rowlist=list(csv.reader((scratch/'qa-export.csv').read_text(encoding='utf-8-sig').splitlines()));assert len(rowlist)==3;qa['csv']='one saved record; notice + headers + row'
 pg.reload();assert pg.locator('#pls-count').inner_text()=='1';assert pg.locator('#pls-tab-results').get_attribute('aria-selected')=='true';assert pg.evaluate('plsApp.getState().mode')=='idle';qa['persistence']='saved records and active tab survive; load does not restart'
 qa['browser_errors']=errors;assert not errors,errors
 print(json.dumps(qa,indent=2));ctx.close();b.close()
(scratch/'qa-core.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
