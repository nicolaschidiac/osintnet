import hashlib
import hmac
import json
import os
import secrets
import time
from contextvars import ContextVar
from pathlib import Path
import jwt

ROLE=ContextVar('osintnet_role',default='analyst')
RANK={'analyst':1,'operator':2,'admin':3}
def hashed(token):return hashlib.sha256(token.encode()).hexdigest()

class Auth:
    def __init__(self,store):
        self.store=store;self.path=store.root/'auth.json'
        if not self.path.exists():
            key=secrets.token_urlsafe(40)
            with(self.store.root/'operator.key').open('x')as f:f.write(key+'\n')
            os.chmod(self.store.root/'operator.key',0o600)
            with self.path.open('x')as f:json.dump({'tokens':[{'hash':hashed(key),'role':'admin'}]},f)
            os.chmod(self.path,0o600)
        self.tokens=json.loads(self.path.read_text())['tokens']
        self.audience=os.getenv('OSINTNET_ACCESS_AUD','')
        self.issuer=os.getenv('OSINTNET_ACCESS_ISSUER','').rstrip('/')
        if bool(self.audience)!=bool(self.issuer):raise RuntimeError('access_audience_and_issuer_required_together')
        if self.issuer and not(self.issuer.startswith('https://')and self.issuer.endswith('.cloudflareaccess.com')):raise RuntimeError('invalid_access_issuer')
        self.jwks=jwt.PyJWKClient(self.issuer+'/cdn-cgi/access/certs',cache_keys=True)if self.issuer else None

    def role(self,token):
        digest=hashed(token)
        for item in self.tokens:
            if hmac.compare_digest(digest,item['hash'])and item['role']in RANK:return item['role']
        rows=self.store.rows('SELECT role FROM sessions WHERE hash=? AND expires>?',(digest,time.time()))
        return rows[0]['role']if rows else None

    def access(self,token):
        if not self.jwks:return True
        try:
            key=self.jwks.get_signing_key_from_jwt(token)
            jwt.decode(token,key.key,algorithms=['RS256'],audience=self.audience,issuer=self.issuer,options={'require':['exp','iat','aud','iss']})
            return True
        except Exception:return False

    def session(self,role):
        key=secrets.token_urlsafe(32)
        with self.store.db()as c:
            c.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
            c.execute('INSERT INTO sessions VALUES(?,?,?)',(hashed(key),role,time.time()+8*3600))
        return key
