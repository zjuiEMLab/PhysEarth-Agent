"""The host side of the approval gate, and checking an answer the host wrote.

No language model is called: the agent turn is driven by a scripted client.
"""

import io
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from physearth import agent

from integrations.physearth import mcp_server, service

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
    assert "physearth_decide" in paused["next_action"]

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


def test_a_cancelled_elicitation_leaves_the_request_for_physearth_decide(asking):
    _client_with_elicitation({"action": "cancel"})
    session_id = service.new_session()["session_id"]

    _, payload = _mcp("run_model", {"session_id": session_id, "model": "smrt"})
    assert payload["status"] == "awaiting_approval"

    mcp_server._CLIENT["elicitation"] = False
    _, payload = _mcp("physearth_decide", {"session_id": session_id, "decision": "approve"})
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
                {"jsonrpc": "2.0", "id": "physearth-elicit-x", "result": {"action": "accept"}},
            )
        )
        + "\n"
    )
    writer = io.StringIO()
    channel = mcp_server._Stdio(reader, writer)

    answer = channel.await_response("physearth-elicit-x")

    assert answer["result"] == {"action": "accept"}
    assert json.loads(writer.getvalue()) == {"jsonrpc": "2.0", "id": "p", "result": {}}
    assert [message["id"] for message in channel.messages()] == [9]


def test_a_real_server_process_asks_over_its_own_pipes(tmp_path):
    server = Path(__file__).resolve().parents[1] / "integrations" / "physearth" / "mcp_server.py"
    process = subprocess.Popen(
        [sys.executable, str(server), "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        cwd=tmp_path,
    )

    def send(message):
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    def receive():
        return json.loads(process.stdout.readline())

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"capabilities": {"elicitation": {}}}})
        receive()
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
              "params": {"name": "run_model", "arguments": {"model": "smrt"}}})
        asked = receive()
        assert asked["method"] == "elicitation/create"
        send({"jsonrpc": "2.0", "id": "p", "method": "ping"})
        send({"jsonrpc": "2.0", "id": asked["id"], "result": {"action": "decline"}})
        assert receive() == {"jsonrpc": "2.0", "id": "p", "result": {}}
        answered = receive()
        assert answered["id"] == 2
        assert answered["result"]["isError"] is True
        assert "declined" in answered["result"]["content"][0]["text"]
    finally:
        process.stdin.close()
        process.wait(timeout=30)


def test_the_operator_chooses_approval_when_the_server_starts(monkeypatch, asking):
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "physearth_session_new", "arguments": {}},
        },
    ]
    monkeypatch.setattr("sys.stdin", io.StringIO("".join(json.dumps(r) + "\n" for r in requests)))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)

    mcp_server.main(["--approval", "always", "--stdio"])

    created = json.loads(out.getvalue().splitlines()[-1])["result"]["content"][0]["text"]
    assert json.loads(created)["approval"] == "always"
    assert service.health()["approval"] == "always"


@pytest.fixture()
def evidenced(monkeypatch):
    """A session that read one section, ran one model and queried one dataset."""
    monkeypatch.setitem(service._OPERATOR, "approval", "always")
    session_id = service.new_session()["session_id"]
    service.call("read_literature", {"slug": "smrt-v1", "section_id": "03"}, session_id=session_id)
    service.call("run_model", json.loads(SINGLE_RUN), session_id=session_id)
    service.call("read_reference_dataset", {"dataset": "tvc-backscatter"}, session_id=session_id)
    model = service.evidence(session_id)["models_run"][0]
    return session_id, model


def test_a_report_whose_markers_resolve_passes(evidenced):
    session_id, model = evidenced
    text = (
        "SMRT treats snow as a layered medium [smrt-v1#03]. The run gave a brightness "
        f"temperature for the default snowpack [model:{model}], and the measured backscatter "
        "is in the reference set [data:tvc-backscatter]."
    )

    report = service.verify_report(session_id, text)

    assert report["passed"] is True, report
    assert [check["rule"] for check in report["checks"]] == [
        "evidence_gate",
        "citation_integrity",
        "abstract_depth",
    ]
    assert report["corrections"] == []


def test_a_marker_for_something_never_read_or_run_fails(evidenced):
    session_id, model = evidenced
    text = f"See [smrt-v1#07] and [model:tau_omega@9.9] and [data:nope], unlike [model:{model}]."

    report = service.verify_report(session_id, text)

    assert report["passed"] is False
    citation = next(c for c in report["checks"] if c["rule"] == "citation_integrity")
    assert set(citation["unresolved"]) == {"smrt-v1#07", "tau_omega@9.9", "nope"}
    assert "citation integrity" in report["corrections"][0]


def test_an_abstract_cannot_carry_a_result_value(evidenced):
    session_id, _ = evidenced

    report = service.verify_report(session_id, "Tb was 213 K [abs:10.5194/gmd-11-2763-2018].")

    failed = {c["rule"] for c in report["checks"] if not c["passed"]}
    assert "abstract_depth" in failed


def test_a_long_answer_with_no_evidence_behind_it_fails():
    session_id = service.new_session()["session_id"]

    report = service.verify_report(session_id, "Snow is bright at 37 GHz. " * 30)

    assert report["passed"] is False
    assert report["checks"][0]["rule"] == "evidence_gate"
    assert report["checks"][0]["passed"] is False


def test_verify_report_through_mcp(evidenced):
    session_id, _ = evidenced

    result, payload = _mcp(
        "physearth_verify_report", {"session_id": session_id, "text": "As read [smrt-v1#03]."}
    )

    assert result["isError"] is False
    assert payload["passed"] is True
    assert service.verify_report("ses_nope", "x")["error"] == "unknown_session"


def test_a_second_turn_on_a_busy_session_is_refused(scripted):
    """A host that times out and asks again must not run a second turn beside the first."""
    sent = scripted([_text("Done.")])
    first = service.ask("A plain question")
    session = service.get_session(first["session_id"])
    service._RUNNING.add(session["id"])
    try:
        busy = service.ask("Again", session_id=session["id"])
    finally:
        service._RUNNING.discard(session["id"])
    assert busy["error"] == "session_busy"
    assert len(sent) == 1
