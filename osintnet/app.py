"""Authenticated API, MCP and operations console. No model calls on timers."""
import asyncio
import contextlib
import datetime as dt
import json
import os
import re
import shutil
import resource
import socket
import time
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import FileResponse,HTMLResponse,JSONResponse,RedirectResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel,Field,ConfigDict
from .store import Store
from .auth import Auth,ROLE,RANK,hashed
from .adapters import MANIFEST,BY_ID,validate,run
from .network import FetchError

ROOT=Path(__file__).resolve().parent
CASE=re.compile(r'^[a-zA-Z0-9_-]{1,64}$')

class Query(BaseModel):
    model_config=ConfigDict(extra='forbid')
    case_id:str=Field(pattern=CASE.pattern)
    adapter:str=Field(max_length=80)
    parameters:dict
    idempotency_key:str=Field(min_length=8,max_length=128,pattern=r'^[a-zA-Z0-9_.:-]+$')
    depends_on:str|None=None

class Toggle(BaseModel):
    model_config=ConfigDict(extra='forbid')
    enabled:bool

def create_app(data_dir=None):
    store=Store(data_dir or os.getenv('OSINTNET_DATA','private/runtime'));store.register(MANIFEST);auth=Auth(store)
    origins=set(filter(None,os.getenv('OSINTNET_ORIGINS','http://127.0.0.1:8780,http://localhost:8780').split(',')))
    hosts={urlsplit(x).netloc for x in origins}|{'127.0.0.1:8780','localhost:8780'}
    mcp=MCPServer('OSINTNET',version='0.1.0',instructions='Public-source evidence. Reported assertions are not findings. No arbitrary URLs outside adapter allowlists.')
    stopping=asyncio.Event()
    worker_count=int(os.getenv('OSINTNET_WORKERS','2'))
    if not 0<=worker_count<=8:raise ValueError('invalid_worker_count')

    def snapshot():
        nodes=store.rows('SELECT * FROM nodes ORDER BY rowid')
        for n in nodes:
            m=BY_ID[n['id']];n.update({'kind':m['kind'],'capability':m['capability'],'source':m['source'],'budget':m['budget'],'pending':bool(m.get('pending')),'detail':json.loads(n['detail'])})
            n['requests']=store.rows("SELECT count(*)n FROM events WHERE node=?AND kind='request'",(n['id'],))[0]['n']
            n['metrics']=store.rows("SELECT count(*) admitted, sum(state='failed') failed, sum(state='complete') complete FROM jobs WHERE adapter=?AND created>?",(n['id'],time.time()-3600))[0]
            n['metrics']['hourly_ceiling']=100
            n['worker']=None
            if not worker_count and not n['pending']:
                observed=store.rows('SELECT * FROM workers WHERE adapter=?',(n['id'],))
                if observed:
                    n['worker']={**observed[0],'detail':json.loads(observed[0]['detail']),'online':observed[0]['heartbeat']>time.time()-90}
                if n['enabled']and not(n['worker']or{}).get('online'):n['state']='offline'
            n['recent_events']=store.rows('SELECT at,kind,payload FROM events WHERE node=?ORDER BY id DESC LIMIT 8',(n['id'],))
        return {'worker_mode':'shared'if worker_count else'dedicated','worker_count':worker_count,'schema_version':1,'at':time.time(),'running':store.rows("SELECT value FROM settings WHERE key='running'")[0]['value']=='true','nodes':nodes,'jobs':store.rows('SELECT id,case_id,adapter,state,created,updated,attempts,error,result FROM jobs ORDER BY created DESC LIMIT 60'),'counts':{'captures':store.rows('SELECT count(*)n FROM captures')[0]['n'],'documents':store.rows('SELECT count(*)n FROM documents')[0]['n'],'assertions':store.rows('SELECT count(*)n FROM assertions')[0]['n'],'events':store.rows('SELECT count(*)n FROM events')[0]['n']},'host':{'instance':os.getenv('OSINTNET_INSTANCE',socket.gethostname()),'revision':os.getenv('OSINTNET_REVISION','development'),'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'process_cpu_seconds':round(time.process_time(),3),'logical_cpus':os.cpu_count(),'observed_at':time.time()},'disk_free_bytes':shutil.disk_usage(store.root).free,'last_event':store.rows('SELECT coalesce(max(id),0)id FROM events')[0]['id']}

    def submit(q):
        validate(q.adapter,q.parameters)
        if shutil.disk_usage(store.root).free<1_000_000_000:raise ValueError('disk_headroom_required')
        # Atomic new-job ceiling; replaying an existing key does not consume it.
        return store.submit(q.case_id,q.adapter,q.parameters,q.idempotency_key,q.depends_on,hourly_limit=100)

    @mcp.tool()
    def network_status()->dict:
        """Read actual source health, durable jobs and telemetry counts."""
        return snapshot()

    @mcp.tool()
    def evidence_search(case_id:str,query:str)->list[dict]:
        """Search captured documents with exact source IDs and provenance."""
        if not CASE.fullmatch(case_id)or len(query)>200:raise ValueError('invalid_search')
        return store.search(query,case_id)

    @mcp.tool()
    def evidence_record(capture_id:int)->dict:
        """Read one evidence-ledger record; no arbitrary filesystem paths."""
        rows=store.rows('SELECT * FROM captures WHERE id=?',(capture_id,))
        if not rows:raise ValueError('capture_not_found')
        return rows[0]

    @mcp.tool()
    def source_query(case_id:str,adapter:str,parameters:dict,idempotency_key:str)->dict:
        """Queue one bounded, GET-only adapter query; operator/admin required."""
        if RANK.get(ROLE.get(),0)<2:raise ValueError('operator_role_required')
        return submit(Query(case_id=case_id,adapter=adapter,parameters=parameters,idempotency_key=idempotency_key))

    transport=mcp.streamable_http_app(streamable_http_path='/',stateless_http=True,json_response=True,max_request_body_size=65536,transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,allowed_hosts=list(hosts),allowed_origins=list(origins)))

    async def worker(index):
        owner=f'worker-{os.getpid()}-{index}'
        while not stopping.is_set():
            job=store.claim(owner)
            if not job:
                await asyncio.sleep(.5);continue
            try:
                result=await asyncio.to_thread(run,store,job);store.finish(job,owner,result=result)
            except Exception as e:
                error=str(e)if isinstance(e,(ValueError,FetchError))and re.fullmatch(r'[a-z0-9_]{1,80}',str(e))else'collection_failed'
                store.finish(job,owner,error=error)

    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with transport.router.lifespan_context(transport):
            tasks=[asyncio.create_task(worker(i))for i in range(worker_count)]
            store.event('gateway','started',{'workers':worker_count})
            yield
            stopping.set()
            await asyncio.gather(*tasks,return_exceptions=True)
            store.event('gateway','stopped')

    app=FastAPI(title='OSINTNET',version='0.1.0',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.state.store=store;app.state.auth=auth

    @app.middleware('http')
    async def security(request:Request,call_next):
        host=request.headers.get('host','');origin=request.headers.get('origin')
        if host not in hosts:return JSONResponse({'error':'host_not_allowed'},400)
        if origin and origin not in origins:return JSONResponse({'error':'origin_not_allowed'},403)
        path=request.url.path
        if path!='/healthz'and not auth.access(request.headers.get('cf-access-jwt-assertion','')):return JSONResponse({'error':'access_identity_required'},401)
        if request.headers.get('content-length','0').isdigit()and int(request.headers.get('content-length','0'))>65536:return JSONResponse({'error':'request_too_large'},413)
        public=path in('/login','/healthz')or path.startswith('/static/')
        bearer=request.headers.get('authorization','');cookie=request.cookies.get('osintnet_session','')
        token=bearer[7:]if bearer.startswith('Bearer ')else cookie
        role=auth.role(token)if token else None
        if not public and not role:
            if path=='/':return RedirectResponse('/login',303)
            return JSONResponse({'error':'authentication_required'},401)
        if request.method in('POST','PUT','PATCH','DELETE')and not bearer and origin not in origins:return JSONResponse({'error':'same_origin_required'},403)
        request.state.role=role;request.state.actor='key:'+hashed(token)[:12]if token else'none';context=ROLE.set(role or'analyst')
        try:response=await call_next(request)
        finally:ROLE.reset(context)
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'same-origin','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        return response

    def require(request,role):
        if RANK.get(request.state.role,0)<RANK[role]:raise HTTPException(403,'role_required')

    @app.get('/healthz')
    def health():return {'ok':True,'version':'0.1.0'}

    @app.get('/login',response_class=HTMLResponse)
    def login():return FileResponse(ROOT/'web/login.html')

    @app.post('/login')
    async def sign_in(request:Request):
        remote=request.client.host if request.client else'unknown';now=time.time()
        with store.db()as c:
            c.execute('BEGIN IMMEDIATE')
            rate=c.execute('SELECT * FROM rate_limits WHERE key=?',('login:'+remote,)).fetchone()
            if rate and rate['at']>now-900 and rate['count']>=10:raise HTTPException(429,'login_rate_limit')
            n=rate['count']+1 if rate and rate['at']>now-900 else 1
            c.execute('INSERT OR REPLACE INTO rate_limits VALUES(?,?,?)',('login:'+remote,now,n))
        body=await request.body()
        if len(body)>2048:raise HTTPException(413,'request_too_large')
        token=parse_qs(body.decode()).get('key',[''])[0];role=auth.role(token)
        if not role:return HTMLResponse('Key not accepted. <a href="/login">Try again</a>',401)
        response=RedirectResponse('/',303);response.set_cookie('osintnet_session',auth.session(role),httponly=True,secure=bool(auth.audience)or request.url.scheme=='https',samesite='strict',max_age=8*3600)
        return response

    @app.post('/api/logout')
    def logout(request:Request):
        with store.db()as c:c.execute('DELETE FROM sessions WHERE hash=?',(hashed(request.cookies.get('osintnet_session','')),))
        r=JSONResponse({'ok':True});r.delete_cookie('osintnet_session');return r

    @app.get('/')
    def console():return FileResponse(ROOT/'web/index.html')

    @app.get('/api/snapshot')
    def network(request:Request):return {**snapshot(),'role':request.state.role}

    @app.get('/api/events')
    async def events(request:Request,after:int=0):
        if after<0:raise HTTPException(400,'invalid_cursor')
        try:after=max(after,int(request.headers.get('last-event-id','0')))
        except ValueError:raise HTTPException(400,'invalid_cursor')
        async def stream():
            cursor=after;deadline=time.monotonic()+30
            # EventSource reconnects with Last-Event-ID. Bound open streams so
            # graceful server shutdown can finish without losing the cursor.
            while time.monotonic()<deadline and not await request.is_disconnected():
                rows=store.rows('SELECT * FROM events WHERE id>?ORDER BY id LIMIT 100',(cursor,))
                for row in rows:
                    cursor=row['id'];row['payload']=json.loads(row['payload']);yield f"id: {cursor}\ndata: {json.dumps(row)}\n\n"
                if not rows:yield ': heartbeat\n\n'
                await asyncio.sleep(1)
        return StreamingResponse(stream(),media_type='text/event-stream',headers={'X-Accel-Buffering':'no'})

    @app.post('/api/nodes/{node}/toggle')
    def toggle(node:str,body:Toggle,request:Request):
        require(request,'admin')
        if node not in BY_ID:raise HTTPException(404,'node_not_found')
        if body.enabled and BY_ID[node].get('pending'):raise HTTPException(409,'integration_pending')
        store.toggle(node,body.enabled,request.state.actor);return {'ok':True}

    @app.post('/api/nodes/{node}/restart')
    def restart(node:str,request:Request):
        require(request,'admin')
        if node not in BY_ID:raise HTTPException(404,'node_not_found')
        if worker_count or BY_ID[node].get('pending'):raise HTTPException(409,'dedicated_worker_required')
        with store.db()as c:
            c.execute("UPDATE settings SET value=CAST(value AS INTEGER)+1 WHERE key=?",('worker_generation:'+node,))
            store.event(node,'restart_requested',{'actor':request.state.actor},c)
        return {'ok':True,'mode':'drain_then_restart'}

    @app.post('/api/control')
    def control(body:Toggle,request:Request):
        require(request,'admin')
        with store.db()as c:
            c.execute("UPDATE settings SET value=?WHERE key='running'",('true'if body.enabled else'false',));store.event('gateway','up'if body.enabled else'draining',{'actor':request.state.actor},c)
        return {'ok':True,'running':body.enabled}

    @app.post('/api/jobs')
    def queue(body:Query,request:Request):
        require(request,'operator')
        try:return submit(body)
        except ValueError as e:raise HTTPException(409,str(e))from None

    @app.get('/api/search')
    def search(case_id:str,q:str=''):
        if not CASE.fullmatch(case_id)or len(q)>200:raise HTTPException(400,'invalid_search')
        return store.search(q,case_id)

    @app.get('/api/captures/{capture_id}')
    def capture(capture_id:int):
        rows=store.rows('SELECT * FROM captures WHERE id=?',(capture_id,))
        if not rows:raise HTTPException(404,'capture_not_found')
        row=rows[0];row['documents']=store.rows('SELECT title,text,parser FROM documents WHERE capture_id=?',(capture_id,));return row

    @app.get('/api/cases')
    def cases():return store.rows('SELECT case_id,count(*)captures FROM captures GROUP BY case_id')

    @app.get('/api/cases/{case_id}')
    def case(case_id:str):
        if not CASE.fullmatch(case_id):raise HTTPException(400,'invalid_case')
        return {'reports':store.rows("SELECT c.id,d.title,d.text,c.captured_at FROM captures c JOIN documents d ON d.capture_id=c.id WHERE c.case_id=?AND c.issuer='case-analysis' ORDER BY c.id DESC LIMIT 3",(case_id,)),'case_id':case_id,'finance':store.rows('SELECT * FROM finance WHERE case_id=?ORDER BY year',(case_id,)),'assertions':store.rows('SELECT * FROM assertions WHERE case_id=?ORDER BY created',(case_id,)),'entities':store.rows('SELECT * FROM entities WHERE case_id=?',(case_id,)),'edges':store.rows('SELECT * FROM edges WHERE case_id=?',(case_id,)),'geo_centers':store.rows('SELECT * FROM geo_centers WHERE case_id=?ORDER BY created DESC',(case_id,)),'places':store.rows('SELECT * FROM places WHERE case_id=?ORDER BY distance_m',(case_id,)),'captures':store.rows('SELECT id,url,issuer,captured_at,bytes,sha256 FROM captures WHERE case_id=?ORDER BY id DESC LIMIT 500',(case_id,))}

    @app.get('/api/verify')
    def verify(request:Request):
        require(request,'operator');return store.verify()

    app.mount('/static',StaticFiles(directory=ROOT/'web'),name='static')
    app.mount('/mcp',transport)
    return app

app=create_app()
