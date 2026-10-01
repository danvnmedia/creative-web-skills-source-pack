#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
sys.dont_write_bytecode = True
from _common import copy_source_tree, safe_temp_base

ROOT = Path(__file__).resolve().parents[2]
tempfile.tempdir=str(safe_temp_base(ROOT, for_copy=True))
PY = sys.executable


def run(cmd, cwd=ROOT, expect=0):
    p = subprocess.run(cmd, cwd=str(cwd), text=True, encoding='utf-8', errors='replace', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != expect:
        raise SystemExit(f'V5.4.2 REGRESSION: FAIL expected {expect}, got {p.returncode}: {cmd}\n{p.stdout}')
    return p.stdout or ''


def false_traits(**updates):
    values = {
        'user_facing_web': False,
        'external_runtime_dependencies': False,
        'ai_integration': False,
        'security_sensitive': False,
        'performance_sensitive': False,
        'production_release': False,
        'stateful_user_workflow': False,
        'large_binary_data': False,
        'truthful_claims': False,
        'harness_modification': False,
        'skill_modification': False,
        'borrowed_browser_session': False,
        'mcp_runtime': False,
    }
    values.update(updates)
    return values


def finding_hash(finding):
    fields = ('id', 'check', 'severity', 'component', 'attack_path', 'evidence_refs')
    canonical = {k: finding.get(k) for k in fields}
    raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def waiver_task(expires_offset_hours=24):
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    finding = {
        'id': 'finding-1',
        'check': 'security-negative',
        'severity': 'medium',
        'component': 'fixture-component',
        'attack_path': 'fixture-input -> guarded-operation',
        'evidence_refs': ['fixture://finding-1'],
    }
    waiver = {
        'check': 'security-negative',
        'reason': 'fixture risk accepted for regression only',
        'owner': 'fixture-owner',
        'approved_at': (now - dt.timedelta(hours=2)).isoformat().replace('+00:00', 'Z'),
        'expires_at': (now + dt.timedelta(hours=expires_offset_hours)).isoformat().replace('+00:00', 'Z'),
        'finding_id': finding['id'],
        'accepted_finding_sha256': finding_hash(finding),
        'accepted_scope': {
            'finding_id': finding['id'],
            'check': finding['check'],
            'severity': finding['severity'],
            'component': finding['component'],
            'attack_path': finding['attack_path'],
        },
        'human_approved': True,
    }
    return {
        'schema_version': 5,
        'id': 'WAIVER',
        'mode': 'FEATURE',
        'status': 'READY',
        'traits': false_traits(),
        'execution_contract': {'profile': 'native', 'resolved_profile': 'native'},
        'verification': {'required_checks': ['security-negative'], 'findings': [finding], 'waivers': [waiver]},
        'release': {},
        'risk': {'level': 'medium'},
    }


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        tmp = td/'harness'
        copy_source_tree(ROOT, tmp, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        run(['git', 'init', '-q'], tmp)
        run(['git', 'config', 'user.email', 'v542@example.invalid'], tmp)
        run(['git', 'config', 'user.name', 'V542 Test'], tmp)

        # --- Content-pinned waiver: valid, expired, changed finding, closure tamper ---
        task_path = tmp/'.ai/tasks/WAIVER.json'
        task = waiver_task(24)
        write_json(task_path, task)
        valid = run([PY, '.ai/scripts/evidence_gate.py', '--task', 'WAIVER'], tmp)
        if '[WAIVED] security-negative' not in valid:
            raise SystemExit('V5.4.2 REGRESSION: FAIL valid content-pinned waiver was not accepted')

        expired = waiver_task(-1)
        write_json(task_path, expired)
        out = run([PY, '.ai/scripts/evidence_gate.py', '--task', 'WAIVER'], tmp, expect=1)
        if 'expired' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL expired waiver did not fail closed')

        stale = waiver_task(24)
        stale['verification']['findings'][0]['severity'] = 'high'
        write_json(task_path, stale)
        out = run([PY, '.ai/scripts/evidence_gate.py', '--task', 'WAIVER'], tmp, expect=1)
        if 'digest is stale' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL changed finding did not invalidate waiver')

        valid_task = waiver_task(24)
        write_json(task_path, valid_task)
        run(['git', 'add', '.'], tmp)
        run(['git', 'commit', '-qm', 'waiver candidate'], tmp)
        run([PY, '.ai/scripts/close_task.py', '--task', 'WAIVER'], tmp)
        run([PY, '.ai/scripts/evidence_gate.py', '--task', 'WAIVER'], tmp)
        closure = tmp/'.ai/evidence/closure-WAIVER.json'
        closure_doc = json.loads(closure.read_text(encoding='utf-8'))
        closure_doc['waivers'][0]['reason'] = 'tampered after closure'
        write_json(closure, closure_doc)
        out = run([PY, '.ai/scripts/evidence_gate.py', '--task', 'WAIVER'], tmp, expect=1)
        if 'closure waiver digest mismatch' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL closure waiver tamper was not detected')
        # restore exact closure for subsequent git operations
        closure_doc['waivers'][0]['reason'] = 'fixture risk accepted for regression only'
        write_json(closure, closure_doc)
        run(['git', 'add', '.ai/tasks/WAIVER.json', '.ai/STATE.json'], tmp)
        run(['git', 'commit', '-qm', 'waiver closure source state'], tmp)

        # --- Deterministic controller: RETRY -> REPLAN; fresh pass -> ACCEPT ---
        loop_task = {
            'schema_version': 5, 'id': 'LOOP', 'mode': 'FEATURE', 'status': 'READY',
            'traits': false_traits(), 'execution_contract': {'profile': 'native', 'resolved_profile': 'native'},
            'verification': {'required_checks': ['focused-test'], 'findings': [], 'waivers': []},
            'release': {}, 'risk': {'level': 'medium'},
        }
        write_json(tmp/'.ai/tasks/LOOP.json', loop_task)
        run(['git', 'add', '.ai/tasks/LOOP.json'], tmp)
        run(['git', 'commit', '-qm', 'loop task'], tmp)
        fail_cmd = [PY, '-c', "print('fixture failure'); raise SystemExit(1)"]
        run([PY, '.ai/scripts/record_evidence.py', '--task', 'LOOP', '--check', 'focused-test', '--hypothesis-id', 'H1', '--', *fail_cmd], tmp, expect=1)
        out = run([PY, '.ai/scripts/control_decision.py', '--task', 'LOOP', '--check', 'focused-test', '--next-hypothesis-id', 'H2', '--no-write'], tmp)
        if '"decision": "RETRY"' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL changed hypothesis did not permit bounded retry')
        for _ in range(2):
            run([PY, '.ai/scripts/record_evidence.py', '--task', 'LOOP', '--check', 'focused-test', '--hypothesis-id', 'H1', '--', *fail_cmd], tmp, expect=1)
        out = run([PY, '.ai/scripts/control_decision.py', '--task', 'LOOP', '--check', 'focused-test', '--next-hypothesis-id', 'H2', '--no-write'], tmp)
        if '"decision": "REPLAN"' not in out or 'repeated-identical-failure' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL repeated failure did not force replan')
        run([PY, '.ai/scripts/record_evidence.py', '--task', 'LOOP', '--check', 'focused-test', '--hypothesis-id', 'H2', '--', PY, '-c', "print('ok')"], tmp)
        out = run([PY, '.ai/scripts/control_decision.py', '--task', 'LOOP', '--check', 'focused-test', '--no-write'], tmp)
        if '"decision": "ACCEPT"' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL fresh pass did not produce ACCEPT')

        # --- Hard boundary -> ROLLBACK only to a valid verified checkpoint ---
        rb_task = {
            'schema_version': 5, 'id': 'ROLLBACK', 'mode': 'FEATURE', 'status': 'READY',
            'traits': false_traits(), 'execution_contract': {'profile': 'portable', 'resolved_profile': 'portable'},
            'verification': {'required_checks': [], 'findings': [], 'waivers': []},
            'release': {}, 'risk': {'level': 'high'},
        }
        write_json(tmp/'.ai/tasks/ROLLBACK.json', rb_task)
        run(['git', 'add', '.ai/tasks/ROLLBACK.json'], tmp)
        run(['git', 'commit', '-qm', 'rollback task'], tmp)
        run([PY, '.ai/scripts/record_evidence.py', '--task', 'ROLLBACK', '--check', 'baseline-check', '--', PY, '-c', "print('baseline ok')"], tmp)
        run([PY, '.ai/scripts/verified_checkpoint.py', 'checkpoint', '--task', 'ROLLBACK', '--completed', 'safe baseline verified', '--next-action', 'continue guarded work', '--check', 'baseline-check'], tmp)
        run([PY, '.ai/scripts/record_evidence.py', '--task', 'ROLLBACK', '--check', 'security-negative', '--hard-boundary-breach', '--risk-boundary', 'security', '--hypothesis-id', 'unsafe-path', '--', PY, '-c', "print('boundary breach'); raise SystemExit(1)"], tmp, expect=1)
        out = run([PY, '.ai/scripts/control_decision.py', '--task', 'ROLLBACK', '--check', 'security-negative', '--no-write'], tmp)
        if '"decision": "ROLLBACK"' not in out or 'safe baseline verified' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL hard boundary did not target verified checkpoint')
        (tmp/'.ai/checkpoints/ROLLBACK.json').unlink()
        out = run([PY, '.ai/scripts/control_decision.py', '--task', 'ROLLBACK', '--check', 'security-negative', '--no-write'], tmp)
        if '"decision": "REPLAN"' not in out or 'without-valid-checkpoint' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL controller invented rollback without valid checkpoint')

        # --- MCP surface pinning: order-stable, drift-sensitive, bounded call guard ---
        surface = td/'surface.json'
        surface_same = td/'surface-same.json'
        surface_added = td/'surface-added.json'
        surface_desc = td/'surface-desc.json'
        surface_schema = td/'surface-schema.json'
        tools = [
            {'name': 'read_file', 'description': 'Read a project file', 'inputSchema': {'type': 'object', 'properties': {'path': {'type': 'string'}}, 'required': ['path']}, 'capability_class': 'read'},
            {'name': 'status', 'description': 'Return status', 'inputSchema': {'type': 'object', 'properties': {}}, 'capability_class': 'read'},
        ]
        write_json(surface, {'server_identity': 'fixture-bin-sha256:abc', 'tools': tools})
        write_json(surface_same, {'tools': list(reversed(tools)), 'server_identity': 'fixture-bin-sha256:abc'})
        write_json(surface_added, {'server_identity': 'fixture-bin-sha256:abc', 'tools': tools + [{'name': 'delete_all', 'description': 'Delete data', 'inputSchema': {'type': 'object'}, 'capability_class': 'destructive'}]})
        changed_desc = json.loads(json.dumps(tools)); changed_desc[0]['description'] = 'Read any file on the host'
        write_json(surface_desc, {'server_identity': 'fixture-bin-sha256:abc', 'tools': changed_desc})
        changed_schema = json.loads(json.dumps(tools)); changed_schema[0]['inputSchema']['properties']['path']['description'] = 'May be absolute'
        write_json(surface_schema, {'server_identity': 'fixture-bin-sha256:abc', 'tools': changed_schema})
        run([PY, '.ai/scripts/mcp_surface_pin.py', 'pin', '--server', 'fixture', '--surface', str(surface)], tmp)
        run([PY, '.ai/scripts/mcp_surface_pin.py', 'verify', '--server', 'fixture', '--surface', str(surface_same)], tmp)
        for candidate, marker in [(surface_added, 'tool_added'), (surface_desc, 'description_changed'), (surface_schema, 'input_schema_changed')]:
            out = run([PY, '.ai/scripts/mcp_surface_pin.py', 'verify', '--server', 'fixture', '--surface', str(candidate)], tmp, expect=2)
            if marker not in out:
                raise SystemExit(f'V5.4.2 REGRESSION: FAIL MCP drift missing {marker}')
        args_ok = td/'args-ok.json'; write_json(args_ok, {'path': 'src/main.py'})
        run([PY, '.ai/scripts/mcp_surface_pin.py', 'guard-call', '--server', 'fixture', '--tool', 'read_file', '--arguments', str(args_ok)], tmp)
        args_escape = td/'args-escape.json'; write_json(args_escape, {'path': str(td/'outside.txt')})
        out = run([PY, '.ai/scripts/mcp_surface_pin.py', 'guard-call', '--server', 'fixture', '--tool', 'read_file', '--arguments', str(args_escape)], tmp, expect=2)
        if 'escapes project root' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL MCP absolute path escape was not blocked')
        args_secret = td/'args-secret.json'; write_json(args_secret, {'token': 'fixture-secret'})
        out = run([PY, '.ai/scripts/mcp_surface_pin.py', 'guard-call', '--server', 'fixture', '--tool', 'status', '--arguments', str(args_secret)], tmp, expect=2)
        if 'sensitive argument key' not in out:
            raise SystemExit('V5.4.2 REGRESSION: FAIL MCP sensitive argument was not blocked')

    print('V5.4.2 REGRESSION: PASS - pinned waivers + deterministic control decisions + MCP surface pinning')


if __name__ == '__main__':
    main()
