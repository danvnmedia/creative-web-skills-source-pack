#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

function usage(code=0) {
  console.log(`Usage: node .ai/scripts/browser_smoke.mjs --url URL --out DIR [options]\n\nOptions:\n  --viewports 390x844,1440x900\n  --settle-ms 1200\n  --timeout-ms 30000\n  --fresh-output            fail if DIR already contains artifacts\n  --allow-url-regex REGEX   repeatable; HTTP errors matching it do not fail\n  --check-text TEXT         require visible body text to contain TEXT\n`);
  process.exit(code);
}
const argv=process.argv.slice(2); if (argv.includes('--help')||argv.includes('-h')) usage(0);
let url=null,out=null,viewports='390x844,1440x900',settleMs=1200,timeoutMs=30000,checkText=null,freshOutput=false; const allow=[];
for (let i=0;i<argv.length;i++) {
  const a=argv[i]; const v=()=>argv[++i];
  if(a==='--url') url=v(); else if(a==='--out') out=v(); else if(a==='--viewports') viewports=v();
  else if(a==='--settle-ms') settleMs=Number(v()); else if(a==='--timeout-ms') timeoutMs=Number(v());
  else if(a==='--fresh-output') freshOutput=true;
  else if(a==='--allow-url-regex') allow.push(new RegExp(v())); else if(a==='--check-text') checkText=v(); else usage(2);
}
if(!url||!out) usage(2);
let pw;
try { pw=await import('playwright'); }
catch { try { pw=await import('@playwright/test'); } catch {
  console.error('Playwright is not installed. Add playwright or @playwright/test to this project before claiming browser verification.'); process.exit(2);
}}
const chromium=pw.chromium; if(!chromium){console.error('Chromium launcher unavailable from Playwright package');process.exit(2);}
if(freshOutput && fs.existsSync(out) && fs.readdirSync(out).length){
  console.error(`Output directory is not fresh: ${out}`); process.exit(2);
}
fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true});
const report={url,startedAt:new Date().toISOString(),viewports:[],summary:{consoleErrors:0,pageErrors:0,requestFailures:0,httpErrors:0,textFailures:0}};
const allowed=u=>allow.some(r=>r.test(u));
for(const spec of viewports.split(',').map(s=>s.trim()).filter(Boolean)){
  const [width,height]=spec.split('x').map(Number); if(!width||!height) throw new Error(`invalid viewport ${spec}`);
  const page=await browser.newPage({viewport:{width,height}}); const rec={viewport:{width,height},consoleErrors:[],consoleWarnings:[],pageErrors:[],requestFailures:[],httpErrors:[],screenshot:null,finalUrl:null};
  page.on('console',msg=>{ const item={type:msg.type(),text:msg.text()}; if(msg.type()==='error') rec.consoleErrors.push(item); else if(msg.type()==='warning') rec.consoleWarnings.push(item); });
  page.on('pageerror',err=>rec.pageErrors.push(String(err)));
  page.on('requestfailed',req=>{ if(!allowed(req.url())) rec.requestFailures.push({url:req.url(),method:req.method(),failure:req.failure()}); });
  page.on('response',res=>{ if(res.status()>=400 && !allowed(res.url())) rec.httpErrors.push({url:res.url(),status:res.status(),statusText:res.statusText()}); });
  try{
    await page.goto(url,{waitUntil:'domcontentloaded',timeout:timeoutMs});
    await page.waitForLoadState('networkidle',{timeout:Math.min(timeoutMs,8000)}).catch(()=>{});
    if(settleMs>0) await page.waitForTimeout(settleMs);
    rec.finalUrl=page.url();
    if(checkText){ const body=await page.locator('body').innerText().catch(()=> ''); if(!body.includes(checkText)) { rec.textFailure=`missing required text: ${checkText}`; report.summary.textFailures++; } }
    const shot=path.join(out,`smoke-${width}x${height}.png`); await page.screenshot({path:shot,fullPage:true}); rec.screenshot=shot;
  }catch(e){ rec.pageErrors.push(`navigation: ${String(e)}`); }
  report.summary.consoleErrors+=rec.consoleErrors.length; report.summary.pageErrors+=rec.pageErrors.length; report.summary.requestFailures+=rec.requestFailures.length; report.summary.httpErrors+=rec.httpErrors.length;
  report.viewports.push(rec); await page.close();
}
await browser.close(); report.finishedAt=new Date().toISOString();
report.pass=Object.values(report.summary).every(n=>n===0);
fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify(report,null,2));
const owned=['browser-report.json',...report.viewports.map(x=>x.screenshot && path.basename(x.screenshot)).filter(Boolean)];
fs.writeFileSync(path.join(out,'.harness-owned-files.json'),JSON.stringify({schemaVersion:1,files:owned},null,2));
console.log(JSON.stringify(report,null,2)); process.exit(report.pass?0:1);
