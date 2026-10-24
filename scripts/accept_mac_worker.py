"""Run one bounded real Mac worker acceptance job against the linked cloud queue."""
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import dotenv_values,load_dotenv
def main():
    load_dotenv(ROOT/'.env')
    cloud=dotenv_values(ROOT/'.env.vercel.local')
    os.environ['POSTGRES_URL']=cloud['POSTGRES_URL']
    os.environ['MAX_SOURCE_DURATION_SECONDS']='1800'
    os.environ['MAX_SOURCE_BYTES']='314572800'
    # Two failed cloud-download acceptance attempts consumed the normal demo quota.
    # This one-process allowance permits the explicitly approved Mac acceptance run.
    os.environ['MAX_DAILY_JOBS_PER_USER']='8'
    from src.job_store import JobStore
    from worker import run_one
    store=JobStore()
    user=next(iter(json.loads((ROOT/'.deploy-secrets.json').read_text())))
    owner=hashlib.sha256(user.encode()).hexdigest()
    jid=store.submit(owner,'iPhone 16e Mac worker acceptance',['https://www.youtube.com/watch?v=0amYSfrACao'],source_limit=1)
    identity='mac-qa-'+uuid.uuid4().hex
    job=store.claim(identity)
    if not job or job['id']!=jid:raise SystemExit('Acceptance job not claimable. Stop and inspect the queue.')
    (ROOT/'data/mac-acceptance-job.json').write_text(json.dumps({'id':jid}))
    print(json.dumps({'id':jid,'status':'running','worker':'Mac'}),flush=True)
    run_one(store,job,identity)
    public=store.public(jid,owner)
    print(json.dumps({'id':jid,'status':public['status'],'message':public['message']}),flush=True)

if __name__=='__main__':main()
