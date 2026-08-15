from physearth import agent, harness, session, tools
from physearth.harness import results

from frontend import views as render


def test_evidence_read_in_the_first_turn_still_resolves_in_the_third():
    box = session.new_session("m")
    first = session.new_state(box)
    tools_result = tools.call("read_literature", {"slug": "smrt-v1", "section_id": "05"})
    agent._record_tool_result("read_literature", tools_result, first, [])
    assert "smrt-v1#05" in box["sections_read"]

    session.new_state(box)
    third = session.new_state(box)
    check = harness.check_citations("The ACF matters [smrt-v1#05].", third["sections_read"])
    assert check["passed"]


def test_a_model_run_stays_citable_and_replottable_across_turns():
    box = session.new_session("m")
    first = session.new_state(box)
    run = tools.call(
        "run_model",
        {"model": "smrt", "parameters": {"frequency_ghz": 37}},
        owner=box["id"],
    )
    assert run["status"] == "success"
    agent._record_tool_result("run_model", run, first, [])
    handle = run["data"]["handle"]

    later = session.new_state(box)
    assert harness.check_citations(
        "It ran [model:smrt@%s]." % run["data"]["version"], set(), later["models_run"]
    )["passed"]
    assert results.get(handle, box["id"]) is not None
    assert handle in session.held_block(dict(box, turns=2))


def test_a_handle_does_not_read_back_in_another_session():
    mine = session.new_session("m")
    yours = session.new_session("m")
    run = tools.call("run_model", {"model": "smrt"}, owner=mine["id"])
    handle = run["data"]["handle"]
    assert results.get(handle, mine["id"]) is not None
    assert results.get(handle, yours["id"]) is None

    drawn = tools.call(
        "plot",
        {"series": [{"handle": handle, "x": "frequency_ghz", "y": "tb_v"}]},
        owner=yours["id"],
    )
    assert drawn["status"] == "needs_input"
    assert "not a live result handle" in drawn["error"]


def test_the_model_cannot_claim_another_sessions_store():
    mine = session.new_session("m")
    run = tools.call("run_model", {"model": "smrt"}, owner=mine["id"])
    handle = run["data"]["handle"]
    forged = tools.call(
        "plot",
        {
            "series": [{"handle": handle, "x": "frequency_ghz", "y": "tb_v"}],
            "_owner": mine["id"],
        },
        owner="ses_someone_else",
    )
    assert forged["status"] == "needs_input"


def test_call_budgets_are_unlimited_by_default_and_optional_when_configured():
    box = session.new_session("m")
    state = session.new_state(box)
    state["model_calls"] = 1000
    box["model_calls"] = 1000
    assert harness.check_budget(state)["passed"]

    state["max_model_calls"] = 3
    state["model_calls"] = 3
    turn = harness.check_budget(state)
    assert not turn["passed"] and turn["scope"] == "turn"

    fresh = session.new_state(box)
    box["max_model_calls"] = 4
    box["model_calls"] = 4
    spent = harness.check_budget(fresh)
    assert not spent["passed"] and spent["scope"] == "session"


def test_a_counter_moves_in_the_turn_and_in_the_session_together():
    box = session.new_session("m")
    first = session.new_state(box)
    session.bump(first, "model_calls", 3)
    second = session.new_state(box)
    session.bump(second, "model_calls", 2)
    assert first["model_calls"] == 3 and second["model_calls"] == 2
    assert box["model_calls"] == 5


def test_the_held_block_is_bounded_and_never_shown_before_the_first_turn():
    box = session.new_session("m")
    assert session.held_block(box) == ""
    box["turns"] = 1
    for n in range(session.MAX_KEPT_HANDLES + 5):
        session.remember_handle(session.new_state(box), "res_%03d" % n, "row %d" % n)
    assert len(box["handles"]) == session.MAX_KEPT_HANDLES
    block = session.held_block(box)
    assert block.count("res_") == session.MAX_HELD_HANDLES
    assert "res_%03d" % (session.MAX_KEPT_HANDLES + 4) in block
    assert "res_000" not in block


def test_a_dropped_handle_line_does_not_break_the_citation_it_earned():
    box = session.new_session("m")
    box["turns"] = 1
    box["sections_read"] |= {"smrt-v1#%02d" % n for n in range(session.MAX_HELD_SECTIONS + 6)}
    block = session.held_block(box)
    assert "and 6 more" in block
    assert harness.check_citations("[smrt-v1#00]", box["sections_read"])["passed"]


def test_the_trace_meters_report_the_session_not_the_turn():
    box = session.new_session("m")
    box["turns"] = 3
    box["model_calls"] = 20
    state = session.new_state(box)
    state["model_calls"] = 4
    out = render.trace([], state)
    assert "20 / ∞" in out
    assert "4 this question, no hard cap" in out
    assert "3 questions in this session" in out


def test_clearing_a_session_wipes_the_evidence_but_keeps_its_identity():
    box = session.new_session("m")
    box["sections_read"].add("smrt-v1#05")
    box["turns"] = 2
    identity = box["id"]
    session.clear(box)
    assert box["id"] == identity
    assert box["turns"] == 0 and not box["sections_read"]
