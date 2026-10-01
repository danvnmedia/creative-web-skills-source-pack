#!/usr/bin/env python3
"""Fast Harness self-test with an explicit source-vs-installed boundary.

Source distribution mode validates the distributable tree/archive contract.
Installed mode validates only Harness-owned state inside the product repository and
never treats unrelated product files (.git, node_modules, package.json, etc.) as
Harness package residue.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True

from _common import harness_context

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable


def run(cmd):
    print('SELFTEST RUN:', ' '.join(map(str, cmd)), flush=True)
    p = subprocess.run(cmd, cwd=str(ROOT), text=True, encoding='utf-8', errors='replace', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode:
        print(p.stdout or '')
        raise SystemExit(p.returncode)
    return p.stdout or ''


def resolve_context(requested: str) -> str:
    if requested != 'auto': return requested
    observed=harness_context(ROOT)
    if observed=='source': return 'source'
    if observed=='installed': return 'installed'
    if observed=='legacy-installed':
        raise SystemExit('HARNESS SELF-TEST: REFUSED - legacy/manual install boundary is ambiguous. Re-run the v5.4.3+ collision-safe installer to create schema-v2 ownership state.')
    raise SystemExit('HARNESS SELF-TEST: REFUSED - cannot identify source distribution or managed installation context')


def main():
    ap=argparse.ArgumentParser(description='Run Harness self-test without crossing source-package and product-install boundaries.')
    ap.add_argument('--context', choices=['auto','source','installed'], default='auto')
    args=ap.parse_args(); context=resolve_context(args.context)
    checks=[]

    if context=='source':
        run([PY,'.ai/scripts/validate_harness.py']); checks.append('source-structure-and-contract-validator')
        run([PY,'.ai/scripts/verify_package.py','--path','.']); checks.append('source-package-contract')
    else:
        run([PY,'.ai/scripts/verify_installation.py','--root','.']); checks.append('installed-ownership-and-runtime-contract')

    run([PY,'.ai/scripts/skill_security_gate.py','--target','.agents/skills','--fail-on','block']); checks.append('skill-security-contract')

    for script, label in [
        ('runtime_control_state.py','excluded-runtime-control-state'),
        ('provider_policy_lint.py','provider-policy'),
        ('surface_drift.py','cross-harness-surface-contract'),
        ('harness_security.py','harness-security-baseline'),
    ]:
        run([PY, f'.ai/scripts/{script}']); checks.append(label)

    syntax="import pathlib; [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in pathlib.Path('.ai/scripts').glob('*.py')]"
    run([PY,'-c',syntax]); checks.append('python-syntax-without-pycache')
    if shutil.which('node'):
        run(['node','--check','.ai/scripts/browser_smoke.mjs'])
        run(['node','--check','.ai/scripts/browser_flow.mjs'])
        checks.append('browser-script-syntax')
    print(f'HARNESS SELF-TEST: PASS (context={context})')
    for check in checks: print(f'- {check}')
    if context=='source':
        print('Release deterministic regressions: python .ai/scripts/deterministic_regression_gate.py (auto-discovers every *_regression_test.py, including v553_regression_test.py)')
        print('Extended historical suite: python .ai/scripts/self_test_extended.py')
    else:
        print('Installed mode intentionally ignores unrelated product-repository residue and validates only Harness-owned runtime surfaces.')
    print('Note: live autonomous Skill activation requires trusted host telemetry or paired external eval; self-report is not proof.')


if __name__ == '__main__':
    main()
