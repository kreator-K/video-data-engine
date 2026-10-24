"""Opt-in real PostgreSQL durability checks. Never contacts model providers.

Run with QA_POSTGRES_URL configured privately. Own disposable rows are cleaned up.
"""
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from src.job_store import JobStore


@pytest.mark.skipif(not os.getenv('QA_POSTGRES_URL'),reason='Real PostgreSQL acceptance is opt-in')
def test_real_postgres_durability_leases_owner_and_images():
    try:
        _check_real_postgres()
    except Exception as error:
        pytest.fail('PostgreSQL acceptance failed ('+type(error).__name__+'); connection details withheld.',pytrace=False)


def _check_real_postgres():
    store=JobStore(database_url=os.environ['QA_POSTGRES_URL'])
    owner='qa-regression-'+uuid.uuid4().hex
    other=owner+'-other'
    digest=None
    jid=None
    with store.connection() as db:
        active=db.execute("SELECT COUNT(*) AS n FROM jobs WHERE status IN ('queued','running')").fetchone()['n']
    if active:
        pytest.skip('Database has active jobs; do not interfere with real work')
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            ids=list(pool.map(lambda _:store.submit(owner,'Disposable QA durability check',[]),range(3)))
        assert len(set(ids))==1
        jid=ids[0]
        assert store.history(owner)==[]
        claimed=store.claim(owner+'-worker-one')
        assert claimed['id']==jid
        assert store.claim(owner+'-worker-two') is None
        store.update(jid,owner+'-worker-one',sources=[{'status':'queued','url':'https://youtu.be/aaaaaaaaaaa'}])
        with store.connection(write=True) as db:
            db.execute('UPDATE jobs SET lease=? WHERE id=? AND owner=?',(time.time()-1,jid,owner))
        with pytest.raises(RuntimeError):store.update(jid,owner+'-worker-one',message='Expired')
        claimed=store.claim(owner+'-worker-two')
        assert claimed['id']==jid and claimed['sources'][0]['status']=='queued'
        image=b'\xff\xd8qa-regression-'+uuid.uuid4().bytes
        url=store.image(image,jid)
        digest=url.rsplit('/',1)[-1][:-4]
        assert store.get_image(digest,owner) is None
        report={'id':jid,'query':'Disposable QA durability check','sources':[]}
        store.update(jid,owner+'-worker-two',status='completed',report=report)
        reopened=JobStore(database_url=os.environ['QA_POSTGRES_URL'])
        assert reopened.public(jid,owner)['analysis']==report
        assert reopened.public(jid,other) is None
        assert reopened.get_image(digest,owner)==image
        assert reopened.get_image(digest,other) is None
        assert reopened.history(owner)[0]['id']==jid
        with store.connection() as db:
            security=db.execute("SELECT relname,relrowsecurity FROM pg_class JOIN pg_namespace ON pg_namespace.oid=pg_class.relnamespace WHERE nspname='studio_private' AND relname IN ('jobs','images','job_images')").fetchall()
            assert len(security)==3 and all(r['relrowsecurity'] for r in security)
            assert db.execute("SELECT has_schema_privilege('anon','studio_private','USAGE') AS allowed").fetchone()['allowed'] is False
            assert db.execute("SELECT has_schema_privilege('authenticated','studio_private','USAGE') AS allowed").fetchone()['allowed'] is False
    finally:
        with store.connection(write=True) as db:
            db.execute('DELETE FROM job_images WHERE job_id IN (SELECT id FROM jobs WHERE owner=?)',(owner,))
            db.execute('DELETE FROM jobs WHERE owner=?',(owner,))
            if digest:
                db.execute('DELETE FROM images WHERE digest=? AND NOT EXISTS (SELECT 1 FROM job_images WHERE job_images.digest=images.digest)',(digest,))
