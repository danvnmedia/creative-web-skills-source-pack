#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
sys.dont_write_bytecode=True
from _common import CHECK_ID_RE, TASK_ID_RE, configure_utf8_stdio, resolve_task, root_from_script

ALLOWED_STATUS={'DRAFT','READY','IN_PROGRESS','LOCALLY_ACCEPTED','COMPLETE','EXTERNALLY_PENDING','BLOCKED','CANCELLED'}
# The shipped schema is the single mode-enum authority. No permissive fallback.
_SCHEMA = json.loads((Path(__file__).resolve().parents[1] / 'schemas/task.schema.json').read_text(encoding='utf-8'))
ALLOWED_MODES=set(_SCHEMA['properties']['mode']['enum'])

def errors_for(task:dict)->list[str]:
    errors=[]
    schema=int(task.get('schema_version') or 0)
    if schema not in {5,6}: errors.append('schema_version must be 5 (legacy) or 6')
    tid=str(task.get('id') or '')
    if not TASK_ID_RE.fullmatch(tid): errors.append('id is invalid')
    if schema>=6:
        if task.get('status') not in ALLOWED_STATUS: errors.append('status enum invalid')
        if 'mode' in task and (not isinstance(task.get('mode'),str) or task['mode'] not in ALLOWED_MODES): errors.append('mode enum invalid; allowed: '+', '.join(sorted(ALLOWED_MODES))+'; PATCH is described as BUGFIX, PRODUCT as FEATURE or AUDIT according to the actual task')
        if not isinstance(task.get('traits'),dict): errors.append('traits must be object')
        ver=task.get('verification')
        if not isinstance(ver,dict): errors.append('verification must be object')
        else:
            checks=ver.get('required_checks',[])
            if not isinstance(checks,list) or any(not isinstance(x,str) or not CHECK_ID_RE.fullmatch(x) for x in checks): errors.append('verification.required_checks contains invalid check id')
            findings=ver.get('findings',[])
            if not isinstance(findings,list): errors.append('verification.findings must be array')
            else:
                ids=set()
                for i,item in enumerate(findings):
                    if not isinstance(item,dict): errors.append(f'finding[{i}] must be object'); continue
                    fid=str(item.get('id') or '')
                    if not fid: errors.append(f'finding[{i}].id required')
                    elif fid in ids: errors.append(f'duplicate finding id: {fid}')
                    ids.add(fid)
                    for k in ('check','severity','component','attack_path','evidence_refs'):
                        if k not in item: errors.append(f'finding[{i}].{k} required')
                for i,w in enumerate(ver.get('waivers',[]) or []):
                    if isinstance(w,dict) and w.get('finding_id') and w.get('finding_id') not in ids:
                        errors.append(f'waiver[{i}] references missing finding_id')
            states=ver.get('check_states',{})
            if states is not None and not isinstance(states,dict): errors.append('verification.check_states must be object')
    if 'prompt_context' in task:
        from prompt_brief import validate_context
        errors.extend(validate_context(task['prompt_context']))
    return errors

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description='Validate a task contract. Schema 6 is strict; schema 5 remains readable for migration.')
    ap.add_argument('--task'); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); root=root_from_script()
    try: path,task=resolve_task(root,args.task)
    except ValueError as exc: raise SystemExit(f'TASK VALIDATION: FAIL — {exc}')
    errors=errors_for(task)
    from task_guidance import guidance
    advice=guidance(root,task)
    report={'status':'pass' if not errors else 'fail','task':task.get('id'),'schema_version':task.get('schema_version'),'errors':errors, 'guidance':advice}
    if args.json: print(json.dumps(report,indent=2,ensure_ascii=False))
    else:
        print('TASK VALIDATION: '+report['status'].upper()+f" — {task.get('id')}")
        for e in errors: print('- '+e)
        for w in advice['warnings']: print('[WARN] '+w)
        if advice['recommended_skills']: print('SKILL PREPARATION (not activation evidence): '+', '.join(advice['recommended_skills']))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
