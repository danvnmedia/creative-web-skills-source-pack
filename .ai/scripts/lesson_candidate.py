#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode = True

from _common import redact, root_from_script

ROOT=root_from_script()
POLICY_PATH=ROOT/'.ai/LEARNING_POLICY.json'


def load_policy():
    return json.loads(POLICY_PATH.read_text(encoding='utf-8'))


def project_id() -> tuple[str,str]:
    for cmd,label in [(['git','remote','get-url','origin'],'git-remote'),(['git','rev-parse','--show-toplevel'],'git-root')]:
        p=subprocess.run(cmd,cwd=str(ROOT),text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        if p.returncode==0 and p.stdout.strip():
            value=p.stdout.strip()
            return hashlib.sha256(value.encode('utf-8')).hexdigest()[:12], label
    value=str(ROOT.resolve())
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:12], 'path'


def candidate_path(policy: dict, cid: str) -> Path:
    return ROOT/policy['paths']['candidates']/f'{cid}.json'


def curated_path(policy: dict, cid: str) -> Path:
    return ROOT/policy['paths']['curated']/f'{cid}.json'


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def summarize(doc: dict, policy: dict) -> dict:
    obs=doc.get('observations',[])
    avg=(sum(float(o.get('confidence',0)) for o in obs)/len(obs)) if obs else 0.0
    projects=sorted({o.get('project_id') for o in obs if o.get('project_id')})
    result={'observations':len(obs),'average_confidence':round(avg,3),'distinct_projects':len(projects),'project_ids':projects}
    eligibility={}
    for scope in ('project','global'):
        rule=policy['promotion'][scope]
        ok=len(obs)>=rule.get('min_observations',0) and avg>=rule.get('min_average_confidence',0)
        if scope=='global': ok=ok and len(projects)>=rule.get('min_distinct_projects',0)
        eligibility[scope]=ok
    result['eligible']=eligibility
    return result


def cmd_capture(args, policy):
    if not 0 <= args.confidence <= 1: raise SystemExit('confidence must be between 0 and 1')
    path=candidate_path(policy,args.id)
    if path.exists(): doc=read_json(path)
    else:
        doc={'schema_version':1,'id':args.id,'trigger':redact(args.trigger),'action':redact(args.action),'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'observations':[],'status':'candidate'}
    if doc.get('trigger') != redact(args.trigger) or doc.get('action') != redact(args.action):
        raise SystemExit('candidate id already exists with different trigger/action')
    pid,source=project_id()
    pid=args.project_id or pid
    evidence=[redact(x) for x in (args.evidence or [])]
    if not evidence: raise SystemExit('at least one --evidence reference is required')
    obs={'timestamp':dt.datetime.now(dt.timezone.utc).isoformat(),'project_id':pid,'project_source':source,'confidence':args.confidence,'evidence':evidence,'note':redact(args.note or '')}
    max_obs=policy['capture'].get('max_observations_per_candidate',50)
    doc['observations']=(doc.get('observations',[])+[obs])[-max_obs:]
    doc['updated_at']=obs['timestamp']
    write_json(path,doc)
    print(json.dumps({'status':'captured','path':path.relative_to(ROOT).as_posix(),'summary':summarize(doc,policy)},indent=2,ensure_ascii=False))


def cmd_status(args, policy):
    path=candidate_path(policy,args.id)
    if not path.exists(): raise SystemExit(f'candidate not found: {args.id}')
    doc=read_json(path)
    print(json.dumps({'id':args.id,'trigger':doc.get('trigger'),'action':doc.get('action'),'status':doc.get('status'),'summary':summarize(doc,policy)},indent=2,ensure_ascii=False))


def cmd_promote(args, policy):
    path=candidate_path(policy,args.id)
    if not path.exists(): raise SystemExit(f'candidate not found: {args.id}')
    doc=read_json(path); stats=summarize(doc,policy); rule=policy['promotion'][args.scope]
    if not stats['eligible'][args.scope]:
        raise SystemExit(f'promotion criteria not met for {args.scope}: {json.dumps(stats,ensure_ascii=False)}')
    if rule.get('human_approval_required') and not args.human_approved:
        raise SystemExit('promotion requires --human-approved')
    out=curated_path(policy,args.id)
    curated={
        'schema_version':1,'id':args.id,'scope':args.scope,'trigger':doc.get('trigger'),'action':doc.get('action'),
        'promoted_at':dt.datetime.now(dt.timezone.utc).isoformat(),'human_approved':True,
        'provenance':{'source':path.relative_to(ROOT).as_posix(),'observation_count':stats['observations'],'distinct_projects':stats['distinct_projects'],'average_confidence':stats['average_confidence']},
        'policy':{'auto_mutate_skills':False},
    }
    write_json(out,curated)
    doc['status']='curated'; doc['curated_path']=out.relative_to(ROOT).as_posix(); write_json(path,doc)
    print(json.dumps({'status':'promoted','path':out.relative_to(ROOT).as_posix(),'provenance':curated['provenance'],'note':'Promotion does not modify Skills automatically.'},indent=2,ensure_ascii=False))


def main():
    ap=argparse.ArgumentParser(description='Capture evidence-backed project lessons and promote only with policy + human approval.')
    sub=ap.add_subparsers(dest='command',required=True)
    cap=sub.add_parser('capture'); cap.add_argument('--id',required=True); cap.add_argument('--trigger',required=True); cap.add_argument('--action',required=True); cap.add_argument('--confidence',type=float,required=True); cap.add_argument('--evidence',action='append'); cap.add_argument('--note'); cap.add_argument('--project-id')
    st=sub.add_parser('status'); st.add_argument('--id',required=True)
    pr=sub.add_parser('promote'); pr.add_argument('--id',required=True); pr.add_argument('--scope',choices=['project','global'],default='project'); pr.add_argument('--human-approved',action='store_true')
    args=ap.parse_args(); policy=load_policy()
    {'capture':cmd_capture,'status':cmd_status,'promote':cmd_promote}[args.command](args,policy)

if __name__=='__main__': main()
