"""WSGI boundary regression, independent of socket permissions and paid services."""
import io
import json
import app
from src.job_store import JobStore


def test_wsgi_submission_and_polling(tmp_path,monkeypatch):
    from src.http_app import handle
    store=JobStore(tmp_path/'jobs.db')
    monkeypatch.setattr(app,'handle',lambda *args:handle(*args,store=store))
    request=json.dumps({'query':'Topic'}).encode()
    captured=[]
    environ={'REQUEST_METHOD':'POST','PATH_INFO':'/api/searches','CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(request)),'wsgi.input':io.BytesIO(request),'HTTP_HOST':'localhost'}
    body=b''.join(app.application(environ,lambda status,headers:captured.append(status)))
    assert captured[-1].startswith('202')
    jid=json.loads(body)['id']
    environ.update(REQUEST_METHOD='GET',PATH_INFO='/api/searches/'+jid,CONTENT_LENGTH='0')
    body=b''.join(app.application(environ,lambda status,headers:captured.append(status)))
    assert json.loads(body)['status']=='queued'
