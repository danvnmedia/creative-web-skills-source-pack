#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from _common import load_events, root_from_script

ROOT=root_from_script()


def main():
    ap=argparse.ArgumentParser(description='Detect repeated identical verification failures and stop blind retry loops.')
    ap.add_argument('--task',required=True); ap.add_argument('--check'); ap.add_argument('--json',action='store_true')
    args=ap.parse_args()
    budget=json.loads((ROOT/'.ai/RUNTIME_BUDGET.json').read_text(encoding='utf-8'))['evidence']
    events=[e for e in load_events(ROOT/'.ai/evidence/events.jsonl') if e.get('task')==args.task and not e.get('ephemeral')]
    if args.check: events=[e for e in events if e.get('check')==args.check]
    failures=[e for e in events if e.get('status')!='pass']
    repeat=0; signature=None
    for e in reversed(events):
        if e.get('status')=='pass': break
        sig=e.get('failure_signature')
        if not sig: break
        if signature is None: signature=sig
        if sig!=signature: break
        repeat+=1
    attempts_by_check={}
    for e in events: attempts_by_check[e.get('check')]=attempts_by_check.get(e.get('check'),0)+1
    over_attempts={k:v for k,v in attempts_by_check.items() if v>=budget.get('max_attempts_per_check',6)}
    stop=repeat>=budget.get('same_failure_stop_after',3) or bool(over_attempts)
    report={'schema_version':1,'task':args.task,'check':args.check,'consecutive_same_failure':repeat,'attempts_by_check':attempts_by_check,'over_attempt_budget':over_attempts,'stop_repeating':stop,'next_action':'Use systematic-debugging: change hypothesis or gather new evidence before retry.' if stop else 'Retry only if the next attempt tests a changed hypothesis.'}
    if args.json: print(json.dumps(report,indent=2,ensure_ascii=False))
    else:
        print('LOOP GUARD: '+('STOP' if stop else 'OK'))
        print(json.dumps(report,indent=2,ensure_ascii=False))
    if stop: raise SystemExit(2)

if __name__=='__main__': main()
