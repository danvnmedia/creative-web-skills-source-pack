#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, sys
sys.dont_write_bytecode=True
from _common import configure_utf8_stdio, dump_json, resolve_task, root_from_script
from validate_task import ALLOWED_STATUS, errors_for

ALLOWED={
'DRAFT':{'READY','CANCELLED'},'READY':{'IN_PROGRESS','CANCELLED','BLOCKED'},'IN_PROGRESS':{'BLOCKED','LOCALLY_ACCEPTED','COMPLETE','EXTERNALLY_PENDING','CANCELLED'},
'BLOCKED':{'IN_PROGRESS','CANCELLED'},'LOCALLY_ACCEPTED':{'IN_PROGRESS','COMPLETE','EXTERNALLY_PENDING'},'EXTERNALLY_PENDING':{'IN_PROGRESS','COMPLETE','BLOCKED'},'COMPLETE':set(),'CANCELLED':set(),
}
def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description='Apply a validated task lifecycle transition without editing JSON by hand.')
    ap.add_argument('--task'); ap.add_argument('--to',required=True,choices=sorted(ALLOWED_STATUS)); ap.add_argument('--reason'); args=ap.parse_args(); root=root_from_script()
    try: path,task=resolve_task(root,args.task)
    except ValueError as exc: raise SystemExit(f'TASK TRANSITION: FAIL — {exc}')
    errs=errors_for(task)
    if errs: raise SystemExit('TASK TRANSITION: FAIL — invalid task: '+'; '.join(errs))
    old=str(task.get('status') or 'DRAFT')
    if args.to!=old and args.to not in ALLOWED.get(old,set()): raise SystemExit(f'TASK TRANSITION: FAIL — {old} -> {args.to} is not allowed; COMPLETE/CANCELLED are terminal. Create a new task for a changed candidate and reference the prior task; preserve its closure/evidence.')
    task['status']=args.to; task['lifecycle']={**(task.get('lifecycle') or {}),'updated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'last_transition':{'from':old,'to':args.to,'reason':args.reason}}
    dump_json(path,task); print(f'TASK TRANSITION: PASS — {task.get("id")} {old} -> {args.to}')
if __name__=='__main__': main()
