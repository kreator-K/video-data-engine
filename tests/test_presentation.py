import json
from pathlib import Path
from src.presentation import library, saved_report, safe_url


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_saved_adapter_preserves_evidence_without_inventing_metrics(tmp_path):
    folder = tmp_path / 'data/frames/Example'
    put(tmp_path / 'data/videos/Example.json', {'title': 'Example phone', 'webpage_url': 'https://www.youtube.com/watch?v=abc', 'private': 'secret'})
    put(folder / 'brand_intelligence_report.json', {'video_summary': 'A real saved summary', 'raw_report': 'private', 'brand_context': {'Samsung': {'positive': True}}})
    put(tmp_path / 'data/videos/Example.transcript.json', {'segments': [{'start': 12.5, 'end': 15, 'text': 'Exact transcript excerpt'}]})
    put(folder / 'vision_analysis.json', [{'frame': 'frame_0003.jpg', 'actions': 'Holding a phone', 'vision_provider_used': 'private'}])
    (folder / 'frame_0003.jpg').write_bytes(b'image')
    report = saved_report(tmp_path, 'phone')
    assert report['sources'][0]['status'] == 'completed'
    assert report['evidence'][0]['start_seconds'] == 12.5
    assert 'timestamp' not in report['evidence'][1]
    assert report['insights'] == report['attributes'] == report['comparisons'] == []
    assert all(x not in json.dumps(report) for x in ['secret', 'raw_report', 'vision_provider_used', 'brand_context'])
    assert saved_report(tmp_path, 'phone')['id'] == report['id']
    assert library(tmp_path)[0]['id'] == report['sources'][0]['id']


def test_missing_and_failed_sources_not_counted_as_completed(tmp_path):
    put(tmp_path / 'data/videos/Example.json', {'title': 'Example', 'webpage_url': 'https://youtu.be/abc'})
    (tmp_path / 'data/frames/Example').mkdir(parents=True)
    report = saved_report(tmp_path, 'Example', ['https://youtu.be/abc', 'https://youtu.be/def'])
    assert [s['status'] for s in report['sources']] == ['unavailable', 'unavailable']
    assert not report['source_summaries']


def test_source_link_allowlist():
    assert safe_url('javascript:alert(1)') == ''
    assert safe_url('https://youtube.com.evil.test/watch?v=x') == ''
    assert safe_url('https://user:secret@youtube.com/watch?v=x') == ''
    assert safe_url('https://youtu.be/abc')
