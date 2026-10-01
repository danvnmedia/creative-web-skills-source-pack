#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import sys
sys.dont_write_bytecode = True

from _common import (
    approved_waivers,
    configure_utf8_stdio,
    derive_required_checks,
    load_events,
    load_json,
    resolve_task,
    root_from_script,
    validate_closure,
    workspace_fingerprint,
    waiver_validation,
)


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description='Render a human-readable, candidate-aware evidence report.')
    parser.add_argument('--task')
    parser.add_argument('--out', help='Optional markdown output path')
    args = parser.parse_args()
    root = root_from_script()
    try:
        task_path, task = resolve_task(root, args.task)
    except ValueError as exc:
        raise SystemExit(f'COMPLETION REPORT: {exc}')
    quality = load_json(root/'.ai/QUALITY.json')
    required = derive_required_checks(task, quality)
    waivers, waiver_errors = waiver_validation(task)
    current = workspace_fingerprint(root)
    target = current
    closure, closure_errors = validate_closure(root, task_path, task)
    if closure:
        target = closure.get('candidate_fingerprint', current)
        required = set(closure.get('required_checks', []))
        closure_task = {'verification': {'waivers': closure.get('waivers', []), 'findings': closure.get('findings', [])}}
        waivers, closure_waiver_errors = waiver_validation(closure_task)
        expected_digests = closure.get('waiver_digests', {}) or {}
        for check, item in waivers.items():
            if expected_digests.get(check) != item.get('waiver_sha256'):
                closure_waiver_errors.append(f'closure waiver digest mismatch: {check}')
        waiver_errors = list(waiver_errors) + closure_waiver_errors
    events = [event for event in load_events(root/'.ai/evidence/events.jsonl') if event.get('task') == task.get('id')]
    lines = [
        *([f'- Invalid waiver: {x}' for x in waiver_errors] if waiver_errors else []),
        f'# Completion Evidence Report — {task.get("id")}', '',
        f'Task: `{task_path.relative_to(root).as_posix()}`',
        f'Current workspace fingerprint: `{current}`',
        f'Accepted candidate fingerprint: `{target}`',
    ]
    if closure:
        release = closure.get('release') or {}
        lines += [
            f'Candidate revision: `{closure.get("candidate_sha")}`',
            f'Closure validation: `{"PASS" if not closure_errors else "FAIL"}`',
        ]
        if release.get('production_url'):
            lines.append(f'Production: `{release.get("production_url")}` at `{release.get("deployed_revision")}`')
        if release:
            lines.append(f'Production acceptance: `{release.get("status", "externally_pending")}`')
    lines += ['', '| Check | State | Candidate-fresh | Exit | Time | Command | Evidence |', '|---|---|---:|---:|---|---|---|']
    blocking = list(closure_errors) + [f'waiver: {x}' for x in waiver_errors]
    for check in sorted(required):
        if check in waivers:
            reason = str(waivers[check].get('reason', 'human-approved')).replace('|', '\\|')
            lines.append(f'| `{check}` | WAIVED | — | — | — | human-approved | {reason} |')
            continue
        check_target = current if closure and check.startswith('production-') else target
        matching = [event for event in events if event.get('check') == check and event.get('fingerprint_after') == check_target]
        if not matching:
            lines.append(f'| `{check}` | MISSING/STALE | no | — | — | — | — |')
            blocking.append(f'{check}: no {"deployment" if check.startswith("production-") else "candidate"}-fresh evidence')
            continue
        event = matching[-1]
        state = str(event.get('status', 'unknown')).upper()
        if event.get('status') != 'pass':
            blocking.append(f'{check}: {state.lower()}')
        command = str(event.get('command', '')).replace('|', '\\|').replace('\n', ' ')
        log = str(event.get('log', '')).replace('|', '\\|')
        lines.append(f'| `{check}` | {state} | yes | {event.get("exit_code", "—")} | {event.get("timestamp", "—")} | `{command}` | `{log}` |')
    lines += ['', f'**Gate summary:** {"PASS" if not blocking else "FAIL"}']
    if blocking:
        lines += ['', 'Blocking evidence:', *[f'- {item}' for item in blocking]]
    lines += ['', 'This report proves the recorded checks for the accepted candidate plus closure-source equivalence when a closure manifest is present. It does not replace acceptance-criteria review.', '']
    text = '\n'.join(lines)
    if args.out:
        output = Path(args.out)
        output = output if output.is_absolute() else root/output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding='utf-8')
        print(f'wrote {output}')
    print(text, end='')
    if blocking:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
