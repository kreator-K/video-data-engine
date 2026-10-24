"""Isolated worker subprocess, always uses the existing pipeline and providers."""
import json
import sys
from pathlib import Path

if __name__ == '__main__':
    mode, request_file, output = sys.argv[1:]
    request = json.loads(Path(request_file).read_text())
    if mode == 'finalize':
        from src.grounded_insights import canonicalize
        result=canonicalize(request['observations'])
    elif mode == 'discover':
        from src.youtube_search import search_videos
        from src.presentation import video_key
        limit=request.get('source_limit',10)
        refs = [{'url':u,'id':video_key(u),'title':'Reference video'} for u in request.get('reference_urls',[])]
        discovered = search_videos(request['query'],limit=limit) if len(refs)<limit else []
        sources, seen = [], set()
        for row in refs+discovered:
            if row['id'] not in seen:
                seen.add(row['id']); sources.append(row)
        result = sources[:limit]
    else:
        from main import run_pipeline
        from src.presentation import saved_report, read_json
        from src.grounded_insights import extract_review_observations
        path = run_pipeline(request['url'])
        report = saved_report(Path.cwd(),request['query'],[request['url']])
        if not report['sources'] or report['sources'][0]['status']!='completed':
            raise RuntimeError('Source did not produce a usable report')
        folder = path.parent
        transcript = read_json(Path('data/videos')/(folder.name+'.transcript.json'),{})
        observations = extract_review_observations(request['query'],transcript.get('segments',[]))
        images = {}
        for e in report['evidence']:
            if e.get('image_url'):
                images[e['id']] = str((folder / e['image_url'].rsplit('/',1)[-1]).resolve())
        result = {'report':report,'observations':observations,'images':images}
    Path(output).write_text(json.dumps(result))
