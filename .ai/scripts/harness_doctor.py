#!/usr/bin/env python3
from pathlib import Path
import argparse, json, os, shutil, subprocess
import sys
sys.dont_write_bytecode = True
from _common import root_from_script, load_json, harness_context, harness_version
from browser_capability import collect as collect_browser_capability

REQUIRED = [
    'AGENTS.md', 'ANTIGRAVITY.md', '.ai/PROJECT.md', '.ai/STATE.json', '.ai/COMMANDS.json', '.ai/QUALITY.json',
    '.ai/AI_PROVIDER_POLICY.json', '.ai/TASK_TEMPLATE.json', '.ai/SURFACE_OWNERSHIP.json', '.ai/INSTALL_POLICY.json', '.ai/LEARNING_POLICY.json', '.ai/RUNTIME_BUDGET.json', '.ai/EXECUTION_POLICY.json', '.ai/SKILL_EVAL_POLICY.json', '.ai/HARNESS_MANIFEST.json', '.ai/RESUME.md',
    '.ai/scripts/record_evidence.py', '.ai/scripts/evidence_gate.py', '.ai/scripts/repo_mapping.py', '.ai/scripts/execution_profile.py', '.ai/scripts/verified_checkpoint.py', '.ai/scripts/skill_eval.py', '.ai/scripts/export_agent_plugin.py',
    '.ai/scripts/verify_installation.py', '.ai/scripts/install_plan.py', '.ai/scripts/browser_smoke.mjs', '.ai/scripts/browser_flow.mjs', '.ai/scripts/harness_security.py', '.ai/scripts/surface_drift.py', '.ai/scripts/lesson_candidate.py', '.ai/scripts/loop_guard.py', '.ai/scripts/harness_ownership.py', '.agents/skills/runtime-verification/SKILL.md',
    '.agents/skills/ai-provider-routing/SKILL.md'
]

def main():
    ap = argparse.ArgumentParser(description='Inspect whether the harness and project expose enough real mechanisms for reliable agent work.')
    ap.add_argument('--strict', action='store_true')
    args = ap.parse_args()
    root = root_from_script()
    problems=[]; warnings=[]
    for rel in REQUIRED:
        if not (root/rel).exists():
            problems.append(f'missing required harness path: {rel}')
    try:
        commands=load_json(root/'.ai/COMMANDS.json')
        quality=load_json(root/'.ai/QUALITY.json')
        policy=load_json(root/'.ai/AI_PROVIDER_POLICY.json')
    except Exception as e:
        problems.append(f'control-plane JSON invalid: {e}')
        commands={'commands':{}, 'runtime':{}}; quality={}; policy={}
    configured=[k for k,v in commands.get('commands',{}).items() if v]
    if not configured:
        warnings.append('no real project commands configured yet; run bootstrap_project.py --write and inspect the result')
    missing_agents = [rel for rel in REQUIRED if rel.startswith('.agents/') and not (root/rel).exists()]
    if missing_agents:
        warnings.append('partial Harness install detected: .agents paths are missing. Re-run the collision-safe installer from a trusted release; do not repair by copying the ZIP into the project root.')
    if harness_context(root) != 'source' and not (root/'.ai/HARNESS_INSTALL_STATE.json').exists():
        warnings.append('Harness schema-v2 ownership state is missing; use the v5.4.3+ plan/apply installer rather than direct overlay/adopt')
    if harness_context(root) != 'source':
        from install_preflight import collect as collect_preflight
        try:
            audit=collect_preflight(root,root)
            warnings.extend(audit['warnings'])
            if audit['legacy_surfaces']:
                warnings.append('Legacy or project text remains outside managed blocks: review install_preflight.py --target .; unknown text is preserved, never auto-deleted.')
        except (OSError, ValueError, KeyError) as exc:
            warnings.append(f'install preflight incomplete: {exc}')
    pkg=root/'package.json'
    if pkg.exists():
        try:
            data=json.loads(pkg.read_text(encoding='utf-8'))
            deps={**data.get('dependencies',{}), **data.get('devDependencies',{})}
            if '@google/generative-ai' in deps:
                problems.append('legacy @google/generative-ai detected; migrate AI work to current @google/genai')
            if '@google/genai' in deps:
                print('[OK] current @google/genai detected')
            browser_info=collect_browser_capability(root)
            print('browser capability: '+json.dumps(browser_info,ensure_ascii=False))
            if not browser_info.get('project_local_playwright',{}).get('available'):
                warnings.append('project-local reproducible Playwright dependency not detected; host/connected/transient capability is reported separately and must not be conflated with project reproducibility')
            if browser_info.get('connected_browser',{}).get('declared_env_only') and not browser_info.get('connected_browser',{}).get('available'):
                warnings.append('HARNESS_HOST_BROWSER is only a declaration; no valid host-attested connected-browser receipt was found')
        except Exception as e:
            warnings.append(f'could not parse package.json: {e}')
    print(f'Codex Product Harness {harness_version(root) or "unknown"} Doctor')
    print('--------------------------------')
    print(f'context: {harness_context(root)}')
    print(f'root: {root}')
    print(f'configured commands: {", ".join(configured) if configured else "none"}')
    repo_map=root/'.ai/REPO_MAP.json'
    if repo_map.exists():
        try:
            mapping=json.loads(repo_map.read_text(encoding='utf-8'))
            counts={}
            for item in mapping.get('entries',[]): counts[item.get('trust','unknown')]=counts.get(item.get('trust','unknown'),0)+1
            print('repo map trust: '+', '.join(f'{k}={v}' for k,v in sorted(counts.items())))
        except Exception as e:
            warnings.append(f'could not parse .ai/REPO_MAP.json: {e}')
    else:
        warnings.append('no .ai/REPO_MAP.json yet; run bootstrap_project.py --write before trusting inferred project commands')
    for w in warnings: print(f'[WARN] {w}')
    for p in problems: print(f'[FAIL] {p}')
    if not problems: print('[OK] harness control plane is structurally present')
    if args.strict and (problems or warnings): raise SystemExit(1)
    if problems: raise SystemExit(1)

if __name__=='__main__': main()
