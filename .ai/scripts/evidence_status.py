#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
sys.dont_write_bytecode=True
from _common import configure_utf8_stdio, load_events, resolve_task, root_from_script, task_contract_digest, validate_closure, workspace_fingerprint

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description='Show candidate-aware evidence with optional stale explanations.')
    ap.add_argument('--task'); ap.add_argument('--current-only',action='store_true'); ap.add_argument('--history',action='store_true'); ap.add_argument('--failures',action='store_true'); ap.add_argument('--json',action='store_true'); ap.add_argument('--explain-stale',action='store_true'); args=ap.parse_args()
    root=root_from_script(); current=workspace_fingerprint(root); target=current; closure_active=False; task_filter=args.task; contract=None
    if args.task:
        try:
            task_path,task=resolve_task(root,args.task); task_filter=task.get('id'); contract=task_contract_digest(task)
            closure,errors=validate_closure(root,task_path,task)
            if errors and not args.json: print('closure invalid: '+'; '.join(errors))
            elif closure: target=closure.get('candidate_fingerprint',target); closure_active=True
        except ValueError as exc:
            raise SystemExit(f'EVIDENCE STATUS: FAIL — {exc}')
    events=[e for e in load_events(root/'.ai/evidence/events.jsonl') if not task_filter or e.get('task')==task_filter]
    if args.failures: events=[e for e in events if e.get('status')!='pass']
    if not args.history:
        latest={}
        for e in events: latest[(e.get('task'),e.get('check'))]=e
        events=list(latest.values())
    rows=[]
    for e in sorted(events,key=lambda x:(str(x.get('task')),str(x.get('check')),str(x.get('timestamp')))):
        expected=current if closure_active and str(e.get('check','')).startswith('production-') else target
        source_ok=e.get('fingerprint_after')==expected
        contract_ok=(contract is None or e.get('task_contract_digest') in (None,contract))
        fresh=source_ok and contract_ok
        if args.current_only and not fresh: continue
        reason=[]
        if not source_ok: reason.append('product source digest changed')
        if not contract_ok: reason.append('task contract digest changed')
        rows.append({'task':e.get('task'),'check':e.get('check'),'status':e.get('status'),'fresh':fresh,'timestamp':e.get('timestamp'),'stale_reason':reason,'event_id':e.get('event_id')})
    if args.json: print(json.dumps({'rows':rows},indent=2,ensure_ascii=False)); return
    if not rows: print('no evidence'); return
    for r in rows:
        extra=(' :: '+'; '.join(r['stale_reason'])) if args.explain_stale and r['stale_reason'] else ''
        print(f"{r['task']} :: {r['check']} :: {r['status']} :: {'FRESH' if r['fresh'] else 'STALE'} :: {r['timestamp']}{extra}")
if __name__=='__main__': main()
