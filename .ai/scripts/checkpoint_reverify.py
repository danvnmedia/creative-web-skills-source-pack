#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True

from _common import configure_utf8_stdio, load_json, resolve_task, root_from_script
from verified_checkpoint import checkpoint_path, validate_doc


def sha_file(path:Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_summary(summary:dict, doc:dict, cp_hash:str) -> list[str]:
    errors=[]
    if summary.get('task') != doc.get('task'): errors.append('summary task mismatch')
    if summary.get('checkpoint_sha256') != cp_hash: errors.append('summary checkpoint digest is stale')
    if any(k in summary for k in ('claims','facts','verified_facts','completed')):
        errors.append('summary must reference verified claim ids, not carry autonomous verified facts')
    claims={str(c.get('claim_id')):c for c in (doc.get('claims') or []) if c.get('claim_id')}
    ids=summary.get('verified_claim_ids') or []
    if not isinstance(ids,list) or not ids: errors.append('summary verified_claim_ids is empty')
    unknown=[x for x in ids if x not in claims]
    if unknown: errors.append('summary references unknown claim ids: '+', '.join(map(str,unknown)))
    required=set()
    for cid in ids:
        if cid in claims: required.update(claims[cid].get('source_event_ids') or [])
    observed=set(summary.get('source_event_ids') or [])
    if not required.issubset(observed): errors.append('summary source-event coverage is incomplete')
    return errors


def main():
    configure_utf8_stdio(); root=root_from_script(); policy=load_json(root/'.ai/COMPACTION_POLICY.json')
    ap=argparse.ArgumentParser(description='Reverify verified progress after compaction/context refresh and emit a bounded resume digest.')
    ap.add_argument('--task'); ap.add_argument('--summary',help='Optional external compaction summary metadata JSON to validate by references only.')
    args=ap.parse_args()
    try: _,task=resolve_task(root,args.task)
    except ValueError as exc: print(f'CHECKPOINT REVERIFY: FAIL - {exc}'); raise SystemExit(1)
    task_id=str(task.get('id') or ''); path=checkpoint_path(root,task_id)
    if not path.is_file(): print('CHECKPOINT REVERIFY: FAIL - checkpoint missing'); raise SystemExit(1)
    doc=json.loads(path.read_text(encoding='utf-8')); errors=validate_doc(root,task_id,doc); cp_hash=sha_file(path)
    if args.summary:
        try: summary=json.loads(Path(args.summary).read_text(encoding='utf-8'))
        except Exception as exc: errors.append(f'invalid summary metadata: {exc}')
        else: errors.extend(validate_summary(summary,doc,cp_hash))
    if errors:
        print('CHECKPOINT REVERIFY: FAIL'); [print(f'- {e}') for e in errors]; raise SystemExit(1)
    claims=doc.get('claims') or [{'claim_id':f'legacy-{i+1}','text':x,'source_event_ids':[]} for i,x in enumerate(doc.get('completed',[]))]
    payload={'task':task_id,'checkpoint_sha256':cp_hash,'verified_claims':[{'claim_id':c.get('claim_id'),'text':c.get('text')} for c in claims],'next_action':doc.get('next_action'),'boundary_capture':doc.get('boundary_capture','manual'),'source_event_ids':sorted({eid for c in claims for eid in (c.get('source_event_ids') or [])}),'unresolved':[{'check':x.get('check'),'status':x.get('status'),'event_id':x.get('event_id')} for x in doc.get('failed_or_rejected_evidence',[])]}
    rendered=json.dumps(payload,ensure_ascii=False,separators=(',',':'))
    limit=int(policy.get('max_resume_digest_chars',1200))
    if len(rendered)>limit:
        payload['unresolved']=[]; rendered=json.dumps(payload,ensure_ascii=False,separators=(',',':'))
    if len(rendered)>limit:
        print(f'CHECKPOINT REVERIFY: FAIL - bounded resume digest exceeds {limit} characters'); raise SystemExit(1)
    print('CHECKPOINT REVERIFY: PASS')
    print(json.dumps(payload,indent=2,ensure_ascii=False))

if __name__=='__main__': main()
