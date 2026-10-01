#!/usr/bin/env python3
from pathlib import Path
import argparse, json, urllib.request, urllib.error, time
import sys
sys.dont_write_bytecode = True
from _common import root_from_script, dump_json


def load_urls(path: Path):
    if path.suffix.lower()=='.json':
        data=json.loads(path.read_text(encoding='utf-8'))
        if isinstance(data,dict) and 'urls' in data:
            return [x['url'] if isinstance(x,dict) else x for x in data['urls']]
        if isinstance(data,list): return data
    return [x.strip() for x in path.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#')]

def probe(url, timeout):
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 CodexProductHarness/5','Range':'bytes=0-2047'})
    start=time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {'url':url,'ok':200 <= r.status < 400,'status':r.status,'final_url':r.geturl(),
                    'content_type':r.headers.get('Content-Type'),'content_length':r.headers.get('Content-Length'),
                    'duration_ms':round((time.monotonic()-start)*1000)}
    except urllib.error.HTTPError as e:
        return {'url':url,'ok':False,'status':e.code,'error':str(e),'duration_ms':round((time.monotonic()-start)*1000)}
    except Exception as e:
        return {'url':url,'ok':False,'status':None,'error':str(e),'duration_ms':round((time.monotonic()-start)*1000)}

def main():
    ap=argparse.ArgumentParser(description='Probe a deliberately selected list of critical runtime URLs. Use a small list; do not blindly probe the whole internet.')
    ap.add_argument('--input', required=True)
    ap.add_argument('--out', default='.ai/evidence/url-probe.json')
    ap.add_argument('--timeout',type=float,default=10)
    ap.add_argument('--max',type=int,default=50)
    args=ap.parse_args(); root=root_from_script(); input_path=Path(args.input); input_path=input_path if input_path.is_absolute() else root/input_path; urls=load_urls(input_path)[:args.max]
    results=[probe(u,args.timeout) for u in urls]
    report={'count':len(results),'failed':sum(not x['ok'] for x in results),'results':results}
    out_path=Path(args.out); out_path=out_path if out_path.is_absolute() else root/out_path
    dump_json(out_path,report); print(json.dumps(report,indent=2))
    if report['failed']: raise SystemExit(1)

if __name__=='__main__': main()
