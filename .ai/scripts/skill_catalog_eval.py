#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def canonical_skills(root:Path)->list[str]:
    return sorted(p.parent.name for p in (root/'.agents/skills').glob('*/SKILL.md'))
def validate_matrix(doc:dict,skills:list[str])->list[str]:
    errors=[];cases=doc.get('cases',[])
    if not isinstance(cases,list):return ['cases must be a list']
    seen={(c.get('target_skill'),c.get('kind')) for c in cases if isinstance(c,dict)}
    allset=set(skills)
    for skill in skills:
        for kind in ('should-trigger','should-not-trigger','no-skill-baseline'):
            if (skill,kind) not in seen:errors.append(f'missing {kind} catalog case for {skill}')
    for i,c in enumerate(cases):
        if not isinstance(c,dict):errors.append(f'case {i} is not an object');continue
        target=c.get('target_skill');vis=c.get('visible_catalog');kind=c.get('kind');expected=c.get('expected_skills')
        if target not in allset:errors.append(f'case {i} unknown target {target!r}')
        if not isinstance(vis,list) or not set(vis).issubset(allset):errors.append(f'case {i} invalid visible_catalog')
        if kind in {'should-trigger','should-not-trigger'} and set(vis)!=allset:errors.append(f'case {i} catalog case must expose full canonical catalog')
        if kind=='no-skill-baseline' and target in set(vis or []):errors.append(f'case {i} no-skill baseline must exclude target')
        if kind not in {'should-trigger','should-not-trigger','no-skill-baseline'}:errors.append(f'case {i} invalid kind {kind!r}')
        if not isinstance(expected,list) or not set(expected).issubset(set(vis or [])):errors.append(f'case {i} expected skill is not visible')
    return errors
def score_observations(doc:dict,observations:list[dict],accepted:set[str])->dict:
    cases={str(c['id']):c for c in doc.get('cases',[])};errors=[];rows=[]
    for o in observations:
        cid=str(o.get('case_id'));c=cases.get(cid)
        if not c:errors.append(f'unknown case_id {cid}');continue
        sensor=o.get('sensor');observed=o.get('observed_skills')
        if sensor not in accepted:errors.append(f'{cid}: untrusted activation sensor {sensor!r}');continue
        if not isinstance(observed,list):errors.append(f'{cid}: observed_skills must be list');continue
        visible=set(c['visible_catalog']); invisible=sorted(set(observed)-visible); target=c['target_skill']; kind=c['kind']
        if invisible:errors.append(f'{cid}: activation attributed to non-visible skill: {invisible}')
        if kind=='should-trigger' and target not in observed:errors.append(f'{cid}: target skill did not activate: {target}')
        if kind in {'should-not-trigger','no-skill-baseline'} and target in observed:errors.append(f'{cid}: forbidden target skill activated: {target}')
        rows.append({'case_id':cid,'observed_skills':observed,'target_skill':target,'kind':kind,'invisible':invisible})
    return {'schema_version':1,'status':'PASS' if not errors else 'FAIL','errors':errors,'cases_scored':rows,'live_activation_proof':bool(rows) and not errors}
def main():
    ap=argparse.ArgumentParser(description='Validate or score full-catalog Skill routing without treating self-report or fixture inference as activation proof.')
    sub=ap.add_subparsers(dest='cmd',required=True);v=sub.add_parser('validate');v.add_argument('--matrix',default=str(ROOT/'.ai/evals/skill-catalog-routing.json'))
    s=sub.add_parser('score');s.add_argument('--matrix',default=str(ROOT/'.ai/evals/skill-catalog-routing.json'));s.add_argument('--observations',required=True);s.add_argument('--out')
    a=ap.parse_args();skills=canonical_skills(ROOT);doc=json.loads(Path(a.matrix).read_text(encoding='utf-8'));errs=validate_matrix(doc,skills)
    if a.cmd=='validate':
        report={'schema_version':1,'status':'PASS' if not errs else 'FAIL','canonical_skills':skills,'case_count':len(doc.get('cases',[])),'errors':errs,'live_activation':'NOT_RUN','matrix_validation_is_live_proof':False}
    else:
        if errs:report={'schema_version':1,'status':'FAIL','errors':errs,'live_activation_proof':False}
        else:
            policy=json.loads((ROOT/'.ai/SKILL_CATALOG_EVAL_POLICY.json').read_text(encoding='utf-8'));obs=json.loads(Path(a.observations).read_text(encoding='utf-8'));report=score_observations(doc,obs.get('observations',[]),set(policy['accepted_activation_sensors']))
    text=json.dumps(report,indent=2,ensure_ascii=False)+'\n';print(text,end='')
    if getattr(a,'out',None):Path(a.out).write_text(text,encoding='utf-8')
    if report['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
