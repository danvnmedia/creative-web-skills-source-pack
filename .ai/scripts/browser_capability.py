#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, shutil, sys
from pathlib import Path
sys.dont_write_bytecode=True
from _common import load_json, root_from_script
ROOT=root_from_script()

def _parse_time(value:str|None):
    if not value: return None
    try: return dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    except Exception: return None

def _receipt_hash(obj:dict)->str:
    copy={k:v for k,v in obj.items() if k!='receipt_sha256'}
    raw=json.dumps(copy,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def _connected_receipts(root:Path)->list[dict]:
    out=[]; now=dt.datetime.now(dt.timezone.utc); base=root/'.ai/checkpoints/browser-capabilities'
    if not base.is_dir(): return out
    for p in sorted(base.glob('*.json')):
        try: obj=load_json(p)
        except Exception: continue
        required={'schema_version','executor','available','issued_at','expires_at','attested_by','receipt_sha256'}
        valid=required.issubset(obj) and obj.get('executor')=='connected-browser' and obj.get('available') is True
        exp=_parse_time(obj.get('expires_at')); issued=_parse_time(obj.get('issued_at'))
        valid=bool(valid and exp and issued and exp>now and obj.get('receipt_sha256')==_receipt_hash(obj))
        out.append({'path':p.relative_to(root).as_posix(),'valid':valid,'attested_by':obj.get('attested_by'),'expires_at':obj.get('expires_at')})
    return out

def collect(root:Path=ROOT)->dict:
    policy_path=root/'.ai/BROWSER_CAPABILITY_POLICY.json'
    policy=load_json(policy_path) if policy_path.is_file() else {'allow_transient_playwright':False}
    pkg=root/'package.json'; deps={}
    if pkg.is_file():
        try:
            data=load_json(pkg); deps={**(data.get('dependencies') or {}),**(data.get('devDependencies') or {})}
        except Exception: pass
    receipts=_connected_receipts(root); connected=any(r['valid'] for r in receipts)
    local=('playwright' in deps or '@playwright/test' in deps)
    transient=bool(policy.get('allow_transient_playwright') and shutil.which('npx'))
    declared=bool(os.environ.get('HARNESS_HOST_BROWSER'))
    borrowed=any((root/'.ai/checkpoints').glob('**/*browser*lease*.json')) if (root/'.ai/checkpoints').exists() else False
    if connected: selected='connected-browser'; trust='host-receipt'
    elif local: selected='project-local-playwright'; trust='observed'
    elif transient: selected='approved-transient-playwright'; trust='policy-approved-launcher'
    else: selected='unavailable'; trust='none'
    return {
      'schema_version':1,'selected_executor':selected,'selected_trust':trust,
      'connected_browser':{'available':connected,'receipts':receipts,'declared_env_only':declared},
      'project_local_playwright':{'available':local,'reproducible':local},
      'approved_transient_playwright':{'available':transient,'policy_enabled':bool(policy.get('allow_transient_playwright')),'npx_available':bool(shutil.which('npx'))},
      'harness_browser_scripts':{'available':(root/'.ai/scripts/browser_smoke.mjs').is_file() and (root/'.ai/scripts/browser_flow.mjs').is_file()},
      'borrowed_browser_session':{'lease_present':borrowed},
      'reason':None if selected!='unavailable' else 'no valid connected-browser receipt, no project-local Playwright, and transient executor is not approved/available'
    }

def main():
    ap=argparse.ArgumentParser(description='Report browser verification capability without conflating project reproducibility and host runtime access.')
    ap.add_argument('--json',action='store_true'); args=ap.parse_args(); report=collect(ROOT)
    if args.json: print(json.dumps(report,indent=2,ensure_ascii=False))
    else:
        print('BROWSER CAPABILITY: '+report['selected_executor']+f" (trust={report['selected_trust']})")
        print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
