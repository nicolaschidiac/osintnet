"""Short SQLite transactions, append-only evidence and durable read-only jobs."""
import contextlib
import hashlib
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path

def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)

class Store:
    def __init__(self,root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.blobs=self.root/'blobs';self.blobs.mkdir(exist_ok=True,mode=0o700)
        self.path=self.root/'osintnet.sqlite3'
        with self.db()as c:
            c.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY,label TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 0,state TEXT NOT NULL DEFAULT 'unknown',observed REAL,detail TEXT NOT NULL DEFAULT '{}');
            CREATE TABLE IF NOT EXISTS captures(id INTEGER PRIMARY KEY,case_id TEXT NOT NULL,url TEXT NOT NULL,final_url TEXT NOT NULL,issuer TEXT NOT NULL,captured_at TEXT NOT NULL,status INTEGER NOT NULL,sha256 TEXT NOT NULL,bytes INTEGER NOT NULL,content_type TEXT,previous_hash TEXT NOT NULL,ledger_hash TEXT NOT NULL UNIQUE,metadata TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,capture_id INTEGER NOT NULL UNIQUE REFERENCES captures(id),title TEXT NOT NULL,text TEXT NOT NULL,parser TEXT NOT NULL);
            CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(title,text,content='documents',content_rowid='id');
            CREATE TRIGGER IF NOT EXISTS doc_insert AFTER INSERT ON documents BEGIN INSERT INTO search(rowid,title,text)VALUES(new.id,new.title,new.text); END;
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,at REAL NOT NULL,node TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,case_id TEXT NOT NULL,adapter TEXT NOT NULL REFERENCES nodes(id),input TEXT NOT NULL,idempotency TEXT NOT NULL UNIQUE,input_hash TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'queued',created REAL NOT NULL,updated REAL NOT NULL,lease_until REAL,owner TEXT,attempts INTEGER NOT NULL DEFAULT 0,result TEXT,error TEXT,depends_on TEXT REFERENCES jobs(id));
            CREATE TABLE IF NOT EXISTS entities(id TEXT PRIMARY KEY,case_id TEXT NOT NULL,name TEXT NOT NULL,kind TEXT NOT NULL,identifiers TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS assertions(id TEXT PRIMARY KEY,case_id TEXT NOT NULL,kind TEXT NOT NULL,text TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN('reported','verified','inferred','contradicted','unknown')),capture_id INTEGER REFERENCES captures(id),locator TEXT,limitations TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS edges(id TEXT PRIMARY KEY,case_id TEXT NOT NULL,source TEXT NOT NULL REFERENCES entities(id),target TEXT NOT NULL REFERENCES entities(id),kind TEXT NOT NULL,capture_id INTEGER NOT NULL REFERENCES captures(id),status TEXT NOT NULL,limitations TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS finance(id TEXT PRIMARY KEY,case_id TEXT NOT NULL,year INTEGER NOT NULL,data TEXT NOT NULL,capture_id INTEGER NOT NULL REFERENCES captures(id),basis TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS geo_centers(id TEXT PRIMARY KEY,case_id TEXT NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,radius_m REAL NOT NULL,capture_id INTEGER NOT NULL REFERENCES captures(id),note TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS places(id TEXT PRIMARY KEY,case_id TEXT NOT NULL,provider TEXT NOT NULL,source_id TEXT NOT NULL,name TEXT NOT NULL,category TEXT NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,distance_m REAL NOT NULL,capture_id INTEGER NOT NULL REFERENCES captures(id));
            CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY,role TEXT NOT NULL,expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS rate_limits(key TEXT PRIMARY KEY,at REAL NOT NULL,count INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS workers(adapter TEXT PRIMARY KEY,owner TEXT NOT NULL,heartbeat REAL NOT NULL,started REAL NOT NULL,generation INTEGER NOT NULL,detail TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS events_node_id ON events(node,id);
            CREATE INDEX IF NOT EXISTS jobs_adapter_created ON jobs(adapter,created);
            ''')
            for table in ('captures','events','assertions','edges','finance','documents','geo_centers','places'):
                for op in ('UPDATE','DELETE'):
                    c.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append_only'); END")
            c.execute("INSERT OR IGNORE INTO settings VALUES('running','true')")
        os.chmod(self.path,0o600)

    @contextlib.contextmanager
    def db(self):
        c=sqlite3.connect(self.path,timeout=5);c.row_factory=sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=5000')
        try:
            with c:yield c
        finally:c.close()

    def rows(self,sql,args=()):
        with self.db()as c:return [dict(x)for x in c.execute(sql,args)]

    def event(self,node,kind,payload=None,c=None):
        values=(time.time(),node,kind,encoded(payload or {}))
        if c is not None:return c.execute('INSERT INTO events(at,node,kind,payload) VALUES(?,?,?,?)',values).lastrowid
        with self.db()as c:return self.event(node,kind,payload,c)

    def register(self,manifest):
        with self.db()as c:
            for m in manifest:
                c.execute('INSERT OR IGNORE INTO nodes(id,label)VALUES(?,?)',(m['id'],m['label']))
                c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('worker_generation:'+m['id'],'0'))

    def toggle(self,node,enabled,actor):
        with self.db()as c:
            if c.execute('UPDATE nodes SET enabled=? WHERE id=?',(enabled,node)).rowcount!=1:raise ValueError('unknown_node')
            self.event(node,'enabled'if enabled else'disabled',{'actor':actor},c)

    def observe(self,node,state,detail):
        with self.db()as c:
            c.execute('UPDATE nodes SET state=?,observed=?,detail=?WHERE id=?',(state,time.time(),encoded(detail),node))
            self.event(node,'health',{'state':state,**detail},c)

    def capture(self,raw,case_id,url,final_url,issuer,captured_at,status=200,content_type='',metadata=None,title='',text='',parser='raw-v1'):
        digest=hashlib.sha256(raw).hexdigest();target=self.blobs/digest
        if not target.exists():
            temp=self.blobs/('.'+secrets.token_hex(16))
            try:
                with temp.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
                os.chmod(temp,0o400)
                try:os.link(temp,target)
                except FileExistsError:pass
            finally:temp.unlink(missing_ok=True)
        if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('blob_integrity_error')
        fields=dict(case_id=case_id,url=url,final_url=final_url,issuer=issuer,captured_at=captured_at,status=status,sha256=digest,bytes=len(raw),content_type=content_type,metadata=metadata or {})
        with self.db()as c:
            c.execute('BEGIN IMMEDIATE')
            last=c.execute('SELECT ledger_hash FROM captures ORDER BY id DESC LIMIT 1').fetchone()
            prev=last[0]if last else'0'*64
            ledger=hashlib.sha256((prev+encoded(fields)).encode()).hexdigest()
            cols=list(fields);values=[encoded(v)if k=='metadata'else v for k,v in fields.items()]
            cursor=c.execute(f"INSERT INTO captures({','.join(cols)},previous_hash,ledger_hash)VALUES({','.join('?'for _ in range(len(cols)+2))})",[*values,prev,ledger]);capture_id=cursor.lastrowid
            if text:c.execute('INSERT INTO documents(capture_id,title,text,parser)VALUES(?,?,?,?)',(capture_id,title,text,parser))
            self.event(issuer,'capture',{'capture_id':capture_id,'bytes':len(raw),'sha256':digest},c)
        return capture_id

    def verify(self):
        prev='0'*64;count=0
        for row in self.rows('SELECT * FROM captures ORDER BY id'):
            fields={k:v for k,v in row.items()if k not in('id','previous_hash','ledger_hash')};fields['metadata']=json.loads(fields['metadata'])
            expected=hashlib.sha256((prev+encoded(fields)).encode()).hexdigest()
            if row['previous_hash']!=prev or row['ledger_hash']!=expected:raise ValueError('ledger_integrity_error')
            if hashlib.sha256((self.blobs/row['sha256']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('blob_integrity_error')
            prev=expected;count+=1
        return {'captures':count,'tip':prev,'verified':True}

    def submit(self,case_id,adapter,params,key,depends_on=None,hourly_limit=None):
        payload=encoded(params);digest=hashlib.sha256(encoded([case_id,adapter,params,depends_on]).encode()).hexdigest();now=time.time()
        with self.db()as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT * FROM jobs WHERE idempotency=?',(key,)).fetchone()
            if old:
                if old['input_hash']!=digest:raise ValueError('idempotency_conflict')
                return dict(old)
            if hourly_limit is not None and c.execute('SELECT count(*)FROM jobs WHERE adapter=?AND created>?',(adapter,now-3600)).fetchone()[0]>=hourly_limit:raise ValueError('hourly_job_limit')
            job=secrets.token_hex(12)
            c.execute('INSERT INTO jobs(id,case_id,adapter,input,idempotency,input_hash,created,updated,depends_on)VALUES(?,?,?,?,?,?,?,?,?)',(job,case_id,adapter,payload,key,digest,now,now,depends_on))
            self.event(adapter,'queued',{'job_id':job},c)
            return dict(c.execute('SELECT * FROM jobs WHERE id=?',(job,)).fetchone())

    def claim(self,owner,seconds=90,adapter=None):
        now=time.time()
        with self.db()as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute("SELECT value FROM settings WHERE key='running'").fetchone()[0]!='true':return None
            # All current adapters are GET-only; an expired attempt can be safely retried.
            c.execute("UPDATE jobs SET state='queued',owner=NULL WHERE state='running'AND lease_until<?AND attempts<3",(now,))
            c.execute("UPDATE jobs SET state='failed',error='lease_retries_exhausted',updated=? WHERE state='running'AND lease_until<?AND attempts>=3",(now,now))
            row=c.execute("SELECT j.* FROM jobs j JOIN nodes n ON n.id=j.adapter LEFT JOIN jobs d ON d.id=j.depends_on WHERE j.state='queued'AND n.enabled=1 AND(? IS NULL OR j.adapter=?)AND(j.depends_on IS NULL OR d.state='complete') ORDER BY j.created LIMIT 1",(adapter,adapter)).fetchone()
            if not row:return None
            c.execute("UPDATE jobs SET state='running',owner=?,lease_until=?,updated=?,attempts=attempts+1 WHERE id=?",(owner,now+seconds,now,row['id']))
            self.event(row['adapter'],'running',{'job_id':row['id']},c)
            return dict(c.execute('SELECT * FROM jobs WHERE id=?',(row['id'],)).fetchone())

    def finish(self,job,owner,result=None,error=None):
        with self.db()as c:
            count=c.execute("UPDATE jobs SET state=?,result=?,error=?,updated=?,lease_until=NULL WHERE id=?AND owner=?AND state='running'",('failed'if error else'complete',encoded(result),error,time.time(),job['id'],owner)).rowcount
            if count:self.event(job['adapter'],'failed'if error else'complete',{'job_id':job['id'],'error':error},c)
            return bool(count)

    def search(self,query,case_id,limit=30):
        # Quote tokens so public search input cannot become an FTS expression.
        tokens=query.split()[:12]
        if not tokens:return []
        match=' AND '.join('"'+x.replace('"','""')+'"'for x in tokens)
        return self.rows("SELECT d.capture_id,d.title,snippet(search,1,'[',']','…',28)excerpt,c.url,c.captured_at FROM search JOIN documents d ON d.id=search.rowid JOIN captures c ON c.id=d.capture_id WHERE search MATCH ?AND c.case_id=?ORDER BY rank LIMIT ?",(match,case_id,limit))
