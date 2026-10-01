#!/usr/bin/env python3
"""Immutable experiment identities and commit-last artifact transactions.
This validates experiment integrity, not Skill quality or host activation. No
remote submission/retry is implemented, so unknown spend is never resubmitted.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
from _truth import digest, inventory, lock, portable_rel, read_json, write_json, no_redirect_ancestors, sha as sha256

REQUIRED = {'run-contract.json','trace.jsonl','capture.json','metrics.json','output.txt'}
IDENTITY = {'agent','model','reasoning_effort','cli_version','source_revision'}


def prepare(experiment: Path, matrix: dict, skills: Path, runtime: dict, repetitions=2, split='tune', graders:dict|None=None):
    if not IDENTITY <= set(runtime) or any(not isinstance(runtime[k],str) or not runtime[k].strip() for k in IDENTITY):
        raise ValueError('complete runtime identity required')
    if split not in {'tune','holdout','holdback'} or not 1 <= repetitions <= 5:
        raise ValueError('invalid split/repetitions')
    cases = [c for c in matrix['cases'] if c.get('split','tune') == split]
    if not cases or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('empty or duplicate case selection')
    # Design is evaluator-private. Runners receive ONLY the selected prompt,
    # never this design, labels, answers, split manifests or canonical source.
    body = {'schema_version':1,'runtime':runtime,'repetitions':repetitions,'split':split,
            'matrix_sha256':digest(matrix),'canonical_skills_sha256':digest(inventory(skills)),
            'cases':[{'case_id':c['id'],'case_sha256':digest(c),'prompt_sha256':digest(c['prompt'])} for c in cases],
            'variants':['with_skill','without_skill'],'required_artifacts':sorted(REQUIRED), 'graders':graders or {}}
    design = dict(body, design_sha256=digest(body))
    experiment.mkdir(parents=True,exist_ok=False)
    write_json(experiment/'answer-design.json',design,exclusive=True)
    return design


def load_design(experiment: Path):
    no_redirect_ancestors(experiment/'answer-design.json')
    design=read_json(experiment/'answer-design.json'); body=dict(design); claimed=body.pop('design_sha256',None)
    if claimed!=digest(body) or body.get('schema_version')!=1:
        raise ValueError('experiment design tampered or unsupported')
    return design


def start(experiment: Path, run_dir: Path, case_id: str, repetition: int, variant: str, materialized: Path | None=None):
    design=load_design(experiment)
    if case_id not in {c['case_id'] for c in design['cases']} or not 1<=repetition<=design['repetitions'] or variant not in design['variants']:
        raise ValueError('run identity outside expected experiment')
    if run_dir.exists():
        raise ValueError('run destination already exists; never overwrite attempts')
    arm_tree = digest(inventory(materialized)) if materialized is not None else None
    if variant=='with_skill' and arm_tree != design['canonical_skills_sha256']:
        raise ValueError('with_skill requires the exact materialized canonical skill tree')
    if variant=='without_skill' and materialized is not None:
        raise ValueError('without_skill must not mount the skill tree')
    contract={'schema_version':1,'design_sha256':design['design_sha256'],'case_id':case_id,'run':repetition,
              'variant':variant,'runtime':design['runtime'],'canonical_skills_sha256':design['canonical_skills_sha256'],
              'materialized_tree_sha256':arm_tree}
    run_dir.mkdir(parents=True)
    write_json(run_dir/'run-contract.json',contract,exclusive=True)
    return contract


def validate_payload(experiment: Path, run_dir: Path):
    design=load_design(experiment); entries=inventory(run_dir,exclude=('artifact-commit.json',))
    if not REQUIRED <= {x['path'] for x in entries}:
        raise ValueError('partial run: missing required artifact')
    contract=read_json(run_dir/'run-contract.json')
    if contract.get('design_sha256') != design['design_sha256'] or contract.get('runtime') != design['runtime'] or contract.get('canonical_skills_sha256')!=design['canonical_skills_sha256']:
        raise ValueError('run design/runtime/revision drift')
    if contract.get('case_id') not in {c['case_id'] for c in design['cases']} or type(contract.get('run')) is not int or not 1<=contract['run']<=design['repetitions']:
        raise ValueError('unexpected case or repetition')
    if contract.get('variant') not in design['variants']:
        raise ValueError('unexpected variant')
    expected_tree=design['canonical_skills_sha256'] if contract['variant']=='with_skill' else None
    if contract.get('materialized_tree_sha256') != expected_tree:
        raise ValueError('materialized arm tree mismatch')
    capture=read_json(run_dir/'capture.json')
    if capture.get('process_complete') is not True or capture.get('provider_response_complete') is not True or capture.get('trace_complete') is not True or capture.get('returncode')!=0:
        raise ValueError('partial process/provider/trace channel')
    metrics=read_json(run_dir/'metrics.json')
    for key in ('input_tokens','output_tokens'):
        if type(metrics.get(key)) is not int or metrics[key]<0:
            raise ValueError('unmeasured token metric: '+key)
    if not isinstance(metrics.get('duration_seconds'),(float,int)) or isinstance(metrics['duration_seconds'],bool) or metrics['duration_seconds']<0:
        raise ValueError('unmeasured runtime metric')
    if metrics.get('billing_class') not in {'free','local','metered'}:
        raise ValueError('unmeasured billing class')
    if metrics['billing_class']=='metered' and (not isinstance(metrics.get('cost_usd'),(float,int)) or isinstance(metrics['cost_usd'],bool) or metrics['cost_usd']<0):
        raise ValueError('unmeasured metered cost')
    return design,contract,entries


def commit(experiment: Path, run_dir: Path):
    # Lock outside the run to avoid polluting the exact artifact inventory.
    with lock(run_dir.parent/('.'+run_dir.name+'.commit.lock')):
        if (run_dir/'artifact-commit.json').exists():
            raise ValueError('run is already committed')
        design,contract,entries=validate_payload(experiment,run_dir)
        marker={'schema_version':1,'design_sha256':design['design_sha256'],'run_contract_sha256':digest(contract),
                'files':entries,'inventory_sha256':digest(entries),'provenance':'hashed-local-artifacts-not-signed-host-attestation'}
        # This is the LAST write in the run. An interrupted marker is not a commit.
        write_json(run_dir/'artifact-commit.json',marker,exclusive=True)
    return verify(experiment,run_dir)


def verify(experiment: Path, run_dir: Path):
    design,contract,entries=validate_payload(experiment,run_dir)
    marker=read_json(run_dir/'artifact-commit.json')
    if marker.get('schema_version')!=1 or marker.get('design_sha256')!=design['design_sha256'] or marker.get('run_contract_sha256')!=digest(contract) or marker.get('files')!=entries or marker.get('inventory_sha256')!=digest(entries):
        raise ValueError('committed artifact integrity failure')
    return {'status':'committed','design_sha256':design['design_sha256'],'identity':{k:contract[k] for k in ('case_id','run','variant')},'artifact_count':len(entries)}


def compare(experiment: Path, left: Path, right: Path):
    a=verify(experiment,left); b=verify(experiment,right)
    x=a['identity']; y=b['identity']
    if a['design_sha256']!=b['design_sha256'] or (x['case_id'],x['run'])!=(y['case_id'],y['run']) or {x['variant'],y['variant']}!={'with_skill','without_skill'}:
        raise ValueError('not an exact with/without pair')
    return {'status':'pair-integrity-pass','design_sha256':a['design_sha256'],'case_id':x['case_id'],'run':x['run'],'quality_lift':'not-calculated-by-integrity-validator'}


def deterministic_grade(experiment:Path, run_dir:Path):
    """Small deterministic grader. Answers stay only in evaluator-private design.
    Criteria suitability is a reviewed experimental assumption, not proved here.
    """
    design=load_design(experiment); contract=read_json(run_dir/'run-contract.json')
    spec=design.get('graders',{}).get(contract['case_id'])
    if not isinstance(spec,dict) or spec.get('kind')!='text-predicate-v1':
        raise ValueError('missing pinned deterministic grader')
    if set(spec)-{'kind','equals','contains_all','forbids_any'} or not any(k in spec for k in ('equals','contains_all','forbids_any')):
        raise ValueError('unsupported or empty deterministic grader')
    output=run_dir/'output.txt'; no_redirect_ancestors(output)
    if output.stat().st_size>2*1024*1024:
        raise ValueError('grader output budget exceeded')
    text=output.read_text(encoding='utf-8'); checks=[]
    if 'equals' in spec:
        if not isinstance(spec['equals'],str): raise ValueError('invalid equals criterion')
        checks.append(text==spec['equals'])
    for key in ('contains_all','forbids_any'):
        if key in spec:
            values=spec[key]
            if not isinstance(values,list) or not values or any(not isinstance(x,str) or not x for x in values):
                raise ValueError('invalid predicate criteria')
            checks.extend((x in text) if key=='contains_all' else (x not in text) for x in values)
    return {'schema_version':1,'grader_kind':'text-predicate-v1','grader_sha256':digest(spec),
            'output_sha256':sha256(output),'score':1.0 if all(checks) else 0.0}


def ablation_provenance(canonical_root: Path, materialized_root: Path, removed: list[str]):
    """File-removal ablation only; no prompt simulation and no arbitrary edits."""
    parent=inventory(canonical_root); child=inventory(materialized_root)
    for rel in removed:
        portable_rel(rel)
    if not removed or len(set(removed))!=len(removed) or any(rel not in {x['path'] for x in parent} for rel in removed):
        raise ValueError('ablation must remove existing explicit files')
    expected=[x for x in parent if x['path'] not in removed]
    if child!=expected:
        raise ValueError('ablation changed more than declared removals')
    return {'canonical_parent_sha256':digest(parent),'materialized_tree_sha256':digest(child),'mechanism':'file-removal','removed':sorted(removed)}


def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('prepare'); p.add_argument('--matrix',required=True); p.add_argument('--skills',required=True); p.add_argument('--runtime',required=True); p.add_argument('--out',required=True); p.add_argument('--split',default='tune'); p.add_argument('--runs',type=int,default=2); p.add_argument('--graders')
    for name in ('start','commit','verify','grade'):
        p=sub.add_parser(name); p.add_argument('--experiment',required=True); p.add_argument('--run-dir',required=True)
        if name=='start':
            p.add_argument('--case',required=True); p.add_argument('--run',required=True,type=int); p.add_argument('--variant',choices=['with_skill','without_skill'],required=True); p.add_argument('--materialized-skills')
    p=sub.add_parser('compare'); p.add_argument('--experiment',required=True); p.add_argument('--left',required=True); p.add_argument('--right',required=True)
    a=ap.parse_args()
    try:
        if a.cmd=='prepare': result=prepare(Path(a.out),read_json(Path(a.matrix)),Path(a.skills),read_json(Path(a.runtime)),a.runs,a.split,read_json(Path(a.graders)) if a.graders else None)
        elif a.cmd=='start': result=start(Path(a.experiment),Path(a.run_dir),a.case,a.run,a.variant,Path(a.materialized_skills) if a.materialized_skills else None)
        elif a.cmd=='grade':
            result=deterministic_grade(Path(a.experiment),Path(a.run_dir))
            if (Path(a.run_dir)/'artifact-commit.json').exists(): raise ValueError('cannot grade a committed run')
            write_json(Path(a.run_dir)/'grade.json',result,exclusive=True)
        elif a.cmd=='compare': result=compare(Path(a.experiment),Path(a.left),Path(a.right))
        else: result=globals()[a.cmd](Path(a.experiment),Path(a.run_dir))
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'blocked','reason':str(exc)})); raise SystemExit(1)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
