from __future__ import annotations

from pathlib import Path
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from typing import Iterable, Iterator

# Harness scripts must not dirty a repository merely by being executed.
sys.dont_write_bytecode = True

EXCLUDE_DIRS = {'.git', 'node_modules', '.next', 'dist', 'build', 'coverage', '.turbo', '.cache', '__pycache__'}
SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|token|secret|authorization|password)(\s*[=:]\s*)([^\s,;]+)'),
    re.compile(r'AIza[0-9A-Za-z_\-]{20,}'),
    re.compile(r'\bsk-[A-Za-z0-9_\-]{12,}\b'),
]
TASK_ID_RE = re.compile(r'^[A-Z0-9][A-Z0-9._-]{0,127}$')
CHECK_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')

CLOSURE_MUTABLE_PATHS = {
    '.ai/STATE.json', '.ai/RESUME.md', '.ai/DECISIONS.md', '.ai/REPO_MAP.json',
}
RUNTIME_STATE_PREFIXES = ('.ai/evidence/', '.ai/checkpoints/')
RUNTIME_STATE_EXACT = {'.ai/REPO_MAP.json'}
PRODUCT_DIGEST_EXACT_EXCLUDES = {
    '.ai/STATE.json', '.ai/RESUME.md', '.ai/DECISIONS.md', '.ai/REPO_MAP.json',
    '.ai/HARNESS_INSTALL_STATE.json',
}
PRODUCT_DIGEST_PREFIX_EXCLUDES = ('.ai/evidence/', '.ai/checkpoints/', '.ai/tasks/')


def is_runtime_state_path(rel: str) -> bool:
    rel = rel.replace('\\', '/')
    return rel in RUNTIME_STATE_EXACT or any(rel.startswith(prefix) for prefix in RUNTIME_STATE_PREFIXES)


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except (OSError, ValueError):
                pass


def root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def run_capture_full(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Keep data and diagnostics separate. No Git/user configuration is changed."""
    p = subprocess.run(args, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, encoding='utf-8', errors='surrogateescape')
    return p.returncode, p.stdout, p.stderr


def run_capture(args: list[str], cwd: Path) -> tuple[int, str]:
    rc, stdout, stderr = run_capture_full(args, cwd)
    if stderr:
        sys.stderr.write(stderr)
    return rc, stdout


def git_info(root: Path) -> dict:
    rc, sha, diagnostics = run_capture_full(['git', 'rev-parse', 'HEAD'], root)
    if rc != 0:
        return {'is_git': False, 'sha': None, 'branch': None}
    if diagnostics:
        sys.stderr.write(diagnostics)
    rc, branch = run_capture(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], root)
    return {'is_git': True, 'sha': sha.strip(), 'branch': branch.strip() if rc == 0 else None}


def nul_paths(output: str) -> list[str]:
    if not output:
        return []
    if not output.endswith('\0'):
        raise ValueError('incomplete NUL-delimited Git output')
    paths = output[:-1].split('\0')
    if any(not path for path in paths):
        raise ValueError('empty Git path record')
    return paths


def parse_git_status_z(output: str) -> list[tuple[str, str]]:
    """Porcelain v1 -z: preserve path bytes; include BOTH sides of a rename."""
    fields = nul_paths(output); rows = []; index = 0
    while index < len(fields):
        record = fields[index]; index += 1
        if len(record) < 4 or record[2] != ' ' or any(c not in ' MADRCUT?!' for c in record[:2]):
            raise ValueError('invalid Git porcelain status record')
        status, path = record[:2], record[3:]
        if not path:
            raise ValueError('empty Git status path')
        rows.append((status, path))
        if 'R' in status or 'C' in status:
            if index >= len(fields):
                raise ValueError('missing rename/copy source path')
            rows.append((status, fields[index])); index += 1
    return rows


def git_status_entries(root: Path) -> list[tuple[str, str]]:
    rc, output = run_capture(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], root)
    if rc != 0:
        raise RuntimeError('git status failed; cleanliness is unknown')
    return parse_git_status_z(output)


def _task_path_from_ref(root: Path, ref: str) -> Path:
    # IDs map to .ai/tasks/<id>.json. Paths are locators only; identity comes from JSON id.
    if TASK_ID_RE.fullmatch(ref):
        return root/'.ai/tasks'/f'{ref}.json'
    path = Path(ref)
    if not path.is_absolute():
        path = root/path
    return path


def resolve_task(root: Path, ref: str | None) -> tuple[Path, dict]:
    if not ref:
        state = load_json(root/'.ai/STATE.json')
        ref = state.get('active_task')
    if not ref:
        raise ValueError('no active task')
    path = _task_path_from_ref(root, str(ref)).resolve()
    tasks_root = (root/'.ai/tasks').resolve()
    try:
        path.relative_to(tasks_root)
    except ValueError:
        raise ValueError(f'task locator escapes .ai/tasks: {ref}')
    if path.suffix.lower() != '.json' or not path.exists():
        raise ValueError(f'task not found: {path}')
    task = load_json(path)
    task_id = str(task.get('id') or '').strip()
    if not TASK_ID_RE.fullmatch(task_id):
        raise ValueError(f'invalid canonical task id in {path.name}: {task_id!r}')
    expected_name = f'{task_id}.json'
    if path.name != expected_name:
        raise ValueError(f'task filename/id mismatch: {path.name} != {expected_name}')
    return path, task


def _load_event_file(path: Path) -> dict | None:
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def load_events(path: Path) -> list[dict]:
    """Load v5.5 atomic events first, then legacy JSONL entries not already present."""
    result: list[dict] = []
    seen: set[str] = set()
    event_dir = path.parent/'events'
    if event_dir.is_dir():
        for p in sorted(event_dir.glob('*.json')):
            event = _load_event_file(p)
            if not event:
                continue
            eid = evidence_event_id(event)
            if eid in seen:
                continue
            seen.add(eid); result.append(event)
    if path.exists():
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            eid = evidence_event_id(event)
            if eid in seen:
                continue
            seen.add(eid); result.append(event)
    result.sort(key=lambda e: (str(e.get('timestamp') or ''), str(e.get('event_id') or '')))
    return result


def derive_required_checks(task: dict, quality: dict) -> set[str]:
    required = set(task.get('verification', {}).get('required_checks', []))
    for trait, enabled in task.get('traits', {}).items():
        if enabled:
            required.update(quality.get('trait_required_checks', {}).get(trait, []))
    profile = str((task.get('execution_contract') or {}).get('resolved_profile') or '').lower()
    if profile:
        required.update(quality.get('profile_required_checks', {}).get(profile, []))
    return required


def _parse_utc(value: object) -> dt.datetime | None:
    text = str(value or '').strip()
    if not text:
        return None
    try:
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        parsed = dt.datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def finding_digest(finding: dict) -> str:
    fields = ('id', 'check', 'severity', 'component', 'attack_path', 'evidence_refs')
    canonical = {key: finding.get(key) for key in fields}
    raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def waiver_digest(waiver: dict) -> str:
    canonical = {key: waiver.get(key) for key in ('check','reason','owner','approved_at','expires_at','finding_id','accepted_finding_sha256','accepted_scope','human_approved')}
    raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def waiver_validation(task: dict, now: dt.datetime | None = None) -> tuple[dict[str, dict], list[str]]:
    now = now or dt.datetime.now(dt.timezone.utc)
    verification = task.get('verification', {}) or {}
    findings = {str(x.get('id')): x for x in verification.get('findings', []) if isinstance(x, dict) and x.get('id')}
    approved: dict[str, dict] = {}; errors: list[str] = []
    for index, waiver in enumerate(verification.get('waivers', [])):
        if not isinstance(waiver, dict): errors.append(f'waiver[{index}] is not an object'); continue
        check = str(waiver.get('check') or '').strip(); prefix=f'waiver[{index}]'+(f' {check}' if check else '')
        required=('check','reason','owner','approved_at','expires_at','finding_id','accepted_finding_sha256','accepted_scope')
        missing=[key for key in required if waiver.get(key) in (None,'',[])]
        if missing: errors.append(prefix+': missing '+', '.join(missing)); continue
        if waiver.get('human_approved') is not True: errors.append(prefix+': human_approved must be true'); continue
        approved_at=_parse_utc(waiver.get('approved_at')); expires_at=_parse_utc(waiver.get('expires_at'))
        if not approved_at or not expires_at: errors.append(prefix+': approved_at/expires_at must be timezone-aware ISO-8601'); continue
        if expires_at<=approved_at: errors.append(prefix+': expires_at must be after approved_at'); continue
        if now>=expires_at: errors.append(prefix+': expired'); continue
        finding=findings.get(str(waiver.get('finding_id')))
        if not finding: errors.append(prefix+': referenced finding is missing'); continue
        if finding.get('check')!=check: errors.append(prefix+': finding check mismatch'); continue
        current_digest=finding_digest(finding)
        if waiver.get('accepted_finding_sha256')!=current_digest: errors.append(prefix+': accepted finding digest is stale'); continue
        scope=waiver.get('accepted_scope')
        if not isinstance(scope,dict): errors.append(prefix+': accepted_scope must be an object'); continue
        current_scope={'finding_id':finding.get('id'),'check':finding.get('check'),'severity':finding.get('severity'),'component':finding.get('component'),'attack_path':finding.get('attack_path')}
        if scope!=current_scope: errors.append(prefix+': accepted_scope is stale'); continue
        if check in approved: errors.append(prefix+': duplicate active waiver for check'); continue
        item=dict(waiver); item['waiver_sha256']=waiver_digest(waiver); approved[check]=item
    return approved, errors


def approved_waivers(task: dict) -> dict[str, dict]:
    approved,_=waiver_validation(task); return approved


def evidence_event_id(event: dict) -> str:
    existing=str(event.get('event_id') or '').strip()
    if re.fullmatch(r'[0-9a-f]{64}',existing): return existing
    canonical={key:event.get(key) for key in ('timestamp','task','check','status','command_exit_code','output_digest','fingerprint_after','product_source_digest','task_contract_digest','check_contract_digest','runtime_candidate_digest','catalog_runner','command')}
    raw=json.dumps(canonical,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _contract_projection(task: dict) -> dict:
    """Fields that define what must be built/verified; lifecycle timestamps/status are excluded."""
    verification = task.get('verification', {}) or {}
    release = task.get('release', {}) or {}
    projection = {
        'schema_version': task.get('schema_version'), 'id': task.get('id'), 'mode': task.get('mode'),
        'objective': task.get('objective'), 'user_outcome': task.get('user_outcome'), 'scope': task.get('scope'),
        'traits': task.get('traits'), 'execution_contract': task.get('execution_contract'),
        'experience_contract': task.get('experience_contract'), 'state_contract': task.get('state_contract'),
        'acceptance_criteria': task.get('acceptance_criteria'), 'critical_user_flows': task.get('critical_user_flows'),
        'change_budget': task.get('change_budget'), 'risk': task.get('risk'),
        'verification': {
            'required_checks': verification.get('required_checks', []), 'waivers': verification.get('waivers', []),
            'findings': verification.get('findings', []), 'notes': verification.get('notes'),
            'check_states': verification.get('check_states', {}),
        },
        'release_contract': {'production_url': release.get('production_url'), 'rollback': release.get('rollback')},
    }

    # Optional brief context is task intent, not excluded runtime state.
    # Omit the key for legacy tasks to preserve their existing contract digests.
    if 'prompt_context' in task:
        projection['prompt_context'] = task['prompt_context']
    return projection


def task_contract_digest(task: dict) -> str:
    raw=json.dumps(_contract_projection(task),ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def check_contract_digest(task: dict, check: str) -> str:
    """Per-check contract identity: global acceptance truth plus only findings/waivers relevant to this check."""
    projection=_contract_projection(task)
    verification=projection.get('verification',{}) or {}
    findings=[]
    for item in verification.get('findings',[]) or []:
        if isinstance(item,dict) and item.get('check') in (None,check): findings.append(item)
    waivers=[]
    for item in verification.get('waivers',[]) or []:
        if isinstance(item,dict) and item.get('check')==check: waivers.append(item)
    verification['findings']=findings; verification['waivers']=waivers
    projection['verification']=verification
    raw=json.dumps(projection,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def lifecycle_state_digest(root: Path, task: dict | None = None) -> str:
    payload: dict[str, object] = {}
    for rel in ('.ai/STATE.json','.ai/RESUME.md','.ai/DECISIONS.md'):
        p=root/rel
        payload[rel]=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    if task is not None:
        payload['task_lifecycle']={k:task.get(k) for k in ('id','status','closure')}
        payload['release_state']=(task.get('release') or {}).get('deployed_revision')
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def runtime_candidate_digest(root: Path, task: dict | None = None) -> str:
    """Identity of the exact runtime/deployment candidate without coupling lifecycle prose to source evidence."""
    task = task or {}
    release = task.get('release', {}) or {}
    payload = {
        'task': task.get('id'),
        'product_source_digest': product_source_digest(root),
        'candidate_revision': release.get('candidate_revision'),
        'deployed_revision': release.get('deployed_revision'),
        'revision_marker': release.get('revision_marker'),
        'artifact_sha256': release.get('artifact_sha256'),
        'deployment_id': release.get('deployment_id'),
        'production_url': release.get('production_url'),
    }
    # Closure creation/status is lifecycle provenance, validated independently by
    # validate_closure. Adding a receipt cannot change an unchanged runtime.
    # Actual release URL/revisions/marker/artifact/deployment ID remain bound above.
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def platform_id() -> str:
    if os.name == 'nt': return 'windows'
    if sys.platform == 'darwin': return 'macos'
    return 'linux'


def check_catalog_digest(root: Path) -> str | None:
    p=root/'.ai/CHECK_CATALOG.json'
    if not p.is_file(): return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_check_catalog(root: Path) -> dict:
    p=root/'.ai/CHECK_CATALOG.json'
    if not p.is_file(): return {'schema_version':0,'runners':[]}
    data=load_json(p)
    if not isinstance(data.get('runners'), list):
        raise ValueError('CHECK_CATALOG runners must be a list')
    return data


def catalog_runner(root: Path, runner_id: str) -> dict | None:
    for item in load_check_catalog(root).get('runners', []):
        if item.get('id') == runner_id: return item
    return None


def catalog_runner_for_check(root: Path, check: str, context: str | None = None, platform: str | None = None) -> dict | None:
    platform = platform or platform_id()
    for item in load_check_catalog(root).get('runners', []):
        if check not in item.get('checks', []): continue
        contexts=item.get('contexts', ['source','installed','legacy-installed'])
        platforms=item.get('platforms', ['windows','linux','macos'])
        if context and context not in contexts: continue
        if platform not in platforms: continue
        return item
    return None


def closure_manifest_path(root: Path, task_id: str) -> Path:
    return root/'.ai/evidence'/f'closure-{task_id}.json'


def validate_closure(root: Path, task_path: Path, task: dict) -> tuple[dict | None, list[str]]:
    manifest_path=closure_manifest_path(root,str(task.get('id','')))
    if task.get('status') not in {'COMPLETE','LOCALLY_ACCEPTED'} or not manifest_path.exists(): return None,[]
    errors=[]
    try: manifest=load_json(manifest_path)
    except Exception as exc: return None,[f'invalid closure manifest: {exc}']
    task_id=task.get('id')
    if manifest.get('task')!=task_id: errors.append('closure manifest task id mismatch')
    # v5.5 task contract excludes lifecycle status so closure can legitimately mutate status.
    if manifest.get('task_contract_digest')!=task_contract_digest(task): errors.append('task contract changed after closure')
    candidate=str(manifest.get('candidate_sha') or '')
    candidate_fp=str(manifest.get('candidate_fingerprint') or manifest.get('product_source_digest') or '')
    if manifest.get('closure_kind')=='local_snapshot':
        if not re.fullmatch(r'[0-9a-f]{64}',candidate_fp): errors.append('local snapshot digest missing or invalid')
        return manifest,errors
    if not re.fullmatch(r'[0-9a-fA-F]{7,40}',candidate): errors.append('closure candidate_sha is missing or invalid')
    if not re.fullmatch(r'[0-9a-f]{64}',candidate_fp): errors.append('closure candidate_fingerprint is missing or invalid')
    gi=git_info(root)
    if not gi.get('is_git'): errors.append('closure validation requires git'); return manifest,errors
    if candidate:
        rc,_=run_capture(['git','merge-base','--is-ancestor',candidate,'HEAD'],root)
        if rc!=0: errors.append('closure candidate is not an ancestor of HEAD')
        rc,changed=run_capture(['git','diff','--name-only','-z',candidate,'--','.'],root)
        if rc!=0: errors.append('could not compare closure against candidate')
        else:
            task_rel=task_path.relative_to(root).as_posix(); allowed_exact=CLOSURE_MUTABLE_PATHS|{task_rel}; invalid=[]
            for rel in nul_paths(changed):
                if rel not in allowed_exact and not is_runtime_state_path(rel): invalid.append(rel)
            if invalid: errors.append('non-closure paths changed after candidate: '+', '.join(sorted(invalid)))
    try:
        rows = git_status_entries(root)
        task_rel=task_path.relative_to(root).as_posix(); allowed_exact=CLOSURE_MUTABLE_PATHS|{task_rel}; invalid=[]
        for _, rel in rows:
            if rel not in allowed_exact and not is_runtime_state_path(rel): invalid.append(rel)
        if invalid: errors.append('working tree contains non-closure changes: '+', '.join(sorted(set(invalid))))
    except (RuntimeError, ValueError) as exc:
        errors.append(str(exc))
    return manifest,errors


def _hash_file_content(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def _include_product_path(rel: str) -> bool:
    rel=rel.replace('\\','/')
    if rel in PRODUCT_DIGEST_EXACT_EXCLUDES: return False
    if any(rel.startswith(prefix) for prefix in PRODUCT_DIGEST_PREFIX_EXCLUDES): return False
    return True


def product_source_manifest(root: Path) -> dict[str, str]:
    """Deterministic content manifest used for source evidence freshness and mutation diffs."""
    result: dict[str,str] = {}
    gi=git_info(root)
    if gi.get('is_git'):
        rc,files=run_capture(['git','ls-files','-z','--cached','--others','--exclude-standard'],root)
        if rc != 0: raise RuntimeError('git ls-files failed; source fingerprint is unknown')
        candidates=nul_paths(files)
    else:
        candidates=[]
        for p in root.rglob('*'):
            if not p.is_file(): continue
            rel=p.relative_to(root).as_posix()
            if any(part in EXCLUDE_DIRS for part in Path(rel).parts): continue
            candidates.append(rel)
    for raw in sorted(set(x for x in candidates if x)):
        if not _include_product_path(raw): continue
        p=root/raw
        if p.is_file():
            try: result[raw]=_hash_file_content(p)
            except OSError: result[raw]='ERROR'
    return result


def product_source_digest(root: Path) -> str:
    manifest=product_source_manifest(root)
    raw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def workspace_fingerprint(root: Path) -> str:
    """Compatibility alias. Since v5.5 evidence freshness means product source, not lifecycle prose."""
    return product_source_digest(root)


def manifest_diff(before: dict[str,str], after: dict[str,str]) -> dict:
    b=set(before); a=set(after)
    added=sorted(a-b); deleted=sorted(b-a); modified=sorted(k for k in a&b if before[k]!=after[k])
    return {'added':added,'modified':modified,'deleted':deleted,'count':len(added)+len(modified)+len(deleted)}


def redact(text: str) -> str:
    out=text
    for pat in SECRET_PATTERNS:
        if pat.pattern.startswith('(?i)'): out=pat.sub(lambda m:f'{m.group(1)}{m.group(2)}[REDACTED]',out)
        else: out=pat.sub('[REDACTED]',out)
    return out


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def dump_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f'.tmp-{uuid.uuid4().hex}')
    data=(json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    with tmp.open('wb') as fh:
        fh.write(data); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp,path)


def iter_source_files(root: Path, extensions: set[str]) -> Iterable[Path]:
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in extensions: continue
        rel_parts=p.relative_to(root).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts): continue
        if len(rel_parts)>=2 and rel_parts[0]=='.ai' and rel_parts[1]=='evidence': continue
        yield p


def harness_context(root: Path) -> str:
    marker=root/'.ai/SOURCE_DISTRIBUTION.json'; state=root/'.ai/HARNESS_INSTALL_STATE.json'
    if marker.is_file(): return 'source'
    if state.is_file():
        try: schema=int(load_json(state).get('schema_version') or 0)
        except Exception: return 'installed'
        return 'installed' if schema>=2 else 'legacy-installed'
    if (root/'.ai/HARNESS_MANIFEST.json').is_file(): return 'legacy-installed'
    return 'unknown'


def harness_version(root: Path) -> str:
    context=harness_context(root)
    if context=='source': p=root/'VERSION'
    elif (root/'.ai/harness/VERSION').is_file(): p=root/'.ai/harness/VERSION'
    elif (root/'.ai/HARNESS_INSTALL_STATE.json').is_file():
        try:
            value=str(load_json(root/'.ai/HARNESS_INSTALL_STATE.json').get('harness_version') or '').strip()
            if value: return value
        except Exception: pass
        p=root/'VERSION'
    else: p=root/'VERSION'
    return p.read_text(encoding='utf-8').strip() if p.is_file() else ''


def _writable_probe(path: Path) -> bool:
    try:
        path.mkdir(parents=True,exist_ok=True)
        probe=path/f'.harness-probe-{uuid.uuid4().hex}'
        with probe.open('wb') as fh:
            fh.write(b'probe'); fh.flush(); os.fsync(fh.fileno())
        probe.unlink()
        return True
    except OSError:
        return False


def safe_temp_base(root: Path | None = None, explicit: str | None = None, *, for_copy: bool = False) -> Path:
    root=root or root_from_script()
    candidates=[]
    if explicit: candidates.append(Path(explicit))
    if os.environ.get('HARNESS_TEMP_DIR'): candidates.append(Path(os.environ['HARNESS_TEMP_DIR']))
    if os.environ.get('HARNESS_TMP'): candidates.append(Path(os.environ['HARNESS_TMP']))
    for key in ('TMPDIR', 'TEMP', 'TMP'):
        if os.environ.get(key): candidates.append(Path(os.environ[key]))
    # Probe OS temp first when writable so regressions that copy the repository do not
    # recurse into a workspace-owned temp directory. Managed Windows sandboxes fall
    # through to the runtime-state workspace temp when OS temp is denied.
    try: candidates.append(Path(tempfile.gettempdir()))
    except Exception: pass
    candidates.append(root/'.ai/checkpoints/tmp')
    seen=set(); rejected=[]
    for candidate in candidates:
        lexical = Path(os.path.abspath(candidate))
        try: candidate=candidate.resolve()
        except OSError as exc:
            rejected.append(f'{lexical}: {type(exc).__name__}'); continue
        if str(candidate) in seen: continue
        seen.add(str(candidate))
        if for_copy and (candidate.is_relative_to(root.resolve()) or lexical.is_relative_to(Path(os.path.abspath(root)))):
            rejected.append(f'{candidate}: COPY_TEMP_OVERLAP')
            if explicit and lexical == Path(os.path.abspath(explicit)):
                raise RuntimeError('COPY_TEMP_OVERLAP: --temp-root must be outside the source tree being copied')
            continue
        if _writable_probe(candidate): return candidate
        rejected.append(f'{candidate}: not writable')
    purpose='copy-safe ' if for_copy else ''
    raise RuntimeError(f'no writable {purpose}Harness temp root; use --temp-root or HARNESS_TEMP_DIR outside the source tree; '+ '; '.join(rejected))


def assert_copy_destination(source: Path, destination: Path) -> None:
    src=source.resolve(); dst=destination.resolve()
    if dst.is_relative_to(src) or src.is_relative_to(dst):
        raise ValueError('COPY_TREE_OVERLAP: source and destination must not contain each other')


def copy_source_tree(source: Path, destination: Path, **kwargs):
    """Fail before allocating/copying a recursive destination (including resolved aliases)."""
    assert_copy_destination(source, destination)
    return shutil.copytree(source, destination, **kwargs)


@contextlib.contextmanager
def harness_temp_dir(root: Path | None = None, prefix: str = 'harness-', temp_root: str | None = None, *, for_copy: bool = False) -> Iterator[Path]:
    root=root or root_from_script(); base=safe_temp_base(root,temp_root,for_copy=for_copy)
    path=base/f'{prefix}{uuid.uuid4().hex}'
    path.mkdir(parents=True,exist_ok=False)
    lease=path/'.harness-temp-lease.json'
    dump_json(lease,{'owner':'codex-product-harness','created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'path':str(path)})
    try:
        yield path
    finally:
        cleanup_error=[]
        def _cleanup():
            try: shutil.rmtree(path)
            except OSError as exc: cleanup_error.append(str(exc))
        t=threading.Thread(target=_cleanup,daemon=True); t.start(); t.join(10)
        if t.is_alive() or cleanup_error or path.exists():
            # Teardown is bounded. Residue is recorded and may only be removed by lease-aware cleanup.
            residue=root/'.ai/checkpoints/temp-residue.jsonl'; residue.parent.mkdir(parents=True,exist_ok=True)
            with residue.open('a',encoding='utf-8') as fh:
                fh.write(json.dumps({'path':str(path),'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),'reason':'cleanup-timeout' if t.is_alive() else (cleanup_error[0] if cleanup_error else 'residue-remains')},ensure_ascii=False)+'\n')
