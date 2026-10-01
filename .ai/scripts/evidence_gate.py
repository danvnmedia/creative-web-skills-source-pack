#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
sys.dont_write_bytecode = True

from _common import (
    approved_waivers,
    catalog_runner,
    check_catalog_digest,
    check_contract_digest,
    configure_utf8_stdio,
    derive_required_checks,
    load_events,
    load_json,
    resolve_task,
    root_from_script,
    runtime_candidate_digest,
    validate_closure,
    workspace_fingerprint,
    waiver_validation,
    task_contract_digest,
)


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description='Fail unless all task-required checks have fresh passing evidence for the accepted candidate.')
    parser.add_argument('--task', help='Task id or path. Defaults to .ai/STATE.json active_task.')
    parser.add_argument('--pre-release', action='store_true', help='Validate the local/CI candidate before deployment; production-* checks remain externally pending.')
    args = parser.parse_args()
    root = root_from_script()
    from runtime_control_state import validate as validate_runtime
    runtime_report=validate_runtime(root)
    if runtime_report['errors']:
        raise SystemExit('EVIDENCE GATE: FAIL - '+ '; '.join(runtime_report['errors']))
    quality = load_json(root/'.ai/QUALITY.json')
    try:
        task_path, task = resolve_task(root, args.task)
    except ValueError as exc:
        print(f'EVIDENCE GATE: FAIL — {exc}')
        raise SystemExit(1)

    if (root/'.ai/TRAIT_SKILL_MAP.json').is_file():
        from task_guidance import guidance
        try:
            advice=guidance(root,task)
            for note in advice['warnings']: print('[ADVISORY] '+note)
            if advice['recommended_skills']: print('[SKILL PREPARATION; NOT TELEMETRY] '+', '.join(advice['recommended_skills']))
        except (ValueError,OSError,KeyError,TypeError) as exc:
            print('[ADVISORY INCOMPLETE] '+str(exc))
    task_id = task.get('id')
    required = derive_required_checks(task, quality)
    waivers, waiver_errors = waiver_validation(task)
    if waiver_errors:
        print('EVIDENCE GATE: FAIL — invalid or stale waiver')
        for error in waiver_errors:
            print(f'- {error}')
        raise SystemExit(1)
    target_fingerprint = workspace_fingerprint(root)
    current_contract = task_contract_digest(task)
    current_runtime_candidate = runtime_candidate_digest(root, task)
    fp_policy = load_json(root/'.ai/FINGERPRINT_POLICY.json')
    runtime_bound_checks=set((fp_policy.get('runtime_candidate_digest') or {}).get('invalidates_checks', []))
    current_catalog_digest=check_catalog_digest(root)
    closure, closure_errors = validate_closure(root, task_path, task)
    if closure_errors:
        print('EVIDENCE GATE: FAIL — invalid task closure')
        for error in closure_errors:
            print(f'- {error}')
        raise SystemExit(1)
    if closure:
        target_fingerprint = closure['candidate_fingerprint']
        required = set(closure.get('required_checks', []))
        closure_task = {'verification': {'waivers': closure.get('waivers', []), 'findings': closure.get('findings', [])}}
        waivers, closure_waiver_errors = waiver_validation(closure_task)
        expected_digests = closure.get('waiver_digests', {}) or {}
        for check, item in waivers.items():
            if expected_digests.get(check) != item.get('waiver_sha256'):
                closure_waiver_errors.append(f'closure waiver digest mismatch: {check}')
        if closure_waiver_errors:
            print('EVIDENCE GATE: FAIL — closure waiver invalid, stale, or expired')
            for error in closure_waiver_errors:
                print(f'- {error}')
            raise SystemExit(1)
        print(f'[CLOSURE] candidate={closure.get("candidate_sha")} current={closure.get("closure_revision") or "working-tree"}')
    if args.pre_release:
        if closure:
            raise SystemExit('EVIDENCE GATE: FAIL — --pre-release is only valid before task closure')
        pending={check for check in required if check.startswith('production-')}
        required-=pending
        for check in sorted(pending): print(f'[EXTERNALLY_PENDING] {check}: requires deployed candidate')

    task_events = [event for event in load_events(root/'.ai/evidence/events.jsonl') if event.get('task') == task_id]
    failures: list[str] = []
    for check in sorted(required):
        if check in waivers:
            print(f'[WAIVED] {check}: {waivers[check].get("reason", "human-approved")}')
            continue
        accepted_fingerprints={target_fingerprint}
        if closure and check.startswith('production-'):
            accepted_fingerprints.add(workspace_fingerprint(root))
        matching=[]
        for event in task_events:
            direct=event.get('check') == check
            shared=check in (event.get('satisfies_checks') or [])
            if not (direct or shared): continue
            if event.get('fingerprint_after') not in accepted_fingerprints: continue
            if event.get('check_contract_digest') is not None:
                observed_check_contract=(event.get('satisfies_check_contract_digests') or {}).get(check) if shared else event.get('check_contract_digest')
                if observed_check_contract != check_contract_digest(task,check): continue
            elif event.get('task_contract_digest', current_contract) != current_contract:
                continue
            if shared:
                rid=str(event.get('catalog_runner') or '')
                runner=catalog_runner(root,rid) if rid else None
                if not runner or check not in (runner.get('checks') or []): continue
                if event.get('catalog_digest') != current_catalog_digest: continue
            if check in runtime_bound_checks and event.get('runtime_candidate_digest') not in (None,current_runtime_candidate): continue
            matching.append(event)
        if not matching:
            prior = [event for event in task_events if event.get('check') == check]
            if prior and any(e.get('fingerprint_after') in accepted_fingerprints and ((e.get('check_contract_digest') is not None and ((e.get('satisfies_check_contract_digests') or {}).get(check) if check in (e.get('satisfies_checks') or []) else e.get('check_contract_digest')) != check_contract_digest(task,check)) or (e.get('check_contract_digest') is None and e.get('task_contract_digest') not in (None,current_contract))) for e in prior):
                failures.append(f'{check}: evidence is stale because task contract changed for this check')
            elif prior and check in runtime_bound_checks and any(e.get('runtime_candidate_digest') not in (None,current_runtime_candidate) for e in prior):
                failures.append(f'{check}: evidence is stale because runtime candidate changed')
            else:
                failures.append(f'{check}: evidence is stale' if prior else f'{check}: no evidence')
            continue
        event = matching[-1]
        if event.get('status') != 'pass':
            failures.append(f'{check}: latest candidate status={event.get("status")}')
            continue
        if check=='skill-eval-live':
            try:
                from skill_eval_acceptance import validate_binding
                validate_binding(root,event.get('skill_eval_binding'))
            except (ValueError,OSError,KeyError,TypeError) as exc:
                failures.append(f'{check}: {exc}')
                continue
        print(f'[PASS] {check} — {event.get("timestamp")}')
    if failures:
        print('EVIDENCE GATE: FAIL')
        for failure in failures:
            print(f'- {failure}')
        raise SystemExit(1)
    print(f'EVIDENCE GATE: PASS — {task_id} ({len(required)} required checks)')


if __name__ == '__main__':
    main()
