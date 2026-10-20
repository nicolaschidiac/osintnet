#!/usr/bin/env python3
"""Offline credential-preserving restore. Stop the owning gateway first."""
import argparse
import json
import os
import re
import shutil
import sqlite3
import tarfile
import tempfile
import time
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from osintnet.store import Store

def restore(archive, destination, expected_tip):
    destination=Path(destination)
    old=Store(destination)
    current=old.verify()
    if current['tip']!=expected_tip:raise ValueError('destination_changed_restore_refused')
    with tempfile.TemporaryDirectory(prefix='.restore-',dir=destination)as work:
        incoming=Path(work)/'incoming';incoming.mkdir()
        with tarfile.open(archive,'r:gz')as t:
            members=t.getmembers()
            for m in members:
                if not (m.name in ('osintnet.sqlite3','export-manifest.json','blobs','blobs/')or re.fullmatch(r'blobs/[a-f0-9]{64}',m.name)):
                    raise ValueError('unexpected_archive_member')
                if not(m.isfile()or m.isdir())or m.size>100_000_000:raise ValueError('unsafe_archive_member')
            if sum(m.size for m in members)>1_000_000_000:raise ValueError('archive_too_large')
            t.extractall(incoming,filter='data')
        restored=Store(incoming);result=restored.verify()
        manifest=json.loads((incoming/'export-manifest.json').read_text())
        if any(result[k]!=manifest[k]for k in result):raise ValueError('manifest_mismatch')
        with restored.db()as c:
            if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('integrity_failed')
            if c.execute('SELECT count(*)FROM sessions').fetchone()[0]:raise ValueError('export_contains_sessions')
            c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        # Retain an isolated SQLite backup before replacing the stopped instance.
        backup=destination/'backups'/str(time.time_ns());backup.mkdir(parents=True,mode=0o700)
        with sqlite3.connect(old.path)as src,sqlite3.connect(backup/'osintnet.sqlite3')as dst:src.backup(dst)
        (backup/'manifest.json').write_text(json.dumps(current))
        for blob in restored.blobs.iterdir():
            target=old.blobs/blob.name
            if not target.exists():shutil.copy2(blob,target)
        with old.db()as c:c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        # All connections are closed. Authentication files remain instance-local.
        for suffix in ('-wal','-shm'):Path(str(old.path)+suffix).unlink(missing_ok=True)
        os.replace(restored.path,old.path);os.chmod(old.path,0o600)
        if Store(destination).verify()!=result:raise ValueError('post_restore_verification_failed')
        return {**result,'previous_captures':current['captures'],'backup':str(backup),'credentials_preserved':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('destination');p.add_argument('--expected-tip',required=True)
    a=p.parse_args();print(json.dumps(restore(a.archive,a.destination,a.expected_tip)))
