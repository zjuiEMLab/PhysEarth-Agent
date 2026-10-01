"""The host side of the approval gate.

No language model is called: the agent turn is driven by a scripted client.
"""

import io
import json
from types import SimpleNamespace

import pytest
from physearth import agent

from integrations.geoai import mcp_server, service

SINGLE_RUN = '{"model": "smrt", "parameters": {"output": "tb"}}'


def _text(content):
    delta = SimpleNamespace(content=content, reasoning_content=None, tool_calls=None)
    return [SimpleNamespace(choices=[SimpleNamespace(delta=delta, finish_reason=None)], usage=None)]


def _tool_call(name, arguments):
    part = SimpleNamespace(
        index=0, id="call_1", function=SimpleNamespace(name=name, arguments=arguments)
    )
    delta = SimpleNamespace(content=None, reasoning_content=None, tool_calls=[part])
    return [SimpleNamespace(choices=[SimpleNamespace(delta=delta, finish_reason=None)], usage=None)]


@pytest.fixture()
def scripted(monkeypatch):
    """Install a client that plays a fixed script; returns the requests it was sent."""

    def install(script):
        turns = iter(script)
        sent = []

        def create(**kwargs):
            sent.append(list(kwargs["messages"]))
            return next(turns)

        completions = SimpleNamespace(create=create)
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        monkeypatch.setattr(agent.completion, "_client", lambda: client)
        monkeypatch.setattr(service.config, "has_token", lambda: True)
        return sent

    return install


@pytest.fixture()
def asking(monkeypatch):
    monkeypatch.setitem(service._OPERATOR, "approval", "ask")
    monkeypatch.setitem(mcp_server._CLIENT, "elicitation", False)
    monkeypatch.setitem(mcp_server._CHANNEL, "io", None)


def test_a_turn_pauses_at_a_run_and_the_verdict_resumes_it(scripted, asking):
    sent = scripted([_tool_call("run_model", SINGLE_RUN), _text("SMRT ran.")])
    session_id = service.new_session()["session_id"]

    paused = service.ask("run smrt for me", session_id=session_id)

    assert paused["status"] == "awaiting_approval"
    assert paused["pending"]["tool"] == "run_model"
    assert paused["pending"]["description"]["model"] == "smrt"
    assert paused["evidence"]["models_run"] == []
    assert "geoai_decide" in paused["next_action"]

    resumed = service.decide(session_id, "approve")

    assert resumed["status"] == "success", resumed
    assert "SMRT ran." in resumed["answer"]
    assert any(name.startswith("smrt@") for name in resumed["evidence"]["models_run"])
    assert len(sent) == 2, "the held completion is not requested again"


def test_a_rejected_turn_resumes_with_the_declined_result(scripted, asking):
    sent = scripted([_tool_call("run_model", SINGLE_RUN), _text("I could not run it.")])
    session_id = service.new_session()["session_id"]
    service.ask("run smrt for me", session_id=session_id)

    resumed = service.decide(session_id, "reject")

    assert resumed["status"] == "success"
    assert resumed["evidence"]["models_run"] == []
    assert any("declined" in str(message.get("content")) for message in sent[-1])


def test_a_new_question_drops_the_request_instead_of_running_it(scripted, asking):
    scripted([_tool_call("run_model", SINGLE_RUN), _text("Something else.")])
    session_id = service.new_session()["session_id"]
    service.ask("run smrt for me", session_id=session_id)

    later = service.ask("something else", session_id=session_id)

    assert later["status"] == "success"
    assert later["evidence"]["models_run"] == []
    assert service.decide(session_id, "approve")["error"] == "nothing_pending"


class _Channel:
    """The client end of an elicitation: records what was asked, answers from a script."""

    def __init__(self, answer):
        self.answer = answer
        self.sent = []

    def send(self, message):
        self.sent.append(message)

    def await_response(self, request_id):
        if self.answer is None:
            return None
        return {"jsonrpc": "2.0", "id": request_id, "result": self.answer}


def _mcp(name, arguments):
    response = mcp_server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    return response["result"], json.loads(response["result"]["content"][0]["text"])


def _client_with_elicitation(answer):
    mcp_server.handle(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"capabilities": {"elicitation": {}}},
        }
    )
    channel = _Channel(answer)
    mcp_server._CHANNEL["io"] = channel
    return channel


def test_elicitation_puts_the_run_to_the_person_and_runs_on_accept(asking):
    channel = _client_with_elicitation({"action": "accept", "content": {"approve": True}})
    session_id = service.new_session()["session_id"]

    result, payload = _mcp("run_model", {"session_id": session_id, "model": "smrt"})

    assert result["isError"] is False
    assert payload["status"] == "success"
    assert payload["data"]["handle"]
    asked = channel.sent[0]
    assert asked["method"] == "elicitation/create"
    assert "smrt" in asked["params"]["message"]
    assert "Nothing has been computed" in asked["params"]["message"]


def test_elicitation_declined_or_unticked_is_a_refusal(asking):
    for answer in (
        {"action": "decline"},
        {"action": "accept", "content": {"approve": False}},
    ):
        _client_with_elicitation(answer)
        session_id = service.new_session()["session_id"]

        result, payload = _mcp("run_model", {"session_id": session_id, "model": "smrt"})

        assert result["isError"] is True
        assert "declined" in payload["error"]
        assert service.evidence(session_id)["models_run"] == []


def test_a_cancelled_elicitation_leaves_the_request_for_geoai_decide(asking):
    _client_with_elicitation({"action": "cancel"})
    session_id = service.new_session()["session_id"]

    _, payload = _mcp("run_model", {"session_id": session_id, "model": "smrt"})
    assert payload["status"] == "awaiting_approval"

    mcp_server._CLIENT["elicitation"] = False
    _, payload = _mcp("geoai_decide", {"session_id": session_id, "decision": "approve"})
    assert payload["status"] == "success"


def test_without_elicitation_nothing_is_sent_to_the_client(asking):
    channel = _Channel({"action": "accept"})
    mcp_server._CHANNEL["io"] = channel
    session_id = service.new_session()["session_id"]

    _, payload = _mcp("run_model", {"session_id": session_id, "model": "smrt"})

    assert payload["status"] == "awaiting_approval"
    assert channel.sent == []


def test_the_stdio_channel_keeps_what_arrives_before_the_answer():
    reader = io.StringIO(
        "\n".join(
            json.dumps(message)
            for message in (
                {"jsonrpc": "2.0", "id": "p", "method": "ping"},
                {"jsonrpc": "2.0", "id": 9, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": "geoai-elicit-x", "result": {"action": "accept"}},
            )
        )
        + "\n"
    )
    writer = io.StringIO()
    channel = mcp_server._Stdio(reader, writer)

    answer = channel.await_response("geoai-elicit-x")

    assert answer["result"] == {"action": "accept"}
    assert json.loads(writer.getvalue()) == {"jsonrpc": "2.0", "id": "p", "result": {}}
    assert [message["id"] for message in channel.messages()] == [9]


def test_the_operator_chooses_approval_when_the_server_starts(monkeypatch, asking):
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "geoai_session_new", "arguments": {}},
        },
    ]
    monkeypatch.setattr("sys.stdin", io.StringIO("".join(json.dumps(r) + "\n" for r in requests)))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)

    mcp_server.main(["--approval", "always", "--stdio"])

    created = json.loads(out.getvalue().splitlines()[-1])["result"]["content"][0]["text"]
    assert json.loads(created)["approval"] == "always"
    assert service.health()["approval"] == "always"
