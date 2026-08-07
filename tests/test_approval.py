"""The gate between deciding to run a model and running it."""

import threading
import time

from physearth import agent, approval, session, tools


def _asking():
    box = session.new_session("m")
    approval.set_mode(box, approval.ASK)
    return box


def test_the_gate_is_off_until_something_switches_it_on():
    box = session.new_session("m")
    assert not approval.required(box)
    approval.set_mode(box, approval.ASK)
    assert approval.required(box)


def test_a_headless_run_is_never_held_up():
    """The evaluation suite and every test drive the agent with nobody watching."""
    box = session.new_session("m")
    started = time.perf_counter()
    result = tools.call("run_model", {"model": "smrt"}, owner=box["id"], session=box)
    assert result["status"] == "success"
    assert time.perf_counter() - started < approval.TIMEOUT_S / 2


def test_a_verdict_with_nothing_pending_is_discarded():
    box = _asking()
    assert approval.decide(box, "approve") is False
    approval.request(box, "run_model", {"model": "smrt"})
    assert approval.decide(box, "approve") is True


def test_the_description_is_in_the_reader_s_terms_not_the_model_s():
    described = approval.describe(
        "run_model",
        {
            "model": "smrt",
            "parameters": {
                "frequency_ghz": 37,
                "sweep_parameter": "density_kg_m3",
                "sweep_start": 100,
                "sweep_stop": 500,
                "sweep_points": 9,
            },
        },
    )
    assert described["model"] == "smrt"
    assert described["shape"] == "sweep density_kg_m3 from 100 to 500 in 9 points"
    assert described["parameters"] == {"frequency_ghz": 37}

    single = approval.describe("run_model", {"model": "smrt", "parameters": {"angle_deg": 55}})
    assert single["shape"] == "a single point"


def test_an_unanswered_gate_lets_the_call_through_and_says_so():
    box = _asking()
    approval.request(box, "run_model", {"model": "smrt"})
    started = time.perf_counter()
    verdict = approval.wait(box, timeout=0.2)
    assert verdict["decision"] == "timeout"
    assert time.perf_counter() - started < 2.0
    assert approval.pending(box) is None


def test_a_decision_from_another_thread_releases_the_wait():
    box = _asking()
    approval.request(box, "run_model", {"model": "smrt"})
    threading.Timer(0.05, lambda: approval.decide(box, "reject")).start()
    verdict = approval.wait(box, timeout=5.0)
    assert verdict["decision"] == "reject"


def test_approving_everything_stops_the_gate_asking_again():
    box = _asking()
    approval.request(box, "run_model", {"model": "smrt"})
    approval.decide(box, approval.ALWAYS)
    assert approval.wait(box, timeout=1.0)["decision"] == "approve"
    assert not approval.required(box)


def test_a_declined_call_comes_back_as_an_ordinary_refusal():
    result = approval.declined_result("run_model", {"model": "smrt"})
    assert result["status"] == "needs_input"
    assert "declined" in result["error"]
    assert "Do not repeat it unchanged" in result["data"]["problems"][0]


def test_the_model_cannot_switch_the_gate_off_through_a_tool_call():
    box = _asking()
    tools.call(
        "run_model",
        {"model": "smrt", "parameters": {}, "_switches": {"harness": False}, "approval": "always"},
        owner=box["id"],
        session=box,
    )
    assert approval.required(box)
    assert approval.mode(box) == approval.ASK


def test_tool_arguments_are_canonical_json_even_when_provider_uses_python_syntax():
    values, canonical, note = agent._tool_arguments("{'model': 'smrt',}")
    assert values == {"model": "smrt"}
    assert canonical == '{"model":"smrt"}'
    assert note


def test_unrepairable_tool_arguments_are_not_replayed_to_provider(monkeypatch):
    box = _asking()
    script = [
        [_call_chunk("list_models", "this is not json")],
        [_Chunk(_Delta(content="I could not form the tool call."))],
    ]
    client, sent = _fake_client(script)
    monkeypatch.setattr(agent, "_client", lambda: client)

    final_events = []
    for _, final_events, _ in agent.stream("inspect the models", session=box):
        pass

    assert any(event["kind"] == "tool_arguments_invalid" for event in final_events)
    second_request = sent[1]
    assert not any(message.get("tool_calls") for message in second_request)
    assert any("strict JSON" in message.get("content", "") for message in second_request)


def test_citation_rewrite_discards_invalid_marker_from_pre_tool_narration(monkeypatch):
    box = _asking()
    script = [
        [
            _Chunk(_Delta(content="Working note [smrt-v1#03].")),
            _call_chunk("list_models", '{"model":"smrt"}'),
        ],
        [_Chunk(_Delta(content="Draft still cites [smrt-v1#03]."))],
        [_Chunk(_Delta(content="Verified local model run declaration [model:smrt@1.5.1]."))],
    ]
    client, _ = _fake_client(script)
    monkeypatch.setattr(agent, "_client", lambda: client)

    answer, events, _ = agent.run("inspect smrt", session=box)
    assert "smrt-v1#03" not in answer
    assert "model:smrt@1.5.1" in answer
    assert any(event["kind"] == "harness_pass" for event in events)


class _Delta:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.reasoning_content = None
        self.tool_calls = tool_calls


class _Chunk:
    def __init__(self, delta):
        self.choices = [type("Choice", (), {"delta": delta})()]
        self.usage = None


def _call_chunk(name, arguments):
    part = type(
        "Part",
        (),
        {
            "index": 0,
            "id": "call_1",
            "function": type("Fn", (), {"name": name, "arguments": arguments})(),
        },
    )()
    return _Chunk(_Delta(tool_calls=[part]))


def _fake_client(scripted):
    """A client that plays a fixed script, so the loop can be driven without an endpoint."""
    turns = iter(scripted)
    sent = []

    def create(**kwargs):
        sent.append(list(kwargs["messages"]))
        return next(turns)

    client = type(
        "C",
        (),
        {
            "chat": type(
                "Chat",
                (),
                {"completions": type("Completions", (), {"create": staticmethod(create)})()},
            )()
        },
    )()
    return client, sent


def test_a_declined_call_reaches_the_model_as_a_tool_result(monkeypatch):
    box = _asking()
    script = [
        [_call_chunk("run_model", '{"model": "smrt"}')],
        [_Chunk(_Delta(content="I could not run it, so here is what I can say."))],
    ]
    client, sent = _fake_client(script)
    monkeypatch.setattr(agent, "_client", lambda: client)

    steps = agent.stream("run smrt for me", session=box)
    phases = []
    for _, _events, state in steps:
        phases.append(state.get("phase"))
        if state.get("phase") == "needs_approval":
            approval.decide(box, "reject")

    assert "needs_approval" in phases
    tool_messages = [m for turn in sent for m in turn if m.get("role") == "tool"]
    assert tool_messages, "the model was never told what happened"
    assert "declined" in tool_messages[-1]["content"]
    assert box["model_runs"] == 0


def test_an_approved_call_runs_and_the_gate_is_recorded(monkeypatch):
    box = _asking()
    script = [
        [_call_chunk("run_model", '{"model": "smrt"}')],
        [_Chunk(_Delta(content="It ran [model:smrt@1.5.1]."))],
    ]
    client, _ = _fake_client(script)
    monkeypatch.setattr(agent, "_client", lambda: client)

    kinds = []
    for _, events, state in agent.stream("run smrt", session=box):
        kinds = [e["kind"] for e in events]
        if state.get("phase") == "needs_approval":
            approval.decide(box, "approve")

    assert "approval" in kinds
    assert box["model_runs"] == 1


def test_the_trace_names_what_is_waiting_and_what_was_decided():
    from physearth.ui import render

    waiting = {
        "kind": "approval_wait",
        "at": "00:00:00",
        "rule": "human_approval",
        "name": "run_model",
        "arguments": {"model": "smrt", "parameters": {"frequency_ghz": 37}},
    }
    out = render.trace([waiting], session.new_state(_asking()))
    assert "WAITING FOR YOU" in out
    assert "smrt" in out and "37" in out
    assert "Nothing has been computed yet" in out

    for decision, phrase in (
        ("approve", "You approved"),
        ("reject", "You declined"),
        ("timeout", "Nobody answered"),
    ):
        event = {"kind": "approval", "at": "00:00:00", "rule": "human_approval", "decision": decision}
        assert phrase in render.trace([event], session.new_state(_asking()))


def test_the_approval_bar_appears_only_while_something_waits():
    from physearth.ui import render

    box = _asking()
    assert "hidden" in render.approval_bar(box)
    approval.request(box, "run_model", {"model": "smrt", "parameters": {"frequency_ghz": 37}})
    bar = render.approval_bar(box)
    assert "hidden" not in bar
    assert "smrt" in bar and "a single point" in bar
    approval.decide(box, "approve")
    approval.wait(box, timeout=1.0)
    assert "hidden" in render.approval_bar(box)
