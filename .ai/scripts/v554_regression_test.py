#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
SCRIPTS=ROOT/'.ai/scripts'
sys.path.insert(0,str(SCRIPTS))
import quarantine_scan as qs
import skill_security_gate as ssg

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class ScannerUnitTests(unittest.TestCase):
    def scan(self,text,name='x.py'):
        f=[]; qs.scan_text(name,text,f); return f
    def rules(self,findings): return [(x['rule'],x['severity']) for x in findings]
    def test_direct_exec_blocks(self):
        self.assertIn(('python-dynamic-exec','block'),self.rules(self.scan("exec('x')\n")))
    def test_reflective_builtins_exec_constant_join_blocks(self):
        text="import builtins\n_runner=getattr(builtins, ''.join(['e','x','e','c']))\n_runner('x')\n"
        self.assertIn(('python-reflective-exec','block'),self.rules(self.scan(text)))
    def test_reflective_eval_alias_blocks(self):
        text="import builtins as b\nf=getattr(b, 'ev'+'al')\nf('1+1')\n"
        self.assertIn(('python-reflective-exec','block'),self.rules(self.scan(text)))
    def test_importfrom_alias_runtime_sink_is_review(self):
        text="from subprocess import run as go\ngo(['echo','ok'])\n"
        self.assertIn(('python-runtime-exec','review'),self.rules(self.scan(text)))
    def test_unimported_os_name_is_not_treated_as_module(self):
        self.assertNotIn(('python-runtime-exec','review'),self.rules(self.scan("os.system('x')\n")))
    def test_python_parse_failure_is_partial_signal(self):
        self.assertIn(('python-ast-incomplete','review'),self.rules(self.scan('def broken(:\n')))
    def test_opaque_extension_blocks(self):
        f=[]; qs.scan_opaque_executable('__pycache__/payload.cpython-313.pyc',b'not-real-pyc',f)
        self.assertEqual(f[0]['rule'],'opaque-executable-artifact'); self.assertEqual(f[0]['severity'],'block')
    def test_renamed_native_magic_blocks(self):
        f=[]; qs.scan_opaque_executable('asset.dat',b'\x7fELFxxxx',f)
        self.assertEqual(f[0]['rule'],'opaque-executable-artifact')

class SkillGateIntegrationTests(unittest.TestCase):
    def run_gate(self,files:dict[str,bytes],baseline:Path|None=None):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); (p/'SKILL.md').write_text('---\nname: demo\ndescription: bounded demo\n---\n',encoding='utf-8')
            for rel,data in files.items():
                q=p/rel; q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(data)
            cmd=[sys.executable,str(SCRIPTS/'skill_security_gate.py'),'--target',str(p),'--fail-on','never']
            if baseline is not None: cmd += ['--baseline',str(baseline)]
            cp=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(cp.returncode,0,cp.stderr); return json.loads(cp.stdout)
    def test_pyc_makes_analysis_partial_and_block(self):
        r=self.run_gate({'__pycache__/payload.cpython-313.pyc':b'bytes'})
        self.assertEqual(r['analysis_status'],'partial'); self.assertEqual(r['status'],'block')
        self.assertTrue(any(x['rule']=='opaque-executable-artifact' for x in r['findings']))
    def test_reflective_exec_is_blocking_but_analysis_complete(self):
        src=b"import builtins\nf=getattr(builtins, ''.join(['e','x','e','c']))\nf('print(1)')\n"
        r=self.run_gate({'runner.py':src})
        self.assertEqual(r['analysis_status'],'complete'); self.assertEqual(r['status'],'block')
        self.assertTrue(any(x['rule']=='python-reflective-exec' for x in r['findings']))
    def test_baseline_cannot_launder_opaque_incompleteness(self):
        files={'payload.pyc':b'opaque'}
        first=self.run_gate(files)
        fp=next(x['fingerprint'] for x in first['findings'] if x['rule']=='opaque-executable-artifact')
        with tempfile.TemporaryDirectory() as td:
            baseline=Path(td)/'baseline.json'; baseline.write_text(json.dumps({'accepted_fingerprints':[fp]}),encoding='utf-8')
            second=self.run_gate(files,baseline)
        self.assertEqual(second['baseline_accepted_count'],1)
        self.assertEqual(second['analysis_status'],'partial'); self.assertEqual(second['status'],'block')
    def test_clean_text_skill_remains_complete(self):
        r=self.run_gate({'helper.py':b'def add(a,b): return a+b\n'})
        self.assertEqual(r['analysis_status'],'complete'); self.assertEqual(r['status'],'pass')

class PreservationTests(unittest.TestCase):
    def test_security_policy_requires_new_truth_controls(self):
        p=load(ROOT/'.ai/SKILL_SECURITY_POLICY.json')['principles']
        self.assertTrue(p['opaque_executable_content_makes_static_analysis_partial'])
        self.assertTrue(p['python_ast_sink_resolution_required_for_python_sources'])
        self.assertTrue(p['statically_resolved_reflective_exec_is_blocking'])
    def test_v53_quality_controls_remain(self):
        q=load(ROOT/'.ai/QUALITY.json')
        self.assertIn('skill-eval-live',q['trait_required_checks']['skill_modification'])
        self.assertEqual(q['profile_required_checks']['native'],[])
        self.assertIn('verified-progress',q['profile_required_checks']['portable'])
        self.assertIn('verified-progress',q['profile_required_checks']['audited'])
    def test_canonical_skills_unchanged(self):
        expected=load(ROOT/'.ai/CANONICAL_SKILL_HASHES.json')['sha256']; self.assertEqual(len(expected),13)
        for name,digest in expected.items(): self.assertEqual(sha(ROOT/'.agents/skills'/name/'SKILL.md'),digest)
    def test_runtime_state_exclusion_contract_unchanged(self):
        raw=json.dumps(load(ROOT/'.ai/FINGERPRINT_POLICY.json'))
        self.assertIn('.ai/checkpoints',raw); self.assertIn('.ai/REPO_MAP.json',raw)

if __name__=='__main__': unittest.main(verbosity=2)
