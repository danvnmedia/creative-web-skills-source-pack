#!/usr/bin/env python3
"""Strict Harness export validator, NOT a generic 1.1-conformant host loader.
Stricter authoring policy rejects unknown fields and all filesystem redirects.
The optional 1.1 safety rules do not imply 1.1 host conformance.
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
from _truth import digest, inventory, portable_rel, read_json

SCHEMA = 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
FIELDS = {'$schema', 'name', 'version', 'description', 'author', 'homepage', 'repository', 'license', 'keywords', 'extensions'}


def validate(plugin: Path, expected_skills=13):
    errors = []; warnings = []; discovered = []; skipped = []
    try:
        files = inventory(plugin, exclude=('plugin-lock.json',))
        doc = read_json(plugin / 'plugin.json')
        if not isinstance(doc, dict):
            raise ValueError('manifest is not an object')
        if set(doc) - FIELDS:
            errors.append('unknown manifest fields have no semantics: ' + ','.join(sorted(set(doc) - FIELDS)))
        if doc.get('$schema') != SCHEMA:
            errors.append('unsupported schema (export remains 1.0.0)')
        name = doc.get('name', '')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?', name) or '--' in name or '..' in name:
            errors.append('invalid plugin name')
        for field in ('version', 'description', 'homepage', 'repository', 'license'):
            if field in doc and not isinstance(doc[field], str):
                errors.append('invalid manifest string: ' + field)
        if 'author' in doc and (not isinstance(doc['author'], dict) or set(doc['author']) - {'name','email','url'} or any(not isinstance(v,str) for v in doc['author'].values())):
            errors.append('invalid author')
        if 'keywords' in doc and (not isinstance(doc['keywords'],list) or any(not isinstance(v,str) for v in doc['keywords'])):
            errors.append('invalid keywords')
        extensions = doc.get('extensions', {})
        if not isinstance(extensions, dict):
            errors.append('extensions must be an object')
        else:
            for ns, value in extensions.items():
                if not re.fullmatch(r'[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+', ns) or not isinstance(value, dict):
                    errors.append('invalid extension namespace: ' + ns)
            if extensions:
                errors.append('host extensions are not emitted by this skills-only exporter')
        allowed = {'plugin.json'}
        for item in files:
            rel = item['path']
            if rel not in allowed and not rel.startswith('skills/'):
                errors.append('non-skills payload: ' + rel)
        skillroot = plugin / 'skills'
        if skillroot.is_dir():
            for child in sorted(skillroot.iterdir()):
                entry = child / 'SKILL.md'
                if not child.is_dir() or not entry.is_file():
                    continue
                text = entry.read_text(encoding='utf-8')
                head = text.split('---', 2)
                valid = len(head) == 3 and not head[0].strip() and re.search(r'^name:\s*\S', head[1], re.M) and re.search(r'^description:\s*\S', head[1], re.M)
                if valid:
                    discovered.append(child.name)
                else:
                    skipped.append(child.name)
            for path in skillroot.rglob('SKILL.md'):
                if len(path.relative_to(skillroot).parts) != 2:
                    errors.append('nested SKILL.md is not a discovery location: ' + path.relative_to(plugin).as_posix())
        if skipped:
            errors.append('invalid skills skipped: ' + ','.join(skipped))
        if expected_skills is not None and len(discovered) != expected_skills:
            errors.append(f'expected {expected_skills} valid skills; found {len(discovered)}')
        lock = read_json(plugin / 'plugin-lock.json')
        if lock.get('version') != doc.get('version') or lock.get('scope') != 'skills-only':
            errors.append('lock identity mismatch')
        # Exact inventory equality rejects added, removed, repeated and unbound paths.
        entries = lock.get('files', [])
        if not isinstance(entries, list):
            raise ValueError('invalid lock inventory')
        for item in entries:
            portable_rel(item['path'])
        if entries != files:
            errors.append('exact plugin inventory mismatch')
    except (ValueError, OSError, UnicodeError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    return {'status': 'fail' if errors else 'pass', 'scope': 'strict-skills-only-export', 'errors': errors,
            'warnings': warnings, 'discovered_skills': discovered, 'skipped_skills': skipped,
            'host_install_permission_sandbox_parity': False}


def main():
    import json
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--path', required=True)
    args = ap.parse_args(); report = validate(Path(args.path))
    print(json.dumps(report, indent=2)); raise SystemExit(bool(report['errors']))

if __name__ == '__main__':
    main()
