#!/usr/bin/env python3
"""Durable input delivery for one primary agent. Never a progress/evidence store.
Claims are transactional. An ambiguous claimed input BLOCKS a different round;
only an explicit, digest-pinned recovery may replay the input. External side
 effects are NOT exactly-once and must never be automatically replayed.
"""
from __future__ import annotations
import argparse, contextlib, datetime as dt, json, sqlite3, sys, uuid
from pathlib import Path
sys.dont_write_bytecode = True
from _truth import canonical, digest, no_redirect_ancestors, parse_json

MAX_EVENTS=10000
MAX_TEXT_BYTES=16384


@contextlib.contextmanager
def database(path:Path, create=False):
    no_redirect_ancestors(path)
    if not create and not path.exists():
        raise ValueError('operator ledger not found')
    if create:
        path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(str(path),timeout=5,isolation_level=None)
    try:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA journal_mode=DELETE')
        if create and db.execute('PRAGMA user_version').fetchone()[0]==0:
            db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, body TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL)')
            db.execute('PRAGMA user_version=1')
        if db.execute('PRAGMA user_version').fetchone()[0]!=1:
            raise ValueError('unsupported operator ledger schema')
        db.execute('BEGIN IMMEDIATE')
        yield db
        db.commit()
    except BaseException:
        db.rollback(); raise
    finally:
        db.close()


def read_events(db):
    if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
        raise ValueError('operator ledger storage integrity failure')
    rows=db.execute('SELECT seq, body, prev, hash FROM events ORDER BY seq LIMIT ?', (MAX_EVENTS+1,)).fetchall()
    if len(rows)>MAX_EVENTS:
        raise ValueError('operator ledger event budget exceeded')
    previous='0'*64; events=[]; states={}
    for expected,(seq,text,prev,claimed) in enumerate(rows,1):
        body=parse_json(text)
        if seq!=expected or prev!=previous or claimed!=digest({'seq':seq,'prev':prev,'body':body}):
            raise ValueError('operator event chain broken')
        event_id=body.get('event_id'); op=body.get('op')
        if op=='enqueue':
            if event_id in states or not isinstance(body.get('text'),str) or len(body['text'].encode())>MAX_TEXT_BYTES:
                raise ValueError('invalid/duplicate enqueue')
            states[event_id]={'state':'pending','text':body['text'],'event_id':event_id,'sequence':seq,'enqueued_at':body['at']}
        elif op=='claim':
            if event_id not in states or states[event_id]['state']!='pending':
                raise ValueError('invalid claim transition')
            states[event_id].update(state='claimed',round_id=body['round_id'],token=body['token'],claim_hash=claimed)
        elif op in {'ack','recover-ack','recover-replay'}:
            state=states.get(event_id)
            if not state or state['state']!='claimed' or state['token']!=body.get('token'):
                raise ValueError('invalid ack/recovery transition')
            if op.startswith('recover') and (not body.get('reason') or not body.get('approved_by') or body.get('expected_claim_hash')!=state['claim_hash']):
                raise ValueError('unapproved recovery')
            if op=='ack' and body.get('round_id')!=state['round_id']:
                raise ValueError('wrong-round acknowledgement')
            state['state']='pending' if op=='recover-replay' else 'consumed'
        else:
            raise ValueError('unknown operator event operation')
        previous=claimed; events.append({'seq':seq,'body':body,'hash':claimed})
    return events,states


def append(db,events,body):
    if len(events)>=MAX_EVENTS:
        raise ValueError('bounded ledger full: archive outside runtime, do not silently prune')
    seq=len(events)+1; prev=events[-1]['hash'] if events else '0'*64
    body=dict(body,at=dt.datetime.now(dt.timezone.utc).isoformat())
    h=digest({'seq':seq,'prev':prev,'body':body})
    db.execute('INSERT INTO events VALUES (?, ?, ?, ?)',(seq,canonical(body).decode(),prev,h))
    return {'seq':seq,'body':body,'hash':h}


def enqueue(path:Path,text:str,event_id:str):
    if not text.strip() or len(text.encode('utf-8'))>MAX_TEXT_BYTES or not event_id or len(event_id)>128:
        raise ValueError('invalid input size/identity')
    with database(path,create=True) as db:
        events,states=read_events(db)
        if event_id in states:
            if states[event_id]['text']!=text:
                raise ValueError('idempotency identity reused for different input')
            return {'status':'already-recorded','event_id':event_id,'sequence':states[event_id]['sequence']}
        event=append(db,events,{'op':'enqueue','event_id':event_id,'text':text})
        return {'status':'queued','event_id':event_id,'sequence':event['seq']}


def claim(path:Path,round_id:str):
    if not round_id or len(round_id)>128:
        raise ValueError('round identity required')
    with database(path) as db:
        events,states=read_events(db)
        unresolved=[s for s in states.values() if s['state']=='claimed']
        if unresolved:
            existing=unresolved[0]
            if existing['round_id']==round_id:
                return dict(existing,resumed_claim=True)
            raise ValueError('ambiguous-delivery: resolve the prior claimed input before another round')
        pending=[s for s in states.values() if s['state']=='pending']
        if not pending:
            return {'state':'empty'}
        state=min(pending,key=lambda s:s['sequence']); token=uuid.uuid4().hex
        e=append(db,events,{'op':'claim','event_id':state['event_id'],'round_id':round_id,'token':token})
        return dict(state,state='claimed',round_id=round_id,token=token,claim_hash=e['hash'])


def acknowledge(path:Path,event_id:str,round_id:str,token:str,receipt_sha256:str):
    if len(receipt_sha256)!=64 or any(c not in '0123456789abcdef' for c in receipt_sha256):
        raise ValueError('delivery receipt digest required (not product success)')
    with database(path) as db:
        events,states=read_events(db); state=states.get(event_id)
        if not state or state['state']!='claimed' or state['round_id']!=round_id or state['token']!=token:
            raise ValueError('stale/wrong claim acknowledgement')
        append(db,events,{'op':'ack','event_id':event_id,'round_id':round_id,'token':token,'receipt_sha256':receipt_sha256})
        return {'state':'consumed','event_id':event_id,'verified_progress':False}


def recover(path:Path,event_id:str,expected_hash:str,action:str,reason:str,approved_by:str):
    if action not in {'replay','ack'} or not reason.strip() or not approved_by.strip():
        raise ValueError('explicit bounded recovery decision required')
    with database(path) as db:
        events,states=read_events(db); state=states.get(event_id)
        if not state or state['state']!='claimed' or state['claim_hash']!=expected_hash:
            raise ValueError('stale recovery plan')
        append(db,events,{'op':'recover-'+action,'event_id':event_id,'token':state['token'],
                         'expected_claim_hash':expected_hash,'reason':reason,'approved_by':approved_by})
        return {'state':'pending' if action=='replay' else 'consumed','external_side_effect_replay':False}


def status(path:Path):
    if not path.exists():
        return {'status':'not-created','events':0,'verified_progress':False}
    with database(path) as db:
        events,states=read_events(db)
        return {'status':'valid','events':len(events),'head_sha256':events[-1]['hash'] if events else None,
                'counts':{state:sum(s['state']==state for s in states.values()) for state in ('pending','claimed','consumed')},
                'verified_progress':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--db',default=str(Path(__file__).resolve().parents[2]/'.ai/checkpoints/operator-events.sqlite3'))
    sub=ap.add_subparsers(dest='cmd',required=True); sub.add_parser('status')
    p=sub.add_parser('enqueue'); p.add_argument('--text',required=True); p.add_argument('--event-id',required=True)
    p=sub.add_parser('claim'); p.add_argument('--round',required=True)
    p=sub.add_parser('ack'); p.add_argument('--event-id',required=True); p.add_argument('--round',required=True); p.add_argument('--token',required=True); p.add_argument('--receipt-sha256',required=True)
    p=sub.add_parser('recover'); p.add_argument('--event-id',required=True); p.add_argument('--expect-claim-hash',required=True); p.add_argument('--action',choices=['ack','replay'],required=True); p.add_argument('--reason',required=True); p.add_argument('--approved-by',required=True)
    a=ap.parse_args(); path=Path(a.db)
    try:
        if a.cmd=='status': result=status(path)
        elif a.cmd=='enqueue': result=enqueue(path,a.text,a.event_id)
        elif a.cmd=='claim': result=claim(path,a.round)
        elif a.cmd=='ack': result=acknowledge(path,a.event_id,a.round,a.token,a.receipt_sha256)
        else: result=recover(path,a.event_id,a.expect_claim_hash,a.action,a.reason,a.approved_by)
    except (ValueError,OSError,sqlite3.Error,KeyError,TypeError) as exc:
        print(json.dumps({'status':'blocked','reason':str(exc)})); raise SystemExit(1)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
