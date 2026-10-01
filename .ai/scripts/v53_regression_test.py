#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
sys.dont_write_bytecode = True
from _common import copy_source_tree, safe_temp_base

ROOT=Path(__file__).resolve().parents[2]
tempfile.tempdir=str(safe_temp_base(ROOT, for_copy=True))
PY=sys.executable


def run(cmd,cwd,expect=0):
    p=subprocess.run(cmd,cwd=str(cwd),text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode!=expect:
        print(p.stdout or '')
        raise SystemExit(f'V5.3 REGRESSION: FAIL - expected {expect}, got {p.returncode}: {cmd}')
    return p.stdout or ''


def false_traits():
    return {k:False for k in ['user_facing_web','external_runtime_dependencies','ai_integration','security_sensitive','performance_sensitive','production_release','stateful_user_workflow','large_binary_data','truthful_claims','harness_modification','skill_modification','borrowed_browser_session']}


def main():
    run([PY,'.ai/scripts/skill_eval.py','validate'],ROOT)
    with tempfile.TemporaryDirectory() as td_raw:
        td=Path(td_raw)
        tmp=td/'harness'; copy_source_tree(ROOT,tmp,ignore=shutil.ignore_patterns('__pycache__','.git'))
        # Repo mapping: observed scripts may be enabled; framework defaults stay inferred.
        (tmp/'package.json').write_text(json.dumps({'scripts':{'dev':'vite','build':'vite build'},'devDependencies':{'vite':'1.0.0'}},indent=2)+'\n',encoding='utf-8')
        (tmp/'package-lock.json').write_text('{}\n',encoding='utf-8')
        out=run([PY,'.ai/scripts/bootstrap_project.py','--write'],tmp)
        commands=json.loads((tmp/'.ai/COMMANDS.json').read_text(encoding='utf-8'))
        repo_map=json.loads((tmp/'.ai/REPO_MAP.json').read_text(encoding='utf-8'))
        if commands['commands'].get('dev')!='npm run dev' or commands['commands'].get('build')!='npm run build':
            raise SystemExit('V5.3 REGRESSION: FAIL - observed package scripts were not enabled')
        if commands['runtime'].get('start_url') is not None:
            raise SystemExit('V5.3 REGRESSION: FAIL - inferred runtime URL was silently enabled')
        hints=[x for x in repo_map['entries'] if x.get('kind')=='runtime-hint' and x.get('trust')=='inferred']
        if not hints: raise SystemExit('V5.3 REGRESSION: FAIL - inferred runtime hint missing from repo map')

        # Execution profile routing.
        task={'schema_version':5,'id':'PROFILE','mode':'FEATURE','status':'READY','traits':false_traits(),'execution_contract':{'profile':'auto','cross_session_expected':False,'external_wait_expected':False,'context_refresh_expected':False},'risk':{'level':'medium'},'verification':{'required_checks':[],'waivers':[]}}
        taskp=tmp/'.ai/tasks/PROFILE.json'; taskp.parent.mkdir(parents=True,exist_ok=True); taskp.write_text(json.dumps(task,indent=2)+'\n',encoding='utf-8')
        native=run([PY,'.ai/scripts/execution_profile.py','--task','PROFILE'],tmp)
        if 'profile=native' not in native: raise SystemExit('V5.3 REGRESSION: FAIL - native profile routing failed')
        task['execution_contract']['cross_session_expected']=True; taskp.write_text(json.dumps(task,indent=2)+'\n',encoding='utf-8')
        portable=run([PY,'.ai/scripts/execution_profile.py','--task','PROFILE','--write'],tmp)
        if 'profile=portable' not in portable: raise SystemExit('V5.3 REGRESSION: FAIL - portable profile routing failed')
        task=json.loads(taskp.read_text(encoding='utf-8')); task['traits']['security_sensitive']=True; task['execution_contract']['profile']='native'; taskp.write_text(json.dumps(task,indent=2)+'\n',encoding='utf-8')
        weak=run([PY,'.ai/scripts/execution_profile.py','--task','PROFILE'],tmp,expect=1)
        if 'weaker than derived minimum audited' not in weak: raise SystemExit('V5.3 REGRESSION: FAIL - weak explicit profile was not rejected')

        # Git/evidence-backed verified checkpoint.
        run(['git','init','-q'],tmp); run(['git','config','user.email','v53@example.invalid'],tmp); run(['git','config','user.name','V53 Test'],tmp)
        task=json.loads(taskp.read_text(encoding='utf-8')); task['traits']['security_sensitive']=False; task['execution_contract']={'profile':'portable','resolved_profile':'portable','cross_session_expected':True,'external_wait_expected':False,'context_refresh_expected':False,'routing_reasons':['test']}; taskp.write_text(json.dumps(task,indent=2)+'\n',encoding='utf-8')
        run(['git','add','.'],tmp); run(['git','commit','-qm','baseline'],tmp)
        run([PY,'.ai/scripts/record_evidence.py','--task','PROFILE','--check','focused-test','--',PY,'-c',"print('ok')"],tmp)
        run([PY,'.ai/scripts/verified_checkpoint.py','checkpoint','--task','PROFILE','--completed','focused test passes','--next-action','continue verification','--check','focused-test'],tmp)
        run([PY,'.ai/scripts/verified_checkpoint.py','validate','--task','PROFILE'],tmp)
        run([PY,'.ai/scripts/record_evidence.py','--task','PROFILE','--check','verified-progress','--',PY,'.ai/scripts/verified_checkpoint.py','validate','--task','PROFILE'],tmp)
        gate=run([PY,'.ai/scripts/evidence_gate.py','--task','PROFILE'],tmp,expect=0)
        if 'EVIDENCE GATE: PASS' not in gate:
            raise SystemExit('V5.3 REGRESSION: FAIL - verified-progress did not satisfy the portable profile gate')

        # Legacy synthetic routing fixture remains diagnostic only; strict acceptance is tested in v552.
        matrix=json.loads((tmp/'.ai/evals/skill-routing.json').read_text(encoding='utf-8'))
        trusted=td/'trusted-runs.jsonl'; rows=[]
        for case in matrix['cases']:
            observed=[case['skill']] if case['polarity']=='should_trigger' else []
            for n in (1,2): rows.append(json.dumps({'case_id':case['id'],'run':n,'observed_skills':observed,'telemetry':'trace'}))
        trusted.write_text('\n'.join(rows)+'\n',encoding='utf-8')
        report=run([PY,'.ai/scripts/skill_eval.py','report','--runs',str(trusted),'--legacy-diagnostic','--fail-on-regression'],tmp)
        if '"status": "pass"' not in report: raise SystemExit('V5.3 REGRESSION: FAIL - trusted skill routing report failed')
        untrusted=td/'untrusted-runs.jsonl'; untrusted.write_text('\n'.join(x.replace('"trace"','"self_report"') for x in rows)+'\n',encoding='utf-8')
        bad=run([PY,'.ai/scripts/skill_eval.py','report','--runs',str(untrusted),'--legacy-diagnostic','--fail-on-regression'],tmp,expect=1)
        if 'untrusted-telemetry:self_report' not in bad: raise SystemExit('V5.3 REGRESSION: FAIL - self-report was accepted as activation proof')

        # Portable Agent Plugins export is skills-only and path portable.
        plugin=td/'plugin.zip'; run([PY,'.ai/scripts/export_agent_plugin.py','--out',str(plugin)],tmp)
        with zipfile.ZipFile(plugin) as z:
            names=[i.filename for i in z.infolist() if not i.is_dir()]
        if 'plugin.json' not in names or len([n for n in names if n.startswith('skills/') and n.endswith('/SKILL.md')])!=13 or any('\\' in n for n in names):
            raise SystemExit('V5.3 REGRESSION: FAIL - Agent Plugins export contract failed')

    print('V5.3 REGRESSION: PASS - trust mapping, adaptive profiles, verified checkpoints, skill-eval trust, and portable export')


if __name__=='__main__':
    main()
