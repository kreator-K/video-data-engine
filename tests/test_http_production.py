import base64
import json

import pytest
from src.http_app import handle
from src.job_store import JobStore


def call(store,path='/api/analyses',method='GET',body=None,headers=None):
    h={'Host':'127.0.0.1:4173',**(headers or {})}
    if body is not None:h['Content-Type']='application/json'
    status,raw,_=handle(method,path,h,json.dumps(body).encode() if body is not None else b'',store)
    return status,json.loads(raw)


def test_auth_isolation_and_no_internal_payload(tmp_path,monkeypatch):
    monkeypatch.setenv('STUDIO_USERS_JSON',json.dumps({'alice':'secret-one','bob':'secret-two'}))
    store=JobStore(tmp_path/'jobs.db')
    def auth(user,password):return {'Authorization':'Basic '+base64.b64encode(f'{user}:{password}'.encode()).decode()}
    alice=auth('alice','secret-one');bob=auth('bob','secret-two')
    assert call(store)[0]==401
    status,result=call(store,'/api/searches','POST',{'query':'Topic'},alice)
    assert status==202
    jid=result['id']
    assert call(store,'/api/searches/'+jid,headers=bob)[0]==404
    status,public=call(store,'/api/searches/'+jid,headers=alice)
    assert status==200
    assert not any(k in public for k in ['owner','request','sources','worker','lease'])
    assert call(store,headers=alice)[1]['analyses']==[]


def test_boundaries_origin_and_production_fail_closed(tmp_path,monkeypatch):
    store=JobStore(tmp_path/'jobs.db')
    monkeypatch.delenv('STUDIO_USERS_JSON',raising=False)
    monkeypatch.delenv('STUDIO_ENV',raising=False)
    monkeypatch.delenv('VERCEL',raising=False)
    for path in ['/.env','/src/vision_analyser.py','/data/videos/a.mp4','/../README.md']:
        assert call(store,path)[0]==404
    assert call(store,'/api/searches','POST',{'query':'Topic'},{'Origin':'https://evil.test'})[0]==403
    monkeypatch.setenv('STUDIO_ENV','production')
    assert call(store)[0]==401
    monkeypatch.setenv('STUDIO_USERS_JSON','{"user":"password"}')
    auth={'Authorization':'Basic '+base64.b64encode(b'user:password').decode()}
    monkeypatch.delenv('DATABASE_URL',raising=False)
    assert call(store,headers=auth)[0]==503


def test_validation_and_no_costly_call_in_web(tmp_path,monkeypatch):
    store=JobStore(tmp_path/'jobs.db')
    monkeypatch.delenv('STUDIO_USERS_JSON',raising=False)
    for body in [{},[],{'query':' '},{'query':'topic','reference_urls':['https://youtube.com/channel/test']}]:
        assert call(store,'/api/searches','POST',body)[0]==400
    assert call(store,'/api/searches','POST',{'query':'Topic'})[0]==202


def test_unauthenticated_local_adapter_rejects_rebinding_host(tmp_path,monkeypatch):
    for key in ['STUDIO_USERS_JSON','STUDIO_ENV','VERCEL']:
        monkeypatch.delenv(key,raising=False)
    store=JobStore(tmp_path/'jobs.db')
    assert call(store,headers={'Host':'attacker.example:4173'})[0]==403
    assert call(store,'/api/searches','POST',{'query':'Topic'},{'Host':'attacker.example:4173','Origin':'http://attacker.example:4173'})[0]==403
    assert call(store,headers={'Host':'localhost:4173'})[0]==200


@pytest.mark.parametrize('limit',[0,11,-1,True,False,1.0,'1',None])
def test_source_limit_rejects_invalid_values_without_admission(tmp_path,monkeypatch,limit):
    for key in ['STUDIO_USERS_JSON','STUDIO_ENV','VERCEL']:monkeypatch.delenv(key,raising=False)
    store=JobStore(tmp_path/'jobs.db')
    assert call(store,'/api/searches','POST',{'query':'Topic','source_limit':limit})[0]==400
    with store.connection() as db:assert db.execute('SELECT COUNT(*) AS n FROM jobs').fetchone()['n']==0


@pytest.mark.parametrize('limit',[1,10])
def test_source_limit_is_persisted_and_equivalent_reference_forms_deduplicate(tmp_path,monkeypatch,limit):
    for key in ['STUDIO_USERS_JSON','STUDIO_ENV','VERCEL']:monkeypatch.delenv(key,raising=False)
    store=JobStore(tmp_path/'jobs.db')
    first={'query':' Topic ','source_limit':limit,'reference_urls':['https://youtu.be/aaaaaaaaaaa?t=20','https://www.youtube.com/watch?v=aaaaaaaaaaa']}
    second={'query':'Topic','source_limit':limit,'reference_urls':['https://www.youtube.com/watch?v=aaaaaaaaaaa']}
    status,a=call(store,'/api/searches','POST',first)
    assert status==202
    status,b=call(store,'/api/searches','POST',second)
    assert status==202 and a['id']==b['id']
    assert store.internal(a['id'])['request']=={'query':'Topic','source_limit':limit,'reference_urls':['https://www.youtube.com/watch?v=aaaaaaaaaaa']}
    assert call(store,'/api/searches','POST',{**second,'source_limit':11-limit})[0]==429


def test_active_dedup_is_per_authenticated_user(tmp_path,monkeypatch):
    monkeypatch.setenv('STUDIO_USERS_JSON',json.dumps({'alice':'one','bob':'two'}))
    monkeypatch.delenv('STUDIO_ENV',raising=False);monkeypatch.delenv('VERCEL',raising=False)
    store=JobStore(tmp_path/'jobs.db')
    auth=lambda who,pwd:{'Authorization':'Basic '+base64.b64encode(f'{who}:{pwd}'.encode()).decode()}
    body={'query':'Topic','source_limit':1}
    status,a=call(store,'/api/searches','POST',body,auth('alice','one'))
    status,b=call(store,'/api/searches','POST',body,auth('bob','two'))
    assert status==202 and a['id']!=b['id']
    assert call(store,'/api/searches/'+a['id'],headers=auth('bob','two'))[0]==404
