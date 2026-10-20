import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from osintnet.store import Store
from osintnet.adapters import MANIFEST
from fastapi.testclient import TestClient

def test_restart_control_is_admin_only_and_records_generation(tmp_path,monkeypatch):
    monkeypatch.setenv('OSINTNET_ORIGINS','http://testserver');monkeypatch.setenv('OSINTNET_WORKERS','0')
    from osintnet.app import create_app
    from osintnet.auth import hashed
    app=create_app(tmp_path);key=(tmp_path/'operator.key').read_text().strip()
    app.state.auth.tokens.append({'hash':hashed('analyst'),'role':'analyst'})
    with TestClient(app)as c:
        assert c.post('/api/nodes/propublica/restart',headers={'Authorization':'Bearer analyst'}).status_code==403
        assert c.post('/api/nodes/propublica/restart',headers={'Authorization':'Bearer '+key}).status_code==200
        assert app.state.store.rows("SELECT value FROM settings WHERE key='worker_generation:propublica'")[0]['value']=='1'
        assert c.post('/api/nodes/shodan/restart',headers={'Authorization':'Bearer '+key}).status_code==409

def eventually(check,seconds=8):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=check()
        if value:return value
        time.sleep(.05)
    raise AssertionError('worker did not reach expected state')

def test_dedicated_claim_cannot_consume_another_adapters_work(tmp_path):
    s=Store(tmp_path);s.register(MANIFEST);s.toggle('propublica',True,'test');s.toggle('irs-records',True,'test')
    s.submit('case','irs-records',{'url':'https://www.irs.gov/'},'first-adapter-job')
    own=s.submit('case','propublica',{'ein':'123456789'},'second-adapter-job')
    assert s.claim('dedicated',adapter='propublica')['id']==own['id']
    assert s.claim('dedicated',adapter='propublica')is None
    assert s.rows("SELECT state FROM jobs WHERE adapter='irs-records'")[0]['state']=='queued'

def test_real_worker_heartbeat_restart_and_other_worker_survival(tmp_path):
    s=Store(tmp_path);s.register(MANIFEST)
    env={**os.environ,'OSINTNET_DATA':str(tmp_path)}
    processes=[]
    try:
        for adapter in ('propublica','irs-records'):
            processes.append(subprocess.Popen([sys.executable,'-m','osintnet.worker','--adapter',adapter],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        eventually(lambda:len(s.rows('SELECT * FROM workers'))==2)
        with s.db()as c:c.execute("UPDATE settings SET value='1'WHERE key='worker_generation:propublica'")
        eventually(lambda:processes[0].poll()is not None)
        assert processes[0].returncode==0 and processes[1].poll()is None
        assert s.rows("SELECT heartbeat FROM workers WHERE adapter='propublica'")[0]['heartbeat']==0
        assert s.rows("SELECT kind FROM events WHERE node='propublica'ORDER BY id DESC LIMIT 1")[0]['kind']=='worker_stopped'
    finally:
        for process in processes:
            if process.poll()is None:process.terminate()
        for process in processes:process.wait(timeout=8)
