#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse, datetime as dt, hashlib, json, os, queue, re, shlex, signal, subprocess, sys, threading, time, uuid
sys.dont_write_bytecode=True
from _common import (
    CHECK_ID_RE, catalog_runner, check_catalog_digest, check_contract_digest, configure_utf8_stdio, evidence_event_id, git_info, harness_context, lifecycle_state_digest,
    load_events, manifest_diff, platform_id, product_source_digest, product_source_manifest, redact,
    resolve_task, root_from_script, runtime_candidate_digest, task_contract_digest,
)

MAX_CAPTURE_BYTES=2_000_000
MAX_LOG_BYTES_DEFAULT=20_000_000


def _safe_id(value:str, kind:str, pattern:re.Pattern[str])->str:
    text=str(value or '').strip()
    if not pattern.fullmatch(text):
        raise SystemExit(f'RECORD EVIDENCE: FAIL — invalid {kind} identity: {text!r}')
    return text


def _classify_failure(code:int, timed_out:bool, output:str)->tuple[str,str|None]:
    if timed_out: return 'blocked','timeout'
    # Output may name expected negative cases or historical failures. Only use
    # keyword heuristics to explain a failed process, never to override exit 0.
    # The caller still enforces mutation and check-specific evidence contracts.
    if code==0: return 'pass',None
    low=output.lower()
    environment_patterns=('command_unavailable','server_identity_mismatch','port_in_use','spawn eperm','permissionerror','sandbox denied','operation not permitted','eacces','browser launch denied')
    external_patterns=('enotfound','econnreset','econnrefused','dns','503 service unavailable','502 bad gateway','upstream timeout')
    security_patterns=('security boundary','policy denied','permission denied by policy')
    if any(x in low for x in environment_patterns): return 'blocked','environment_blocked'
    if any(x in low for x in security_patterns): return 'blocked','security_boundary_failure'
    if any(x in low for x in external_patterns): return 'blocked','external_dependency_failure'
    return 'fail','product_failure'


def _terminate_tree(proc:subprocess.Popen)->None:
    if proc.poll() is not None: return
    try:
        if os.name=='nt':
            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
        else:
            os.killpg(proc.pid,signal.SIGKILL)
    except Exception:
        try: proc.kill()
        except Exception: pass


def _run_stream(cmd:list[str],cwd:Path,timeout:int,log_path:Path,max_log_bytes:int, env_overrides:dict[str,str]|None=None)->tuple[int,str,float,bool,str]:
    child_env=os.environ.copy(); child_env['PYTHONIOENCODING']='utf-8'; child_env['PYTHONUTF8']='1'
    if env_overrides: child_env.update(env_overrides)
    kwargs={}
    if os.name=='nt': kwargs['creationflags']=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)
    else: kwargs['start_new_session']=True
    start=time.monotonic(); timed_out=False; captured=[]; captured_bytes=0; log_bytes=0; digest=hashlib.sha256()
    log_path.parent.mkdir(parents=True,exist_ok=True)
    from command_runtime import resolve_argv
    try:
        executed=resolve_argv(cmd,env=child_env)
        proc=subprocess.Popen(executed,cwd=str(cwd),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=False,env=child_env,**kwargs)
    except (ValueError,OSError) as exc:
        message='COMMAND_UNAVAILABLE: '+str(exc)+'\n'
        log_path.write_bytes(message.encode('utf-8'))
        return 127,message,round(time.monotonic()-start,3),False,hashlib.sha256(message.encode('utf-8')).hexdigest()
    chunks:queue.Queue[bytes|None]=queue.Queue()
    def _reader():
        try:
            if proc.stdout:
                while True:
                    chunk=proc.stdout.read(65536)
                    if not chunk: break
                    chunks.put(chunk)
        finally:
            # The reader owns the pipe: close it on EOF/error before publishing
            # completion. Do not rely on garbage collection to release OS handles.
            try:
                if proc.stdout: proc.stdout.close()
            finally:
                chunks.put(None)
    reader=threading.Thread(target=_reader,daemon=True); reader.start()
    deadline=start+timeout; reader_done=False; parent_exited_at=None
    with log_path.open('wb') as log:
        while True:
            now=time.monotonic()
            if now>deadline and proc.poll() is None:
                timed_out=True; _terminate_tree(proc)
            try: item=chunks.get(timeout=0.1)
            except queue.Empty: item=b''
            if item is None:
                reader_done=True
            elif item:
                digest.update(item)
                if log_bytes<max_log_bytes:
                    take=item[:max(0,max_log_bytes-log_bytes)]; log.write(take); log_bytes+=len(take)
                text=item.decode('utf-8',errors='replace')
                if captured_bytes<MAX_CAPTURE_BYTES:
                    enc=text.encode('utf-8',errors='replace')[:max(0,MAX_CAPTURE_BYTES-captured_bytes)]
                    captured.append(enc.decode('utf-8',errors='replace')); captured_bytes+=len(enc)
            if proc.poll() is not None:
                if parent_exited_at is None: parent_exited_at=time.monotonic()
                if reader_done and chunks.empty(): break
                # A descendant may inherit stdout after the recorded parent exited. Never let
                # that inherited pipe hold evidence capture open indefinitely.
                if time.monotonic()-parent_exited_at>2.0:
                    try:
                        if proc.stdout: proc.stdout.close()
                    except Exception: pass
                    break
        log.flush(); os.fsync(log.fileno())
    try: proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        timed_out=True; _terminate_tree(proc)
        try: proc.wait(timeout=2)
        except Exception: pass
    code=124 if timed_out else int(proc.returncode or 0)
    output=''.join(captured)
    if timed_out: output+='\n[TIMEOUT]\n'
    return code,output,round(time.monotonic()-start,3),timed_out,digest.hexdigest()


def _append_jsonl_locked(path:Path,event:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True); lock=path.with_suffix(path.suffix+'.lock'); deadline=time.monotonic()+10
    fd=None
    while time.monotonic()<deadline:
        try:
            fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY); break
        except FileExistsError: time.sleep(0.02)
    if fd is None: return
    try:
        os.close(fd)
        with path.open('a',encoding='utf-8',newline='\n') as fh:
            fh.write(json.dumps(event,ensure_ascii=False)+'\n'); fh.flush(); os.fsync(fh.fileno())
    finally:
        try: lock.unlink()
        except OSError: pass


def _write_atomic_event(root:Path,event:dict)->Path:
    event_dir=root/'.ai/evidence/events'; event_dir.mkdir(parents=True,exist_ok=True)
    eid=evidence_event_id(event); event['event_id']=eid; final=event_dir/f'{eid}.json'; tmp=event_dir/f'.{eid}.{uuid.uuid4().hex}.tmp'
    data=(json.dumps(event,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    with tmp.open('wb') as fh: fh.write(data); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp,final); return final


def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(description='Run a real verification command and record candidate-bound evidence atomically.')
    ap.add_argument('--task',required=True); ap.add_argument('--check',required=True); ap.add_argument('--timeout',type=int,default=900)
    ap.add_argument('--catalog-runner',help="Trusted CHECK_CATALOG runner id; permits one execution to satisfy the runner's declared checks.")
    ap.add_argument('--max-log-bytes',type=int,default=MAX_LOG_BYTES_DEFAULT)
    ap.add_argument('--allow-workspace-mutation-reason'); ap.add_argument('--ephemeral',action='store_true')
    ap.add_argument('--hypothesis-id'); ap.add_argument('--hard-boundary-breach',action='store_true')
    ap.add_argument('--risk-boundary',choices=['security','data-loss','permission','secret-exposure','production-safety'])
    ap.add_argument('--summary',action='store_true',help='Print one compact human line; legacy JSON remains the default and stored evidence is unchanged.')
    ap.add_argument('command',nargs=argparse.REMAINDER,help='Prefix command with --'); args=ap.parse_args()
    cmd=args.command[1:] if args.command and args.command[0]=='--' else args.command
    if not cmd: ap.error('missing command after --')
    root=root_from_script()
    try: task_path,task=resolve_task(root,args.task)
    except ValueError as exc: raise SystemExit(f'RECORD EVIDENCE: FAIL — {exc}')
    task_id=_safe_id(str(task['id']),'task',re.compile(r'^[A-Z0-9][A-Z0-9._-]{0,127}$'))
    check=_safe_id(args.check,'check',CHECK_ID_RE)
    satisfies_checks=[]; catalog_id=None; catalog_digest=None
    if args.catalog_runner:
        runner=catalog_runner(root,args.catalog_runner)
        if not runner: raise SystemExit(f'RECORD EVIDENCE: FAIL — unknown catalog runner: {args.catalog_runner}')
        if check != str(runner.get('primary_check') or ''):
            raise SystemExit('RECORD EVIDENCE: FAIL — check must equal catalog runner primary_check')
        context=harness_context(root); contexts=runner.get('contexts',[]) or []
        if context not in contexts:
            raise SystemExit(f'RECORD EVIDENCE: FAIL — catalog runner {args.catalog_runner} is not valid in context={context}')
        if platform_id() not in (runner.get('platforms',[]) or []):
            raise SystemExit(f'RECORD EVIDENCE: FAIL — catalog runner {args.catalog_runner} is not valid on {platform_id()}')
        expected=[]
        for token in runner.get('command') or []:
            token=str(token).replace('{python}',sys.executable).replace('{task}',task_id)
            expected.append(token)
        if expected != cmd:
            raise SystemExit('RECORD EVIDENCE: FAIL — command does not match trusted CHECK_CATALOG runner')
        satisfies_checks=[_safe_id(str(x),'check',CHECK_ID_RE) for x in runner.get('checks',[]) if str(x)!=check]
        catalog_id=args.catalog_runner; catalog_digest=check_catalog_digest(root)
    before_manifest=product_source_manifest(root); before=product_source_digest(root); gi=git_info(root)
    ts=dt.datetime.now(dt.timezone.utc); stamp=ts.strftime('%Y%m%dT%H%M%S.%fZ'); nonce=uuid.uuid4().hex[:12]
    log_rel=Path('.ai/evidence/logs')/f'{stamp}-{task_id}-{check}-{nonce}.log'; log_path=(root/log_rel).resolve(); log_root=(root/'.ai/evidence/logs').resolve()
    try: log_path.relative_to(log_root)
    except ValueError: raise SystemExit('RECORD EVIDENCE: FAIL — evidence log escaped log root')
    code,raw_output,duration,timed_out,raw_digest=_run_stream(cmd,root,max(1,args.timeout),log_path,max(1024,args.max_log_bytes))
    # Redact the persisted log after execution while keeping a digest of the raw stream for identity only.
    raw_bytes=log_path.read_bytes(); redacted=redact(raw_bytes.decode('utf-8',errors='replace'))
    log_path.write_text(redacted,encoding='utf-8',newline='\n')
    output=redact(raw_output); output_digest=hashlib.sha256(redacted.encode('utf-8')).hexdigest()
    after_manifest=product_source_manifest(root); after=product_source_digest(root); mutation=manifest_diff(before_manifest,after_manifest)
    mutated=mutation['count']>0; mutation_allowed=bool(args.allow_workspace_mutation_reason)
    evidence_code=code if code!=0 else (3 if mutated and not mutation_allowed else 0)
    status,disposition=_classify_failure(evidence_code,timed_out,output)
    if evidence_code==3: status='fail'; disposition='verification_mutation'
    skill_binding=None
    if check=='skill-eval-live' and status=='pass':
        try:
            from skill_eval_acceptance import command_binding, validate_binding
            skill_binding=command_binding(root,cmd)
            validate_binding(root,skill_binding)
        except (ValueError,OSError,KeyError,TypeError) as exc:
            evidence_code=4; status='fail'; disposition='invalid_skill_runtime_evidence'
            output+='\nSKILL LIVE ACCEPTANCE BLOCKED: '+str(exc)
    failure_signature=None; repeat_count=0; previous_matching=None
    if status!='pass':
        material='\n'.join([check,redact(shlex.join(cmd)),str(code),output_digest]); failure_signature=hashlib.sha256(material.encode()).hexdigest()
        prior=load_events(root/'.ai/evidence/events.jsonl')
        matches=[e for e in prior if e.get('task')==task_id and e.get('check')==check and e.get('failure_signature')==failure_signature]
        repeat_count=len(matches)+1
        if matches: previous_matching=evidence_event_id(matches[-1])
    event={
        'skill_eval_binding':skill_binding,
        'evidence_event_schema_version':2,'timestamp':ts.isoformat(),'task':task_id,
        'task_path':task_path.relative_to(root).as_posix(),'check':check,'status':status,'failure_disposition':disposition,
        'exit_code':evidence_code,'command_exit_code':code,'duration_seconds':duration,'command':redact(shlex.join(cmd)),'git':gi,
        'fingerprint_before':before,'fingerprint_after':after,'product_source_digest':after,
        'task_contract_digest':task_contract_digest(task),'check_contract_digest':check_contract_digest(task,check),'lifecycle_state_digest':lifecycle_state_digest(root,task),'runtime_candidate_digest':runtime_candidate_digest(root,task),
        'workspace_mutated_by_check':mutated,'workspace_mutation':mutation,'workspace_mutation_allowed_reason':args.allow_workspace_mutation_reason,
        'ephemeral':args.ephemeral,'log_path':log_rel.as_posix(),'log':log_rel.as_posix(),
        'output_tail':'\n'.join(output.splitlines()[-40:]),'output_digest':output_digest,'raw_stream_sha256':raw_digest,
        'failure_signature':failure_signature,'same_failure_repeat_count':repeat_count,'previous_matching_event':previous_matching,
        'hypothesis_id':args.hypothesis_id,'hard_boundary_breach':bool(args.hard_boundary_breach),'risk_boundary':args.risk_boundary,
        'producer_kind':'verification-command','producer_exit_status':code,'tool_pair_state':'closed',
        'catalog_runner':catalog_id,'catalog_digest':catalog_digest,'satisfies_checks':satisfies_checks,
        'satisfies_check_contract_digests':{c:check_contract_digest(task,c) for c in satisfies_checks},
    }
    event['event_id']=evidence_event_id(event)
    if not args.ephemeral:
        _write_atomic_event(root,event); _append_jsonl_locked(root/'.ai/evidence/events.jsonl',event)
    else:
        event['ephemeral_log_persisted']=False
    if args.summary:
        sha=str((gi or {}).get('sha') or 'UNKNOWN')
        print(f"{status.upper()} · {check} · {sha} · {duration:.3f}s · {log_rel.as_posix()}")
    else:
        print(json.dumps(event,indent=2,ensure_ascii=False))
    if args.ephemeral:
        try: log_path.unlink(missing_ok=True)
        except OSError: pass
    raise SystemExit(evidence_code)

if __name__=='__main__': main()
