from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import openai
import pytest

from src import synthesiser as synthesis


def provider_error(status, message):
    return openai.APIStatusError(message, response=httpx.Response(
        status, request=httpx.Request("POST", "https://example.com")), body=None)


@pytest.mark.parametrize("status,message,fallback", [
    (400, "maximum context length is 32768 tokens", True),
    (400, "context_length_exceeded", True),
    (401, "Invalid API key", False),
    (429, "Rate limit exceeded", False),
    (400, "Invalid model", False),
])
def test_fallback_routing(monkeypatch, status, message, fallback):
    create = Mock(side_effect=provider_error(status, message))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(synthesis, "nvidia_clients", lambda: [client])
    alternate = Mock(return_value=('{"video_summary":"review"}', "claude-sonnet-4-5"))
    monkeypatch.setattr(synthesis, "anthropic_report", alternate)
    if fallback:
        result = synthesis.synthesise_insights({"transcript": {"text": "complete transcript"}})
        assert result["report_provider_used"] == "anthropic"
        assert result["report_fallback_reason"] == "nvidia_context_limit"
        assert alternate.call_args.args[0] == create.call_args.kwargs["messages"][0]["content"]
    else:
        with pytest.raises(RuntimeError):
            synthesis.synthesise_insights({})
        alternate.assert_not_called()


@pytest.mark.parametrize("payload", [
    {"stop_reason": "max_tokens", "content": [{"type": "text", "text": "partial"}]},
    {"stop_reason": "end_turn", "content": []},
])
def test_incomplete_anthropic_report_rejected(monkeypatch, payload):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only")
    monkeypatch.setattr(synthesis.httpx, "post", Mock(return_value=httpx.Response(200, json=payload)))
    with pytest.raises(RuntimeError):
        synthesis.anthropic_report("prompt")


def test_anthropic_report_request(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only")
    monkeypatch.setenv("ANTHROPIC_REPORT_MODEL", "custom-model")
    post = Mock(return_value=httpx.Response(200, json={"stop_reason": "end_turn", "content": [
        {"type": "text", "text": '{"video_summary":"ok"}'},
    ]}))
    monkeypatch.setattr(synthesis.httpx, "post", post)
    raw, model = synthesis.anthropic_report("full prompt")
    assert model == "custom-model"
    assert raw == '{"video_summary":"ok"}'
    assert post.call_args.kwargs["json"]["messages"][0]["content"] == "full prompt"


def test_nvidia_timeout_falls_back_with_original_prompt(monkeypatch):
    create = Mock(side_effect=openai.APITimeoutError(request=httpx.Request('POST','https://example.com')))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(synthesis,'nvidia_clients',lambda:[client])
    alternate=Mock(return_value=('{"video_summary":"review"}','claude-sonnet-4-5'))
    monkeypatch.setattr(synthesis,'anthropic_report',alternate)
    result=synthesis.synthesise_insights({'transcript':{'text':'real source transcript'}})
    assert result['report_provider_used']=='anthropic'
    assert result['report_fallback_reason']=='nvidia_timeout'
    assert alternate.call_args.args[0]==create.call_args.kwargs['messages'][0]['content']


@pytest.mark.parametrize('failure',[
    httpx.ReadTimeout('read timed out'),
    httpx.ConnectTimeout('connect timed out'),
    TimeoutError('provider deadline'),
])
def test_typed_timeout_is_recognized_through_causal_rotation_wrapper(failure):
    wrapper=RuntimeError('All configured keys failed')
    wrapper.__cause__=failure
    assert synthesis.is_provider_timeout(wrapper) is True


@pytest.mark.parametrize('failure',[
    RuntimeError('timeout mentioned in untyped message'),
    provider_error(401,'Authentication timeout'),
    provider_error(429,'Rate-limit timeout'),
    openai.APIConnectionError(request=httpx.Request('POST','https://example.com')),
])
def test_non_timeout_failures_do_not_trigger_alternate_provider(failure):
    wrapper=RuntimeError('All configured keys failed')
    wrapper.__cause__=failure
    assert synthesis.is_provider_timeout(wrapper) is False


def test_cyclic_exception_chain_does_not_loop():
    first=RuntimeError('first');second=RuntimeError('second')
    first.__cause__=second;second.__cause__=first
    assert synthesis.is_provider_timeout(first) is False
