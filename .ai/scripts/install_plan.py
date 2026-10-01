#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from typing import Any

sys.dont_write_bytecode = True

OWNER = "codex-product-harness"
BEGIN_FMT = "<!-- CODEX_PRODUCT_HARNESS:{marker}:BEGIN -->"
END_FMT = "<!-- CODEX_PRODUCT_HARNESS:{marker}:END -->"
RUNTIME_EXACT = {'.ai/REPO_MAP.json', '.ai/HARNESS_INSTALL_STATE.json'}
RUNTIME_PREFIXES = ('.ai/checkpoints/', '.ai/evidence/', '.ai/lessons/candidates/', '.ai/lessons/curated/')


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def rel_safe(value: str) -> str:
    value = value.replace('\\', '/').lstrip('/')
    p = PurePosixPath(value)
    if not value or value.startswith('../') or '..' in p.parts or p.is_absolute():
        raise ValueError(f'unsafe relative path: {value!r}')
    return p.as_posix()


def source_marker_ok(source: Path, policy: dict) -> tuple[bool, str]:
    marker = source / policy.get('source_distribution_marker', '.ai/SOURCE_DISTRIBUTION.json')
    if not marker.is_file():
        return False, 'source distribution marker is missing'
    try:
        doc = load_json(marker)
    except Exception as exc:
        return False, f'invalid source distribution marker: {exc}'
    if doc.get('kind') != 'codex-product-harness-source-distribution':
        return False, 'source distribution marker kind mismatch'
    version = (source / 'VERSION').read_text(encoding='utf-8').strip() if (source / 'VERSION').is_file() else ''
    if doc.get('version') != version:
        return False, 'source distribution marker version mismatch'
    return True, version


def manifest_map(source: Path) -> tuple[dict, dict[str, dict]]:
    doc = load_json(source / '.ai/HARNESS_MANIFEST.json')
    return doc, {rel_safe(x['path']): x for x in doc.get('entries', [])}


def verify_source_entry(source: Path, manifest: dict[str, dict], rel: str) -> bytes:
    rel = rel_safe(rel)
    entry = manifest.get(rel)
    if not entry:
        raise ValueError(f'source path is not in HARNESS_MANIFEST: {rel}')
    path = source / rel
    if not path.is_file():
        raise ValueError(f'source payload missing: {rel}')
    data = path.read_bytes()
    if sha_bytes(data) != entry.get('sha256') or len(data) != entry.get('size'):
        raise ValueError(f'source payload/hash mismatch: {rel}')
    return data


def is_runtime_source(rel: str) -> bool:
    if rel in RUNTIME_EXACT:
        return True
    if rel == '.ai/checkpoints/README.md' or rel == '.ai/evidence/README.md':
        return False
    return any(rel.startswith(prefix) for prefix in RUNTIME_PREFIXES)


def match_prefix(rel: str, prefix: str) -> bool:
    prefix = prefix.rstrip('/') + '/'
    return rel.startswith(prefix)


def transform_surface(data: bytes) -> bytes:
    """Rewrite source-distribution doc pointers to the installed namespaced docs.

    Canonical Skill files are never transformed. Only copied adapter/reference
    surfaces under .ai/harness/surfaces use this mapping.
    """
    text = data.decode('utf-8')
    text = text.replace('docs/harness/', '.ai/harness/docs/harness/')
    text = text.replace('docs/research/', '.ai/harness/docs/research/')
    # Remaining top-level docs references (including immutable Skill companion docs).
    text = re.sub(r'(?<![\w./-])docs/([A-Za-z0-9_.-]+\.md)', r'.ai/harness/docs/\1', text)
    return text.encode('utf-8')


def marker_block(marker: str, pointer: str, label: str | None = None) -> bytes:
    title = f'{label} adapter' if label else 'compatibility reference'
    text = (
        f'{BEGIN_FMT.format(marker=marker)}\n'
        f'## Codex Product Harness — {title}\n'
        f'Read and follow `{pointer}` for Harness-owned instructions. '\
        'Content outside this managed block belongs to the project and must be preserved.\n'
        f'{END_FMT.format(marker=marker)}\n'
    )
    return text.encode('utf-8')


def find_block(data: bytes, marker: str) -> tuple[int, int, bytes] | None:
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return None
    begin = ('# CODEX_PRODUCT_HARNESS:git-attributes:BEGIN' if marker == 'git-attributes' else BEGIN_FMT.format(marker=marker))
    end = ('# CODEX_PRODUCT_HARNESS:git-attributes:END' if marker == 'git-attributes' else END_FMT.format(marker=marker))
    s = text.find(begin)
    if s < 0:
        return None
    e = text.find(end, s + len(begin))
    if e < 0:
        raise ValueError(f'managed block has BEGIN without END: {marker}')
    e += len(end)
    if text[e:e+2] == '\r\n':
        e += 2
    elif text[e:e+1] == '\n':
        e += 1
    return len(text[:s].encode('utf-8')), len(text[:e].encode('utf-8')), text[s:e].encode('utf-8')


def merge_block(container: bytes | None, marker: str, block: bytes) -> bytes:
    if container is None:
        return block
    found = find_block(container, marker)
    if found:
        s, e, _ = found
        return container[:s] + block + container[e:]
    if container and not container.endswith(b'\n'):
        container += b'\n'
    if container and not container.endswith(b'\n\n'):
        container += b'\n'
    return container + block


def strip_block(container: bytes, marker: str) -> bytes:
    found = find_block(container, marker)
    if not found:
        return container
    s, e, _ = found
    out = container[:s] + container[e:]
    # Tidy at most one separator introduced by the managed append.
    out = re.sub(br'\n{3,}', b'\n\n', out)
    return out


def _previous_records(target: Path) -> tuple[dict[str, dict], dict[str, str], int]:
    state_path = target / '.ai/HARNESS_INSTALL_STATE.json'
    if not state_path.is_file():
        return {}, {}, 0
    try:
        state = load_json(state_path)
    except Exception:
        return {}, {}, -1
    schema = int(state.get('schema_version') or 0)
    if schema >= 2:
        return state.get('records', {}) or {}, {}, schema
    if schema == 1:
        return {}, state.get('installed_hashes', {}) or {}, schema
    return {}, {}, schema




def path_has_symlink(root: Path, rel: str) -> str | None:
    """Return the first symlink component on a target path; installers never traverse it."""
    cur = root
    for part in PurePosixPath(rel).parts:
        cur = cur / part
        if cur.is_symlink():
            return cur.relative_to(root).as_posix()
    return None

def _desired_whole_action(target: Path, target_rel: str, data: bytes, source_rel: str,
                          source_hash: str, records: dict[str, dict], legacy: dict[str, str],
                          mode: str) -> dict:
    path = target / target_rel
    symlink = path_has_symlink(target, target_rel)
    exists = path.is_file()
    current_hash = sha_file(path)
    desired_hash = sha_bytes(data)
    rec = records.get(target_rel) or {}
    action = 'CREATE'
    reason = 'target missing'
    if symlink:
        action, reason = 'PROTECTED_CONFLICT', f'target path traverses symlink: {symlink}'
    elif exists and current_hash == desired_hash:
        action, reason = 'UNCHANGED', 'target already equals desired managed bytes'
    elif exists and rec and rec.get('mode') == 'whole_file' and current_hash == rec.get('last_managed_sha256'):
        action, reason = 'OWNED_UPDATE', 'current bytes match last managed baseline'
    elif exists and legacy.get(target_rel) and current_hash == legacy.get(target_rel):
        action, reason = 'OWNED_UPDATE', 'current bytes match legacy v1 installed baseline'
    elif exists:
        action, reason = 'PROTECTED_CONFLICT', 'existing bytes are not proven Harness-owned'
    return {
        'target_path': target_rel, 'source_path': source_rel, 'mode': 'whole_file',
        'install_mode': mode, 'action': action, 'reason': reason,
        'observed_exists': exists, 'observed_sha256': current_hash,
        'source_sha256': source_hash, 'desired_sha256': desired_hash,
        'desired_size': len(data),
    }




def _desired_mutable_seed_action(target: Path, target_rel: str, data: bytes, source_rel: str,
                                 source_hash: str, records: dict[str, dict], legacy: dict[str, str]) -> dict:
    """Plan a seed file that Harness installs but runtime/project workflows may legitimately change.

    Unknown pre-existing bytes remain a protected conflict. Once ownership is established,
    divergence from the last seed is preserved rather than treated as Harness tampering.
    """
    path = target / target_rel
    symlink = path_has_symlink(target, target_rel)
    exists = path.is_file()
    current_hash = sha_file(path)
    desired_hash = sha_bytes(data)
    rec = records.get(target_rel) or {}
    prior_seed = rec.get('last_seed_sha256')
    if not prior_seed and rec.get('mode') == 'whole_file':
        prior_seed = rec.get('last_managed_sha256')
    if not prior_seed and legacy.get(target_rel):
        prior_seed = legacy.get(target_rel)
    if symlink:
        action, reason = 'PROTECTED_CONFLICT', f'target path traverses symlink: {symlink}'
    elif not exists:
        action, reason = 'CREATE', 'mutable seed target missing'
    elif current_hash == desired_hash:
        action, reason = 'UNCHANGED', 'mutable seed already equals current source seed'
    elif rec and prior_seed and current_hash == prior_seed:
        action, reason = 'MUTABLE_SEED_UPDATE', 'runtime seed is still pristine and may advance safely'
    elif rec and prior_seed:
        action, reason = 'PRESERVE_MUTABLE', 'runtime/project mutation differs from seed and must be preserved'
    elif legacy.get(target_rel) and current_hash == legacy.get(target_rel):
        action, reason = 'MUTABLE_SEED_UPDATE', 'legacy baseline proves pristine mutable seed'
    else:
        action, reason = 'PROTECTED_CONFLICT', 'pre-existing mutable path is not proven Harness-seeded'
    return {
        'target_path': target_rel, 'source_path': source_rel, 'mode': 'mutable_seed',
        'install_mode': 'mutable_seed', 'action': action, 'reason': reason,
        'observed_exists': exists, 'observed_sha256': current_hash,
        'source_sha256': source_hash, 'desired_sha256': desired_hash,
        'prior_seed_sha256': prior_seed, 'desired_size': len(data),
    }

def _desired_block_action(target: Path, target_rel: str, source_rel: str, marker: str,
                          block: bytes, records: dict[str, dict], legacy: dict[str, str],
                          snapshot: str) -> dict:
    path = target / target_rel
    symlink = path_has_symlink(target, target_rel)
    exists = path.is_file()
    current = path.read_bytes() if exists else None
    current_hash = sha_bytes(current) if current is not None else None
    rec = records.get(target_rel) or {}
    try:
        found = find_block(current or b'', marker)
    except ValueError as exc:
        return {
            'target_path': target_rel, 'source_path': source_rel, 'mode': 'managed_block', 'marker_id': marker,
            'snapshot_path': snapshot, 'action': 'PROTECTED_CONFLICT', 'reason': str(exc),
            'observed_exists': exists, 'observed_sha256': current_hash, 'desired_block_sha256': sha_bytes(block),
        }
    current_block_hash = sha_bytes(found[2]) if found else None
    desired_block_hash = sha_bytes(block)
    if symlink:
        action, reason = 'PROTECTED_CONFLICT', f'target path traverses symlink: {symlink}'
    elif found and current_block_hash == desired_block_hash:
        action, reason = 'UNCHANGED', 'managed block already current'
    elif found and rec.get('mode') == 'managed_block' and current_block_hash == rec.get('last_managed_sha256'):
        action, reason = 'SAFE_MERGE', 'managed block matches last baseline; project content outside block is preserved'
    elif found:
        action, reason = 'PROTECTED_CONFLICT', 'existing managed marker was modified or is not owned by this install state'
    elif exists:
        # Legacy whole-file ownership is intentionally not used to replace the container.
        # Append the pointer block, preserving every existing project/user byte.
        action, reason = 'SAFE_MERGE', 'append managed pointer; preserve existing container byte-for-byte outside block'
    else:
        action, reason = 'SAFE_MERGE', 'create container with managed pointer block'
    return {
        'target_path': target_rel, 'source_path': source_rel, 'mode': 'managed_block', 'marker_id': marker,
        'snapshot_path': snapshot, 'action': action, 'reason': reason,
        'observed_exists': exists, 'observed_sha256': current_hash,
        'observed_block_sha256': current_block_hash, 'desired_block_sha256': desired_block_hash,
        'legacy_whole_file_baseline': legacy.get(target_rel),
    }


def build_plan(source: Path, target: Path, *, repair_eol: bool = False) -> tuple[dict, dict[str, bytes]]:
    source = source.resolve(); target = target.resolve()
    policy = load_json(source / '.ai/INSTALL_POLICY.json')
    ok, version_or_error = source_marker_ok(source, policy)
    if not ok:
        raise ValueError(version_or_error)
    version = version_or_error
    manifest_doc, manifest = manifest_map(source)
    if manifest_doc.get('harness_version') != version:
        raise ValueError('HARNESS_MANIFEST version does not match source VERSION')
    for foreign in (target/'.agents/skills/codex-product-harness/.ai',target/'.agent/skills/codex-product-harness/.ai'):
        if foreign.exists():
            raise ValueError('foreign skill-first Harness topology: staged migration required; no overlay applied')
    state_path=target/'.ai/HARNESS_INSTALL_STATE.json'
    prior_version=load_json(state_path).get('harness_version') if state_path.is_file() else None
    version_path=target/'.ai/harness/VERSION'
    if version_path.is_file(): prior_version=version_path.read_text(encoding='utf-8').strip()
    if prior_version:
        import re
        def triplet(value):
            if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',str(value)):
                raise ValueError('unrecognized installed version: explicit migration required')
            return tuple(int(x) for x in value.split('.'))
        if triplet(prior_version)>triplet(version):
            raise ValueError('newer installed Harness detected: downgrade requires a separate reviewed migration')
    records, legacy, state_schema = _previous_records(target)
    desired: dict[str, bytes] = {}
    actions: list[dict] = []
    mutable_seed_paths = {rel_safe(x) for x in policy.get('mutable_seed_paths', [])}

    block_sources = {x['source'] for x in policy.get('managed_block_surfaces', [])}
    compat_sources = {x['source'] for x in policy.get('compatibility_pointer_surfaces', [])}
    relocated_sources: set[str] = set()
    relocation_map: dict[str, str] = {}
    for item in policy.get('relocations', []):
        relocation_map[rel_safe(item['source'])] = rel_safe(item['target'])
        relocated_sources.add(rel_safe(item['source']))
    for item in policy.get('relocation_prefixes', []):
        sp = rel_safe(item['source_prefix'].rstrip('/')) + '/'
        tp = rel_safe(item['target_prefix'].rstrip('/')) + '/'
        for rel in manifest:
            if rel.startswith(sp):
                relocation_map[rel] = tp + rel[len(sp):]
                relocated_sources.add(rel)

    # 1. Relocated source-only metadata/docs/templates live under .ai/harness/**.
    for source_rel, target_rel in sorted(relocation_map.items()):
        data = verify_source_entry(source, manifest, source_rel)
        desired[target_rel] = data
        actions.append(_desired_whole_action(target, target_rel, data, source_rel, sha_bytes(data), records, legacy, 'relocated'))

    # 2. Canonical adapter snapshots are namespaced. Only these copies are transformed
    # so their doc references resolve inside the namespaced installation.
    for item in policy.get('managed_block_surfaces', []):
        source_rel = rel_safe(item['source']); snap = rel_safe(item['snapshot'])
        src = verify_source_entry(source, manifest, source_rel)
        data = transform_surface(src)
        desired[snap] = data
        actions.append(_desired_whole_action(target, snap, data, source_rel, sha_bytes(src), records, legacy, 'surface_snapshot'))
        block = marker_block(str(item['marker_id']), snap, str(item.get('label') or ''))
        desired[f'@block:{item["target"]}'] = block
        actions.append(_desired_block_action(target, rel_safe(item['target']), source_rel, str(item['marker_id']), block, records, legacy, snap))

    # 3. Immutable v5.3 Skills point at three docs paths. Preserve project docs and
    # append a tiny pointer block instead of copying Harness docs over them.
    for item in policy.get('compatibility_pointer_surfaces', []):
        source_rel = rel_safe(item['source']); snap = rel_safe(item['snapshot'])
        # snapshot already exists from relocation_prefixes; verify it is planned.
        if snap not in desired:
            data = verify_source_entry(source, manifest, source_rel)
            desired[snap] = data
            actions.append(_desired_whole_action(target, snap, data, source_rel, sha_bytes(data), records, legacy, 'relocated'))
        block = marker_block(str(item['marker_id']), snap, 'Skill reference')
        desired[f'@block:{item["target"]}'] = block
        actions.append(_desired_block_action(target, rel_safe(item['target']), source_rel, str(item['marker_id']), block, records, legacy, snap))

    # 4. The source ownership manifest is intentionally outside its own entry list,
    # but installed runtime tools still need the exact source manifest as control metadata.
    manifest_rel='.ai/HARNESS_MANIFEST.json'
    manifest_bytes=(source/manifest_rel).read_bytes()
    desired[manifest_rel]=manifest_bytes
    actions.append(_desired_whole_action(target, manifest_rel, manifest_bytes, manifest_rel, sha_bytes(manifest_bytes), records, legacy, 'control_manifest'))

    # 5. Everything else under .ai/** and .agents/** is exact managed payload,
    # except runtime state, source-only marker, and files already handled above.
    source_only = {rel_safe(x) for x in policy.get('source_only_paths', [])}
    for rel, entry in sorted(manifest.items()):
        if rel in source_only or rel in relocated_sources or rel in block_sources or rel in compat_sources:
            continue
        if is_runtime_source(rel):
            continue
        if rel.startswith('.ai/') or rel.startswith('.agents/'):
            data = verify_source_entry(source, manifest, rel)
            desired[rel] = data
            if rel in mutable_seed_paths:
                actions.append(_desired_mutable_seed_action(target, rel, data, rel, entry['sha256'], records, legacy))
            else:
                actions.append(_desired_whole_action(target, rel, data, rel, entry['sha256'], records, legacy, 'managed_exact'))

    # Exact path attributes preserve shipped bytes through clean Git checkouts.
    # No global settings, wildcard product normalization, or hashing relaxation.
    protected = sorted({x['target_path'] for x in actions if x['mode'] in ('whole_file', 'managed_block')}
                       | {'.ai/HARNESS_INSTALL_STATE.json', '.gitattributes'})
    attr_lines = ['# CODEX_PRODUCT_HARNESS:git-attributes:BEGIN',
                  '# Exact Harness-owned files and managed-block containers only. Preserve raw bytes.']
    attr_lines += [json.dumps('/' + rel, ensure_ascii=True) + ' -text -filter -ident -working-tree-encoding' for rel in protected]
    attr_lines += ['# CODEX_PRODUCT_HARNESS:git-attributes:END', '']
    attr_block = '\n'.join(attr_lines).encode('utf-8')
    desired['@block:.gitattributes'] = attr_block
    actions.append(_desired_block_action(target, '.gitattributes', '.ai/INSTALL_POLICY.json',
                                         'git-attributes', attr_block, records, legacy, ''))

    # Diagnosing LF equivalence is not accepting a different hash. Repair is a
    # separate explicitly reviewed mutation, bound to the old raw-byte hash.
    for item in actions:
        if item['action'] != 'PROTECTED_CONFLICT' or path_has_symlink(target, item['target_path']): continue
        rec = records.get(item['target_path']) or {}
        if item['mode'] not in ('whole_file', 'managed_block') or rec.get('mode') != item['mode']: continue
        path = target / item['target_path']
        if not path.is_file(): continue
        raw = path.read_bytes()
        if item['mode'] == 'managed_block':
            block = find_block(raw, item['marker_id'])
            if not block: continue
            raw = block[2]
        if b'\r\n' not in raw or b'\0' in raw: continue
        try: raw.decode('utf-8')
        except UnicodeDecodeError: continue
        if sha_bytes(raw.replace(b'\r\n', b'\n')) == rec.get('last_managed_sha256'):
            item['eol_repair_available'] = True
            item['reason'] += '; CRLF-only transform matches prior raw LF baseline; explicit --repair-eol required'
            if repair_eol:
                item['action'] = 'OWNED_EOL_REPAIR'
                item['reason'] = 'explicit byte restoration/update from trusted source; prior LF baseline matched; raw hash verification remains strict'

    from install_preflight import collect as collect_preflight
    preflight = collect_preflight(source, target)
    conflicts = [x for x in actions if x['action'] == 'PROTECTED_CONFLICT']
    mutations = [x for x in actions if x['action'] not in ('UNCHANGED', 'PRESERVE_MUTABLE', 'PROTECTED_CONFLICT')]
    plan_core = {
        'schema_version': 2,
        'owner': policy.get('owner', OWNER),
        'canonical_baseline': policy.get('canonical_baseline', '5.3.0'),
        'source_version': version,
        'source_root': str(source),
        'target_root': str(target),
        'previous_state_schema': state_schema,
        'repair_eol_requested': repair_eol,
        'preflight': preflight,
        'actions': actions,
        'conflict_count': len(conflicts),
        'mutation_count': len(mutations),
        'safe_to_apply': not conflicts,
        'protected_project_policy': {
            'paths': policy.get('protected_project_paths', []),
            'prefixes': policy.get('protected_project_prefixes', []),
        },
    }
    digest = sha_bytes(canonical_json(plan_core))
    plan = dict(plan_core)
    plan['plan_digest'] = digest
    return plan, desired


def render_summary(plan: dict) -> dict:
    counts: dict[str, int] = {}
    for item in plan.get('actions', []):
        counts[item['action']] = counts.get(item['action'], 0) + 1
    return {
        'schema_version': plan.get('schema_version'),
        'source_version': plan.get('source_version'),
        'target_root': plan.get('target_root'),
        'plan_digest': plan.get('plan_digest'),
        'safe_to_apply': plan.get('safe_to_apply'),
        'mutation_count': plan.get('mutation_count'),
        'conflict_count': plan.get('conflict_count'),
        'action_counts': counts,
        'preflight': {k: plan.get('preflight', {}).get(k) for k in ('status', 'warnings', 'references', 'legacy_surfaces', 'git_state', 'limits')},
        'conflicts': [
            {'path': x['target_path'], 'mode': x['mode'], 'reason': x['reason']}
            for x in plan.get('actions', []) if x['action'] == 'PROTECTED_CONFLICT'
        ],
    }


def _assert_observed(target: Path, item: dict) -> None:
    path = target / item['target_path']
    exists = path.is_file()
    current = sha_file(path)
    if exists != bool(item.get('observed_exists')) or current != item.get('observed_sha256'):
        raise RuntimeError(f'compare-and-swap refused changed target: {item["target_path"]}')


def _backup_path(tx: Path, rel: str) -> Path:
    return tx / 'backup' / PurePosixPath(rel)


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.harness-write-', dir=str(path.parent), delete=False) as fh:
        tmp = Path(fh.name); fh.write(data); fh.flush()
    try:
        tmp.replace(path)
    finally:
        try: tmp.unlink()
        except FileNotFoundError: pass


def apply_plan(source: Path, target: Path, confirm_digest: str, *, repair_eol: bool = False) -> dict:
    source = source.resolve(); target = target.resolve()
    plan, desired = build_plan(source, target, repair_eol=repair_eol)
    if confirm_digest != plan['plan_digest']:
        raise RuntimeError('plan digest is stale or does not match this target/source state; generate a new plan')
    if not plan['safe_to_apply']:
        raise RuntimeError('plan has protected conflicts; no mutation performed')

    policy = load_json(source / '.ai/INSTALL_POLICY.json')
    tx_root = target / policy.get('transaction_root', '.ai/checkpoints/install-transactions')
    tx = tx_root / plan['plan_digest'][:16]
    if tx.exists():
        shutil.rmtree(tx)
    (tx / 'backup').mkdir(parents=True, exist_ok=True)
    (tx / 'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    state_path = target / policy.get('state_path', '.ai/HARNESS_INSTALL_STATE.json')
    old_state_bytes = state_path.read_bytes() if state_path.is_file() else None
    records, legacy, previous_schema = _previous_records(target)
    records = {k: dict(v) for k, v in records.items()}
    mutated: list[dict] = []

    try:
        for item in plan['actions']:
            if item['action'] in ('UNCHANGED', 'PRESERVE_MUTABLE', 'PROTECTED_CONFLICT'):
                # Adopt exact bytes into state without claiming they were created by Harness.
                if item['action'] == 'UNCHANGED' and item['mode'] == 'whole_file' and item['target_path'] not in records:
                    records[item['target_path']] = {
                        'mode': 'whole_file', 'source_path': item.get('source_path'),
                        'last_managed_sha256': item.get('desired_sha256'), 'created_by_harness': False,
                        'adopted_exact': True,
                    }
                elif item['mode'] == 'mutable_seed' and item['action'] in ('UNCHANGED', 'PRESERVE_MUTABLE'):
                    old = records.get(item['target_path']) or {}
                    prior_seed = item.get('prior_seed_sha256') or old.get('last_seed_sha256') or item.get('desired_sha256')
                    created = old.get('created_by_harness')
                    if created is None:
                        created = False if item['action'] == 'UNCHANGED' and item.get('observed_exists') else True
                    records[item['target_path']] = {
                        'mode': 'mutable_seed', 'source_path': item.get('source_path'), 'install_mode': 'mutable_seed',
                        'last_seed_sha256': prior_seed, 'source_sha256': item.get('source_sha256'),
                        'last_observed_sha256': item.get('observed_sha256'),
                        'created_by_harness': bool(created),
                        'runtime_modified': item['action'] == 'PRESERVE_MUTABLE',
                    }
                continue
            _assert_observed(target, item)
            path = target / item['target_path']
            before = path.read_bytes() if path.is_file() else None
            backup = _backup_path(tx, item['target_path'])
            if before is not None:
                backup.parent.mkdir(parents=True, exist_ok=True); backup.write_bytes(before)
            mutated.append({'path': item['target_path'], 'existed': before is not None})

            if item['mode'] in ('whole_file', 'mutable_seed'):
                data = desired[item['target_path']]
                _write_atomic(path, data)
                old = records.get(item['target_path']) or {}
                created = old.get('created_by_harness')
                if created is None:
                    created = before is None
                if item['mode'] == 'mutable_seed':
                    records[item['target_path']] = {
                        'mode': 'mutable_seed', 'source_path': item.get('source_path'), 'install_mode': 'mutable_seed',
                        'last_seed_sha256': sha_bytes(data), 'source_sha256': item.get('source_sha256'),
                        'last_observed_sha256': sha_bytes(data), 'created_by_harness': bool(created),
                        'runtime_modified': False,
                    }
                else:
                    records[item['target_path']] = {
                        'mode': 'whole_file', 'source_path': item.get('source_path'),
                        'install_mode': item.get('install_mode'),
                        'last_managed_sha256': sha_bytes(data), 'created_by_harness': bool(created),
                        'source_sha256': item.get('source_sha256'),
                    }
            else:
                block = desired[f'@block:{item["target_path"]}']
                after = merge_block(before, item['marker_id'], block)
                _write_atomic(path, after)
                old = records.get(item['target_path']) or {}
                container_created = old.get('container_created_by_harness')
                if container_created is None:
                    container_created = before is None
                records[item['target_path']] = {
                    'mode': 'managed_block', 'source_path': item.get('source_path'),
                    'snapshot_path': item.get('snapshot_path'), 'marker_id': item.get('marker_id'),
                    'last_managed_sha256': sha_bytes(block),
                    'container_created_by_harness': bool(container_created),
                    'container_after_sha256': sha_bytes(after),
                }

        # State is written last. It is runtime control state and is excluded from source/artifact fingerprints.
        state = {
            'schema_version': 3,
            'owner': policy.get('owner', OWNER),
            'harness_version': plan['source_version'],
            'canonical_baseline': plan.get('canonical_baseline'),
            'source_plan_digest': plan['plan_digest'],
            'records': records,
            'legacy_state_schema_migrated_from': previous_schema if previous_schema == 1 else None,
            'install_policy_sha256': sha_file(source / '.ai/INSTALL_POLICY.json'),
        }
        _write_atomic(state_path, json.dumps(state, indent=2, ensure_ascii=False).encode('utf-8') + b'\n')
        result = {'status': 'pass', 'plan_digest': plan['plan_digest'], 'mutated': [x['path'] for x in mutated], 'state_path': str(state_path)}
        (tx / 'result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        # Backups are only transaction scratch. Hash/audit plan remains, raw preimages are removed after success.
        shutil.rmtree(tx / 'backup', ignore_errors=True)
        return result
    except Exception as exc:
        rollback_errors=[]
        for item in reversed(mutated):
            path = target / item['path']; backup = _backup_path(tx, item['path'])
            try:
                if item['existed']:
                    _write_atomic(path, backup.read_bytes())
                else:
                    path.unlink(missing_ok=True)
            except Exception as rb_exc:
                rollback_errors.append(f'{item["path"]}: {rb_exc}')
        try:
            if old_state_bytes is None:
                state_path.unlink(missing_ok=True)
            else:
                _write_atomic(state_path, old_state_bytes)
        except Exception as rb_exc:
            rollback_errors.append(f'state: {rb_exc}')
        result = {'status': 'rolled_back' if not rollback_errors else 'rollback_incomplete', 'error': str(exc), 'rollback_errors': rollback_errors}
        (tx / 'result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        raise


def main() -> None:
    ap = argparse.ArgumentParser(description='Build a collision-safe, ownership-aware Harness install plan. Planning is read-only.')
    ap.add_argument('--source', default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument('--target', required=True)
    ap.add_argument('--out')
    args = ap.parse_args()
    try:
        plan, _ = build_plan(Path(args.source), Path(args.target))
    except Exception as exc:
        raise SystemExit(f'INSTALL PLAN: FAIL - {exc}')
    rendered = json.dumps(plan if args.out else render_summary(plan), indent=2, ensure_ascii=False) + '\n'
    if args.out:
        Path(args.out).write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(rendered, end='')
    raise SystemExit(2 if not plan['safe_to_apply'] else 0)


if __name__ == '__main__':
    main()
