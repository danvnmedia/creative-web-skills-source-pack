#!/usr/bin/env python3
"""Test the bundled reference MCP response guard, NOT a real host's immunity.
External Codex/Claude/Gemini/Antigravity host abuse checks remain UNVERIFIED.
"""
from __future__ import annotations
import argparse,json,re,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
from _truth import parse_json
from mcp_adversarial_fixture import SCENARIOS


class ResponseGuard:
    def __init__(self,server_identity:str,max_bytes=65536,max_changes=4):
        self.server_identity=server_identity; self.max_bytes=max_bytes; self.max_changes=max_changes
        self.changes=0; self.open_ids={1}; self.tool_ids=set(); self.blocked=False

    def accept(self,raw:bytes):
        if self.blocked: raise ValueError('circuit-open')
        try:
            if len(raw)>self.max_bytes: raise ValueError('response-budget')
            event=parse_json(raw.decode('utf-8'))
            if not isinstance(event,dict) or event.get('jsonrpc')!='2.0': raise ValueError('invalid-envelope')
            if 'method' in event:
                if event.get('method')=='notifications/tools/list_changed' and 'id' not in event:
                    self.changes+=1
                    if self.changes>self.max_changes: raise ValueError('notification-budget')
                    return 'bounded-notification'
                # Inbound requests cannot call host tools, write config or sample.
                raise ValueError('unsolicited-server-request')
            if type(event.get('id')) is not int or event['id'] not in self.open_ids or ('result' in event)==('error' in event):
                raise ValueError('unexpected-response-identity')
            self.open_ids.remove(event['id'])
            result=event.get('result',{})
            if not isinstance(result,dict): raise ValueError('invalid-result')
            tools=result.get('tools',[])
            if not isinstance(tools,list) or len(tools)>128: raise ValueError('tool-count-budget')
            for tool in tools:
                if not isinstance(tool,dict) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}',str(tool.get('name',''))):
                    raise ValueError('non-ascii-or-invalid-tool-identity')
                identity=(self.server_identity,tool['name'])
                if identity in self.tool_ids: raise ValueError('duplicate-tool-identity')
                self.tool_ids.add(identity)
            return 'accepted-as-untrusted-data'
        except (ValueError,UnicodeError,KeyError,TypeError):
            self.blocked=True; raise


def run_suite():
    fixture=Path(__file__).with_name('mcp_adversarial_fixture.py'); results=[]; started=time.monotonic()
    for scenario in SCENARIOS:
        # Only this local fixture may execute. No arbitrary MCP command/URL.
        proc=subprocess.run([sys.executable,'-S',str(fixture),'--scenario',scenario],
             input=b'{"jsonrpc":"2.0","id":0,"method":"initialize"}\n{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n',
             stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3)
        guard=ResponseGuard('local-fixture'); blocked=False; reason=None
        if proc.returncode or len(proc.stdout)>100000:
            raise ValueError('fixture infrastructure failure')
        lines=proc.stdout.splitlines()
        handshake=parse_json(lines.pop(0).decode())
        if handshake.get('id')!=0 or 'result' not in handshake: raise ValueError('invalid fixture handshake')
        for raw in lines:
            try: guard.accept(raw)
            except ValueError as exc: blocked=True; reason=str(exc); break
        ok=(not blocked) if scenario=='benign' else blocked
        results.append({'scenario':scenario,'status':'pass' if ok else 'fail','blocked':blocked,'reason':reason})
    return {'status':'pass' if all(r['status']=='pass' for r in results) else 'fail','scope':'bundled-reference-guard-only',
            'real_host_abuse_verification':'UNVERIFIED','network_used':False,'model_tokens':0,
            'duration_seconds':round(time.monotonic()-started,4),'cases':results}


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--out'); a=ap.parse_args()
    result=run_suite(); text=json.dumps(result,indent=2)+'\n'
    if a.out: Path(a.out).write_text(text,encoding='utf-8')
    print(text,end=''); raise SystemExit(result['status']!='pass')

if __name__=='__main__': main()
