"""FR-12 model-access tests: cache, retry then fallback (T-12b), give up cleanly."""
import httpx
import pytest
from openai import RateLimitError

import src.llm as llm_module
from src.llm import LLM, ProviderUnavailable, load_prompt


class _Msg:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})


class FakeClient:
    """Mimics client.chat.completions.create with a list of scripted outcomes."""

    def __init__(self, outcomes):
        self.outcomes, self.calls = list(outcomes), 0
        self.chat = type("C", (), {"completions": self})

    def create(self, **_):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return type("R", (), {"choices": [_Msg(outcome)]})


def _rate_limited():
    return RateLimitError("slow down", body=None,
                          response=httpx.Response(429, request=httpx.Request("POST", "http://x")))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(llm_module.time, "sleep", lambda s: None)


PROMPT = load_prompt("PR-02")
VALUES = {"sentences": "<sentence index=\"0\">x</sentence>", "passages": "<passage id=\"a\">x</passage>"}


def test_t12b_rate_limit_retries_then_falls_back(tmp_path):
    primary = FakeClient([_rate_limited()] * llm_module.RATE_LIMIT_RETRIES)
    fallback = FakeClient(['{"results": []}'])
    llm = LLM(cache_dir=str(tmp_path), providers=[("llm", primary, "m1"), ("fallback", fallback, "m2")])
    data, info = llm.complete_json(PROMPT, **VALUES)
    assert data == {"results": []} and info["provider"] == "fallback"
    assert primary.calls == llm_module.RATE_LIMIT_RETRIES and fallback.calls == 1


def test_rate_limit_waits_then_succeeds_on_same_provider(tmp_path):
    client = FakeClient([_rate_limited(), '{"results": []}'])
    llm = LLM(cache_dir=str(tmp_path), providers=[("llm", client, "m1")])
    assert llm.complete_json(PROMPT, **VALUES)[1]["provider"] == "llm" and client.calls == 2


def test_all_providers_down_raises_provider_unavailable(tmp_path):
    llm = LLM(cache_dir=str(tmp_path),
              providers=[("llm", FakeClient([_rate_limited()] * llm_module.RATE_LIMIT_RETRIES), "m1")])
    with pytest.raises(ProviderUnavailable):
        llm.complete_json(PROMPT, **VALUES)


def test_same_inputs_are_answered_from_cache(tmp_path):
    client = FakeClient(['{"results": []}'])
    llm = LLM(cache_dir=str(tmp_path), providers=[("llm", client, "m1")])
    llm.complete_json(PROMPT, **VALUES)
    _, info = llm.complete_json(PROMPT, **VALUES)
    assert info["cached"] and client.calls == 1


def test_bad_json_is_not_cached(tmp_path):
    client = FakeClient(["not json", '{"results": []}'])
    llm = LLM(cache_dir=str(tmp_path), providers=[("llm", client, "m1")])
    with pytest.raises(ValueError):
        llm.complete_json(PROMPT, **VALUES)
    assert llm.complete_json(PROMPT, **VALUES)[0] == {"results": []}
