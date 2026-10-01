#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
sys.dont_write_bytecode=True
from _common import safe_temp_base
ROOT=Path(__file__).resolve().parents[2]; PY=sys.executable
SOURCE_MARKER=ROOT/'.ai/SOURCE_DISTRIBUTION.json'
INSTALL_STATE=ROOT/'.ai/HARNESS_INSTALL_STATE.json'
EXCLUDE_DIRS={'.git','node_modules','.next','dist','build','coverage','.turbo','.cache','__pycache__'}; EXCLUDE_SUFFIXES={'.pyc','.pyo','.tmp','.bak','.orig','.zip'}; EXCLUDE_EXACT={'.ai/HARNESS_INSTALL_STATE.json','.ai/REPO_MAP.json'}
def run(a,cwd=ROOT):
    p=subprocess.run(a,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace'); print(p.stdout,end='',flush=True)
    if p.returncode: raise SystemExit(p.returncode)
def include(p):
    rel=p.relative_to(ROOT); s=rel.as_posix()
    if any(x in EXCLUDE_DIRS for x in rel.parts) or p.suffix.lower() in EXCLUDE_SUFFIXES: return False
    if s in EXCLUDE_EXACT or (s.startswith('.ai/evidence/') and s!='.ai/evidence/README.md') or (s.startswith('.ai/checkpoints/') and s!='.ai/checkpoints/README.md') or s.startswith('.ai/lessons/candidates/') or s.startswith('.ai/lessons/curated/'): return False
    return True
def main():
    if INSTALL_STATE.exists():
        raise SystemExit('RELEASE PACKAGE: REFUSED - this is an installed product repository, not a Harness source distribution. Package from an extracted canonical release/source tree.')
    if not SOURCE_MARKER.is_file():
        raise SystemExit('RELEASE PACKAGE: REFUSED - .ai/SOURCE_DISTRIBUTION.json is missing; source-release boundary is not proven.')
    try:
        marker=json.loads(SOURCE_MARKER.read_text(encoding='utf-8'))
    except Exception as exc:
        raise SystemExit(f'RELEASE PACKAGE: REFUSED - invalid source distribution marker: {exc}')
    if marker.get('kind')!='codex-product-harness-source-distribution':
        raise SystemExit('RELEASE PACKAGE: REFUSED - source distribution marker kind mismatch')
    ap=argparse.ArgumentParser(description='Build, re-extract, and verify the exact v5.5.10 source artifact with SPDX SBOM and release witness.')
    ap.add_argument('--temp-root',help='Writable scratch base outside the Harness source tree'); ap.add_argument('--out',required=True); ap.add_argument('--witness-out'); ap.add_argument('--sign-key'); ap.add_argument('--skip-self-test',action='store_true'); ap.add_argument('--skip-regressions',action='store_true'); a=ap.parse_args(); out=Path(a.out).resolve(); witness=Path(a.witness_out).resolve() if a.witness_out else Path(str(out)+'.witness.json')
    scratch_base=safe_temp_base(ROOT,a.temp_root,for_copy=True)
    run([PY,'.ai/scripts/build_sbom.py']); run([PY,'.ai/scripts/build_manifest.py']); run([PY,'.ai/scripts/validate_harness.py']); run([PY,'.ai/scripts/verify_package.py','--path','.']); run([PY,'.ai/scripts/surface_drift.py']); run([PY,'.ai/scripts/harness_security.py']); run([PY,'.ai/scripts/quarantine_scan.py','--target','.agents/skills','--fail-on','block']); run([PY,'.ai/scripts/skill_security_gate.py','--target','.agents/skills','--fail-on','block'])
    before_tests={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file() and include(p)}
    if not a.skip_regressions:
        run([PY,'.ai/scripts/deterministic_regression_gate.py','--temp-root',str(scratch_base)])
    if not a.skip_self_test: run([PY,'.ai/scripts/self_test.py','--context','source'])
    after_tests={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file() and include(p)}
    if after_tests != before_tests:
        raise SystemExit('RELEASE PACKAGE: FAIL - tests mutated package source; no automatic rebaseline')
    out.parent.mkdir(parents=True,exist_ok=True); out.unlink(missing_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(ROOT.rglob('*')):
            if p.is_file() and include(p): z.write(p,arcname=p.relative_to(ROOT).as_posix())
    run([PY,'.ai/scripts/verify_package.py','--path',str(out)])
    with tempfile.TemporaryDirectory(dir=scratch_base) as td:
        exact=Path(td)/'exact'; exact.mkdir()
        with zipfile.ZipFile(out) as z: z.extractall(exact)
        run([PY,str(exact/'.ai/scripts/verify_package.py'),'--path',str(exact)],cwd=exact)
        if not a.skip_regressions:
            run([PY,str(exact/'.ai/scripts/deterministic_regression_gate.py'),'--temp-root',str(scratch_base)],cwd=exact)
        if not a.skip_self_test:
            run([PY,str(exact/'.ai/scripts/self_test.py'),'--context','source'],cwd=exact)
    cmd=[PY,'.ai/scripts/release_witness.py','create','--artifact',str(out),'--out',str(witness)]
    if a.sign_key: cmd += ['--sign-key',a.sign_key]
    run(cmd); run([PY,'.ai/scripts/release_witness.py','verify','--artifact',str(out),'--witness',str(witness)])
    print('RELEASE PACKAGE:',out); print('SHA256:',hashlib.sha256(out.read_bytes()).hexdigest()); print('WITNESS:',witness)
if __name__=='__main__': main()
