import json
from pathlib import Path

import pytest


@pytest.fixture
def pipeline(monkeypatch, tmp_path):
    import main
    monkeypatch.chdir(tmp_path)
    Path('data/frames/current').mkdir(parents=True)
    metadata = {'filepath': 'data/videos/current.mp4', 'title': 'Current video', 'view_count': None}
    monkeypatch.setattr(main, 'download_video', lambda url: metadata)
    monkeypatch.setattr(main, 'extract_frames', lambda path: ['frame.jpg'])
    monkeypatch.setattr(main, 'transcribe_video', lambda *args, **kwargs: {'text': 'current audio', 'segments': []})
    monkeypatch.setattr(main, 'analyse_video_frames', lambda path: [{'brands': ['Example']}])
    return main


def test_current_video_signals_reach_report(pipeline, monkeypatch):
    observed = []

    def synthesize(data):
        observed.append(data)
        return {'video_summary': 'Current summary'}

    monkeypatch.setattr(pipeline, 'synthesise_insights', synthesize)
    path = pipeline.run_pipeline('https://youtu.be/current')
    assert observed[0]['metadata']['title'] == 'Current video'
    assert observed[0]['transcript']['text'] == 'current audio'
    assert json.loads(path.read_text())['video_summary'] == 'Current summary'


def test_failed_frames_cannot_produce_completed_report(pipeline, monkeypatch):
    monkeypatch.setattr(pipeline, 'analyse_video_frames', lambda path: [{'error': 'api_error'}, {'raw_response': 'bad JSON'}])
    with pytest.raises(RuntimeError, match='No frames'):
        pipeline.run_pipeline('https://youtu.be/current')
    assert not Path('data/frames/current/brand_intelligence_report.json').exists()


def test_invalid_synthesis_cannot_produce_completed_report(pipeline, monkeypatch):
    monkeypatch.setattr(pipeline, 'synthesise_insights', lambda data: {'raw_report': 'bad JSON'})
    with pytest.raises(RuntimeError, match='valid report'):
        pipeline.run_pipeline('https://youtu.be/current')
    assert not Path('data/frames/current/brand_intelligence_report.json').exists()
