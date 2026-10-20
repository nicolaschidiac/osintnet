import concurrent.futures
import json
import sqlite3
import time
import pytest
from osintnet.store import Store

@pytest.fixture
def store(tmp_path):
    s=Store(tmp_path);s.register([{'id':'one','label':'One'},{'id':'two','label':'Two'}]);return s

def test_atomic_claim_and_adapter_isolation(store):
    store.toggle('one',True,'test');store.toggle('two',True,'test')
    a=store.submit('case','one',{},'first-key');b=store.submit('case','two',{},'second-key')
    store.toggle('one',False,'test')
    with concurrent.futures.ThreadPoolExecutor(8)as pool:
        claims=list(pool.map(lambda i:store.claim(str(i)),range(8)))
    claims=[x for x in claims if x]
    assert len(claims)==1 and claims[0]['id']==b['id']
    assert store.rows('SELECT state FROM jobs WHERE id=?',(a['id'],))[0]['state']=='queued'

def test_idempotency_and_lease_fencing(store):
    store.toggle('one',True,'test')
    a=store.submit('case','one',{'q':'x'},'same-key')
    assert a['id']==store.submit('case','one',{'q':'x'},'same-key')['id']
    with pytest.raises(ValueError,match='idempotency_conflict'):store.submit('case','one',{'q':'y'},'same-key')
    old=store.claim('old')
    with store.db()as c:c.execute('UPDATE jobs SET lease_until=?WHERE id=?',(time.time()-1,a['id']))
    current=store.claim('new')
    assert current['id']==old['id'] and current['attempts']==2
    assert not store.finish(old,'old',result={'bad':True})
    assert store.finish(current,'new',result={'ok':True})

def test_dependencies_and_master_pause(store):
    store.toggle('one',True,'test');first=store.submit('case','one',{},'first-key')
    store.submit('case','one',{},'second-key',first['id'])
    first_claim=store.claim('a');assert first_claim['id']==first['id'];assert store.claim('b')is None
    store.finish(first_claim,'a',result={})
    with store.db()as c:c.execute("UPDATE settings SET value='false'WHERE key='running'")
    assert store.claim('b')is None
    with store.db()as c:c.execute("UPDATE settings SET value='true'WHERE key='running'")
    assert store.claim('b')['depends_on']==first['id']

def test_evidence_is_append_only_and_tamper_detected(store):
    args=dict(case_id='case',url='https://example.org',final_url='https://example.org',issuer='test',captured_at='2026-10-19T00:00:00Z')
    a=store.capture(b'original',**args,title='A',text='source claim with context')
    store.capture(b'original',**args,title='A',text='source claim with context')
    assert len(list(store.blobs.iterdir()))==1
    assert store.verify()['captures']==2
    assert store.search('claim','case')[0]['capture_id']==a
    for table in ['captures','documents','events']:
        with pytest.raises(sqlite3.IntegrityError,match='append_only'):
            with store.db()as c:c.execute(f'DELETE FROM {table}')
    blob=next(store.blobs.iterdir());blob.chmod(0o600);blob.write_bytes(b'changed')
    with pytest.raises(ValueError,match='blob_integrity_error'):store.verify()

def test_search_is_case_scoped_and_fts_operators_literal(store):
    for case in ['a','b']:
        store.capture(case.encode(),case_id=case,url='https://example.org',final_url='https://example.org',issuer='test',captured_at='2026-10-19',title=case,text='context evidence')
    assert len(store.search('evidence','a'))==1
    assert store.search('evidence OR anything','a')==[]

def test_admission_ceiling_is_atomic_and_does_not_break_replay(store):
    def submit(i):
        try:return store.submit('case','one',{},'limited-'+str(i),hourly_limit=3)['id']
        except ValueError as e:
            assert str(e)=='hourly_job_limit'
            return None
    with concurrent.futures.ThreadPoolExecutor(8)as pool:results=list(pool.map(submit,range(8)))
    assert sum(x is not None for x in results)==3
    existing=store.rows('SELECT id,idempotency FROM jobs LIMIT 1')[0]
    assert store.submit('case','one',{},existing['idempotency'],hourly_limit=3)['id']==existing['id']
