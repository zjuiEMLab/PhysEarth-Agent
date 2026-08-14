import pytest

from physearth import harness, prompt, session, switches, tools, validation
from physearth.models import registry


def _state(flags=None):
    state = session.new_state(session.new_session("m"))
    state["switches"] = switches.resolve(flags)
    return state


def test_everything_is_on_unless_a_caller_says_otherwise():
    assert switches.resolve(None) == switches.ALL_ON
    assert switches.resolve({}) == switches.ALL_ON
    assert switches.resolve({"harness": False})["harness"] is False
    assert switches.resolve({"harness": False})["literature"] is True
    with pytest.raises(ValueError):
        switches.resolve({"citations": False})


def test_the_model_cannot_reach_a_switch_through_its_arguments():
    forged = tools.call(
        "run_model",
        {"model": "smrt", "parameters": {"density_kg_m3": 2000}, "_switches": {"harness": False}},
    )
    assert forged["status"] == "needs_input"
    assert "outside the physical range" in forged["error"]


def test_the_harness_ablation_lets_an_illegal_call_through():
    guarded = tools.call("run_model", {"model": "smrt", "parameters": {"density_kg_m3": 2000}})
    assert guarded["status"] == "needs_input"
    unguarded = tools.call(
        "run_model",
        {"model": "smrt", "parameters": {"density_kg_m3": 2000}},
        switches_in={"harness": False},
    )
    assert unguarded["status"] != "needs_input"


def test_the_harness_ablation_delivers_an_unresolvable_marker():
    state = _state({"harness": False})
    check, correction = harness.review_final("Snow is cold [smrt-v1#99].", state)
    assert correction is None
    on = _state()
    _, blocked = harness.review_final("Snow is cold [smrt-v1#99].", on)
    assert blocked and "smrt-v1#99" in blocked


def test_the_corpus_ablation_removes_every_literature_tool_and_the_catalogue():
    off = {"literature": False}
    names = [s["function"]["name"] for s in tools.specs(off)]
    assert not set(names) & set(tools.CORPUS_TOOLS)
    assert set(names) == {
        "list_models", "read_model_instruction", "register_model_guideline",
        "register_github_model_repo", "inspect_github_model_repo", "run_model",
        "run_planned_model", "read_reference_dataset", "plot", "plot_planned_chart",
        "research_plan",
    }
    assert tools.call("read_literature", {"slug": "smrt-v1"}, switches_in=off)["status"] == (
        "terminal_error"
    )
    assert tools.call("discover_literature", {"query": "snow"}, switches_in=off)["status"] == (
        "terminal_error"
    )
    text = prompt.build(_state(off))
    assert "Literature corpus" not in text
    assert "read_literature" not in text
    assert "[slug#section_id]" not in text
    assert "run_model" in text


def test_the_capability_ablation_withholds_ranges_but_keeps_enforcement():
    off = {"capability": False}
    text = prompt.build(_state(off))
    assert "50.0 to 917.0" not in text
    assert "density_kg_m3" in text
    assert "constraint:" not in text

    declaration = tools.call("list_models", {"model": "smrt"}, switches_in=off)["data"]
    assert declaration["combinations"] == []
    assert "minimum" not in declaration["parameters"]["density_kg_m3"]
    assert declaration["parameters"]["density_kg_m3"]["unit"] == "kg m-3"

    still_refused = tools.call(
        "run_model", {"model": "smrt", "parameters": {"density_kg_m3": 2000}}, switches_in=off
    )
    assert still_refused["status"] == "needs_input"


def test_an_unenforced_resolve_keeps_the_offending_value_and_still_reports_it():
    card = registry.get("smrt").card
    spec, problems = validation.resolve(card, {"density_kg_m3": 2000}, enforce=False)
    assert spec["density_kg_m3"] == 2000.0
    assert any("outside the physical range" in p for p in problems)
    blocked_spec, blocked = validation.resolve(card, {"density_kg_m3": 2000})
    assert "density_kg_m3" not in blocked_spec
    assert blocked


def test_the_full_configuration_is_what_the_application_runs():
    plain = prompt.build(_state())
    assert prompt.build(session.new_state(session.new_session("m"))) == plain
    assert "Q1 sparse-medium requires exactly six main coefficient runs" not in plain
    assert "read_research_guideline" in plain
    assert "read_model_instruction" in plain
