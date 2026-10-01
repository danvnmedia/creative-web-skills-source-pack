#!/usr/bin/env python3
"""Offline source-distribution regression suite for Codex Product Harness v5.4.4.

This proves harness mechanisms, not the host product.
"""
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
sys.dont_write_bytecode = True

from _common import copy_source_tree, safe_temp_base, configure_utf8_stdio, harness_context

ROOT = Path(__file__).resolve().parents[2]
tempfile.tempdir=str(safe_temp_base(ROOT, for_copy=True))
PY = sys.executable
FALSE_TRAITS = {
    'user_facing_web': False, 'external_runtime_dependencies': False,
    'ai_integration': False, 'security_sensitive': False,
    'performance_sensitive': False, 'production_release': False,
    'stateful_user_workflow': False, 'large_binary_data': False,
    'truthful_claims': False, 'harness_modification': False, 'skill_modification': False, 'borrowed_browser_session': False, 'mcp_runtime': False,
}


def run(cmd, cwd=ROOT, expect=0):
    print('SELFTEST RUN:', ' '.join(map(str, cmd)), flush=True)
    process = subprocess.run(
        cmd, cwd=str(cwd), text=True, encoding='utf-8', errors='replace',
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if process.returncode != expect:
        print(process.stdout or '')
        raise RuntimeError(f'expected exit {expect}, got {process.returncode}: {cmd}')
    return process.stdout or ''


def main():
    configure_utf8_stdio()
    if harness_context(ROOT) != 'source':
        raise RuntimeError('extended historical suite is source-distribution-only; use self_test.py --context installed inside a product repository')
    checks=[]
    run([PY, '.ai/scripts/validate_harness.py']); checks.append('structure-and-contract-validator')
    run([PY, '.ai/scripts/provider_policy_lint.py']); checks.append('provider-policy')
    run([PY, '.ai/scripts/surface_drift.py']); checks.append('cross-harness-surface-contract')
    run([PY, '.ai/scripts/harness_security.py']); checks.append('harness-security-baseline')
    run([PY, '.ai/scripts/verify_package.py', '--path', '.']); checks.append('package-source-and-ownership-contract')
    run([PY, '.ai/scripts/v53_regression_test.py']); checks.append('v53-adaptive-trust-skill-eval-regression')
    run([PY, '.ai/scripts/v543_regression_test.py']); checks.append('v543-install-boundary-regression')
    run([PY, '.ai/scripts/v544_regression_test.py']); checks.append('v544-skill-security-compaction-regression')
    syntax = "import pathlib; [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in pathlib.Path('.ai/scripts').glob('*.py')]"
    run([PY, '-c', syntax]); checks.append('python-syntax-without-pycache')
    if shutil.which('node'):
        run(['node','--check','.ai/scripts/browser_smoke.mjs'])
        run(['node','--check','.ai/scripts/browser_flow.mjs'])
        smoke_help=run(['node','.ai/scripts/browser_smoke.mjs','--help'])
        flow_help=run(['node','.ai/scripts/browser_flow.mjs','--help'])
        for token in ('--fresh-output',):
            if token not in smoke_help or token not in flow_help: raise RuntimeError('browser help missing fresh-output control')
        for token in ('waitForAttributeChange','expectNoHorizontalOverflow','expectNoOverlap'):
            if token not in flow_help: raise RuntimeError(f'browser flow help missing {token}')
        checks.append('browser-script-contract')

    # Package verifier must explicitly reject the Windows-backslash ZIP bug from v5.1.
    with tempfile.TemporaryDirectory() as zd:
        badzip=Path(zd)/'bad.zip'
        with zipfile.ZipFile(badzip,'w') as z: z.writestr('bad\\path.txt','x')
        out=run([PY,'.ai/scripts/verify_package.py','--path',str(badzip)],expect=1)
        if 'backslash separators' not in out: raise RuntimeError('portable ZIP separator regression was not detected')
        checks.append('portable-zip-path-rejection')

    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)/'harness'
        copy_source_tree(ROOT,tmp,ignore=shutil.ignore_patterns('__pycache__'))
        run(['git','init','-q'],tmp)
        run(['git','config','user.email','harness-selftest@example.invalid'],tmp)
        run(['git','config','user.name','Harness Self Test'],tmp)
        run(['git','add','.'],tmp); run(['git','commit','-qm','baseline'],tmp)
        run([PY,'.ai/scripts/workspace_hygiene.py','--strict'],tmp); checks.append('clean-workspace-hygiene')

        run([PY,'.ai/scripts/install_regression_test.py'],tmp)
        checks.append('install-overlay-recovery-regression')

        # Ownership baseline: adopt exact files, repair missing files, preserve user modifications.
        run([PY,'.ai/scripts/harness_ownership.py','adopt','--legacy-unsafe'],tmp)
        status=run([PY,'.ai/scripts/harness_ownership.py','status'],tmp)
        if '"missing": 0' not in status: raise RuntimeError('ownership status reported missing files after adopt')
        (tmp/'GEMINI.md').unlink()
        repair=run([PY,'.ai/scripts/harness_ownership.py','repair','--source',str(ROOT)],tmp)
        if 'GEMINI.md' not in repair or not (tmp/'GEMINI.md').exists(): raise RuntimeError('ownership repair failed to restore missing file')
        claude=tmp/'CLAUDE.md'; claude_original=claude.read_text(encoding='utf-8'); claude.write_text(claude_original+'\nuser-local change\n',encoding='utf-8')
        preserve=run([PY,'.ai/scripts/harness_ownership.py','repair','--source',str(ROOT)],tmp)
        if 'CLAUDE.md' not in preserve or 'user-local change' not in claude.read_text(encoding='utf-8'): raise RuntimeError('repair overwrote a user-modified managed file')
        claude.write_text(claude_original,encoding='utf-8')
        run(['git','add','.ai/HARNESS_INSTALL_STATE.json'],tmp); run(['git','commit','-qm','adopt harness ownership'],tmp)
        checks.append('ownership-repair-user-file-preservation')

        # Harness security must fail closed on a secret-like token in the control surface.
        secret=tmp/'.ai/selftest-secret.txt'; secret.write_text('sk-' + 'selftest' + ('0'*24) + '\n',encoding='utf-8')
        sec=run([PY,'.ai/scripts/harness_security.py'],tmp,expect=1)
        if 'secret-like-token' not in sec: raise RuntimeError('harness security did not detect secret-like token')
        secret.unlink(); run([PY,'.ai/scripts/harness_security.py'],tmp)
        checks.append('harness-security-negative')

        # Learning: provenance/confidence + human promotion, no automatic Skill mutation.
        skill_before=(tmp/'.agents/skills/harness-improvement/SKILL.md').read_bytes()
        for pid,conf,evidence in [('proj-a','0.9','evidence-a'),('proj-a','0.8','evidence-b')]:
            run([PY,'.ai/scripts/lesson_candidate.py','capture','--id','lesson-selftest','--trigger','when verification repeats','--action','change hypothesis before retry','--confidence',conf,'--evidence',evidence,'--project-id',pid],tmp)
        promoted=run([PY,'.ai/scripts/lesson_candidate.py','promote','--id','lesson-selftest','--scope','project','--human-approved'],tmp)
        if 'Promotion does not modify Skills automatically' not in promoted: raise RuntimeError('lesson promotion contract missing')
        if (tmp/'.agents/skills/harness-improvement/SKILL.md').read_bytes()!=skill_before: raise RuntimeError('lesson promotion auto-mutated a Skill')
        # Global requires evidence from 2+ projects and enough observations.
        for pid,evidence in [('proj-a','ga'),('proj-b','gb'),('proj-b','gc')]:
            run([PY,'.ai/scripts/lesson_candidate.py','capture','--id','global-selftest','--trigger','when a general failure repeats','--action','use bounded deterministic recovery','--confidence','0.9','--evidence',evidence,'--project-id',pid],tmp)
        run([PY,'.ai/scripts/lesson_candidate.py','promote','--id','global-selftest','--scope','global','--human-approved'],tmp)
        run(['git','add','.ai/lessons'],tmp); run(['git','commit','-qm','selftest curated lessons'],tmp)
        checks.append('provenance-safe-project-learning')

        task={
            'schema_version':5, 'id':'SELFTEST', 'status':'READY',
            'traits':dict(FALSE_TRAITS),
            'verification':{'required_checks':['selftest'],'waivers':[]},
        }
        task_path=tmp/'.ai/tasks/SELFTEST.json'
        task_path.write_text(json.dumps(task,indent=2)+'\n',encoding='utf-8')
        run(['git','add','.ai/tasks/SELFTEST.json'],tmp); run(['git','commit','-qm','add selftest task'],tmp)

        out=run([PY,'.ai/scripts/record_evidence.py','--task','SELFTEST','--check','selftest','--',PY,'-c',"print('Đã lưu; API_KEY=redaction-test-value')"],tmp)
        events=(tmp/'.ai/evidence/events.jsonl').read_text(encoding='utf-8')
        if 'Đã lưu' not in out or 'redaction-test-value' in out or 'redaction-test-value' in events:
            raise RuntimeError('UTF-8 evidence output or redaction failed')
        run([PY,'.ai/scripts/evidence_gate.py','--task','SELFTEST'],tmp); checks.append('fresh-utf8-redacted-evidence')

        mutation=tmp/'verification-mutation.tmp'
        run([PY,'.ai/scripts/record_evidence.py','--task','SELFTEST','--check','must-not-mutate','--',PY,'-c',"from pathlib import Path; Path('verification-mutation.tmp').write_text('x')"],tmp,expect=3)
        mutation.unlink()
        last=json.loads((tmp/'.ai/evidence/events.jsonl').read_text(encoding='utf-8').splitlines()[-1])
        if last.get('status') != 'fail' or not last.get('workspace_mutated_by_check'):
            raise RuntimeError('unexpected verification mutation was not rejected')
        checks.append('verification-mutation-rejection')

        with (tmp/'README.md').open('a',encoding='utf-8') as file: file.write('\nstale mutation\n')
        stale=run([PY,'.ai/scripts/evidence_gate.py','--task','SELFTEST'],tmp,expect=1)
        if 'stale' not in stale: raise RuntimeError('stale evidence was not rejected')
        run(['git','restore','README.md'],tmp); checks.append('stale-evidence-rejection')

        run([PY,'.ai/scripts/close_task.py','--task','SELFTEST'],tmp)
        run([PY,'.ai/scripts/evidence_gate.py','--task','SELFTEST'],tmp)
        if not (tmp/'.ai/evidence/closure-SELFTEST.json').exists(): raise RuntimeError('closure manifest missing')
        with (tmp/'README.md').open('a',encoding='utf-8') as file: file.write('\nsource drift after closure\n')
        drift=run([PY,'.ai/scripts/evidence_gate.py','--task','SELFTEST'],tmp,expect=1)
        if 'non-closure' not in drift: raise RuntimeError('post-closure source drift was not rejected')
        run(['git','restore','README.md'],tmp); checks.append('candidate-closure-source-equivalence')

        webtraits=dict(FALSE_TRAITS)
        webtraits.update({'user_facing_web':True,'external_runtime_dependencies':True,'ai_integration':True,'stateful_user_workflow':True,'large_binary_data':True,'truthful_claims':True,'production_release':True,'harness_modification':True})
        webtask={'id':'WEBTEST','traits':webtraits,'verification':{'required_checks':[],'waivers':[]}}
        (tmp/'.ai/tasks/WEBTEST.json').write_text(json.dumps(webtask,indent=2)+'\n',encoding='utf-8')
        matrix=run([PY,'.ai/scripts/evidence_gate.py','--task','WEBTEST'],tmp,expect=1)
        required=['build','runtime-browser','critical-flow','external-probe','ai-failure-matrix','ai-contract','state-recovery','capacity-degradation','claim-contract','production-smoke','production-critical-flow','harness-security','surface-drift','package-contract','harness-self-test','skill-eval-contract','quarantine-contract','release-witness-contract','waiver-contract','control-decision-contract','mcp-surface-contract','install-collision-contract','source-installed-boundary']
        if any(f'{item}: no evidence' not in matrix for item in required):
            print(matrix); raise RuntimeError('trait-derived gate matrix failed')
        checks.append('expanded-trait-gate-matrix-v5')

        # Same failed check three times must trip the loop guard.
        loop_task={'schema_version':5,'id':'LOOPTEST','status':'READY','traits':dict(FALSE_TRAITS),'verification':{'required_checks':[],'waivers':[]}}
        (tmp/'.ai/tasks/LOOPTEST.json').write_text(json.dumps(loop_task,indent=2)+'\n',encoding='utf-8')
        run(['git','add','.ai/tasks/LOOPTEST.json'],tmp); run(['git','commit','-qm','add loop task'],tmp)
        for _ in range(3):
            ev=run([PY,'.ai/scripts/record_evidence.py','--task','LOOPTEST','--check','repeat-fail','--',PY,'-c',"print('same failure'); raise SystemExit(1)"],tmp,expect=1)
        last=json.loads(ev)
        if last.get('same_failure_repeat_count') != 3: raise RuntimeError('failure signature repeat counter failed')
        guard=run([PY,'.ai/scripts/loop_guard.py','--task','LOOPTEST','--check','repeat-fail'],tmp,expect=2)
        if 'STOP' not in guard: raise RuntimeError('loop guard failed to stop repeated identical failure')
        checks.append('repeat-loop-guard')

        fixture=tmp/'selftest-fixture'; fixture.mkdir()
        (fixture/'a.ts').write_text('const x="https://example.com/a.mp4";\n',encoding='utf-8')
        scanout=fixture/'urls.json'
        run([PY,'.ai/scripts/scan_external_urls.py','--root',str(fixture),'--out',str(scanout)],tmp)
        if json.loads(scanout.read_text(encoding='utf-8')).get('count') != 1:
            raise RuntimeError('external URL scanner failed')
        checks.append('external-url-scanner')

        run(['git','add','.'],tmp); run(['git','commit','-qm','selftest intermediate state'],tmp)
        release_traits=dict(FALSE_TRAITS); release_traits['production_release']=True
        release_task={'schema_version':5,'id':'RELEASETEST','status':'READY','traits':release_traits,'verification':{'required_checks':[],'waivers':[]},'release':{'production_url':'https://example.invalid'}}
        (tmp/'.ai/tasks/RELEASETEST.json').write_text(json.dumps(release_task,indent=2)+'\n',encoding='utf-8')
        run(['git','add','.ai/tasks/RELEASETEST.json'],tmp); run(['git','commit','-qm','add release task'],tmp)
        close_output=run([PY,'.ai/scripts/close_task.py','--task','RELEASETEST','--production-url','https://example.invalid','--ci-url','https://ci.example.invalid/run/1'],tmp)
        if 'EXTERNALLY_PENDING' not in close_output: raise RuntimeError('release was accepted before deployment')
        run(['git','add','.'],tmp); run(['git','commit','-qm','close release candidate'],tmp)
        closure_sha=run(['git','rev-parse','HEAD'],tmp).strip()
        run([PY,'.ai/scripts/record_evidence.py','--task','RELEASETEST','--check','production-smoke','--',PY,'-c',f"print('{closure_sha}')"],tmp)
        run([PY,'.ai/scripts/record_evidence.py','--task','RELEASETEST','--check','production-critical-flow','--',PY,'-c',"print('critical flow pass')"],tmp)
        run([PY,'.ai/scripts/accept_release.py','--task','RELEASETEST','--production-url','https://example.invalid','--deployed-revision',closure_sha,'--ci-url','https://ci.example.invalid/run/1'],tmp)
        run([PY,'.ai/scripts/evidence_gate.py','--task','RELEASETEST'],tmp)
        release_manifest=json.loads((tmp/'.ai/evidence/closure-RELEASETEST.json').read_text(encoding='utf-8'))
        if release_manifest.get('release',{}).get('status')!='production_accepted': raise RuntimeError('release acceptance state not persisted')
        checks.append('candidate-deploy-production-acceptance')

        bad=tmp/'.agents/skills/runtime-verification/SKILL.md'
        backup=bad.read_text(encoding='utf-8'); bad.unlink()
        negative=run([PY,'.ai/scripts/validate_harness.py'],tmp,expect=1)
        if 'missing skill' not in negative: raise RuntimeError('negative packaging validator failed')
        bad.parent.mkdir(parents=True,exist_ok=True); bad.write_text(backup,encoding='utf-8')
        checks.append('negative-packaging-validator')

    print('HARNESS SELF-TEST: PASS')
    for check in checks: print(f'- {check}')
    print('Note: this proves harness mechanisms, not a target product. Product completion still requires task evidence.')


if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'HARNESS SELF-TEST: FAIL - {exc}')
        raise SystemExit(1)
