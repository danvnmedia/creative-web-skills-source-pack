#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
sys.dont_write_bytecode=True
from _common import copy_source_tree, safe_temp_base

ROOT=Path(__file__).resolve().parents[2]
tempfile.tempdir=str(safe_temp_base(ROOT, for_copy=True))
PY=sys.executable


def run(cmd,cwd,expect=0):
    p=subprocess.run(cmd,cwd=str(cwd),text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode!=expect:
        print(p.stdout or '')
        raise SystemExit(f'V5.4.3 REGRESSION: FAIL expected {expect}, got {p.returncode}: {cmd}')
    return p.stdout or ''


def install(target: Path):
    plan_file=target.parent/'install-plan.json'
    run([PY,'.ai/scripts/install_plan.py','--source',str(ROOT),'--target',str(target),'--out',str(plan_file)],ROOT)
    plan=json.loads(plan_file.read_text(encoding='utf-8'))
    run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target),'--apply','--confirm',plan['plan_digest']],ROOT)


def main():
    with tempfile.TemporaryDirectory() as td_raw:
        td=Path(td_raw)
        product=td/'app'; product.mkdir()
        # Exact reported failure shape: a real application repository contains product residue
        # that is invalid inside a Harness archive but completely normal in an installed app.
        (product/'package.json').write_text('{"name":"real-app","scripts":{"test":"echo ok"}}\n',encoding='utf-8')
        (product/'README.md').write_text('# Real App\n',encoding='utf-8')
        (product/'VERSION').write_text('9.9.9\n',encoding='utf-8')
        (product/'node_modules/pkg').mkdir(parents=True); (product/'node_modules/pkg/index.js').write_text('module.exports=1\n')
        run(['git','init','-q'],product)
        (product/'.git/config').read_text(encoding='utf-8')
        install(product)

        # Installed self-test must validate Harness ownership only and ignore product repo residue.
        out=run([PY,'.ai/scripts/self_test.py','--context','installed'],product)
        if 'HARNESS SELF-TEST: PASS (context=installed)' not in out or 'product-repository residue' not in out:
            raise SystemExit('V5.4.3 REGRESSION: FAIL - installed self-test did not use the installed-runtime boundary')

        # Package verifier must explicitly reject use on an installed app, not report fake residue.
        out=run([PY,'.ai/scripts/verify_package.py','--path','.'],product,expect=1)
        if 'installed product repository is not a Harness source package' not in out:
            raise SystemExit('V5.4.3 REGRESSION: FAIL - package verifier did not distinguish installed app from source package')

        # Source-only packager must refuse before it can package the product repository.
        out=run([PY,'.ai/scripts/package_release.py','--out',str(td/'should-not-exist.zip'),'--skip-regressions','--skip-self-test'],product,expect=1)
        if 'installed product repository' not in out or (td/'should-not-exist.zip').exists():
            raise SystemExit('V5.4.3 REGRESSION: FAIL - installed app could invoke source release packaging')

        # Harness metadata must not read the product VERSION. Agent Plugin export should report the current Harness release version.
        plugin=td/'plugin.zip'
        run([PY,'.ai/scripts/export_agent_plugin.py','--out',str(plugin)],product)
        import zipfile
        with zipfile.ZipFile(plugin) as z:
            doc=json.loads(z.read('plugin.json'))
        if doc.get('version')!=(ROOT/'VERSION').read_text(encoding='utf-8').strip():
            raise SystemExit('V5.4.3 REGRESSION: FAIL - plugin export confused product VERSION with Harness VERSION')

        # Conversely source-package verification remains strict; do not weaken residue rules to make installed tests green.
        src=td/'source'; copy_source_tree(ROOT,src,ignore=shutil.ignore_patterns('__pycache__','.git'))
        (src/'node_modules/fake').mkdir(parents=True); (src/'node_modules/fake/x.js').write_text('x\n')
        out=run([PY,'.ai/scripts/verify_package.py','--path',str(src)],ROOT,expect=1)
        if 'forbidden source/package residue' not in out or 'node_modules' not in out:
            raise SystemExit('V5.4.3 REGRESSION: FAIL - source package residue rule was weakened')

    print('V5.4.3 REGRESSION: PASS - source/install boundary, app residue isolation, source-only packaging, and Harness metadata resolution')

if __name__=='__main__': main()
