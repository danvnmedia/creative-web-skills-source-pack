#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
sys.dont_write_bytecode=True
from _common import configure_utf8_stdio, git_info, resolve_task, root_from_script

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description='Fail early when a task expects candidate closure but immutable candidate identity is unavailable.')
    ap.add_argument('--task'); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); root=root_from_script()
    try: _,task=resolve_task(root,args.task)
    except ValueError as exc: raise SystemExit(f'CANDIDATE PREFLIGHT: FAIL — {exc}')
    gi=git_info(root); profile=str((task.get('execution_contract') or {}).get('resolved_profile') or (task.get('execution_contract') or {}).get('profile') or 'native').lower()
    critical=str(task.get('mode') or '').upper()=='CRITICAL'; production=bool((task.get('traits') or {}).get('production_release'))
    requires=profile=='audited' or critical or production
    state='pass'; message='git candidate identity available' if gi.get('is_git') else 'no git candidate identity'
    if requires and not gi.get('is_git'): state='blocked'; message='audited/critical/production candidate closure requires Git, or explicit local snapshot closure that cannot be production-accepted'
    report={'status':state,'task':task.get('id'),'profile':profile,'requires_candidate_identity':requires,'git':gi,'message':message}
    if args.json: print(json.dumps(report,indent=2,ensure_ascii=False))
    else: print(('CANDIDATE PREFLIGHT: PASS' if state=='pass' else 'CANDIDATE PREFLIGHT: BLOCKED')+' — '+message)
    if state!='pass': raise SystemExit(2)
if __name__=='__main__': main()
