"""Three refusals that between them stopped a Figure 7 reproduction dead.

Each one is a contract defect, not a model mistake: a stand-in value demanded to be the
card default by one rule and past a depth threshold by another; a parameter the adapter
never reads range-checked as if it did; and a figure whose y is solved for reported as
unproducible however it was written.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from physearth import registry, session as session_state, tools  # noqa: E402
from physearth.research import propose  # noqa: E402
from physearth.harness import validation  # noqa: E402
from physearth.research import charts, execution  # noqa: E402


def _card():
    return registry.get("smrt").card


# --------------------------------------------------------------- parameters a run reads


def test_a_parameter_the_run_does_not_read_is_dropped_not_refused():
    """`stickiness = 0.0` is out of range and irrelevant: SMRT sets tau=infinity itself."""
    arguments = {
        "output": "tb", "electromagnetic_model": "iba",
        "microstructure_model": "non_sticky_hard_spheres", "stickiness": 0.0,
        "frequency_ghz": 37.0, "density_kg_m3": 300.0, "temperature_k": 265.0,
        "thickness_m": 100.0, "corr_length_m": 1e-4, "radius_m": 1e-4, "dort_streams": 32,
    }
    spec, problems = validation.resolve(_card(), arguments)
    assert problems == []
    assert "stickiness" not in spec
    dropped = validation.unread(_card(), arguments)
    assert [item["name"] for item in dropped] == ["stickiness"]
    assert "sticky_hard_spheres" in dropped[0]["read_when"]


def test_a_parameter_the_run_does_read_is_still_range_checked():
    """The drop is about being unread, not about being inconvenient."""
    arguments = {
        "output": "tb", "electromagnetic_model": "iba",
        "microstructure_model": "sticky_hard_spheres", "stickiness": 0.0,
        "frequency_ghz": 37.0, "density_kg_m3": 300.0, "temperature_k": 265.0,
        "thickness_m": 100.0, "corr_length_m": 1e-4, "radius_m": 1e-4, "dort_streams": 32,
    }
    spec, problems = validation.resolve(_card(), arguments)
    assert any("outside the physical range" in item for item in problems)
    assert validation.unread(_card(), arguments) == []


def test_the_radius_is_read_by_the_sphere_microstructures_only():
    arguments = {"microstructure_model": "exponential", "radius_m": 9.0}
    assert validation.unread(_card(), arguments)
    arguments = {"microstructure_model": "independent_sphere", "radius_m": 9.0}
    assert validation.unread(_card(), arguments) == []


def test_dropping_an_unread_parameter_is_recorded_as_a_repair():
    """A plan that changes a submitted value says so, and this is visible at review."""
    from physearth.research.normalise import _clean_runs

    runs = [{
        "id": "scale_200", "label": "Non-sticky radius scaling", "model": "smrt",
        "parameters": {
            "output": "tb", "electromagnetic_model": "iba",
            "microstructure_model": "non_sticky_hard_spheres", "stickiness": 0.0,
            "frequency_ghz": 37.0, "density_kg_m3": 200.0, "temperature_k": 265.0,
            "thickness_m": 100.0, "corr_length_m": 1e-4, "radius_m": 1e-4, "dort_streams": 32,
        },
    }]
    cleaned, problems, repairs, _resolutions, _details = _clean_runs(runs)
    assert problems == [] and cleaned
    assert any(item["field"] == "parameters.stickiness" for item in repairs)


# --------------------------------------------------- one rule owns each parameter


def test_a_stand_in_parameter_is_not_asked_to_be_the_card_default():
    """The depth rule and the default rule contradicted each other on `thickness_m`.

    One demanded the card default 1.0 m, the other a value past the depth where the result
    stops changing. A plan that followed either was refused by the other five times.
    """
    from physearth.research import evidence

    session = session_state.new_session("m")
    session["sections_read"] = {"smrt-v1#07"}
    mapping = [{
        "model": "smrt", "model_input": "thickness_m", "mapped_value": 2.0,
        "provenance_class": "model_assumption",
    }]
    targets = [{"id": "fig07", "source_id": "smrt-v1#fig07"}]
    runs = [{"id": "r1", "model": "smrt",
             "parameters": {"thickness_m": 2.0, "substrate": "none"}}]
    # The rule that owns this parameter asks for a depth, and names the number it wants.
    depth = evidence._semi_infinite_problems(session, mapping, targets, runs)
    assert depth, "a 2 m layer is not a stand-in for a semi-infinite medium"
    assert "or more" in depth[0]["expected"]
    assert "Do not use the card default" in depth[0]["repair"]
    # The default rule stays out of it: demanding 1.0 m here was the contradiction.
    assert evidence._unstated_value_problems(session, mapping, runs, targets) == []


def test_a_thick_layer_standing_in_for_the_medium_is_accepted():
    from physearth.research import evidence

    session = session_state.new_session("m")
    session["sections_read"] = {"smrt-v1#07"}
    mapping = [{
        "model": "smrt", "model_input": "thickness_m", "mapped_value": 100.0,
        "provenance_class": "model_assumption", "evidence_ref": "smrt-v1#07",
    }]
    targets = [{"id": "fig07", "source_id": "smrt-v1#fig07"}]
    runs = [{"id": "r1", "model": "smrt",
             "parameters": {"thickness_m": 100.0, "substrate": "none"}}]
    assert evidence._semi_infinite_problems(session, mapping, targets, runs) == []
    assert evidence._unstated_value_problems(session, mapping, runs, targets) == []


# ------------------------------------------------------- a figure whose y is solved for


def _fig7_plan():
    runs = [
        {"id": "sticky_200", "label": "Sticky HS, density 200", "model": "smrt",
         "parameters": {"output": "tb", "microstructure_model": "sticky_hard_spheres",
                        "sweep_parameter": "stickiness", "sweep_start": 0.08, "sweep_stop": 1.0}},
        {"id": "scale_200", "label": "Non-sticky radius scaling, density 200", "model": "smrt",
         "parameters": {"output": "tb", "microstructure_model": "non_sticky_hard_spheres",
                        "sweep_parameter": "radius_m", "sweep_start": 1e-4, "sweep_stop": 4e-4}},
    ]
    plan = {
        "runs": runs,
        "derived": [{
            "id": "scaling_factor", "label": "grain-size scaling factor",
            "operation": "solve_for_parameter", "from_runs": ["scale_200", "sticky_200"],
            "method": "brentq on the brightness-temperature difference",
        }],
        "charts": [{
            "id": "fig07", "label": "Grain-size scaling factor vs stickiness",
            "x": "stickiness", "y": "scaling_factor", "ys": ["scaling_factor"],
            "runs": ["sticky_200", "scale_200"], "required": True,
        }],
    }
    return plan


def test_a_computed_quantity_can_be_plotted_after_all():
    """The plan had no way to say "a script computes this", so no chart could say it."""
    plan = _fig7_plan()
    assert charts._validate_chart_runs(plan["charts"], plan["runs"], plan) == []
    assert charts.scripted_y_names(plan["charts"][0], plan) == ["scaling_factor"]


def test_without_the_declaration_the_chart_is_still_unproducible():
    """The allowance is the declaration, not a loosening of the rule."""
    plan = _fig7_plan()
    problems = charts._validate_chart_runs(plan["charts"], plan["runs"], {"derived": []})
    assert any("no planned run produces scaling_factor" in item for item in problems)


def test_a_computed_quantity_over_an_axis_no_run_sweeps_is_refused():
    plan = _fig7_plan()
    plan["charts"][0]["x"] = "density_kg_m3"
    problems = charts._validate_chart_runs(plan["charts"], plan["runs"], plan)
    assert any("do not sweep density_kg_m3" in item for item in problems)


def test_a_computed_quantity_is_not_mixed_with_model_outputs_in_one_chart():
    plan = _fig7_plan()
    plan["charts"][0]["ys"] = ["scaling_factor", "tb_v"]
    problems = charts._validate_chart_runs(plan["charts"], plan["runs"], plan)
    assert any("mixes the computed quantity" in item for item in problems)


def test_a_derived_step_must_name_a_step_no_tool_provides():
    from physearth.research.normalise import _clean_derived

    runs = _fig7_plan()["runs"]
    cleaned, problems = _clean_derived([{
        "id": "x", "label": "a slope", "operation": "plot_results",
        "from_runs": ["sticky_200"],
    }], runs)
    assert cleaned == [] and any("registered tool computes" in item for item in problems)

    cleaned, problems = _clean_derived([{
        "id": "x", "label": "a value", "operation": "solve_for_parameter",
        "from_runs": ["not_a_run"],
    }], runs)
    assert cleaned == [] and any("not planned" in item for item in problems)

    cleaned, problems = _clean_derived([{
        "id": "scaling_factor", "label": "a value", "operation": "solve_for_parameter",
        "from_runs": ["sticky_200"],
    }], runs)
    assert problems == [] and cleaned[0]["operation"] == "solve_for_parameter"


def test_a_scripted_chart_is_not_waited_for_as_a_run_output():
    """Waiting for a run to produce a solved quantity left the figure missing for ever."""
    box = session_state.new_session("m")
    plan = _fig7_plan()
    box["research"] = {
        "plan": plan, "phase": "chart_selected", "selected_charts": ["fig07"],
        "research_id": box["id"],
    }
    gaps = execution.execution_gaps(box)
    assert [item["chart"]["id"] for item in gaps["missing_derived"]] == ["fig07"]
    assert "scripted step" in gaps["figure_problem"]
    assert "solve_for_parameter" in gaps["figure_problem"]
    assert execution.planned_chart_derived(box, "fig07")[0]["id"] == "scaling_factor"


def test_plotting_a_scripted_chart_says_what_to_do_instead():
    from physearth.harness import approval

    box = session_state.new_session("m")
    box["research"] = {
        "plan": _fig7_plan(), "phase": "approved", "selected_charts": ["fig07"],
        "research_id": box["id"],
    }
    box["research_required"] = True
    approval.set_mode(box, approval.ALWAYS)
    result = tools.call("plot_planned_chart", {"chart_id": "fig07"}, session=box)
    assert result["status"] == "needs_input"
    assert "run_analysis_script" in result["summary"]
    assert "solve_for_parameter" in result["summary"]


def test_the_plan_sheet_says_a_figure_comes_from_a_script():
    from physearth.research import sheet

    built = sheet.build(_fig7_plan())
    assert built["derived"][0]["id"] == "scaling_factor"
    assert built["charts"][0]["scripted"] is True


def test_an_invalid_derived_step_is_refused_rather_than_crashing():
    """The refusal is raised after the closure it calls exists.

    It was called before `refuse` was defined, so a proposal carrying a derived step the
    workflow cannot use died with `UnboundLocalError: cannot access local variable 'refuse'`
    instead of coming back as a repairable refusal -- and only that path reached it.
    """
    box = session_state.new_session("m")
    tools.call("list_models", {"model": "smrt"}, session=box)
    tools.call("read_model_instruction", {"model": "smrt"}, session=box)
    runs = [{
        "id": "sticky_200", "label": "Sticky HS", "model": "smrt",
        "parameters": {
            "output": "tb", "electromagnetic_model": "iba",
            "microstructure_model": "sticky_hard_spheres", "stickiness": 0.2,
            "frequency_ghz": 37.0, "density_kg_m3": 200.0, "temperature_k": 265.0,
            "thickness_m": 100.0, "radius_m": 1e-4, "dort_streams": 32,
            "sweep_parameter": "stickiness", "sweep_start": 0.08, "sweep_stop": 1.0,
            "sweep_points": 5,
        },
    }]
    result = propose(
        box, question="Reproduce Figure 7", objective="scaling equivalence",
        hypothesis="a scaling factor exists", steps=["run", "solve"],
        runs=runs,
        derived=[{
            "id": "scaling_factor", "label": "scaling factor",
            "operation": "plot_results",  # a tool provides this: not a derived step
            "from_runs": ["sticky_200"],
        }],
        charts=[{"id": "fig07", "label": "factor vs stickiness", "x": "stickiness", "y": "tb_v"}],
        quantities=["factor"], controls=["37 GHz"], metrics=["factor"],
        diagnostics=["convergence"], success_criteria=["drawn"],
        stop_conditions=["a run fails"], assumptions=["semi-infinite"],
        limitations=["one frequency"],
    )
    assert result["status"] == "terminal_error"
    assert result["data"]["error_code"] == "derived_quantity_invalid"
    assert any("registered tool computes" in str(item) for item in result["data"]["problems"])


def test_the_script_result_is_what_the_planned_chart_draws():
    """A figure of a computed quantity is drawn from the script's saved result.

    Without this the chart had no series at all: `plot_planned_chart` refused it, the figure
    gate asked for it again, and three refusals stopped the turn -- while the script's result
    sat in the store the whole time.
    """
    from physearth.harness import approval, results

    box = session_state.new_session("m")
    plan = _fig7_plan()
    box["research_required"] = True
    box["research"] = {
        "plan": plan, "phase": "approved", "selected_charts": ["fig07"],
        "research_id": box["id"],
    }
    approval.set_mode(box, approval.ALWAYS)

    # Before the script: no series, the step is named as what is missing.
    assert execution.scripted_series(box, {"chart": plan["charts"][0],
                                           "derived": plan["derived"]}) == []
    gaps = execution.execution_gaps(box)
    assert [item["chart"]["id"] for item in gaps["missing_derived"]] == ["fig07"]
    result = tools.call("plot_planned_chart", {"chart_id": "fig07"}, owner=box["id"], session=box)
    assert result["status"] == "needs_input" and "run_analysis_script" in result["summary"]

    # The script saves the quantity under the name the plan declared.
    handle = results.put({
        "model": "analysis_script", "version": "abc123",
        "spec": {"script_sha256": "abc123", "name": "scaling_factor", "note": ""},
        "axis": {"name": "stickiness", "values": [0.08, 0.2, 1.0]},
        "series": {"scaling_factor": [1.05, 1.25, 2.30]},
        "points": [], "units": {"scaling_factor": "none"}, "diagnostics": {},
    }, box["id"])
    box["analysis_runs"] = [{
        "sha256": "abc123", "saved": ["scaling_factor"],
        "saved_results": [{"name": "scaling_factor", "handle": handle, "points": 3}],
    }]

    series = execution.scripted_series(box, {"chart": plan["charts"][0], "derived": plan["derived"]})
    assert [item["y"] for item in series] == ["scaling_factor"]
    assert series[0]["handle"] == handle and series[0]["x"] == "stickiness"
    assert execution.planned_chart_series(box, "fig07")["series"] == series
    # The step is no longer missing; the figure is.
    gaps = execution.execution_gaps(box)
    assert gaps["missing_derived"] == []
    assert "drawn from the saved script result" in gaps["figure_problem"]


def test_a_saved_result_under_another_name_is_not_the_declared_quantity():
    """Matching is by the name the plan declared, not by any saved result."""
    from physearth.harness import results

    box = session_state.new_session("m")
    plan = _fig7_plan()
    box["research"] = {"plan": plan, "phase": "approved",
                       "selected_charts": ["fig07"], "research_id": box["id"]}
    handle = results.put({
        "model": "analysis_script", "version": "abc",
        "spec": {}, "axis": {"name": "stickiness", "values": [1.0, 2.0]},
        "series": {"something_else": [1.0, 2.0]}, "points": [], "units": {},
    }, box["id"])
    box["analysis_runs"] = [{"saved": ["something_else"],
                             "saved_results": [{"name": "something_else", "handle": handle}]}]
    assert execution.scripted_series(box, {"chart": plan["charts"][0],
                                           "derived": plan["derived"]}) == []
