#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, load_json, root_from_script


def matrix_and_policy(root: Path):
    return load_json(root/'.ai/evals/skill-routing.json'), load_json(root/'.ai/SKILL_EVAL_POLICY.json')


def validate_matrix(root: Path, matrix: dict, policy: dict) -> list[str]:
    errors=[]
    if matrix.get('version') != 1: errors.append('matrix version must be 1')
    cases=matrix.get('cases')
    if not isinstance(cases,list) or not cases: return errors+['cases must be a non-empty list']
    supported_splits=set((policy.get('split_policy') or {}).get('supported',[])) or {'tune'}
    ids=set(); by_skill={}
    for case in cases:
        cid=case.get('id'); skill=case.get('skill'); polarity=case.get('polarity'); prompt=case.get('prompt'); split=case.get('split','tune')
        if not cid or cid in ids: errors.append(f'invalid/duplicate case id: {cid!r}')
        else: ids.add(cid)
        if polarity not in {'should_trigger','should_not_trigger'}: errors.append(f'{cid}: invalid polarity {polarity!r}')
        if split not in supported_splits: errors.append(f'{cid}: unsupported split {split!r}')
        if not skill or not (root/'.agents/skills'/str(skill)/'SKILL.md').is_file(): errors.append(f'{cid}: missing skill {skill!r}')
        if not isinstance(prompt,str) or len(prompt.strip()) < 20: errors.append(f'{cid}: prompt is too short/empty')
        by_skill.setdefault(skill,set()).add(polarity)
    shipped={p.parent.name for p in (root/'.agents/skills').glob('*/SKILL.md')}
    if set(by_skill) != shipped: errors.append('skill routing matrix does not cover exactly the shipped skills')
    for skill,polarities in sorted(by_skill.items()):
        if polarities != {'should_trigger','should_not_trigger'}: errors.append(f'{skill}: both positive and negative routing cases are required')
    return errors


def load_jsonl(path: Path) -> list[dict]:
    rows=[]
    if not path.is_file(): return rows
    from _truth import parse_json, no_redirect_ancestors
    no_redirect_ancestors(path)
    if path.stat().st_size>16*1024*1024: raise ValueError('eval rows exceed size budget')
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: row=parse_json(line)
        except Exception as exc: raise ValueError(f'{path}:{i}: invalid JSONL: {exc}')
        if not isinstance(row,dict): raise ValueError(f'{path}:{i}: row must be an object')
        rows.append(row)
    return rows


def activation_report(matrix: dict, policy: dict, runs_path: Path, root: Path | None=None, legacy_diagnostic: bool=False) -> tuple[dict,int]:
    cases={c['id']:c for c in matrix['cases']}; rows=load_jsonl(runs_path)
    accepted=set(policy['activation_acceptance']['accepted_telemetry']); min_runs=int(policy['activation_acceptance']['min_runs_per_case'])
    min_pos=float(policy['activation_acceptance']['min_should_trigger_rate']); max_neg=float(policy['activation_acceptance']['max_should_not_trigger_rate'])
    grouped={cid:[] for cid in cases}; rejected=[]; seen_runs=set()
    for row in rows:
        cid=row.get('case_id')
        if cid not in cases: rejected.append({'case_id':cid,'reason':'unknown-case'}); continue
        telemetry=row.get('telemetry')
        if telemetry not in accepted: rejected.append({'case_id':cid,'reason':f'untrusted-telemetry:{telemetry}'}); continue
        if not legacy_diagnostic:
            try:
                from skill_trigger_eval import validate_row
                derived=validate_row(row,runs_path.parent,cases[cid],root/'.agents/skills' if root else None)
                key=(cid,row.get('run'))
                if key in seen_runs or type(row.get('run')) is not int or row['run']<1:
                    raise ValueError('duplicate-or-invalid-repetition')
                seen_runs.add(key)
                row=dict(row,observed_skills=[cases[cid]['skill']] if derived['state']=='TRIGGERED' else [])
            except (ValueError,OSError,KeyError,TypeError) as exc:
                rejected.append({'case_id':cid,'reason':str(exc)}); continue
        observed=row.get('observed_skills')
        if not isinstance(observed,list): rejected.append({'case_id':cid,'reason':'observed_skills-not-list'}); continue
        grouped[cid].append(row)
    case_results=[]; insufficient=[]; pos_total=pos_hit=neg_total=neg_hit=0
    for cid,case in cases.items():
        usable=grouped[cid]
        if len(usable) < min_runs:
            insufficient.append(cid); case_results.append({'case_id':cid,'status':'not-measured','usable_runs':len(usable),'required_runs':min_runs}); continue
        skill=case['skill']; fires=sum(1 for row in usable if skill in row.get('observed_skills',[])); rate=fires/len(usable)
        if case['polarity']=='should_trigger': pos_total+=len(usable); pos_hit+=fires; ok=rate>=min_pos
        else: neg_total+=len(usable); neg_hit+=fires; ok=rate<=max_neg
        case_results.append({'case_id':cid,'skill':skill,'polarity':case['polarity'],'usable_runs':len(usable),'trigger_rate':round(rate,4),'status':'pass' if ok else 'fail'})
    pos_rate=(pos_hit/pos_total) if pos_total else None; neg_rate=(neg_hit/neg_total) if neg_total else None
    failures=[x['case_id'] for x in case_results if x.get('status')=='fail']
    status='pass' if not rejected and not insufficient and not failures and pos_rate is not None and neg_rate is not None and pos_rate>=min_pos and neg_rate<=max_neg else 'fail'
    result={'schema_version':2,'mode':'activation','status':status,'runs_path':str(runs_path),'telemetry_policy':{'accepted':sorted(accepted),'self_report_is_not_proof':True},'summary':{'should_trigger_rate':None if pos_rate is None else round(pos_rate,4),'should_not_trigger_false_positive_rate':None if neg_rate is None else round(neg_rate,4),'min_should_trigger_rate':min_pos,'max_should_not_trigger_rate':max_neg,'min_runs_per_case':min_runs},'insufficient_cases':insufficient,'failed_cases':failures,'rejected_rows':rejected,'cases':case_results,'note':'Package presence, agent self-report, and generic file-read inference do not prove autonomous Skill activation.'}
    result['acceptance_eligible']=status=='pass' and not legacy_diagnostic
    result['legacy_diagnostic']=legacy_diagnostic
    return result,0 if status=='pass' else 1


def finite_num(value): return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value))


def metric(row:dict,name:str): return (row.get('metrics') or {}).get(name)

def total_tokens(row:dict): return int(metric(row,'input_tokens'))+int(metric(row,'output_tokens'))

def score(row:dict): return float(row.get('score'))


def validate_causal_row(row:dict,cases:dict,causal:dict) -> list[str]:
    errors=[]; cid=row.get('case_id'); variant=row.get('variant'); run=row.get('run'); runtime=row.get('runtime') or {}; metrics=row.get('metrics') or {}
    if cid not in cases: errors.append('unknown-case')
    if variant not in {'with_skill','without_skill'}: errors.append('invalid-variant')
    if not isinstance(run,int) or run<1: errors.append('invalid-run')
    if not finite_num(row.get('score')) or not 0<=float(row.get('score',-1))<=1: errors.append('score-must-be-0..1')
    for field in causal['required_runtime_identity_fields']:
        if not isinstance(runtime.get(field),str) or not runtime.get(field).strip(): errors.append(f'missing-runtime:{field}')
    origin=runtime.get('artifact_origin','source')
    if origin not in causal['artifact_policy']['accepted_artifact_origins']: errors.append('invalid-artifact-origin')
    for field in causal['required_metrics']:
        if field not in metrics: errors.append(f'missing-metric:{field}')
    for field in ('input_tokens','output_tokens'):
        if field in metrics and (not isinstance(metrics[field],int) or isinstance(metrics[field],bool) or metrics[field]<0): errors.append(f'invalid-metric:{field}')
    if 'duration_seconds' in metrics and (not finite_num(metrics['duration_seconds']) or float(metrics['duration_seconds'])<0): errors.append('invalid-metric:duration_seconds')
    billing=metrics.get('billing_class')
    if billing not in causal['billing_classes']: errors.append('invalid-metric:billing_class')
    if billing=='metered':
        if not finite_num(metrics.get('cost_usd')) or float(metrics.get('cost_usd',-1))<0: errors.append('metered-run-requires-cost_usd')
    elif metrics.get('cost_usd') is not None and (not finite_num(metrics.get('cost_usd')) or float(metrics.get('cost_usd'))<0): errors.append('invalid-metric:cost_usd')
    return errors


def ratio_improvement(base:float,with_value:float) -> float|None:
    if base<=0: return None
    return (base-with_value)/base


def causal_report(matrix:dict,policy:dict,runs_path:Path,require_exact_artifact:bool=False,root:Path|None=None,legacy_diagnostic:bool=False) -> tuple[dict,int]:
    cases={c['id']:c for c in matrix['cases']}; causal=policy['causal_acceptance']; budget=causal['budget']; rows=load_jsonl(runs_path); rejected=[]; valid=[]
    integrity_errors=[]
    if not legacy_diagnostic:
        from skill_eval_acceptance import causal_integrity
        integrity_errors=causal_integrity(rows,runs_path.parent,matrix,root)
    for idx,row in enumerate(rows,1):
        errors=validate_causal_row(row,cases,causal)
        if errors: rejected.append({'row':idx,'case_id':row.get('case_id'),'run':row.get('run'),'variant':row.get('variant'),'reasons':errors}); continue
        valid.append(row)
    grouped={}
    for row in valid: grouped.setdefault((row['case_id'],row['run']),[]).append(row)
    pair_errors=[]; pairs=[]; case_run_counts={}
    identity_fields=causal['required_runtime_identity_fields']
    for key,items in sorted(grouped.items()):
        arms={}
        for row in items:
            if row['variant'] in arms: pair_errors.append({'pair':list(key),'reason':f'duplicate-arm:{row["variant"]}'})
            arms[row['variant']]=row
        if set(arms)!={'with_skill','without_skill'}:
            pair_errors.append({'pair':list(key),'reason':'missing-paired-arm'}); continue
        w,b=arms['with_skill'],arms['without_skill']
        mismatches=[f for f in identity_fields if (w.get('runtime') or {}).get(f)!=(b.get('runtime') or {}).get(f)]
        if mismatches: pair_errors.append({'pair':list(key),'reason':'runtime-identity-mismatch','fields':mismatches}); continue
        case_run_counts[key[0]]=case_run_counts.get(key[0],0)+1; pairs.append((key,w,b))
    for cid,count in case_run_counts.items():
        if count>int(budget['max_runs_per_case']): pair_errors.append({'case_id':cid,'reason':'max-runs-per-case-exceeded','count':count})
    all_case_ids={row['case_id'] for row in valid}
    insufficient=[cid for cid in sorted(all_case_ids) if case_run_counts.get(cid,0)<int(causal['min_paired_runs_per_case'])]
    budget_errors=[]; total_suite_tokens=0; total_suite_duration=0.0; total_suite_cost=0.0
    for row in valid:
        t=total_tokens(row); d=float(metric(row,'duration_seconds')); c=float(metric(row,'cost_usd') or 0.0)
        total_suite_tokens+=t; total_suite_duration+=d; total_suite_cost+=c
        if t>int(budget['max_tokens_per_run']): budget_errors.append({'case_id':row['case_id'],'run':row['run'],'variant':row['variant'],'reason':'tokens-per-run-over-budget','actual':t})
        if d>float(budget['max_duration_seconds_per_run']): budget_errors.append({'case_id':row['case_id'],'run':row['run'],'variant':row['variant'],'reason':'duration-per-run-over-budget','actual':d})
        if (row['metrics']['billing_class']=='metered' and c>float(budget['max_cost_usd_per_run'])): budget_errors.append({'case_id':row['case_id'],'run':row['run'],'variant':row['variant'],'reason':'cost-per-run-over-budget','actual':c})
    if total_suite_tokens>int(budget['max_total_suite_tokens']): budget_errors.append({'reason':'suite-tokens-over-budget','actual':total_suite_tokens})
    if total_suite_duration>float(budget['max_total_suite_duration_seconds']): budget_errors.append({'reason':'suite-duration-over-budget','actual':round(total_suite_duration,3)})
    if total_suite_cost>float(budget['max_total_suite_cost_usd']): budget_errors.append({'reason':'suite-cost-over-budget','actual':round(total_suite_cost,6)})
    case_results=[]; exact_origins=set(causal['artifact_policy']['exact_artifact_origins']); exact_seen=False
    for cid in sorted(all_case_ids):
        cp=[(w,b) for (key,w,b) in pairs if key[0]==cid]
        if not cp: continue
        q_with=sum(score(w) for w,b in cp)/len(cp); q_base=sum(score(b) for w,b in cp)/len(cp); q_delta=q_with-q_base
        tw=sum(total_tokens(w) for w,b in cp)/len(cp); tb=sum(total_tokens(b) for w,b in cp)/len(cp)
        dw=sum(float(metric(w,'duration_seconds')) for w,b in cp)/len(cp); db=sum(float(metric(b,'duration_seconds')) for w,b in cp)/len(cp)
        cw=sum(float(metric(w,'cost_usd') or 0) for w,b in cp)/len(cp); cb=sum(float(metric(b,'cost_usd') or 0) for w,b in cp)/len(cp)
        token_gain=ratio_improvement(tb,tw); duration_gain=ratio_improvement(db,dw); cost_gain=ratio_improvement(cb,cw)
        for w,b in cp:
            if (w.get('runtime') or {}).get('artifact_origin') in exact_origins or (b.get('runtime') or {}).get('artifact_origin') in exact_origins: exact_seen=True
        no_regression=q_delta>=-float(causal['max_quality_regression'])-1e-12
        meaningful=q_delta>=float(causal['min_quality_lift']) or any(x is not None and x>=float(causal['min_efficiency_improvement_ratio']) for x in (token_gain,duration_gain,cost_gain))
        status='pass' if no_regression and meaningful and len(cp)>=int(causal['min_paired_runs_per_case']) else 'fail'
        case_results.append({'case_id':cid,'paired_runs':len(cp),'status':status,'quality':{'with_skill':round(q_with,4),'without_skill':round(q_base,4),'delta':round(q_delta,4)},'efficiency_improvement_ratio':{'tokens':None if token_gain is None else round(token_gain,4),'duration':None if duration_gain is None else round(duration_gain,4),'cost':None if cost_gain is None else round(cost_gain,4)}})
    exact_error=require_exact_artifact and not exact_seen
    failed_cases=[x['case_id'] for x in case_results if x['status']!='pass']
    status='pass' if rows and not integrity_errors and not rejected and not pair_errors and not insufficient and not budget_errors and not failed_cases and not exact_error else 'fail'
    result={'schema_version':2,'mode':'causal','status':status,'runs_path':str(runs_path),'paired_runs':len(pairs),'cases':case_results,'failed_cases':failed_cases,'insufficient_cases':insufficient,'rejected_rows':rejected,'pair_errors':pair_errors,'budget':{'policy':budget,'observed':{'total_tokens':total_suite_tokens,'total_duration_seconds':round(total_suite_duration,3),'total_cost_usd':round(total_suite_cost,6)},'errors':budget_errors},'exact_artifact':{'required':require_exact_artifact,'seen':exact_seen,'accepted_origins':sorted(exact_origins)},'causal_rule':'Pass requires paired same-runtime arms, no quality regression, and either >=5% quality lift or >=5% measured token/duration/cost improvement, all within explicit budgets.'}
    result['integrity_errors']=integrity_errors
    result['acceptance_eligible']=status=='pass' and not legacy_diagnostic
    result['legacy_diagnostic']=legacy_diagnostic
    if exact_error: result['exact_artifact']['error']='loader/export change requires a reextracted-zip or published-package run'
    return result,0 if status=='pass' else 1


def append_audit(path:Path,result:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    event={'timestamp':dt.datetime.now(dt.timezone.utc).isoformat(),'mode':result.get('mode'),'status':result.get('status'),'runs_path':result.get('runs_path'),'paired_runs':result.get('paired_runs'),'failed_cases':result.get('failed_cases'),'budget_observed':(result.get('budget') or {}).get('observed'),'exact_artifact':result.get('exact_artifact')}
    with path.open('a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')


def main() -> None:
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description='Validate Skill routing and causal acceptance without treating package presence or self-report as activation proof.')
    sub=ap.add_subparsers(dest='cmd',required=True); sub.add_parser('validate')
    p=sub.add_parser('prepare'); p.add_argument('--out',required=True); p.add_argument('--runs-per-case',type=int,default=2); p.add_argument('--split',default='tune')
    r=sub.add_parser('report'); r.add_argument('--runs',required=True); r.add_argument('--out'); r.add_argument('--legacy-diagnostic',action='store_true'); r.add_argument('--fail-on-regression',action='store_true')
    c=sub.add_parser('causal-report'); c.add_argument('--runs',required=True); c.add_argument('--out'); c.add_argument('--legacy-diagnostic',action='store_true'); c.add_argument('--audit-log'); c.add_argument('--require-exact-artifact',action='store_true'); c.add_argument('--fail-on-regression',action='store_true')
    args=ap.parse_args(); root=root_from_script(); matrix,policy=matrix_and_policy(root); errors=validate_matrix(root,matrix,policy)
    if errors:
        print('SKILL EVAL CONTRACT: FAIL'); [print(f'- {e}') for e in errors]; raise SystemExit(1)
    if args.cmd=='validate':
        print(f"SKILL EVAL CONTRACT: PASS - {len(matrix['cases'])} cases across {len({c['skill'] for c in matrix['cases']})} skills; causal budgets enabled") ; return
    if args.cmd=='prepare':
        if args.runs_per_case<1: raise SystemExit('--runs-per-case must be >= 1')
        if args.split not in set(policy['split_policy']['supported']): raise SystemExit(f'unsupported split: {args.split}')
        out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); lines=[]
        for case in matrix['cases']:
            if case.get('split','tune')!=args.split: continue
            for run_no in range(1,args.runs_per_case+1): lines.append(json.dumps({'case_id':case['id'],'prompt':case['prompt'],'split':case.get('split','tune'),'run':run_no},ensure_ascii=False))
        out.write_text('\n'.join(lines)+('\n' if lines else ''),encoding='utf-8'); print(f'SKILL EVAL PREPARE: PASS - {len(lines)} answer-key-safe rows -> {out}'); return
    if args.cmd=='report': result,code=activation_report(matrix,policy,Path(args.runs),root,args.legacy_diagnostic)
    else:
        result,code=causal_report(matrix,policy,Path(args.runs),args.require_exact_artifact,root,args.legacy_diagnostic)
        if args.audit_log: append_audit(Path(args.audit_log),result)
    rendered=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.out:
        out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(rendered,encoding='utf-8')
    print(rendered,end='')
    if args.fail_on_regression and code: raise SystemExit(code)

if __name__=='__main__': main()
