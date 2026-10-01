#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, hashlib
from pathlib import Path
sys.dont_write_bytecode=True
from _common import harness_temp_dir
ROOT=Path(__file__).resolve().parents[2]; PY=sys.executable

def run(cmd,cwd,expect=0):
    p=subprocess.run(cmd,cwd=str(cwd),text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode!=expect:
        print(p.stdout or '')
        raise SystemExit(f'V5.4.5 REGRESSION: FAIL expected {expect}, got {p.returncode}: {cmd}')
    return p.stdout or ''

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def make_plan(target:Path, out:Path):
    run([PY,'.ai/scripts/install_plan.py','--source',str(ROOT),'--target',str(target),'--out',str(out)],ROOT)
    return json.loads(out.read_text(encoding='utf-8'))

def main():
    with harness_temp_dir(ROOT,for_copy=True,prefix='v545-') as td:
        target=td/'product'; target.mkdir()
        (target/'package.json').write_text('{"name":"fixture","scripts":{"dev":"vite","test":"vitest"}}\n',encoding='utf-8')
        plan=make_plan(target,td/'plan.json')
        run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target),'--apply','--confirm',plan['plan_digest']],ROOT)

        statep=target/'.ai/HARNESS_INSTALL_STATE.json'; state=json.loads(statep.read_text(encoding='utf-8'))
        if state.get('schema_version')<3: raise SystemExit('V5.4.5 REGRESSION: FAIL schema 3 install state missing')
        mutable={'.ai/PROJECT.md','.ai/STATE.json','.ai/COMMANDS.json','.ai/RESUME.md','.ai/DECISIONS.md'}
        if any((state['records'].get(x) or {}).get('mode')!='mutable_seed' for x in mutable):
            raise SystemExit('V5.4.5 REGRESSION: FAIL mutable seed classification incomplete')

        # Runtime bootstrap changes COMMANDS.json. It must remain a valid installed state.
        before=sha(target/'.ai/COMMANDS.json')
        run([PY,'.ai/scripts/bootstrap_project.py','--write'],target)
        after=sha(target/'.ai/COMMANDS.json')
        if before==after: raise SystemExit('V5.4.5 REGRESSION: FAIL fixture did not exercise COMMANDS mutation')
        report=json.loads(run([PY,'.ai/scripts/verify_installation.py','--root','.','--json'],target))
        if report.get('status')!='pass' or report.get('mutable_runtime_changed_count',0)<1:
            raise SystemExit('V5.4.5 REGRESSION: FAIL legitimate runtime mutation failed installation verification')

        # STATE.json is also runtime mutable. A lifecycle-style state change must not be called Harness tamper.
        sd=json.loads((target/'.ai/STATE.json').read_text(encoding='utf-8')); sd['status']='IN_PROGRESS'; sd['active_task']='.ai/tasks/FIXTURE.json'
        (target/'.ai/STATE.json').write_text(json.dumps(sd,indent=2)+'\n',encoding='utf-8')
        report=json.loads(run([PY,'.ai/scripts/verify_installation.py','--root','.','--json'],target))
        changed={x['path'] for x in report.get('mutable_runtime_changed',[])}
        if not {'.ai/COMMANDS.json','.ai/STATE.json'}.issubset(changed):
            raise SystemExit('V5.4.5 REGRESSION: FAIL runtime mutable changes were not classified truthfully')

        # A re-install/update plan must preserve those changes rather than force manual hash rebaseline.
        commands_bytes=(target/'.ai/COMMANDS.json').read_bytes(); state_bytes=(target/'.ai/STATE.json').read_bytes()
        plan2=make_plan(target,td/'plan2.json')
        acts={x['target_path']:x['action'] for x in plan2['actions']}
        if acts.get('.ai/COMMANDS.json')!='PRESERVE_MUTABLE' or acts.get('.ai/STATE.json')!='PRESERVE_MUTABLE':
            raise SystemExit('V5.4.5 REGRESSION: FAIL runtime changes were not preserved by update plan')
        run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target),'--apply','--confirm',plan2['plan_digest']],ROOT)
        if (target/'.ai/COMMANDS.json').read_bytes()!=commands_bytes or (target/'.ai/STATE.json').read_bytes()!=state_bytes:
            raise SystemExit('V5.4.5 REGRESSION: FAIL update overwrote runtime mutable content')

        # Immutable Harness controls remain hash-strict.
        quality=target/'.ai/QUALITY.json'; quality_source_bytes=(ROOT/'.ai/QUALITY.json').read_bytes(); quality.write_bytes(quality.read_bytes()+b'\n')
        out=run([PY,'.ai/scripts/verify_installation.py','--root','.'],target,expect=1)
        if 'managed file drift: .ai/QUALITY.json' not in out:
            raise SystemExit('V5.4.5 REGRESSION: FAIL immutable control drift was weakened')

        # Simulate a v5.4.4 schema-2 ownership state and prove migration does not clobber modified runtime bytes.
        quality.write_bytes(quality_source_bytes)
        st=json.loads(statep.read_text(encoding='utf-8')); st['schema_version']=2
        for rel in mutable:
            rec=st['records'][rel]
            rec['mode']='whole_file'; rec['last_managed_sha256']=rec.get('last_seed_sha256'); rec.pop('last_seed_sha256',None); rec.pop('runtime_modified',None)
        statep.write_text(json.dumps(st,indent=2)+'\n',encoding='utf-8')
        plan3=make_plan(target,td/'plan3.json')
        if not plan3['safe_to_apply']:
            raise SystemExit('V5.4.5 REGRESSION: FAIL schema-2 runtime ownership cannot migrate safely')
        run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target),'--apply','--confirm',plan3['plan_digest']],ROOT)
        migrated=json.loads(statep.read_text(encoding='utf-8'))
        if migrated.get('schema_version')<3 or any((migrated['records'].get(x) or {}).get('mode')!='mutable_seed' for x in mutable):
            raise SystemExit('V5.4.5 REGRESSION: FAIL schema-2 mutable ownership was not migrated')
    print('V5.4.5 REGRESSION: PASS - runtime mutable ownership, no manual rebaseline, safe update preservation, immutable hash strictness, schema-2 migration')

if __name__=='__main__': main()
