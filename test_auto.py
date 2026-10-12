
import json,csv,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
artifact=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).with_name('index.html');scratch=Path(__file__).with_name('test-output');scratch.mkdir(exist_ok=True)
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,channel='msedge');pg=b.new_page(accept_downloads=True,viewport={'width':1440,'height':1050});errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(artifact.as_uri());pg.clock.install()
 pg.select_option('#pls-cycles','3');pg.locator('#pls-auto').click();assert pg.locator('#pls-target-number').is_disabled();assert pg.locator('#pls-cycles').is_disabled();assert pg.locator('#pls-auto-progress').is_visible()
 for i in range(15):
  pg.clock.run_for(15000)
  state=pg.evaluate('plsApp.getState()');n=pg.evaluate('plsApp.getRecords().length')
  if not state['auto']:break
 records=pg.evaluate('plsApp.getRecords()');assert len(records)==12,(len(records),state);assert not state['auto'];assert state['mode']=='idle';assert state['mass']==0 and state['pressure']==0
 expected=[5,10,15,20]*3;assert [r['target'] for r in records]==expected;assert len(set(r['loadCycle'] for r in records))==12
 assert max(abs(r['reference']-r['target']) for r in records)<.05
 assert not pg.locator('#pls-target-number').is_disabled();assert pg.locator('#pls-auto-progress').is_hidden()
 pg.locator('#pls-tab-results').click();assert pg.locator('#pls-result-rows tr').count()==12
 assert pg.locator('#pls-summary-repeat').inner_text()!='—';assert pg.locator('#pls-summary-linearity').inner_text()!='—'
 with pg.expect_download() as dl:pg.locator('#pls-export').click()
 dest=scratch/'qa-auto-12.csv';dl.value.save_as(str(dest));rows=list(csv.reader(dest.read_text(encoding='utf-8-sig').splitlines()));assert len(rows)==14
 report={'automatic_targets':[r['target'] for r in records],'record_count':len(records),'distinct_load_cycles':len(set(r['loadCycle'] for r in records)),'max_reference_error_kg':max(abs(r['reference']-r['target']) for r in records),'simulation_time_s':state['t'],'unloaded_at_completion':state['mass']==0,'export_data_rows':len(rows)-2,'browser_errors':errors};assert not errors;print(json.dumps(report,indent=2));(scratch/'qa-auto.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(scratch/'qa-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 pg.screenshot(path=str(scratch/'studio-results-final.png'),full_page=True);b.close()
