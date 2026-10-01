#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys, unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.ai/scripts'))
import _common as c
import provider_policy_lint as ppl
import provider_route_budget as prb

class PolicyV3Tests(unittest.TestCase):
    def source(self):
        return json.loads((ROOT/'.ai/AI_PROVIDER_POLICY.json').read_text(encoding='utf-8'))
    def test_v3_source_policy_requires_actual_target_budget_gate(self):
        p=self.source(); self.assertEqual(p['version'],3); self.assertEqual(ppl.errors_for(p),[])
        g=p['routing']['billing_target_budget_gate']
        self.assertTrue(g['evaluate_actual_billing_target_before_execution'])
        self.assertTrue(g['zero_cost_primary_never_exempts_paid_target'])
        self.assertTrue(g['reserve_only_after_target_selected'])
        self.assertTrue(g['reservation_must_be_atomic'])
    def test_v2_remains_compatible(self):
        p=self.source(); p['version']=2
        p['routing'].pop('billing_target_budget_gate',None); p['routing'].pop('fallback_graph_validation',None)
        p['routing']['circuit_breaker'].pop('half_open_probe',None); p['routing']['circuit_breaker'].pop('failure_accounted_to_actual_target_scope',None)
        self.assertEqual(ppl.errors_for(p),[])
    def test_v3_rejects_zero_cost_paid_fallback_bypass(self):
        p=self.source(); p['routing']['billing_target_budget_gate']['zero_cost_primary_never_exempts_paid_target']=False
        self.assertTrue(any('zero_cost_primary' in x for x in ppl.errors_for(p)))
    def test_v3_rejects_non_atomic_or_preselection_reservation(self):
        p=self.source(); p['routing']['billing_target_budget_gate']['reserve_only_after_target_selected']=False; p['routing']['billing_target_budget_gate']['reservation_must_be_atomic']=False
        errs=ppl.errors_for(p); self.assertTrue(any('reserve_only_after' in x for x in errs)); self.assertTrue(any('reservation_must_be_atomic' in x for x in errs))
    def test_v3_requires_fallback_graph_preflight(self):
        p=self.source(); p['routing']['fallback_graph_validation']['validate_before_runtime']=False
        self.assertTrue(any('fallback_graph_validation.validate_before_runtime' in x for x in ppl.errors_for(p)))

class ReferenceDecisionTests(unittest.TestCase):
    def test_over_budget_free_primary_can_still_use_free_target(self):
        r=prb.evaluate({'paid_budget_authorized':False,'target':{'id':'free-b','cost_class':'free'}})
        self.assertEqual((r['status'],r['reason']),('allow','free-target'))
    def test_over_budget_free_primary_cannot_spill_to_paid_target(self):
        r=prb.evaluate({'paid_budget_authorized':True,'target':{'id':'paid-b','cost_class':'paid','max_request_cost':0.25},'budget_scopes':[{'id':'user','limit':1.0,'spend':1.0,'reserved':0.0}]})
        self.assertEqual((r['status'],r['reason']),('skip-target','budget-exceeded'))
    def test_under_budget_paid_target_requires_atomic_reservation(self):
        r=prb.evaluate({'paid_budget_authorized':True,'target':{'id':'paid-b','cost_class':'paid','max_request_cost':0.25},'budget_scopes':[{'id':'user','limit':2.0,'spend':1.0,'reserved':0.25},{'id':'project','limit':5.0,'spend':2.0,'reserved':0.0}]})
        self.assertEqual(r['status'],'allow'); self.assertTrue(r['requires_atomic_reservation']); self.assertEqual(r['reserve_amount'],0.25)
    def test_unknown_paid_target_cost_or_scope_fails_closed(self):
        a=prb.evaluate({'paid_budget_authorized':True,'target':{'id':'paid','cost_class':'paid'},'budget_scopes':[{'id':'user','limit':2,'spend':0}]})
        b=prb.evaluate({'paid_budget_authorized':True,'target':{'id':'paid','cost_class':'paid','max_request_cost':0.2}})
        self.assertEqual(a['status'],'block'); self.assertEqual(b['status'],'block')

class IdentityTests(unittest.TestCase):
    def test_version_lineage_and_skills(self):
        self.assertEqual(c.harness_version(ROOT),'5.5.10')
        lin=json.loads((ROOT/'.ai/RELEASE_LINEAGE.json').read_text(encoding='utf-8')); self.assertEqual(lin['implementation_parent'],'5.5.9')
        parent=next(x for x in lin['input_artifacts'] if x['role']=='implementation-parent'); self.assertEqual(parent['sha256'],'9d8e99b8f2767b0db218ff0d987645dc840fbc6318acec9323877e965d379e95')
        snap=ROOT/'.ai/lineage/v5.5.9.json'; self.assertEqual(hashlib.sha256(snap.read_bytes()).hexdigest(),lin['prior_lineage']['sha256'])
        expected=json.loads((ROOT/'.ai/CANONICAL_SKILL_HASHES.json').read_text(encoding='utf-8'))['sha256']; self.assertEqual(len(expected),13)
        for name,sha in expected.items(): self.assertEqual(hashlib.sha256((ROOT/'.agents/skills'/name/'SKILL.md').read_bytes()).hexdigest(),sha)

if __name__=='__main__': unittest.main(verbosity=2)
