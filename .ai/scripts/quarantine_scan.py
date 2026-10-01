#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import zipfile
sys.dont_write_bytecode = True

from _common import configure_utf8_stdio, load_json, root_from_script

TEXT_SUFFIXES={'.md','.txt','.json','.jsonc','.yaml','.yml','.toml','.ini','.cfg','.conf','.py','.js','.mjs','.cjs','.ts','.tsx','.jsx','.sh','.bash','.zsh','.ps1','.cmd','.bat','.xml','.html','.css','.env'}
UNICODE_CONTROLS={chr(x) for x in [0x202A,0x202B,0x202C,0x202D,0x202E,0x2066,0x2067,0x2068,0x2069,0x200B,0x200C,0x200D,0x2060,0xFEFF]}
SECRET_PATTERNS=[
    ('private-key',re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----')),
    ('secret-token',re.compile(r'(?i)\b(?:sk-[A-Za-z0-9_-]{16,}|AIza[0-9A-Za-z_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b')),
]
BLOCK_PATTERNS=[
    ('download-pipe-shell',re.compile(r'(?i)\b(?:curl|wget)\b[^\n|]{0,500}\|\s*(?:sh|bash|zsh)\b')),
    ('powershell-download-exec',re.compile(r'(?i)\b(?:iex|invoke-expression)\b[^\n]{0,500}\b(?:iwr|irm|invoke-webrequest|invoke-restmethod)\b|\b(?:iwr|irm)\b[^\n]{0,500}\|\s*(?:iex|invoke-expression)\b')),
    ('root-destructive-delete',re.compile(r'(?i)(?:\brm\s+-rf\s+/(?:\s|$)|\bRemove-Item\b[^\n]{0,120}\b-Recurse\b[^\n]{0,120}\b(?:C:\\\\|/)(?:\s|$))')),
    ('credential-exfiltration',re.compile(r'(?is)(?:os\.environ|process\.env|\$env:|\.ssh|\.aws|credentials|api[_-]?key|secret)[^\n]{0,300}(?:curl|wget|requests\.(?:post|put)|fetch\(|axios\.|Invoke-RestMethod)')),
]
REVIEW_PATTERNS=[
    ('subprocess-or-shell',re.compile(r'(?i)\b(?:subprocess\.|os\.system\(|child_process|execSync\(|spawn\(|shell\s*=\s*True|Start-Process)')),
    ('network-client',re.compile(r'(?i)\b(?:curl|wget|requests\.|urllib\.|fetch\(|axios\.|httpx\.|Invoke-WebRequest|Invoke-RestMethod)')),
    ('package-install',re.compile(r'(?i)\b(?:pip|pipx|npm|pnpm|yarn|bun|uv)\s+(?:install|add)\b')),
    ('sensitive-path-access',re.compile(r'(?i)(?:~[/\\]\.ssh|~[/\\]\.aws|[/\\]\.env\b|[/\\]credentials\b|AppData[/\\]Roaming[/\\].*(?:token|credential))')),
]
INJECTION_PATTERNS=[
    re.compile(r'(?i)\b(?:ignore|disregard|override|forget)\b[^\n]{0,80}\b(?:previous|prior|system|developer|higher[- ]priority)\b[^\n]{0,80}\b(?:instruction|prompt|rule|policy)s?\b'),
    re.compile(r'(?i)\b(?:reveal|print|dump|expose|send)\b[^\n]{0,100}\b(?:system prompt|developer message|secret|credential|api key|environment variable)s?\b'),
]
BASE64_RE=re.compile(r'(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{240,}={0,2}(?![A-Za-z0-9+/=])')
OPAQUE_EXECUTABLE_SUFFIXES={'.pyc','.pyo','.so','.dll','.dylib','.exe','.com','.scr','.msi','.jar','.class','.wasm','.node'}
PYTHON_BLOCK_SINKS={'builtins.exec','builtins.eval'}
PYTHON_REVIEW_SINKS={
    'builtins.compile','os.system','os.popen','subprocess.run','subprocess.Popen','subprocess.call',
    'subprocess.check_call','subprocess.check_output','runpy.run_path','runpy.run_module','importlib.import_module',
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel_safe(name: str) -> tuple[bool,str]:
    raw=name.replace('\\','/')
    p=PurePosixPath(raw)
    if raw.startswith('/') or re.match(r'^[A-Za-z]:/',raw): return False,'absolute-archive-path'
    if any(part in {'..',''} for part in p.parts): return False,'archive-path-traversal'
    return True,p.as_posix()


def add(findings:list[dict],rule:str,severity:str,path:str,detail:str,context_class:str='executable-code'):
    findings.append({'rule':rule,'severity':severity,'path':path,'detail':detail[:300],'context_class':context_class})


def _rule_definition_lines(text:str)->set[int]:
    lines=set()
    try:
        tree=ast.parse(text)
    except SyntaxError:
        return lines
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='re' and node.func.attr=='compile':
            for child in ast.walk(node):
                if hasattr(child,'lineno'):
                    start=getattr(child,'lineno',None); end=getattr(child,'end_lineno',start)
                    if start:
                        lines.update(range(start,(end or start)+1))
    return lines

def _context_for(path:str,text:str,start:int,rule_lines:set[int])->str:
    line=text.count('\n',0,start)+1
    low=path.lower().replace('\\','/')
    if line in rule_lines and Path(path).suffix.lower()=='.py': return 'rule-definition'
    if '/test' in low or '/fixture' in low or Path(path).name.lower().startswith(('test_','fixture_')): return 'test-fixture'
    if low.startswith('docs/') or Path(path).suffix.lower() in {'.md','.txt'}: return 'documentation-example'
    return 'executable-code'



def opaque_executable_kind(path:str,data:bytes) -> str|None:
    """Identify executable/compiled payloads that this static text gate cannot inspect.

    Extension checks catch Python bytecode and common native/JVM/WASM artifacts. A
    small magic check also catches renamed/extensionless native or WASM payloads.
    Detection is intentionally conservative: finding opaque executable content means
    the scan may be useful, but it cannot truthfully claim complete code analysis.
    """
    suffix=Path(path).suffix.lower()
    if suffix in OPAQUE_EXECUTABLE_SUFFIXES:
        return suffix.lstrip('.') or 'compiled'
    head=data[:8]
    if head.startswith(b'\x7fELF'): return 'elf'
    if head.startswith(b'MZ'): return 'pe'
    if head.startswith(b'\x00asm'): return 'wasm'
    if head.startswith(b'\xca\xfe\xba\xbe'): return 'java-class'
    if head[:4] in {b'\xfe\xed\xfa\xce',b'\xfe\xed\xfa\xcf',b'\xce\xfa\xed\xfe',b'\xcf\xfa\xed\xfe'}: return 'mach-o'
    return None


def scan_opaque_executable(path:str,data:bytes,findings:list[dict]) -> None:
    kind=opaque_executable_kind(path,data)
    if kind:
        add(findings,'opaque-executable-artifact','block',path,
            f'opaque executable/compiled artifact ({kind}) cannot be fully inspected by deterministic text/AST analysis')


def _const_string(node:ast.AST) -> str|None:
    if isinstance(node,ast.Constant) and isinstance(node.value,str):
        return node.value
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
        left=_const_string(node.left); right=_const_string(node.right)
        return left+right if left is not None and right is not None else None
    if isinstance(node,ast.JoinedStr):
        values=[]
        for part in node.values:
            if isinstance(part,ast.Constant) and isinstance(part.value,str): values.append(part.value)
            else: return None
        return ''.join(values)
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='join' and len(node.args)==1:
        sep=_const_string(node.func.value)
        seq=node.args[0]
        if sep is not None and isinstance(seq,(ast.List,ast.Tuple)):
            parts=[_const_string(x) for x in seq.elts]
            if all(x is not None for x in parts): return sep.join(parts)  # type: ignore[arg-type]
    return None


class _PythonSinkVisitor(ast.NodeVisitor):
    def __init__(self,path:str,findings:list[dict]):
        self.path=path; self.findings=findings
        self.modules={}
        self.bound:dict[str,tuple[str,bool]]={}

    def visit_Import(self,node:ast.Import):
        for item in node.names:
            if item.name in {'builtins','os','subprocess','runpy','importlib'}:
                self.modules[item.asname or item.name]=item.name
        self.generic_visit(node)

    def visit_ImportFrom(self,node:ast.ImportFrom):
        if node.module in {'builtins','os','subprocess','runpy','importlib'}:
            for item in node.names:
                if item.name!='*': self.bound[item.asname or item.name]=(f'{node.module}.{item.name}',False)
        self.generic_visit(node)

    def _resolve_obj(self,node:ast.AST) -> str|None:
        if isinstance(node,ast.Name):
            return self.modules.get(node.id)
        return None

    def _resolve_func(self,node:ast.AST) -> tuple[str,bool]|None:
        if isinstance(node,ast.Name):
            if node.id in {'exec','eval','compile'}: return (f'builtins.{node.id}',False)
            return self.bound.get(node.id)
        if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name):
            module=self.modules.get(node.value.id)
            if module: return (f'{module}.{node.attr}',False)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='getattr' and len(node.args)>=2:
            module=self._resolve_obj(node.args[0]); attr=_const_string(node.args[1])
            if module and attr: return (f'{module}.{attr}',True)
        return None

    def _record(self,sink:str,reflective:bool):
        if sink in PYTHON_BLOCK_SINKS:
            add(self.findings,'python-reflective-exec' if reflective else 'python-dynamic-exec','block',self.path,
                f'Python execution sink {sink} is reachable' + (' through statically-resolved reflection' if reflective else ''))
        elif sink in PYTHON_REVIEW_SINKS:
            add(self.findings,'python-reflective-runtime-exec' if reflective else 'python-runtime-exec','review',self.path,
                f'Python runtime execution/loading sink {sink} is reachable' + (' through statically-resolved reflection' if reflective else ''))

    def visit_Assign(self,node:ast.Assign):
        resolved=self._resolve_func(node.value)
        if resolved:
            for target in node.targets:
                if isinstance(target,ast.Name): self.bound[target.id]=resolved
        self.generic_visit(node)

    def visit_AnnAssign(self,node:ast.AnnAssign):
        if node.value is not None and isinstance(node.target,ast.Name):
            resolved=self._resolve_func(node.value)
            if resolved: self.bound[node.target.id]=resolved
        self.generic_visit(node)

    def visit_Call(self,node:ast.Call):
        resolved=self._resolve_func(node.func)
        if resolved: self._record(*resolved)
        self.generic_visit(node)


def scan_python_ast(path:str,text:str,findings:list[dict]) -> None:
    if Path(path).suffix.lower()!='.py': return
    try:
        tree=ast.parse(text)
    except SyntaxError as exc:
        add(findings,'python-ast-incomplete','review',path,
            f'Python AST parse failed at line {exc.lineno or 0}; deterministic Python code analysis is incomplete')
        return
    _PythonSinkVisitor(path,findings).visit(tree)

def text_like(path:str,data:bytes,limit:int) -> str|None:
    suffix=Path(path).suffix.lower()
    if len(data)>limit: return None
    if suffix not in TEXT_SUFFIXES and b'\x00' in data[:4096]: return None
    try: return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        try: return data.decode('utf-8')
        except UnicodeDecodeError: return None


def scan_text(path:str,text:str,findings:list[dict]):
    rule_lines=_rule_definition_lines(text) if Path(path).suffix.lower()=='.py' else set()
    scan_python_ast(path,text,findings)
    for rule,pat in SECRET_PATTERNS:
        for match in pat.finditer(text):
            ctx=_context_for(path,text,match.start(),rule_lines); sev='informational' if ctx=='rule-definition' else 'block'
            add(findings,rule,sev,path,'secret-like credential material detected',ctx)
    for rule,pat in BLOCK_PATTERNS:
        for match in pat.finditer(text):
            ctx=_context_for(path,text,match.start(),rule_lines)
            sev='informational' if ctx=='rule-definition' else ('review' if ctx in {'test-fixture','documentation-example'} else 'block')
            add(findings,rule,sev,path,'high-risk executable or exfiltration pattern detected',ctx)
    if Path(path).name.upper() in {'SKILL.MD','AGENTS.MD','CLAUDE.MD','GEMINI.MD','ANTIGRAVITY.MD'}:
        if any(p.search(text) for p in INJECTION_PATTERNS):
            add(findings,'high-confidence-instruction-override','block',path,'instruction surface contains a high-confidence override/exfiltration directive')
    for rule,pat in REVIEW_PATTERNS:
        if pat.search(text): add(findings,rule,'review',path,'capability deserves manual review before install/activation')
    if any(ch in text for ch in UNICODE_CONTROLS): add(findings,'unicode-control','review',path,'contains bidi/zero-width Unicode control characters')
    if BASE64_RE.search(text): add(findings,'encoded-payload','review',path,'contains a long base64-like payload')
    if Path(path).suffix.lower() in {'.json','.jsonc'}:
        try:
            doc=json.loads(text)
        except Exception:
            doc=None
        if isinstance(doc,dict):
            servers=doc.get('mcpServers') or doc.get('mcp_servers')
            if isinstance(servers,dict):
                for name,cfg in servers.items():
                    if isinstance(cfg,dict) and (cfg.get('command') or cfg.get('args')):
                        add(findings,'mcp-command','review',path,f'MCP server {name!r} declares executable command/args; static scan did not run it')


def dir_payload(root:Path,findings:list[dict],limits:dict) -> dict[str,bytes]:
    payload={}; resolved_root=root.resolve(); total=0
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root).as_posix()
        if p.is_symlink():
            try: target=p.resolve()
            except OSError:
                add(findings,'escaping-symlink','block',rel,'broken/unresolvable symlink in untrusted input'); continue
            try: target.relative_to(resolved_root)
            except ValueError: add(findings,'escaping-symlink','block',rel,'symlink resolves outside scanned root')
            continue
        if not p.is_file(): continue
        if len(payload)>=int(limits['max_files']):
            add(findings,'package-size-limit','block',rel,'file count exceeds policy limit'); break
        data=p.read_bytes(); total+=len(data)
        if total>int(limits['max_total_bytes']):
            add(findings,'package-size-limit','block',rel,'total bytes exceed policy limit'); break
        payload[rel]=data
    return payload


def zip_payload(path:Path,findings:list[dict],limits:dict) -> dict[str,bytes]:
    payload={}; total=0
    with zipfile.ZipFile(path) as z:
        infos=[i for i in z.infolist() if not i.is_dir()]
        if len(infos)>int(limits['max_files']): add(findings,'package-size-limit','block',path.name,'archive file count exceeds policy limit')
        for info in infos[:int(limits['max_files'])]:
            ok,name=rel_safe(info.filename)
            if not ok:
                add(findings,name,'block',info.filename,'unsafe archive entry path'); continue
            mode=(info.external_attr>>16)&0xFFFF
            if stat.S_ISLNK(mode):
                add(findings,'archive-symlink','block',name,'symlink entries are rejected in untrusted archives'); continue
            if info.file_size>int(limits['max_archive_entry_bytes']):
                add(findings,'package-size-limit','block',name,'archive entry exceeds uncompressed size limit'); continue
            total+=info.file_size
            if total>int(limits['max_total_bytes']):
                add(findings,'package-size-limit','block',name,'archive total uncompressed bytes exceed policy limit'); break
            if name in payload:
                add(findings,'duplicate-archive-entry','block',name,'duplicate normalized archive entry'); continue
            payload[name]=z.read(info)
    return payload


def content_hash(payload:dict[str,bytes]) -> str:
    h=hashlib.sha256()
    for rel,data in sorted(payload.items()):
        h.update(rel.encode('utf-8')); h.update(b'\0'); h.update(str(len(data)).encode()); h.update(b'\0'); h.update(hashlib.sha256(data).digest())
    return h.hexdigest()


def main():
    configure_utf8_stdio(); root=root_from_script(); policy=load_json(root/'.ai/QUARANTINE_POLICY.json'); limits=policy['limits']
    ap=argparse.ArgumentParser(description='Static pre-install/pre-activation quarantine scanner for Agent Skills, plugin archives, and MCP configs. Never executes scanned MCP commands.')
    ap.add_argument('--target',required=True)
    ap.add_argument('--fail-on',choices=['block','review','never'],default=policy.get('default_fail_on','review'))
    ap.add_argument('--out')
    ap.add_argument('--cache',action='store_true')
    ap.add_argument('--audit-log')
    args=ap.parse_args(); target=Path(args.target).resolve(); findings=[]
    if not target.exists(): raise SystemExit(f'QUARANTINE SCAN: FAIL - target not found: {target}')
    try:
        payload=zip_payload(target,findings,limits) if target.is_file() and target.suffix.lower()=='.zip' else (dir_payload(target,findings,limits) if target.is_dir() else {target.name:target.read_bytes()})
    except (OSError,zipfile.BadZipFile) as exc:
        add(findings,'unreadable-input','block',target.name,str(exc)); payload={}
    for rel,data in payload.items():
        scan_opaque_executable(rel,data,findings)
        text=text_like(rel,data,int(limits['max_text_file_bytes']))
        if text is not None: scan_text(rel,text,findings)
    digest=content_hash(payload)
    counts={sev:sum(1 for x in findings if x['severity']==sev) for sev in ('block','review','informational')}
    incomplete_rules={'package-size-limit','unreadable-input','opaque-executable-artifact','python-ast-incomplete'}
    incomplete=[x for x in findings if x.get('rule') in incomplete_rules]
    analysis_status='complete' if not incomplete else 'partial'
    status='block' if analysis_status!='complete' or counts['block'] else ('review' if counts['review'] else 'pass')
    report={'schema_version':2,'status':status,'analysis_status':analysis_status,'analysis_complete':analysis_status=='complete','scan_mode':'deterministic-static','target':str(target),'content_sha256':digest,'files_scanned':len(payload),'bytes_scanned':sum(map(len,payload.values())),'counts':counts,'incomplete_reasons':[{'rule':x.get('rule'),'path':x.get('path'),'detail':x.get('detail')} for x in incomplete],'findings':findings,'mcp_commands_executed':False,'scanner':'codex-product-harness/quarantine_scan.py'}
    rendered=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if args.out:
        out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(rendered,encoding='utf-8')
    if args.cache:
        cache=root/'.ai/checkpoints/security'/f'{digest}.json'; cache.parent.mkdir(parents=True,exist_ok=True); cache.write_text(rendered,encoding='utf-8')
    if args.audit_log:
        log=Path(args.audit_log); log.parent.mkdir(parents=True,exist_ok=True)
        event={'timestamp':dt.datetime.now(dt.timezone.utc).isoformat(),'content_sha256':digest,'status':status,'counts':counts,'target_name':target.name}
        with log.open('a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
    print(rendered,end='')
    if args.fail_on=='block' and (analysis_status!='complete' or counts['block']): raise SystemExit(1)
    if args.fail_on=='review' and (analysis_status!='complete' or counts['block'] or counts['review']): raise SystemExit(1)

if __name__=='__main__': main()
