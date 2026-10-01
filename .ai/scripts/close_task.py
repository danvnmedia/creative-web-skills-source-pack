#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
sys.dont_write_bytecode = True

from _common import closure_manifest_path, configure_utf8_stdio, derive_required_checks, dump_json, git_info, load_json, resolve_task, root_from_script, run_capture, git_status_entries, is_runtime_state_path, task_contract_digest, waiver_validation, workspace_fingerprint, product_source_manifest


def main() -> None:
    configure_utf8_stdio()
    parser=argparse.ArgumentParser(description='Close a locally/CI accepted source candidate before deployment.')
    parser.add_argument('--task', help='Task id or path. Defaults to active_task.')
    parser.add_argument('--production-url', help='Optional intended production URL; acceptance still happens after deployment.')
    parser.add_argument('--ci-url', help='Optional candidate CI run URL.')
    parser.add_argument('--snapshot', action='store_true', help='For a non-Git legacy workspace, create a local content-addressed snapshot closure. Never valid for production acceptance.')
    args=parser.parse_args()
    root=root_from_script()
    try:
        task_path, task=resolve_task(root,args.task)
    except ValueError as exc:
        raise SystemExit(f'CLOSE TASK: FAIL — {exc}')
    if task.get('status') == 'COMPLETE' or closure_manifest_path(root, str(task.get('id'))).exists():
        raise SystemExit('CLOSE TASK: FAIL - closure is immutable; create a new successor task for a changed candidate and reference this task. Do not reopen or overwrite its evidence.')
    declared_url=(task.get('release') or {}).get('production_url')
    if args.production_url and declared_url and args.production_url != declared_url:
        raise SystemExit('CLOSE TASK: FAIL - --production-url differs from task.release.production_url; changing the tested environment requires reviewed task changes and fresh evidence, before closure.')
    quality=load_json(root/'.ai/QUALITY.json')
    waivers, waiver_errors=waiver_validation(task)
    if waiver_errors:
        print('CLOSE TASK: FAIL — invalid or stale waiver')
        for error in waiver_errors: print(f'- {error}')
        raise SystemExit(1)
    state_path=root/'.ai/STATE.json'; state=load_json(state_path)
    git=git_info(root)
    if not git.get('is_git') and not args.snapshot:
        raise SystemExit('CLOSE TASK: FAIL — candidate closure requires git. For non-Git local work use explicit --snapshot; local snapshots can never be production-accepted.')
    if git.get('is_git'):
        try: dirty=[rel for _,rel in git_status_entries(root) if not is_runtime_state_path(rel)]
        except (RuntimeError, ValueError) as exc:
            raise SystemExit(f'CLOSE TASK: FAIL - {exc}')
        if dirty:
            print('CLOSE TASK: FAIL - commit product/task changes before closure; only validated runtime state may be dirty')
            print(repr(dirty))
            raise SystemExit(1)
    candidate_sha=str(git.get('sha') or '')
    candidate_fingerprint=workspace_fingerprint(root)
    gate=subprocess.run([sys.executable,'.ai/scripts/evidence_gate.py','--pre-release','--task',str(task.get('id'))],cwd=str(root),text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(gate.stdout,end='')
    if gate.returncode!=0: raise SystemExit('CLOSE TASK: FAIL — candidate evidence gate did not pass')

    production_release=task.get('traits',{}).get('production_release') is True
    release=None
    if production_release:
        print('RELEASE GUIDE: read .agents/skills/release-acceptance/SKILL.md. --production-url is stored in the closure receipt only; the task runtime contract is not rewritten.')
        release={
            'status':'externally_pending',
            'production_url':args.production_url or task.get('release',{}).get('production_url'),
            'candidate_revision':candidate_sha,
            'deployed_revision':None,
            'ci_url':args.ci_url,
        }
    closed_at=dt.datetime.now(dt.timezone.utc).isoformat()
    closure_kind='git' if git.get('is_git') else 'local_snapshot'
    task['status']='COMPLETE' if closure_kind=='git' else 'LOCALLY_ACCEPTED'
    task['closure']={'kind':closure_kind,'candidate_sha':candidate_sha or None,'candidate_fingerprint':candidate_fingerprint,'closed_at':closed_at}
    manifest={
        'version':2,'task':task.get('id'),'closure_kind':closure_kind,'candidate_sha':candidate_sha or None,
        'candidate_fingerprint':candidate_fingerprint,'product_source_digest':candidate_fingerprint,'task_contract_digest':task_contract_digest(task),
        'snapshot_files': product_source_manifest(root) if closure_kind=='local_snapshot' else None,
        'required_checks':sorted(derive_required_checks(task,quality)),
        'waivers':list(waivers.values()),
        'waiver_digests':{check:item.get('waiver_sha256') for check,item in waivers.items()},
        'findings':[x for x in task.get('verification',{}).get('findings',[]) if any(w.get('finding_id')==x.get('id') for w in waivers.values())],
        'closed_at':closed_at,
        'closure_revision':None,'release':release,
    }
    state['active_task']=task_path.relative_to(root).as_posix(); state['status']=task['status']
    state['last_verified_fingerprint']=candidate_fingerprint; state['last_verified_at']=closed_at
    dump_json(task_path,task); dump_json(state_path,state); dump_json(closure_manifest_path(root,str(task.get('id'))),manifest)
    if closure_kind=='local_snapshot': print(f'CLOSE TASK: PASS — LOCAL_SNAPSHOT_ACCEPTED {candidate_fingerprint}')
    else: print(f'CLOSE TASK: PASS — accepted candidate {candidate_sha}')
    if production_release and closure_kind=='local_snapshot':
        print('Production remains EXTERNALLY_PENDING. A local snapshot is not a deployable revision and cannot be production-accepted.')
    elif production_release:
        print('Production remains EXTERNALLY_PENDING. Commit closure paths, deploy that exact revision, record fresh production-smoke + production-critical-flow, then run accept_release.py. Use record_evidence.py --ephemeral ONLY for post-closure read-only revision probes; ephemeral output is NOT persisted evidence for required production checks. See the release-acceptance Skill and .ai/harness/docs/RELEASE_RUNBOOK.md in installed mode.')
    else:
        print('Next: update .ai/RESUME.md, run evidence_gate.py again, and commit only closure-allowed paths.')


if __name__=='__main__': main()
