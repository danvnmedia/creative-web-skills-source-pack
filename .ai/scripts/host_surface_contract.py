#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode=True

def digest_bytes(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def evaluate(snapshot:dict,mapping:dict)->dict:
    caps=snapshot.get('capabilities'); source=snapshot.get('source')
    if not isinstance(caps,list) or not all(isinstance(x,str) and x for x in caps): raise ValueError('snapshot capabilities must be a non-empty string list')
    if not isinstance(source,dict) or not source.get('kind') or not source.get('revision') or not source.get('sha256'): raise ValueError('snapshot source must pin kind, revision, and sha256')
    dispositions={'supported','pass_through','blocked','unavailable'}
    host_map=mapping.get('capabilities',{})
    bad_disp=sorted(k for k,v in host_map.items() if v not in dispositions)
    unknown=sorted(set(caps)-set(host_map)); stale=sorted(set(host_map)-set(caps))
    errors=[]
    if bad_disp: errors.append('invalid dispositions: '+', '.join(bad_disp))
    if unknown: errors.append('unclassified observed capabilities: '+', '.join(unknown))
    return {'schema_version':1,'status':'PASS' if not errors else 'FAIL','host':snapshot.get('host'),'source':source,'unknown_observed':unknown,'stale_mappings':stale,'errors':errors,'parity_claimed':False}
def main():
    ap=argparse.ArgumentParser(description='Compare a pinned machine-readable host capability snapshot against an explicit Harness support map. Performs no network fetch.')
    ap.add_argument('--snapshot',required=True);ap.add_argument('--mapping',required=True);ap.add_argument('--out');a=ap.parse_args()
    sp=Path(a.snapshot);mp=Path(a.mapping);snap=json.loads(sp.read_text(encoding='utf-8'));mapping=json.loads(mp.read_text(encoding='utf-8'))
    report=evaluate(snap,mapping);report['snapshot_file_sha256']=digest_bytes(sp.read_bytes());report['mapping_file_sha256']=digest_bytes(mp.read_bytes())
    text=json.dumps(report,indent=2,ensure_ascii=False)+'\n';print(text,end='')
    if a.out:Path(a.out).write_text(text,encoding='utf-8')
    if report['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
