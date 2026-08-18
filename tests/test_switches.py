import pytest
from physearth.agent import loop
from physearth.agent.results import _record_tool_result
from physearth.harness import switches, validation

from physearth import harness, prompt, registry, session, tools


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
        "research_plan", "research_capability_check",
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


def test_raw_pdf_mode_exposes_no_structured_knowledge_or_model_card():
    flags = {"paper_access": "raw_pdf", "execution_access": "raw_smrt", "harness": False}
    state = _state(flags)
    assert {item["function"]["name"] for item in tools.specs(flags)} == {
        "read_raw_paper",
        "run_raw_smrt",
        "plot",
    }
    text = prompt.build(state)
    assert "Registered physical models" not in text
    assert "Literature corpus" not in text
    assert "model card" in text.lower()
    assert "complete the smallest end-to-end workflow" in text
    assert "call run_raw_smrt for every comparison requested" in text
    assert "call plot with the returned handles" in text

    page = tools.call(
        "read_raw_paper",
        {"doi": "10.5194/gmd-11-2763-2018", "page": 7, "include_image": False},
        switches_in=flags,
        session=state["session"],
    )
    assert page["status"] == "success"
    assert page["data"]["page_count"] == 26
    assert "sections" not in page["data"]
    assert "figures" not in page["data"]

    blocked = tools.call(
        "run_raw_smrt",
        {"recipe": {}},
        owner=state["session"]["id"],
        switches_in=flags,
        session=state["session"],
    )
    assert blocked["status"] == "needs_input"
    assert blocked["data"]["error_code"] == "evaluation_batch_approval_required"


def test_raw_reproduction_step_advances_from_source_to_run_to_chart():
    raw = {"raw_pdf_pages_read": set(), "successful_runs": [], "figures": []}
    assert loop._raw_reproduction_step(raw)[0] == "read_raw_paper"

    raw["raw_pdf_pages_read"].add("paper#page-1")
    assert loop._raw_reproduction_step(raw)[0] == "run_raw_smrt"

    raw["successful_runs"].append({"handle": "raw-1"})
    assert loop._raw_reproduction_step(raw)[0] == "plot"

    raw["figures"].append({"preview": False})
    assert loop._raw_reproduction_step(raw) is None


def test_approved_raw_smrt_keeps_full_arrays_out_of_the_tool_response(monkeypatch):
    flags = {"paper_access": "raw_pdf", "execution_access": "raw_smrt", "harness": False}
    state = _state(flags)
    state["session"]["evaluation_batch_approved"] = True

    monkeypatch.setattr(
        "physearth.tools.raw._raw_smrt_curve",
        lambda recipe: {
            "axis": {"name": "density_kg_m3", "values": [1.0, 6.0, 11.0]},
            "points": [
                {"index": 0, "density_kg_m3": 1.0, "ks_per_m": 0.1},
                {"index": 1, "density_kg_m3": 6.0, "ks_per_m": 0.2},
                {"index": 2, "density_kg_m3": 11.0, "ks_per_m": 0.3},
            ],
            "series": {"ks_per_m": [0.1, 0.2, 0.3]},
        },
    )
    response = tools.call(
        "run_raw_smrt",
        {
            "recipe": {
                "electromagnetic_model": "free_name",
                "microstructure_model": "free_microstructure",
                "frequency_ghz": 37,
                "densities_kg_m3": [1, 6, 11],
                "radius_m": 0.0001,
                "microstructure_parameters": {"free_parameter": 0.15},
            }
        },
        owner=state["session"]["id"],
        switches_in=flags,
        session=state["session"],
    )
    assert response["status"] == "success"
    assert "series" not in response["data"]
    assert "values" not in response["data"]["axis"]
    assert response["data"]["n_points"] == 3

    _record_tool_result("run_raw_smrt", response, state, [])
    assert len(state["session"]["successful_runs"]) == 1
    assert state["session"]["successful_runs"][0]["handle"] == response["data"]["handle"]


def test_text_only_mode_keeps_harness_and_cards_but_hides_figure_information():
    flags = {"paper_access": "structured_text", "execution_access": "harnessed_smrt"}
    state = _state(flags)
    names = {item["function"]["name"] for item in tools.specs(flags)}
    assert "read_literature" in names
    assert "list_models" in names
    assert "research_plan" in names
    assert "read_paper_figure" not in names
    assert "inspect_paper_figure" not in names
    index = tools.call(
        "read_literature",
        {"slug": "smrt-v1"},
        switches_in=flags,
        session=state["session"],
    )
    assert index["status"] == "success"
    assert index["data"]["figures"] == []
    text = prompt.build(state)
    assert "Registered physical models" in text
    assert "Literature corpus" in text
