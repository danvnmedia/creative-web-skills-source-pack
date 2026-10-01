#!/usr/bin/env python3
"""Bounded, read-only upgrade diagnostics. Suggestions never execute project commands."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
sys.dont_write_bytecode = True

MAX_FILES = 512
MAX_FILE_BYTES = 512_000
MAX_TOTAL_BYTES = 4_000_000
MAX_ENTRIES = 4096
MAX_FINDINGS = 2048
ROOT_FILES = ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'ANTIGRAVITY.md', 'package.json',
              'Makefile', 'makefile', 'GNUmakefile', 'README.md', '.gitignore', '.gitattributes')
STATE = '.ai/HARNESS_INSTALL_STATE.json'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(['git', '-C', str(root), *args], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=8)
        return p.returncode, p.stdout.decode('utf-8', errors='surrogateescape')
    except (OSError, subprocess.TimeoutExpired):
        return -1, ''


def git_state(root: Path) -> dict:
    rc, out = git(root, 'rev-parse', '--is-inside-work-tree')
    if rc != 0 or out.strip() != 'true':
        return {'status': 'not_git_or_unavailable', 'tracked': None, 'ignored': None}
    trc, tracked = git(root, 'ls-files', '-z', '--', STATE)
    irc, ignored = git(root, 'check-ignore', '-q', '--no-index', '--', STATE)
    is_tracked = STATE in tracked.split('\0') if trc == 0 else None
    is_ignored = (irc == 0) if irc in (0, 1) else None
    status = 'complete' if trc == 0 and irc in (0, 1) else 'partial'
    return {'status': status, 'tracked': is_tracked, 'ignored': is_ignored,
            'path': STATE, 'exists': (root / STATE).is_file(),
            'fresh_checkout_missing_state': is_tracked is False}


def collect(source: Path, target: Path) -> dict:
    """Only relevant text surfaces, never .env, node_modules, symlink targets or network."""
    source, target = source.resolve(), target.resolve()
    policy = json.loads((source / '.ai/COMMAND_COMPATIBILITY.json').read_text(encoding='utf-8'))
    known = json.loads((source / '.ai/KNOWN_LEGACY_SURFACE_HASHES.json').read_text(encoding='utf-8'))
    candidates = {target / rel for rel in ROOT_FILES if (target / rel).exists() or (target / rel).is_symlink()}
    limits = []; walked_entries = 0
    for prefix in ('.github', 'docs'):
        base = target / prefix
        if base.is_symlink():
            limits.append({'path': prefix, 'reason': 'symlink_not_followed'}); continue
        if not base.is_dir(): continue
        stop = False
        for folder, dirs, names in os.walk(base, followlinks=False):
            dirs.sort(); names.sort()
            walked_entries += 1 + len(dirs) + len(names)
            if walked_entries > MAX_ENTRIES:
                limits.append({'path': prefix, 'reason': 'directory_entry_budget'}); break
            for d in list(dirs):
                path = Path(folder) / d
                if d in {'.git', 'node_modules', '__pycache__'}:
                    dirs.remove(d); continue
                if path.is_symlink():
                    dirs.remove(d); limits.append({'path': path.relative_to(target).as_posix(), 'reason': 'symlink_not_followed'})
            for name in names:
                path = Path(folder) / name
                if path.suffix.lower() in {'.md', '.txt', '.yml', '.yaml', '.json', '.sh', '.ps1', '.cmd', '.bat'}:
                    candidates.add(path)
                if len(candidates) > MAX_FILES:
                    limits.append({'path': prefix, 'reason': 'file_budget'}); stop = True; break
            if stop: break
    observed = {}; findings = []; legacy = []; total = 0
    patterns = [(x, re.compile(r'(?<![\w.-])' + re.escape(x['script']) + r'(?![\w.-])')) for x in policy['rules']]
    for path in sorted(candidates, key=lambda p: p.as_posix())[:MAX_FILES]:
        rel = path.relative_to(target).as_posix()
        if path.is_symlink() or not path.is_file():
            limits.append({'path': rel, 'reason': 'non_regular_not_read'}); continue
        if path.stat().st_size > MAX_FILE_BYTES or total + path.stat().st_size > MAX_TOTAL_BYTES:
            limits.append({'path': rel, 'reason': 'byte_budget'}); continue
        with path.open('rb') as fh: raw = fh.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES or total + len(raw) > MAX_TOTAL_BYTES:
            limits.append({'path': rel, 'reason': 'byte_budget'}); continue
        total += len(raw); observed[rel] = sha(raw)
        try: text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            limits.append({'path': rel, 'reason': 'non_utf8_not_parsed'}); continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for rule, regex in patterns:
                if regex.search(line):
                    if len(findings) >= MAX_FINDINGS:
                        if not any(x['reason'] == 'finding_budget' for x in limits):
                            limits.append({'path': rel, 'reason': 'finding_budget'})
                        continue
                    if rule['kind'] == 'context_sensitive' and '--context source' not in line:
                        # self_test is supported; never label its mere presence an error.
                        kind = 'supported_context_review'
                    else: kind = rule['kind']
                    findings.append({'path': rel, 'line': line_no, 'script': rule['script'],
                                     'kind': kind, 'severity': 'advisory', 'replacement': rule['installed_alternative'],
                                     'reason': rule['reason']})
        # Identify old outside-block prose, without promoting hashes into delete authority.
        if rel in {x['path'] for x in known['entries']}:
            from install_plan import find_block
            marker = {'AGENTS.md':'agents','CLAUDE.md':'claude','GEMINI.md':'gemini',
                      'ANTIGRAVITY.md':'antigravity','docs/AI_INTEGRATION_TESTING.md':'doc-ai-integration-testing',
                      'docs/GEMINI_FREE_FIRST.md':'doc-gemini-free-first','docs/RUNTIME_VERIFICATION.md':'doc-runtime-verification'}[rel]
            try: found = find_block(raw, marker)
            except ValueError: found = None
            outside = raw[:found[0]] + raw[found[1]:] if found else raw
            if outside.strip():
                normalized = sha(outside.rstrip(b'\r\n'))
                matches = [x['version'] for x in known['entries'] if x['path'] == rel and
                           x['trailing_eol_insensitive_sha256'] == normalized]
                legacy.append({'path': rel, 'outside_sha256': sha(outside), 'known_versions': matches,
                               'action': 'review_archive_candidate' if matches else 'preserve_unknown_project_text',
                               'automatic_delete_authorized': False})
    state = git_state(target)
    warnings = []
    if state.get('fresh_checkout_missing_state'):
        warnings.append('CI_INSTALL_STATE_NOT_TRACKED: fresh checkout lacks .ai/HARNESS_INSTALL_STATE.json; review and commit the ownership state, not checkpoints/logs.')
    if state.get('ignored'):
        warnings.append('CI_INSTALL_STATE_IGNORED: adjust the project ignore rule for .ai/HARNESS_INSTALL_STATE.json; no global config change is performed.')
    if limits: warnings.append('REFERENCE_SCAN_PARTIAL: coverage limits remain; no clean-scan claim.')
    if any(x['kind'] != 'supported_context_review' for x in findings):
        warnings.append('COMMAND_CONTEXT_REVIEW: inspect CI/build references before applying; external source paths may be intentional. No project command is executed or rewritten.')
    return {'schema_version': 1, 'status': 'partial' if limits or state.get('status') == 'partial' else 'complete',
            'observed_file_sha256': observed, 'files_read': len(observed), 'bytes_read': total,
            'references': findings, 'legacy_surfaces': legacy, 'git_state': state,
            'limits': limits, 'warnings': warnings, 'mutated': False}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--target', required=True); ap.add_argument('--source', default=str(Path(__file__).resolve().parents[2]))
    args = ap.parse_args()
    try: report = collect(Path(args.source), Path(args.target))
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'status':'failed', 'reason':str(exc), 'mutated':False})); raise SystemExit(2)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if report['status'] != 'complete': raise SystemExit(2)

if __name__ == '__main__': main()
