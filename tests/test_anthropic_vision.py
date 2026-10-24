from unittest.mock import Mock

import httpx
import pytest

from src import vision_analyser as vision


def test_native_anthropic_image_request(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-only')
    monkeypatch.delenv('VISION_PROVIDER', raising=False)
    response = httpx.Response(200, json={'content': [{'type': 'text', 'text': '{"brands":["Apple"]}'}], 'stop_reason': 'end_turn'})
    post = Mock(return_value=response)
    monkeypatch.setattr(vision.httpx, 'post', post)
    completion, model, provider = vision.create_completion_with_fallback('image-data')
    assert provider == 'anthropic'
    assert 'Apple' in completion.choices[0].message.content
    request = post.call_args.kwargs
    assert request['json']['messages'][0]['content'][0]['source']['data'] == 'image-data'
    assert request['headers']['x-api-key'] == 'test-only'
    assert request['follow_redirects'] is False


def test_missing_key_never_falls_back(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    monkeypatch.setenv('VISION_PROVIDER', 'anthropic')
    with pytest.raises(RuntimeError, match='ANTHROPIC_API_KEY'):
        vision.create_completion_with_fallback('image-data')


def test_provider_error_does_not_expose_response(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-only')
    monkeypatch.setattr(vision.httpx, 'post', Mock(return_value=httpx.Response(401, text='private provider details')))
    with pytest.raises(RuntimeError, match=r'HTTP 401') as error:
        vision.create_anthropic_completion('image-data')
    assert 'private' not in str(error.value)
