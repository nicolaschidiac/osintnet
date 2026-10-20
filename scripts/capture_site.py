#!/usr/bin/env python3
"""Bounded public-site snapshot; no browser, forms, credentials or cross-site crawl."""
import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup

def capture(origin, output, maximum=300, delay=1.2):
    root=Path(output); root.mkdir(parents=True,exist_ok=True,mode=0o700)
    ua='OSINTNET/0.1 (bounded public-source archival research)'
    records=[]; done=set()
    if (root/'ledger.jsonl').exists():
        records=[json.loads(x) for x in (root/'ledger.jsonl').read_text().splitlines()]
        done={x['url'] for x in records if x.get('status')==200}
    def get(url):
        if urllib.parse.urlsplit(url).netloc!=urllib.parse.urlsplit(origin).netloc:
            raise ValueError('cross_origin_refused')
        req=urllib.request.Request(url,headers={'User-Agent':ua})
        class Redirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,req,fp,code,msg,headers,newurl):
                if urllib.parse.urlsplit(newurl).netloc!=urllib.parse.urlsplit(origin).netloc:
                    raise ValueError('cross_origin_redirect_refused')
                return super().redirect_request(req,fp,code,msg,headers,newurl)
        with urllib.request.build_opener(Redirect()).open(req,timeout=25)as res:
            raw=res.read(8_000_001)
            if len(raw)>8_000_000:raise ValueError('response_too_large')
            digest=hashlib.sha256(raw).hexdigest(); blob=root/digest
            if not blob.exists():
                with blob.open('xb')as f:f.write(raw)
            rec={'url':url,'final_url':res.url,'captured_at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':res.status,'sha256':digest,'bytes':len(raw),'content_type':res.headers.get('Content-Type'),'etag':res.headers.get('ETag'),'last_modified':res.headers.get('Last-Modified')}
        with(root/'ledger.jsonl').open('a')as f:f.write(json.dumps(rec)+'\n')
        return raw,rec
    robots_raw,_=get(origin+'/robots.txt'); robots=urllib.robotparser.RobotFileParser(); robots.parse(robots_raw.decode().splitlines())
    crawl_delay=robots.crawl_delay(ua) or robots.crawl_delay('*') or 0
    delay=max(delay,crawl_delay)
    sitemap,_=get(origin+'/sitemap.xml')
    urls=[origin+'/']+[x.text for x in ET.fromstring(sitemap).iter()if x.tag.endswith('loc')]
    urls=list(dict.fromkeys(urls)); (root/'routes.json').write_text(json.dumps(urls,indent=2))
    count=0
    for url in urls[:maximum]:
        if url in done:continue
        if not robots.can_fetch(ua,url):
            with(root/'failures.jsonl').open('a')as f:f.write(json.dumps({'url':url,'error':'robots_disallowed'})+'\n')
            continue
        time.sleep(delay)
        try:
            raw,rec=get(url); soup=BeautifulSoup(raw,'html.parser')
            for el in soup(['script','style','nav','footer']):el.decompose()
            text=soup.get_text(' ',strip=True)
            links=sorted({urllib.parse.urljoin(url,x['href'])for x in soup.select('a[href]')})
            derived={'source_sha256':rec['sha256'],'url':url,'title':soup.title.get_text()if soup.title else None,'text':text,'links':links,'parser':'bs4/html.parser-v1'}
            with(root/'pages.jsonl').open('a')as f:f.write(json.dumps(derived)+'\n')
            count+=1
            if count%20==0:print(json.dumps({'captured':count,'total_routes':len(urls)}),flush=True)
        except Exception as e:
            code=e.code if isinstance(e,urllib.error.HTTPError)else None
            with(root/'failures.jsonl').open('a')as f:f.write(json.dumps({'url':url,'error':type(e).__name__,'status':code,'captured_at':dt.datetime.now(dt.timezone.utc).isoformat()})+'\n')
            if code in (401,403,429):
                print(json.dumps({'stopped':'access_or_rate_limit','status':code}),flush=True);break
    print(json.dumps({'done':True,'captured':count,'routes':len(urls)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('origin');p.add_argument('output');p.add_argument('--maximum',type=int,default=300)
    a=p.parse_args();capture(a.origin.rstrip('/'),a.output,a.maximum)
