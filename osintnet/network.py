"""HTTPS-only public egress with DNS pinning, redirect validation and byte limits."""
import http.client
import ipaddress
import socket
import ssl
import time
from urllib.parse import urlsplit,urljoin

class FetchError(Exception):pass

def public_addresses(host):
    try:addresses=list(dict.fromkeys(x[4][0]for x in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)))
    except socket.gaierror:raise FetchError('dns_unavailable')from None
    if not addresses or any(not ipaddress.ip_address(x).is_global for x in addresses):raise FetchError('nonpublic_destination')
    return addresses

class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self,host,address,timeout):
        super().__init__(host,timeout=timeout,context=ssl.create_default_context());self.address=address
    def connect(self):
        sock=socket.create_connection((self.address,443),self.timeout)
        try:self.sock=self._context.wrap_socket(sock,server_hostname=self.host)
        except Exception:sock.close();raise

def fetch(url,hosts,max_bytes=8_000_000,timeout=25,max_redirects=4):
    started=time.monotonic();original=url
    for _ in range(max_redirects+1):
        p=urlsplit(url)
        if p.scheme!='https'or p.username or p.password or p.port not in(None,443)or p.fragment or p.hostname not in hosts:raise FetchError('destination_not_allowed')
        address=public_addresses(p.hostname)[0];remaining=timeout-(time.monotonic()-started)
        if remaining<=0:raise FetchError('request_deadline')
        conn=PinnedHTTPS(p.hostname,address,min(remaining,30))
        try:
            conn.request('GET',(p.path or'/')+('?' + p.query if p.query else''),headers={'User-Agent':'OSINTNET/0.1 https://github.com/joeyqleq/osintnet','Accept-Encoding':'identity'})
            res=conn.getresponse()
            if res.status in(301,302,303,307,308):
                location=res.getheader('Location')
                if not location:raise FetchError('invalid_redirect')
                url=urljoin(url,location);continue
            if res.status!=200:raise FetchError(f'http_{res.status}')
            if res.getheader('Content-Encoding','identity')!='identity':raise FetchError('unexpected_content_encoding')
            length=res.getheader('Content-Length')
            if length and int(length)>max_bytes:raise FetchError('response_too_large')
            chunks=[];size=0
            while True:
                if time.monotonic()-started>=timeout:raise FetchError('request_deadline')
                part=res.read(min(65536,max_bytes-size+1))
                if not part:break
                chunks.append(part);size+=len(part)
                if size>max_bytes:raise FetchError('response_too_large')
            return b''.join(chunks),{'url':original,'final_url':url,'content_type':res.getheader('Content-Type',''),'status':res.status,'latency_ms':round((time.monotonic()-started)*1000),'etag':res.getheader('ETag'),'last_modified':res.getheader('Last-Modified')}
        finally:conn.close()
    raise FetchError('redirect_limit')
