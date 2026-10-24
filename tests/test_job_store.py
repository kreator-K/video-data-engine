import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from src.job_store import JobStore, AdmissionError


def test_atomic_submit_and_cross_process_claim(tmp_path):
    path=tmp_path/'jobs.db'
    store=JobStore(path)
    def submit(_): return JobStore(path).submit('owner','Topic',[])
    with ThreadPoolExecutor(max_workers=5) as pool:
        ids=list(pool.map(submit,range(5)))
    assert len(set(ids))==1
    assert store.claim('one')['id']==ids[0]
    assert JobStore(path).claim('two') is None
    assert store.public(ids[0],'other') is None
    with store.connection(write=True) as db:
        db.execute('UPDATE jobs SET lease=? WHERE id=?',(time.time()-1,ids[0]))
    assert JobStore(path).claim('two')['id']==ids[0]
    with pytest.raises(RuntimeError): store.update(ids[0],'one',message='stale')


def test_history_ownership_order_and_image_immutability(tmp_path):
    store=JobStore(tmp_path/'jobs.db')
    first=store.submit('owner','One',[]); store.claim('w')
    original=b'\xff\xd8original-image'
    url=store.image(original,first)
    store.update(first,'w',status='completed',report={'id':first})
    second=store.submit('owner','Two',[]); store.claim('w')
    store.image(b'\xff\xd8replacement',second)
    store.update(second,'w',status='completed',report={'id':second})
    digest=url.rsplit('/',1)[1][:-4]
    assert store.get_image(digest,'owner')==original
    assert store.get_image(digest,'other') is None
    assert [r['id'] for r in store.history('owner')]==[second,first]
    assert store.history('other')==[]


def test_quota_and_hidden_unfinished_history(tmp_path,monkeypatch):
    monkeypatch.setenv('MAX_DAILY_JOBS_PER_USER','1')
    store=JobStore(tmp_path/'jobs.db')
    jid=store.submit('owner','Topic',[])
    assert store.history('owner')==[]
    store.claim('w');store.update(jid,'w',status='failed')
    with pytest.raises(AdmissionError):store.submit('owner','Another',[])


def test_expired_worker_cannot_renew_without_reclaim(tmp_path):
    store=JobStore(tmp_path/'jobs.db')
    jid=store.submit('owner','Topic',[])
    store.claim('expired-worker')
    with store.connection(write=True) as db:
        db.execute('UPDATE jobs SET lease=? WHERE id=?',(time.time()-1,jid))
    with pytest.raises(RuntimeError):
        store.update(jid,'expired-worker',message='late heartbeat')
