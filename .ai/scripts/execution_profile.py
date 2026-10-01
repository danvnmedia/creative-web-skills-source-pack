#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, dump_json, load_json, resolve_task, root_from_script

ORDER = {'native': 0, 'portable': 1, 'audited': 2}


def derive(task: dict, policy: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    minimum = policy.get('selection', {}).get('default', 'native')
    if task.get('mode') in set(policy.get('selection', {}).get('audited_if_mode', [])):
        minimum = 'audited'; reasons.append(f"mode={task.get('mode')}")
    traits = task.get('traits', {}) or {}
    for trait in policy.get('selection', {}).get('audited_if_traits', []):
        if traits.get(trait):
            minimum = 'audited'; reasons.append(f'trait:{trait}')
    risk = str((task.get('risk') or {}).get('level') or '').lower()
    if risk in set(policy.get('selection', {}).get('audited_if_risk_levels', [])):
        minimum = 'audited'; reasons.append(f'risk:{risk}')

    contract = task.get('execution_contract', {}) or {}
    if minimum != 'audited':
        for flag in policy.get('selection', {}).get('portable_if_execution_flags', []):
            if contract.get(flag):
                minimum = 'portable'; reasons.append(f'execution:{flag}')
    if not reasons:
        reasons.append('default:current-session')

    requested = str(contract.get('profile') or 'auto').lower()
    if requested == 'auto':
        return minimum, reasons
    if requested not in ORDER:
        raise ValueError(f'unsupported execution profile: {requested}')
    if policy.get('selection', {}).get('explicit_profile_cannot_be_weaker_than_derived_minimum', True) and ORDER[requested] < ORDER[minimum]:
        raise ValueError(f'requested profile {requested} is weaker than derived minimum {minimum} ({", ".join(reasons)})')
    if ORDER[requested] > ORDER[minimum]:
        reasons.append(f'explicit-escalation:{requested}')
    return requested, reasons


def main() -> None:
    configure_utf8_stdio()
    ap = argparse.ArgumentParser(description='Resolve the lightest execution profile that preserves safe, honest completion.')
    ap.add_argument('--task', help='Task id or path; defaults to active task.')
    ap.add_argument('--write', action='store_true', help='Persist resolved_profile and routing_reasons into the task contract.')
    args = ap.parse_args()
    root = root_from_script()
    policy = load_json(root/'.ai/EXECUTION_POLICY.json')
    try:
        task_path, task = resolve_task(root, args.task)
        profile, reasons = derive(task, policy)
    except (ValueError, OSError) as exc:
        print(f'EXECUTION PROFILE: FAIL - {exc}')
        raise SystemExit(1)
    print(f'profile={profile}')
    for reason in reasons:
        print(f'reason={reason}')
    if args.write:
        contract = task.setdefault('execution_contract', {})
        contract.setdefault('profile', 'auto')
        contract['resolved_profile'] = profile
        contract['routing_reasons'] = reasons
        dump_json(task_path, task)
        print(f'updated={task_path.relative_to(root).as_posix()}')


if __name__ == '__main__':
    main()
