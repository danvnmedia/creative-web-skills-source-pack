#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode = True

SOURCE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE_ROOT / '.ai/scripts'))
from install_plan import apply_plan, build_plan, render_summary  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            'Collision-safe Codex Product Harness installer. Default behavior is read-only planning. '
            'Apply requires the exact plan digest so changed targets are never silently overwritten.'
        )
    )
    ap.add_argument('--target', required=True, help='Product repository root.')
    ap.add_argument('--apply', action='store_true', help='Apply a previously reviewed current plan.')
    ap.add_argument('--confirm', help='Exact plan_digest printed by the read-only planning run.')
    ap.add_argument('--repair-eol', action='store_true', help='Explicitly restore/update only CRLF-transformed owned bytes that match their prior LF hash; include this flag in both plan and apply.')
    ap.add_argument('--full-plan', action='store_true', help='Print the full per-path plan instead of the compact summary.')
    args = ap.parse_args()

    target = Path(args.target).resolve()
    if target == SOURCE_ROOT.resolve():
        raise SystemExit('INSTALL: FAIL - source distribution cannot install into itself')
    # Scan the exact canonical Skill payload before any install planning or mutation.
    # This is deterministic/static and never executes code from a Skill.
    gate=subprocess.run([sys.executable,str(SOURCE_ROOT/'.ai/scripts/skill_security_gate.py'),'--target',str(SOURCE_ROOT/'.agents/skills'),'--fail-on','block'],cwd=str(SOURCE_ROOT),text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if gate.returncode:
        print(gate.stdout or '')
        raise SystemExit('INSTALL: FAIL - canonical Skill payload failed pre-install security gate')
    try:
        gate_doc=json.loads(gate.stdout)
        print(f"INSTALL PRECHECK: PASS - Skill security gate {gate_doc.get('status')} ({gate_doc.get('exact_bundle_sha256')})")
    except Exception:
        raise SystemExit('INSTALL: FAIL - Skill security gate returned invalid report')
    try:
        plan, _ = build_plan(SOURCE_ROOT, target, repair_eol=args.repair_eol)
    except Exception as exc:
        raise SystemExit(f'INSTALL: FAIL - {exc}')

    print(json.dumps(plan if args.full_plan else render_summary(plan), indent=2, ensure_ascii=False))
    if not args.apply:
        if plan['safe_to_apply']:
            print('INSTALL PLAN: PASS - read-only. Re-run with --apply --confirm <plan_digest>.')
            return
        print('INSTALL PLAN: BLOCKED - protected conflicts exist; no files were changed')
        raise SystemExit(2)

    if not args.confirm:
        print('INSTALL: FAIL - --apply requires --confirm <plan_digest> from a current planning run')
        raise SystemExit(2)
    if not plan['safe_to_apply']:
        print('INSTALL: FAIL - protected conflicts exist; no files were changed')
        raise SystemExit(2)
    try:
        result = apply_plan(SOURCE_ROOT, target, args.confirm, repair_eol=args.repair_eol)
    except Exception as exc:
        raise SystemExit(f'INSTALL: FAIL - {exc}')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"INSTALL: PASS - Codex Product Harness {plan['source_version']} installed transactionally at {target}")


if __name__ == '__main__':
    main()
