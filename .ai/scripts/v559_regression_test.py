#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; PY=sys.executable
sys.path.insert(0,str(ROOT/'.ai/scripts'))
import _common as c
import provider_policy_lint as ppl

def run(args,cwd,expected=0):
    p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
    if p.returncode!=expected: raise AssertionError(f"expected {expected}, got {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p

class PolicyTests(unittest.TestCase):
    def test_v2_source_policy_allows_authorized_capacity_failover(self):
        current=c.harness_version(ROOT); policy_path=ROOT/'.ai/AI_PROVIDER_POLICY.json' if current=='5.5.9' else ROOT/'.ai/lineage/v5.5.9-provider-policy.json'
        p=json.loads(policy_path.read_text(encoding='utf-8'))
        self.assertEqual(p['version'],2); self.assertEqual(ppl.errors_for(p),[])
        af=p['routing']['authorized_capacity_failover']
        self.assertTrue(af['free_to_free']); self.assertTrue(af['free_to_paid_requires_budget_authorization']); self.assertTrue(af['same_scope_credentials_are_not_new_capacity'])
        self.assertNotIn('never_use_rotation_to_evade_provider_quotas_or_terms',p['safety'])
    def test_legacy_v1_remains_compatible(self):
        current=c.harness_version(ROOT); policy_path=ROOT/'.ai/AI_PROVIDER_POLICY.json' if current=='5.5.9' else ROOT/'.ai/lineage/v5.5.9-provider-policy.json'
        p=json.loads(policy_path.read_text(encoding='utf-8'))
        p['version']=1; p['safety']['never_use_rotation_to_evade_provider_quotas_or_terms']=True
        self.assertEqual(ppl.errors_for(p),[])
    def test_v2_rejects_unapproved_paid_or_same_scope_claim(self):
        current=c.harness_version(ROOT); policy_path=ROOT/'.ai/AI_PROVIDER_POLICY.json' if current=='5.5.9' else ROOT/'.ai/lineage/v5.5.9-provider-policy.json'
        p=json.loads(policy_path.read_text(encoding='utf-8'))
        p['routing']['authorized_capacity_failover']['free_to_paid_requires_budget_authorization']=False
        p['routing']['authorized_capacity_failover']['same_scope_credentials_are_not_new_capacity']=False
        errs=ppl.errors_for(p); self.assertTrue(any('free_to_paid' in x for x in errs)); self.assertTrue(any('same_scope' in x for x in errs))

class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(prefix='v559-'); self.addCleanup(self.td.cleanup)
        self.root=Path(self.td.name)/'repo'; shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git'))
        subprocess.run(['git','init','-q'],cwd=self.root,check=True); subprocess.run(['git','config','user.email','fixture@example.invalid'],cwd=self.root,check=True); subprocess.run(['git','config','user.name','Fixture'],cwd=self.root,check=True)
        subprocess.run(['git','add','.'],cwd=self.root,check=True); subprocess.run(['git','commit','-qm','fixture'],cwd=self.root,check=True)
        task=json.loads((self.root/'.ai/TASK_TEMPLATE.json').read_text(encoding='utf-8'))
        task.update(id='TASK-REL',mode='RELEASE',status='IN_PROGRESS',objective='release doctor fixture',user_outcome='truthful release identity')
        task['traits']['production_release']=True; task['release']['production_url']='https://example.invalid'; task['verification']['required_checks']=['unit']
        path=self.root/'.ai/tasks/TASK-REL.json'; path.parent.mkdir(exist_ok=True); path.write_text(json.dumps(task,indent=2)+'\n',encoding='utf-8')
        subprocess.run(['git','add','.ai/tasks/TASK-REL.json'],cwd=self.root,check=True); subprocess.run(['git','commit','-qm','task'],cwd=self.root,check=True)
    def call(self,*args,expected=0): return run([PY,*args],self.root,expected)
    def test_validate_task_warns_marker_early(self):
        p=self.call('.ai/scripts/validate_task.py','--task','TASK-REL'); self.assertIn('RELEASE_MARKER_MISSING',p.stdout)
    def test_release_doctor_is_read_only_and_labels_external_unknown(self):
        before=run(['git','status','--porcelain=v1'],self.root).stdout
        p=self.call('.ai/scripts/release_doctor.py','--task','TASK-REL','--json'); doc=json.loads(p.stdout)
        after=run(['git','status','--porcelain=v1'],self.root).stdout
        self.assertEqual(before,after); self.assertEqual(doc['identity']['alias_revision'],'UNKNOWN-provider-not-queried'); self.assertEqual(doc['identity']['ci_revision'],'UNKNOWN-provider-not-queried')
        self.assertIn('revision_marker_missing',doc['blockers']); self.assertIn('No git fetch',doc['limits'][0])
    def test_release_doctor_rejects_short_target_revision(self):
        p=self.call('.ai/scripts/release_doctor.py','--task','TASK-REL','--target-sha','abc123',expected=1); self.assertIn('full 40/64',p.stderr+p.stdout)
    def test_workflow_commit_detection_is_inferred_only(self):
        wf=self.root/'.github/workflows'; wf.mkdir(parents=True); (wf/'release.yml').write_text('steps:\n  - run: npm version patch && git commit -am release\n',encoding='utf-8')
        p=self.call('.ai/scripts/release_doctor.py','--task','TASK-REL','--json'); doc=json.loads(p.stdout)
        self.assertTrue(doc['workflow_commit_hints']); self.assertTrue(all(x['authority']=='inferred-static-hint' and x['proves_new_commit'] is False for x in doc['workflow_commit_hints']))
    def test_record_evidence_summary_preserves_json_default_and_event(self):
        p=self.call('.ai/scripts/record_evidence.py','--task','TASK-REL','--check','unit','--',PY,'-c',"print('PASS DNS')")
        event=json.loads(p.stdout); self.assertEqual(event['status'],'pass')
        p2=self.call('.ai/scripts/record_evidence.py','--task','TASK-REL','--check','unit','--summary','--',PY,'-c',"print('PASS DNS')")
        self.assertRegex(p2.stdout.strip(),r'^PASS · unit · [0-9a-f]{40} · [0-9.]+s · \.ai/evidence/logs/.+\.log$')
        events=c.load_events(self.root/'.ai/evidence/events.jsonl'); self.assertEqual(len(events),2); self.assertEqual(events[-1]['status'],'pass')

class IdentityTests(unittest.TestCase):
    def test_version_lineage_and_skills(self):
        self.assertIn(c.harness_version(ROOT),{'5.5.9','5.5.10'})
        current=c.harness_version(ROOT); lineage_path=ROOT/'.ai/RELEASE_LINEAGE.json' if current=='5.5.9' else ROOT/'.ai/lineage/v5.5.9.json'
        lin=json.loads(lineage_path.read_text(encoding='utf-8')); self.assertEqual(lin['implementation_parent'],'5.5.8')
        parent=next(x for x in lin['input_artifacts'] if x['role']=='implementation-parent'); self.assertEqual(parent['sha256'],'a7fecb1ec659faf427b60c68f9541cf51424d77f9745dcbf34ec878b69199172')
        expected=json.loads((ROOT/'.ai/CANONICAL_SKILL_HASHES.json').read_text(encoding='utf-8'))['sha256']; self.assertEqual(len(expected),13)
        for name,sha in expected.items(): self.assertEqual(hashlib.sha256((ROOT/'.agents/skills'/name/'SKILL.md').read_bytes()).hexdigest(),sha)

if __name__=='__main__': unittest.main(verbosity=2)
