"""Durable leased worker. Subprocess isolation keeps the existing pipeline unchanged."""
import argparse
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from src.job_store import JobStore
from src.grounded_insights import aggregate, canonicalize

ROOT = Path(__file__).resolve().parent
STOP = False


def stop(*args):
    global STOP
    STOP = True


def child(store, job, worker, mode, request, timeout):
    with tempfile.TemporaryDirectory(prefix='video-analysis-') as directory:
        work = Path(directory).resolve()
        request_file, output = work/'request.json', work/'output.json'
        request_file.write_text(json.dumps(request))
        with (work/'private.log').open('wb') as log:
            proc = subprocess.Popen([sys.executable,str(ROOT/'execute_source.py'),mode,str(request_file),str(output)], cwd=work, stdout=log, stderr=log, start_new_session=True)
            started = time.monotonic()
            try:
                while proc.poll() is None:
                    if STOP or time.monotonic()-started>timeout:
                        raise TimeoutError('Source interrupted or timed out')
                    store.update(job['id'],worker)
                    time.sleep(2)
                if proc.returncode or not output.is_file():
                    logging.error('Source failed for job %s: %s',job['id'], (work/'private.log').read_text(errors='replace')[-4000:])
                    raise RuntimeError('Source processing failed')
                result = json.loads(output.read_text())
                if mode=='analyze':
                    images = result.pop('images',{})
                    for evidence in result['report']['evidence']:
                        if evidence['id'] in images:
                            image = Path(images[evidence['id']]).resolve()
                            if work not in image.parents:
                                raise ValueError('Invalid artifact path')
                            evidence['image_url'] = store.image(image.read_bytes(),job['id'])
                return result
            finally:
                if proc.poll() is None:
                    os.killpg(proc.pid,signal.SIGTERM)
                    try: proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid,signal.SIGKILL); proc.wait()


def run_one(store, job, worker):
    sources = job['sources'] or []
    try:
        if not sources:
            store.update(job['id'],worker,message='Finding relevant videos.')
            discovered = child(store,job,worker,'discover',job['request'],120)
            sources = [{**s,'status':'queued'} for s in discovered]
            store.update(job['id'],worker,sources=sources)
        if not sources:
            raise ValueError('No eligible source videos')
        # Interrupted in-flight work is never silently replayed and charged twice.
        for source in sources:
            if source['status']=='processing': source['status']='failed'
        for index, source in enumerate(sources):
            if STOP: break
            if source['status']!='queued': continue
            source['status']='processing'
            store.update(job['id'],worker,sources=sources,message=f'Analyzing video {index+1} of {len(sources)}.')
            try:
                result = child(store,job,worker,'analyze',{'query':job['request']['query'],'url':source['url']},int(os.getenv('SOURCE_TIMEOUT_SECONDS','2700')))
                source.update(status='completed',snapshot=result)
            except Exception:
                logging.exception('Source failed for job %s',job['id'])
                source['status']='failed'
            store.update(job['id'],worker,sources=sources)
        if STOP:
            # Relinquish lease; a replacement worker resumes untouched queued sources.
            return
        coded={hashlib.sha256(s['url'].encode()).hexdigest()[:20]:s['snapshot']['observations'] for s in sources if s['status']=='completed' and s.get('snapshot')}
        if any(coded.values()):
            store.update(job['id'],worker,message='Consolidating evidence.')
            normalized=child(store,job,worker,'finalize',{'observations':coded},300)
            for source in sources:
                sid=hashlib.sha256(source['url'].encode()).hexdigest()[:20]
                if sid in normalized:source['snapshot']['observations']=normalized[sid]
            store.update(job['id'],worker,sources=sources)
        report = combine(job,sources)
        completed = sum(s['status']=='completed' for s in sources)
        if not completed:
            store.update(job['id'],worker,status='failed',message='No videos could be analyzed. Please check your references or retry later.')
        else:
            store.update(job['id'],worker,status='completed',report=report,message=f'{completed}/{len(sources)} videos analyzed.')
    except Exception:
        logging.exception('Job %s failed',job['id'])
        store.update(job['id'],worker,status='failed',message='Analysis could not be completed. Please retry later.')


def combine(job,sources, normalize=False):
    report = {'id':job['id'],'query':job['request']['query'],'title':job['request']['query'],'status':'completed','kind':'analysis','sources':[], 'evidence':[], 'source_summaries':[]}
    coded = {}
    for source in sources:
        sid = hashlib.sha256(source['url'].encode()).hexdigest()[:20]
        snapshot = source.get('snapshot')
        title = source.get('title','Video')
        if source['status']=='completed' and snapshot:
            saved = snapshot['report']
            if saved['sources']: title=saved['sources'][0]['title']
            for e in saved['evidence']:
                report['evidence'].append({**e,'id':sid+'-'+e['id'],'source_id':sid})
            for summary in saved['source_summaries']:
                report['source_summaries'].append({**summary,'source_ids':[sid]})
            coded[sid]=snapshot['observations']
        report['sources'].append({'id':sid,'title':title,'url':source['url'],'status':source['status']})
    report['completed_at']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    return aggregate(report,canonicalize(coded) if normalize else coded)


def main():
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    store, identity = JobStore(), uuid.uuid4().hex
    while not STOP:
        job = store.claim(identity)
        if job: run_one(store,job,identity)
        else: time.sleep(2)


if __name__=='__main__': main()
