#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import uuid
from pathlib import Path
import sys
sys.dont_write_bytecode = True

from _common import (
    configure_utf8_stdio, dump_json, evidence_event_id, git_info, load_events,
    load_json, resolve_task, root_from_script, workspace_fingerprint, task_contract_digest, lifecycle_state_digest,
)


def checkpoint_path(root: Path, task_id: str) -> Path:
    return root/'.ai/checkpoints'/f'{task_id}.json'


def promotable_pass(event: dict, task_id: str, check: str, fingerprint: str, contract_digest: str | None = None) -> bool:
    if event.get('task') != task_id or event.get('check') != check: return False
    if event.get('status') != 'pass' or event.get('fingerprint_after') != fingerprint: return False
    if contract_digest and event.get('task_contract_digest') not in (None, contract_digest): return False
    # Legacy evidence already recorded command_exit_code. Missing producer_exit_status is accepted
    # only when the original command_exit_code proves success.
    command_exit=event.get('command_exit_code')
    producer_exit=event.get('producer_exit_status', command_exit)
    if command_exit not in (0, None) or producer_exit not in (0, None): return False
    if event.get('tool_pair_state','closed') != 'closed': return False
    return True


def latest_fresh_pass(events: list[dict], task_id: str, check: str, fingerprint: str, contract_digest: str | None = None) -> dict | None:
    rows=[e for e in events if promotable_pass(e,task_id,check,fingerprint,contract_digest)]
    return rows[-1] if rows else None


def unresolved_refs(events: list[dict], task_id: str, limit: int=20) -> list[dict]:
    rows=[]
    for e in events:
        if e.get('task') != task_id or e.get('status') == 'pass': continue
        rows.append({
            'event_id':evidence_event_id(e),'check':e.get('check'),'status':e.get('status'),
            'command_exit_code':e.get('command_exit_code'),'output_digest':e.get('output_digest'),
            'log_path':e.get('log') or e.get('log_path'),
        })
    return rows[-limit:]


def validate_doc(root: Path, task_id: str, doc: dict) -> list[str]:
    errors=[]
    if doc.get('task') != task_id: errors.append('checkpoint task id mismatch')
    current=workspace_fingerprint(root)
    _, task_doc = resolve_task(root, task_id)
    current_contract = task_contract_digest(task_doc)
    if doc.get('workspace_fingerprint') != current: errors.append('checkpoint source fingerprint is stale')
    if doc.get('task_contract_digest') not in (None, current_contract): errors.append('checkpoint task contract is stale')
    policy=load_json(root/'.ai/COMPACTION_POLICY.json') if (root/'.ai/COMPACTION_POLICY.json').is_file() else {'allowed_boundary_capture':['manual','instruction_driven','host_hook']}
    if doc.get('boundary_capture','manual') not in set(policy.get('allowed_boundary_capture',[])):
        errors.append('checkpoint boundary_capture is invalid')
    events=load_events(root/'.ai/evidence/events.jsonl')
    valid_event_ids=set()
    for ref in doc.get('evidence',[]):
        check=ref.get('check')
        event=latest_fresh_pass(events,task_id,check,current,current_contract) if check else None
        if not event:
            errors.append(f'evidence no longer fresh/passing/promotable: {check}')
            continue
        eid=evidence_event_id(event); valid_event_ids.add(eid)
        if ref.get('event_id') and ref.get('event_id') != eid: errors.append(f'evidence event changed: {check}')
        if ref.get('output_digest') and ref.get('output_digest') != event.get('output_digest'): errors.append(f'evidence digest changed: {check}')
        if ref.get('producer_exit_status',0) not in (0,None): errors.append(f'evidence producer exit was nonzero: {check}')
        if ref.get('tool_pair_state','closed') != 'closed': errors.append(f'evidence tool pair is not closed: {check}')
    claims=doc.get('claims')
    if claims is None:
        # v5.3-v5.4.3 checkpoint compatibility. Legacy completed rows are still bound to
        # the fresh passing evidence list above and are never inferred from stdout.
        claims=[{'claim_id':f'legacy-{i+1}','text':x,'claim_status':'verified','source_event_ids':list(valid_event_ids)} for i,x in enumerate(doc.get('completed',[]))]
    for claim in claims:
        cid=str(claim.get('claim_id') or '<missing>')
        if claim.get('claim_status') != 'verified': errors.append(f'checkpoint claim is not verified: {cid}')
        text=str(claim.get('text') or '').strip()
        if not text: errors.append(f'checkpoint claim text is empty: {cid}')
        sources=set(claim.get('source_event_ids') or [])
        if not sources: errors.append(f'checkpoint claim has no source_event_ids: {cid}')
        elif not sources.issubset(valid_event_ids): errors.append(f'checkpoint claim references unverified/stale event: {cid}')
        if any(x not in (0,None) for x in (claim.get('producer_exit_statuses') or [])):
            errors.append(f'checkpoint claim includes nonzero producer exit: {cid}')
        if claim.get('tool_pair_state','closed') != 'closed': errors.append(f'checkpoint claim has open tool-call/result pair: {cid}')
    if not claims: errors.append('checkpoint contains no verified completed milestone')
    if not str(doc.get('next_action') or '').strip(): errors.append('checkpoint next_action is empty')
    return errors


def main() -> None:
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description='Persist only verified progress across session/model/context boundaries.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('checkpoint'); p.add_argument('--task'); p.add_argument('--completed',action='append',required=True); p.add_argument('--next-action',required=True); p.add_argument('--check',action='append',required=True); p.add_argument('--note',action='append',default=[]); p.add_argument('--boundary-capture',choices=['manual','instruction_driven','host_hook'],default='manual'); p.add_argument('--update-state',action='store_true'); p.add_argument('--update-resume',action='store_true')
    v=sub.add_parser('validate'); v.add_argument('--task')
    r=sub.add_parser('resume'); r.add_argument('--task')
    args=ap.parse_args(); root=root_from_script()
    try: _,task=resolve_task(root,getattr(args,'task',None))
    except ValueError as exc: print(f'VERIFIED CHECKPOINT: FAIL - {exc}'); raise SystemExit(1)
    task_id=str(task.get('id') or ''); path=checkpoint_path(root,task_id)
    if args.cmd=='checkpoint':
        fp=workspace_fingerprint(root); contract=task_contract_digest(task); events=load_events(root/'.ai/evidence/events.jsonl'); refs=[]; missing=[]
        for check in dict.fromkeys(args.check):
            event=latest_fresh_pass(events,task_id,check,fp,contract)
            if not event: missing.append(check); continue
            refs.append({'event_id':evidence_event_id(event),'check':check,'timestamp':event.get('timestamp'),'output_digest':event.get('output_digest'),'log_path':event.get('log_path') or event.get('log'),'producer_exit_status':event.get('producer_exit_status',event.get('command_exit_code')),'tool_pair_state':event.get('tool_pair_state','closed')})
        if missing: print('VERIFIED CHECKPOINT: FAIL - missing fresh passing promotable evidence: '+', '.join(missing)); raise SystemExit(1)
        source_ids=[x['event_id'] for x in refs]; gi=git_info(root)
        completed=[str(x).strip() for x in args.completed if str(x).strip()]
        claims=[{'claim_id':f'claim-{i+1:03d}','text':text,'claim_status':'verified','source_event_ids':source_ids,'evidence_checks':[x['check'] for x in refs],'producer_exit_statuses':[x.get('producer_exit_status') for x in refs],'tool_pair_state':'closed','verification_revision':gi.get('sha')} for i,text in enumerate(completed)]
        doc={'schema_version':2,'task':task_id,'created_at':datetime.now(timezone.utc).isoformat(),'workspace_fingerprint':fp,'product_source_digest':fp,'task_contract_digest':contract,'lifecycle_state_digest':lifecycle_state_digest(root,task),'boundary_capture':args.boundary_capture,'completed':completed,'claims':claims,'next_action':args.next_action.strip(),'evidence':refs,'failed_or_rejected_evidence':unresolved_refs(events,task_id),'notes':[str(x).strip() for x in args.note if str(x).strip()],'privacy':'observable facts only; no hidden reasoning/full chat/secrets/provider session objects'}
        if not claims: print('VERIFIED CHECKPOINT: FAIL - completed milestone is empty'); raise SystemExit(1)
        touched=[path]
        if args.update_state: touched.append(root/'.ai/STATE.json')
        if args.update_resume: touched.append(root/'.ai/RESUME.md')
        backups={p:(p.read_bytes() if p.exists() else None) for p in touched}
        try:
            dump_json(path,doc)
            if args.update_state:
                state=load_json(root/'.ai/STATE.json'); state['active_task']=(root/'.ai/tasks'/f'{task_id}.json').relative_to(root).as_posix(); state['status']='IN_PROGRESS'; state['last_verified_fingerprint']=fp; state['last_verified_at']=doc['created_at']; dump_json(root/'.ai/STATE.json',state)
            if args.update_resume:
                resume=root/'.ai/RESUME.md'; text=f'# Resume — {task_id}\n\nVerified at: {doc["created_at"]}\n\nCompleted:\n'+''.join(f'- {x}\n' for x in completed)+f'\nNext action:\n- {args.next_action.strip()}\n'; tmp=resume.with_name(resume.name+f'.tmp-{uuid.uuid4().hex}'); tmp.write_text(text,encoding='utf-8',newline='\n'); os.replace(tmp,resume)
        except Exception:
            for target,data in backups.items():
                if data is None:
                    try: target.unlink()
                    except OSError: pass
                else:
                    target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data)
            raise
        print(f'VERIFIED CHECKPOINT: PASS - {path.relative_to(root).as_posix()}'); return
    if not path.is_file(): print(f'VERIFIED CHECKPOINT: FAIL - missing {path.relative_to(root).as_posix()}'); raise SystemExit(1)
    doc=json.loads(path.read_text(encoding='utf-8')); errors=validate_doc(root,task_id,doc)
    if errors:
        print('VERIFIED CHECKPOINT: FAIL'); [print(f'- {e}') for e in errors]; raise SystemExit(1)
    if args.cmd=='validate': print(f'VERIFIED CHECKPOINT: PASS - {task_id}')
    else:
        payload={'task':task_id,'completed':[c.get('text') for c in (doc.get('claims') or [])] or doc.get('completed',[]),'next_action':doc.get('next_action'),'evidence':[item.get('check') for item in doc.get('evidence',[])],'notes':doc.get('notes',[]),'workspace_fingerprint':doc.get('workspace_fingerprint'),'boundary_capture':doc.get('boundary_capture','manual')}
        print(json.dumps(payload,indent=2,ensure_ascii=False))

if __name__=='__main__': main()
