#!/usr/bin/env python3
"""Conservative Windows argv resolution. Never enables a shell for every command."""
from __future__ import annotations
import os
from pathlib import Path
import re
import shutil
import subprocess

BATCH_UNSAFE = re.compile(r'["%!?&|<>^()\r\n\x00]')


def resolve_argv(argv: list[str], *, windows: bool | None = None, env: dict[str,str] | None = None) -> list[str] | str:
    if not argv or any(not isinstance(x,str) or '\x00' in x for x in argv):
        raise ValueError('COMMAND_UNAVAILABLE: a nonempty string argv with no NUL is required')
    windows = os.name == 'nt' if windows is None else windows
    if not windows: return list(argv)
    env = dict(os.environ if env is None else env)
    executable=shutil.which(argv[0], path=env.get('PATH'))
    if executable is None:
        for suffix in ('.exe','.cmd','.bat'):
            if Path(argv[0]).suffix: break
            executable=shutil.which(argv[0]+suffix,path=env.get('PATH'))
            if executable: break
    if executable is None: raise ValueError('COMMAND_UNAVAILABLE: executable not found: '+argv[0])
    suffix=Path(executable).suffix.lower()
    if suffix=='.ps1':
        raise ValueError('COMMAND_UNAVAILABLE: invoke an approved PowerShell host with -File explicitly; Harness will not bypass execution policy')
    if suffix not in ('.cmd','.bat'): return [executable,*argv[1:]]
    # Batch files are parsed by cmd.exe. Refuse ambiguous metacharacters rather
    # than pretend POSIX shlex quoting secures Windows shell arguments.
    values=[executable,*argv[1:]]
    if any(BATCH_UNSAFE.search(x) for x in values):
        raise ValueError('policy denied: ambiguous batch-shell metacharacter; use a verified native executable/direct Node entry point')
    system_root=env.get('SystemRoot') or env.get('WINDIR')
    if not system_root: raise ValueError('COMMAND_UNAVAILABLE: SystemRoot unavailable for explicit batch host')
    cmd=str(Path(system_root)/'System32'/'cmd.exe')
    if not Path(cmd).is_file(): raise ValueError('COMMAND_UNAVAILABLE: system cmd.exe not found')
    payload=subprocess.list2cmdline(values)
    if BATCH_UNSAFE.search(cmd): raise ValueError('policy denied: unsafe system command-host path')
    # Popen on Windows accepts a command-line string with shell=False. Passing
    # this cmd payload through Python list2cmdline a SECOND time would add
    # backslash-escaped quotes that cmd.exe does not interpret like MSVCRT.
    return '"'+cmd+'" /d /s /c "'+payload+'"'
