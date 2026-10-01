#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, dump_json, load_json, root_from_script


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', value).strip('._') or 'server'


def load_surface(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(raw, list):
        tools = raw
        server_identity = None
    elif isinstance(raw, dict):
        tools = raw.get('tools', [])
        server_identity = raw.get('server_identity') or raw.get('server')
    else:
        raise ValueError('surface JSON must be a list of tools or an object containing tools')
    if not isinstance(tools, list):
        raise ValueError('surface tools must be a list')
    normalized = []
    seen = set()
    for item in tools:
        if not isinstance(item, dict) or not str(item.get('name') or '').strip():
            raise ValueError('every tool must be an object with a non-empty name')
        name = str(item['name']).strip()
        if name in seen:
            raise ValueError(f'duplicate tool name: {name}')
        seen.add(name)
        schema = item.get('inputSchema', item.get('input_schema', {}))
        normalized.append({
            'name': name,
            'description': str(item.get('description') or ''),
            'input_schema': schema if isinstance(schema, (dict, list)) else {},
            'capability_class': str(item.get('capability_class') or item.get('capabilityClass') or 'unspecified'),
        })
    normalized.sort(key=lambda x: x['name'])
    return {'server_identity': server_identity, 'tools': normalized}


def tool_lock(surface: dict) -> list[dict]:
    result = []
    for tool in surface['tools']:
        result.append({
            'name': tool['name'],
            'description_sha256': digest(tool['description']),
            'input_schema_sha256': digest(tool['input_schema']),
            'capability_class': tool['capability_class'],
            'tool_sha256': digest(tool),
        })
    return result


def compare(pin: dict, current: dict, explicit_identity: str | None) -> list[dict]:
    changes = []
    pinned_identity = pin.get('server_identity')
    current_identity = explicit_identity or current.get('server_identity')
    if pinned_identity != current_identity:
        changes.append({'type': 'server_identity_changed', 'before': pinned_identity, 'after': current_identity})
    old = {x['name']: x for x in pin.get('tools', [])}
    new_lock = {x['name']: x for x in tool_lock(current)}
    for name in sorted(set(new_lock) - set(old)):
        changes.append({'type': 'tool_added', 'tool': name})
    for name in sorted(set(old) - set(new_lock)):
        changes.append({'type': 'tool_removed', 'tool': name})
    for name in sorted(set(old) & set(new_lock)):
        a, b = old[name], new_lock[name]
        if a.get('description_sha256') != b.get('description_sha256'):
            changes.append({'type': 'description_changed', 'tool': name})
        if a.get('input_schema_sha256') != b.get('input_schema_sha256'):
            changes.append({'type': 'input_schema_changed', 'tool': name})
        if a.get('capability_class') != b.get('capability_class'):
            changes.append({'type': 'capability_class_changed', 'tool': name, 'before': a.get('capability_class'), 'after': b.get('capability_class')})
    return changes


def nested_items(value, prefix=''):
    if isinstance(value, dict):
        for k, v in value.items():
            path = f'{prefix}.{k}' if prefix else str(k)
            yield path, str(k), v
            yield from nested_items(v, path)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from nested_items(v, f'{prefix}[{i}]')


def main() -> None:
    configure_utf8_stdio()
    ap = argparse.ArgumentParser(description='Pin and verify an MCP tool surface without executing the MCP server.')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('pin')
    p.add_argument('--server', required=True)
    p.add_argument('--surface', required=True)
    p.add_argument('--server-identity')
    p.add_argument('--out')
    v = sub.add_parser('verify')
    v.add_argument('--server', required=True)
    v.add_argument('--surface', required=True)
    v.add_argument('--server-identity')
    v.add_argument('--pin')
    g = sub.add_parser('guard-call')
    g.add_argument('--server', required=True)
    g.add_argument('--tool', required=True)
    g.add_argument('--arguments', required=True, help='JSON file containing tool arguments.')
    g.add_argument('--pin')
    g.add_argument('--allow-sensitive-key', action='append', default=[])
    args = ap.parse_args()
    root = root_from_script()
    policy = load_json(root/'.ai/MCP_POLICY.json')
    default_pin = root/str(policy.get('runtime_pin_root', '.ai/checkpoints/mcp'))/f'{safe_name(args.server)}.json'
    pin_path = Path(getattr(args, 'pin', None) or default_pin)
    if not pin_path.is_absolute():
        pin_path = root/pin_path

    if args.cmd == 'pin':
        surface = load_surface(Path(args.surface))
        identity = args.server_identity or surface.get('server_identity')
        if not identity:
            raise SystemExit('MCP SURFACE PIN: FAIL - server identity is required from --server-identity or surface JSON')
        doc = {
            'schema_version': 1,
            'server': args.server,
            'server_identity': identity,
            'surface_sha256': digest({'server_identity': identity, 'tools': surface['tools']}),
            'tools': tool_lock(surface),
            'tool_count': len(surface['tools']),
            'source': 'trusted-host-enumeration-json',
            'mcp_server_executed_by_harness': False,
        }
        out = Path(args.out).resolve() if args.out else default_pin
        dump_json(out, doc)
        print(json.dumps({'status': 'pass', 'pin': str(out), 'server': args.server, 'tool_count': doc['tool_count'], 'surface_sha256': doc['surface_sha256']}, indent=2))
        return

    if not pin_path.is_file():
        raise SystemExit(f'MCP SURFACE PIN: FAIL - missing pin {pin_path}')
    pin = load_json(pin_path)
    if pin.get('server') != args.server:
        raise SystemExit('MCP SURFACE PIN: FAIL - pin server mismatch')

    if args.cmd == 'verify':
        current = load_surface(Path(args.surface))
        changes = compare(pin, current, args.server_identity)
        report = {'schema_version': 1, 'status': 'pass' if not changes else 'review_required', 'server': args.server, 'pin': str(pin_path), 'changes': changes, 'mcp_server_executed_by_harness': False}
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if changes:
            raise SystemExit(2)
        return

    arguments = json.loads(Path(args.arguments).read_text(encoding='utf-8'))
    tools = {x.get('name') for x in pin.get('tools', [])}
    errors = []
    if policy.get('call_guard', {}).get('require_pinned_tool', True) and args.tool not in tools:
        errors.append('tool is not present in the approved pin')
    allowed_sensitive = {x.lower() for x in args.allow_sensitive_key}
    patterns = [re.compile(x, re.I) for x in policy.get('call_guard', {}).get('sensitive_argument_key_patterns', [])]
    path_key = re.compile(r'(^|_)(path|file|filepath|directory|cwd)(_|$)', re.I)
    project_only = bool(policy.get('call_guard', {}).get('project_relative_paths_only', True))
    root_resolved = root.resolve()
    for location, key, value in nested_items(arguments):
        if key.lower() not in allowed_sensitive and any(p.search(key) for p in patterns):
            errors.append(f'sensitive argument key requires explicit allow: {location}')
        if project_only and path_key.search(key) and isinstance(value, str) and value:
            candidate = Path(os.path.expandvars(os.path.expanduser(value)))
            if candidate.is_absolute():
                try:
                    candidate.resolve().relative_to(root_resolved)
                except Exception:
                    errors.append(f'absolute path escapes project root: {location}')
    report = {'schema_version': 1, 'status': 'pass' if not errors else 'block', 'server': args.server, 'tool': args.tool, 'errors': errors, 'mcp_server_executed_by_harness': False}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
