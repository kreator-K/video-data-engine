"""Publish an already prepared, evidence-bearing report to the linked cloud database."""
import hashlib
import json
import sys
import threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import dotenv_values,load_dotenv
from src.job_store import JobStore
from worker import combine

local=JobStore(ROOT/'data/jobs.sqlite3',database_url='')
source=local.internal(sys.argv[1])
if not source or source['status']!='completed':raise SystemExit('A completed prepared analysis is required.')
load_dotenv(ROOT/'.env')
cloud_values=dotenv_values(ROOT/'.env.vercel.local')
cloud=JobStore(database_url=cloud_values['POSTGRES_URL'])
user=next(iter(json.loads((ROOT/'.deploy-secrets.json').read_text())))
owner=hashlib.sha256(user.encode()).hexdigest()
jid=cloud.submit(owner,source['request']['query'],[])
identity='publish-'+jid;job=cloud.claim(identity)
if not job or job['id']!=jid:raise SystemExit('Wait for active cloud work before publishing.')
done=threading.Event()
def pulse():
    while not done.wait(10):
        try:cloud.update(jid,identity)
        except Exception:return
thread=threading.Thread(target=pulse,daemon=True);thread.start()
try:
    sources=source['sources']
    for row in sources:
        if row.get('snapshot'):
            for evidence in row['snapshot']['report']['evidence']:
                url=evidence.get('image_url','')
                if url.startswith('/api/evidence/'):
                    digest=url.rsplit('/',1)[1][:-4]
                    content=local.get_image(digest,source['owner'])
                    if not content:raise ValueError('Missing immutable evidence')
                    evidence['image_url']=cloud.image(content,jid)
    report=combine(job,sources,normalize=True)
    cloud.update(jid,identity,sources=sources,status='completed',report=report,message=f"{len(report['sources'])} source videos analyzed.")
    print(json.dumps({'job_id':jid,'source_count':len(report['sources']),'attributes':len(report['attributes']),'comparisons':len(report['comparisons'])}))
except BaseException:
    cloud.update(jid,identity,status='failed',message='Prepared analysis could not be published.');raise
finally:done.set();thread.join(timeout=15)
