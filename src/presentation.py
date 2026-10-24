"""Read-only, allowlisted presentation of saved pipeline artifacts. No model calls."""
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

LIMITATIONS = [
    'Observations and transcripts are existing machine-generated outputs and have not been manually verified.',
    'Saved reports provide source summaries, not verified cross-video executive findings.',
    'Attribute sentiment, recurring themes and direct product comparisons are not recorded by the current pipeline.',
    'Visual observations have no saved timestamps; audio excerpts have transcript timestamps. Audio and visuals are not assumed to align.',
    'Cached source order is a local library order, not YouTube search ranking. No topic discovery has been performed.',
]


def read_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def text(value, limit=1600):
    return value[:limit] if isinstance(value, str) else ''


def safe_url(value):
    if not isinstance(value, str):
        return ''
    try:
        p = urlsplit(value)
        if p.scheme == 'https' and p.hostname in {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'} and not p.username and not p.password:
            return value
    except ValueError:
        pass
    return ''


def video_key(url):
    url = safe_url(url)
    p = urlsplit(url)
    if p.hostname == 'youtu.be':
        return p.path.strip('/')
    return parse_qs(p.query).get('v', [''])[0] or p.path.removeprefix('/shorts/').strip('/')


def library(root):
    rows = []
    for folder in sorted((root / 'data/frames').glob('*')):
        if not folder.is_dir() or folder.is_symlink():
            continue
        metadata = read_json(root / 'data/videos' / (folder.name + '.json'), {})
        report = read_json(folder / 'brand_intelligence_report.json', {})
        if not isinstance(metadata, dict) or not isinstance(report, dict):
            continue
        if not metadata.get('title'):
            continue
        sid = hashlib.sha256(folder.name.encode()).hexdigest()[:20]
        rows.append({'id': sid, 'title': text(metadata['title'], 300), 'url': safe_url(metadata.get('webpage_url')), 'status': 'completed' if text(report.get('video_summary')) else ('failed' if (folder / 'brand_intelligence_report.json').exists() else 'unavailable'), '_folder': folder, '_report': report})
    unique = {}
    for row in rows:
        key = video_key(row['url']) or row['id']
        if key not in unique or (row['status'] == 'completed' and unique[key]['status'] != 'completed'):
            unique[key] = row
    return list(unique.values())


def public_source(row):
    return {k: row[k] for k in ('id', 'title', 'url', 'status')}


def saved_report(root, query, reference_urls=(), ids=()):
    rows = library(root)
    if ids:
        rows = [r for r in rows if r['id'] in ids]
    elif reference_urls:
        selected = {video_key(u) for u in reference_urls}
        rows = [r for r in rows if video_key(r['url']) in selected]
    else:
        words = [w for w in re.findall(r'\w+', query.lower()) if w not in {'review', 'reviews', 'analysis', 'insights'}]
        rows = [r for r in rows if words and all(w in r['title'].lower() for w in words)]
    sources = [public_source(r) for r in rows]
    if reference_urls:
        found = {video_key(r['url']) for r in rows}
        for i, url in enumerate(reference_urls):
            if video_key(url) not in found:
                sources.append({'id': f'unavailable-{i}', 'title': 'Reference has no saved analysis', 'url': url, 'status': 'unavailable'})
    summaries, evidence = [], []
    for row in rows:
        sid, folder = row['id'], row['_folder']
        if row['status'] != 'completed':
            continue
        summaries.append({'title': row['title'], 'description': text(row['_report'].get('video_summary')), 'source_ids': [sid], 'evidence_ids': [], 'modality': 'Source-level summary'})
        transcript = read_json(root / 'data/videos' / (folder.name + '.transcript.json'), {})
        segments = transcript.get('segments', []) if isinstance(transcript, dict) else []
        for i, segment in enumerate(segments[:3]):
            if not isinstance(segment, dict):
                continue
            start, end = segment.get('start'), segment.get('end')
            if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in (start, end)) or start < 0 or end < start or not text(segment.get('text')):
                continue
            evidence.append({'id': f'{sid}-audio-{i}', 'source_id': sid, 'title': 'Transcript excerpt', 'summary': 'Saved audio transcript; not an attribute-level finding.', 'start_seconds': start, 'end_seconds': end, 'timestamp': f'{start:g}s–{end:g}s', 'spoken': text(segment['text']), 'modality': 'Said'})
        manifest = read_json(folder / 'frame_manifest.json', {})
        timestamps = {r['frame']: r['timestamp_seconds'] for r in manifest.get('frames', []) if isinstance(r,dict) and isinstance(r.get('timestamp_seconds'),(int,float))} if isinstance(manifest,dict) else {}
        frames = read_json(folder / 'vision_analysis.json', [])
        for i, frame in enumerate(frames[:3] if isinstance(frames, list) else []):
            if not isinstance(frame, dict) or 'error' in frame or not text(frame.get('actions')):
                continue
            filename = frame.get('frame', '')
            if not re.fullmatch(r'frame_\d+\.jpg', filename):
                continue
            image = folder / filename
            if not image.is_file() or image.is_symlink():
                continue
            moment = timestamps.get(filename)
            timing = {'start_seconds': moment, 'timestamp': f'{moment:g}s'} if moment is not None else {}
            evidence.append({**timing, 'id': f'{sid}-visual-{i}', 'source_id': sid, 'title': 'Visual observation', 'summary': text(frame['actions']), 'shown': text(frame['actions']), 'modality': 'Shown', 'image_url': f'/api/frames/{sid}/{filename}'})
    identity = hashlib.sha256(json.dumps([query, [s['id'] for s in sources]]).encode()).hexdigest()[:20]
    return {'id': identity, 'query': query, 'title': query, 'kind': 'saved', 'status': 'completed', 'scope': 'Saved video analysis · limited evidence', 'sources': sources, 'source_summaries': summaries, 'insights': [], 'attributes': [], 'themes': [], 'comparisons': [], 'evidence': evidence, 'limitations': LIMITATIONS}
