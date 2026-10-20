#!/usr/bin/env python3
"""Import dated local captures without substituting summaries for primary evidence."""
import argparse
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from osintnet.store import Store,encoded
from osintnet.adapters import MANIFEST

def import_case(store,case,root,bootstrap):
    store.register(MANIFEST);added=0
    pages={x['source_sha256']:x for x in map(json.loads,(root/'site/pages.jsonl').read_text().splitlines())}
    for lane,issuer in [(root/'site','web-capture'),(root/'filings','irs-records'),(bootstrap,'propublica')]:
        ledger=lane/'ledger.jsonl'
        if not ledger.exists():continue
        for line in ledger.read_text().splitlines():
            rec=json.loads(line);raw_path=lane/rec.get('file',rec['sha256'])
            if not raw_path.exists():continue
            if store.rows('SELECT id FROM captures WHERE case_id=?AND url=?AND sha256=?',(case,rec['url'],rec['sha256'])):continue
            page=pages.get(rec['sha256'],{});raw=raw_path.read_bytes();text=page.get('text','');title=page.get('title')or rec['url'];parser='bs4/html.parser-v1'if text else'raw-v1'
            if rec['url'].endswith('.json'):
                text=json.dumps(json.loads(raw),indent=2);parser='json-v1'
            if 'propublica.org'in rec['url']:issuer='propublica'
            capture_id=store.capture(raw,case,rec['url'],rec['final_url'],issuer,rec['captured_at'],status=rec['status'],content_type=rec.get('content_type',''),metadata={'bootstrap_import':True,'source_sha256':rec['sha256'],'original_file':rec.get('file')},title=title,text=text,parser=parser);added+=1
    pp=store.rows('SELECT id FROM captures WHERE case_id=?AND url=?ORDER BY id DESC LIMIT 1',(case,'https://projects.propublica.org/nonprofits/api/v2/organizations/863883211.json'))
    if pp:
        source_id=pp[0]['id'];data=json.loads((bootstrap/'propublica.json').read_text())
        with store.db()as c:
            for filing in data.get('filings_with_data',[]):
                assets=filing.get('totassetsend');liabilities=filing.get('totliabend')
                values={'revenue':filing.get('totrevenue'),'expenses':filing.get('totfuncexpns'),'net_assets':assets-liabilities if assets is not None and liabilities is not None else None,'assets':assets,'liabilities':liabilities,'tax_period':filing.get('tax_prd'),'form_type':filing.get('formtype')}
                c.execute('INSERT OR IGNORE INTO finance VALUES(?,?,?,?,?,?)',(f'{case}:pp:{filing["tax_prd"]}',case,filing['tax_prd_yr'],encoded(values),source_id,'ProPublica IRS-derived extract; original return not yet obtained'))
    return added

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='private/runtime');p.add_argument('--case',default='umma');p.add_argument('--root',default='private/umma');p.add_argument('--bootstrap',default='private/bootstrap');a=p.parse_args()
    store=Store(a.data);n=import_case(store,a.case,Path(a.root),Path(a.bootstrap));print(json.dumps({'imported':n,'verification':store.verify()}))
