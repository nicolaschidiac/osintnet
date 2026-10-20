import json
import socket
import pytest
from fastapi.testclient import TestClient
from osintnet import network
from osintnet.adapters import validate
from osintnet.auth import hashed

def test_public_dns_rejects_mixed_private_resolution(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(2,1,6,'',('8.8.8.8',443)),(2,1,6,'',('127.0.0.1',443))])
    with pytest.raises(network.FetchError,match='nonpublic_destination'):network.public_addresses('example.org')

@pytest.mark.parametrize('url',['http://example.org','https://user:pass@example.org','https://example.org:8080','https://127.0.0.1/','https://example.org/#fragment'])
def test_unsafe_urls_never_connect(url):
    with pytest.raises(network.FetchError):network.fetch(url,{'example.org'})

def test_redirect_destination_revalidated(monkeypatch):
    monkeypatch.setattr(network,'public_addresses',lambda host:['8.8.8.8'])
    calls=[]
    class Conn:
        def __init__(self,host,*a):calls.append(host)
        def request(self,*a,**k):pass
        def getresponse(self):return self
        status=302
        def getheader(self,key,default=None):return 'https://127.0.0.1/'if key=='Location'else default
        def close(self):pass
    monkeypatch.setattr(network,'PinnedHTTPS',Conn)
    with pytest.raises(network.FetchError,match='destination_not_allowed'):network.fetch('https://example.org/',{'example.org'})
    assert calls==['example.org']

def test_adapter_bounds():
    with pytest.raises(ValueError):validate('overpass',{'latitude':40,'longitude':-73,'radius_m':1700})
    with pytest.raises(ValueError):validate('propublica',{'ein':'123 OR secret'})
    with pytest.raises(ValueError):validate('shodan',{})
    with pytest.raises(ValueError):validate('nyc-socrata',{'dataset':'../../../private'})
    with pytest.raises(ValueError):validate('arcticshift',{'mode':'author','author':'unrelated-user'})
    with pytest.raises(ValueError):validate('arcticshift',{'mode':'posts','ids':['abc']*21})
    with pytest.raises(ValueError):validate('arcticshift',{'mode':'comments','post_id':'abc','limit':1000})
    url,hosts,ceiling=validate('arcticshift',{'mode':'posts','ids':['abc']})
    assert '/api/posts/ids?'in url and hosts=={'arctic-shift.photon-reddit.com'}and ceiling==8_000_000

def test_api_auth_roles_origin_and_no_secrets(tmp_path,monkeypatch):
    monkeypatch.setenv('OSINTNET_ORIGINS','http://testserver')
    from osintnet.app import create_app
    app=create_app(tmp_path)
    app.state.auth.tokens.append({'hash':hashed('analyst-test-key'),'role':'analyst'})
    admin=(tmp_path/'operator.key').read_text().strip()
    with TestClient(app)as client:
        assert client.get('/api/snapshot').status_code==401
        headers={'Authorization':'Bearer analyst-test-key'}
        r=client.get('/api/snapshot',headers=headers);assert r.status_code==200
        assert admin not in r.text and 'operator.key'not in r.text
        assert client.post('/api/control',headers=headers,json={'enabled':False}).status_code==403
        headers={'Authorization':'Bearer '+admin}
        assert client.post('/api/nodes/propublica/toggle',headers=headers,json={'enabled':True}).status_code==200
        assert client.post('/api/nodes/shodan/toggle',headers=headers,json={'enabled':True}).status_code==409
        assert client.get('/api/snapshot',headers={**headers,'Origin':'https://evil.example'}).status_code==403
        assert client.get('/api/snapshot',headers={**headers,'Host':'evil.example'}).status_code==400
        assert client.post('/api/control',headers=headers,json={'enabled':False}).status_code==200
        queued=client.post('/api/jobs',headers=headers,json={'adapter':'propublica','case_id':'example','parameters':{'ein':'123456789'},'idempotency_key':'test-no-network'})
        assert queued.status_code==200 and queued.json()['state']=='queued'
        assert client.get('/api/snapshot',headers=headers).json()['running']is False
        assert client.post('/mcp/',json={'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'1'}}},headers={**headers,'Accept':'application/json, text/event-stream'}).status_code==200
        tools=client.post('/mcp/',json={'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}},headers={**headers,'Accept':'application/json, text/event-stream'})
        assert tools.status_code==200 and {x['name']for x in tools.json()['result']['tools']}=={'network_status','evidence_search','evidence_record','source_query'}

def test_login_csrf_and_session(tmp_path,monkeypatch):
    monkeypatch.setenv('OSINTNET_ORIGINS','http://testserver')
    from osintnet.app import create_app
    app=create_app(tmp_path);key=(tmp_path/'operator.key').read_text().strip()
    with TestClient(app)as client:
        # Chromium can send Origin:null for form POSTs under no-referrer.
        # Keep cross-origin referrers private while permitting same-origin login.
        assert client.get('/login').headers['referrer-policy']=='same-origin'
        assert client.post('/login',data={'key':key},headers={'Origin':'null'}).status_code==403
        assert client.post('/login',data={'key':key}).status_code==403
        r=client.post('/login',data={'key':key},headers={'Origin':'http://testserver'},follow_redirects=False)
        assert r.status_code==303
        assert 'HttpOnly'in r.headers['set-cookie']and 'SameSite=strict'in r.headers['set-cookie']
        assert client.get('/api/snapshot').status_code==200
        assert client.post('/api/control',json={'enabled':False}).status_code==403
        assert client.post('/api/logout',headers={'Origin':'http://testserver'}).status_code==200
        assert client.get('/api/snapshot').status_code==401
