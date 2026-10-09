"""A stop request ends a turn that is waiting out a rate limit, and says so."""

import threading
import time
import types

import openai
import httpx

from physearth.agent import completion, constants, loop


class _AlwaysRateLimited:
    def __init__(self):
        response = httpx.Response(429, request=httpx.Request("POST", "https://example.invalid"))
        self.error = openai.RateLimitError("rate limited", response=response, body=None)
        self.calls = 0
        self.chat = types.SimpleNamespace(completions=self)

    def create(self, **_):
        self.calls += 1
        raise self.error


def test_stop_ends_a_rate_limit_backoff_quickly(monkeypatch):
    client = _AlwaysRateLimited()
    monkeypatch.setattr(completion, "_client", lambda: client)
    monkeypatch.setattr(constants, "RATE_LIMIT_BACKOFF_S", 60)
    monkeypatch.setattr(loop, "RATE_LIMIT_BACKOFF_S", 60)
    session = loop.new_session(None)
    threading.Timer(1.0, lambda: session.__setitem__("stop_requested", True)).start()
    started = time.monotonic()
    final = None
    for final in loop.stream("hello", [], None, session):
        pass
    answer, events, _state = final
    assert time.monotonic() - started < 15
    assert client.calls < constants.RATE_LIMIT_RETRIES
    assert answer == loop.STOP_NOTICE
    assert any(e.get("rule") == "stopped_by_user" for e in events)


def test_a_new_turn_clears_an_old_stop_request(monkeypatch):
    session = loop.new_session(None)
    session["stop_requested"] = True
    stream = loop.stream("hello", [], None, session)
    try:
        next(stream)
    except Exception:
        pass
    assert not loop.stop_requested(session)


def test_a_targets_string_is_not_split_into_characters():
    from physearth.research import capability

    for sent in ("fig3-sparse-medium", '[{"id": "fig3"}]', {"id": "fig3"}):
        specs = capability._target_specs(sent, ["smrt"], [], [])
        assert len(specs) == 1
        assert len(specs[0]["id"]) > 1


def test_a_slow_tool_call_is_abandoned_on_stop():
    session = {}
    threading.Timer(0.5, lambda: session.__setitem__("stop_requested", True)).start()
    started = time.monotonic()
    assert loop._call_watched(session, lambda: time.sleep(30)) is None
    assert time.monotonic() - started < 5
    assert loop._call_watched({}, lambda: "done") == "done"
