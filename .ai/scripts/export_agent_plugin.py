#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
sys.dont_write_bytecode=True
from _common import safe_temp_base, configure_utf8_stdio, root_from_script, harness_version
SCHEMA='https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def safe_tree(root:Path):
    from _truth import inventory
    try: inventory(root); return []
    except (ValueError,OSError) as exc: return [str(exc)]

def verify(plugin:Path):
    from validate_agent_plugin import validate
    return validate(plugin)['errors']

def make_lock(stage:Path,version:str):
    files=[]
    for p in sorted(stage.rglob('*')):
        if p.is_file() and p.name!='plugin-lock.json': files.append({'path':p.relative_to(stage).as_posix(),'sha256':sha(p),'size':p.stat().st_size})
    (stage/'plugin-lock.json').write_text(json.dumps({'schema_version':1,'version':version,'scope':'skills-only','files':files},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description='Export canonical Skills as an Agent Plugins v1 skills-only artifact, then re-extract and verify the exact artifact.')
    ap.add_argument('--out',required=True); ap.add_argument('--name',default='codex-product-harness-skills'); args=ap.parse_args()
    root=root_from_script(); out=Path(args.out).resolve(); version=harness_version(root)
    if not args.name or len(args.name)>64 or args.name.lower()!=args.name or any(ch not in 'abcdefghijklmnopqrstuvwxyz0123456789-.' for ch in args.name) or args.name[0] in '-.' or args.name[-1] in '-.' or '--' in args.name or '..' in args.name: raise SystemExit('AGENT PLUGIN EXPORT: FAIL - invalid plugin name')
    source_errors=safe_tree(root/'.agents/skills')
    if source_errors: raise SystemExit('AGENT PLUGIN EXPORT: FAIL - '+ '; '.join(source_errors))
    if out.exists(): raise SystemExit('AGENT PLUGIN EXPORT: REFUSED - output exists; choose a fresh destination')
    scan=subprocess.run([sys.executable,str(root/'.ai/scripts/quarantine_scan.py'),'--target',str(root/'.agents/skills'),'--fail-on','block'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    if scan.returncode: print(scan.stdout); raise SystemExit(scan.returncode)
    with tempfile.TemporaryDirectory() as td:
        stage=Path(td)/args.name; stage.mkdir(); shutil.copytree(root/'.agents/skills',stage/'skills')
        (stage/'plugin.json').write_text(json.dumps({'$schema':SCHEMA,'name':args.name,'version':version,'description':'Portable Agent Skills exported from Codex Product Harness. Host install, permissions, sandbox, hooks, evidence, and release policy remain host-specific.'},indent=2)+'\n')
        make_lock(stage,version); errors=verify(stage)
        if errors: print('AGENT PLUGIN EXPORT: FAIL'); [print('- '+e) for e in errors]; raise SystemExit(1)
        if out.suffix.lower()=='.zip':
            out.parent.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
                for p in sorted(stage.rglob('*')):
                    if p.is_file(): z.write(p,arcname=p.relative_to(stage).as_posix())
            with tempfile.TemporaryDirectory() as xd:
                extract=Path(xd)/'exact'; extract.mkdir()
                with zipfile.ZipFile(out) as z:
                    if any('\\' in i.filename for i in z.infolist()): raise SystemExit('AGENT PLUGIN EXPORT: FAIL - non-portable ZIP path')
                    z.extractall(extract)
                errors=verify(extract)
                if errors: print('AGENT PLUGIN EXACT ARTIFACT: FAIL'); [print('- '+e) for e in errors]; raise SystemExit(1)
            print(f'AGENT PLUGIN EXPORT: PASS - 13 skills, exact artifact reverified -> {out}')
        else:
            shutil.copytree(stage,out); print(f'AGENT PLUGIN EXPORT: PASS - 13 skills -> {out}')
if __name__=='__main__': main()
