#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
sys.dont_write_bytecode = True

from _common import (
    approved_waivers,
    configure_utf8_stdio,
    derive_required_checks,
    dump_json,
    load_events,
    load_json,
    resolve_task,
    root_from_script,
    waiver_validation,
    workspace_fingerprint,
)
from verified_checkpoint import checkpoint_path, validate_doc


def safe_name(value: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', value).strip('._') or 'task'


def fresh_pass(events: list[dict], task_id: str, check: str, fingerprint: str) -> bool:
    rows = [e for e in events if e.get('task') == task_id and e.get('check') == check and not e.get('ephemeral')]
    return bool(rows and rows[-1].get('status') == 'pass' and rows[-1].get('fingerprint_after') == fingerprint)


def valid_checkpoint(root: Path, task_id: str) -> tuple[dict | None, list[str]]:
    path = checkpoint_path(root, task_id)
    if not path.is_file():
        return None, ['missing verified checkpoint']
    try:
        doc = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return None, [f'invalid verified checkpoint: {exc}']
    errors = validate_doc(root, task_id, doc)
    return (doc if not errors else None), errors


def main() -> None:
    configure_utf8_stdio()
    ap = argparse.ArgumentParser(description='Choose ACCEPT/RETRY/REPLAN/ROLLBACK from fresh evidence, budgets, and verified checkpoints.')
    ap.add_argument('--task', help='Task id or path; defaults to active task.')
    ap.add_argument('--check', help='Limit decision to one verification check.')
    ap.add_argument('--next-hypothesis-id', help='Prospective hypothesis id required for RETRY after failure.')
    ap.add_argument('--no-write', action='store_true', help='Do not persist the runtime decision record.')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    root = root_from_script()
    _, task = resolve_task(root, args.task)
    task_id = str(task.get('id') or '')
    quality = load_json(root/'.ai/QUALITY.json')
    control = load_json(root/'.ai/CONTROL_POLICY.json')
    budget = load_json(root/'.ai/RUNTIME_BUDGET.json').get('evidence', {})
    fp = workspace_fingerprint(root)
    events = [e for e in load_events(root/'.ai/evidence/events.jsonl') if e.get('task') == task_id and not e.get('ephemeral')]
    scoped = [e for e in events if not args.check or e.get('check') == args.check]
    latest = scoped[-1] if scoped else None
    reasons: list[str] = []
    decision = 'REPLAN'
    rollback_target = None

    waivers, waiver_errors = waiver_validation(task)
    if waiver_errors:
        reasons.append('invalid-waiver:' + ';'.join(waiver_errors))

    hard_labels = set(control.get('hard_boundary_labels', []))
    hard_breach = bool(latest and (latest.get('hard_boundary_breach') is True or latest.get('risk_boundary') in hard_labels))
    if hard_breach:
        checkpoint, checkpoint_errors = valid_checkpoint(root, task_id)
        if checkpoint:
            decision = 'ROLLBACK'
            rollback_target = {
                'workspace_fingerprint': checkpoint.get('workspace_fingerprint'),
                'created_at': checkpoint.get('created_at'),
                'completed': checkpoint.get('completed', []),
            }
            reasons.append('hard-boundary-breach')
        else:
            decision = 'REPLAN'
            reasons.append('hard-boundary-breach-without-valid-checkpoint')
            reasons.extend('checkpoint:' + x for x in checkpoint_errors)
    else:
        required = {args.check} if args.check else derive_required_checks(task, quality)
        required = {c for c in required if c and c not in waivers}
        if not waiver_errors and required and all(fresh_pass(events, task_id, c, fp) for c in required):
            decision = 'ACCEPT'
            reasons.append('all-required-evidence-fresh-and-passing')
        elif latest and latest.get('status') != 'pass':
            check_name = str(latest.get('check') or '')
            check_events = [e for e in scoped if e.get('check') == check_name]
            attempts = len(check_events)
            same_failure = int(latest.get('same_failure_repeat_count') or 0)
            max_attempts = int(budget.get('max_attempts_per_check', 6))
            stop_after = int(budget.get('same_failure_stop_after', 3))
            if attempts >= max_attempts or same_failure >= stop_after:
                decision = 'REPLAN'
                reasons.append('retry-budget-exhausted' if attempts >= max_attempts else 'repeated-identical-failure')
            elif args.next_hypothesis_id and args.next_hypothesis_id != str(latest.get('hypothesis_id') or ''):
                decision = 'RETRY'
                reasons.append('changed-hypothesis-within-budget')
            else:
                decision = 'REPLAN'
                reasons.append('retry-requires-changed-hypothesis')
        else:
            reasons.append('missing-or-stale-evidence')

    created = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    report = {
        'schema_version': 1,
        'task': task_id,
        'check': args.check,
        'decision': decision,
        'reason_codes': reasons,
        'workspace_fingerprint': fp,
        'latest_evidence': None if not latest else {
            'check': latest.get('check'),
            'status': latest.get('status'),
            'timestamp': latest.get('timestamp'),
            'failure_signature': latest.get('failure_signature'),
            'hypothesis_id': latest.get('hypothesis_id'),
            'risk_boundary': latest.get('risk_boundary'),
            'hard_boundary_breach': latest.get('hard_boundary_breach'),
        },
        'next_hypothesis_id': args.next_hypothesis_id,
        'rollback_target': rollback_target,
        'created_at': created,
    }
    out = None
    if not args.no_write:
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        out = root/str(control.get('runtime_output_root', '.ai/checkpoints/decisions'))/f'{safe_name(task_id)}-{stamp}.json'
        dump_json(out, report)
        report['runtime_record'] = out.relative_to(root).as_posix()
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
