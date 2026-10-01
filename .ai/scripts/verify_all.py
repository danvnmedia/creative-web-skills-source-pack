#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, shlex, shutil, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
from _common import (
    catalog_runner_for_check, configure_utf8_stdio, derive_required_checks, harness_context,
    harness_version, load_check_catalog, load_json, platform_id, resolve_task, root_from_script,
)
ROOT=root_from_script(); PY=sys.executable

def run(cmd:list[str])->int:
    p=subprocess.run(cmd,cwd=str(ROOT),text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.stdout: print(p.stdout,end='')
    return p.returncode

def expand_command(runner:dict, task_id:str|None)->list[str]:
    out=[]
    for token in runner.get('command') or []:
        token=str(token).replace('{python}',PY).replace('{task}',task_id or '')
        out.append(token)
    return out

def project_command(check:str, catalog:dict)->list[str]|None:
    spec=(catalog.get('project_checks') or {}).get(check)
    if not spec: return None
    commands=(load_json(ROOT/'.ai/COMMANDS.json').get('commands') or {})
    for key in spec.get('command_keys',[]):
        text=commands.get(key)
        if text:
            parts=shlex.split(str(text),posix=(os.name!='nt'))
            if parts and shutil.which(parts[0]): parts[0]=shutil.which(parts[0]) or parts[0]
            return parts
    return None

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description='Run Harness verification from the declarative check catalog, deduplicating shared regression runners.')
    ap.add_argument('--profile',choices=['native','portable','audited'],default='native')
    ap.add_argument('--task'); ap.add_argument('--record-evidence',action='store_true'); ap.add_argument('--explain',action='store_true')
    ap.add_argument('--allow-local-snapshot',action='store_true')
    args=ap.parse_args(); context=harness_context(ROOT); platform=platform_id(); catalog=load_check_catalog(ROOT)
    if context not in {'source','installed','legacy-installed'}:
        raise SystemExit('VERIFY ALL: FAIL — cannot identify source or installed Harness context')
    print(f'Codex Product Harness {harness_version(ROOT) or "unknown"} verify-all — context={context} profile={args.profile} platform={platform}')
    task=None; task_id=None; required=set(); failures=[]; pending=[]; unavailable=[]
    if args.task:
        try: _,task=resolve_task(ROOT,args.task); task_id=str(task['id'])
        except ValueError as exc: raise SystemExit(f'VERIFY ALL: FAIL — {exc}')
        rc=run([PY,'.ai/scripts/validate_task.py','--task',task_id])
        if rc: failures.append('task-contract')
        quality=load_json(ROOT/'.ai/QUALITY.json'); required=derive_required_checks(task,quality)
        required.update(quality.get('profile_required_checks',{}).get(args.profile,[]))
        if args.profile=='audited' or str(task.get('mode') or '').upper()=='CRITICAL' or (task.get('traits') or {}).get('production_release'):
            rc=run([PY,'.ai/scripts/candidate_preflight.py','--task',task_id])
            if rc and not args.allow_local_snapshot: failures.append('candidate-preflight')
    elif args.record_evidence:
        raise SystemExit('VERIFY ALL: FAIL — --record-evidence requires --task')

    # Map required checks before always-runners so required core checks are not executed twice.
    runner_for_required={}
    for check in sorted(required):
        ext=(catalog.get('external_checks') or {}).get(check)
        if ext:
            pending.append((check,ext.get('reason','requires external/runtime evidence'))); continue
        runner=catalog_runner_for_check(ROOT,check,context,platform)
        if runner and runner.get('command'):
            runner_for_required[check]=runner; continue
        if (catalog.get('project_checks') or {}).get(check):
            if project_command(check,catalog): runner_for_required[check]=None
            else: unavailable.append((check,'no observed/verified project command mapping'))
            continue
        unavailable.append((check,'no CHECK_CATALOG or project-command mapping'))

    # Always-run control-plane checks. Defer a runner if task evidence will record it below.
    deferred_ids={r.get('id') for r in runner_for_required.values() if r and args.record_evidence}
    for runner in catalog.get('runners',[]):
        if not runner.get('always') or runner.get('id') in deferred_ids: continue
        if context not in (runner.get('contexts') or []) or platform not in (runner.get('platforms') or []): continue
        cmd=expand_command(runner,task_id)
        if not cmd: continue
        print(f"\n== {runner['id']} ==")
        if run(cmd): failures.append(runner['id'])

    # Execute each catalog runner once even if it satisfies several required checks.
    grouped={}
    for check,runner in runner_for_required.items():
        if runner: grouped.setdefault(runner['id'],runner)
    for rid,runner in grouped.items():
        cmd=expand_command(runner,task_id)
        print(f"\n== {rid}: {', '.join(x for x in runner.get('checks',[]) if x in required)} ==")
        if args.record_evidence:
            rec=[PY,'.ai/scripts/record_evidence.py','--task',task_id,'--check',str(runner['primary_check']),'--catalog-runner',rid,'--',*cmd]
            rc=run(rec)
        else: rc=run(cmd)
        if rc: failures.append(rid)

    # Project checks are inherently per-project and are recorded under their exact check id.
    for check,runner in runner_for_required.items():
        if runner is not None: continue
        cmd=project_command(check,catalog)
        if not cmd: continue
        print(f'\n== project:{check} ==')
        rc=run([PY,'.ai/scripts/record_evidence.py','--task',task_id,'--check',check,'--',*cmd] if args.record_evidence else cmd)
        if rc: failures.append(check)

    if args.explain:
        print('\nCHECK RESOLUTION')
        for check in sorted(required):
            if any(x[0]==check for x in pending): state='EXTERNAL_PENDING'
            elif any(x[0]==check for x in unavailable): state='UNAVAILABLE'
            elif check in runner_for_required and runner_for_required[check]: state='CATALOG:'+runner_for_required[check]['id']
            elif check in runner_for_required: state='PROJECT_COMMAND'
            else: state='UNKNOWN'
            print(f'- {check}: {state}')
    for check,reason in pending: print(f'[EXTERNAL_PENDING] {check}: {reason}')
    for check,reason in unavailable: print(f'[UNAVAILABLE] {check}: {reason}')
    if failures:
        print('\nVERIFY ALL: FAIL — '+', '.join(sorted(set(failures)))); raise SystemExit(1)
    if unavailable:
        print('\nVERIFY ALL: INCOMPLETE — required checks lack trusted command mapping'); raise SystemExit(2)
    if pending:
        print('\nVERIFY ALL: LOCAL COMPLETE — external/runtime checks remain pending'); return
    print('\nVERIFY ALL: PASS')
if __name__=='__main__': main()
