#!/usr/bin/env python3
"""Read-only task preparation hints; not activation telemetry or an execution gate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
from _common import derive_required_checks, load_json, resolve_task, root_from_script


def ux_errors(doc: object) -> list[str]:
    errors = []
    if not isinstance(doc, dict): return ['UX_TOKENS must be an object']
    required = {'schema_version','ui_languages','colors','spacing_px','breakpoints_px','accessibility'}
    allowed = required | {'typography','density'}
    if not required <= doc.keys(): errors.append('UX_TOKENS missing: '+', '.join(sorted(required-doc.keys())))
    if doc.keys()-allowed: errors.append('UX_TOKENS unknown keys: '+', '.join(sorted(doc.keys()-allowed)))
    if type(doc.get('schema_version')) is not int or doc['schema_version'] != 1: errors.append('UX_TOKENS schema_version must be 1')
    langs=doc.get('ui_languages')
    if not isinstance(langs,list) or not 1 <= len(langs) <= 8 or any(not isinstance(x,str) or not re.fullmatch(r'[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*',x) for x in langs): errors.append('UX_TOKENS ui_languages invalid')
    for key, limit in [('colors',64),('typography',32),('spacing_px',64),('breakpoints_px',16)]:
        if key=='typography' and key not in doc: continue
        value=doc.get(key)
        if not isinstance(value,dict) or len(value)>limit or (key!='typography' and not value): errors.append('UX_TOKENS '+key+' must be bounded nonempty object'); continue
        for name,item in value.items():
            if not isinstance(name,str) or not name or len(name)>128: errors.append('UX_TOKENS token name invalid')
            if key in ('colors','typography'):
                if not isinstance(item,str) or not 1<=len(item)<=128: errors.append('UX_TOKENS '+key+' values must be bounded strings')
            elif key=='spacing_px':
                if type(item) not in (int,float) or not 0<=item<=4096: errors.append('UX_TOKENS spacing_px outside range')
            elif type(item) is not int or not 1<=item<=8192: errors.append('UX_TOKENS breakpoints_px outside range')
    if 'density' in doc and doc['density'] not in ('compact','comfortable','spacious'): errors.append('UX_TOKENS density invalid')
    a=doc.get('accessibility')
    if not isinstance(a,dict) or set(a)!={'target','reduced_motion'}: errors.append('UX_TOKENS accessibility requires target and reduced_motion')
    elif not isinstance(a['target'],str) or not 1<=len(a['target'])<=128 or type(a['reduced_motion']) is not bool: errors.append('UX_TOKENS accessibility fields invalid')
    return errors


def guidance(root: Path, task: dict) -> dict:
    warnings=[]; recommended=[]; known=set()
    policy=load_json(root/'.ai/TRAIT_SKILL_MAP.json')
    if policy.get('advisory_only') is not True or policy.get('not_activation_telemetry') is not True:
        raise ValueError('Trait Skill map must remain advisory and non-telemetry')
    for trait,names in policy['mapping'].items():
        if (task.get('traits') or {}).get(trait) is True: recommended.extend(names)
    for row in load_json(root/'.ai/CHECK_CATALOG.json').get('runners',[]):
        known.update(row.get('checks',[]))
    quality=load_json(root/'.ai/QUALITY.json')
    # Built-in product checks can have repo-specific runners rather than catalog commands.
    for values in quality.get('trait_required_checks',{}).values(): known.update(values)
    for values in quality.get('profile_required_checks',{}).values(): known.update(values)
    known.update(quality.get('required_checks',[]))
    if (task.get('traits') or {}).get('production_release') is True and not str((task.get('release') or {}).get('revision_marker') or '').strip():
        warnings.append('RELEASE_MARKER_MISSING: configure an observable in-app build revision marker before production acceptance; HTTP success or expected-SHA echo is not exact deployed identity.')
    explicit=(task.get('verification') or {}).get('required_checks',[])
    if not isinstance(explicit,list): explicit=[]
    unknown=sorted({x for x in explicit if isinstance(x,str) and x not in known})
    for name in unknown: warnings.append(f'UNREGISTERED_CHECK: {name}; register a project runner in CHECK_CATALOG.json for comparable evidence. This advisory never removes the required check.')
    for name in sorted(set(recommended)):
        if not (root/'.agents/skills'/name/'SKILL.md').is_file(): warnings.append('MISSING_SKILL_PACKAGE: '+name)
    ux_path=root/'.ai/UX_TOKENS.json'; ux={'status':'absent','authority':'declared-project-input','is_visual_or_accessibility_acceptance':False}
    if ux_path.exists() or ux_path.is_symlink():
        if ux_path.is_symlink() or ux_path.stat().st_size>128_000:
            ux.update(status='invalid',errors=['UX_TOKENS must be a bounded regular project file'])
        else:
            try:
                errors=ux_errors(load_json(ux_path)); ux.update(status='invalid' if errors else 'structurally_valid',errors=errors,path='.ai/UX_TOKENS.json')
            except (OSError,ValueError,TypeError) as exc: ux.update(status='invalid',errors=[str(exc)])
        warnings += ux.get('errors',[])
    return {'advisory_only':True,'is_activation_evidence':False,'recommended_skills':sorted(set(recommended)),
            'unregistered_checks':unknown,'warnings':warnings,'ux_tokens':ux}


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--task');a=ap.parse_args();root=root_from_script()
    try:
        _,task=resolve_task(root,a.task); result=guidance(root,task)
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc)}));raise SystemExit(2)
    print(json.dumps(result,indent=2,ensure_ascii=True))
    if result['ux_tokens']['status']=='invalid':raise SystemExit(2)

if __name__=='__main__': main()
