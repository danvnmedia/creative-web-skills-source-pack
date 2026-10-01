#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, harness_version
from install_plan import BEGIN_FMT, END_FMT, find_block, sha_file, sha_bytes

ROOT = Path(__file__).resolve().parents[2]
PROTECTED_WHOLE = {
    'README.md','VERSION','CHANGELOG.md','LICENSE','LICENSE.md','LICENSE.txt',
    'START_HERE_PROMPT.md','SBOM.spdx.json','INSTALL_HARNESS.py'
}
ALLOWED_ROOT_BLOCKS = {'.gitattributes','AGENTS.md','CLAUDE.md','GEMINI.md','ANTIGRAVITY.md'}
ALLOWED_DOC_BLOCKS = {'docs/AI_INTEGRATION_TESTING.md','docs/RUNTIME_VERIFICATION.md','docs/GEMINI_FREE_FIRST.md'}


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def canonical_skill_errors(root: Path) -> list[str]:
    errors=[]
    try:
        canonical=load(root/'.ai/CANONICAL_SKILL_HASHES.json')
    except Exception as exc:
        return [f'invalid canonical Skill hash contract: {exc}']
    if canonical.get('canonical_baseline')!='5.3.0' or canonical.get('skill_count')!=13:
        errors.append('canonical Skill hash contract must remain v5.3.0 / 13 Skills')
    for name, expected in (canonical.get('sha256') or {}).items():
        p=root/f'.agents/skills/{name}/SKILL.md'
        if not p.is_file(): errors.append(f'missing canonical Skill: {name}'); continue
        if hashlib.sha256(p.read_bytes()).hexdigest()!=expected: errors.append(f'canonical v5.3 Skill drift: {name}')
    return errors


def main() -> None:
    configure_utf8_stdio()
    ap=argparse.ArgumentParser(description='Validate an installed Harness inside a product repository without treating product files as Harness package residue.')
    ap.add_argument('--root', default=str(ROOT))
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args(); root=Path(args.root).resolve(); errors=[]; warnings=[]; checked=[]; mutable_changed=[]
    state_path=root/'.ai/HARNESS_INSTALL_STATE.json'
    if not state_path.is_file():
        errors.append('missing .ai/HARNESS_INSTALL_STATE.json; installed-runtime acceptance requires explicit ownership state')
        state={}
    else:
        try: state=load(state_path)
        except Exception as exc: errors.append(f'invalid install state: {exc}'); state={}
    schema=int(state.get('schema_version') or 0)
    if schema < 2:
        errors.append('install state schema <2 is legacy; re-run the v5.4.3+ collision-safe installer before installed-runtime acceptance')
    if state.get('owner') not in (None,'codex-product-harness'):
        errors.append('install state owner mismatch')
    if (root/'.ai/SOURCE_DISTRIBUTION.json').exists():
        errors.append('source-distribution marker leaked into installed product repository')
    version=harness_version(root)
    if version != state.get('harness_version'):
        errors.append(f'installed Harness version mismatch: metadata={version!r}, state={state.get("harness_version")!r}')

    records=state.get('records') or {}
    if not isinstance(records, dict):
        errors.append('install state records must be an object'); records={}
    try:
        policy=load(root/'.ai/INSTALL_POLICY.json')
        mutable_seed_paths=set(policy.get('mutable_seed_paths', []))
    except Exception as exc:
        errors.append(f'invalid install policy: {exc}'); mutable_seed_paths=set()
    for rel, rec in records.items():
        path=root/rel; mode=rec.get('mode'); checked.append(rel)
        if mode=='whole_file':
            if rel in PROTECTED_WHOLE or rel.startswith('docs/') or rel.startswith('templates/'):
                errors.append(f'protected project path is incorrectly claimed as whole-file Harness ownership: {rel}')
            if not path.is_file(): errors.append(f'missing managed file: {rel}'); continue
            actual=sha_file(path)
            if actual!=rec.get('last_managed_sha256'):
                errors.append(f'managed file drift: {rel}')
        elif mode=='mutable_seed':
            if rel not in mutable_seed_paths:
                errors.append(f'mutable-seed ownership is not declared by install policy: {rel}')
            if not path.is_file():
                errors.append(f'missing mutable runtime seed: {rel}'); continue
            actual=sha_file(path); seed=rec.get('last_seed_sha256')
            if path.suffix.lower()=='.json':
                try: load(path)
                except Exception as exc: errors.append(f'invalid mutable runtime JSON {rel}: {exc}')
            if actual != seed:
                mutable_changed.append({'path':rel,'current_sha256':actual,'seed_sha256':seed})
        elif mode=='managed_block':
            if rel not in ALLOWED_ROOT_BLOCKS and rel not in ALLOWED_DOC_BLOCKS:
                warnings.append(f'unexpected managed-block surface: {rel}')
            if not path.is_file(): errors.append(f'missing managed-block container: {rel}'); continue
            marker=str(rec.get('marker_id') or '')
            try: found=find_block(path.read_bytes(), marker)
            except Exception as exc: errors.append(f'invalid managed block {rel}: {exc}'); continue
            if not found: errors.append(f'missing managed block: {rel}'); continue
            if sha_bytes(found[2])!=rec.get('last_managed_sha256'):
                errors.append(f'managed block drift: {rel}')
        else:
            errors.append(f'unknown ownership mode for {rel}: {mode!r}')

    # Runtime-critical controls must be state-owned, while project-generic files must not be.
    required=[
        '.ai/INSTALL_POLICY.json','.ai/HARNESS_MANIFEST.json','.ai/QUALITY.json','.ai/TASK_TEMPLATE.json',
        '.ai/scripts/self_test.py','.ai/scripts/verify_installation.py','.ai/scripts/install_plan.py',
        '.ai/harness/VERSION','.ai/harness/surfaces/AGENTS.md',
    ]
    for rel in required:
        if rel not in records: errors.append(f'install state missing runtime-critical managed path: {rel}')
    for rel in mutable_seed_paths:
        rec=records.get(rel) or {}
        if rec.get('mode')!='mutable_seed': errors.append(f'declared mutable runtime seed is not registered as mutable_seed: {rel}')
    for rel in PROTECTED_WHOLE:
        if rel in records and (records.get(rel) or {}).get('mode')=='whole_file':
            errors.append(f'generic project root is Harness-owned: {rel}')

    errors.extend(canonical_skill_errors(root))
    report={
        'schema_version':1,'status':'pass' if not errors else 'fail','context':'installed',
        'harness_version':version,'checked_records':len(checked),'errors':errors,'warnings':warnings,
        'mutable_runtime_changed':mutable_changed,'mutable_runtime_changed_count':len(mutable_changed),
        'product_repo_residue_ignored_by_design':True,
    }
    if args.json: print(json.dumps(report,indent=2,ensure_ascii=False))
    else:
        print('INSTALLED HARNESS VERIFY: '+('PASS' if not errors else 'FAIL'))
        print(f'context=installed version={version or "unknown"} records={len(checked)} mutable_changed={len(mutable_changed)}')
        for w in warnings: print('[WARN] '+w)
        for e in errors: print('[FAIL] '+e)
    if errors: raise SystemExit(1)

if __name__=='__main__': main()
