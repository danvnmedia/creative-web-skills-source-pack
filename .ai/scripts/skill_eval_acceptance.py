#!/usr/bin/env python3
"""Revalidate live Skill evidence at recording AND closure; fail closed.
Local collector/adapter files are an operator trust boundary, not remote host
attestation. Diagnostic and fixture results can never satisfy this contract.
"""
from __future__ import annotations
import re, sys
from pathlib import Path
sys.dont_write_bytecode = True
from _truth import digest, inventory, no_redirect_ancestors, portable_rel, read_json, sha as sha256


def contained(base:Path, rel:str) -> Path:
    portable_rel(rel)
    result=base.joinpath(*rel.split('/'))
    no_redirect_ancestors(result)
    result.resolve().relative_to(base.resolve())
    return result


def causal_integrity(rows:list, base:Path, matrix:dict, root:Path|None) -> list[str]:
    from skill_eval_transaction import verify, load_design, deterministic_grade
    errors=[]; seen=set(); designs={}; expected=set()
    if not rows:
        return ['no committed paired runs']
    canonical=digest(inventory(root/'.agents/skills')) if root else None
    for i,row in enumerate(rows,1):
        try:
            experiment=contained(base,row['experiment_dir']); run_dir=contained(base,row['artifact_dir'])
            verify(experiment,run_dir)
            design=load_design(experiment); contract=read_json(run_dir/'run-contract.json')
            if design['matrix_sha256']!=digest(matrix) or canonical is None or design['canonical_skills_sha256']!=canonical:
                raise ValueError('current matrix/canonical skill revision mismatch')
            for key in ('case_id','run','variant','runtime'):
                if row.get(key)!=contract.get(key):
                    raise ValueError('row differs from committed identity: '+key)
            if row.get('metrics')!=read_json(run_dir/'metrics.json'):
                raise ValueError('row differs from committed metrics')
            capture=read_json(run_dir/'capture.json')
            if capture.get('evidence_tier')!='live-host-capture' or not re.fullmatch(r'[a-f0-9]{64}',str(capture.get('approved_adapter_sha256',''))):
                raise ValueError('causal capture is not an approved live collector result')
            if capture.get('trace_sha256')!=sha256(run_dir/'trace.jsonl'):
                raise ValueError('causal raw trace hash mismatch')
            grade=deterministic_grade(experiment,run_dir)
            if read_json(run_dir/'grade.json')!=grade or row.get('score')!=grade['score']:
                raise ValueError('score differs from reproducible deterministic grader')
            key=(row['case_id'],row['run'],row['variant'])
            if key in seen:
                raise ValueError('duplicate experiment cell')
            seen.add(key); designs[design['design_sha256']]=design
            expected.update((c['case_id'],n,v) for c in design['cases'] for n in range(1,design['repetitions']+1) for v in design['variants'])
        except (ValueError,OSError,KeyError,TypeError) as exc:
            errors.append(f'row {i}: {exc}')
    if len(designs)!=1:
        errors.append('comparison requires exactly one experiment design')
    if seen!=expected:
        errors.append('incomplete or unexpected experiment cells')
    return errors


def command_binding(root:Path, argv:list[str]) -> dict:
    """Bind only the shipped report command, never a shell/echo/legacy report."""
    if len(argv)<6 or not Path(argv[0]).name.lower().startswith(('python','py.exe')):
        raise ValueError('skill-eval-live must execute the shipped Python report command')
    script=Path(argv[1]); script=script if script.is_absolute() else root/script
    if script.resolve()!=(root/'.ai/scripts/skill_eval.py').resolve():
        raise ValueError('unrecognized live Skill evaluator')
    mode=argv[2]
    if mode not in ('report','causal-report') or '--legacy-diagnostic' in argv or '--fail-on-regression' not in argv:
        raise ValueError('live acceptance requires strict report and --fail-on-regression')
    allowed_values={'--runs','--out','--audit-log'}; allowed_flags={'--fail-on-regression','--require-exact-artifact'}
    values={}; flags=set(); i=3
    while i<len(argv):
        key=argv[i]
        if key in values or key in flags:
            raise ValueError('duplicate report option')
        if key in allowed_values and i+1<len(argv):
            values[key]=argv[i+1]; i+=2
        elif key in allowed_flags:
            flags.add(key); i+=1
        else:
            raise ValueError('unsupported report option')
    path=Path(values['--runs']); path=path if path.is_absolute() else root/path
    no_redirect_ancestors(path)
    rel=path.resolve().relative_to(root.resolve()).as_posix()
    if not rel.startswith(('.ai/checkpoints/','.ai/evidence/')):
        raise ValueError('live run evidence must remain in project runtime/evidence storage')
    return {'schema_version':1,'mode':mode,'runs':rel,'runs_sha256':sha256(path),
            'require_exact_artifact':'--require-exact-artifact' in flags,
            'evaluator_sha256':sha256(root/'.ai/scripts/skill_eval.py')}


def validate_binding(root:Path,binding:dict) -> dict:
    from skill_eval import matrix_and_policy, activation_report, causal_report
    if not isinstance(binding,dict) or binding.get('schema_version')!=1:
        raise ValueError('missing v5.5.2+ live evidence binding; rerun or use a bounded approved waiver')
    runs=contained(root,binding['runs'])
    if binding.get('runs_sha256')!=sha256(runs) or binding.get('evaluator_sha256')!=sha256(root/'.ai/scripts/skill_eval.py'):
        raise ValueError('live evidence/evaluator changed after recording')
    matrix,policy=matrix_and_policy(root)
    if binding.get('mode')=='report':
        report,code=activation_report(matrix,policy,runs,root)
    elif binding.get('mode')=='causal-report':
        report,code=causal_report(matrix,policy,runs,bool(binding.get('require_exact_artifact')),root)
    else:
        raise ValueError('unrecognized live evidence mode')
    if code or not report.get('acceptance_eligible'):
        raise ValueError('live evidence artifacts no longer satisfy strict acceptance')
    return {'status':'pass','mode':binding['mode'],'runs_sha256':binding['runs_sha256']}
