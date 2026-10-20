#!/usr/bin/env python3
"""Retrieve one original IRS XML from a public ZIP using verified byte ranges.

Avoids downloading gigabyte bundles. Refuses servers that ignore Range requests.
"""
import argparse
import datetime as dt
import hashlib
import io
import json
import re
import urllib.request
import urllib.parse
import zipfile
from pathlib import Path

class RemoteZIP(io.RawIOBase):
    def __init__(self,url,output,budget=32_000_000):
        if urllib.parse.urlsplit(url).hostname!='apps.irs.gov'or not url.startswith('https://apps.irs.gov/pub/epostcard/990/xml/'):raise ValueError('official_irs_zip_required')
        self.url=url;self.output=Path(output);self.output.mkdir(parents=True,exist_ok=True,mode=0o700);self.budget=budget;self.used=0;self.pos=0;self.cache=[];self.receipts=[]
        data,header=self.request('bytes=-65557');match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',header)
        if not match:raise ValueError('invalid_content_range')
        start,end,self.size=map(int,match.groups());self.cache.append((start,end+1,data))
    def request(self,byte_range):
        req=urllib.request.Request(self.url,headers={'Range':byte_range,'User-Agent':'OSINTNET/0.1 https://github.com/joeyqleq/osintnet','Accept-Encoding':'identity'})
        with urllib.request.urlopen(req,timeout=30)as r:
            if r.status!=206:raise ValueError('range_not_supported')
            content_range=r.headers.get('Content-Range','');match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',content_range)
            if not match:raise ValueError('invalid_content_range')
            start,end,total=map(int,match.groups());length=end-start+1
            if self.used+length>self.budget:raise ValueError('range_budget_exceeded')
            b=r.read(length+1)
            if len(b)!=length:raise ValueError('range_length_mismatch')
        self.used+=length;digest=hashlib.sha256(b).hexdigest();target=self.output/f'range-{start}-{end}-{digest}'
        if not target.exists():target.write_bytes(b)
        self.receipts.append({'start':start,'end':end,'sha256':digest,'file':target.name})
        return b,content_range
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        if pos<0:raise ValueError('negative_seek')
        self.pos=pos;return pos
    def read(self,n=-1):
        if n<0:n=self.size-self.pos
        n=min(n,self.size-self.pos)
        if n<=0:return b''
        start=self.pos;end=start+n
        if n>self.budget-self.used:raise ValueError('range_budget_exceeded')
        for low,high,data in self.cache:
            if low<=start and end<=high:self.pos=end;return data[start-low:end-low]
        data,header=self.request(f'bytes={start}-{end-1}')
        if not header.startswith(f'bytes {start}-{end-1}/'):raise ValueError('wrong_range')
        self.cache.append((start,end,data));self.pos=end;return data

def extract(url,object_id,output):
    if not re.fullmatch(r'\d{18}',object_id):raise ValueError('object_id_required')
    remote=RemoteZIP(url,output)
    with zipfile.ZipFile(remote)as z:
        matches=[i for i in z.infolist()if Path(i.filename).name==object_id+'_public.xml']
        if len(matches)!=1:raise ValueError('object_not_in_this_batch')
        info=matches[0]
        if info.file_size>8_000_000 or info.compress_size>4_000_000:raise ValueError('xml_size_limit')
        raw=z.read(info)  # zipfile verifies the member CRC.
    p=Path(output);name=object_id+'_public.xml';(p/name).write_bytes(raw)
    meta={'url':url,'final_url':url,'file':name,'captured_at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':200,'sha256':hashlib.sha256(raw).hexdigest(),'content_type':'application/xml','archive_member':info.filename,'archive_bytes':remote.size,'retrieved_bytes':remote.used,'member_crc32':info.CRC,'ranges':remote.receipts}
    (p/(object_id+'-meta.json')).write_text(json.dumps(meta,indent=2));print(json.dumps({k:v for k,v in meta.items()if k!='ranges'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('object_id');p.add_argument('output');a=p.parse_args();extract(a.url,a.object_id,a.output)
