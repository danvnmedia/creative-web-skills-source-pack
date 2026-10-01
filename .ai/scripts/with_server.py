#!/usr/bin/env python3
"""Start an owned local server; refuse occupied ports; optionally observe app identity."""
from __future__ import annotations
import argparse
import json
import os
import shlex
import signal
import socket
import subprocess
import sys
import time
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.parse import urlsplit
sys.dont_write_bytecode = True
from command_runtime import resolve_argv


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host,port),timeout=.25): return True
    except OSError: return False


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None


def identity_matches(url: str, key: str, expected: str) -> bool:
    try:
        # This is a local test probe; never route it through a proxy or redirect.
        with build_opener(ProxyHandler({}),NoRedirect()).open(url,timeout=.8) as response:
            raw=response.read(65_537)
        if len(raw)>65_536: return False
        value=json.loads(raw)
        for part in key.split('.'):
            if not isinstance(value,dict): return False
            value=value[part]
        return isinstance(value,str) and value==expected
    except (OSError,ValueError,KeyError): return False


def wait_port(host,port,timeout):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if port_open(host,port): return True
        time.sleep(.1)
    return False


def stop_process(p):
    if p.poll() is not None: return
    if os.name=='nt':
        subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: p.kill();p.wait(timeout=5)
    else:
        try: os.killpg(p.pid,signal.SIGTERM)
        except ProcessLookupError: return
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try: os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            p.wait(timeout=5)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--server',help='Trusted server command; prefer --server-argv JSON for Windows paths/complex arguments')
    group.add_argument('--server-argv',help='JSON string array, e.g. ["npm","run","dev"]')
    ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--port',required=True,type=int)
    ap.add_argument('--timeout',type=float,default=60)
    ap.add_argument('--identity-path',help='Optional observed JSON endpoint path; no assumed /api/health schema')
    ap.add_argument('--identity-key');ap.add_argument('--identity-value')
    ap.add_argument('command',nargs=argparse.REMAINDER)
    a=ap.parse_args();cmd=a.command[1:] if a.command and a.command[0]=='--' else a.command
    if not cmd: ap.error('missing verification command after --')
    if a.host not in ('127.0.0.1','localhost','::1'): ap.error('owned local-server probes require a loopback host')
    if not 1<=a.port<=65535 or not 0<a.timeout<=900: ap.error('port/timeout outside bounded range')
    identity_args=(a.identity_path is not None,a.identity_key is not None,a.identity_value is not None)
    if any(identity_args) and not all(identity_args): ap.error('identity-path/key/value must be supplied together')
    if a.identity_path:
        u=urlsplit(a.identity_path)
        if not a.identity_path.startswith('/') or u.scheme or u.netloc or u.fragment or len(a.identity_path)>2048:
            ap.error('identity-path must be an in-origin relative path')
        if not a.identity_key or len(a.identity_key)>128 or len(a.identity_key.split('.'))>8:
            ap.error('identity-key must be a bounded JSON object key path')
    # No launch or verification against an already-running unrelated app.
    if port_open(a.host,a.port):
        raise SystemExit(f'PORT_IN_USE: {a.host}:{a.port}; no server/verification launched. Choose an observed free port and update the task runtime target, not just the probe.')
    try:
        if a.server_argv:
            argv=json.loads(a.server_argv)
            if not isinstance(argv,list): raise ValueError('server-argv must be a JSON array')
            server_cmd=resolve_argv(argv);shell=False
        elif os.name=='nt':
            argv=shlex.split(a.server,posix=False)
            argv=[x[1:-1] if len(x)>1 and x[0]==x[-1] and x[0] in ('"',"'") else x for x in argv]
            server_cmd=resolve_argv(argv);shell=False
        else: server_cmd=a.server;shell=True  # Explicit trusted shell-string compatibility.
        verification_cmd=resolve_argv(cmd)
    except (ValueError,OSError) as exc: raise SystemExit('COMMAND_UNAVAILABLE: '+str(exc))
    kwargs={'shell':shell}
    if os.name=='nt':kwargs['creationflags']=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)
    else:kwargs['start_new_session']=True
    server=subprocess.Popen(server_cmd,**kwargs)
    try:
        end=time.monotonic()+a.timeout;ready=False
        host='['+a.host+']' if ':' in a.host else a.host
        url=f'http://{host}:{a.port}'+(a.identity_path or '/')
        while time.monotonic()<end:
            if server.poll() is not None: raise SystemExit('SERVER_EXITED: owned launcher exited before readiness; verification not run')
            if port_open(a.host,a.port) and (not a.identity_path or identity_matches(url,a.identity_key,a.identity_value)):
                ready=True;break
            time.sleep(.1)
        if server.poll() is not None: raise SystemExit('SERVER_EXITED: owned launcher exited before readiness; verification not run')
        if not ready: raise SystemExit('SERVER_IDENTITY_MISMATCH: readiness/declared identity not observed before deadline; no product failure conclusion')
        print('SERVER READY: '+('declared JSON identity matched' if a.identity_path else 'port-only readiness; application identity NOT_VERIFIED'),flush=True)
        p=subprocess.run(verification_cmd);raise SystemExit(p.returncode)
    finally:stop_process(server)

if __name__=='__main__':main()
