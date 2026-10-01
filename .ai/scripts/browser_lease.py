#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import secrets
import sys
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, load_json, root_from_script


def now(): return dt.datetime.now(dt.timezone.utc)
def parse_ts(value:str): return dt.datetime.fromisoformat(value.replace('Z','+00:00'))
def dump(path:Path,obj): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def digest(doc:dict) -> str:
    material={k:v for k,v in doc.items() if k not in {'return_evidence','returned_at','lease_digest'}}
    return hashlib.sha256(json.dumps(material,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def load_lease(path:Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: raise SystemExit(f'BROWSER LEASE: FAIL - invalid lease: {exc}')


def validate_doc(doc:dict,policy:dict,require_returned:bool=False) -> list[str]:
    errors=[]
    if doc.get('schema_version')!=1: errors.append('schema_version must be 1')
    if not re.fullmatch(r'lease-[0-9a-f]{16}',str(doc.get('lease_id',''))): errors.append('invalid lease_id')
    if not str(doc.get('target','')).strip(): errors.append('target is required')
    scope=doc.get('scope')
    if not isinstance(scope,dict) or not any(scope.get(k) for k in ('tab_id','url_origin','window_id')): errors.append('scope requires tab_id, window_id, or url_origin')
    allowed=set(policy['defaults']['allowed_actions']); actions=doc.get('allowed_actions')
    if not isinstance(actions,list) or not actions: errors.append('allowed_actions must be non-empty')
    elif set(actions)-allowed: errors.append('allowed_actions contains values outside policy')
    try:
        created=parse_ts(doc['borrowed_at']); expires=parse_ts(doc['expires_at'])
        ttl=(expires-created).total_seconds()
        if ttl<=0 or ttl>int(policy['defaults']['max_ttl_seconds']): errors.append('lease TTL outside policy')
        if now()>=expires and not doc.get('returned_at'): errors.append('lease expired')
    except Exception: errors.append('invalid borrowed_at/expires_at')
    if doc.get('lease_digest')!=digest(doc): errors.append('lease_digest mismatch')
    if require_returned:
        if not doc.get('returned_at'): errors.append('lease has not been returned')
        if not isinstance(doc.get('return_evidence'),dict) or not doc['return_evidence'].get('returned_scope_unchanged'): errors.append('return_evidence missing scope-return proof')
    elif doc.get('returned_at'): errors.append('lease already returned')
    return errors


def main():
    configure_utf8_stdio(); root=root_from_script(); policy=load_json(root/'.ai/BROWSER_LEASE_POLICY.json')
    ap=argparse.ArgumentParser(description='Create, validate, and return an explicit lease for borrowing a logged-in browser tab/window. Disposable headless contexts do not need a lease.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('create'); c.add_argument('--target',required=True); c.add_argument('--tab-id'); c.add_argument('--window-id'); c.add_argument('--url-origin'); c.add_argument('--ttl-seconds',type=int,default=int(policy['defaults']['ttl_seconds'])); c.add_argument('--allow',action='append',dest='actions'); c.add_argument('--out',required=True)
    v=sub.add_parser('validate'); v.add_argument('--lease',required=True); v.add_argument('--require-action'); v.add_argument('--tab-id'); v.add_argument('--window-id'); v.add_argument('--url-origin')
    r=sub.add_parser('return'); r.add_argument('--lease',required=True); r.add_argument('--evidence',required=True,help='Human/tool evidence string proving the borrowed scope was returned unchanged.');
    args=ap.parse_args()
    if args.cmd=='create':
        if args.ttl_seconds<=0 or args.ttl_seconds>int(policy['defaults']['max_ttl_seconds']): raise SystemExit('BROWSER LEASE: FAIL - ttl outside policy')
        scope={k:v for k,v in {'tab_id':args.tab_id,'window_id':args.window_id,'url_origin':args.url_origin}.items() if v}
        if not scope: raise SystemExit('BROWSER LEASE: FAIL - provide tab-id, window-id, or url-origin')
        actions=args.actions or list(policy['defaults']['allowed_actions']); unsupported=set(actions)-set(policy['defaults']['allowed_actions'])
        if unsupported: raise SystemExit('BROWSER LEASE: FAIL - unsupported actions: '+', '.join(sorted(unsupported)))
        created=now(); expires=created+dt.timedelta(seconds=args.ttl_seconds)
        doc={'schema_version':1,'lease_id':'lease-'+secrets.token_hex(8),'target':args.target,'scope':scope,'allowed_actions':actions,'borrowed_at':created.isoformat(),'expires_at':expires.isoformat(),'returned_at':None,'return_evidence':None}
        doc['lease_digest']=digest(doc); out=Path(args.out); dump(out,doc); print(json.dumps(doc,indent=2,ensure_ascii=False)); return
    path=Path(args.lease); doc=load_lease(path)
    if args.cmd=='validate':
        errors=validate_doc(doc,policy)
        if args.require_action and args.require_action not in set(doc.get('allowed_actions') or []): errors.append(f'action not leased: {args.require_action}')
        supplied={k:v for k,v in {'tab_id':args.tab_id,'window_id':args.window_id,'url_origin':args.url_origin}.items() if v}
        for k,v in supplied.items():
            if (doc.get('scope') or {}).get(k)!=v: errors.append(f'scope mismatch for {k}')
        if errors:
            print('BROWSER LEASE: FAIL'); [print('- '+e) for e in errors]; raise SystemExit(1)
        print(f"BROWSER LEASE: PASS - {doc['lease_id']} active and in scope"); return
    errors=validate_doc(doc,policy)
    if errors:
        print('BROWSER LEASE RETURN: FAIL'); [print('- '+e) for e in errors]; raise SystemExit(1)
    doc['returned_at']=now().isoformat(); doc['return_evidence']={'returned_scope_unchanged':True,'evidence':args.evidence,'scope':doc.get('scope')}; doc['lease_digest']=digest(doc); dump(path,doc)
    verify=validate_doc(doc,policy,require_returned=True)
    if verify:
        print('BROWSER LEASE RETURN: FAIL'); [print('- '+e) for e in verify]; raise SystemExit(1)
    print(f"BROWSER LEASE RETURN: PASS - {doc['lease_id']}")

if __name__=='__main__': main()
