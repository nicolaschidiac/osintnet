"""One adapter per bounded process. No Docker socket or provider secrets."""
import argparse
import json
import os
import re
import resource
import secrets
import signal
import threading
import time
from .adapters import MANIFEST,BY_ID,run
from .network import FetchError
from .store import Store,encoded

def generation(store,adapter):
    return int(store.rows('SELECT value FROM settings WHERE key=?',('worker_generation:'+adapter,))[0]['value'])

def serve(adapter,root):
    if adapter not in BY_ID or BY_ID[adapter].get('pending'):raise ValueError('unsupported_worker')
    store=Store(root);store.register(MANIFEST);stop=threading.Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stop.set())
    owner=f'{os.getpid()}-{secrets.token_hex(8)}';started=time.time();gen=generation(store,adapter)
    def heartbeat():
        usage=resource.getrusage(resource.RUSAGE_SELF)
        with store.db()as c:c.execute('INSERT OR REPLACE INTO workers VALUES(?,?,?,?,?,?)',(adapter,owner,time.time(),started,gen,encoded({'peak_rss_bytes':usage.ru_maxrss*1024,'cpu_seconds':round(time.process_time(),3)})))
    heartbeat();store.event(adapter,'worker_started',{'owner':owner,'generation':gen})
    last=0
    while not stop.is_set()and generation(store,adapter)==gen:
        if time.monotonic()-last>10:heartbeat();last=time.monotonic()
        job=store.claim(owner,seconds=120,adapter=adapter)
        if not job:stop.wait(.5);continue
        try:store.finish(job,owner,result=run(store,job))
        except Exception as e:
            error=str(e)if isinstance(e,(ValueError,FetchError))and re.fullmatch(r'[a-z0-9_]{1,80}',str(e))else'collection_failed'
            store.finish(job,owner,error=error)
        heartbeat()
    store.event(adapter,'worker_stopped',{'owner':owner,'generation':gen})
    with store.db()as c:c.execute('UPDATE workers SET heartbeat=0 WHERE adapter=?AND owner=?',(adapter,owner))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--adapter',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    root=os.getenv('OSINTNET_DATA','private/runtime')
    if a.check:
        rows=Store(root).rows('SELECT heartbeat FROM workers WHERE adapter=?',(a.adapter,))
        raise SystemExit(0 if rows and rows[0]['heartbeat']>time.time()-90 else 1)
    serve(a.adapter,root)
