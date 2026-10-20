#!/usr/bin/env python3
"""Case-specific assembly; the platform itself contains no target identifiers."""
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from bs4 import BeautifulSoup
from osintnet.store import Store,encoded
from osintnet.filings import extract_990
from osintnet.geometry import normalize_places

BASE=Path(__file__).resolve().parents[2];ROOT=BASE/'private/umma';store=Store(BASE/'private/runtime');CASE='umma'

def capture(raw,meta,issuer,title,text='',parser='raw-v1'):
    old=store.rows('SELECT id FROM captures WHERE case_id=?AND sha256=?AND url=?',(CASE,hashlib.sha256(raw).hexdigest(),meta['url']))
    if old:return old[0]['id']
    return store.capture(raw,CASE,meta['url'],meta.get('final_url',meta['url']),issuer,meta['captured_at'],status=meta.get('status',200),content_type=meta.get('content_type',''),metadata={k:v for k,v in meta.items()if k not in('url','final_url','captured_at','status','content_type')},title=title,text=text,parser=parser)

def assertion(key,text,status,capture_id,locator,limitations='',kind='observation'):
    with store.db()as c:c.execute('INSERT OR IGNORE INTO assertions VALUES(?,?,?,?,?,?,?,?,?)',(CASE+':'+key,CASE,kind,text,status,capture_id,locator,limitations,time.time()))

def entity(key,name,kind,identifiers):
    with store.db()as c:c.execute('INSERT OR IGNORE INTO entities VALUES(?,?,?,?,?)',(key,CASE,name,kind,encoded(identifiers)))

ORG='ein:863883211';entity(ORG,'Umma Foundation / OUR UMMA INC','organization',{'ein':'86-3883211'})
primary=[]
for f in sorted((ROOT/'irs/originals').glob('*_public.xml')):
    meta=json.loads(f.with_name(f.name.replace('_public.xml','-meta.json')).read_text());raw=f.read_bytes();data=extract_990(raw)
    if data['ein']!='863883211':raise ValueError('wrong_case_identity')
    cid=capture(raw,meta,'irs-records',f'IRS original Form 990 {data["year"]}',text=json.dumps(data,indent=2),parser='irs-xml-v1')
    primary.append({**data,'capture_id':cid,'source_url':meta['url'],'archive_member':meta['archive_member'],'sha256':meta['sha256']})
    with store.db()as c:c.execute('INSERT OR IGNORE INTO finance VALUES(?,?,?,?,?,?)',(f'umma:irs:{meta["sha256"]}:parser-v2',CASE,data['year'],encoded(data),cid,'IRS original XML; field-level extraction'))
    assertion(f'filing-{data["year"]}',f'The original {data["year"]} Form 990 reports revenue ${data["revenue"]:,}, expenses ${data["expenses"]:,}, and net assets ${data["net_assets"]:,}.','verified',cid,'ReturnData/IRS990: CYTotalRevenueAmt, CYTotalExpensesAmt, NetAssetsOrFundBalancesEOYAmt','Verified as a filing disclosure, not an independent audit of underlying transactions.')
    for person in data['officers']:
        if not person['name']:continue
        pid='role-person:'+hashlib.sha256((ORG+person['name']).encode()).hexdigest()[:20]
        entity(pid,person['name'],'public_officer',{'identity_scope':'name and role within this EIN; no kinship inference'})
        with store.db()as c:c.execute('INSERT OR IGNORE INTO edges VALUES(?,?,?,?,?,?,?,?)',(f'{CASE}:officer:{pid}:{data["year"]}',CASE,ORG,pid,'lists_officer',cid,'filing-reported',f'{data["year"]}: {person["title"]}; compensation categories are filing disclosures.'))

# Preserve renderer bytes (some are gzip); derived text is explicitly labeled.
ledger=ROOT/'filings/ledger.jsonl'
for line in ledger.read_text().splitlines():
    meta=json.loads(line);f=ROOT/'filings'/meta['file']
    if not f.exists()or'-IRS'not in f.name:continue
    raw=f.read_bytes();body=gzip.GzipFile(fileobj=io.BytesIO(raw)).read(8_000_001)if raw.startswith(b'\x1f\x8b')else raw
    if len(body)>8_000_000:raise ValueError('decompression_limit')
    text=BeautifulSoup(body,'html.parser').get_text(' ',strip=True)
    meta['content_encoding']='gzip'if raw.startswith(b'\x1f\x8b')else'identity'
    capture(raw,meta,'propublica',f.name,text=text,parser='gzip+bs4-v1'if raw.startswith(b'\x1f\x8b')else'bs4-v1')

source=store.rows('SELECT id FROM captures WHERE case_id=?AND url=?ORDER BY id LIMIT 1',(CASE,'https://ummafoundation.org/campaigns/in-the-middle-of-war-hashem-built-a-classroom'))
if source:assertion('hashem-context','The cited campaign identifies Hashem as an English teacher in Gaza. This occurrence does not establish religious authorship.','verified',source[0]['id'],'Campaign body: teacher description','Does not validate the campaign beneficiary or every other occurrence of the name.','correction')
source=store.rows('SELECT id FROM captures WHERE case_id=?AND url=?ORDER BY id LIMIT 1',(CASE,'https://ummafoundation.org/disclosure/financial-disclosure'))
if source:assertion('audits','The financial-disclosure page says the organization conducts regular independent audits and makes reports public.','reported',source[0]['id'],'Financial Transparency / Regular Audits','The archived page does not by itself supply an independent audit; no conclusion that an audit does not exist.')
for f in primary:
    if f['advertising']is not None:
        pct=f['advertising']/f['expenses']*100
        assertion(f'advertising-{f["year"]}',f'The {f["year"]} return reports ${f["advertising"]:,} in advertising, {pct:.2f}% of total expenses; the reported advertising is classified as program services.','verified',f['capture_id'],'ReturnData/IRS990/AdvertisingGrp; TotalFunctionalExpensesGrp','Classification is reported by the filer. Its correctness and advertising purpose require supporting workpapers and campaign evidence.')

geo=ROOT/'geo';geocode=json.loads((geo/'geocode.json').read_text())[0];lat,lon=float(geocode['lat']),float(geocode['lon']);meta=json.loads((geo/'geocode-meta.json').read_text());cid=capture((geo/'geocode.json').read_bytes(),meta,'overpass','OSM geocode: advertised office',text=json.dumps(geocode),parser='nominatim-json-v1')
with store.db()as c:c.execute('INSERT OR IGNORE INTO geo_centers VALUES(?,?,?,?,?,?,?,?)',('umma:office-center:20261019',CASE,lat,lon,1609.344,cid,'Advertised contact-address point from Nominatim; does not verify tenancy, occupancy or operational headquarters.',time.time()))
all_places=[];seen=set();coverage=[]
for category in ['shop','office','amenity']:
    datafile=geo/(category+'-response.json');metafile=geo/(category+'-meta.json')
    if not datafile.exists()or not metafile.exists():continue
    meta=json.loads(metafile.read_text());raw=datafile.read_bytes();data=json.loads(raw);cid=capture(raw,meta,'overpass','OSM one-mile '+category+' inventory',text='',parser='overpass-json-v1')
    rows=normalize_places(data.get('elements',[]),lat,lon);coverage.append({'category':category,'returned':len(data.get('elements',[])),'inside_by_centroid':len(rows),'capture_id':cid})
    for row in rows:
        if row['source_id']in seen:continue
        seen.add(row['source_id']);all_places.append({**row,'capture_id':cid})
        with store.db()as c:c.execute('INSERT OR IGNORE INTO places VALUES(?,?,?,?,?,?,?,?,?,?)',('umma:osm:'+row['source_id'],CASE,row['provider'],row['source_id'],row['name'],row['category'],row['latitude'],row['longitude'],row['distance_m'],cid))

(ROOT/'financial-panel.json').write_text(json.dumps(primary,indent=2));(geo/'coverage.json').write_text(json.dumps({'center':[lat,lon],'radius_m':1609.344,'coverage':coverage,'unique_places':len(all_places),'limits':'OSM shop inventory currently available; office/amenity query failures are gaps. Not all businesses; centroid-based boundary; no verified organizational relationship inferred.','attribution':'© OpenStreetMap contributors, ODbL 1.0'},indent=2))
with(ROOT/'financial-panel.csv').open('w',newline='')as f:
    fields=['year','revenue','expenses','net_assets','program_expenses','management_expenses','fundraising_expenses','advertising','advertising_program','government_grants','foreign_grants','capture_id','source_url','archive_member','sha256'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(sorted(primary,key=lambda x:x['year']))
if all_places:
    with(geo/'directory.csv').open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(all_places[0]));w.writeheader();w.writerows(all_places)
print(json.dumps({'primary_returns':len(primary),'places':len(all_places),'ledger':store.verify()}))
