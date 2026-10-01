#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, urllib.parse
import sys
sys.dont_write_bytecode = True
from _common import root_from_script, iter_source_files, dump_json

URL_RE=re.compile(r'https?://[^\s\"\'<>`)\\]+')
DEFAULT_EXT={'.ts','.tsx','.js','.jsx','.mjs','.cjs','.json','.html','.css','.scss','.py','.go','.rs'}

def main():
    ap=argparse.ArgumentParser(description='Discover hard-coded external runtime URLs without crawling the internet.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='.ai/evidence/external-urls.json')
    ap.add_argument('--include-docs', action='store_true')
    args=ap.parse_args(); base=root_from_script(); scan=(base/args.root).resolve()
    exts=set(DEFAULT_EXT)
    if args.include_docs: exts.update({'.md','.mdx','.txt'})
    found={}
    for p in iter_source_files(scan, exts):
        try: text=p.read_text(encoding='utf-8', errors='ignore')
        except OSError: continue
        for i,line in enumerate(text.splitlines(),1):
            for raw in URL_RE.findall(line):
                url=raw.rstrip('.,;:]}')
                host=urllib.parse.urlparse(url).hostname or ''
                if host in {'localhost','127.0.0.1','0.0.0.0'}: continue
                rec=found.setdefault(url, {'url':url,'host':host,'occurrences':[]})
                if len(rec['occurrences'])<20:
                    rec['occurrences'].append({'file':p.relative_to(scan).as_posix(),'line':i})
    result={'count':len(found),'urls':sorted(found.values(), key=lambda x:(x['host'],x['url']))}
    out_path=Path(args.out); out_path=out_path if out_path.is_absolute() else base/out_path
    dump_json(out_path,result)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
