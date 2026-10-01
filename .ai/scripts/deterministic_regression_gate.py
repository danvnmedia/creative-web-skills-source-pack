#!/usr/bin/env python3
from __future__ import annotations
import argparse, contextlib, hashlib, json, os, platform, re, subprocess, sys, time
from pathlib import Path
sys.dont_write_bytecode=True
from _common import configure_utf8_stdio, harness_context, harness_version, harness_temp_dir, safe_temp_base
from record_evidence import _run_stream

ROOT=Path(__file__).resolve().parents[2]

def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def discover(root:Path)->list[Path]:
    policy=json.loads((root/'.ai/DETERMINISTIC_E2E_POLICY.json').read_text(encoding='utf-8'))
    found=set()
    for pattern in policy.get('discovery_globs',[]):
        found.update(p for p in root.glob(pattern) if p.is_file())
    excluded=set(policy.get('exclude',[]))
    return sorted((p for p in found if p.relative_to(root).as_posix() not in excluded),key=lambda p:p.as_posix())

def runtime_environment()->dict:
    kernel=platform.release(); system=platform.system()
    kind='windows-native' if sys.platform=='win32' else ('wsl-linux' if system=='Linux' and 'microsoft' in kernel.lower() else 'linux-native' if system=='Linux' else 'macos-native' if system=='Darwin' else 'other')
    return {'kind':kind,'system':system,'kernel':kernel,'os_name':os.name,'python_sys_platform':sys.platform,'is_native_windows_runtime':sys.platform=='win32'}

def _git_probe(root:Path,args:list[str])->dict:
    try:
        p=subprocess.run(['git',*args],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10)
        return {'returncode':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()}
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {'returncode':None,'error':type(exc).__name__}

def _unittest_summary(output:str)->dict:
    # These counts describe only unittest's own explicit summary, never every legacy runner.
    ran=list(re.finditer(r'(?m)^Ran (\d+) tests? in ',output))
    if not ran:return {'known':False,'scope':'no-unittest-summary'}
    tail=output[ran[-1].end():]
    ok=re.search(r'(?m)^OK(?: \(([^\n]*)\))?\s*$',tail)
    if not ok:return {'known':False,'scope':'no-successful-unittest-summary'}
    values=ok.group(1) or '';skip=re.search(r'skipped=(\d+)',values)
    xfail=re.search(r'expected failures=(\d+)',values)
    total=int(ran[-1].group(1));skipped=int(skip.group(1)) if skip else 0;expected=int(xfail.group(1)) if xfail else 0
    return {'known':True,'total':total,'passed':total-skipped-expected,'skipped':skipped,'expected_failures':expected,'scope':'last-unittest-summary-only'}

def run_gate(root:Path, execute:bool=True, temp_root:str|None=None, timeout_seconds:int|None=None)->dict:
    root=root.resolve(); started=time.monotonic(); context=harness_context(root)
    python_path=Path(sys.executable).resolve()
    report={
      'schema_version':2,'status':'NOT_RUN','discovered_count':0,'tests':[],
      'execution_context':context,'required_context':'source',
      'runner_provenance':{'python':sys.version.split()[0],'python_executable':str(python_path),'python_executable_sha256':sha256(python_path) if python_path.is_file() else None,'platform':platform.platform(),'environment':runtime_environment(),'harness_version':harness_version(root),'git_version':_git_probe(root,['--version']),'git_core_autocrlf':_git_probe(root,['config','--get','core.autocrlf'])},
      'live_external_e2e':'NOT_RUN','live_external_e2e_counted_as_pass':False,
      'scope_note':'PASS means every discovered runner exited successfully; reported SKIP is not a passed test. An OS result never establishes another OS result.'
    }
    def finish():
        report['duration_seconds']=round(time.monotonic()-started,4)
        return report
    if context in {'installed','legacy-installed'} and execute:
        report.update(status='BLOCKED',reason_code='SOURCE_ONLY_REGRESSION_SUITE',remediation='Use self_test.py --context installed here. Run this full suite from a separately verified source distribution outside the product tree.')
        return finish()
    tests=discover(root);report['discovered_count']=len(tests)
    policy=json.loads((root/'.ai/DETERMINISTIC_E2E_POLICY.json').read_text(encoding='utf-8'))
    timeout=timeout_seconds if timeout_seconds is not None else int(policy.get('per_runner_timeout_seconds',300))
    if not 1<=timeout<=3600:raise ValueError('per-runner timeout must be between 1 and 3600 seconds')
    if not execute:
        report['tests']=[{'path':p.relative_to(root).as_posix(),'sha256':sha256(p),'status':'NOT_RUN','returncode':None,'duration_seconds':0.0} for p in tests]
        return finish()
    try:
        base=safe_temp_base(root,temp_root,for_copy=True)
    except (OSError,RuntimeError) as exc:
        report.update(status='BLOCKED',reason_code='TEMP_PREFLIGHT_FAILED',detail=str(exc));return finish()
    with harness_temp_dir(root,prefix='regression-suite-',temp_root=str(base),for_copy=True) as scratch:
        overrides={key:str(scratch) for key in ('TMPDIR','TEMP','TMP','HARNESS_TEMP_DIR','HARNESS_TMP')}
        report['scratch']={'base':str(base),'path':str(scratch),'outside_source':True,'child_environment_keys':sorted(overrides),'global_environment_changed':False}
        for path in tests:
            rel=path.relative_to(root).as_posix();row={'path':rel,'sha256':sha256(path),'status':'NOT_RUN','returncode':None,'duration_seconds':0.0}
            log=scratch/(path.stem+'.log')
            try:
                code,output,duration,timed_out,digest=_run_stream([sys.executable,str(path)],root,timeout,log,20_000_000,env_overrides=overrides)
                row.update(status='INFRA_ERROR' if timed_out else 'PASS' if code==0 else 'FAIL',returncode=code,duration_seconds=duration,output_tail=output[-8000:],output_digest=digest,timed_out=timed_out,unittest_summary=_unittest_summary(output))
            except OSError as exc:
                row.update(status='INFRA_ERROR',error=type(exc).__name__,detail=str(exc))
            report['tests'].append(row)
    report['status']='PASS' if report['tests'] and all(r['status']=='PASS' for r in report['tests']) else 'FAIL'
    return finish()

def main():
    configure_utf8_stdio()
    ap=argparse.ArgumentParser(description='Source-only auto-discovered deterministic regressions with copy-safe scratch and explicit OS provenance.')
    ap.add_argument('--list-only',action='store_true');ap.add_argument('--out')
    ap.add_argument('--temp-root',help='Writable scratch base outside the entire Harness source tree. Child-only TEMP/TMP/TMPDIR; no global changes.')
    ap.add_argument('--timeout',type=int,help='Bounded seconds per regression runner (default from policy).')
    a=ap.parse_args()
    try:report=run_gate(ROOT,not a.list_only,a.temp_root,a.timeout)
    except (OSError,ValueError,KeyError) as exc:report={'status':'BLOCKED','reason_code':'PREFLIGHT_FAILED','detail':str(exc)}
    rendered=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(rendered,encoding='utf-8')
    print(rendered,end='')
    if report['status']=='BLOCKED':raise SystemExit(2)
    if not a.list_only and report['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
