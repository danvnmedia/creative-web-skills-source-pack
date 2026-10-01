#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

ROOT=Path(__file__).resolve().parents[2]
EXCLUDE_DIRS={'.git','node_modules','.next','dist','build','coverage','.turbo','.cache','__pycache__'}
EXCLUDE_EXACT={'.ai/HARNESS_MANIFEST.json','.ai/HARNESS_INSTALL_STATE.json','.ai/REPO_MAP.json','SBOM.spdx.json'}
EXCLUDE_SUFFIXES={'.pyc','.pyo','.tmp','.bak','.orig','.zip'}


def include(p:Path)->bool:
    rel=p.relative_to(ROOT); posix=rel.as_posix()
    if any(part in EXCLUDE_DIRS for part in rel.parts): return False
    if posix in EXCLUDE_EXACT or posix.startswith('.ai/evidence/') or posix.startswith('.ai/checkpoints/') or posix.startswith('.ai/lessons/candidates/') or posix.startswith('.ai/lessons/curated/'): return False
    return p.is_file() and p.suffix.lower() not in EXCLUDE_SUFFIXES

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def spdx_id(rel:str): return 'SPDXRef-File-'+hashlib.sha256(rel.encode()).hexdigest()[:20]

def main():
    if (ROOT/'.ai/HARNESS_INSTALL_STATE.json').exists() or not (ROOT/'.ai/SOURCE_DISTRIBUTION.json').is_file():
        raise SystemExit('SBOM: REFUSED - source-distribution boundary is not proven')
    version=(ROOT/'VERSION').read_text(encoding='utf-8').strip(); files=[]
    for p in sorted(ROOT.rglob('*')):
        if include(p):
            rel=p.relative_to(ROOT).as_posix(); files.append({'fileName':'./'+rel,'SPDXID':spdx_id(rel),'checksums':[{'algorithm':'SHA256','checksumValue':sha(p)}]})
    namespace=f'https://codex-product-harness.local/spdx/{version}/{hashlib.sha256((version+str(len(files))).encode()).hexdigest()[:16]}'
    doc={'spdxVersion':'SPDX-2.3','dataLicense':'CC0-1.0','SPDXID':'SPDXRef-DOCUMENT','name':f'Codex Product Harness {version}','documentNamespace':namespace,'creationInfo':{'created':dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),'creators':['Tool: Codex Product Harness build_sbom.py']},'packages':[{'name':'codex-product-harness','SPDXID':'SPDXRef-Package','versionInfo':version,'downloadLocation':'NOASSERTION','filesAnalyzed':True,'licenseConcluded':'NOASSERTION','licenseDeclared':'NOASSERTION','copyrightText':'NOASSERTION'}],'files':files,'relationships':[{'spdxElementId':'SPDXRef-Package','relationshipType':'CONTAINS','relatedSpdxElement':f['SPDXID']} for f in files]}
    (ROOT/'SBOM.spdx.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'SBOM: SPDX-2.3 - {len(files)} source files -> SBOM.spdx.json')

if __name__=='__main__': main()
