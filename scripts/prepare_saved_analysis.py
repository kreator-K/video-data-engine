"""Enrich a genuine saved run without repeating video ingestion or transcription."""
import argparse
import hashlib
import json
import sys
import threading
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
from src.job_store import JobStore
from src.presentation import saved_report,video_key,read_json
from src.grounded_insights import extract_observations
from worker import combine


def prepare(path,owner,cloud):
    load_dotenv(ROOT/'.env')
    if cloud:load_dotenv(ROOT/'.env.vercel.local',override=True)
    manifest=read_json(path,{})
    if not manifest.get('results'):raise ValueError('A completed source manifest is required')
    store=JobStore();jid=store.submit(owner,manifest['query'],[]);identity='prepare-'+jid
    job=store.claim(identity)
    if not job or job['id']!=jid:raise RuntimeError('Wait for the existing analysis to finish')
    done=threading.Event()
    def heartbeat():
        while not done.wait(10):
            try:store.update(jid,identity)
            except Exception:return
    thread=threading.Thread(target=heartbeat,daemon=True);thread.start()
    sources=[]
    try:
        for index,row in enumerate(manifest['results']):
            source={k:row[k] for k in ('id','title','url')};source['status']='failed'
            if row['status']=='completed':
                report_path=(ROOT/row['report_path']).resolve()
                if ROOT not in report_path.parents or not report_path.is_file():raise ValueError('Missing report artifact')
                name=report_path.parent.name
                metadata=read_json(ROOT/'data/videos'/(name+'.json'),{})
                if video_key(metadata.get('webpage_url',''))!=video_key(row['url']):raise ValueError('Source artifact provenance mismatch')
                transcript=read_json(ROOT/'data/videos'/(name+'.transcript.json'),{})
                segments=transcript.get('segments',[])
                key=hashlib.sha256(json.dumps([manifest['query'],segments,'grounded-v3'],sort_keys=True).encode()).hexdigest()
                cache=ROOT/'data/grounded_cache'/(key+'.json');coded=read_json(cache)
                if coded is None:
                    print(f'Coding transcript {index+1}/{len(manifest["results"])}',flush=True)
                    coded=extract_observations(manifest['query'],segments)
                    cache.parent.mkdir(parents=True,exist_ok=True);cache.write_text(json.dumps(coded))
                comparisons_cache=ROOT/'data/grounded_cache'/(key+'-comparisons.json')
                comparison_rows=read_json(comparisons_cache)
                if comparison_rows is None:
                    print(f'Checking direct comparisons {index+1}/{len(manifest["results"])}',flush=True)
                    comparison_rows=extract_observations(manifest['query'],segments,window_size=20,comparisons_only=True)
                    comparisons_cache.write_text(json.dumps(comparison_rows))
                coded=coded+comparison_rows
                report=saved_report(ROOT,manifest['query'],[row['url']])
                for e in report['evidence']:
                    if e.get('image_url'):
                        e['image_url']=store.image((report_path.parent/e['image_url'].rsplit('/',1)[-1]).read_bytes(),jid)
                source.update(status='completed',snapshot={'report':report,'observations':coded})
                print(f'Source {index+1}: {len(coded)} grounded observations',flush=True)
            sources.append(source)
            store.update(jid,identity,sources=sources,message=f'Consolidating source {index+1} of {len(manifest["results"])}.')
        report=combine(job,sources,normalize=True)
        if not report['attributes']:raise ValueError('Insufficient grounded observations')
        store.update(jid,identity,status='completed',report=report,message=f'{sum(s["status"]=="completed" for s in sources)}/{len(sources)} videos analyzed.')
        print(json.dumps({'job_id':jid,'sources':len(report['sources']),'attributes':len(report['attributes']),'comparisons':len(report['comparisons']),'evidence':len(report['evidence'])}),flush=True)
    except BaseException:
        store.update(jid,identity,status='failed',message='Saved source analysis could not be completed.');raise
    finally:
        done.set();thread.join(timeout=15)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);parser.add_argument('--owner',default='local-owner');parser.add_argument('--cloud',action='store_true')
    args=parser.parse_args();prepare(args.manifest,args.owner,args.cloud)
