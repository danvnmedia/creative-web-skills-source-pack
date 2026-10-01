"""Small integrity primitives. Hashes prove byte identity, not trusted authorship.
No shell, network, host configuration discovery, or credential copying.
"""
from __future__ import annotations
import contextlib, hashlib, json, os, re, stat, tempfile, time
from pathlib import Path, PurePosixPath

MAX_FILE = 16 * 1024 * 1024
MAX_TREE = 64 * 1024 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key: ' + key)
        out[key] = value
    return out


def parse_json(text):
    def bad(value):
        raise ValueError('non-finite JSON value: ' + value)
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=bad)


def read_json(path: Path, limit=MAX_FILE):
    no_redirect_ancestors(path)
    if path.stat().st_size > limit:
        raise ValueError('JSON exceeds byte budget')
    return parse_json(path.read_bytes().decode('utf-8'))


def sha(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def portable_rel(value: str):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise ValueError('non-portable path')
    p = PurePosixPath(value)
    if p.is_absolute() or p.as_posix() != value or any(x in ('', '.', '..') for x in value.split('/')):
        raise ValueError('unsafe relative path')
    for part in p.parts:
        if part[-1:] in (' ', '.') or any(ord(c) < 32 for c in part):
            raise ValueError('ambiguous path component')
        if re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part, re.I):
            raise ValueError('Windows device path')
    return p


def is_redirect(path: Path):
    st = path.lstat()
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, 'st_file_attributes', 0) & 0x400)


def no_redirect_ancestors(path: Path):
    path = path.absolute()
    for p in (path, *path.parents):
        if (p.exists() or p.is_symlink()) and is_redirect(p):
            raise ValueError('symlink/junction/reparse path rejected: ' + str(p))


def inventory(root: Path, exclude=()):
    """Reject redirects BEFORE any traversal/read; bounds apply even to excluded files."""
    no_redirect_ancestors(root)
    if not root.is_dir():
        raise ValueError('tree root is not a directory')
    out = []; seen = set(); total = 0; entries = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            p = Path(base) / name
            rel = p.relative_to(root).as_posix()
            portable_rel(rel)
            entries += 1
            if entries > 4096:
                raise ValueError('tree entry budget exceeded')
            if rel.casefold() in seen:
                raise ValueError('case-colliding path: ' + rel)
            seen.add(rel.casefold())
            if is_redirect(p):
                raise ValueError('symlink/junction/reparse rejected: ' + rel)
            st = p.stat()
            if stat.S_ISDIR(st.st_mode):
                continue
            if not stat.S_ISREG(st.st_mode):
                raise ValueError('special file rejected: ' + rel)
            total += st.st_size
            if st.st_size > MAX_FILE or total > MAX_TREE:
                raise ValueError('artifact byte budget exceeded')
            if rel not in exclude:
                out.append({'path': rel, 'sha256': sha(p), 'size': st.st_size})
    return sorted(out, key=lambda x: x['path'])


def write_json(path: Path, value, exclusive=False):
    no_redirect_ancestors(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(value) + b'\n'
    if exclusive:
        with path.open('xb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        return
    fd, name = tempfile.mkstemp(prefix='.truth-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def lock(path: Path, timeout=5.0):
    """OS-released advisory lock: a crash cannot leave a stale owned lock."""
    no_redirect_ancestors(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as f:
        f.seek(0, 2)
        if f.tell() == 0:
            f.write(b'0'); f.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                f.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise TimeoutError('exclusive lock unavailable')
                time.sleep(0.02)
        try:
            yield
        finally:
            f.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
