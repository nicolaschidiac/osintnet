from pathlib import Path
import pytest
from scripts.export_workspace import export
from osintnet.store import Store
from scripts.restore_workspace import restore
import tarfile

def test_repeated_export_preserves_read_only_blobs_and_removes_sessions(tmp_path):
    source=Store(tmp_path/'source');source.capture(b'source',case_id='case',url='https://example.org/',final_url='https://example.org/',issuer='test',captured_at='2026-10-19')
    with source.db()as c:c.execute("INSERT INTO sessions VALUES('privatehash','admin',9999999999)")
    target=tmp_path/'export'
    first=export(source.root,target,True)
    blob=next((target/'blobs').iterdir());stat=blob.stat()
    second=export(source.root,target,True)
    assert first==second and blob.stat().st_ino==stat.st_ino
    assert blob.stat().st_mode&0o777==0o400
    assert Store(target).rows('SELECT * FROM sessions')==[]
    assert not (target/'operator.key').exists()
    with pytest.raises(ValueError,match='separate_export'):export(source.root,source.root)

def test_offline_restore_is_fenced_and_preserves_instance_auth(tmp_path):
    source=Store(tmp_path/'source');source.capture(b'evidence','case','https://example.org/','https://example.org/','test','2026-10-19')
    output=tmp_path/'export';export(source.root,output,True)
    archive=tmp_path/'export.tar.gz'
    with tarfile.open(archive,'w:gz')as t:
        for name in ('osintnet.sqlite3','blobs','export-manifest.json'):t.add(output/name,arcname=name)
    destination=Store(tmp_path/'destination');auth=destination.root/'operator.key';auth.write_text('instance-local-key')
    with pytest.raises(ValueError,match='destination_changed'):restore(archive,destination.root,'wrong-tip')
    result=restore(archive,destination.root,'0'*64)
    assert result['captures']==1 and result['credentials_preserved']
    assert auth.read_text()=='instance-local-key'
    assert source.verify()==destination.verify()
