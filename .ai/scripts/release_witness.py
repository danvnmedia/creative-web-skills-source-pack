#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import zipfile
sys.dont_write_bytecode = True


def sha_bytes(data:bytes): return hashlib.sha256(data).hexdigest()
def sha_file(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def canonical(doc:dict)->bytes:
    material={k:v for k,v in doc.items() if k!='signature'}
    return json.dumps(material,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')

def zip_member(path:Path,name:str)->bytes:
    with zipfile.ZipFile(path) as z: return z.read(name)

def load_crypto():
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
        return serialization,Ed25519PrivateKey,Ed25519PublicKey
    except Exception as exc: raise SystemExit(f'RELEASE WITNESS: FAIL - Ed25519 signing/verification requires optional cryptography package: {exc}')

def create(args):
    artifact=Path(args.artifact).resolve()
    version=zip_member(artifact,'VERSION').decode('utf-8-sig').strip(); manifest=zip_member(artifact,'.ai/HARNESS_MANIFEST.json'); sbom=zip_member(artifact,'SBOM.spdx.json')
    with zipfile.ZipFile(artifact) as z: file_count=len([i for i in z.infolist() if not i.is_dir()])
    doc={'schema_version':1,'release':'Codex Product Harness','harness_version':version,'canonical_baseline':'5.3.0','artifact':{'name':artifact.name,'size':artifact.stat().st_size,'sha256':sha_file(artifact),'file_count':file_count},'embedded':{'manifest_sha256':sha_bytes(manifest),'sbom_sha256':sha_bytes(sbom)},'created_at_utc':dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),'signature':{'status':'absent','algorithm':None,'key_sha256':None,'public_key_base64':None,'value_base64':None}}
    if args.sign_key:
        serialization,Ed25519PrivateKey,_=load_crypto(); key=serialization.load_pem_private_key(Path(args.sign_key).read_bytes(),password=None)
        if not isinstance(key,Ed25519PrivateKey): raise SystemExit('RELEASE WITNESS: FAIL - sign key is not Ed25519')
        pub=key.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
        sig=key.sign(canonical(doc)); doc['signature']={'status':'signed','algorithm':'ed25519','key_sha256':sha_bytes(pub),'public_key_base64':base64.b64encode(pub).decode(),'value_base64':base64.b64encode(sig).decode()}
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"RELEASE WITNESS: CREATED - signature={doc['signature']['status']} -> {out}")

def verify(args):
    artifact=Path(args.artifact).resolve(); witness=json.loads(Path(args.witness).read_text(encoding='utf-8')); errors=[]
    art=witness.get('artifact') or {}
    if art.get('sha256')!=sha_file(artifact): errors.append('artifact sha256 mismatch')
    if art.get('size')!=artifact.stat().st_size: errors.append('artifact size mismatch')
    try:
        version=zip_member(artifact,'VERSION').decode('utf-8-sig').strip(); manifest=zip_member(artifact,'.ai/HARNESS_MANIFEST.json'); sbom=zip_member(artifact,'SBOM.spdx.json')
        if witness.get('harness_version')!=version: errors.append('harness version mismatch')
        if (witness.get('embedded') or {}).get('manifest_sha256')!=sha_bytes(manifest): errors.append('manifest hash mismatch')
        if (witness.get('embedded') or {}).get('sbom_sha256')!=sha_bytes(sbom): errors.append('SBOM hash mismatch')
    except Exception as exc: errors.append(f'cannot verify embedded release controls: {exc}')
    sig=witness.get('signature') or {}; sig_status='absent'
    if sig.get('status')=='signed':
        serialization,_,Ed25519PublicKey=load_crypto()
        try:
            embedded=base64.b64decode(sig['public_key_base64']); signature=base64.b64decode(sig['value_base64'])
            if sha_bytes(embedded)!=sig.get('key_sha256'): errors.append('embedded public key fingerprint mismatch')
            Ed25519PublicKey.from_public_bytes(embedded).verify(signature,canonical(witness)); sig_status='verified-untrusted-key'
            if args.trusted_public_key:
                trusted=serialization.load_pem_public_key(Path(args.trusted_public_key).read_bytes())
                if not isinstance(trusted,Ed25519PublicKey): errors.append('trusted public key is not Ed25519')
                else:
                    raw=trusted.public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
                    if raw!=embedded: errors.append('signature key does not match trusted public key')
                    else: sig_status='verified-trusted-key'
        except Exception as exc: errors.append(f'signature verification failed: {exc}')
    elif args.trusted_public_key: errors.append('trusted key supplied but witness is unsigned')
    report={'schema_version':1,'status':'pass' if not errors else 'fail','artifact':str(artifact),'artifact_sha256':sha_file(artifact),'signature_status':sig_status,'provenance_identity_proven':sig_status=='verified-trusted-key','errors':errors}
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if errors: raise SystemExit(1)

def main():
    ap=argparse.ArgumentParser(description='Create/verify exact-artifact release witnesses. Ed25519 signing is optional; identity trust requires an out-of-band trusted public key.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('create'); c.add_argument('--artifact',required=True); c.add_argument('--out',required=True); c.add_argument('--sign-key')
    v=sub.add_parser('verify'); v.add_argument('--artifact',required=True); v.add_argument('--witness',required=True); v.add_argument('--trusted-public-key')
    args=ap.parse_args(); create(args) if args.cmd=='create' else verify(args)

if __name__=='__main__': main()
