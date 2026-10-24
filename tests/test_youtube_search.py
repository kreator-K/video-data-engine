import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src import youtube_search
import run_search


def test_search_uses_flat_results_and_filters_duplicates_and_live(monkeypatch):
    downloader = MagicMock()
    downloader.__enter__.return_value = downloader
    downloader.extract_info.return_value = {'entries': [
        {'id': 'abc', 'title': 'First'}, None, {'id': 'abc'},
        {'id': 'live', 'is_live': True}, {'id': 'def', 'title': 'Second'},
    ]}
    factory = MagicMock(return_value=downloader)
    monkeypatch.setattr(youtube_search.yt_dlp, 'YoutubeDL', factory)
    results = youtube_search.search_videos('headphones')
    assert [r['id'] for r in results] == ['abc', 'def']
    downloader.extract_info.assert_called_once_with('ytsearch10:headphones', download=False)
    assert factory.call_args.args[0]['skip_download'] is True


def test_empty_search_rejected():
    with pytest.raises(ValueError):
        youtube_search.search_videos(' ')


def test_search_run_continues_after_failed_video(monkeypatch, tmp_path):
    monkeypatch.setenv('VISION_PROVIDER', 'openai')
    videos = [{'id': str(i), 'title': str(i), 'url': f'https://www.youtube.com/watch?v={i}'} for i in range(10)]
    monkeypatch.setattr(run_search, 'search_videos', lambda query, limit: videos)
    calls = []

    def pipeline(url):
        calls.append(url)
        if url == videos[1]['url']:
            raise RuntimeError('Download failed')
        return tmp_path / 'report.json'

    monkeypatch.setitem(sys.modules, 'main', SimpleNamespace(run_pipeline=pipeline))
    result = run_search.run_search('headphones', tmp_path)
    assert len(calls) == 10
    assert result['results'][1]['status'] == 'failed'
    assert sum(r['status'] == 'completed' for r in result['results']) == 9
    assert json.loads((tmp_path / 'summary.json').read_text()) == result
