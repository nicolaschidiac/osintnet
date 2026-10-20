#!/usr/bin/env python3
"""Consistent private database/blob export; credentials are never copied."""
import argparse
import fcntl
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from osintnet.store import Store

def export(source,output,deployment=False):
    source=Store(source);output=Path(output)
    if output.resolve()==source.root.resolve():raise ValueError('separate_export_directory_required')
    output.mkdir(parents=True,exist_ok=True,mode=0o700);marker=output/'.osintnet-export'
    if (output/'osintnet.sqlite3').exists()and not marker.exists():raise ValueError('refusing_unmarked_existing_workspace')
    with marker.open('a+')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        temp=output/'snapshot.sqlite3.tmp';src=sqlite3.connect(source.path);dest=sqlite3.connect(temp)
        try:
            src.backup(dest)
            dest.execute('DELETE FROM sessions');dest.execute('DELETE FROM rate_limits');dest.execute('DELETE FROM workers')
            if deployment:
                dest.execute("UPDATE settings SET value='false'WHERE key='running'");dest.execute('UPDATE nodes SET enabled=0');dest.execute("UPDATE jobs SET state='cancelled',error='exported_without_execution'WHERE state IN('queued','running')")
            dest.commit();hashes=[x[0]for x in dest.execute('SELECT DISTINCT sha256 FROM captures')]
            if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('database_integrity_failed')
        finally:src.close();dest.close()
        blobs=output/'blobs';blobs.mkdir(exist_ok=True,mode=0o700)
        for digest in hashes:
            src=source.blobs/digest;dst=blobs/digest
            if not dst.exists():shutil.copy2(src,dst)
            if hashlib.sha256(dst.read_bytes()).hexdigest()!=digest:raise ValueError('export_blob_mismatch')
        if (output/'osintnet.sqlite3').exists():
            with sqlite3.connect(output/'osintnet.sqlite3')as c:c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        os.replace(temp,output/'osintnet.sqlite3');os.chmod(output/'osintnet.sqlite3',0o600)
        result=Store(output).verify();(output/'export-manifest.json').write_text(json.dumps({**result,'credentials_included':False,'deployment_paused':deployment},indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');p.add_argument('--deployment',action='store_true');a=p.parse_args();print(json.dumps(export(a.source,a.output,a.deployment)))
