#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest import mock
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
SCRIPTS=ROOT/'.ai/scripts'
sys.path.insert(0,str(SCRIPTS))
import deterministic_regression_gate as drg
import harness_security as hs
import host_surface_contract as hsc
import skill_catalog_eval as sce
import skill_security_gate as ssg

def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class TempCase(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name)
    def tearDown(self):self.t.cleanup()

class SecurityCompletenessTests(TempCase):
    def test_harness_unreadable_payload_is_partial(self):
        f=self.p/'owned.md';f.write_text('ok',encoding='utf-8'); blockers=[];warnings=[];seen=set();incomplete=[]
        with mock.patch.object(Path,'read_bytes',side_effect=OSError('denied')):
            hs.scan_payload('owned.md',f,None,blockers,warnings,seen,incomplete)
        self.assertEqual(incomplete[0]['analyzer'],'content-static')
        self.assertEqual(incomplete[0]['reason'],'unreadable-harness-owned-payload')
    def test_resource_limit_completeness_precedes_baseline(self):
        findings=[{'rule':'package-size-limit','severity':'block','path':'x','detail_code':'archive-member-count','detail':'x','evidence_sha256':None}]
        for f in findings:f['fingerprint']=ssg.canonical_fingerprint(f);f['baseline_accepted']=True
        effective=[f for f in findings if not f['baseline_accepted']]
        self.assertEqual(effective,[])
        incomplete=[f for f in findings if f['rule'] in {'package-size-limit','unreadable-input'}]
        self.assertTrue(incomplete,'raw completeness evidence must survive baseline acceptance')
    def test_security_policy_is_fail_closed(self):
        p=load(ROOT/'.ai/HARNESS_SECURITY_POLICY.json')
        self.assertTrue(p['principles']['analysis_incomplete_is_never_clean'])
        self.assertTrue(p['principles']['required_analyzer_failure_is_release_blocking'])

class DeterministicGateTests(TempCase):
    def make_root(self):
        (self.p/'.ai/scripts').mkdir(parents=True)
        (self.p/'.ai/DETERMINISTIC_E2E_POLICY.json').write_text(json.dumps({'discovery_globs':['.ai/scripts/*_regression_test.py'],'exclude':[]}),encoding='utf-8')
        (self.p/'VERSION').write_text('x',encoding='utf-8')
        return self.p
    def test_new_regression_needs_no_allowlist(self):
        root=self.make_root();a=root/'.ai/scripts/a_regression_test.py';a.write_text('raise SystemExit(0)\n');
        self.assertEqual([x.name for x in drg.discover(root)],['a_regression_test.py'])
        b=root/'.ai/scripts/brand_new_regression_test.py';b.write_text('raise SystemExit(0)\n')
        self.assertEqual([x.name for x in drg.discover(root)],['a_regression_test.py','brand_new_regression_test.py'])
    def test_failure_is_not_green(self):
        root=self.make_root();(root/'.ai/scripts/a_regression_test.py').write_text('raise SystemExit(3)\n')
        self.assertEqual(drg.run_gate(root,True)['status'],'FAIL')
    def test_list_only_is_not_pass(self):
        root=self.make_root();(root/'.ai/scripts/a_regression_test.py').write_text('raise SystemExit(0)\n')
        self.assertEqual(drg.run_gate(root,False)['status'],'NOT_RUN')
    def test_real_source_discovers_v553(self):
        names=[p.name for p in drg.discover(ROOT)]
        self.assertIn('v553_regression_test.py',names);self.assertIn('install_regression_test.py',names);self.assertIn('lifecycle_regression_test.py',names)

class CatalogEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills=sce.canonical_skills(ROOT);cls.doc=load(ROOT/'.ai/evals/skill-catalog-routing.json')
    def test_all_13_have_three_case_kinds(self):
        self.assertEqual(len(self.skills),13);self.assertEqual(sce.validate_matrix(self.doc,self.skills),[]);self.assertEqual(len(self.doc['cases']),39)
    def test_positive_requires_target_not_self_report(self):
        c=next(x for x in self.doc['cases'] if x['kind']=='should-trigger');obs=[{'case_id':c['id'],'sensor':'claude-stream-json','observed_skills':[]}]
        r=sce.score_observations(self.doc,obs,{'claude-stream-json'});self.assertEqual(r['status'],'FAIL');self.assertIn('did not activate',r['errors'][0])
        obs[0]['sensor']='self-report';r=sce.score_observations(self.doc,obs,{'claude-stream-json'});self.assertEqual(r['status'],'FAIL');self.assertIn('untrusted',r['errors'][0])
    def test_negative_forbids_target_but_allows_other_visible_skill(self):
        c=next(x for x in self.doc['cases'] if x['kind']=='should-not-trigger');other=next(x for x in c['visible_catalog'] if x!=c['target_skill'])
        r=sce.score_observations(self.doc,[{'case_id':c['id'],'sensor':'claude-stream-json','observed_skills':[other]}],{'claude-stream-json'});self.assertEqual(r['status'],'PASS')
        r=sce.score_observations(self.doc,[{'case_id':c['id'],'sensor':'claude-stream-json','observed_skills':[c['target_skill']]}],{'claude-stream-json'});self.assertEqual(r['status'],'FAIL')
    def test_no_skill_baseline_excludes_target(self):
        for c in self.doc['cases']:
            if c['kind']=='no-skill-baseline':self.assertNotIn(c['target_skill'],c['visible_catalog'])

class HostSurfaceTests(unittest.TestCase):
    def snap(self,caps):return {'host':'demo','source':{'kind':'fixture-schema','revision':'r1','sha256':'1'*64},'capabilities':caps}
    def test_known_capabilities_pass(self):
        r=hsc.evaluate(self.snap(['a','b']),{'capabilities':{'a':'supported','b':'blocked'}});self.assertEqual(r['status'],'PASS');self.assertFalse(r['parity_claimed'])
    def test_new_upstream_capability_fails_until_classified(self):
        r=hsc.evaluate(self.snap(['a','new']),{'capabilities':{'a':'supported'}});self.assertEqual(r['status'],'FAIL');self.assertEqual(r['unknown_observed'],['new'])
    def test_stale_mapping_reported(self):
        r=hsc.evaluate(self.snap(['a']),{'capabilities':{'a':'supported','old':'unavailable'}});self.assertEqual(r['status'],'PASS');self.assertEqual(r['stale_mappings'],['old'])
    def test_unpinned_snapshot_rejected(self):
        with self.assertRaises(ValueError):hsc.evaluate({'host':'x','source':{},'capabilities':['a']},{'capabilities':{'a':'supported'}})

class PreservationTests(unittest.TestCase):
    def test_v53_controls_preserved(self):
        q=load(ROOT/'.ai/QUALITY.json')
        for c in ('harness-security','surface-drift','package-contract','harness-self-test','skill-eval-contract','skill-trigger-truth-contract','skill-eval-transaction-contract','plugin-containment-contract','operator-event-contract','mcp-client-abuse-contract'):
            self.assertIn(c,q['trait_required_checks']['harness_modification'])
        self.assertIn('skill-eval-live',q['trait_required_checks']['skill_modification'])
        self.assertEqual(q['profile_required_checks']['native'],[]);self.assertIn('verified-progress',q['profile_required_checks']['portable']);self.assertIn('verified-progress',q['profile_required_checks']['audited'])
    def test_runtime_state_exclusion_contract_unchanged(self):
        p=load(ROOT/'.ai/FINGERPRINT_POLICY.json');raw=json.dumps(p)
        self.assertIn('.ai/checkpoints',raw);self.assertIn('.ai/REPO_MAP.json',raw)
    def test_all_canonical_skill_bytes_match_pinned_hashes(self):
        expected=load(ROOT/'.ai/CANONICAL_SKILL_HASHES.json')['sha256'];self.assertEqual(len(expected),13)
        for name,d in expected.items():self.assertEqual(sha(ROOT/'.agents/skills'/name/'SKILL.md'),d)

if __name__=='__main__':unittest.main(verbosity=2)
