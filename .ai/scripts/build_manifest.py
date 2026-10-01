#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
EXCLUDE_DIRS = {'.git','node_modules','.next','dist','build','coverage','.turbo','.cache','__pycache__'}
EXCLUDE_FILES = {
    '.ai/HARNESS_MANIFEST.json',
    '.ai/HARNESS_INSTALL_STATE.json',
    '.ai/REPO_MAP.json',
}
EXCLUDE_SUFFIXES = {'.pyc','.pyo','.tmp','.bak','.orig','.zip'}


def excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    posix = rel.as_posix()
    if posix in EXCLUDE_FILES or (posix.startswith('.ai/evidence/') and posix != '.ai/evidence/README.md') or (posix.startswith('.ai/checkpoints/') and posix != '.ai/checkpoints/README.md') or posix.startswith('.ai/lessons/candidates/') or posix.startswith('.ai/lessons/curated/'):
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    return False


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if (ROOT/'.ai/HARNESS_INSTALL_STATE.json').exists() or not (ROOT/'.ai/SOURCE_DISTRIBUTION.json').is_file():
        raise SystemExit('HARNESS MANIFEST: REFUSED - source-distribution boundary is not proven')
    ap=argparse.ArgumentParser(description='Build the deterministic ownership manifest for the harness source tree.')
    ap.add_argument('--out', default='.ai/HARNESS_MANIFEST.json')
    args=ap.parse_args()
    version=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
    entries=[]
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or excluded(path):
            continue
        rel=path.relative_to(ROOT).as_posix()
        entries.append({'path':rel,'sha256':sha256(path),'size':path.stat().st_size})
    doc={
        'schema_version':2,
        'harness_version':version,
        'entry_count':len(entries),
        'entries':entries,
        'ownership_policy':{
            'overwrite_user_modified_files':False,
            'generic_project_roots_are_source_only':True,
            'managed_blocks_preserve_outside_content':True,
            'apply_requires_fresh_plan_digest':True,
            'compare_and_swap_before_write':True,
            'rollback_on_failure':True,
            'generated_state_path':'.ai/HARNESS_INSTALL_STATE.json',
            'install_policy':'.ai/INSTALL_POLICY.json'
        }
    }
    out=ROOT/args.out
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'HARNESS MANIFEST: {len(entries)} files -> {out.relative_to(ROOT).as_posix()}')

if __name__=='__main__':
    main()
