"""Small GET adapters. Provider limits and legal interpretation belong in skills."""
import datetime as dt
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.robotparser
from bs4 import BeautifulSoup
from .network import fetch,FetchError

MANIFEST=[
 {'id':'propublica','label':'Nonprofit Explorer','kind':'api','source':'https://projects.propublica.org/nonprofits/api/','auth':None,'interval':2,'budget':'Free public GET; 1 request/job; 8 MB ceiling','capability':'IRS-derived identity and filing summaries'},
 {'id':'web-capture','label':'Website archive','kind':'source','source':'Operator approved public HTTPS hosts','auth':None,'interval':1.2,'budget':'2 requests/job including robots; 8 MB/document','capability':'Public HTML capture and text extraction'},
 {'id':'irs-records','label':'IRS source documents','kind':'source','source':'https://www.irs.gov/charities-non-profits/form-990-series-downloads','auth':None,'interval':2,'budget':'1 request/job; 16 MB ceiling','capability':'Original public IRS XML/PDF/TIFF capture'},
 {'id':'nyc-socrata','label':'NYC Open Data','kind':'api','source':'https://dev.socrata.com/','auth':None,'interval':2,'budget':'100 records/job; explicit dataset ID and offset','capability':'Attributable civic dataset pages'},
 {'id':'overpass','label':'OpenStreetMap places','kind':'api','source':'https://wiki.openstreetmap.org/wiki/Overpass_API','auth':None,'interval':10,'budget':'1 query/job; radius <=1609.344m; 10 MB','capability':'Provider-specific business inventory'},
 {'id':'wayback-cdx','label':'Wayback index','kind':'api','source':'https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server','auth':None,'interval':3,'budget':'100 index rows/job; stop on access/rate errors','capability':'Public archived-URL discovery'},
 {'id':'arcticshift','label':'Arctic Shift','kind':'api','source':'https://github.com/ArthurHeitmann/arctic_shift/blob/master/api/README.md','auth':None,'interval':3,'budget':'One GET/job; <=20 post IDs or <=100 comments; 8 MB','capability':'Public thread records; no user-profile or interaction queries'},
 {'id':'courtlistener','label':'CourtListener MCP','kind':'external','source':'https://mcp.courtlistener.com/','auth':'COURTLISTENER_TOKEN','interval':2,'budget':'Official OAuth enrollment and smoke test pending','capability':'Court search; integration pending','pending':True},
 {'id':'ad-transparency','label':'Advertising libraries','kind':'external','source':'https://adstransparency.google.com/','auth':None,'interval':5,'budget':'Collector terms and live contract review pending','capability':'Public advertiser creatives; integration pending','pending':True},
 {'id':'rotoxy','label':'ROTOXY research','kind':'agent','source':'Local operator bridge','auth':None,'interval':1,'budget':'Explicit bounded research dispatch script','capability':'External-worker observations imported separately','pending':True},
 {'id':'shodan','label':'Existing Shodan MCP','kind':'external','source':'Existing protected endpoint; preserve service','auth':'SHODAN_TOKEN','interval':3,'budget':'Credential rotation/smoke pending; never target scan','capability':'Passive index integration pending','pending':True},
 {'id':'langsmith','label':'LangSmith evaluations','kind':'external','source':'https://docs.langchain.com/langsmith/','auth':'LANGSMITH_API_KEY','interval':3,'budget':'Credit eligibility unknown; no inference or trace exports','capability':'Optional observability; integration pending','pending':True},
]
BY_ID={m['id']:m for m in MANIFEST}
_locks={m['id']:threading.Lock()for m in MANIFEST}
_last={}

def validate(adapter,p):
    if adapter not in BY_ID:raise ValueError('unknown_adapter')
    if BY_ID[adapter].get('pending'):raise ValueError('integration_pending')
    if adapter=='propublica':
        if set(p)!={'ein'}or not re.fullmatch(r'\d{9}',str(p['ein'])):raise ValueError('ein_must_be_nine_digits')
        return f"https://projects.propublica.org/nonprofits/api/v2/organizations/{p['ein']}.json",{'projects.propublica.org'},8_000_000
    if adapter in('web-capture','irs-records'):
        if set(p)!={'url'}or not isinstance(p['url'],str)or len(p['url'])>2048:raise ValueError('url_required')
        hosts={'www.irs.gov','apps.irs.gov'}if adapter=='irs-records'else set(filter(None,os.getenv('OSINTNET_WEB_HOSTS','').split(',')))
        if urllib.parse.urlsplit(p['url']).hostname not in hosts:raise ValueError('host_requires_operator_configuration')
        return p['url'],hosts,16_000_000 if adapter=='irs-records'else 8_000_000
    if adapter=='nyc-socrata':
        if set(p)-{'dataset','query','offset'}or not re.fullmatch(r'[a-z0-9]{4}-[a-z0-9]{4}',str(p.get('dataset',''))):raise ValueError('dataset_id_required')
        offset=p.get('offset',0);query=p.get('query','')
        if type(offset)is not int or not 0<=offset<=10000 or not isinstance(query,str)or len(query)>160:raise ValueError('invalid_query_bounds')
        q={'$limit':100,'$offset':offset}
        if query:q['$q']=query
        return 'https://data.cityofnewyork.us/resource/'+p['dataset']+'.json?'+urllib.parse.urlencode(q),{'data.cityofnewyork.us'},8_000_000
    if adapter=='wayback-cdx':
        if set(p)!={'domain'}or not re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,24}',str(p['domain'])):raise ValueError('domain_required')
        q={'url':p['domain']+'/*','output':'json','filter':'statuscode:200','collapse':'digest','limit':100}
        return 'https://web.archive.org/cdx/search/cdx?'+urllib.parse.urlencode(q),{'web.archive.org'},8_000_000
    if adapter=='arcticshift':
        mode=p.get('mode')
        if mode=='posts':
            if set(p)!={'mode','ids'}or not isinstance(p['ids'],list)or not 1<=len(p['ids'])<=20 or any(not isinstance(x,str)or not re.fullmatch(r'[a-z0-9]{1,12}',x)for x in p['ids']):raise ValueError('bounded_post_ids_required')
            path='/api/posts/ids';q={'ids':','.join(p['ids']),'fields':'id,title,selftext,url,subreddit,created_utc'}
        elif mode=='comments':
            if set(p)-{'mode','post_id','limit'}or not re.fullmatch(r'[a-z0-9]{1,12}',str(p.get('post_id','')))or type(p.get('limit',100))is not int or not 1<=p.get('limit',100)<=100:raise ValueError('bounded_thread_required')
            path='/api/comments/tree';q={'link_id':'t3_'+p['post_id'],'limit':p.get('limit',100),'start_breadth':10,'start_depth':5}
        else:raise ValueError('supported_modes_posts_or_comments')
        return 'https://arctic-shift.photon-reddit.com'+path+'?'+urllib.parse.urlencode(q),{'arctic-shift.photon-reddit.com'},8_000_000
    if adapter=='overpass':
        if set(p)-{'latitude','longitude','radius_m','categories'}or not all(type(p.get(k))in(int,float)for k in('latitude','longitude')):raise ValueError('coordinates_required')
        lat,lon=p['latitude'],p['longitude'];radius=p.get('radius_m',1609.344)
        if not(-90<=lat<=90 and -180<=lon<=180 and type(radius)in(int,float)and 1<=radius<=1609.344):raise ValueError('invalid_radius_or_coordinates')
        categories=p.get('categories',['shop'])
        if not isinstance(categories,list)or not 1<=len(categories)<=3 or any(type(x)is not str or x not in('shop','office','amenity')for x in categories)or len(set(categories))!=len(categories):raise ValueError('supported_place_categories_required')
        clauses=''.join(f'nwr(around:{radius},{lat},{lon})[{category}];'for category in categories)
        query=f'[out:json][timeout:25];({clauses});out center tags;'
        host=os.getenv('OSINTNET_OVERPASS_HOST','overpass.private.coffee')
        if host not in('overpass-api.de','overpass.private.coffee'):raise ValueError('unapproved_overpass_host')
        return 'https://'+host+'/api/interpreter?'+urllib.parse.urlencode({'data':query}),{host},10_000_000
    raise ValueError('integration_pending')

def run(store,job):
    adapter=job['adapter'];params=json.loads(job['input']);url,hosts,ceiling=validate(adapter,params)
    with _locks[adapter]:
        wait=BY_ID[adapter]['interval']-(time.monotonic()-_last.get(adapter,0))
        if wait>0:time.sleep(wait)
        node=store.rows('SELECT enabled FROM nodes WHERE id=?',(adapter,))[0]
        if not node['enabled']:raise FetchError('adapter_disabled')
        store.event(adapter,'request',{'job_id':job['id']})
        try:
            if adapter=='web-capture':
                p=urllib.parse.urlsplit(url);robots_url=f'https://{p.hostname}/robots.txt'
                try:robots_raw,_=fetch(robots_url,hosts,max_bytes=200_000)
                except FetchError as e:
                    if str(e)!='http_404':raise
                    robots_raw=b''
                robots=urllib.robotparser.RobotFileParser();robots.parse(robots_raw.decode(errors='replace').splitlines())
                if not robots.can_fetch('OSINTNET',url):raise FetchError('robots_disallowed')
                delay=robots.crawl_delay('OSINTNET')or robots.crawl_delay('*')or 1.2
                if delay>30:raise FetchError('crawl_delay_requires_scheduled_collection')
                time.sleep(max(delay,1.2))
            raw,meta=fetch(url,hosts,max_bytes=ceiling,timeout=45 if adapter=='overpass'else 25)
            text='';title=url;parser='raw-v1'
            if 'html'in meta['content_type']:
                soup=BeautifulSoup(raw,'html.parser');title=soup.title.get_text()if soup.title else url
                for tag in soup(['script','style']):tag.decompose()
                text=soup.get_text(' ',strip=True);parser='bs4/html.parser-v1'
            elif'json'in meta['content_type']:
                text=json.dumps(json.loads(raw),ensure_ascii=False,indent=2);parser='json-v1'
            capture_id=store.capture(raw,job['case_id'],url,meta['final_url'],adapter,dt.datetime.now(dt.timezone.utc).isoformat(),content_type=meta['content_type'],metadata={'job_id':job['id'],'parameters':params,'latency_ms':meta['latency_ms']},text=text,title=title,parser=parser)
            store.observe(adapter,'healthy',{'latency_ms':meta['latency_ms'],'bytes':len(raw),'capture_id':capture_id})
            return {'capture_id':capture_id,'bytes':len(raw),'latency_ms':meta['latency_ms']}
        except Exception:
            store.observe(adapter,'degraded',{'reason':'collection_failed'});raise
        finally:_last[adapter]=time.monotonic()
