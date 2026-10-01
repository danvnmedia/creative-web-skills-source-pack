#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import sys
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, git_info, root_from_script, run_capture, git_status_entries

RESIDUE_NAMES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
RESIDUE_SUFFIXES = {'.pyc', '.pyo', '.tmp', '.bak', '.orig'}
SKIP_DIRS = {'.git', 'node_modules', '.next', 'dist', 'build', 'coverage', '.turbo', '.cache'}


def normalized_status_path(line: str) -> str:
    return line[3:].strip().strip('"').replace('\\', '/')


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description='Audit dirty worktree state, secret-like untracked files, and packaged build residue without deleting anything.')
    parser.add_argument('--strict', action='store_true', help='Exit non-zero when source dirt, sensitive untracked files, or residue exists.')
    parser.add_argument('--allow-evidence', action='store_true', help='Ignore .ai/evidence changes while preparing a closure commit.')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    root = root_from_script()
    report = {
        'git': git_info(root),
        'source_changes': [],
        'evidence_changes': [],
        'runtime_state_changes': [],
        'sensitive_untracked': [],
        'residue': [],
    }
    if report['git'].get('is_git'):
        try: entries=git_status_entries(root)
        except (RuntimeError, ValueError) as exc:
            raise SystemExit(f'WORKSPACE HYGIENE: FAIL - {exc}')
        for status, rel in entries:
            if rel.startswith('.ai/evidence/'):
                report['evidence_changes'].append(rel)
            elif rel.startswith('.ai/checkpoints/') or rel == '.ai/REPO_MAP.json':
                report['runtime_state_changes'].append(rel)
            else:
                report['source_changes'].append(rel)
            if status == '??' and re.search(r'(^|/|\\)\.env(?:\.|$)', rel) and not rel.endswith(('.example', '.sample', '.template')):
                report['sensitive_untracked'].append(rel)
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel_path.parts):
            continue
        rel = rel_path.as_posix()
        if '__pycache__' in rel_path.parts or path.name in RESIDUE_NAMES or path.suffix.lower() in RESIDUE_SUFFIXES:
            report['residue'].append(rel)
    report['source_changes'] = sorted(set(report['source_changes']))
    report['evidence_changes'] = sorted(set(report['evidence_changes']))
    report['runtime_state_changes'] = sorted(set(report['runtime_state_changes']))
    report['sensitive_untracked'] = sorted(set(report['sensitive_untracked']))
    report['residue'] = sorted(set(report['residue']))
    blocking_source = report['source_changes']
    blocking_evidence = [] if args.allow_evidence else report['evidence_changes']
    report['pass'] = not (blocking_source or blocking_evidence or report['sensitive_untracked'] or report['residue'])
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f'WORKSPACE HYGIENE: {"PASS" if report["pass"] else "FAIL"}')
        for key in ('source_changes', 'evidence_changes', 'runtime_state_changes', 'sensitive_untracked', 'residue'):
            values = report[key]
            if values:
                print(f'- {key}:')
                for value in values:
                    print(f'  - {value}')
    if args.strict and not report['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
