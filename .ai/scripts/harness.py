#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
from _common import configure_utf8_stdio, root_from_script
ROOT=root_from_script(); PY=sys.executable

def verify(args)->int:
    cmd=[PY,'.ai/scripts/verify_all.py','--profile',args.profile]
    if args.task: cmd += ['--task',args.task]
    if args.record_evidence: cmd += ['--record-evidence']
    if args.allow_local_snapshot: cmd += ['--allow-local-snapshot']
    if args.explain: cmd += ['--explain']
    return subprocess.run(cmd,cwd=str(ROOT)).returncode

def cleanup(args)->int:
    residue=ROOT/'.ai/checkpoints/temp-residue.jsonl'; candidates=[]
    if residue.is_file():
        for line in residue.read_text(encoding='utf-8',errors='replace').splitlines():
            try: candidates.append(Path(json.loads(line).get('path','')))
            except Exception: pass
    temp_root=ROOT/'.ai/checkpoints/tmp'
    if temp_root.is_dir(): candidates.extend(p for p in temp_root.iterdir() if p.is_dir())
    unique=[]; seen=set()
    for p in candidates:
        try: p=p.resolve()
        except Exception: continue
        if str(p) in seen: continue
        seen.add(str(p))
        if (p/'.harness-temp-lease.json').is_file(): unique.append(p)
    if not unique:
        print('HARNESS CLEANUP: nothing leased to clean'); return 0
    for p in unique:
        print(('DELETE' if args.apply else 'WOULD DELETE')+': '+str(p))
        if args.apply:
            try: shutil.rmtree(p)
            except OSError as exc: print(f'[WARN] cleanup failed: {p}: {exc}')
    if args.apply and residue.is_file():
        remaining=[str(p) for p in unique if p.exists()]
        residue.write_text(''.join(json.dumps({'path':p})+'\n' for p in remaining),encoding='utf-8')
    return 0

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(prog='harness',description='Boundary-aware operator command plane for Codex Product Harness.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    v=sub.add_parser('verify'); v.add_argument('--profile',choices=['native','portable','audited'],default='native'); v.add_argument('--task'); v.add_argument('--record-evidence',action='store_true'); v.add_argument('--allow-local-snapshot',action='store_true'); v.add_argument('--explain',action='store_true')
    c=sub.add_parser('cleanup'); c.add_argument('--apply',action='store_true')
    args=ap.parse_args(); raise SystemExit(verify(args) if args.cmd=='verify' else cleanup(args))
if __name__=='__main__': main()
