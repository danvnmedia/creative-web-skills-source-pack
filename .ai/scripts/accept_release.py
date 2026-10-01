#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
sys.dont_write_bytecode = True

from _common import closure_manifest_path, configure_utf8_stdio, dump_json, git_info, load_events, resolve_task, root_from_script, validate_closure, workspace_fingerprint


def revision_matches(expected: str, actual: str) -> bool:
    if not isinstance(expected,str) or not isinstance(actual,str): return False
    if not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})',expected): return False
    if not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})',actual): return False
    return expected.lower() == actual.lower()


def observed_revision_marker(expected: str, output: str) -> bool:
    if not revision_matches(expected,expected): return False
    return re.search(r'(?<![0-9a-fA-F])'+re.escape(expected)+r'(?![0-9a-fA-F])',output,re.IGNORECASE) is not None


def main() -> None:
    configure_utf8_stdio()
    parser=argparse.ArgumentParser(description='Accept an exact deployed revision after production smoke and critical-flow evidence pass.')
    parser.add_argument('--task'); parser.add_argument('--production-url',required=True)
    parser.add_argument('--deployed-revision',required=True); parser.add_argument('--ci-url',required=True)
    args=parser.parse_args(); root=root_from_script()
    try: task_path,task=resolve_task(root,args.task)
    except ValueError as exc: raise SystemExit(f'ACCEPT RELEASE: FAIL — {exc}')
    if task.get('traits',{}).get('production_release') is not True:
        raise SystemExit('ACCEPT RELEASE: FAIL — task is not a production release')
    manifest,errors=validate_closure(root,task_path,task)
    if not manifest or errors:
        raise SystemExit('ACCEPT RELEASE: FAIL — valid candidate closure required: '+('; '.join(errors) if errors else f'expected COMPLETE/LOCALLY_ACCEPTED task and manifest at {closure_manifest_path(root, str(task.get("id")))}; current status={task.get("status")}'))
    if manifest.get('closure_kind')=='local_snapshot':
        raise SystemExit('ACCEPT RELEASE: FAIL — local snapshot closure cannot be production-accepted; deploy an immutable Git/artifact revision instead')
    expected_url=(manifest.get('release') or {}).get('production_url') or (task.get('release') or {}).get('production_url')
    if expected_url and expected_url != args.production_url:
        raise SystemExit('ACCEPT RELEASE: FAIL - production URL differs from the closed intended environment; create a new task for environment changes.')
    current=git_info(root)
    if not current.get('sha') or not revision_matches(str(current['sha']),args.deployed_revision):
        raise SystemExit('ACCEPT RELEASE: FAIL — deployed revision must match current closure HEAD exactly; supply the full 40/64-character commit ID, not a prefix or empty string')
    fingerprint=workspace_fingerprint(root)
    events=[event for event in load_events(root/'.ai/evidence/events.jsonl') if event.get('task')==task.get('id')]
    for check in ('production-smoke','production-critical-flow'):
        matches=[event for event in events if event.get('check')==check and event.get('fingerprint_after')==fingerprint]
        if not matches or matches[-1].get('status')!='pass':
            raise SystemExit(f'ACCEPT RELEASE: FAIL — fresh passing {check} evidence required')
        if check=='production-smoke' and not observed_revision_marker(args.deployed_revision,str(matches[-1].get('output_tail',''))):
            raise SystemExit(f'ACCEPT RELEASE: FAIL - production-smoke stdout/output_tail must include the observed deployed revision {args.deployed_revision} (full exact commit ID, not a prefix). Read the configured task.release.revision_marker endpoint, e.g. /build-info.json when that endpoint exists. Do not echo the expected revision without probing the deployed app.')
    manifest['release']={'status':'production_accepted','production_url':args.production_url,'candidate_revision':manifest.get('candidate_sha'),'deployed_revision':args.deployed_revision,'ci_url':args.ci_url,'accepted_at':dt.datetime.now(dt.timezone.utc).isoformat()}
    manifest['closure_revision']=current['sha']
    dump_json(root/'.ai/evidence'/f'closure-{task.get("id")}.json',manifest)
    print(f'ACCEPT RELEASE: PASS — {args.production_url} at {args.deployed_revision}')


if __name__=='__main__': main()
