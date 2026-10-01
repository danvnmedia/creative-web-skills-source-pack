#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, dump_json, load_json, root_from_script
from repo_mapping import collect

SEMANTIC_SCRIPTS = {
    'dev':['dev'], 'build':['build'], 'lint':['lint'],
    'typecheck':['typecheck','type-check','check:types'],
    'test':['test'], 'test_unit':['test:unit','unit'],
    'test_integration':['test:integration','integration'],
    'test_e2e':['test:e2e','e2e','playwright']
}


def detect(root: Path) -> dict:
    repo_map=collect(root)
    observed_commands={item['name']:item['value'] for item in repo_map['entries'] if item.get('kind')=='command' and item.get('trust')=='observed' and item.get('execution_enabled') is True}
    commands={}
    for semantic,names in SEMANTIC_SCRIPTS.items():
        for name in names:
            if name in observed_commands:
                commands[semantic]=observed_commands[name]; break
    # Install commands are conventions rather than repository scripts; keep them as hints only.
    inferred=[item for item in repo_map['entries'] if item.get('trust')=='inferred']
    return {
        'detected_framework':repo_map.get('framework'),
        'package_manager':repo_map.get('package_manager'),
        'commands':commands,
        'runtime':{},
        'repo_map':repo_map,
        'inferred_hints':inferred,
    }


def main() -> None:
    configure_utf8_stdio()
    ap=argparse.ArgumentParser(description='Bootstrap project truth from observed repository signals. Inferred commands/URLs are reported but not silently enabled.')
    ap.add_argument('--write',action='store_true',help='Write observed commands and .ai/REPO_MAP.json.')
    args=ap.parse_args(); root=root_from_script(); found=detect(root)
    print(json.dumps({k:v for k,v in found.items() if k!='repo_map'},indent=2,ensure_ascii=False))
    if not args.write: return
    map_path=root/'.ai/REPO_MAP.json'; dump_json(map_path,found['repo_map'])
    commands_path=root/'.ai/COMMANDS.json'; cfg=load_json(commands_path)
    if found.get('detected_framework'):
        cfg['detected_framework']=found['detected_framework']
    for key,value in found.get('commands',{}).items():
        if value and not cfg.get('commands',{}).get(key):
            cfg['commands'][key]=value
    notes=str(cfg.get('notes') or '')
    truth_note=' v5.3: only observed repository scripts are auto-enabled; inferred command/runtime hints stay in .ai/REPO_MAP.json until confirmed.'
    if truth_note.strip() not in notes:
        cfg['notes']=(notes+truth_note).strip()
    dump_json(commands_path,cfg)
    print(f'updated {commands_path}')
    print(f'updated {map_path}')


if __name__=='__main__':
    main()
