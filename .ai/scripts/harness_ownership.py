#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
import zipfile
sys.dont_write_bytecode = True
from _common import safe_temp_base

ROOT=Path(__file__).resolve().parents[2]
tempfile.tempdir=str(safe_temp_base(ROOT))
MANIFEST=ROOT/'.ai/HARNESS_MANIFEST.json'
STATE=ROOT/'.ai/HARNESS_INSTALL_STATE.json'

from install_plan import build_plan, apply_plan, render_summary, find_block, strip_block, sha_bytes, sha_file


def load(path: Path): return json.loads(path.read_text(encoding='utf-8'))
def save(path: Path,obj): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def manifest_entries(): return {x['path']:x for x in load(MANIFEST)['entries']}


def source_payload(source: Path) -> dict[str,bytes]:
    if source.is_dir():
        return {rel:(source/rel).read_bytes() for rel in manifest_entries() if (source/rel).is_file()}
    if source.suffix.lower()=='.zip':
        out={}
        with zipfile.ZipFile(source) as z:
            names={}
            for i in z.infolist():
                if i.is_dir(): continue
                name=i.filename.replace('\\','/').lstrip('/')
                if '..' in PurePosixPath(name).parts: raise SystemExit('unsafe source ZIP path: '+name)
                names[name]=i
            for rel in manifest_entries():
                if rel in names: out[rel]=z.read(names[rel])
        return out
    raise SystemExit('source must be an extracted harness directory or zip')


def read_state():
    if not STATE.is_file(): return None
    return load(STATE)


def cmd_status(args):
    state=read_state()
    if state and int(state.get('schema_version') or 0)>=2:
        rows=[]
        for rel,rec in (state.get('records') or {}).items():
            p=ROOT/rel; mode=rec.get('mode')
            if mode=='whole_file':
                status='missing' if not p.is_file() else ('clean' if sha_file(p)==rec.get('last_managed_sha256') else 'modified')
            elif mode=='mutable_seed':
                if not p.is_file(): status='missing'
                else: status='clean' if sha_file(p)==rec.get('last_seed_sha256') else 'modified-expected'
            elif mode=='managed_block':
                if not p.is_file(): status='missing'
                else:
                    try: found=find_block(p.read_bytes(),str(rec.get('marker_id') or ''))
                    except Exception: found=None
                    status='missing' if not found else ('clean' if sha_bytes(found[2])==rec.get('last_managed_sha256') else 'modified')
            else: status='invalid-record'
            rows.append({'path':rel,'mode':mode,'status':status})
        summary={k:sum(1 for r in rows if r['status']==k) for k in ('clean','modified-expected','modified','missing','invalid-record')}
        print(json.dumps({'registered':True,'schema_version':state.get('schema_version'),'version':state.get('harness_version'),'summary':summary,'problems':[r for r in rows if r['status']!='clean']},indent=2,ensure_ascii=False))
        if summary['missing'] or summary['invalid-record']: raise SystemExit(1)
        return
    entries=manifest_entries(); rows=[]
    for rel,entry in entries.items():
        p=ROOT/rel; status='missing' if not p.is_file() else ('clean' if sha_file(p)==entry['sha256'] else 'modified')
        rows.append({'path':rel,'status':status})
    summary={k:sum(1 for r in rows if r['status']==k) for k in ('clean','modified','missing')}
    print(json.dumps({'registered':bool(state),'schema_version':(state or {}).get('schema_version'),'version':load(MANIFEST).get('harness_version'),'summary':summary,'problems':[r for r in rows if r['status']!='clean']},indent=2,ensure_ascii=False))
    if summary['missing']: raise SystemExit(1)


def cmd_adopt(args):
    if (ROOT/'.ai/SOURCE_DISTRIBUTION.json').is_file() and not args.legacy_unsafe:
        raise SystemExit('adopt is a legacy overlay recovery path. v5.4.3+ uses INSTALL_HARNESS.py plan/apply. Use --legacy-unsafe only for reviewed historical recovery.')
    entries=manifest_entries(); bad=[]
    for rel,entry in entries.items():
        p=ROOT/rel
        if not p.is_file(): bad.append(f'missing:{rel}')
        elif sha_file(p)!=entry['sha256']: bad.append(f'modified:{rel}')
    if bad and not args.force: raise SystemExit('cannot adopt non-matching legacy harness; use --force only after review: '+', '.join(bad[:20]))
    installed={rel:(sha_file(ROOT/rel) if (ROOT/rel).is_file() else None) for rel in entries}
    save(STATE,{'schema_version':1,'harness_version':load(MANIFEST).get('harness_version'),'installed_hashes':installed})
    print(f'HARNESS OWNERSHIP: adopted {len(installed)} legacy managed paths')


def cmd_bootstrap(args):
    if (ROOT/'.ai/SOURCE_DISTRIBUTION.json').is_file() and not args.legacy_unsafe:
        raise SystemExit('bootstrap is a legacy direct-overlay recovery path. Use INSTALL_HARNESS.py plan/apply for v5.4.3+ collision-safe installation.')
    source=Path(args.source).resolve(); payload=source_payload(source); entries=manifest_entries(); restored=[]; conflicts=[]; missing_source=[]
    for rel,expected in entries.items():
        data=payload.get(rel)
        if data is None or sha_bytes(data)!=expected['sha256']: missing_source.append(rel); continue
        p=ROOT/rel
        if p.is_file():
            if sha_file(p)==expected['sha256']: continue
            if not args.force: conflicts.append(rel); continue
        p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data); restored.append(rel)
    print(json.dumps({'restored':restored,'preserved_conflicts':conflicts,'missing_or_invalid_source':missing_source},indent=2,ensure_ascii=False))
    if missing_source: raise SystemExit(1)
    if conflicts and not args.force: raise SystemExit(2)


def materialize_source(source: Path):
    if source.is_dir():
        class Ctx:
            def __enter__(self): return source
            def __exit__(self,*_): return False
        return Ctx()
    if source.suffix.lower()!='.zip': raise SystemExit('source must be extracted Harness directory or ZIP')
    td=tempfile.TemporaryDirectory(); root=Path(td.name)/'source'; root.mkdir()
    with zipfile.ZipFile(source) as z:
        for i in z.infolist():
            if i.is_dir(): continue
            n=i.filename.replace('\\','/').lstrip('/'); parts=PurePosixPath(n).parts
            if '..' in parts: td.cleanup(); raise SystemExit('unsafe source ZIP path: '+n)
            dst=root/PurePosixPath(n); dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(z.read(i))
    class Ctx:
        def __enter__(self): return root
        def __exit__(self,*_): td.cleanup(); return False
    return Ctx()


def cmd_repair(args):
    state=read_state()
    if state and int(state.get('schema_version') or 0)>=2:
        with materialize_source(Path(args.source).resolve()) as src:
            plan,_=build_plan(src,ROOT); print(json.dumps(render_summary(plan),indent=2,ensure_ascii=False))
            if not args.apply:
                print('HARNESS REPAIR PLAN: read-only; use --apply --confirm <plan_digest>.')
                if not plan['safe_to_apply']: raise SystemExit(2)
                return
            if not args.confirm: raise SystemExit('repair --apply requires --confirm <plan_digest>')
            if not plan['safe_to_apply']: raise SystemExit('repair refused: protected conflicts exist')
            result=apply_plan(src,ROOT,args.confirm); print(json.dumps(result,indent=2,ensure_ascii=False)); return
    if not state: raise SystemExit('ownership state missing; use the collision-safe installer from a trusted release')
    # Legacy schema-v1 repair preserved for backward compatibility.
    source=Path(args.source).resolve(); payload=source_payload(source); installed=state.get('installed_hashes',{}); repaired=[]; preserved=[]; missing_source=[]
    for rel,expected in manifest_entries().items():
        data=payload.get(rel)
        if data is None or sha_bytes(data)!=expected['sha256']: missing_source.append(rel); continue
        p=ROOT/rel; baseline=installed.get(rel); current=sha_file(p) if p.is_file() else None
        if current==expected['sha256']: continue
        if current is not None and baseline is not None and current!=baseline and not args.force: preserved.append(rel); continue
        p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data); installed[rel]=expected['sha256']; repaired.append(rel)
    state['installed_hashes']=installed; state['harness_version']=load(MANIFEST).get('harness_version'); save(STATE,state)
    print(json.dumps({'repaired':repaired,'preserved_user_modified':preserved,'missing_or_invalid_source':missing_source},indent=2,ensure_ascii=False))
    if missing_source: raise SystemExit(1)


def cmd_uninstall(args):
    state=read_state()
    if not state: raise SystemExit('ownership state missing; refusing marker-only uninstall')
    if int(state.get('schema_version') or 0)<2:
        removable=[]; preserved=[]
        for rel,baseline in state.get('installed_hashes',{}).items():
            p=ROOT/rel
            if not p.is_file(): continue
            current=sha_file(p)
            if baseline and current==baseline: removable.append(rel)
            else: preserved.append(rel)
        print(json.dumps({'legacy_schema':1,'would_remove':removable,'preserved_user_modified':preserved,'dry_run':not args.apply},indent=2,ensure_ascii=False))
        if not args.apply: return
        for rel in sorted(removable,key=lambda x:len(Path(x).parts),reverse=True): (ROOT/rel).unlink(missing_ok=True)
        STATE.unlink(missing_ok=True); return

    operations=[]; preserved=[]; remaining={}
    for rel,rec in (state.get('records') or {}).items():
        p=ROOT/rel; mode=rec.get('mode')
        if mode=='whole_file':
            if not p.is_file(): continue
            if sha_file(p)!=rec.get('last_managed_sha256'):
                preserved.append(rel); remaining[rel]=rec; continue
            if rec.get('created_by_harness'):
                operations.append({'path':rel,'action':'remove_file'})
            else:
                # Exact pre-existing bytes were adopted but never owned; leave them.
                preserved.append(rel)
        elif mode=='mutable_seed':
            if not p.is_file(): continue
            current=sha_file(p); seed=rec.get('last_seed_sha256')
            if current==seed and rec.get('created_by_harness'):
                operations.append({'path':rel,'action':'remove_file'})
            else:
                preserved.append(rel); remaining[rel]=rec
        elif mode=='managed_block':
            if not p.is_file(): continue
            try: found=find_block(p.read_bytes(),str(rec.get('marker_id') or ''))
            except Exception: found=None
            if not found or sha_bytes(found[2])!=rec.get('last_managed_sha256'):
                preserved.append(rel); remaining[rel]=rec; continue
            after=strip_block(p.read_bytes(),str(rec.get('marker_id') or ''))
            action='remove_file' if rec.get('container_created_by_harness') and not after.strip() else 'remove_block'
            operations.append({'path':rel,'action':action,'after':after.decode('utf-8',errors='replace') if action=='remove_block' else None})
    print(json.dumps({'schema_version':2,'would_apply':[{k:v for k,v in x.items() if k!='after'} for x in operations],'preserved_or_unowned':preserved,'dry_run':not args.apply},indent=2,ensure_ascii=False))
    if not args.apply: return
    for op in operations:
        p=ROOT/op['path']
        if op['action']=='remove_file': p.unlink(missing_ok=True)
        else: p.write_text(op['after'],encoding='utf-8')
    if remaining:
        state['records']=remaining; save(STATE,state)
        print('HARNESS UNINSTALL: PARTIAL - modified managed content was preserved and remains registered')
        raise SystemExit(2)
    STATE.unlink(missing_ok=True)
    print('HARNESS UNINSTALL: PASS - only proven Harness-owned files/blocks were removed')


def main():
    ap=argparse.ArgumentParser(description='Ownership-aware status, repair, and uninstall for source-safe/installed Harness boundaries.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('status')
    a=sub.add_parser('adopt'); a.add_argument('--force',action='store_true'); a.add_argument('--legacy-unsafe',action='store_true')
    b=sub.add_parser('bootstrap'); b.add_argument('--source',required=True); b.add_argument('--force',action='store_true'); b.add_argument('--legacy-unsafe',action='store_true')
    r=sub.add_parser('repair'); r.add_argument('--source',required=True); r.add_argument('--force',action='store_true'); r.add_argument('--apply',action='store_true'); r.add_argument('--confirm')
    u=sub.add_parser('uninstall'); u.add_argument('--apply',action='store_true')
    args=ap.parse_args(); {'status':cmd_status,'adopt':cmd_adopt,'bootstrap':cmd_bootstrap,'repair':cmd_repair,'uninstall':cmd_uninstall}[args.cmd](args)

if __name__=='__main__': main()
