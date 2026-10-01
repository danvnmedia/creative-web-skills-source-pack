#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, dump_json, root_from_script

AGENT_SURFACES = [
    'AGENTS.md','CLAUDE.md','GEMINI.md','ANTIGRAVITY.md','.agents','.claude','.codex','.gemini','.cursor','.opencode'
]
CI_GLOBS = ['.github/workflows/*.yml','.github/workflows/*.yaml']
TEST_CONFIGS = [
    'playwright.config.ts','playwright.config.js','vitest.config.ts','vitest.config.js','jest.config.js','jest.config.ts',
    'pytest.ini','tox.ini','phpunit.xml','cypress.config.ts','cypress.config.js'
]
LOCKFILES = {
    'package-lock.json':'npm','pnpm-lock.yaml':'pnpm','yarn.lock':'yarn','bun.lockb':'bun','bun.lock':'bun',
    'uv.lock':'uv','poetry.lock':'poetry','Pipfile.lock':'pipenv'
}


def add(entries: list[dict], *, kind: str, name: str, value, trust: str, source: str, execution_enabled: bool | None = None) -> None:
    item={'kind':kind,'name':name,'value':value,'trust':trust,'source':source}
    if execution_enabled is not None:
        item['execution_enabled']=execution_enabled
    entries.append(item)


def collect(root: Path) -> dict:
    entries: list[dict] = []
    pkg = root/'package.json'
    framework = None
    package_manager = None
    for lock,manager in LOCKFILES.items():
        if (root/lock).is_file():
            package_manager=manager
            add(entries,kind='package-manager',name='package-manager',value=manager,trust='observed',source=lock)
            break
    if pkg.is_file():
        try:
            data=json.loads(pkg.read_text(encoding='utf-8'))
            scripts=data.get('scripts') or {}
            deps={**(data.get('dependencies') or {}), **(data.get('devDependencies') or {})}
            runner = {'pnpm':'pnpm run','yarn':'yarn','bun':'bun run','npm':'npm run'}.get(package_manager or 'npm','npm run')
            for name in sorted(scripts):
                add(entries,kind='command',name=name,value=f'{runner} {name}',trust='observed',source=f'package.json#scripts.{name}',execution_enabled=True)
            if 'next' in deps: framework='nextjs'
            elif 'vite' in deps: framework='vite'
            elif 'react' in deps: framework='react'
            if framework:
                add(entries,kind='framework',name='frontend',value=framework,trust='observed',source='package.json dependencies')
            for sdk in ('@google/genai','@google/generative-ai','playwright','@playwright/test'):
                if sdk in deps:
                    add(entries,kind='dependency',name=sdk,value=deps[sdk],trust='observed',source='package.json dependencies')
        except Exception as exc:
            add(entries,kind='warning',name='package-json-parse',value=str(exc),trust='observed',source='package.json')
    if (root/'pyproject.toml').is_file():
        add(entries,kind='project',name='python',value='pyproject.toml',trust='observed',source='pyproject.toml')
    if (root/'requirements.txt').is_file():
        add(entries,kind='project',name='python-requirements',value='requirements.txt',trust='observed',source='requirements.txt')
    for rel in AGENT_SURFACES:
        p=root/rel
        if p.exists():
            add(entries,kind='agent-surface',name=rel,value='present',trust='observed',source=rel)
    for pattern in CI_GLOBS:
        for p in sorted(root.glob(pattern)):
            add(entries,kind='ci',name=p.name,value=p.relative_to(root).as_posix(),trust='observed',source=p.relative_to(root).as_posix())
    for rel in TEST_CONFIGS:
        if (root/rel).is_file():
            add(entries,kind='test-config',name=rel,value='present',trust='observed',source=rel)
    for rel in ('Dockerfile','docker-compose.yml','docker-compose.yaml','compose.yml','compose.yaml'):
        if (root/rel).is_file():
            add(entries,kind='runtime-config',name=rel,value='present',trust='observed',source=rel)
    # Framework-default URLs are useful hints, but remain inferred until the runtime is actually observed.
    if framework == 'nextjs':
        add(entries,kind='runtime-hint',name='start_url',value='http://localhost:3000',trust='inferred',source='Next.js conventional default',execution_enabled=False)
    elif framework == 'vite':
        add(entries,kind='runtime-hint',name='start_url',value='http://localhost:5173',trust='inferred',source='Vite conventional default',execution_enabled=False)
    if (root/'pyproject.toml').is_file() or (root/'requirements.txt').is_file():
        add(entries,kind='command-hint',name='test',value='python -m pytest',trust='inferred',source='Python project heuristic',execution_enabled=False)
    return {
        'schema_version':1,
        'generated_at':datetime.now(timezone.utc).isoformat(),
        'root':str(root),
        'framework':framework,
        'package_manager':package_manager,
        'entries':entries,
        'policy':{
            'observed':'Directly read from a repository file/path. May still need runtime verification.',
            'declared':'Explicit human/project declaration not independently observed yet.',
            'inferred':'Heuristic or convention. Never execute solely because it appears here.'
        }
    }


def main() -> None:
    configure_utf8_stdio()
    ap=argparse.ArgumentParser(description='Build a deterministic repo map with observed/declared/inferred trust labels without executing repository code.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='.ai/REPO_MAP.json')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    report=collect(root)
    out=Path(args.out)
    if not out.is_absolute(): out=root/out
    dump_json(out,report)
    counts={k:0 for k in ('observed','declared','inferred')}
    for item in report['entries']:
        if item.get('trust') in counts: counts[item['trust']]+=1
    print(json.dumps({'status':'pass','out':str(out),'entries':len(report['entries']),'trust_counts':counts},indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
