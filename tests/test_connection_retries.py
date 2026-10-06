"""Connection faults and timeouts are waited out, not reported after a few seconds."""

import httpx
import openai

from physearth import config
from physearth.agent import completion, constants, faults


def test_timeouts_and_refused_connections_are_connection_faults():
    request = httpx.Request("POST", "https://example.invalid/v1/chat/completions")
    assert faults._connection_fault(openai.APITimeoutError(request=request))
    assert faults._connection_fault(openai.APIConnectionError(request=request))
    assert faults._connection_fault(ConnectionResetError("reset"))
    assert faults._connection_fault(TimeoutError("slow"))


def test_other_faults_keep_their_own_handling():
    assert not faults._connection_fault(ValueError("bad request"))
    assert not faults._connection_fault(RuntimeError("quota"))


def test_the_connection_budget_outlasts_a_short_blip():
    waited = sum(
        min(constants.CONNECTION_BACKOFF_MAX_S, constants.CONNECTION_BACKOFF_S * attempt)
        for attempt in range(1, constants.CONNECTION_RETRIES)
    )
    assert constants.CONNECTION_RETRIES > constants.EMPTY_RESPONSE_RETRIES
    assert waited >= 60


def test_the_client_has_a_connect_timeout_longer_than_the_sdk_default(monkeypatch):
    monkeypatch.setattr(config, "llm_api_key", lambda: "k")
    client = completion._client()
    assert client.timeout.connect == constants.CONNECT_TIMEOUT_S > 5.0
    assert client.timeout.read == constants.REQUEST_TIMEOUT_S
