"""The method notes and the two increments that live inside the plot tool.

Neither `compare` nor a chart preview is a new medium, so neither gets a tool of its own.
The comparison is a mode of the tool that already holds two curves, and the preview is a
mode of the tool that already knows what a chart of them would look like.
"""

from pathlib import Path

import pytest
from physearth import harness, plotting, prompt, session, tools
from physearth.corpus import knowledge


def _own():
    box = session.new_session("m")
    return box, box["id"]


def test_the_three_declared_method_notes_all_exist_and_are_readable():
    slugs = {item["slug"] for item in knowledge.skills()}
    assert slugs == {"model-comparison", "research-planning", "research-reporting"}
    box, _ = _own()
    for slug in sorted(slugs):
        opened = tools.call("read_literature", {"slug": slug, "section_id": "00"}, session=box)
        assert opened["status"] == "success"
        assert opened["data"]["source"] == "skill"
        assert len(opened["data"]["text"]) > 1500


def test_a_method_note_is_findable_through_the_catalogue_not_only_the_prompt():
    box, _ = _own()
    only_skills = tools.call("list_literature", {"kind": "skill"}, session=box)
    assert {p["slug"] for p in only_skills["data"]["papers"]} == {
        "model-comparison",
        "research-planning",
        "research-reporting",
    }
    only_papers = tools.call("list_literature", {"kind": "paper"}, session=box)
    assert "model-comparison" not in {p["slug"] for p in only_papers["data"]["papers"]}
    both = tools.call("list_literature", {"kind": "any"}, session=box)
    assert len(both["data"]["papers"]) == len(only_papers["data"]["papers"]) + 3


def test_following_a_protocol_is_a_claim_that_has_to_be_earned():
    box, _ = _own()
    state = session.new_state(box)
    claim = "I established comparability first [skill:model-comparison]."
    refused = harness.check_citations(claim, set(), skills_read=state["skills_read"])
    assert refused["unresolved"] == ["skill:model-comparison"]

    from physearth import agent

    opened = tools.call(
        "read_literature", {"slug": "model-comparison", "section_id": "00"}, session=box
    )
    events = []
    agent._record_tool_result("read_literature", opened, state, events)
    assert "model-comparison" in box["skills_read"]
    assert any(e["kind"] == "protocol" for e in events)
    assert harness.check_citations(claim, set(), skills_read=state["skills_read"])["passed"]


def test_reading_the_index_of_a_note_is_not_reading_it():
    box, _ = _own()
    from physearth import agent

    state = session.new_state(box)
    index = tools.call("read_literature", {"slug": "model-comparison"}, session=box)
    agent._record_tool_result("read_literature", index, state, [])
    assert "model-comparison" not in box["skills_read"]


def test_the_prompt_names_the_situation_not_only_the_note():
    text = prompt.build(session.new_state(session.new_session("m")))
    assert "first run_model call of an answer" in text
    assert "put two model runs side by side" in text
    assert "final answer that contains a number" in text
    assert "[skill:slug]" in text


def test_a_preview_needs_no_data_and_says_so():
    box, own = _own()
    result = tools.call(
        "plot",
        {
            "dry_run": True,
            "series": [
                {"x": "density_kg_m3", "y": "tb_v", "label": "SMRT"},
                {"x": "density_kg_m3", "y": "tb_v", "label": "measured", "source": "measured"},
            ],
        },
        owner=own,
    )
    assert result["status"] == "success"
    assert result["data"]["preview"] is True
    assert all(s["n_points"] == 0 for s in result["data"]["series"])
    assert result["ui"]["figure"]["preview"] is True
    assert result["ui"]["figure"]["kind"] == "preview"
    assert result["ui"]["figure"]["image_url"].startswith("/gradio_api/file=")
    assert Path(result["ui"]["figure"]["image_path"]).is_file()
    assert "measured" in result["ui"]["figure"]["provenance"]


def test_a_preview_still_refuses_a_chart_that_makes_no_sense():
    box, own = _own()
    assert tools.call("plot", {"dry_run": True, "series": []}, owner=own)["status"] == (
        "needs_input"
    )
    missing = tools.call("plot", {"dry_run": True, "series": [{"x": "a"}]}, owner=own)
    assert missing["status"] == "needs_input"
    assert "both an x and a y" in missing["error"]


@pytest.fixture
def two_runs():
    box, own = _own()
    first = tools.call(
        "run_model",
        {
            "model": "smrt",
            "parameters": {
                "sweep_parameter": "temperature_k",
                "sweep_start": 240,
                "sweep_stop": 270,
                "sweep_points": 7,
            },
        },
        owner=own,
    )
    second = tools.call(
        "run_model",
        {
            "model": "smrt",
            "parameters": {
                "corr_length_m": 0.0002,
                "sweep_parameter": "temperature_k",
                "sweep_start": 245,
                "sweep_stop": 272,
                "sweep_points": 6,
            },
        },
        owner=own,
    )
    return own, first["data"]["handle"], second["data"]["handle"]


def test_two_comparable_curves_get_statistics_tied_to_their_overlap(two_runs):
    own, a, b = two_runs
    result = tools.call(
        "plot",
        {
            "metrics": ["bias", "rmse", "r"],
            "series": [
                {"handle": a, "x": "temperature_k", "y": "tb_v", "label": "0.15 mm"},
                {"handle": b, "x": "temperature_k", "y": "tb_v", "label": "0.20 mm"},
            ],
        },
        owner=own,
    )
    values = result["data"]["agreement"]
    assert values["unit"] == "K"
    assert values["overlap"] == [245.0, 270.0]
    assert values["n_points"] >= 2
    assert values["bias"] is not None and values["rmse"] >= abs(values["bias"])
    assert "agreement" in result["ui"]["figure"]


def test_a_bias_between_kelvin_and_decibels_is_refused_and_the_chart_survives():
    box, own = _own()
    passive = tools.call(
        "run_model",
        {
            "model": "tau_omega",
            "parameters": {
                "sweep_parameter": "soil_moisture",
                "sweep_start": 0.05,
                "sweep_stop": 0.45,
                "sweep_points": 6,
            },
        },
        owner=own,
    )
    active = tools.call(
        "run_model",
        {
            "model": "water_cloud",
            "parameters": {
                "sweep_parameter": "soil_moisture",
                "sweep_start": 0.05,
                "sweep_stop": 0.45,
                "sweep_points": 6,
            },
        },
        owner=own,
    )
    result = tools.call(
        "plot",
        {
            "metrics": ["bias"],
            "series": [
                {"handle": passive["data"]["handle"], "x": "soil_moisture", "y": "tb_v"},
                {
                    "handle": active["data"]["handle"],
                    "x": "soil_moisture",
                    "y": "sigma0_total_db",
                },
            ],
        },
        owner=own,
    )
    assert result["status"] == "success"
    assert "agreement" not in result["data"]
    assert "different units" in result["data"]["agreement_refused"][0]
    assert Path(result["ui"]["figure"]["image_path"]).is_file()


def test_statistics_are_refused_when_there_is_nothing_to_compare_against(two_runs):
    own, a, _ = two_runs
    alone = tools.call(
        "plot",
        {"metrics": ["bias"], "series": [{"handle": a, "x": "temperature_k", "y": "tb_v"}]},
        owner=own,
    )
    assert "agreement" not in alone["data"]
    assert "exactly two series" in alone["data"]["agreement_refused"][0]


def test_series_that_never_overlap_are_refused_rather_than_extrapolated():
    left = {
        "label": "a",
        "x": [1.0, 2.0, 3.0],
        "y": [1.0, 2.0, 3.0],
        "x_name": "t",
        "y_name": "tb_v",
        "units": {"tb_v": "K"},
        "source": "model_run",
    }
    right = dict(left, label="b", x=[10.0, 11.0], y=[1.0, 2.0])
    values, problems = plotting.agreement([left, right], ["bias"])
    assert values is None
    assert "do not overlap" in problems[0]


def test_figure_quality_blocks_an_abrupt_internal_jump():
    series = [
        {
            "label": "DMRT brightness temperature",
            "x": [100, 150, 200, 250, 300, 350, 400, 450, 500],
            "y": [90, 101, 112, 123, 134, 145, 156, 245, 248],
            "x_name": "density_kg_m3",
            "y_name": "tb_v",
            "source": "model_run",
            "origin": "test",
            "handle": "res_test",
            "units": {"density_kg_m3": "kg m-3", "tb_v": "K"},
        }
    ]
    figure = plotting.render(
        {"kind": "line+markers", "title": "stability check"}, series
    )

    review = plotting.review_quality({"kind": "line+markers"}, series, figure)

    assert review["passed"] is False
    assert any("abrupt adjacent jump" in issue for issue in review["issues"])


def test_figure_quality_warns_but_does_not_fail_on_a_steep_endpoint():
    series = [
        {
            "label": "angular brightness",
            "x": [10, 20, 30, 40, 50, 60],
            "y": [260.0, 260.2, 260.4, 260.6, 260.8, 257.0],
            "x_name": "angle_deg",
            "y_name": "tb_h",
            "source": "model_run",
            "origin": "test",
            "handle": "res_endpoint",
            "units": {"angle_deg": "degree", "tb_h": "K"},
        }
    ]
    figure = plotting.render({"kind": "line", "title": "endpoint check"}, series)

    review = plotting.review_quality({"kind": "line"}, series, figure)

    assert review["passed"] is True
    assert review["issues"] == []
    assert any("endpoint behaviour" in warning for warning in review["warnings"])


def test_the_tool_count_did_not_grow_for_either_increment():
    names = {s["function"]["name"] for s in tools.specs()}
    assert "compare" not in names
    assert "propose_plan" not in names
    assert names == {
        "list_literature",
        "read_literature",
        "list_models",
        "run_model",
        "run_planned_model",
        "plot_planned_chart",
        "read_reference_dataset",
        "plot",
        "discover_literature",
        "ingest_paper",
        "read_research_guideline",
        "read_model_instruction",
        "research_capability_check",
            "read_paper_figure",
            "inspect_paper_figure",
        "register_model_guideline",
        "inspect_github_model_repo",
        "register_github_model_repo",
        "research_plan",
    }


# --- three refusals that used to cost a round trip each --------------------------------


def test_an_enum_near_miss_names_the_values_it_is_close_to():
    """`hard_spheres` is the shared stem of two legal values; the message named neither.

    It listed all six declared values, so the model guessed again and lost another round
    trip. The same near-miss the model-name resolver already handles, one layer down.
    """
    from physearth.harness import validation

    hint = validation._near_miss(
        "hard_spheres",
        ["exponential", "sticky_hard_spheres", "non_sticky_hard_spheres", "independent_sphere"],
    )
    assert "sticky_hard_spheres" in hint and "non_sticky_hard_spheres" in hint

    assert "Did you mean exponential?" in validation._near_miss("exponentia", ["exponential", "gaussian"])
    assert validation._near_miss("zzz", ["exponential", "gaussian"]) == ""
    # a value close to everything says nothing: that is a list, not a suggestion
    assert validation._near_miss("s", ["s_one", "s_two"]) == ""


def test_a_chart_is_refused_while_its_runs_are_outstanding():
    """Drawing before the runs exist produced a wrong chart, then two redraws."""
    from physearth.tools import charts

    requirement = {
        "chart": {"id": "c1", "run_ids": ["r1", "r2", "r3"]},
        "series": [{"run_id": "r1"}, {"run_id": "r2"}],
    }
    missing = charts._runs_still_missing(None, requirement)
    assert missing == ["r3"]

    complete = {**requirement, "series": [{"run_id": "r%d" % n} for n in (1, 2, 3)]}
    assert charts._runs_still_missing(None, complete) == []

    # a chart that names no runs is not waiting on any
    assert charts._runs_still_missing(None, {"chart": {"id": "c2"}, "series": []}) == []
