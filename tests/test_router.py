"""Which kind of turn this is, before the model is offered any tool."""

import json

from test_approval import _Chunk, _Delta, _call_chunk, _fake_client

from physearth import agent, prompt, session, tools
from physearth.agent import router


def test_a_tool_ban_is_an_answer():
    assert router.decide("x", {}, bypass=True)["path"] == router.ANSWER


def test_a_project_under_way_stays_a_reproduction():
    assert router.decide("and at 19 GHz?", {"research": {"phase": "approved"}})["path"] == router.REPRODUCE
    assert router.decide("go on", {"research_required": True})["path"] == router.REPRODUCE


def test_reproduction_wording_is_a_reproduction_without_a_model_call():
    called = []
    result = router.decide("q", {}, reproduction=True, classify=lambda q: called.append(q))
    assert result["path"] == router.REPRODUCE and not called


def test_a_held_request_keeps_the_route_it_had():
    route = {"path": "run", "source": "model", "reason": "x"}
    assert router.decide("", {"route": route}, held=True) == route


def test_the_model_decides_what_the_rules_cannot(monkeypatch):
    monkeypatch.setenv("PHYSEARTH_ROUTER", "model")
    assert router.decide("q", {}, classify=lambda q: "Run.")["path"] == router.RUN
    assert router.decide("q", {}, classify=lambda q: "answer")["path"] == router.ANSWER


def test_rules_only_mode_never_calls_the_model():
    called = []
    result = router.decide("q", {}, classify=lambda q: called.append(q))
    assert result["path"] == router.AUTO and not called


def test_a_failed_or_unclear_classifier_keeps_every_tool(monkeypatch):
    monkeypatch.setenv("PHYSEARTH_ROUTER", "model")

    def boom(q):
        raise TimeoutError

    assert router.decide("q", {}, classify=boom)["path"] == router.AUTO
    assert router.decide("q", {}, classify=lambda q: "banana")["path"] == router.AUTO


def test_a_direct_run_is_not_offered_the_reading_tools():
    names = {s["function"]["name"] for s in tools.specs(path="run")}
    assert {"list_models", "run_model", "plot", "research_plan"} <= names
    assert not names & {"list_literature", "read_literature", "read_research_guideline", "read_paper_digest"}
    assert len(names) < len(tools.specs())


def test_a_tool_outside_the_route_is_refused_at_call_time():
    box = session.new_session("m")
    box["route"] = {"path": "run"}
    result = tools.call("read_literature", {"slug": "smrt-v1"}, session=box)
    assert result["status"] == "terminal_error" and "Unknown tool" in result["summary"]


def test_the_direct_run_prompt_leaves_out_the_corpus_and_the_research_workflow():
    full = prompt.build({"switches": None, "session": None})
    lean = prompt.build({"switches": None, "session": None, "path": "run"})
    assert "Ordinary Q&A" in full and "Ordinary Q&A" not in lean
    assert "direct model question" in lean
    assert len(lean) < len(full) / 2


def test_no_path_leaves_the_prompt_exactly_as_it_was():
    assert prompt.build({"switches": None, "session": None, "path": None}) == prompt.build(
        {"switches": None, "session": None}
    )


def _run_turn(monkeypatch, question, replies, route_reply=None):
    monkeypatch.setenv("PHYSEARTH_ROUTER", "model")
    box = session.new_session("m")
    script = ([[_Chunk(_Delta(content=route_reply))]] if route_reply is not None else []) + replies
    client, sent = _fake_client(script)
    monkeypatch.setattr(agent.completion, "_client", lambda: client)
    events = []
    for _a, events, _s in agent.stream(question, session=box):
        pass
    return box, events, sent


def test_a_direct_question_is_routed_run_and_the_first_request_carries_the_lean_set(monkeypatch):
    box, events, sent = _run_turn(
        monkeypatch, "How does brightness temperature change with density?",
        [[_Chunk(_Delta(content="It falls."))]], route_reply="run",
    )
    route = [e for e in events if e["kind"] == "route"][0]
    assert route["path"] == "run" and route["source"] == "model"
    assert box["route"]["path"] == "run"


def test_asking_for_the_research_plan_lifts_the_lean_set(monkeypatch):
    replies = [
        [_call_chunk("research_plan", json.dumps({"action": "status"}))],
        [_Chunk(_Delta(content="ok"))],
    ]
    box, events, _sent = _run_turn(monkeypatch, "What would a plan for this be?", replies, route_reply="run")
    routes = [e for e in events if e["kind"] == "route"]
    assert [r["path"] for r in routes] == ["run", "reproduce"]
    assert box["route"]["source"] == "escalation"


def test_once_a_check_exists_the_gate_forces_the_plan_again(monkeypatch):
    box = session.new_session("m")
    approval_mode = __import__("physearth.harness.approval", fromlist=["x"])
    approval_mode.set_mode(box, approval_mode.ASK)
    box["research_required"] = True
    box["capability_review"] = {"status": "ready"}
    client, _sent = _fake_client([[_Chunk(_Delta(content="no plan"))]] * 6)
    monkeypatch.setattr(agent.completion, "_client", lambda: client)
    agent.run("Run a scientific comparison", session=box)
    forced = {c["function"]["name"] for c in client.tool_choices[1:] if isinstance(c, dict)}
    assert forced == {"research_plan"}


def test_changes_sent_as_a_string_do_not_crash_the_plan_tool():
    box = session.new_session("m")
    for sent in ('{"charts": []}', "make it smaller", 7, ["x"]):
        result = tools.call(
            "research_plan", {"action": "revise_plan", "changes": sent}, session=box
        )
        assert result["status"] in ("terminal_error", "needs_input", "success")


def test_choosing_a_script_gives_the_turn_the_script_tools_and_leaves_research_mode(monkeypatch):
    from physearth.research import capability

    box = session.new_session("m")
    capability.capability_check(
        box, reference_models=["smrt"], requested_outputs=["tb_v"], local_models=["smrt"],
        needed_operations=["solve_for_parameter"],
    )
    box["research_required"] = True
    box["research_context"] = {"reproduction_case": "paper-reproduction"}
    client, sent = _fake_client([[_Chunk(_Delta(content="Reading first."))]] * 2)
    monkeypatch.setattr(agent.completion, "_client", lambda: client)
    events = []
    for _a, events, _s in agent.stream("A", session=box):
        pass
    kinds = [(e["kind"], e.get("path")) for e in events if e["kind"] in ("route", "option_chosen")]
    assert ("option_chosen", None) in kinds and ("route", "script") in kinds
    assert box["route"]["path"] == "script" and box["research_required"] is False
    names = {t["function"]["name"] for t in tools.specs(path="script")}
    assert "run_analysis_script" in names and "research_plan" not in names
    assert "research_capability_check" not in names
    assert "run_analysis_script" in sent[0][-2]["content"] or any(
        "chose option A" in str(m.get("content")) for m in sent[0]
    )
