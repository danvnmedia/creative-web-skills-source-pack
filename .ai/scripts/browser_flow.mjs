#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

function usage(code=0) {
  console.log(`Usage: node .ai/scripts/browser_flow.mjs --spec FILE --out DIR [--timeout-ms 30000] [--fresh-output]\n\nSpec example:\n{\n  "baseUrl": "http://localhost:3000",\n  "viewport": {"width": 390, "height": 844},\n  "allowHttpErrors": [{"regex": "favicon\\\\.ico$", "reason": "non-critical optional icon"}],\n  "steps": [\n    {"action":"goto","path":"/"},\n    {"action":"fill","label":"Prompt","value":"hello"},\n    {"action":"click","role":"button","name":"Generate"},\n    {"action":"expectText","text":"Result"},\n    {"action":"screenshot","name":"result"}\n  ]\n}\n\nSupported actions: goto, reload, click, fill, press, waitForVisible, expectVisible, expectText, expectUrl, captureAttribute, waitForAttributeChange, expectAttribute, expectNoHorizontalOverflow, expectNoOverlap, screenshot.\nSelectors may use selector, label, role+name, placeholder, or text. No arbitrary JavaScript/eval is supported.\n`);
  process.exit(code);
}

const argv=process.argv.slice(2); if(argv.includes('--help')||argv.includes('-h')) usage(0);
let specPath=null,out=null,timeoutMs=30000,freshOutput=false;
for(let i=0;i<argv.length;i++){
  const a=argv[i], v=()=>argv[++i];
  if(a==='--spec') specPath=v(); else if(a==='--out') out=v(); else if(a==='--timeout-ms') timeoutMs=Number(v()); else if(a==='--fresh-output') freshOutput=true; else usage(2);
}
if(!specPath||!out) usage(2);

let pw;
try { pw=await import('playwright'); }
catch { try { pw=await import('@playwright/test'); } catch {
  console.error('Playwright is not installed. Add playwright or @playwright/test before claiming critical-flow verification.');
  process.exit(2);
}}
if(!pw.chromium){ console.error('Chromium launcher unavailable from Playwright package'); process.exit(2); }

const spec=JSON.parse(fs.readFileSync(specPath,'utf8'));
if(!spec.baseUrl || !Array.isArray(spec.steps) || spec.steps.length===0){
  console.error('Flow spec requires baseUrl and a non-empty steps array.'); process.exit(2);
}
for(const item of spec.allowHttpErrors || []){
  if(!item.regex || !item.reason || String(item.reason).trim().length < 8){
    console.error('Every allowHttpErrors entry requires regex and a meaningful reason.'); process.exit(2);
  }
}
const allowed=(url)=> (spec.allowHttpErrors || []).some(x=>new RegExp(x.regex).test(url));
if(freshOutput && fs.existsSync(out) && fs.readdirSync(out).length){
  console.error(`Output directory is not fresh: ${out}`); process.exit(2);
}
fs.mkdirSync(out,{recursive:true});

function locator(page, step){
  if(step.selector) return page.locator(step.selector);
  if(step.label) return page.getByLabel(step.label, {exact: step.exact ?? true});
  if(step.placeholder) return page.getByPlaceholder(step.placeholder, {exact: step.exact ?? true});
  if(step.role) return page.getByRole(step.role, {name: step.name, exact: step.exact ?? true});
  if(step.text) return page.getByText(step.text, {exact: step.exact ?? false});
  throw new Error(`step ${step.action} requires selector, label, placeholder, role+name, or text`);
}
function resolveUrl(baseUrl, step){
  if(step.url) return new URL(step.url, baseUrl).toString();
  if(step.path) return new URL(step.path, baseUrl).toString();
  return baseUrl;
}

const browser=await pw.chromium.launch({headless:true});
const viewport=spec.viewport || {width: 1440, height: 900};
const page=await browser.newPage({viewport});
page.setDefaultTimeout(timeoutMs);
const report={
  spec: path.resolve(specPath), baseUrl: spec.baseUrl, viewport,
  startedAt:new Date().toISOString(), finalUrl:null, pass:false,
  steps:[], consoleErrors:[], consoleWarnings:[], pageErrors:[], requestFailures:[], httpErrors:[],
  allowHttpErrors: spec.allowHttpErrors || [], artifacts:[]
};
page.on('console',msg=>{ const item={type:msg.type(),text:msg.text()}; if(msg.type()==='error') report.consoleErrors.push(item); else if(msg.type()==='warning') report.consoleWarnings.push(item); });
page.on('pageerror',err=>report.pageErrors.push(String(err)));
page.on('requestfailed',req=>{ if(!allowed(req.url())) report.requestFailures.push({url:req.url(),method:req.method(),failure:req.failure()}); });
page.on('response',res=>{ if(res.status()>=400 && !allowed(res.url())) report.httpErrors.push({url:res.url(),status:res.status(),statusText:res.statusText()}); });

let failed=null; const variables={};
try{
  for(let index=0; index<spec.steps.length; index++){
    const step=spec.steps[index]; const rec={index,action:step.action,status:'running'}; const start=Date.now();
    try{
      switch(step.action){
        case 'goto':
          await page.goto(resolveUrl(spec.baseUrl,step), {waitUntil:step.waitUntil || 'domcontentloaded', timeout:step.timeoutMs || timeoutMs});
          if(step.networkIdle !== false) await page.waitForLoadState('networkidle',{timeout:Math.min(step.timeoutMs||timeoutMs,8000)}).catch(()=>{});
          break;
        case 'reload':
          await page.reload({waitUntil:step.waitUntil || 'domcontentloaded', timeout:step.timeoutMs || timeoutMs});
          if(step.networkIdle !== false) await page.waitForLoadState('networkidle',{timeout:Math.min(step.timeoutMs||timeoutMs,8000)}).catch(()=>{});
          break;
        case 'click': await locator(page,step).click(); break;
        case 'fill': await locator(page,step).fill(String(step.value ?? '')); break;
        case 'press': await locator(page,step).press(step.key || 'Enter'); break;
        case 'waitForVisible': await locator(page,step).waitFor({state:'visible',timeout:step.timeoutMs||timeoutMs}); break;
        case 'expectVisible':
          if(!(await locator(page,step).isVisible())) throw new Error('expected locator to be visible');
          break;
        case 'expectText': {
          const scope=step.selector ? page.locator(step.selector) : page.locator('body');
          const body=await scope.innerText();
          if(!body.includes(String(step.text))) throw new Error(`missing expected text: ${step.text}`);
          break;
        }
        case 'expectUrl': {
          const current=page.url();
          if(step.regex){ if(!(new RegExp(step.regex)).test(current)) throw new Error(`URL ${current} does not match ${step.regex}`); }
          else if(step.url && current!==resolveUrl(spec.baseUrl,step)) throw new Error(`URL mismatch: ${current}`);
          else if(step.path && new URL(current).pathname!==step.path) throw new Error(`URL path mismatch: ${current}`);
          break;
        }
        case 'captureAttribute': {
          if(!step.attribute || !step.as) throw new Error('captureAttribute requires attribute and as');
          const value=await locator(page,step).getAttribute(step.attribute);
          if(value===null) throw new Error(`attribute ${step.attribute} is missing`);
          variables[step.as]=value; rec.value=value; break;
        }
        case 'waitForAttributeChange': {
          if(!step.attribute || !step.from) throw new Error('waitForAttributeChange requires attribute and from');
          const previous=variables[step.from];
          if(previous===undefined) throw new Error(`unknown captured variable: ${step.from}`);
          const target=locator(page,step); const deadline=Date.now()+(step.timeoutMs||timeoutMs); let value;
          do { value=await target.getAttribute(step.attribute); if(value!==null && value!==previous) break; await page.waitForTimeout(100); } while(Date.now()<deadline);
          if(value===null || value===previous) throw new Error(`attribute ${step.attribute} did not change from ${previous}`);
          if(step.as) variables[step.as]=value; rec.value=value; break;
        }
        case 'expectAttribute': {
          if(!step.attribute) throw new Error('expectAttribute requires attribute');
          const expected=step.from ? variables[step.from] : String(step.value ?? '');
          if(step.from && expected===undefined) throw new Error(`unknown captured variable: ${step.from}`);
          const actual=await locator(page,step).getAttribute(step.attribute);
          if(actual!==expected) throw new Error(`attribute ${step.attribute} mismatch: expected ${expected}, got ${actual}`);
          break;
        }
        case 'expectNoHorizontalOverflow': {
          const scope=step.selector ? page.locator(step.selector) : page.locator('html');
          const dimensions=await scope.evaluate(el=>({scrollWidth:el.scrollWidth,clientWidth:el.clientWidth}));
          if(dimensions.scrollWidth>dimensions.clientWidth+(step.tolerance||1)) throw new Error(`horizontal overflow: ${dimensions.scrollWidth}px > ${dimensions.clientWidth}px`);
          rec.dimensions=dimensions; break;
        }
        case 'expectNoOverlap': {
          if(!step.otherSelector) throw new Error('expectNoOverlap requires otherSelector');
          const first=await locator(page,step).boundingBox(); const second=await page.locator(step.otherSelector).boundingBox();
          if(!first || !second) throw new Error('cannot measure one or both overlap targets');
          const tolerance=step.tolerance||0;
          const overlapX=Math.min(first.x+first.width,second.x+second.width)-Math.max(first.x,second.x);
          const overlapY=Math.min(first.y+first.height,second.y+second.height)-Math.max(first.y,second.y);
          if(overlapX>tolerance && overlapY>tolerance) throw new Error(`elements overlap by ${overlapX}px x ${overlapY}px`);
          rec.bounds={first,second}; break;
        }
        case 'screenshot': {
          const safe=String(step.name || `step-${index}`).replace(/[^A-Za-z0-9_-]/g,'_');
          const shot=path.join(out,`${String(index).padStart(2,'0')}-${safe}.png`);
          await page.screenshot({path:shot,fullPage:step.fullPage ?? true}); report.artifacts.push(shot); rec.artifact=shot; break;
        }
        default: throw new Error(`unsupported action: ${step.action}`);
      }
      rec.status='pass';
    }catch(e){ rec.status='fail'; rec.error=String(e); throw Object.assign(new Error(`step ${index} ${step.action}: ${e}`),{_rec:rec}); }
    finally{ rec.durationMs=Date.now()-start; report.steps.push(rec); }
  }
}catch(e){ failed=String(e); report.failure=failed; }

report.finalUrl=page.url();
try{
  const finalShot=path.join(out,'final.png'); await page.screenshot({path:finalShot,fullPage:true}); report.artifacts.push(finalShot);
}catch{}
await browser.close();
report.finishedAt=new Date().toISOString();
const runtimeFailure = report.consoleErrors.length || report.pageErrors.length || report.requestFailures.length || report.httpErrors.length;
report.pass=!failed && !runtimeFailure;
fs.writeFileSync(path.join(out,'flow-report.json'),JSON.stringify(report,null,2));
const owned=['flow-report.json',...report.artifacts.map(x=>path.basename(x))];
fs.writeFileSync(path.join(out,'.harness-owned-files.json'),JSON.stringify({schemaVersion:1,files:owned},null,2));
console.log(JSON.stringify(report,null,2));
process.exit(report.pass?0:1);
