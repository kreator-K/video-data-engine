"""Exercise durable worker restart and evidence paths without paid provider calls."""
import json
import time

import pytest
import worker
from src.http_app import handle
from src.job_store import JobStore


def snapshot(title='First source'):
    return {'report': {'sources':[{'title':title}], 'evidence':[], 'source_summaries':[]}, 'observations':[]}


def test_reclaimed_job_never_replays_inflight_or_completed_source(tmp_path, monkeypatch):
    store=JobStore(tmp_path/'jobs.db')
    jid=store.submit('local-owner','Phone reviews',[])
    store.claim('crashed-worker')
    sources=[
        {'url':'https://youtu.be/aaaaaaaaaaa','title':'Already completed','status':'completed','snapshot':snapshot()},
        {'url':'https://youtu.be/bbbbbbbbbbb','title':'Paid call interrupted','status':'processing'},
        {'url':'https://youtu.be/ccccccccccc','title':'Untouched queued source','status':'queued'},
    ]
    store.update(jid,'crashed-worker',sources=sources)
    with store.connection(write=True) as db:
        db.execute('UPDATE jobs SET lease=? WHERE id=?',(time.time()-1,jid))
    job=JobStore(tmp_path/'jobs.db').claim('replacement-worker')
    called=[]
    def child(*args):
        called.append(args[4]['url'])
        return snapshot('New source')
    monkeypatch.setattr(worker,'child',child)
    monkeypatch.setattr(worker,'STOP',False)
    worker.run_one(store,job,'replacement-worker')
    assert called==['https://youtu.be/ccccccccccc']
    public=store.public(jid,'local-owner')
    assert public['status']=='completed'
    assert [s['status'] for s in public['analysis']['sources']]==['completed','failed','completed']
    assert public['analysis']['completed_at']
    assert store.history('local-owner')[0]['id']==jid
    with pytest.raises(RuntimeError):store.update(jid,'crashed-worker',message='stale owner')


def test_graceful_stop_preserves_unstarted_work(tmp_path,monkeypatch):
    store=JobStore(tmp_path/'jobs.db')
    jid=store.submit('local-owner','Phone reviews',[])
    store.claim('worker')
    store.update(jid,'worker',sources=[{'url':'https://youtu.be/aaaaaaaaaaa','title':'Untouched','status':'queued'}])
    monkeypatch.setattr(worker,'STOP',True)
    monkeypatch.setattr(worker,'child',lambda *args:pytest.fail('Must not start source work after stop'))
    worker.run_one(store,store.internal(jid),'worker')
    assert store.internal(jid)['sources'][0]['status']=='queued'
    assert store.history('local-owner')==[]


def test_completed_worker_report_reopens_through_authenticated_boundary(tmp_path,monkeypatch):
    monkeypatch.delenv('STUDIO_USERS_JSON',raising=False)
    monkeypatch.delenv('STUDIO_ENV',raising=False)
    monkeypatch.delenv('VERCEL',raising=False)
    store=JobStore(tmp_path/'jobs.db')
    jid=store.submit('local-owner','Phone reviews',[])
    job=store.claim('worker')
    def child(_store,_job,_identity,mode,request,timeout):
        return [{'url':'https://youtu.be/aaaaaaaaaaa','title':'Source'}] if mode=='discover' else snapshot()
    monkeypatch.setattr(worker,'child',child)
    monkeypatch.setattr(worker,'STOP',False)
    worker.run_one(store,job,'worker')
    # Reconstruct store to prove persistence rather than Python process memory.
    reopened=JobStore(tmp_path/'jobs.db')
    status,raw,_=handle('GET','/api/analyses/'+jid,{'Host':'localhost'},store=reopened)
    assert status==200
    report=json.loads(raw)['analysis']
    assert report['id']==jid and report['sources'][0]['status']=='completed'
    status,raw,_=handle('GET','/api/searches/'+jid,{'Host':'localhost'},store=reopened)
    public=json.loads(raw)
    assert status==200 and public['status']=='completed'
    assert not {'snapshot','observations','worker','request','lease'} & public.keys()


def test_evidence_accepts_resolved_temporary_workspace_alias(tmp_path,monkeypatch):
    from contextlib import contextmanager
    from pathlib import Path
    from types import SimpleNamespace
    actual=tmp_path/'actual';actual.mkdir()
    alias=tmp_path/'alias';alias.symlink_to(actual,target_is_directory=True)
    @contextmanager
    def temporary(**kwargs):yield str(alias)
    monkeypatch.setattr(worker.tempfile,'TemporaryDirectory',temporary)
    captured=[]
    def process(args,**kwargs):
        image=actual/'frame.jpg';image.write_bytes(b'jpeg-content')
        Path(args[4]).write_text(json.dumps({'report':{'evidence':[{'id':'frame'}]},'images':{'frame':str(image.resolve())}}))
        return SimpleNamespace(poll=lambda:0,returncode=0)
    monkeypatch.setattr(worker.subprocess,'Popen',process)
    store=SimpleNamespace(image=lambda content,jid:captured.append((content,jid)) or '/api/evidence/digest.jpg')
    result=worker.child(store,{'id':'job'},'worker','analyze',{},5)
    assert captured==[(b'jpeg-content','job')]
    assert result['report']['evidence'][0]['image_url']=='/api/evidence/digest.jpg'


@pytest.mark.parametrize('symlink_escape',[False,True])
def test_evidence_workspace_canonicalization_still_rejects_outside_files(tmp_path,monkeypatch,symlink_escape):
    from contextlib import contextmanager
    from pathlib import Path
    from types import SimpleNamespace
    actual=tmp_path/'actual';actual.mkdir()
    alias=tmp_path/'alias';alias.symlink_to(actual,target_is_directory=True)
    outside=tmp_path/'outside.jpg';outside.write_bytes(b'outside-content')
    image=outside
    if symlink_escape:
        image=actual/'escape.jpg';image.symlink_to(outside)
    @contextmanager
    def temporary(**kwargs):yield str(alias)
    monkeypatch.setattr(worker.tempfile,'TemporaryDirectory',temporary)
    def process(args,**kwargs):
        Path(args[4]).write_text(json.dumps({'report':{'evidence':[{'id':'frame'}]},'images':{'frame':str(image)}}))
        return SimpleNamespace(poll=lambda:0,returncode=0)
    monkeypatch.setattr(worker.subprocess,'Popen',process)
    store=SimpleNamespace(image=lambda *args:pytest.fail('Outside artifacts must not enter evidence storage'))
    with pytest.raises(ValueError,match='Invalid artifact path'):
        worker.child(store,{'id':'job'},'worker','analyze',{},5)
