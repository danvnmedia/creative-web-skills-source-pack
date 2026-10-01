#!/usr/bin/env python3
"""Pure reference evaluator for actual-target AI routing budget decisions.

This does not call providers or reserve money. It models the fail-closed decision an
application router should make immediately before executing a resolved target.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.dont_write_bytecode=True

def evaluate(case:dict)->dict:
    target=case.get('target') or {}
    cost_class=target.get('cost_class')
    target_id=target.get('id') or 'unknown-target'
    if cost_class=='free':
        return {'status':'allow','reason':'free-target','target_id':target_id,'requires_atomic_reservation':False}
    if cost_class!='paid':
        return {'status':'block','reason':'unknown-target-cost-class','target_id':target_id,'requires_atomic_reservation':False}
    if case.get('paid_budget_authorized') is not True:
        return {'status':'block','reason':'paid-budget-not-authorized','target_id':target_id,'requires_atomic_reservation':False}
    max_cost=target.get('max_request_cost')
    if not isinstance(max_cost,(int,float)) or isinstance(max_cost,bool) or max_cost < 0:
        return {'status':'block','reason':'paid-target-cost-unknown','target_id':target_id,'requires_atomic_reservation':False}
    scopes=case.get('budget_scopes')
    if not isinstance(scopes,list) or not scopes:
        return {'status':'block','reason':'paid-target-budget-scope-unknown','target_id':target_id,'requires_atomic_reservation':False}
    checked=[]
    for scope in scopes:
        if not isinstance(scope,dict) or scope.get('enabled',True) is not True:
            continue
        name=str(scope.get('id') or 'unknown-scope')
        limit=scope.get('limit'); spend=scope.get('spend'); reserved=scope.get('reserved',0)
        vals=(limit,spend,reserved)
        if any(not isinstance(v,(int,float)) or isinstance(v,bool) or v < 0 for v in vals):
            return {'status':'block','reason':'budget-scope-state-unknown','target_id':target_id,'scope':name,'requires_atomic_reservation':False}
        projected=spend+reserved+max_cost
        checked.append({'id':name,'limit':limit,'projected':projected})
        if projected > limit:
            return {'status':'skip-target','reason':'budget-exceeded','target_id':target_id,'scope':name,'checked_scopes':checked,'requires_atomic_reservation':False}
    if not checked:
        return {'status':'block','reason':'no-enabled-budget-scope','target_id':target_id,'requires_atomic_reservation':False}
    return {'status':'allow','reason':'paid-target-within-budget','target_id':target_id,'checked_scopes':checked,'reserve_amount':max_cost,'requires_atomic_reservation':True}

def main():
    ap=argparse.ArgumentParser(description='Evaluate an actual-target provider budget fixture; no provider or billing side effects.')
    ap.add_argument('--input',required=True,help='JSON fixture path')
    a=ap.parse_args(); case=json.loads(Path(a.input).read_text(encoding='utf-8')); result=evaluate(case)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    raise SystemExit(0 if result['status']=='allow' else 1)
if __name__=='__main__': main()
