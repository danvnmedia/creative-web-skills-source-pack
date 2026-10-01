#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True

from _common import harness_context
from install_plan import find_block

ROOT=Path(__file__).resolve().parents[2]
SOURCE_SURFACES=['AGENTS.md','GEMINI.md','CLAUDE.md','ANTIGRAVITY.md','.agents','.ai']
BIDI=set(chr(x) for x in [0x202A,0x202B,0x202D,0x202E,0x202C,0x2066,0x2067,0x2068,0x2069])
SECRET_REGEXES=[
    re.compile(r'AIza[0-9A-Za-z_\-]{20,}'),
    re.compile(r'\bsk-[A-Za-z0-9_\-]{16,}\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
]
DANGEROUS=[
    ('pipe-to-shell', re.compile(r'(?i)\b(?:curl|wget)\b[^\n|]*\|\s*(?:sh|bash|zsh)\b')),
    ('world-writable', re.compile(r'(?i)\bchmod\s+(?:-R\s+)?777\b')),
    ('root-delete', re.compile(r'(?i)\brm\s+-rf\s+/(?:\s|$)')),
]


def source_files():
    for rel in SOURCE_SURFACES:
        p=ROOT/rel
        if p.is_file():
            yield rel,p,None
        elif p.is_dir():
            for f in p.rglob('*'):
                r=f.relative_to(ROOT).as_posix()
                if f.is_file() and not r.startswith('.ai/evidence/') and not r.startswith('.ai/tasks/') and not r.startswith('.ai/lessons/candidates/') and not r.startswith('.ai/lessons/curated/') and r != '.ai/HARNESS_INSTALL_STATE.json' and '__pycache__' not in f.parts:
                    yield r,f,None


def installed_payloads():
    state_path=ROOT/'.ai/HARNESS_INSTALL_STATE.json'
    if not state_path.is_file(): return
    try: state=json.loads(state_path.read_text(encoding='utf-8'))
    except Exception: return
    for rel,rec in (state.get('records') or {}).items():
        p=ROOT/rel; mode=rec.get('mode'); source=str(rec.get('source_path') or '')
        if mode in ('whole_file','mutable_seed') and p.is_file():
            # Match the source security boundary: control plane, Skills, and agent adapter
            # surfaces are scanned; relocated human release docs/metadata are not newly
            # promoted into a stricter attack-surface class merely because of namespacing.
            if source.startswith('.ai/') or source.startswith('.agents/') or source in {'AGENTS.md','CLAUDE.md','GEMINI.md','ANTIGRAVITY.md'}:
                yield rel,p,None
        elif mode=='managed_block' and p.is_file():
            marker=str(rec.get('marker_id') or '')
            try: found=find_block(p.read_bytes(),marker)
            except Exception: found=None
            if found:
                yield rel,p,found[2]


def scan_payload(rel: str, p: Path, raw_override: bytes | None, blockers: list, warnings: list, seen: set, incomplete: list):
    key=(rel, 'block' if raw_override is not None else 'file')
    if key in seen: return
    seen.add(key)
    if p.is_symlink():
        blockers.append({'rule':'managed-symlink','path':rel}); return
    if p.name.startswith('.env') and p.name != '.env.example': blockers.append({'rule':'environment-file-in-harness','path':rel})
    try: raw=raw_override if raw_override is not None else p.read_bytes()
    except OSError as exc:
        incomplete.append({'analyzer':'content-static','path':rel,'reason':'unreadable-harness-owned-payload','detail':str(exc)[:300]}); return
    if any(bytes(ch,'utf-8') in raw for ch in BIDI): blockers.append({'rule':'bidi-control-character','path':rel})
    text=raw.decode('utf-8',errors='replace')
    for rx in SECRET_REGEXES:
        if rx.search(text): blockers.append({'rule':'secret-like-token','path':rel})
    for rule,rx in DANGEROUS:
        if rx.search(text): blockers.append({'rule':rule,'path':rel})
    if raw_override is None:
        if os.name == 'nt':
            try:
                proc=subprocess.run(['icacls',str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',timeout=10)
                if proc.returncode==0:
                    low=proc.stdout.lower()
                    risky=[]
                    for line in proc.stdout.splitlines()[1:]:
                        ll=line.lower()
                        principal_risky=('everyone' in ll or 'builtin\\users' in ll or '\\users:' in ll)
                        can_write=any(tok in ll for tok in ('(f)','(m)','(w)'))
                        inherited='(i)' in ll
                        if principal_risky and can_write and not inherited:
                            risky.append(line.strip())
                    if risky:
                        warnings.append({'rule':'windows-explicit-broad-write-acl','path':rel,'detail':'; '.join(risky)[:500]})
                else:
                    incomplete.append({'analyzer':'native-permission-metadata','path':rel,'reason':'windows-acl-not-evaluated','detail':'icacls returned nonzero; POSIX mode bits were not used as ACL truth'})
            except Exception as exc:
                incomplete.append({'analyzer':'native-permission-metadata','path':rel,'reason':'windows-acl-not-evaluated','detail':str(exc)[:300]})
        else:
            try:
                mode=p.stat().st_mode
                if mode & 0o002: warnings.append({'rule':'world-writable-file','path':rel,'detail':'POSIX others-write bit is set'})
            except OSError as exc: incomplete.append({'analyzer':'native-permission-metadata','path':rel,'reason':'posix-mode-not-evaluated','detail':str(exc)[:300]})


def main() -> None:
    ap=argparse.ArgumentParser(description='Static security audit of Harness-owned instructions, skills, scripts, config, and managed blocks.')
    ap.add_argument('--strict', action='store_true', help='Treat warnings as failure too.')
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args(); blockers=[]; warnings=[]; seen=set(); incomplete=[]; context=harness_context(ROOT)
    payloads=installed_payloads() if context=='installed' else source_files()
    for rel,p,raw in payloads or []:
        scan_payload(rel,p,raw,blockers,warnings,seen,incomplete)
    if context=='installed' and not seen:
        blockers.append({'rule':'missing-install-ownership-state','path':'.ai/HARNESS_INSTALL_STATE.json'})
    analyzers_requested=['content-static','native-permission-metadata']; analyzers_completed=[x for x in analyzers_requested if not any(i.get('analyzer')==x for i in incomplete)]
    analysis_status='complete' if not incomplete else 'partial'
    report={'schema_version':3,'status':'pass' if analysis_status=='complete' and not blockers and not (args.strict and warnings) else 'fail','analysis_status':analysis_status,'scan_mode':'deterministic-static','context':context,'analyzers_requested':analyzers_requested,'analyzers_completed':analyzers_completed,'incomplete_reasons':incomplete,'blockers':blockers,'warnings':warnings,'files_or_blocks_scanned':len(seen),'dynamic_or_semantic_analysis':'not_run'}
    if args.json: print(json.dumps(report,indent=2,ensure_ascii=False))
    else:
        print('HARNESS SECURITY: '+('PASS' if report['status']=='pass' else 'FAIL')+f' (context={context})')
        print(f'files/blocks scanned: {len(seen)}; analysis={analysis_status}')
        for x in incomplete: print(f"[INCOMPLETE] {x['analyzer']}: {x['path']}: {x['reason']}")
        for x in warnings: print(f"[WARN] {x['rule']}: {x['path']}")
        for x in blockers: print(f"[BLOCK] {x['rule']}: {x['path']}")
    if report['status']!='pass': raise SystemExit(1)

if __name__=='__main__': main()
