#!/usr/bin/env python3
"""Recorder status regressions; subprocess fixtures are not application acceptance."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True
import _common as c
import record_evidence as recorder
ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable

ENVIRONMENT = ('COMMAND_UNAVAILABLE', 'SERVER_IDENTITY_MISMATCH', 'PORT_IN_USE',
               'spawn EPERM', 'PermissionError', 'sandbox denied',
               'operation not permitted', 'EACCES', 'browser launch denied')
EXTERNAL = ('ENOTFOUND', 'ECONNRESET', 'ECONNREFUSED', 'DNS',
            '503 Service Unavailable', '502 Bad Gateway', 'upstream timeout')
SECURITY = ('security boundary', 'policy denied', 'permission denied by policy')


class ClassificationTests(unittest.TestCase):
    def test_zero_exit_dns_is_process_pass(self):
        self.assertEqual(recorder._classify_failure(0, False, 'PASS: DNS rejection'), ('pass', None))
    def test_zero_exit_all_external_case_names_pass(self):
        for name in EXTERNAL:
            with self.subTest(name=name):
                self.assertEqual(recorder._classify_failure(0, False, 'PASS: '+name), ('pass', None))
    def test_zero_exit_all_environment_case_names_pass(self):
        for name in ENVIRONMENT:
            with self.subTest(name=name):
                self.assertEqual(recorder._classify_failure(0, False, 'PASS: '+name), ('pass', None))
    def test_zero_exit_all_security_case_names_pass(self):
        for name in SECURITY:
            with self.subTest(name=name):
                self.assertEqual(recorder._classify_failure(0, False, 'PASS: '+name), ('pass', None))
    def test_zero_exit_empty_output_stays_pass(self):
        self.assertEqual(recorder._classify_failure(0, False, ''), ('pass', None))
    def test_zero_exit_historical_error_transcript_is_not_live_failure(self):
        output = 'Previous failure: DNS\nExpected policy denied\nRetries tested: ECONNRESET\nOK\n'
        self.assertEqual(recorder._classify_failure(0, False, output), ('pass', None))
    def test_casefold_crlf_and_unicode_do_not_change_success(self):
        self.assertEqual(recorder._classify_failure(0, False, 'PASS dNs\r\n\u0110\u00e3 ki\u1ec3m tra\r\n'), ('pass', None))
    def test_nonzero_external_is_still_blocked(self):
        for name in EXTERNAL:
            with self.subTest(name=name):
                self.assertEqual(recorder._classify_failure(1, False, name), ('blocked', 'external_dependency_failure'))
    def test_nonzero_environment_is_still_blocked(self):
        for name in ENVIRONMENT:
            with self.subTest(name=name):
                self.assertEqual(recorder._classify_failure(1, False, name), ('blocked', 'environment_blocked'))
    def test_nonzero_security_is_still_blocked(self):
        for name in SECURITY:
            with self.subTest(name=name):
                self.assertEqual(recorder._classify_failure(1, False, name), ('blocked', 'security_boundary_failure'))
    def test_nonzero_priority_is_unchanged(self):
        self.assertEqual(recorder._classify_failure(1, False, 'EACCES policy denied DNS'), ('blocked', 'environment_blocked'))
        self.assertEqual(recorder._classify_failure(1, False, 'policy denied DNS'), ('blocked', 'security_boundary_failure'))
    def test_nonzero_generic_is_still_failure_even_with_pass_text(self):
        self.assertEqual(recorder._classify_failure(1, False, 'PASS\nassertion failed'), ('fail', 'product_failure'))
    def test_negative_signal_exit_is_not_success(self):
        self.assertEqual(recorder._classify_failure(-9, False, 'PASS'), ('fail', 'product_failure'))
    def test_timeout_overrides_zero_exit(self):
        self.assertEqual(recorder._classify_failure(0, True, 'PASS DNS'), ('blocked', 'timeout'))
    def test_timeout_overrides_nonzero_error_keywords(self):
        self.assertEqual(recorder._classify_failure(124, True, 'EACCES policy denied DNS'), ('blocked', 'timeout'))


class RecorderCLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='v558-recorder-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        scripts = self.root / '.ai/scripts'
        scripts.parent.mkdir(parents=True)
        shutil.copytree(ROOT / '.ai/scripts', scripts, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        # Minimal repository control plane; never use/mutate the caller's active task.
        for p in (ROOT / '.ai').glob('*.json'):
            if p.name not in {'HARNESS_INSTALL_STATE.json', 'HARNESS_MANIFEST.json', 'SOURCE_DISTRIBUTION.json', 'REPO_MAP.json'}:
                shutil.copyfile(p, self.root / '.ai' / p.name)
        (self.root / 'README.md').write_bytes(b'Recorder protocol fixture, not a production test.\r\n')
        self.task = json.loads((ROOT / '.ai/TASK_TEMPLATE.json').read_text(encoding='utf-8'))
        self.task.update(id='TASK-RECORDER', mode='BUGFIX', status='IN_PROGRESS',
                         objective='Test recorder status protocol', user_outcome='Avoid false process failure')
        self.task['execution_contract'].update(profile='native', resolved_profile='native')
        self.task['verification']['required_checks'] = ['unit']
        self.write_task()
    def write_task(self):
        path = self.root / '.ai/tasks/TASK-RECORDER.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(self.task, indent=2)+'\n', encoding='utf-8')
    def call(self, argv, expected=0):
        result = subprocess.run([PY, *argv], cwd=self.root, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout+'\n'+result.stderr)
        return result
    def record(self, code="print('PASS DNS fixture')", expected=0, check='unit', flags=(), command=None):
        result = self.call(['.ai/scripts/record_evidence.py', '--task', 'TASK-RECORDER',
                            '--check', check, *flags, '--', *(command or [PY, '-c', code])], expected)
        event = json.loads(result.stdout)
        self.assertEqual(event['event_id'], c.evidence_event_id(event))
        return event
    def gate(self, expected=0):
        return self.call(['.ai/scripts/evidence_gate.py', '--task', 'TASK-RECORDER'], expected)
    def test_dns_success_records_passing_event_and_gate_accepts(self):
        event = self.record()
        self.assertEqual(event['status'], 'pass')
        self.assertEqual(event['command_exit_code'], 0)
        self.assertEqual(event['exit_code'], 0)
        self.assertFalse(event['workspace_mutated_by_check'])
        self.assertIsNone(event['failure_disposition'])
        self.assertIsNone(event['failure_signature'])
        self.assertEqual(event['same_failure_repeat_count'], 0)
        self.assertIn('DNS', (self.root / event['log_path']).read_text())
        self.assertEqual(event['output_digest'], hashlib.sha256((self.root / event['log_path']).read_bytes()).hexdigest())
        self.assertIn('EVIDENCE GATE: PASS', self.gate().stdout)
    def test_success_with_error_names_on_stderr(self):
        text='PASS: '+', '.join(ENVIRONMENT+EXTERNAL+SECURITY)
        event=self.record('import sys; print('+repr(text)+', file=sys.stderr)')
        self.assertEqual(event['status'], 'pass'); self.gate()
    def test_real_unittest_negative_case_names_are_not_external_outage(self):
        code='''import unittest
class NegativeCases(unittest.TestCase):
    def test_DNS_error_is_rejected(self): self.assertTrue(True)
    def test_security_boundary(self): self.assertEqual(1, 1)
unittest.main(verbosity=2)
'''
        event=self.record(code)
        self.assertEqual(event['status'], 'pass'); self.assertIn('Ran 2 tests', event['output_tail']); self.gate()
    def test_failed_dns_still_blocks_and_exits_nonzero(self):
        event=self.record("import sys; print('DNS failure'); sys.exit(2)", expected=2)
        self.assertEqual(event['status'], 'blocked'); self.assertEqual(event['failure_disposition'], 'external_dependency_failure')
        self.assertIsNotNone(event['failure_signature']); self.gate(expected=1)
    def test_failed_command_cannot_pass_from_pass_text(self):
        event=self.record("import sys; print('PASS'); sys.exit(1)", expected=1)
        self.assertEqual(event['status'], 'fail'); self.assertEqual(event['failure_disposition'], 'product_failure'); self.gate(expected=1)
    def test_unavailable_command_is_environment_blocked(self):
        event=self.record(command=[str(self.root/'does-not-exist-no-command')], expected=127)
        self.assertEqual(event['failure_disposition'], 'environment_blocked'); self.gate(expected=1)
    def test_real_timeout_after_success_text_is_not_pass(self):
        event=self.record("import time; print('PASS DNS', flush=True); time.sleep(5)", flags=['--timeout','1'], expected=124)
        self.assertEqual(event['status'], 'blocked'); self.assertEqual(event['failure_disposition'], 'timeout'); self.gate(expected=1)
    def test_zero_exit_source_mutation_still_fails(self):
        event=self.record("from pathlib import Path; Path('README.md').write_text('changed'); print('PASS DNS')", expected=3)
        self.assertEqual(event['command_exit_code'], 0); self.assertEqual(event['exit_code'], 3)
        self.assertTrue(event['workspace_mutated_by_check']); self.assertEqual(event['failure_disposition'], 'verification_mutation'); self.gate(expected=1)
    def test_zero_exit_skill_self_report_still_rejected(self):
        event=self.record("print('PASS DNS; I used the Skill')", check='skill-eval-live', expected=4)
        self.assertEqual(event['command_exit_code'], 0); self.assertEqual(event['status'], 'fail')
        self.assertEqual(event['failure_disposition'], 'invalid_skill_runtime_evidence')
    def test_ephemeral_success_does_not_satisfy_durable_evidence(self):
        event=self.record(flags=['--ephemeral'])
        self.assertEqual(event['status'], 'pass'); self.assertFalse((self.root/event['log_path']).exists())
        self.assertFalse(c.load_events(self.root/'.ai/evidence/events.jsonl')); self.gate(expected=1)
    def test_new_success_preserves_previous_failure_bytes(self):
        first=self.record("import sys; print('DNS failure'); sys.exit(2)", expected=2)
        saved=self.root/'.ai/evidence/events'/(first['event_id']+'.json'); raw=saved.read_bytes()
        event=self.record()
        self.assertEqual(event['status'], 'pass'); self.assertEqual(saved.read_bytes(), raw)
        self.assertEqual(len(c.load_events(self.root/'.ai/evidence/events.jsonl')), 2); self.gate()
    def test_changed_task_still_invalidates_successful_evidence(self):
        self.record(); self.task['objective']='Different objective'; self.write_task(); self.gate(expected=1)
    def test_changed_source_still_invalidates_successful_evidence(self):
        self.record(); (self.root/'README.md').write_bytes(b'Changed source\n'); self.gate(expected=1)
    def test_missing_other_required_check_is_not_satisfied_by_exit_zero(self):
        self.task['verification']['required_checks'].append('integration'); self.write_task()
        self.record(); result=self.gate(expected=1); self.assertIn('integration', result.stdout)


class IdentityTests(unittest.TestCase):
    def test_current_release_and_exact_parent(self):
        current=c.harness_version(ROOT)
        self.assertIn(current, {'5.5.8','5.5.9','5.5.10'})
        # When a later release runs the historical v5.5.8 regression, verify the
        # immutable v5.5.8 lineage snapshot rather than pretending the current
        # release still has the v5.5.7 implementation parent.
        lineage_path=ROOT/'.ai/RELEASE_LINEAGE.json' if current=='5.5.8' else ROOT/'.ai/lineage/v5.5.8.json'
        doc=json.loads(lineage_path.read_text(encoding='utf-8'))
        self.assertEqual(doc['distribution_version'], '5.5.8'); self.assertEqual(doc['implementation_parent'], '5.5.7')
        self.assertEqual(next(x for x in doc['input_artifacts'] if x['role']=='implementation-parent')['sha256'], '95c20f53c42615fa33886d2f469a48b2c21145d18cc6eca7cb2c6381023326e0')
        prior=doc['prior_lineage']; self.assertEqual(hashlib.sha256((ROOT/prior['path']).read_bytes()).hexdigest(), prior['sha256'])
    def test_all_13_canonical_skills_remain_unchanged(self):
        expected=json.loads((ROOT/'.ai/CANONICAL_SKILL_HASHES.json').read_text(encoding='utf-8'))['sha256']
        self.assertEqual(len(expected),13)
        for name, sha in expected.items():
            self.assertEqual(hashlib.sha256((ROOT/'.agents/skills'/name/'SKILL.md').read_bytes()).hexdigest(), sha)


if __name__ == '__main__':
    unittest.main(verbosity=2)
