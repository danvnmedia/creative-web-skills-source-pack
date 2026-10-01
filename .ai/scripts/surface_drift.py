#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

from _common import harness_context
from install_plan import find_block

ROOT=Path(__file__).resolve().parents[2]


def main() -> None:
    ap=argparse.ArgumentParser(description='Validate canonical-vs-adapter Harness surfaces without assuming host feature parity or mistaking product-owned paths for Harness duplicates.')
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args()
    cfg=json.loads((ROOT/'.ai/SURFACE_OWNERSHIP.json').read_text(encoding='utf-8'))
    context=harness_context(ROOT)
    installed=context=='installed'
    errors=[]; warnings=[]; checked=[]
    canonical=dict(cfg.get('canonical',{}))
    if installed:
        canonical['operating_constitution']='.ai/harness/surfaces/AGENTS.md'
    for label, rel in canonical.items():
        p=ROOT/rel
        if not p.exists(): errors.append(f'canonical {label} missing: {rel}')
        else: checked.append(rel)

    policy={}
    if installed and (ROOT/'.ai/INSTALL_POLICY.json').is_file():
        policy=json.loads((ROOT/'.ai/INSTALL_POLICY.json').read_text(encoding='utf-8'))
    snapshots={x['target']:x for x in policy.get('managed_block_surfaces',[])}
    for adapter, spec in cfg.get('adapters',{}).items():
        entrypoints=spec.get('entrypoints',[])
        for rel in entrypoints:
            p=ROOT/rel
            if not p.is_file():
                errors.append(f'{adapter} entrypoint missing: {rel}')
                continue
            if installed:
                item=snapshots.get(rel)
                if not item:
                    errors.append(f'{adapter} installed entrypoint has no managed-block policy: {rel}')
                    continue
                marker=str(item.get('marker_id') or '')
                try: found=find_block(p.read_bytes(),marker)
                except Exception as exc: errors.append(f'{adapter} entrypoint block invalid: {rel}: {exc}'); continue
                if not found: errors.append(f'{adapter} entrypoint missing Harness managed block: {rel}'); continue
                snapshot_rel=item['snapshot']; snapshot=ROOT/snapshot_rel
                if not snapshot.is_file(): errors.append(f'{adapter} snapshot missing: {snapshot_rel}'); continue
                text=snapshot.read_text(encoding='utf-8',errors='replace')
                checked.extend([rel,snapshot_rel])
            else:
                text=p.read_text(encoding='utf-8',errors='replace'); checked.append(rel)
            for token in spec.get('must_reference',[]):
                if token not in text:
                    errors.append(f'{adapter} canonical adapter surface for {rel} does not reference {token}')
        for rel in spec.get('native_surfaces',[]):
            if not (ROOT/rel).exists(): errors.append(f'{adapter} native surface missing: {rel}')

    skill_root=Path(canonical.get('skills_root','.agents/skills'))
    duplicate_roots=[]
    canonical_hashes={}
    try:
        canonical_hashes=json.loads((ROOT/'.ai/CANONICAL_SKILL_HASHES.json').read_text(encoding='utf-8')).get('sha256',{})
    except Exception:
        pass
    for candidate in ('skills','.codex/skills','.gemini/skills','.claude/skills'):
        p=ROOT/candidate
        if not p.exists() or p.resolve()==(ROOT/skill_root).resolve(): continue
        if not installed:
            duplicate_roots.append(candidate); continue
        # In product repositories an unrelated directory named "skills" is not Harness drift.
        # Count it only when it actually duplicates at least one canonical Harness Skill byte-for-byte.
        duplicated=False
        for name, expected in canonical_hashes.items():
            cp=p/name/'SKILL.md'
            if cp.is_file() and hashlib.sha256(cp.read_bytes()).hexdigest()==expected:
                duplicated=True; break
        if duplicated: duplicate_roots.append(candidate)
    if duplicate_roots and cfg.get('policy',{}).get('skills_have_one_canonical_copy'):
        errors.append('duplicate Harness skill roots violate canonical ownership: '+', '.join(duplicate_roots))
    report={'schema_version':2,'status':'pass' if not errors else 'fail','context':context,'checked':sorted(set(checked)),'warnings':warnings,'errors':errors}
    if args.json: print(json.dumps(report,indent=2,ensure_ascii=False))
    else:
        print('SURFACE DRIFT: '+('PASS' if not errors else 'FAIL')+f' (context={context})')
        for w in warnings: print('[WARN] '+w)
        for e in errors: print('[FAIL] '+e)
    if errors: raise SystemExit(1)

if __name__=='__main__': main()
