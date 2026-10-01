#!/usr/bin/env python3
from __future__ import annotations
import copy, datetime as dt, hashlib, json, os, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
from _common import catalog_runner_for_check, check_contract_digest, harness_temp_dir, load_json, runtime_candidate_digest, safe_temp_base
ROOT=Path(__file__).resolve().parents[2]; PY=sys.executable

def run(cmd,cwd,expect=0,env=None):
    child_env=os.environ.copy() if env is None else env.copy(); child_env['PYTHONDONTWRITEBYTECODE']='1'; child_env['PYTHONUTF8']='1'
    p=subprocess.run(cmd,cwd=str(cwd),text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=child_env)
    if p.returncode!=expect: raise SystemExit(f'V5.5.1 REGRESSION: FAIL expected {expect}, got {p.returncode}: {cmd}\n{p.stdout}')
    return p.stdout

def receipt_hash(obj:dict)->str:
    raw=json.dumps({k:v for k,v in obj.items() if k!='receipt_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def main():
    print('[v551] start',flush=True)
    with harness_temp_dir(ROOT,for_copy=True,prefix='v551-') as tmp:
        print('[v551] temp',flush=True)
        # HARNESS_TEMP_DIR is first-class and takes priority over OS temp.
        explicit=tmp/'explicit-temp'; env=os.environ.copy(); env['HARNESS_TEMP_DIR']=str(explicit); env.pop('HARNESS_TMP',None)
        out=run([PY,'-c',"import sys; sys.path.insert(0,'.ai/scripts'); from _common import safe_temp_base,root_from_script; print(safe_temp_base(root_from_script()))"],ROOT,env=env)
        if str(explicit.resolve()) not in out: raise SystemExit('V5.5.1 REGRESSION: FAIL HARNESS_TEMP_DIR precedence')

        print('[v551] fingerprints',flush=True)
        # Runtime-candidate identity changes for source/deployment identity, not unrelated findings/lifecycle prose.
        fp_root=tmp/'fp'; (fp_root/'.ai/evidence').mkdir(parents=True); (fp_root/'app.txt').write_text('A',encoding='utf-8')
        task={'id':'TASK-RUNTIME','release':{'production_url':'https://example.test','candidate_revision':'abc'}}
        d1=runtime_candidate_digest(fp_root,task)
        t2=copy.deepcopy(task); t2['verification']={'findings':[{'summary':'note'}]}; t2['status']='IN_PROGRESS'
        if runtime_candidate_digest(fp_root,t2)!=d1: raise SystemExit('V5.5.1 REGRESSION: FAIL runtime digest coupled to lifecycle/finding prose')
        t3=copy.deepcopy(task); t3['release']['deployment_id']='dpl_123'
        if runtime_candidate_digest(fp_root,t3)==d1: raise SystemExit('V5.5.1 REGRESSION: FAIL deployment identity did not change runtime digest')
        contract_task={'schema_version':6,'id':'TASK-RUNTIME','mode':'FEATURE','objective':'x','verification':{'required_checks':['build','security-negative'],'findings':[],'waivers':[]}}
        build_digest=check_contract_digest(contract_task,'build')
        contract_task['verification']['findings']=[{'id':'F1','check':'security-negative','severity':'high','component':'x','attack_path':'a','evidence_refs':[]}]
        if check_contract_digest(contract_task,'build')!=build_digest: raise SystemExit('V5.5.1 REGRESSION: FAIL unrelated finding staled build contract')
        sec_digest=check_contract_digest(contract_task,'security-negative')
        contract_task['verification']['findings'][0]['severity']='critical'
        if check_contract_digest(contract_task,'security-negative')==sec_digest: raise SystemExit('V5.5.1 REGRESSION: FAIL relevant finding did not stale its check contract')
        (fp_root/'app.txt').write_text('B',encoding='utf-8')
        if runtime_candidate_digest(fp_root,task)==d1: raise SystemExit('V5.5.1 REGRESSION: FAIL source change did not change runtime digest')

        print('[v551] browser',flush=True)
        # Connected browser requires a fresh self-hashed host receipt; env declaration alone is not trusted.
        browser=tmp/'browser'; (browser/'.ai/checkpoints/browser-capabilities').mkdir(parents=True); (browser/'.ai/scripts').mkdir(parents=True)
        (browser/'.ai/BROWSER_CAPABILITY_POLICY.json').write_text(json.dumps({'allow_transient_playwright':False})+'\n',encoding='utf-8')
        now=dt.datetime.now(dt.timezone.utc); rec={'schema_version':1,'executor':'connected-browser','available':True,'issued_at':now.isoformat(),'expires_at':(now+dt.timedelta(minutes=30)).isoformat(),'attested_by':'fixture-host'}; rec['receipt_sha256']=receipt_hash(rec)
        (browser/'.ai/checkpoints/browser-capabilities/host.json').write_text(json.dumps(rec)+'\n',encoding='utf-8')
        sys.path.insert(0,str(ROOT/'.ai/scripts')); from browser_capability import collect
        report=collect(browser)
        if report['selected_executor']!='connected-browser' or report['selected_trust']!='host-receipt': raise SystemExit('V5.5.1 REGRESSION: FAIL connected-browser receipt not selected')
        rec['receipt_sha256']='0'*64; (browser/'.ai/checkpoints/browser-capabilities/host.json').write_text(json.dumps(rec)+'\n',encoding='utf-8')
        old=os.environ.get('HARNESS_HOST_BROWSER'); os.environ['HARNESS_HOST_BROWSER']='1'
        try: report=collect(browser)
        finally:
            if old is None: os.environ.pop('HARNESS_HOST_BROWSER',None)
            else: os.environ['HARNESS_HOST_BROWSER']=old
        if report['selected_executor']=='connected-browser' or not report['connected_browser']['declared_env_only']:
            raise SystemExit('V5.5.1 REGRESSION: FAIL env declaration was trusted as host receipt')

        print('[v551] catalog-dedupe',flush=True)
        # Three quality checks resolve to one declarative runner. Execute the runner once
        # through record_evidence in ephemeral mode and verify shared evidence projection.
        runners={catalog_runner_for_check(ROOT,c,'source','linux').get('id') for c in ('waiver-contract','control-decision-contract','mcp-surface-contract')}
        if runners!={'v542-contracts'}: raise SystemExit(f'V5.5.1 REGRESSION: FAIL catalog did not dedupe v542 checks: {runners}')
        tasks=ROOT/'.ai/tasks'; tasks.mkdir(exist_ok=True); taskp=tasks/'TASK-CATALOG.json'
        taskp.write_text(json.dumps({'id':'TASK-CATALOG','verification':{'required_checks':['waiver-contract','control-decision-contract','mcp-surface-contract'],'findings':[],'waivers':[]},'release':{}},indent=2)+'\n',encoding='utf-8')
        try:
            out=run([PY,'.ai/scripts/record_evidence.py','--task','TASK-CATALOG','--check','waiver-contract','--catalog-runner','v542-contracts','--ephemeral','--',PY,'.ai/scripts/v542_regression_test.py'],ROOT)
            event=json.loads(out)
        finally:
            taskp.unlink(missing_ok=True)
            try: tasks.rmdir()
            except OSError: pass
        if event.get('catalog_runner')!='v542-contracts': raise SystemExit('V5.5.1 REGRESSION: FAIL catalog runner identity missing')
        if set(event.get('satisfies_checks') or [])!={'control-decision-contract','mcp-surface-contract'}:
            raise SystemExit('V5.5.1 REGRESSION: FAIL shared runner evidence projection mismatch')
    print('V5.5.1 REGRESSION: PASS - temp alias/order + runtime candidate digest + browser capability receipts + declarative deduplicated check catalog')
if __name__=='__main__': main()
