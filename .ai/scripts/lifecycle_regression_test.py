#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
from _common import copy_source_tree, safe_temp_base
ROOT = Path(__file__).resolve().parents[2]
tempfile.tempdir=str(safe_temp_base(ROOT, for_copy=True))
PY = sys.executable


def run(cmd, cwd, expect=0):
    p = subprocess.run(cmd, cwd=str(cwd), text=True, encoding='utf-8', errors='replace', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != expect:
        print(p.stdout or '')
        raise SystemExit(f'LIFECYCLE REGRESSION: FAIL - expected {expect}, got {p.returncode}: {cmd}')
    return p.stdout or ''


def traits(**overrides):
    data = {k: False for k in [
        'user_facing_web','external_runtime_dependencies','ai_integration','security_sensitive',
        'performance_sensitive','production_release','stateful_user_workflow','large_binary_data',
        'truthful_claims','harness_modification','skill_modification'
    ]}
    data.update(overrides)
    return data


def execution(profile='native'):
    return {
        'profile': profile,
        'resolved_profile': profile if profile != 'auto' else None,
        'cross_session_expected': profile in {'portable','audited'},
        'external_wait_expected': False,
        'context_refresh_expected': False,
        'routing_reasons': ['lifecycle-regression'],
        'checkpoint_policy': 'verified-boundary-only',
    }


def main():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw) / 'harness'
        copy_source_tree(ROOT, tmp, ignore=shutil.ignore_patterns('.git','__pycache__','.ai/REPO_MAP.json'))
        run(['git','init','-q'], tmp)
        run(['git','config','user.email','lifecycle@example.invalid'], tmp)
        run(['git','config','user.name','Lifecycle Regression'], tmp)
        run(['git','add','.'], tmp)
        run(['git','commit','-qm','baseline'], tmp)

        # Candidate closure still preserves evidence identity and rejects source drift.
        task = {
            'schema_version': 4, 'id': 'LIFE', 'mode': 'FEATURE', 'status': 'READY',
            'traits': traits(), 'execution_contract': execution('native'),
            'verification': {'required_checks': ['focused-test'], 'waivers': []},
            'release': {'candidate_revision': None, 'production_url': None, 'revision_marker': None, 'rollback': None},
            'risk': {'level': 'medium', 'human_gate': False, 'reasons': []},
        }
        tp = tmp/'.ai/tasks/LIFE.json'; tp.parent.mkdir(parents=True, exist_ok=True)
        tp.write_text(json.dumps(task, indent=2)+'\n', encoding='utf-8')
        run(['git','add','.ai/tasks/LIFE.json'], tmp); run(['git','commit','-qm','add lifecycle task'], tmp)
        run([PY,'.ai/scripts/record_evidence.py','--task','LIFE','--check','focused-test','--',PY,'-c',"print('pass')"], tmp)
        run([PY,'.ai/scripts/close_task.py','--task','LIFE'], tmp)
        run([PY,'.ai/scripts/evidence_gate.py','--task','LIFE'], tmp)
        with (tmp/'README.md').open('a', encoding='utf-8') as f: f.write('\npost-closure drift\n')
        drift = run([PY,'.ai/scripts/evidence_gate.py','--task','LIFE'], tmp, expect=1)
        if 'non-closure' not in drift:
            raise SystemExit('LIFECYCLE REGRESSION: FAIL - post-closure source drift not rejected')
        run(['git','restore','README.md'], tmp)
        run(['git','add','.ai/tasks/LIFE.json','.ai/STATE.json','.ai/evidence/closure-LIFE.json'], tmp)
        run(['git','commit','-qm','commit lifecycle closure'], tmp)

        # Audited production work must persist only verified progress; checkpoint runtime state must not dirty closure.
        release_task = {
            'schema_version': 4, 'id': 'RELEASE', 'mode': 'CRITICAL', 'status': 'READY',
            'traits': traits(production_release=True),
            'execution_contract': {
                'profile': 'auto', 'resolved_profile': None, 'cross_session_expected': False,
                'external_wait_expected': False, 'context_refresh_expected': False,
                'routing_reasons': [], 'checkpoint_policy': 'verified-boundary-only'
            },
            'verification': {'required_checks': [], 'waivers': []},
            'release': {'candidate_revision': None, 'production_url': 'https://example.invalid', 'revision_marker': None, 'rollback': 'git revert'},
            'risk': {'level': 'high', 'human_gate': False, 'reasons': ['release regression']},
        }
        rp = tmp/'.ai/tasks/RELEASE.json'; rp.write_text(json.dumps(release_task, indent=2)+'\n', encoding='utf-8')
        routed = run([PY,'.ai/scripts/execution_profile.py','--task','RELEASE','--write'], tmp)
        if 'profile=audited' not in routed:
            raise SystemExit('LIFECYCLE REGRESSION: FAIL - production task did not route audited')
        run(['git','add','.ai/tasks/RELEASE.json'], tmp); run(['git','commit','-qm','add audited release task'], tmp)
        run([PY,'.ai/scripts/record_evidence.py','--task','RELEASE','--check','candidate-local','--',PY,'-c',"print('candidate local pass')"], tmp)
        run([PY,'.ai/scripts/verified_checkpoint.py','checkpoint','--task','RELEASE','--completed','candidate local verified','--next-action','close candidate','--check','candidate-local'], tmp)
        run([PY,'.ai/scripts/record_evidence.py','--task','RELEASE','--check','verified-progress','--',PY,'.ai/scripts/verified_checkpoint.py','validate','--task','RELEASE'], tmp)
        # Runtime checkpoint may remain untracked; source hygiene/closure must still work.
        run([PY,'.ai/scripts/workspace_hygiene.py','--strict','--allow-evidence'], tmp)
        close = run([PY,'.ai/scripts/close_task.py','--task','RELEASE','--production-url','https://example.invalid','--ci-url','https://ci.example.invalid/run/1'], tmp)
        if 'EXTERNALLY_PENDING' not in close:
            raise SystemExit('LIFECYCLE REGRESSION: FAIL - release was not left externally pending')
        run(['git','add','.ai/tasks/RELEASE.json','.ai/STATE.json','.ai/evidence/closure-RELEASE.json'], tmp)
        run(['git','commit','-qm','close release candidate'], tmp)
        closure_sha = run(['git','rev-parse','HEAD'], tmp).strip()
        run([PY,'.ai/scripts/record_evidence.py','--task','RELEASE','--check','production-smoke','--',PY,'-c',f"print('{closure_sha}')"], tmp)
        run([PY,'.ai/scripts/record_evidence.py','--task','RELEASE','--check','production-critical-flow','--',PY,'-c',"print('critical flow pass')"], tmp)
        run([PY,'.ai/scripts/accept_release.py','--task','RELEASE','--production-url','https://example.invalid','--deployed-revision',closure_sha,'--ci-url','https://ci.example.invalid/run/1'], tmp)
        gate = run([PY,'.ai/scripts/evidence_gate.py','--task','RELEASE'], tmp)
        if 'EVIDENCE GATE: PASS' not in gate:
            raise SystemExit('LIFECYCLE REGRESSION: FAIL - production acceptance gate failed')

    print('LIFECYCLE REGRESSION: PASS - closure integrity, audited verified-progress, runtime-state cleanliness, and production acceptance')


if __name__ == '__main__':
    main()
