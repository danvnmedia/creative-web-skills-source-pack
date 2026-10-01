#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
from _common import harness_temp_dir, load_events, safe_temp_base
ROOT=Path(__file__).resolve().parents[2]; PY=sys.executable

def run(cmd,cwd=ROOT,expect=0,env=None):
    print('V550 RUN:', ' '.join(map(str,cmd)), flush=True)
    p=subprocess.run(cmd,cwd=str(cwd),text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
    if p.returncode!=expect:
        print(p.stdout or '')
        raise SystemExit(f'V5.5.0 REGRESSION: FAIL expected {expect}, got {p.returncode}: {cmd}')
    return p.stdout or ''

def install(target:Path, td:Path):
    planp=td/f'plan-{target.name}.json'
    run([PY,'.ai/scripts/install_plan.py','--source',str(ROOT),'--target',str(target),'--out',str(planp)],ROOT)
    plan=json.loads(planp.read_text(encoding='utf-8'))
    if not plan.get('safe_to_apply'): raise SystemExit('V5.5.0 REGRESSION: FAIL install plan unsafe')
    run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target),'--apply','--confirm',plan['plan_digest']],ROOT)

def task_doc(tid='TASK-V550',production=False):
    traits={k:False for k in ['user_facing_web','ai_integration','security_sensitive','performance_sensitive','production_release','external_runtime_dependencies','stateful_user_workflow','large_binary_data','truthful_claims','harness_modification','skill_modification','borrowed_browser_session','mcp_runtime']}
    traits['production_release']=production
    return {
      'schema_version':6,'id':tid,'mode':'CRITICAL' if production else 'FEATURE','status':'IN_PROGRESS','objective':'v5.5 fixture','user_outcome':'verified fixture',
      'scope':{'in':['fixture'],'out':[]},'traits':traits,
      'execution_contract':{'profile':'native','resolved_profile':'native','cross_session_expected':False,'external_wait_expected':False,'context_refresh_expected':False,'routing_reasons':[],'checkpoint_policy':'verified-boundary-only'},
      'experience_contract':{},'state_contract':{},'acceptance_criteria':['unit evidence is fresh'],'critical_user_flows':[],'change_budget':{'expected_files':1,'schema_change':False,'public_api_change':False},
      'verification':{'required_checks':['unit'],'waivers':[],'findings':[],'check_states':{},'notes':''},
      'release':{'candidate_revision':None,'production_url':'https://example.invalid' if production else None,'revision_marker':None,'rollback':'fixture'},
      'risk':{'level':'high' if production else 'low','human_gate':False,'reasons':[]},'notes':[]
    }

def init_git(target:Path):
    run(['git','init','-q'],target); run(['git','config','user.email','v550@example.invalid'],target); run(['git','config','user.name','V550 Regression'],target)
    run(['git','add','.'],target); run(['git','commit','-qm','baseline'],target)

def main():
    with harness_temp_dir(ROOT,for_copy=True,prefix='v550-') as td:
        target=td/'product'; target.mkdir(); (target/'package.json').write_text('{"name":"fixture","scripts":{"build":"python -c \\\"print(1)\\\""}}\n',encoding='utf-8')
        install(target,td)
        report=json.loads(run([PY,'.ai/scripts/verify_installation.py','--root','.','--json'],target))
        if report.get('status')!='pass': raise SystemExit('V5.5.0 REGRESSION: FAIL installed verification')
        wrong=run([PY,'.ai/scripts/validate_harness.py'],target,expect=2)
        if 'wrong boundary' not in wrong.lower(): raise SystemExit('V5.5.0 REGRESSION: FAIL source validator did not refuse installed boundary clearly')
        extended=run([PY,'.ai/scripts/self_test_extended.py'],target,expect=1)
        if 'source-distribution-only' not in extended: raise SystemExit('V5.5.0 REGRESSION: FAIL extended suite boundary message missing')

        # Immutable byte restoration must be exact; text/newline normalization must not be needed.
        quality=target/'.ai/QUALITY.json'; exact=quality.read_bytes(); quality.write_bytes(exact+b'\n')
        drift=run([PY,'.ai/scripts/verify_installation.py','--root','.'],target,expect=1)
        if 'managed file drift: .ai/QUALITY.json' not in drift: raise SystemExit('V5.5.0 REGRESSION: FAIL immutable drift not detected')
        quality.write_bytes(exact); run([PY,'.ai/scripts/verify_installation.py','--root','.'],target)

        task=task_doc(); taskp=target/'.ai/tasks/TASK-V550.json'; taskp.parent.mkdir(parents=True,exist_ok=True); taskp.write_text(json.dumps(task,indent=2)+'\n',encoding='utf-8')
        state=json.loads((target/'.ai/STATE.json').read_text(encoding='utf-8')); state['active_task']='.ai/tasks/TASK-V550.json'; state['status']='IN_PROGRESS'; (target/'.ai/STATE.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
        init_git(target); run([PY,'.ai/scripts/validate_task.py','--task','TASK-V550'],target)

        out=run([PY,'.ai/scripts/record_evidence.py','--task','.ai/tasks/TASK-V550.json','--check','unit','--',PY,'-c',"print('unit ok')"],target)
        event=json.loads(out)
        if event.get('task')!='TASK-V550' or not event.get('log_path') or '/' not in event['log_path']: raise SystemExit('V5.5.0 REGRESSION: FAIL canonical task/log contract')
        abs_task=str(taskp.resolve()); out2=run([PY,'.ai/scripts/record_evidence.py','--task',abs_task,'--check','alias','--',PY,'-c',"print('alias ok')"],target)
        if json.loads(out2).get('task')!='TASK-V550': raise SystemExit('V5.5.0 REGRESSION: FAIL absolute task path did not canonicalize')
        bad=run([PY,'.ai/scripts/record_evidence.py','--task','../../outside','--check','unit','--',PY,'-c','print(1)'],target,expect=1)
        if 'escapes .ai/tasks' not in bad and 'task not found' not in bad: raise SystemExit('V5.5.0 REGRESSION: FAIL path traversal locator not rejected')

        # Concurrent writers: per-event files are truth; JSONL remains parseable compatibility index.
        procs=[]
        for i in range(8):
            procs.append(subprocess.Popen([PY,'.ai/scripts/record_evidence.py','--task','TASK-V550','--check',f'concurrent-{i}','--',PY,'-c',f"print({i})"],cwd=str(target),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace'))
        for p in procs:
            text=p.communicate(timeout=60)[0]
            if p.returncode!=0: print(text); raise SystemExit('V5.5.0 REGRESSION: FAIL concurrent writer')
        events=load_events(target/'.ai/evidence/events.jsonl')
        if sum(1 for e in events if str(e.get('check','')).startswith('concurrent-'))!=8: raise SystemExit('V5.5.0 REGRESSION: FAIL concurrent events missing/corrupt')
        # Prove compatibility JSONL is still valid line-by-line.
        for line in (target/'.ai/evidence/events.jsonl').read_text(encoding='utf-8').splitlines(): json.loads(line)

        run([PY,'.ai/scripts/evidence_gate.py','--task','TASK-V550'],target)
        # Lifecycle-only edits do not stale product evidence.
        st=json.loads((target/'.ai/STATE.json').read_text(encoding='utf-8')); st['status']='BLOCKED'; (target/'.ai/STATE.json').write_text(json.dumps(st,indent=2)+'\n',encoding='utf-8')
        (target/'.ai/RESUME.md').write_text('# runtime handoff\n',encoding='utf-8')
        run([PY,'.ai/scripts/evidence_gate.py','--task','TASK-V550'],target)
        # Contract edit must stale evidence even though task file is excluded from product digest.
        original_task=taskp.read_bytes(); changed=json.loads(original_task); changed['acceptance_criteria'].append('new contract'); taskp.write_text(json.dumps(changed,indent=2)+'\n',encoding='utf-8')
        stale=run([PY,'.ai/scripts/evidence_gate.py','--task','TASK-V550'],target,expect=1)
        if 'task contract changed' not in stale: raise SystemExit('V5.5.0 REGRESSION: FAIL task-contract staleness not detected')
        taskp.write_bytes(original_task); run([PY,'.ai/scripts/evidence_gate.py','--task','TASK-V550'],target)

        run([PY,'.ai/scripts/verified_checkpoint.py','checkpoint','--task','TASK-V550','--completed','unit verified','--next-action','close candidate','--check','unit','--update-state','--update-resume'],target)
        cp=json.loads((target/'.ai/checkpoints/TASK-V550.json').read_text(encoding='utf-8'))
        lp=cp['evidence'][0].get('log_path')
        if not lp or not (target/lp).is_file(): raise SystemExit('V5.5.0 REGRESSION: FAIL checkpoint log provenance')
        run([PY,'.ai/scripts/verified_checkpoint.py','validate','--task','TASK-V550'],target)
        # Commit lifecycle surfaces before closure; evidence/checkpoint paths remain runtime exclusions.
        run(['git','add','.ai/STATE.json','.ai/RESUME.md'],target); run(['git','commit','-qm','checkpoint lifecycle'],target)
        run([PY,'.ai/scripts/close_task.py','--task','TASK-V550'],target)
        run([PY,'.ai/scripts/self_test.py','--context','installed'],target)

        q=json.loads(run([PY,'.ai/scripts/quarantine_scan.py','--target','.ai/scripts/quarantine_scan.py','--fail-on','block'],target))
        if q['counts']['block']!=0 or q['counts'].get('informational',0)<2: raise SystemExit('V5.5.0 REGRESSION: FAIL scanner rule-definition classification')
        doctor=run([PY,'.ai/scripts/harness_doctor.py'],target)
        if 'browser capability:' not in doctor or 'project-local reproducible Playwright' not in doctor: raise SystemExit('V5.5.0 REGRESSION: FAIL browser capability taxonomy')
        explicit=target/'.ai/checkpoints/tmp-explicit'; env=os.environ.copy(); env['HARNESS_TMP']=str(explicit); env.pop('HARNESS_TEMP_DIR',None)
        tempout=run([PY,'-c',"import sys; sys.path.insert(0,'.ai/scripts'); from _common import safe_temp_base,root_from_script; print(safe_temp_base(root_from_script()))"],target,env=env)
        if str(explicit.resolve()) not in tempout: raise SystemExit('V5.5.0 REGRESSION: FAIL safe temp override/fallback')

    print('V5.5.0 REGRESSION: PASS - evidence architecture, boundary routing, Windows-safe primitives, concurrency, lifecycle freshness, checkpoint provenance')
if __name__=='__main__': main()
