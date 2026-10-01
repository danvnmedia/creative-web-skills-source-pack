#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
sys.dont_write_bytecode = True
from _common import safe_temp_base

ROOT = Path(__file__).resolve().parents[2]
tempfile.tempdir=str(safe_temp_base(ROOT, for_copy=True))
PY = sys.executable


def run(cmd, cwd, expect=0):
    p = subprocess.run(cmd, cwd=str(cwd), text=True, encoding='utf-8', errors='replace', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != expect:
        print(p.stdout or '')
        raise SystemExit(f'INSTALL REGRESSION: FAIL - expected {expect}, got {p.returncode}: {cmd}')
    return p.stdout or ''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan(target: Path):
    out=run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target),'--full-plan'],ROOT)
    # JSON is first payload; use install_plan directly for unambiguous machine output.
    raw=run([PY,'.ai/scripts/install_plan.py','--source',str(ROOT),'--target',str(target),'--out',str(target.parent/'plan.json')],ROOT)
    doc=json.loads((target.parent/'plan.json').read_text(encoding='utf-8'))
    return doc,out


def apply(target: Path, digest: str, expect=0):
    return run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target),'--apply','--confirm',digest],ROOT,expect=expect)


def main():
    with tempfile.TemporaryDirectory() as td_raw:
        td=Path(td_raw); target=td/'product'; target.mkdir()
        # Real product-owned generic roots must remain byte-identical.
        (target/'README.md').write_text('# Product README\nkeep me\n',encoding='utf-8')
        (target/'VERSION').write_text('2.7.3\n',encoding='utf-8')
        (target/'CHANGELOG.md').write_text('product history\n',encoding='utf-8')
        (target/'package.json').write_text('{"name":"product","scripts":{"dev":"vite","test":"vitest"}}\n',encoding='utf-8')
        (target/'AGENTS.md').write_text('# Product agent rules\nNever delete this line.\n',encoding='utf-8')
        (target/'docs').mkdir(); (target/'docs/RUNTIME_VERIFICATION.md').write_text('# Product runtime doc\nkeep\n',encoding='utf-8')
        protected={p:sha(target/p) for p in ('README.md','VERSION','CHANGELOG.md')}
        agent_before=(target/'AGENTS.md').read_text(encoding='utf-8')
        doc_before=(target/'docs/RUNTIME_VERIFICATION.md').read_text(encoding='utf-8')

        first,_=plan(target)
        if not first['safe_to_apply']:
            raise SystemExit('INSTALL REGRESSION: FAIL - fresh collision-safe plan unexpectedly blocked')
        # Planning is read-only.
        if any(sha(target/p)!=h for p,h in protected.items()) or (target/'.ai/HARNESS_INSTALL_STATE.json').exists():
            raise SystemExit('INSTALL REGRESSION: FAIL - plan-only mode mutated product')
        apply(target,first['plan_digest'])

        for p,h in protected.items():
            if sha(target/p)!=h: raise SystemExit(f'INSTALL REGRESSION: FAIL - protected project root changed: {p}')
        expected_version=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
        if not (target/'.ai/harness/VERSION').is_file() or (target/'.ai/harness/VERSION').read_text().strip()!=expected_version:
            raise SystemExit('INSTALL REGRESSION: FAIL - namespaced Harness VERSION missing')
        if (target/'.ai/SOURCE_DISTRIBUTION.json').exists():
            raise SystemExit('INSTALL REGRESSION: FAIL - source marker leaked into product')
        if len(list((target/'.agents/skills').glob('*/SKILL.md')))!=13:
            raise SystemExit('INSTALL REGRESSION: FAIL - 13 canonical Skills were not installed')
        agents=(target/'AGENTS.md').read_text(encoding='utf-8')
        if not agents.startswith(agent_before) or 'CODEX_PRODUCT_HARNESS:agents:BEGIN' not in agents:
            raise SystemExit('INSTALL REGRESSION: FAIL - AGENTS project content was not preserved around managed block')
        runtime_doc=(target/'docs/RUNTIME_VERIFICATION.md').read_text(encoding='utf-8')
        if not runtime_doc.startswith(doc_before) or 'CODEX_PRODUCT_HARNESS:doc-runtime-verification:BEGIN' not in runtime_doc:
            raise SystemExit('INSTALL REGRESSION: FAIL - compatibility doc content was not preserved')
        state=json.loads((target/'.ai/HARNESS_INSTALL_STATE.json').read_text(encoding='utf-8'))
        if state.get('schema_version')<3 or 'README.md' in state.get('records',{}) or 'VERSION' in state.get('records',{}):
            raise SystemExit('INSTALL REGRESSION: FAIL - generic product roots were claimed by Harness ownership')
        for rel in ('.ai/PROJECT.md','.ai/STATE.json','.ai/COMMANDS.json','.ai/RESUME.md','.ai/DECISIONS.md'):
            if (state.get('records',{}).get(rel) or {}).get('mode')!='mutable_seed':
                raise SystemExit(f'INSTALL REGRESSION: FAIL - runtime mutable seed misclassified: {rel}')

        # Legitimate runtime bootstrap may change COMMANDS/REPO_MAP without invalidating installation ownership.
        run([PY,'.ai/scripts/bootstrap_project.py','--write'],target)
        verify=run([PY,'.ai/scripts/verify_installation.py','--root','.','--json'],target)
        report=json.loads(verify)
        if report.get('status')!='pass' or not any(x.get('path')=='.ai/COMMANDS.json' for x in report.get('mutable_runtime_changed',[])):
            raise SystemExit('INSTALL REGRESSION: FAIL - runtime bootstrap mutation was treated as immutable Harness drift')
        commands_after=(target/'.ai/COMMANDS.json').read_bytes()
        runtime_plan,_=plan(target)
        if not runtime_plan['safe_to_apply']:
            raise SystemExit('INSTALL REGRESSION: FAIL - runtime-mutated seed blocked a safe Harness update plan')
        cmd_action=next(x for x in runtime_plan['actions'] if x.get('target_path')=='.ai/COMMANDS.json')
        if cmd_action.get('action')!='PRESERVE_MUTABLE':
            raise SystemExit('INSTALL REGRESSION: FAIL - runtime-mutated COMMANDS.json was not preserved')
        apply(target,runtime_plan['plan_digest'])
        if (target/'.ai/COMMANDS.json').read_bytes()!=commands_after:
            raise SystemExit('INSTALL REGRESSION: FAIL - Harness update overwrote runtime-mutated COMMANDS.json')

        # Product edits outside a managed block are preserved; a fresh plan remains safe.
        with (target/'AGENTS.md').open('a',encoding='utf-8') as f: f.write('\nProduct-only rule after install.\n')
        second,_=plan(target)
        if not second['safe_to_apply']:
            raise SystemExit('INSTALL REGRESSION: FAIL - project edit outside managed block caused a false conflict')

        # A stale digest must fail if a planned container changes before apply.
        stale=second['plan_digest']
        with (target/'CLAUDE.md').open('a',encoding='utf-8') as f: f.write('\nconcurrent project edit\n')
        out=apply(target,stale,expect=1)
        if 'plan digest is stale' not in out:
            raise SystemExit('INSTALL REGRESSION: FAIL - stale plan digest was not rejected')

        # User modification of a whole Harness-owned file must become a hard conflict; no overwrite.
        quality=target/'.ai/QUALITY.json'; quality.write_text(quality.read_text(encoding='utf-8')+'\n',encoding='utf-8'); qhash=sha(quality)
        blocked=run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target)],ROOT,expect=2)
        if '.ai/QUALITY.json' not in blocked or sha(quality)!=qhash:
            raise SystemExit('INSTALL REGRESSION: FAIL - user-modified managed file was overwritten or conflict not reported')

        # Modified managed block is also protected.
        txt=(target/'AGENTS.md').read_text(encoding='utf-8').replace('Read and follow `.ai/harness/surfaces/AGENTS.md`','Read and follow `tampered.md`')
        (target/'AGENTS.md').write_text(txt,encoding='utf-8')
        blocked=run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target)],ROOT,expect=2)
        if 'AGENTS.md' not in blocked:
            raise SystemExit('INSTALL REGRESSION: FAIL - modified managed block was silently accepted')

    print('INSTALL REGRESSION: PASS - protected roots, mutable runtime seeds, namespace relocation, managed blocks, plan digest CAS, and ownership conflicts')

if __name__ == '__main__': main()
