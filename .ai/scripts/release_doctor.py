#!/usr/bin/env python3
"""Read-only release identity preflight. Reports observed/local facts, inferred workflow hints, UNKNOWN external state, and one safe next step."""
from __future__ import annotations
import argparse, datetime as dt, json, re, sys
from pathlib import Path
sys.dont_write_bytecode=True
from _common import configure_utf8_stdio, git_info, git_status_entries, is_runtime_state_path, resolve_task, root_from_script, run_capture_full, validate_closure

FULL_SHA=re.compile(r'^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$')
WORKFLOW_PATTERNS={
    'git-commit': re.compile(r'(?i)\bgit\s+commit\b'),
    'npm-version': re.compile(r'(?i)\bnpm\s+version\b'),
    'semantic-release': re.compile(r'(?i)\bsemantic-release\b'),
    'release-please': re.compile(r'(?i)\brelease-please\b'),
    'changesets': re.compile(r'(?i)\bchangeset(?:s)?\b'),
}

def _git_text(root:Path,args:list[str])->str|None:
    rc,out,_=run_capture_full(['git',*args],root)
    return out.strip() if rc==0 and out.strip() else None

def workflow_commit_hints(root:Path)->list[dict]:
    base=root/'.github/workflows'; rows=[]
    if not base.is_dir(): return rows
    for path in sorted([*base.glob('*.yml'),*base.glob('*.yaml')])[:64]:
        try:
            if path.stat().st_size>1_000_000: continue
            text=path.read_text(encoding='utf-8',errors='replace')
        except OSError: continue
        for name,pat in WORKFLOW_PATTERNS.items():
            if pat.search(text):
                rows.append({'path':path.relative_to(root).as_posix(),'signal':name,'authority':'inferred-static-hint','proves_new_commit':False})
    return rows

def build_report(root:Path, task_arg:str|None, target_sha:str|None)->dict:
    task_path,task=resolve_task(root,task_arg)
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    git=git_info(root); head=git.get('sha')
    upstream_ref=_git_text(root,['rev-parse','--symbolic-full-name','@{u}']) if git.get('is_git') else None
    upstream_sha=_git_text(root,['rev-parse','@{u}']) if upstream_ref else None
    dirty=[]
    if git.get('is_git'):
        try: dirty=sorted({rel for _,rel in git_status_entries(root) if not is_runtime_state_path(rel)})
        except Exception as exc: dirty=[f'UNKNOWN:{type(exc).__name__}']
    closure,closure_errors=validate_closure(root,task_path,task)
    release=task.get('release') or {}; production=bool((task.get('traits') or {}).get('production_release'))
    marker=release.get('revision_marker')
    marker_ready=isinstance(marker,str) and bool(marker.strip())
    if target_sha is not None and not FULL_SHA.fullmatch(target_sha):
        raise ValueError('--target-sha must be a full 40/64-character hexadecimal revision')
    target=target_sha or (closure or {}).get('closure_revision') or (closure or {}).get('candidate_sha') or release.get('candidate_revision') or head
    target_trust='user-supplied' if target_sha else 'local-derived'
    manifest_release=(closure or {}).get('release') or {}
    accepted=manifest_release.get('status')=='production_accepted'
    blockers=[]
    if production and not marker_ready: blockers.append('revision_marker_missing')
    if dirty: blockers.append('non_runtime_workspace_changes')
    if closure_errors: blockers.append('closure_invalid')
    if production and not closure: blockers.append('closure_missing')
    if accepted:
        next_action='Release receipt says production_accepted; create a successor task for any changed candidate. Do not infer newer production state from this receipt.'
    elif production and not marker_ready:
        next_action='Define an observable in-app build revision marker before production acceptance; then rerun this doctor. Do not echo an expected SHA as proof.'
    elif dirty:
        next_action='Preserve or isolate unrelated workspace changes before closure. Do not use ignore-dirty or stash as an automatic bypass.'
    elif closure_errors:
        next_action='Resolve closure validation errors before deployment or acceptance.'
    elif production and not closure:
        next_action='Run the candidate evidence gate and close_task for the pinned candidate before deployment.'
    elif production:
        next_action='Verify CI/deployment/alias/in-app marker for the exact closure revision, then record fresh production-smoke and production-critical-flow evidence.'
    else:
        next_action='This task is not a production release; use the normal local completion path.'
    return {
      'schema_version':1,'status':'READY' if not blockers else 'ATTENTION','observed_at_utc':now,
      'task':{'id':task.get('id'),'status':task.get('status'),'production_release':production,'path':task_path.relative_to(root).as_posix()},
      'identity':{
        'target_revision':target,'target_revision_authority':target_trust,
        'candidate_revision':(closure or {}).get('candidate_sha') or release.get('candidate_revision'),
        'closure_revision':(closure or {}).get('closure_revision'),
        'local_head':head,'local_branch':git.get('branch'),'upstream_ref':upstream_ref,'local_upstream_ref_sha':upstream_sha,
        'upstream_freshness':'UNKNOWN-no-fetch-performed',
        'deployed_revision':manifest_release.get('deployed_revision'),'deployment_status':manifest_release.get('status') or 'UNKNOWN',
        'production_url':manifest_release.get('production_url') or release.get('production_url'),
        'revision_marker':marker,'revision_marker_ready':marker_ready,
        'alias_revision':'UNKNOWN-provider-not-queried','ci_revision':'UNKNOWN-provider-not-queried'
      },
      'closure':{'present':bool(closure),'errors':closure_errors},
      'workspace':{'non_runtime_dirty_paths':dirty,'clean_for_closure':not dirty},
      'workflow_commit_hints':workflow_commit_hints(root),
      'limits':[
        'No git fetch, CI-provider query, deployment-provider query, alias mutation, push, deploy, promotion, or task mutation was performed.',
        'Workflow commit hints are lexical/inferred only; they do not prove a workflow will create a commit.',
        'A local upstream ref may be stale because doctor intentionally does not fetch.'
      ],
      'blockers':blockers,'next_safe_action':next_action
    }

def main()->None:
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--task'); ap.add_argument('--target-sha'); ap.add_argument('--json',action='store_true')
    args=ap.parse_args(); root=root_from_script()
    try: report=build_report(root,args.task,args.target_sha)
    except (ValueError,OSError,KeyError) as exc: raise SystemExit('RELEASE DOCTOR: FAIL — '+str(exc))
    if args.json: print(json.dumps(report,indent=2,ensure_ascii=False)); return
    ident=report['identity']; print('RELEASE DOCTOR:',report['status'])
    print(f"task={report['task']['id']} production_release={report['task']['production_release']} target={ident['target_revision'] or 'UNKNOWN'}")
    print(f"HEAD={ident['local_head'] or 'UNKNOWN'} upstream={ident['local_upstream_ref_sha'] or 'UNKNOWN'} ({ident['upstream_freshness']})")
    print(f"closure={ident['closure_revision'] or ident['candidate_revision'] or 'UNKNOWN'} deployed={ident['deployed_revision'] or 'UNKNOWN'} alias={ident['alias_revision']}")
    print(f"revision_marker={'READY' if ident['revision_marker_ready'] else 'MISSING'} ci={ident['ci_revision']}")
    if report['workflow_commit_hints']: print('workflow_commit_hint=' + ','.join(sorted({x['signal'] for x in report['workflow_commit_hints']})) + ' (INFERRED, not proof)')
    for b in report['blockers']: print('BLOCKER:',b)
    print('NEXT:',report['next_safe_action'])
if __name__=='__main__': main()
