#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
from _common import harness_temp_dir
ROOT=Path(__file__).resolve().parents[2]; PY=sys.executable

def run(cmd,cwd=ROOT,expect=0):
    p=subprocess.run(cmd,cwd=str(cwd),text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode!=expect:
        print(p.stdout or '')
        raise SystemExit(f'V5.5 SNAPSHOT REGRESSION: FAIL expected {expect}, got {p.returncode}: {cmd}')
    return p.stdout or ''

def main():
    with harness_temp_dir(ROOT,for_copy=True,prefix='v550-snapshot-') as td:
        target=td/'legacy'; target.mkdir(); (target/'package.json').write_text('{"name":"legacy"}\n',encoding='utf-8')
        planp=td/'plan.json'; run([PY,'.ai/scripts/install_plan.py','--source',str(ROOT),'--target',str(target),'--out',str(planp)],ROOT); plan=json.loads(planp.read_text())
        run([PY,str(ROOT/'INSTALL_HARNESS.py'),'--target',str(target),'--apply','--confirm',plan['plan_digest']],ROOT)
        traits={k:False for k in ['user_facing_web','ai_integration','security_sensitive','performance_sensitive','production_release','external_runtime_dependencies','stateful_user_workflow','large_binary_data','truthful_claims','harness_modification','skill_modification','borrowed_browser_session','mcp_runtime']}; traits['production_release']=True
        task={'schema_version':6,'id':'TASK-SNAPSHOT','mode':'CRITICAL','status':'IN_PROGRESS','objective':'snapshot fixture','user_outcome':'local snapshot only','scope':{'in':['fixture'],'out':[]},'traits':traits,'execution_contract':{'profile':'native','resolved_profile':'native','cross_session_expected':False,'external_wait_expected':False,'context_refresh_expected':False,'routing_reasons':[],'checkpoint_policy':'verified-boundary-only'},'experience_contract':{},'state_contract':{},'acceptance_criteria':['unit evidence'],'critical_user_flows':[],'change_budget':{},'verification':{'required_checks':['unit'],'waivers':[],'findings':[],'check_states':{},'notes':''},'release':{'candidate_revision':None,'production_url':'https://example.invalid','revision_marker':None,'rollback':'fixture'},'risk':{'level':'high','human_gate':False,'reasons':[]},'notes':[]}
        tp=target/'.ai/tasks/TASK-SNAPSHOT.json'; tp.parent.mkdir(parents=True,exist_ok=True); tp.write_text(json.dumps(task,indent=2)+'\n')
        state=json.loads((target/'.ai/STATE.json').read_text()); state['active_task']='.ai/tasks/TASK-SNAPSHOT.json'; state['status']='IN_PROGRESS'; (target/'.ai/STATE.json').write_text(json.dumps(state,indent=2)+'\n')
        run([PY,'.ai/scripts/record_evidence.py','--task','TASK-SNAPSHOT','--check','unit','--',PY,'-c',"print('snapshot unit')"],target)
        close=run([PY,'.ai/scripts/close_task.py','--task','TASK-SNAPSHOT','--snapshot'],target)
        if 'LOCAL_SNAPSHOT_ACCEPTED' not in close: raise SystemExit('V5.5 SNAPSHOT REGRESSION: FAIL local snapshot closure')
        rejected=run([PY,'.ai/scripts/accept_release.py','--task','TASK-SNAPSHOT','--production-url','https://example.invalid','--deployed-revision','deadbeef','--ci-url','https://ci.invalid'],target,expect=1)
        if 'local snapshot closure cannot be production-accepted' not in rejected: raise SystemExit('V5.5 SNAPSHOT REGRESSION: FAIL production boundary')
        run([PY,'.ai/scripts/self_test.py','--context','installed'],target)
    print('V5.5 SNAPSHOT REGRESSION: PASS - non-Git local snapshot closure is explicit and never production acceptance')
if __name__=='__main__': main()
