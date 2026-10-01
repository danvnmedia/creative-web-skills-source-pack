#!/usr/bin/env python3
"""Bounded isolated trace collector and strict Skill activation sensor.
This is filesystem/config isolation, NOT an OS security sandbox. An operator-
reviewed adapter is trusted to capture the host stream, never model self-report.
Unknown host telemetry fails closed rather than borrowing Claude semantics.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, os, queue, re, shutil, signal, subprocess, sys, tempfile, threading, time, uuid
from pathlib import Path
sys.dont_write_bytecode = True
from _truth import canonical, digest, inventory, parse_json, read_json, sha, write_json

STATES = {'TRIGGERED', 'NOT_TRIGGERED', 'INFRA_ERROR', 'ATTRIBUTION_UNCERTAIN'}
MAX_OUTPUT = 2 * 1024 * 1024
MAX_EVENTS = 10000


def classify(raw: bytes, capture: dict, target: str):
    result = {'state': 'ATTRIBUTION_UNCERTAIN', 'target_skill': target, 'activation_event_ids': [],
              'evidence_tier': capture.get('evidence_tier', 'unverified'), 'live_eligible': False}
    if capture.get('returncode') != 0 or capture.get('timed_out') or capture.get('overflow') or not capture.get('stream_closed'):
        return dict(result, state='INFRA_ERROR', reason='process-or-stream-incomplete')
    if capture.get('trace_sha256') != hashlib.sha256(raw).hexdigest():
        return dict(result, state='INFRA_ERROR', reason='trace-digest-mismatch')
    if capture.get('capture_format') != 'claude-stream-json':
        return dict(result, reason='host-has-no-verified-native-skill-sensor')
    if len(raw) > MAX_OUTPUT:
        return dict(result, state='INFRA_ERROR', reason='trace-byte-budget')
    try:
        lines = raw.decode('utf-8').splitlines()
        if len(lines) > MAX_EVENTS:
            raise ValueError('trace-event-budget')
        events = [parse_json(line) for line in lines if line.strip()]
        if any(not isinstance(e, dict) for e in events):
            raise ValueError('trace-event-not-object')
    except (ValueError, UnicodeError) as exc:
        return dict(result, state='INFRA_ERROR', reason=str(exc))
    completed = [e for e in events if e.get('type') == 'result']
    if len(completed) != 1 or completed[0].get('is_error') is not False or events[-1] is not completed[0]:
        return dict(result, state='INFRA_ERROR', reason='missing-or-failed-terminal-result')
    if capture.get('invocation_mode') != 'autonomous':
        return dict(result, reason='forced-or-user-invocation-not-autonomous')
    seen = {}; activated = []
    for event in events:
        # Read ONLY structured native assistant tool-use blocks, never prose,
        # generic file reads, user messages, tool-result text or file-name hints.
        if event.get('type') != 'assistant':
            continue
        message = event.get('message')
        if not isinstance(message, dict) or message.get('role') != 'assistant':
            continue
        if not isinstance(message.get('content',[]),list):
            return dict(result,state='INFRA_ERROR',reason='malformed-assistant-content')
        for block in message.get('content', []):
            if not isinstance(block, dict) or block.get('type') != 'tool_use' or block.get('name') != 'Skill':
                continue
            eid = block.get('id'); inp = block.get('input')
            if not isinstance(eid, str) or not eid or not isinstance(inp, dict):
                return dict(result, reason='native-skill-event-missing-identity')
            if eid in seen and seen[eid] != inp:
                return dict(result, state='INFRA_ERROR', reason='conflicting-event-identity')
            seen[eid] = inp
            if inp.get('skill') == target and eid not in activated:
                activated.append(eid)
    completed_tools={}
    for event in events:
        if event.get('type')!='user': continue
        message=event.get('message')
        if not isinstance(message,dict) or message.get('role')!='user' or not isinstance(message.get('content'),list): continue
        for block in message['content']:
            if not isinstance(block,dict) or block.get('type')!='tool_result': continue
            eid=block.get('tool_use_id')
            if eid not in activated: continue
            if eid in completed_tools and completed_tools[eid]!=block:
                return dict(result,state='INFRA_ERROR',reason='conflicting-skill-tool-result')
            completed_tools[eid]=block
    for eid in activated:
        if eid not in completed_tools or 'content' not in completed_tools[eid]:
            return dict(result,reason='native-skill-request-not-confirmed-complete')
        if completed_tools[eid].get('is_error') is True:
            return dict(result,state='INFRA_ERROR',reason='native-skill-load-failed')
    result.update(state='TRIGGERED' if activated else 'NOT_TRIGGERED', activation_event_ids=activated)
    result['live_eligible'] = capture.get('evidence_tier') == 'live-host-capture' and bool(re.fullmatch(r'[a-f0-9]{64}',str(capture.get('approved_adapter_sha256',''))))
    return result


def terminate(proc):
    try:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, subprocess.TimeoutExpired):
        try:
            proc.kill()
        except OSError:
            pass


def bounded_run(argv, cwd, env, timeout=60, limit=MAX_OUTPUT):
    start = time.monotonic(); q = queue.Queue(maxsize=16); stop = threading.Event(); buffers = [bytearray(), bytearray()]
    flags = {'creationflags': getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)} if os.name == 'nt' else {'start_new_session': True}
    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **flags)
    except OSError as exc:
        return b'', {'returncode': -1, 'timed_out': False, 'overflow': False, 'stream_closed': False, 'error': type(exc).__name__, 'duration_seconds': 0}
    def reader(stream, index):
        try:
            while not stop.is_set():
                chunk = stream.read(4096)
                while not stop.is_set():
                    try:
                        q.put((index, chunk), timeout=.05); break
                    except queue.Full:
                        pass
                if not chunk:
                    break
        finally:
            stream.close()
    threads = [threading.Thread(target=reader, args=(stream, i), daemon=True) for i, stream in enumerate((proc.stdout, proc.stderr))]
    for t in threads:
        t.start()
    closed = set(); timed_out = overflow = False; total = 0
    while len(closed) < 2:
        if time.monotonic() - start > timeout:
            timed_out = True; break
        try:
            i, chunk = q.get(timeout=.02)
        except queue.Empty:
            continue
        if not chunk:
            closed.add(i); continue
        total += len(chunk)
        if total > limit:
            overflow = True; break
        buffers[i].extend(chunk)
    if timed_out or overflow:
        terminate(proc)
    try:
        proc.wait(timeout=max(.1, timeout - (time.monotonic() - start)))
    except subprocess.TimeoutExpired:
        timed_out = True; terminate(proc); proc.wait(timeout=3)
    stop.set()
    for t in threads:
        t.join(timeout=.2)
    return bytes(buffers[0]), {'returncode': proc.returncode, 'timed_out': timed_out, 'overflow': overflow,
            'stream_closed': len(closed) == 2, 'duration_seconds': round(time.monotonic() - start, 4),
            'stderr_sha256': hashlib.sha256(buffers[1]).hexdigest(), 'captured_bytes': total}


def run_case(case, spec, skills_root: Path, output_root: Path, repetition: int, tier='live-host-capture'):
    from _truth import portable_rel
    portable_rel(case['skill'])
    if '/' in case['skill']: raise ValueError('skill identity must be one path component')
    skills = inventory(skills_root)
    run_id = uuid.uuid4().hex
    destination = output_root / run_id
    destination.mkdir(parents=True, exist_ok=False)
    # Every query gets an independent HOME, cwd and native discovery directory.
    # No original project, answer keys, matrix, user config or credentials copied.
    with tempfile.TemporaryDirectory(prefix='cph-trigger-') as td:
        base = Path(td); home = base / 'home'; home.mkdir(); cwd = base / 'work'; cwd.mkdir()
        discovery = cwd / '.claude' / 'skills'
        discovery.mkdir(parents=True)
        selected = skills_root / case['skill']
        if not selected.is_dir():
            raise ValueError('unknown canonical skill')
        shutil.copytree(selected, discovery / case['skill'])
        env = {k:v for k,v in os.environ.items() if k in {'PATH','SystemRoot','SYSTEMROOT','COMSPEC','PATHEXT','WINDIR','LANG'}}
        env.update({'HOME':str(home), 'USERPROFILE':str(home), 'XDG_CONFIG_HOME':str(home/'config'),
                    'XDG_CACHE_HOME':str(home/'cache'), 'XDG_DATA_HOME':str(home/'data'),
                    'CLAUDE_CONFIG_DIR':str(home/'.claude'), 'CODEX_HOME':str(home/'.codex'),
                    'GEMINI_CLI_HOME':str(home/'.gemini'), 'DSH_HOME':str(home/'.dsh'),
                    'PI_CODING_AGENT_DIR':str(home/'.pi'), 'TMP':str(base), 'TEMP':str(base),
                    'TMPDIR':str(base), 'PYTHONIOENCODING':'utf-8', 'PYTHONUTF8':'1', 'PYTHONDONTWRITEBYTECODE':'1'})
        for key in spec.get('pass_env', []):
            if key in env or key.upper() in {'HOME','USERPROFILE','PATH','PYTHONPATH','CLAUDE_CONFIG_DIR','CODEX_HOME','GEMINI_CLI_HOME','DSH_HOME','PI_CODING_AGENT_DIR'}:
                raise ValueError('adapter cannot override isolation environment: ' + key)
            if key in os.environ:
                env[key] = os.environ[key]  # explicit, reviewed opt-in; values never logged
        argv = [s.replace('{prompt}', case['prompt']) for s in spec['argv']]
        raw, capture = bounded_run(argv, cwd, env, timeout=spec.get('timeout_seconds',60))
        capture.update(schema_version=1, collector='cph-owned-subprocess-v1', capture_format=spec['capture_format'],
                       invocation_mode='autonomous', approved_adapter_sha256=digest(spec), evidence_tier=tier,
                       trace_sha256=hashlib.sha256(raw).hexdigest(), case_id=case['id'], run=repetition,
                       prompt_sha256=hashlib.sha256(case['prompt'].encode()).hexdigest(), target_skill=case['skill'],
                       canonical_skills_sha256=digest(skills), isolation_nonce=run_id,
                       isolation_scope='per-query-home-and-project-not-os-sandbox')
        (destination/'trace.jsonl').write_bytes(raw)
        write_json(destination/'capture.json', capture, exclusive=True)
    result = classify(raw,capture,case['skill'])
    return {'case_id':case['id'], 'run':repetition, 'telemetry':'native', 'capture_dir':run_id,
            'capture_sha256':sha(destination/'capture.json'), 'observed_skills':[case['skill']] if result['state']=='TRIGGERED' else [], **result}


def validate_row(row:dict, root:Path, case:dict, skills_root:Path | None=None):
    """Recompute activation from captured bytes; never trust report booleans."""
    from _truth import portable_rel, no_redirect_ancestors
    if not isinstance(row, dict) or not row.get('capture_dir'):
        raise ValueError('missing-host-capture (legacy rows are diagnostic only)')
    portable_rel(row['capture_dir']); directory = root / row['capture_dir']; no_redirect_ancestors(directory)
    if directory.resolve().parent != root.resolve():
        raise ValueError('capture must be an immediate owned run directory')
    inventory(directory)
    if (directory/'trace.jsonl').stat().st_size>MAX_OUTPUT: raise ValueError('trace-byte-budget')
    if sha(directory/'capture.json') != row.get('capture_sha256'):
        raise ValueError('capture-digest-mismatch')
    cap = read_json(directory/'capture.json')
    if cap.get('collector') != 'cph-owned-subprocess-v1' or cap.get('case_id') != case['id'] or cap.get('run') != row.get('run'):
        raise ValueError('capture-identity-mismatch')
    if cap.get('prompt_sha256') != hashlib.sha256(case['prompt'].encode()).hexdigest():
        raise ValueError('prompt-drift')
    if skills_root is not None and cap.get('canonical_skills_sha256') != digest(inventory(skills_root)):
        raise ValueError('skill-revision-drift')
    result = classify((directory/'trace.jsonl').read_bytes(), cap, case['skill'])
    if not result['live_eligible'] or result['state'] not in {'TRIGGERED','NOT_TRIGGERED'}:
        raise ValueError(result.get('reason') or 'not-live-eligible:' + result['state'])
    if row.get('state') != result['state']:
        raise ValueError('derived-state-mismatch')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--adapter',required=True,help='Operator-reviewed JSON argv/capture contract. Never auto-discovered.')
    ap.add_argument('--approve-adapter-sha256',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--workers',type=int,default=1); ap.add_argument('--runs',type=int,default=2)
    args=ap.parse_args(); spec=read_json(Path(args.adapter))
    if digest(spec)!=args.approve_adapter_sha256:
        raise SystemExit('adapter approval digest mismatch')
    if spec.get('capture_format') not in {'claude-stream-json','codex-unverified','antigravity-unverified','gemini-unverified'}:
        raise SystemExit('unsupported capture format')
    if not isinstance(spec.get('argv'),list) or not spec['argv'] or any(not isinstance(x,str) for x in spec['argv']):
        raise SystemExit('argv must be a nonempty string array')
    if not 1<=args.workers<=8 or not 1<=args.runs<=5 or not 1<=spec.get('timeout_seconds',60)<=900:
        raise SystemExit('eval budget exceeded')
    root=Path(__file__).resolve().parents[2]; matrix=read_json(root/'.ai/evals/skill-routing.json')
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    jobs=[(case,n) for case in matrix['cases'] for n in range(1,args.runs+1)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(run_case,c,spec,root/'.agents/skills',out,n) for c,n in jobs]
        rows=[f.result() for f in futures]
    rows.sort(key=lambda x:(x['case_id'],x['run']))
    (out/'runs.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf-8')
    print(json.dumps({'run_count':len(rows),'states':{s:sum(r['state']==s for r in rows) for s in sorted(STATES)},
                      'report':str(out/'runs.jsonl'),'live_success_claim':False},indent=2))
    raise SystemExit(any(not r['live_eligible'] for r in rows))

if __name__=='__main__':
    main()
