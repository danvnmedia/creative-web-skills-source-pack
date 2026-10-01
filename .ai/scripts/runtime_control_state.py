#!/usr/bin/env python3
"""Validate excluded runtime control state WITHOUT adding it to source digests."""
from __future__ import annotations
import json,sqlite3,sys
from pathlib import Path
sys.dont_write_bytecode=True
from _truth import no_redirect_ancestors,read_json


def validate(root:Path):
    errors=[]; inspected=[]
    path=root/'.ai/REPO_MAP.json'
    if path.exists() or path.is_symlink():
        try:
            no_redirect_ancestors(path); doc=read_json(path)
            if not isinstance(doc,dict) or doc.get('schema_version')!=1 or not isinstance(doc.get('entries'),list):
                raise ValueError('unsupported repo-map schema')
            if len(doc['entries'])>10000: raise ValueError('repo-map entry budget')
            for entry in doc['entries']:
                if not isinstance(entry,dict) or entry.get('trust') not in {'observed','declared','inferred'}:
                    raise ValueError('missing or unknown trust label')
                if entry.get('trust')=='inferred' and entry.get('execution_enabled') is not False:
                    raise ValueError('inferred commands/hints require execution_enabled=false')
                if 'execution_enabled' in entry and type(entry['execution_enabled']) is not bool:
                    raise ValueError('execution_enabled must be boolean')
            inspected.append('repo-map')
        except (OSError,ValueError,KeyError,TypeError) as exc: errors.append('REPO_MAP: '+str(exc))
    ledger=root/'.ai/checkpoints/operator-events.sqlite3'
    if ledger.exists() or ledger.is_symlink():
        try:
            from operator_events import status
            no_redirect_ancestors(ledger); status(ledger); inspected.append('operator-events')
        except (OSError,ValueError,sqlite3.Error,KeyError,TypeError) as exc: errors.append('operator-events: '+str(exc))
    from prompt_brief import validate_store
    errors.extend(validate_store(root))
    if (root/'.ai/checkpoints/briefs').exists(): inspected.append('execution-briefs')
    return {'status':'fail' if errors else 'pass','inspected':inspected,'errors':errors,
            'absent_optional_state_created':False,'runtime_state_in_source_fingerprint':False}


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--root',default=str(Path(__file__).resolve().parents[2])); a=ap.parse_args()
    result=validate(Path(a.root)); print(json.dumps(result,indent=2)); raise SystemExit(bool(result['errors']))
if __name__=='__main__': main()
