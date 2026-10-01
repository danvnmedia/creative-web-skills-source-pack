#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import zipfile
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, load_json, root_from_script
import quarantine_scan as qs


def canonical_fingerprint(f: dict) -> str:
    canonical={k:f.get(k) for k in ('rule','severity','path','detail_code','evidence_sha256')}
    raw=json.dumps(canonical,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def finding(findings:list[dict], rule:str, severity:str, path:str, detail_code:str, detail:str) -> None:
    row={'rule':rule,'severity':severity,'path':path,'detail_code':detail_code,'detail':detail[:300]}
    findings.append(row)


def read_baseline(path: str|None) -> set[str]:
    if not path: return set()
    doc=json.loads(Path(path).read_text(encoding='utf-8'))
    values=doc.get('accepted_fingerprints',[])
    if not isinstance(values,list) or any(not isinstance(v,str) or not re.fullmatch(r'[0-9a-f]{64}',v) for v in values):
        raise ValueError('baseline accepted_fingerprints must be a list of sha256 hex strings')
    return set(values)


def inspect_zip_limits(path:Path, findings:list[dict], limits:dict) -> None:
    with zipfile.ZipFile(path) as z:
        infos=[i for i in z.infolist() if not i.is_dir()]
        if len(infos)>int(limits['max_files']):
            finding(findings,'package-size-limit','block',path.name,'archive-member-count','archive member count exceeds policy limit')
        for info in infos[:int(limits['max_files'])]:
            name=info.filename.replace('\\','/')
            if len([p for p in name.split('/') if p])>int(limits['max_path_depth']):
                finding(findings,'archive-path-depth','block',name,'archive-path-depth','archive path depth exceeds policy limit')
            if info.file_size and info.compress_size >= 0:
                ratio=info.file_size/max(info.compress_size,1)
                if ratio>float(limits['max_compression_ratio']):
                    finding(findings,'archive-compression-ratio','block',name,'archive-compression-ratio',f'compression ratio {ratio:.1f} exceeds policy limit')
            mode=(info.external_attr>>16)&0xFFFF
            if stat.S_ISLNK(mode):
                finding(findings,'archive-symlink','block',name,'archive-symlink','symlink entries are rejected in untrusted Skill archives')


def parse_frontmatter(text:str) -> dict:
    if text.startswith('\ufeff'): text=text[1:]
    lines=text.replace('\r\n','\n').split('\n')
    if not lines or lines[0] != '---': return {}
    try: end=lines.index('---',1)
    except ValueError: return {}
    result={}
    for line in lines[1:end]:
        if ':' in line:
            k,v=line.split(':',1); key=k.strip()
            if key in result: return {}  # Ambiguous metadata is not clean.
            result[key]=v.strip().strip('"\'')
    return result


UNPINNED_PATTERNS=[
    ('unpinned-npx', re.compile(r'(?im)^\s*(?:npx|pnpx|bunx)\s+(?![^\s@]+@(?:\d|sha256:|git\+|https?://))([A-Za-z0-9_.@/-]+)')),
    ('unpinned-pip-install', re.compile(r'(?im)^\s*(?:python\s+-m\s+)?pip\s+install\s+(?![^\n]*(?:==|@\s*(?:https?|git\+)|--require-hashes))([^\n#]+)')),
    ('unpinned-git-clone', re.compile(r'(?im)^\s*git\s+clone\s+(?:--[^\s]+\s+)*(https?://|git@)[^\s]+')),
]


def skill_specific(rel:str, text:str, findings:list[dict]) -> None:
    if Path(rel).name.upper()=='SKILL.MD':
        fm=parse_frontmatter(text)
        if not fm.get('name') or not fm.get('description'):
            finding(findings,'skill-frontmatter','review',rel,'missing-name-or-description','SKILL.md should declare name and description')
        desc=str(fm.get('description') or '')
        if re.search(r'(?i)\b(?:any|all|every)\s+(?:task|request|prompt)s?\b|\balways\s+use\b',desc):
            finding(findings,'overbroad-trigger-scope','review',rel,'overbroad-trigger-scope','Skill description appears broader than a bounded task domain')
    for rule,pat in UNPINNED_PATTERNS:
        if pat.search(text):
            finding(findings,rule,'review',rel,rule,'remote dependency or executable source is not immutably pinned')


def main() -> None:
    configure_utf8_stdio(); root=root_from_script(); policy=load_json(root/'.ai/SKILL_SECURITY_POLICY.json'); limits=policy['limits']
    ap=argparse.ArgumentParser(description='Fail-closed deterministic security gate for Agent Skill files/directories/archives. Never executes scanned Skill code.')
    ap.add_argument('--target',required=True)
    ap.add_argument('--fail-on',choices=['block','review','never'],default=policy.get('default_fail_on','review'))
    ap.add_argument('--baseline',help='Explicit JSON file containing accepted_fingerprints for exact known findings.')
    ap.add_argument('--out')
    ap.add_argument('--cache',action='store_true')
    args=ap.parse_args(); target=Path(args.target).resolve(); findings=[]
    if not target.exists(): raise SystemExit(f'SKILL SECURITY GATE: FAIL - target not found: {target}')
    try:
        accepted=read_baseline(args.baseline)
        if target.is_file() and target.suffix.lower()=='.zip':
            inspect_zip_limits(target,findings,limits)
            qfind=[]; payload=qs.zip_payload(target,qfind,limits)
        elif target.is_dir():
            qfind=[]; payload=qs.dir_payload(target,qfind,limits)
        else:
            qfind=[]; data=target.read_bytes()
            if len(data)>int(limits['max_archive_entry_bytes']):
                finding(findings,'package-size-limit','block',target.name,'single-file-size','single Skill input exceeds policy limit')
                payload={}
            else: payload={target.name:data}
    except (OSError,ValueError,zipfile.BadZipFile) as exc:
        raise SystemExit(f'SKILL SECURITY GATE: FAIL - {exc}')
    for old in qfind:
        finding(findings,str(old.get('rule')) or 'quarantine-rule',str(old.get('severity') or 'review'),str(old.get('path') or ''),str(old.get('rule') or 'quarantine-rule'),str(old.get('detail') or ''))
    skill_paths=[]
    for rel,data in payload.items():
        if len([p for p in rel.replace('\\','/').split('/') if p])>int(limits['max_path_depth']):
            finding(findings,'path-depth','block',rel,'path-depth','Skill package path depth exceeds policy limit')
        before=[]
        qs.scan_opaque_executable(rel,data,before)
        text=qs.text_like(rel,data,int(limits['max_text_file_bytes']))
        if text is None and Path(rel).suffix.lower() in qs.TEXT_SUFFIXES and len(data)>int(limits['max_text_file_bytes']):
            finding(findings,'package-size-limit','block',rel,'text-analysis-limit','text-like file exceeds deterministic text-analysis limit; full static analysis is incomplete')
        if text is not None:
            qs.scan_text(rel,text,before)
            skill_specific(rel,text,findings)
        for old in before:
            finding(findings,str(old.get('rule')),str(old.get('severity')),rel,str(old.get('rule')),str(old.get('detail') or ''))
        if Path(rel).name.upper()=='SKILL.MD': skill_paths.append(rel)
    if not skill_paths:
        finding(findings,'missing-skill-entrypoint','block',target.name,'missing-skill-entrypoint','no SKILL.md entrypoint found')
    names={}
    for rel in skill_paths:
        text=qs.text_like(rel,payload[rel],int(limits['max_text_file_bytes'])) or ''
        name=parse_frontmatter(text).get('name')
        if name:
            if name in names:
                finding(findings,'duplicate-skill-name','block',rel,'duplicate-skill-name',f'duplicate Skill name also declared by {names[name]}')
            else: names[name]=rel
    # Bind text findings to the exact file bytes so a baseline cannot silently accept
    # a changed payload that happens to trigger the same rule at the same path.
    for f in findings:
        data=payload.get(str(f.get('path') or ''))
        f['evidence_sha256']=hashlib.sha256(data).hexdigest() if data is not None else None
        f['fingerprint']=canonical_fingerprint(f)
    # Deduplicate exact findings from layered deterministic rules.
    dedup={f['fingerprint']:f for f in findings}; findings=[dedup[k] for k in sorted(dedup)]
    for f in findings: f['baseline_accepted']=f['fingerprint'] in accepted
    effective=[f for f in findings if not f['baseline_accepted']]
    raw_counts={s:sum(1 for f in findings if f['severity']==s) for s in ('block','review')}
    counts={s:sum(1 for f in effective if f['severity']==s) for s in ('block','review')}
    incomplete_findings=[f for f in findings if f.get('rule') in {'package-size-limit','unreadable-input','opaque-executable-artifact','python-ast-incomplete'}]
    analysis_status='complete' if not incomplete_findings else 'partial'
    # Completeness is derived from raw findings before baselines. A baseline may accept a known
    # finding but can never claim that bytes which were not analyzed were actually analyzed.
    status='block' if analysis_status!='complete' or counts['block'] else ('review' if counts['review'] else 'pass')
    digest=qs.content_hash(payload)
    report={
        'schema_version':2,'status':status,'target':str(target),'exact_bundle_sha256':digest,
        'scan_mode':'deterministic-static','semantic_analysis':'not_run','llm_used':False,'full_semantic_clean':False,
        'analysis_status':analysis_status,'analysis_complete':analysis_status=='complete',
        'analyzers_requested':['archive-or-directory-ingest','deterministic-static-text','python-ast-sink-analysis','opaque-executable-coverage','skill-structure'],
        'analyzers_completed':(['archive-or-directory-ingest','deterministic-static-text','python-ast-sink-analysis','opaque-executable-coverage','skill-structure'] if analysis_status=='complete' else ['skill-structure']),
        'resource_limit_hits':[{'rule':f.get('rule'),'path':f.get('path'),'detail_code':f.get('detail_code')} for f in incomplete_findings],
        'rule_version':policy.get('rule_version'),'skill_entrypoints':sorted(skill_paths),'files_scanned':len(payload),
        'bytes_scanned':sum(map(len,payload.values())),'raw_counts':raw_counts,'effective_counts':counts,
        'baseline_file':str(Path(args.baseline).resolve()) if args.baseline else None,
        'baseline_accepted_count':sum(1 for f in findings if f['baseline_accepted']),'findings':findings,
        'code_executed_from_target':False,'scanner':'codex-product-harness/skill_security_gate.py'
    }
    rendered=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if args.out:
        p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(rendered,encoding='utf-8')
    if args.cache:
        p=root/'.ai/checkpoints/security/skills'/f'{digest}.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(rendered,encoding='utf-8')
    print(rendered,end='')
    if args.fail_on=='block' and (analysis_status!='complete' or counts['block']): raise SystemExit(1)
    if args.fail_on=='review' and (analysis_status!='complete' or counts['block'] or counts['review']): raise SystemExit(1)

if __name__=='__main__': main()
