import copy
from pathlib import Path

import pytest

from physearth import agent, research, session, tools
from physearth.ui import render


def _proposal(box, question="How does snow density affect microwave scattering?"):
    return research.propose(
        box,
        question=question,
        objective="Quantify the density response with a registered physical model",
        hypothesis="Scattering changes nonlinearly as density increases.",
        steps=[
            "Inspect the model declaration and relevant literature.",
            "Run a coarse density sweep with quality control.",
            "Refine around the detected transition and test sensitivity.",
            "Plot the result and report uncertainty and limitations.",
        ],
        parameters={"model": "smrt", "sweep_parameter": "density_kg_m3", "sweep_start": 10, "sweep_stop": 500, "sweep_points": 12},
        runs=[
            {
                "id": "smrt_density",
                "label": "SMRT density sweep",
                "model": "smrt",
                "parameters": {
                    "electromagnetic_model": "iba",
                    "microstructure_model": "exponential",
                    "output": "coefficients",
                    "sweep_parameter": "density_kg_m3",
                    "sweep_start": 10,
                    "sweep_stop": 500,
                    "sweep_points": 12,
                },
            }
        ],
        charts=[{"id": "density_curve", "label": "Density response", "kind": "line", "x": "density_kg_m3", "y": "ks_per_m"}],
        success_criteria=["finite outputs", "stable transition under grid refinement"],
        assumptions=["dry homogeneous snow"],
        limitations=["registered models define the executable scope"],
        quantities=["scattering coefficient ks_per_m (m-1)"],
        controls=["frequency and microstructure held fixed"],
        metrics=["relative change and finite-value rate"],
        diagnostics=["grid-resolution sensitivity"],
        stop_conditions=["stop if baseline QC fails"],
        baseline_run_id="smrt_density",
    )


def test_plan_is_supplied_by_the_agent_not_selected_from_benchmark_templates():
    box = session.new_session("m")
    result = _proposal(box, "A completely new soil-moisture research question")
    assert result["status"] == "needs_input"
    assert box["research"]["proposed_by"] == "llm"
    assert box["research"]["question"] == "A completely new soil-moisture research question"
    assert "kind" not in box["research"]


def test_satisfied_figures_is_the_single_final_review_action():
    box = session.new_session("m")
    assert _proposal(box)["status"] == "needs_input"

    assert research.approve_plan(box)["status"] == "needs_input"
    assert research.pseudo_preview(box)["status"] == "needs_input"
    result = research.review_action(box, "satisfied_figures")

    assert result["status"] == "success"
    assert box["research"]["phase"] == "approved"
    duplicate = research.review_action(box, "satisfied_figures")
    assert duplicate["status"] == "success"
    assert "duplicate" in duplicate["summary"].lower()


def test_plan_recovers_missing_prose_steps_when_runs_and_charts_are_executable():
    box = session.new_session("m")
    result = research.propose(
        box,
        question="How does snow density affect microwave scattering?",
        objective="Quantify the density response with a registered physical model",
        hypothesis="Scattering changes nonlinearly as density increases.",
        steps=None,
        runs=[
            {
                "id": "smrt_density",
                "label": "SMRT density sweep",
                "model": "smrt",
                "parameters": {
                    "electromagnetic_model": "iba",
                    "microstructure_model": "exponential",
                    "output": "coefficients",
                    "sweep_parameter": "density_kg_m3",
                    "sweep_start": 10,
                    "sweep_stop": 500,
                    "sweep_points": 12,
                },
            }
        ],
        charts=[{"id": "density_curve", "label": "Density response", "x": "density_kg_m3", "y": "ks_per_m"}],
        quantities=["ks_per_m"],
        controls=["frequency fixed"],
        metrics=["relative change"],
        diagnostics=["grid sensitivity"],
        success_criteria=["finite curve"],
        stop_conditions=["baseline QC failure"],
        assumptions=["dry homogeneous snow"],
        limitations=["registered-model scope"],
        baseline_run_id="smrt_density",
    )

    assert result["status"] == "needs_input"
    plan = box["research"]["plan"]
    assert len(plan["steps"]) == 3
    assert any(
        repair.get("field") == "steps" for repair in plan["automatic_repairs"]
    )


def test_clean_list_accepts_provider_serialized_numbered_steps():
    assert research._clean_list("1. Inspect declarations\n2) Run model; 3. Review figures") == [
        "Inspect declarations",
        "Run model",
        "Review figures",
    ]






def test_q2_named_external_models_are_recorded_as_capability_gaps():
    gaps = research._capability_gaps(
        "Can SMRT reproduce passive and active predictions from DMRT-ML and DMRT-QMS?"
    )

    assert gaps == ["DMRT-ML", "DMRT-QMS"]


def test_capability_checkpoint_pauses_before_an_unavailable_reference_plan():
    box = session.new_session("m")
    tools.call("list_models", {"model": "smrt"}, session=box)
    tools.call("read_model_instruction", {"model": "smrt"}, session=box)
    check = tools.call(
        "research_capability_check",
        {
            "action": "check",
            "reference_models": ["DMRT-ML", "DMRT-QMS"],
            "requested_outputs": ["tb_v", "sigma_vv_db"],
            "local_models": ["smrt"],
        },
        session=box,
    )

    assert check["status"] == "needs_input"
    report = box["capability_review"]
    assert report["status"] == "waiting_user"
    assert {item["model"] for item in report["unavailable"]} == {"DMRT-ML", "DMRT-QMS"}
    assert report["not_comparable"]
    assert box["research"] is None
    if research.registry.get("smrt", box).runnable:
        assert any(item["model"] == "smrt" for item in report["supported"])

    blocked_plan = tools.call(
        "research_plan",
        {
            "action": "propose",
            "question": "Can the paper reproduce DMRT-ML and DMRT-QMS figures?",
            "runs": [],
        },
        session=box,
    )
    assert blocked_plan["status"] == "terminal_error"
    assert blocked_plan["data"]["error_code"] == "capability_review_required"

    confirmed = tools.call(
        "research_capability_check", {"action": "confirm_partial"}, session=box
    )
    assert confirmed["status"] == "success"
    assert box["capability_review"]["status"] == "confirmed"


def test_local_run_cannot_cover_a_different_reference_model_target():
    problems, _, _ = research._target_coverage(
        [{
            "id": "external-figure",
            "reference_models": ["DMRT-ML"],
            "requested_outputs": ["tb_v"],
            "status": "planned",
            "run_ids": ["local"],
            "chart_ids": [],
        }],
        [{
            "id": "local",
            "model": "smrt",
            "parameters": {"output": "tb"},
        }],
        [],
    )
    assert any("not one of reference_models" in problem for problem in problems)




def test_plan_revision_preview_chart_and_execution_gate():
    box = session.new_session("m")
    box["research_required"] = True
    _proposal(box)
    research.revise(box, {"parameters": {"sweep_points": 16}}, "increase resolution")
    assert box["research"]["plan_version"] == 2
    research.approve_plan(box)
    preview = research.pseudo_preview(box)
    assert preview["status"] == "needs_input"
    assert box["research"]["pseudo"]["label"].startswith("PSEUDO-DATA")
    assert box["figures"][-1]["preview"] is True
    assert box["figures"][-1]["research_preview"] is True
    assert Path(box["figures"][-1]["image_path"]).is_file()
    chart_id = box["research"]["plan"]["charts"][0]["id"]
    research.choose_chart(box, chart_id)
    research.confirm_charts(box)
    assert not research.allow_model(box)
    research.approve_execution(box)
    assert research.allow_model(box)


def test_execution_approval_is_idempotent_and_sends_one_continuation():
    import app

    box = session.new_session("m")
    box["research_required"] = True
    _proposal(box)
    research.approve_plan(box)
    research.pseudo_preview(box)
    chart_id = box["research"]["plan"]["charts"][0]["id"]
    research.choose_chart(box, chart_id)
    research.confirm_charts(box)

    first = app.review_click(box, "primary")
    assert box["research"]["phase"] == "approved"
    assert first[3]
    second = app.review_click(box, "primary")
    assert box["research"]["phase"] == "approved"
    assert second[3] == ""


def test_revision_after_preview_creates_new_version_and_clears_stale_preview():
    box = session.new_session("m")
    _proposal(box)
    research.approve_plan(box)
    research.pseudo_preview(box)
    assert box["figures"]

    result = research.revise(
        box,
        {
            "charts": [
                {
                    "id": "density_curve",
                    "label": "Absorption response",
                    "kind": "line",
                    "x": "density_kg_m3",
                    "y": "ka_per_m",
                }
            ]
        },
        "change the plotted observable",
    )

    assert result["status"] == "needs_input"
    assert box["research"]["phase"] == "plan_review"
    assert box["research"]["plan_version"] == 2
    assert box["research"]["pseudo"] is None
    assert not any(figure.get("research_preview") for figure in box["figures"])
    assert box["research"]["review_log"][-1]["note"] == "change the plotted observable"
    assert box["research"]["plan"]["charts"][0]["y"] == "ka_per_m"


def test_revision_rejects_chart_not_produced_by_planned_runs_without_mutation():
    box = session.new_session("m")
    _proposal(box)
    with pytest.raises(ValueError, match="cannot be produced"):
        research.revise(
            box,
            {
                "charts": [
                    {
                        "id": "bad_chart",
                        "label": "Unsupported chart",
                        "kind": "line",
                        "x": "angle_deg",
                        "y": "ks_per_m",
                    }
                ]
            },
        )
    assert box["research"]["plan_version"] == 1
    assert box["research"]["plan"]["charts"][0]["id"] == "density_curve"


def test_invalid_revision_is_transactional_and_keeps_live_plan():
    box = session.new_session("m")
    box["research_required"] = True
    _proposal(box)
    original = copy.deepcopy(box["research"]["plan"])

    result = research.revise(
        box,
        {
            "charts": [
                {"id": "broken", "kind": "line", "x": "radius_m", "y": ["tb_v"]}
            ],
            "runs": [
                {
                    "id": "broken",
                    "model": "smrt",
                    "label": "broken",
                    "parameters": {"sweep_parameter": "not_a_registered_axis"},
                }
            ],
        },
        "invalid partial revision",
    )
    assert result["status"] == "terminal_error"
    assert result["data"]["error_code"] == "run_validation"

    assert box["research"]["plan"] == original


def test_ui_session_cannot_run_model_before_research_approval():
    box = session.new_session("m")
    box["research_required"] = True
    result = tools.call("run_model", {"model": "smrt"}, owner=box["id"], session=box)
    assert result["status"] == "needs_input"
    assert result["data"]["next"] == "research_plan"


def test_language_model_tool_cannot_approve_human_gates():
    spec = next(item for item in tools.SPECS if item["function"]["name"] == "research_plan")
    actions = spec["function"]["parameters"]["properties"]["action"]["enum"]
    assert "approve_plan" not in actions
    assert "approve_execution" not in actions


def test_research_review_card_exposes_agent_plan_and_pseudo_data():
    box = session.new_session("m")
    _proposal(box)
    card = render.approval_bar(box)
    assert "Research review" in card
    assert "research-steps" in card
    assert "Research plan flow" in card
    assert "How to edit this plan" in card
    assert "data-research-phase='plan_review'" in card
    assert "data-chart-id='density_curve'" in card and "disabled" in card
    research.approve_plan(box)
    research.pseudo_preview(box)
    card = render.approval_bar(box)
    assert "PSEUDO-DATA" in card
    assert "Pseudo-data are deterministic layout demonstrations" in card
    assert "Revise plan in chat" in card
    assert "Chart options" in card
    assert "data-chart-id='density_curve' disabled" not in card


def test_pseudo_preview_uses_generic_range_parameter():
    box = session.new_session("m")
    _proposal(box)
    box["research"]["plan"]["parameters"].pop("sweep_start")
    box["research"]["plan"]["parameters"].pop("sweep_stop")
    box["research"]["plan"]["parameters"]["density_range"] = "5 to 400 kg m-3"
    research.approve_plan(box)
    research.pseudo_preview(box)
    points = box["research"]["pseudo"]["points"]
    assert points[0]["density_kg_m3"] == 5.0
    assert points[-1]["density_kg_m3"] == 400.0


def test_pseudo_preview_uses_nested_start_end_and_regeneration_is_visible():
    box = session.new_session("m")
    _proposal(box)
    box["research"]["plan"]["parameters"] = {
        "density_sweep": {"start": 50, "end": 500, "label": "density range"}
    }
    research.approve_plan(box)
    research.pseudo_preview(box)
    first = box["research"]["pseudo"]
    assert first["points"][0]["density_kg_m3"] == 50.0
    assert first["points"][-1]["density_kg_m3"] == 500.0
    research.pseudo_preview(box)
    second = box["research"]["pseudo"]
    assert second["label"].endswith("v002")
    assert second["points"] != first["points"]


def test_review_buttons_advance_only_the_current_human_gate():
    box = session.new_session("m")
    _proposal(box)
    research.review_action(box, "primary")
    assert box["research"]["phase"] == "plan_approved"
    research.review_action(box, "primary")
    assert box["research"]["phase"] == "pseudo_preview"
    # Required figures are preselected; this click confirms the package, but does not
    # approve physical execution.
    research.review_action(box, "primary")
    assert box["research"]["phase"] == "chart_selected"


def test_complete_requires_real_model_run_and_figure():
    box = session.new_session("m")
    _proposal(box)
    research.approve_plan(box)
    research.pseudo_preview(box)
    research.choose_chart(box, "density_curve")
    research.confirm_charts(box)
    research.approve_execution(box)

    result = research.complete(box)
    assert result["status"] == "needs_input"
    assert box["research"]["phase"] == "approved"

    planned = box["research"]["plan"]["runs"][0]
    box["model_runs"] = 1
    box["successful_runs"].append(
        {"model": planned["model"], "spec": planned["parameters"], "handle": "res-1"}
    )
    result = research.complete(box)
    assert result["status"] == "needs_input"

    box["figures"].append({"id": "figure-1", "series": [{"handle": "res-1", "x": "density_kg_m3", "y": "ks_per_m"}]})
    result = research.complete(box)
    assert result["status"] == "success"
    assert box["research"]["phase"] == "completed"


def test_complete_rejects_partial_multi_run_result_and_partial_figure():
    box = session.new_session("m")
    _proposal(box)
    base = box["research"]["plan"]["runs"][0]
    second = {**base, "id": "second", "label": "Second theory", "parameters": {**base["parameters"], "electromagnetic_model": "iba_original"}}
    box["research"]["plan"]["runs"].append(second)
    box["successful_runs"].append({"model": base["model"], "spec": base["parameters"], "handle": "res-1"})
    box["figures"].append({"series": [{"handle": "res-1", "x": "density_kg_m3", "y": "ks_per_m"}]})
    result = research.complete(box)
    assert result["status"] == "needs_input"
    assert "Second theory" in result["summary"]


def test_selected_chart_does_not_require_runs_for_an_unselected_output():
    box = session.new_session("m")
    _proposal(box)
    base = box["research"]["plan"]["runs"][0]
    second_coefficient = {
        **base,
        "id": "coefficient_two",
        "label": "Second coefficient theory",
        "parameters": {**base["parameters"], "electromagnetic_model": "iba_original"},
    }
    first_tb = {
        **base,
        "id": "tb_one",
        "label": "First TB theory",
        "parameters": {**base["parameters"], "output": "tb"},
    }
    second_tb = {
        **second_coefficient,
        "id": "tb_two",
        "label": "Second TB theory",
        "parameters": {**second_coefficient["parameters"], "output": "tb"},
    }
    box["research"]["plan"]["runs"] = [base, second_coefficient, first_tb, second_tb]
    box["research"]["plan"]["charts"].append(
        {"id": "tb_curve", "label": "TB response", "kind": "line", "x": "density_kg_m3", "y": "tb_v", "required": False}
    )
    research.approve_plan(box)
    research.pseudo_preview(box)
    research.choose_chart(box, "density_curve")
    research.confirm_charts(box)
    research.approve_execution(box)

    handles = ["res-coeff-1", "res-coeff-2", "res-tb-1", "res-tb-2"]
    for run, handle in zip(box["research"]["plan"]["runs"], handles, strict=True):
        box["successful_runs"].append(
            {"model": run["model"], "spec": run["parameters"], "handle": handle}
        )
    box["figures"].append(
        {"series": [
            {"handle": "res-coeff-1", "x": "density_kg_m3", "y": "ks_per_m"},
            {"handle": "res-coeff-2", "x": "density_kg_m3", "y": "ks_per_m"},
        ]}
    )

    gaps = research.execution_gaps(box)
    assert gaps["expected_figure_handles"] == ["res-coeff-1", "res-coeff-2"]
    assert not gaps["figure_problem"]
    assert research.complete(box)["status"] == "success"


def test_figure_gap_names_the_missing_selected_run_and_handle():
    box = session.new_session("m")
    _proposal(box)
    base = box["research"]["plan"]["runs"][0]
    second = {
        **base,
        "id": "second",
        "label": "Second theory",
        "parameters": {**base["parameters"], "electromagnetic_model": "iba_original"},
    }
    box["research"]["plan"]["runs"].append(second)
    research.approve_plan(box)
    research.pseudo_preview(box)
    research.choose_chart(box, "density_curve")
    research.confirm_charts(box)
    research.approve_execution(box)
    for run, handle in ((base, "res-1"), (second, "res-2")):
        box["successful_runs"].append(
            {"model": run["model"], "spec": run["parameters"], "handle": handle}
        )
    box["figures"].append({"series": [{"handle": "res-1", "x": "density_kg_m3", "y": "ks_per_m"}]})

    gaps = research.execution_gaps(box)
    assert gaps["missing_figure_series"][0]["run_id"] == "second"
    assert "second=res-2" in gaps["figure_problem"]


def test_plan_rejects_a_chart_axis_that_the_runs_do_not_sweep():
    box = session.new_session("m")
    result = research.propose(
        box,
        question="Find a density threshold",
        objective="Find the threshold",
        hypothesis="A threshold exists",
        steps=["inspect", "run", "plot"],
        runs=[{"id": "one", "label": "single point", "model": "smrt", "parameters": {"output": "tb"}}],
        charts=[{"id": "curve", "label": "curve", "x": "density_kg_m3", "y": "tb_v"}],
        quantities=["tb_v (K)"], controls=["frequency fixed"], metrics=["bias"],
        diagnostics=["finite values"], success_criteria=["valid curve"],
        stop_conditions=["baseline failure"], assumptions=["dry snow"],
        limitations=["single model"], baseline_run_id="one",
    )
    assert result["status"] == "terminal_error"
    assert "no planned run produces" in result["summary"]


def test_plan_repairs_categorical_theory_axis_to_shared_numeric_sweep():
    box = session.new_session("m")
    run = {
        "id": "iba",
        "label": "IBA",
        "model": "smrt",
        "parameters": {
            "output": "coefficients",
            "electromagnetic_model": "iba",
            "microstructure_model": "exponential",
            "sweep_parameter": "density_kg_m3",
            "sweep_start": 100,
            "sweep_stop": 500,
            "sweep_points": 10,
        },
    }
    result = research.propose(
        box,
        question="Compare electromagnetic scattering coefficients between theories",
        objective="Compare theory response over snow density",
        hypothesis="The coefficient curves diverge with density",
        steps=["validate", "run", "compare"],
        runs=[run, {**run, "id": "iba_original", "label": "IBA original", "parameters": {**run["parameters"], "electromagnetic_model": "iba_original"}}],
        charts=[{"id": "coeff", "label": "Coefficient comparison", "x": "electromagnetic_model", "ys": ["ks_per_m"]}],
        quantities=["ks_per_m (m-1)"], controls=["frequency fixed"], metrics=["difference"],
        diagnostics=["finite values"], success_criteria=["valid curves"],
        stop_conditions=["QC failure"], assumptions=["dry snow"], limitations=["model comparison"],
        baseline_run_id="iba",
    )

    assert result["status"] == "needs_input"
    assert box["research"]["plan"]["charts"][0]["x"] == "density_kg_m3"
    assert box["research"]["plan"]["automatic_repairs"][0]["from"] == "electromagnetic_model"


def test_unrepairable_chart_error_returns_structured_repair_hints():
    box = session.new_session("m")
    result = research.propose(
        box,
        question="Compare brightness temperature configurations",
        objective="Compare configurations",
        hypothesis="They differ",
        steps=["validate", "run", "compare"],
        runs=[{"id": "one", "label": "one", "model": "smrt", "parameters": {"output": "tb"}}],
        charts=[{"id": "tb", "label": "TB", "x": "electromagnetic_model", "ys": ["tb_v", "tb_h"]}],
        quantities=["tb_v and tb_h (K)"], controls=["fixed snow"], metrics=["difference"],
        diagnostics=["finite values"], success_criteria=["valid values"],
        stop_conditions=["QC failure"], assumptions=["dry snow"], limitations=["single point"],
        baseline_run_id="one",
    )

    assert result["status"] == "terminal_error"
    assert result["data"]["error_code"] == "chart_axis_mismatch"
    assert result["data"]["repair_hints"]


def test_scalar_baseline_and_diagnostic_need_not_share_the_main_sweep_axis():
    """Auxiliary computations are mandatory runs, not necessarily plotted series."""
    box = session.new_session("m")
    common = {
        "output": "tb",
        "electromagnetic_model": "iba",
        "microstructure_model": "exponential",
    }
    result = research.propose(
        box,
        question="How does brightness temperature vary over density?",
        objective="Compare a density curve with a scalar reference and numerical check",
        hypothesis="The density response crosses the reference",
        steps=["validate", "execute", "review"],
        runs=[
            {
                "id": "reference", "label": "scalar reference", "model": "smrt",
                "stage": "baseline", "parameters": {**common, "density_kg_m3": 300},
            },
            {
                "id": "curve", "label": "density sweep", "model": "smrt",
                "stage": "main", "parameters": {
                    **common, "sweep_parameter": "density_kg_m3",
                    "sweep_start": 150, "sweep_stop": 450, "sweep_points": 9,
                },
            },
            {
                "id": "solver_check", "label": "solver convergence check", "model": "smrt",
                "stage": "diagnostic", "parameters": {
                    **common, "density_kg_m3": 300, "dort_streams": 64,
                },
            },
        ],
        charts=[{
            "id": "tb", "label": "TB over density", "x": "density_kg_m3",
            "ys": ["tb_v", "tb_h"], "required": True,
        }],
        quantities=["tb_v and tb_h (K)"], controls=["dry homogeneous snow"],
        metrics=["reference residual"], diagnostics=["DORT convergence"],
        success_criteria=["finite aligned curve"], stop_conditions=["QC failure"],
        assumptions=["dry snow"], limitations=["single frequency"],
        baseline_run_id="reference",
    )

    assert result["status"] == "needs_input"
    assert box["research"]["phase"] == "plan_review"


def test_tb_h_is_added_when_planned_tb_runs_already_compute_both_polarizations():
    box = session.new_session("m")
    result = research.propose(
        box,
        question="How does microwave brightness temperature transfer across polarizations?",
        objective="Measure both polarizations over density",
        hypothesis="Horizontal and vertical responses differ",
        steps=["validate", "execute", "review"],
        runs=[{
            "id": "tb", "label": "TB sweep", "model": "smrt", "parameters": {
                "output": "tb", "sweep_parameter": "density_kg_m3",
                "sweep_start": 150, "sweep_stop": 450, "sweep_points": 9,
            },
        }],
        charts=[{"id": "tb", "label": "TB", "x": "density_kg_m3", "y": "tb_v"}],
        quantities=["brightness temperature (K)"], controls=["dry snow"],
        metrics=["polarization difference"], diagnostics=["finite"],
        success_criteria=["valid"], stop_conditions=["QC failure"],
        assumptions=["dry snow"], limitations=["single frequency"], baseline_run_id="tb",
    )

    assert result["status"] == "needs_input"
    assert box["research"]["plan"]["charts"][0]["ys"] == ["tb_v", "tb_h"]
    assert any(
        item.get("field") == "ys"
        for item in box["research"]["plan"]["automatic_repairs"]
    )


def test_q4_inversion_plan_is_not_repaired_from_a_stored_protocol():
    box = session.new_session("m")
    box["sections_read"].add("smrt-v1#09")
    question = (
        "Can sticky hard spheres, scaled non-sticky spheres, and exponential "
        "autocorrelation functions be parameterized to produce equivalent microwave "
        "brightness temperatures, and is that equivalence transferable?"
    )
    runs = [{
        "id": "target", "label": "SHS target", "model": "smrt", "stage": "baseline",
        "parameters": {
            "output": "tb", "electromagnetic_model": "iba",
            "microstructure_model": "sticky_hard_spheres", "radius_m": 1e-4,
            "stickiness": 0.13, "density_kg_m3": 300,
        },
    }]
    for density in (150, 200, 300, 400, 500):
        runs.extend([
            {
                "id": f"sphere_{density}", "label": f"sphere {density}", "model": "smrt",
                "stage": "main", "parameters": {
                    "output": "tb", "electromagnetic_model": "iba",
                    "microstructure_model": "independent_sphere", "density_kg_m3": density,
                    "sweep_parameter": "radius_m", "sweep_start": 5e-5,
                    "sweep_stop": 5e-4, "sweep_points": 10,
                },
            },
            {
                "id": f"exp_{density}", "label": f"exponential {density}", "model": "smrt",
                "stage": "main", "parameters": {
                    "output": "tb", "electromagnetic_model": "iba",
                    "microstructure_model": "exponential", "density_kg_m3": density,
                    "sweep_parameter": "corr_length_m", "sweep_start": 5e-5,
                    "sweep_stop": 5e-4, "sweep_points": 10,
                },
            },
        ])
    result = research.propose(
        box, question=question, objective="Invert equivalent microstructure parameters",
        hypothesis="Calibration is local rather than transferable",
        steps=["run target", "sweep candidates", "invert and review"], runs=runs,
        charts=[
            {"id": "mapping_radius", "label": "radius mapping", "x": "stickiness", "y": "radius_m"},
            {"id": "mapping_corr", "label": "correlation mapping", "x": "stickiness", "y": "corr_length_m"},
        ],
        quantities=["tb_v and tb_h (K)"], controls=["density and SSA"],
        metrics=["minimum TB residual", "root uniqueness"],
        diagnostics=["bracket status", "cross-polarization transfer"],
        success_criteria=["finite sweeps and reported residuals"],
        stop_conditions=["unbracketed root is reported, not hidden"],
        assumptions=["dry homogeneous snow"], limitations=["grid inversion"],
        baseline_run_id="target",
    )

    assert result["status"] == "terminal_error"
    assert box["research"] is None


def test_q4_shs_plan_is_not_repaired_from_a_stored_protocol():
    box = session.new_session("m")
    box["sections_read"].add("smrt-v1#09")
    question = (
        "Can sticky hard spheres, scaled non-sticky spheres, and exponential "
        "autocorrelation functions produce equivalent microwave brightness temperatures?"
    )
    result = research.propose(
        box, question=question, objective="Invert matched parameters",
        hypothesis="The match is not unique", steps=["target", "sweep", "invert"],
        runs=[
            {
                "id": "shs", "label": "SHS targets", "model": "smrt", "stage": "main",
                "parameters": {
                    "output": "tb", "electromagnetic_model": "iba",
                    "microstructure_model": "sticky_hard_spheres",
                    "sweep_parameter": "stickiness", "sweep_start": 0.1,
                    "sweep_stop": 1.0, "sweep_points": 8,
                },
            },
            {
                "id": "sphere", "label": "sphere candidates", "model": "smrt", "stage": "main",
                "parameters": {
                    "output": "tb", "electromagnetic_model": "iba",
                    "microstructure_model": "independent_sphere",
                    "sweep_parameter": "radius_m", "sweep_start": 5e-5,
                    "sweep_stop": 5e-4, "sweep_points": 8,
                },
            },
            {
                "id": "exp", "label": "exponential candidates", "model": "smrt", "stage": "main",
                "parameters": {
                    "output": "tb", "electromagnetic_model": "iba",
                    "microstructure_model": "exponential",
                    "sweep_parameter": "corr_length_m", "sweep_start": 5e-5,
                    "sweep_stop": 5e-4, "sweep_points": 8,
                },
            },
        ],
        charts=[
            {"id": "phi_shs", "label": "phi SHS", "x": "stickiness", "y": "phi_shs"},
            {"id": "phi_exp", "label": "phi exp", "x": "stickiness", "y": "phi_exp"},
        ],
        quantities=["tb_v and tb_h"], controls=["dry snow"], metrics=["root residual"],
        diagnostics=["uniqueness"], success_criteria=["finite roots"],
        stop_conditions=["report missing bracket"], assumptions=["homogeneous layer"],
        limitations=["grid inversion"], baseline_run_id="shs",
    )
    assert result["status"] == "terminal_error"
    assert box["research"] is None


def test_q4_shs_transfer_plan_is_not_repaired_from_a_stored_protocol():
    box = session.new_session("m")
    box["sections_read"].add("smrt-v1#09")
    question = (
        "Can sticky hard spheres, scaled non-sticky spheres, and exponential "
        "autocorrelation functions produce equivalent brightness temperatures, and "
        "is the equivalence transferable across densities?"
    )
    common = {"output": "tb", "electromagnetic_model": "iba", "density_kg_m3": 150}
    result = research.propose(
        box, question=question, objective="Test transferability",
        hypothesis="The mapping changes with density", steps=["target", "sweep", "compare"],
        runs=[
            {"id": "shs_150", "label": "SHS reference at 150", "model": "smrt",
             "stage": "sensitivity", "parameters": {**common,
                 "microstructure_model": "sticky_hard_spheres",
                 "sweep_parameter": "stickiness", "sweep_start": 0.05,
                 "sweep_stop": 2.0, "sweep_points": 12}},
            {"id": "sphere_150", "label": "sphere candidates", "model": "smrt",
             "stage": "sensitivity", "parameters": {**common,
                 "microstructure_model": "independent_sphere",
                 "sweep_parameter": "radius_m", "sweep_start": 3e-5,
                 "sweep_stop": 3e-4, "sweep_points": 12}},
            {"id": "exp_150", "label": "exponential candidates", "model": "smrt",
             "stage": "sensitivity", "parameters": {**common,
                 "microstructure_model": "exponential",
                 "sweep_parameter": "corr_length_m", "sweep_start": 5e-5,
                 "sweep_stop": 5e-4, "sweep_points": 12}},
        ],
        charts=[
            {"id": "radius", "label": "radius response", "x": "radius_m", "y": "tb_v"},
            {"id": "corr", "label": "corr response", "x": "corr_length_m", "y": "tb_v"},
        ],
        quantities=["tb_v"], controls=["same density"], metrics=["minimum residual"],
        diagnostics=["uniqueness"], success_criteria=["finite"], stop_conditions=["QC"],
        assumptions=["dry snow"], limitations=["grid inversion"], baseline_run_id="shs_150",
    )
    assert result["status"] == "terminal_error"
    assert box["research"] is None


def test_q4_transferability_does_not_receive_hidden_protocol_charts():
    box = session.new_session("m")
    box["sections_read"].add("smrt-v1#09")
    question = (
        "Can sticky hard spheres, scaled non-sticky spheres, and exponential "
        "autocorrelation functions be parameterized to produce equivalent microwave "
        "brightness temperatures, and is that equivalence transferable across densities, "
        "frequencies, incidence angles, and polarizations?"
    )
    common = {"model": "smrt", "stage": "main"}
    base_parameters = {
        "output": "tb", "electromagnetic_model": "iba", "density_kg_m3": 300,
        "frequency_ghz": 37, "angle_deg": 55,
    }
    runs = [
        {"id": "shs", "label": "SHS baseline", "model": "smrt", "stage": "baseline",
         "parameters": {**base_parameters, "microstructure_model": "sticky_hard_spheres",
                        "stickiness": 0.13}},
        {"id": "radius", "label": "IS radius tuning", **common,
         "parameters": {**base_parameters, "microstructure_model": "independent_sphere",
                        "sweep_parameter": "radius_m", "sweep_start": 1e-4,
                        "sweep_stop": 5e-4, "sweep_points": 10}},
        {"id": "corr", "label": "EACF tuning", **common,
         "parameters": {**base_parameters, "microstructure_model": "exponential",
                        "sweep_parameter": "corr_length_m", "sweep_start": 5e-5,
                        "sweep_stop": 3e-4, "sweep_points": 10}},
    ]
    for axis, start, stop in (
        ("density_kg_m3", 100, 500), ("frequency_ghz", 10, 37), ("angle_deg", 30, 70)
    ):
        for microstructure, extra in (
            ("sticky_hard_spheres", {"stickiness": 0.13}),
            ("independent_sphere", {"radius_m": 2.5e-4}),
            ("exponential", {"corr_length_m": 1.8e-4}),
        ):
            runs.append({
                "id": f"{axis}_{microstructure}", "label": f"{microstructure} {axis}",
                **common, "parameters": {
                    **base_parameters, **extra, "microstructure_model": microstructure,
                    "sweep_parameter": axis, "sweep_start": start,
                    "sweep_stop": stop, "sweep_points": 10,
                },
            })
    result = research.propose(
        box, question=question, objective="Test local equivalence and transferability",
        hypothesis="A local match will not transfer", steps=["calibrate", "transfer", "review"],
        runs=runs,
        charts=[
            {"id": "phi_radius", "label": "radius mapping", "x": "stickiness", "y": "phi_shs"},
            {"id": "density", "label": "density", "x": "density_kg_m3", "ys": ["tb_v", "tb_h"]},
            {"id": "frequency", "label": "frequency", "x": "frequency_ghz", "ys": ["tb_v", "tb_h"]},
            {"id": "angle", "label": "angle", "x": "angle_deg", "ys": ["tb_v", "tb_h"]},
        ],
        quantities=["tb_v and tb_h"], controls=["same snow state"], metrics=["RMSE"],
        diagnostics=["polarization transfer"], success_criteria=["finite curves"],
        stop_conditions=["QC failure"], assumptions=["dry snow"],
        limitations=["grid calibration"], baseline_run_id="shs",
    )
    assert result["status"] == "terminal_error", result["summary"]
    assert "paper_conditions" not in result["summary"]
    assert "proposed chart cannot be produced" in result["summary"]
    assert box["research"] is None


def test_revise_plan_recovers_retained_rejected_draft():
    box = session.new_session("m")
    rejected = tools.research_plan(
        action="propose", question="q", objective="o", hypothesis="h",
        steps=["one", "two", "three"], runs=[], charts=[], _session=box,
    )
    assert rejected["status"] == "terminal_error"
    result = tools.research_plan(
        action="revise_plan",
        changes={
            "runs": [{"id": "tb", "label": "TB", "model": "smrt", "parameters": {
                "output": "tb", "sweep_parameter": "density_kg_m3",
                "sweep_start": 150, "sweep_stop": 450, "sweep_points": 9,
            }}],
            "charts": [{"id": "tb", "label": "TB", "x": "density_kg_m3", "y": "tb_v"}],
            "quantities": ["tb_v"], "controls": ["dry snow"], "metrics": ["trend"],
            "diagnostics": ["finite"], "success_criteria": ["valid"],
            "stop_conditions": ["QC"], "assumptions": ["dry snow"],
            "limitations": ["single model"], "baseline_run_id": "tb",
        },
        _session=box,
    )
    assert result["status"] == "needs_input"
    assert box["research"]["phase"] == "plan_review"


def test_research_plan_tolerates_provider_supplemental_metadata():
    box = session.new_session("m")
    result = tools.call(
        "research_plan",
        {
            "action": "propose", "question": "Plot brightness temperature",
            "objective": "Measure a density trend", "hypothesis": "TB changes",
            "steps": ["validate", "execute", "review"],
            "runs": [{"id": "tb", "label": "TB", "model": "smrt", "parameters": {
                "output": "tb", "sweep_parameter": "density_kg_m3",
                "sweep_start": 150, "sweep_stop": 450, "sweep_points": 9,
            }}],
            "charts": [{"id": "tb", "label": "TB", "x": "density_kg_m3", "y": "tb_v"}],
            "quantities": ["tb_v"], "controls": ["dry snow"], "metrics": ["trend"],
            "diagnostics": ["finite"], "success_criteria": ["valid"],
            "stop_conditions": ["QC"], "assumptions": ["dry snow"],
            "limitations": ["single model"], "baseline_run_id": "tb",
            "units": ["K"], "variables": ["density_kg_m3", "tb_v"],
        },
        session=box,
    )
    assert result["status"] == "needs_input"
    assert box["research"]["plan"]["supplemental_metadata"] == {
        "units": ["K"], "variables": ["density_kg_m3", "tb_v"]
    }


def test_rejected_plan_is_retained_for_harness_recovery():
    box = session.new_session("m")
    result = tools.research_plan(
        action="propose", question="q", objective="o", hypothesis="h",
        steps=["one", "two", "three"], runs=[], charts=[], _session=box,
    )
    assert result["status"] == "terminal_error"
    status = tools.research_plan(action="status", _session=box)
    assert status["status"] == "needs_input"
    assert status["data"]["phase"] == "draft_recovery"
    assert status["data"]["proposal"]["question"] == "q"


def test_sweep_bound_outside_registered_model_range_is_blocked_with_source_details():
    box = session.new_session("m")
    result = research.propose(
        box, question="How does brightness temperature vary with correlation length?",
        objective="Run the full legal correlation-length range",
        hypothesis="TB changes with correlation length", steps=["validate", "run", "review"],
        runs=[{
            "id": "exp", "label": "exponential sweep", "model": "smrt", "parameters": {
                "output": "tb", "electromagnetic_model": "iba",
                "microstructure_model": "exponential",
                "sweep_parameter": "corr_length_m", "sweep_start": 1e-4,
                "sweep_stop": 5e-3, "sweep_points": 10,
            },
        }],
        charts=[{"id": "tb", "label": "TB", "x": "corr_length_m", "ys": ["tb_v", "tb_h"]}],
        quantities=["tb_v and tb_h"], controls=["dry snow"], metrics=["trend"],
        diagnostics=["finite"], success_criteria=["valid"], stop_conditions=["QC failure"],
        assumptions=["homogeneous layer"], limitations=["single frequency"], baseline_run_id="exp",
    )
    assert result["status"] == "terminal_error"
    assert result["data"]["error_code"] == "run_validation"
    problem = result["data"]["problems"][0]
    assert problem["field"].endswith("sweep_stop")
    assert problem["source"] == "registered_model_declaration"
    assert "0.003" in problem["expected"]
    assert problem["actual"] == 0.005
    assert problem["blocking"] is True


def test_unplotted_main_run_is_still_rejected():
    box = session.new_session("m")
    result = research.propose(
        box,
        question="Compare brightness temperature sweeps",
        objective="Ensure every main result is represented",
        hypothesis="Both sweeps matter",
        steps=["validate", "execute", "review"],
        runs=[
            {
                "id": "density", "label": "density main", "model": "smrt",
                "stage": "main", "parameters": {
                    "output": "tb", "sweep_parameter": "density_kg_m3",
                    "sweep_start": 150, "sweep_stop": 450, "sweep_points": 9,
                },
            },
            {
                "id": "angle", "label": "angle main", "model": "smrt",
                "stage": "main", "parameters": {
                    "output": "tb", "sweep_parameter": "angle_deg",
                    "sweep_start": 10, "sweep_stop": 60, "sweep_points": 11,
                },
            },
        ],
        charts=[{"id": "tb", "label": "TB density", "x": "density_kg_m3", "ys": ["tb_v", "tb_h"]}],
        quantities=["tb_v and tb_h (K)"], controls=["dry snow"], metrics=["difference"],
        diagnostics=["finite"], success_criteria=["valid"], stop_conditions=["QC failure"],
        assumptions=["dry snow"], limitations=["single model"], baseline_run_id="density",
    )

    assert result["status"] == "terminal_error"
    assert "angle main contributes to none" in result["summary"]


def test_coefficients_cannot_be_swept_over_dort_solver_streams():
    box = session.new_session("m")
    result = research.propose(
        box,
        question="Test coefficient and solver sensitivity",
        objective="Separate medium coefficients from solver effects",
        hypothesis="DORT affects TB but not coefficients",
        steps=["validate", "run", "compare"],
        runs=[{
            "id": "coeff", "label": "coefficients", "model": "smrt",
            "parameters": {
                "output": "coefficients", "sweep_parameter": "dort_streams",
                "sweep_start": 8, "sweep_stop": 32, "sweep_points": 3,
            },
        }],
        charts=[{"id": "coeff", "label": "coefficients", "x": "dort_streams", "ys": ["ka_per_m", "ks_per_m"]}],
        quantities=["ka and ks"], controls=["snow fixed"], metrics=["difference"],
        diagnostics=["finite"], success_criteria=["valid"], stop_conditions=["QC"],
        assumptions=["dry snow"], limitations=["single model"], baseline_run_id="coeff",
    )

    assert result["status"] == "terminal_error"
    assert result["data"]["error_code"] == "output_independent_sweep"
    assert "computed before the DORT solver" in result["summary"]


def test_under_resolved_line_sweep_is_densified_before_human_review():
    box = session.new_session("m")
    run = {
        "id": "tb", "label": "TB", "model": "smrt",
        "parameters": {
            "output": "tb", "sweep_parameter": "dort_streams",
            "sweep_start": 8, "sweep_stop": 32, "sweep_points": 3,
        },
    }
    result = research.propose(
        box, question="Test solver convergence", objective="Check TB convergence",
        hypothesis="TB stabilizes", steps=["validate", "run", "compare"], runs=[run],
        charts=[{"id": "tb", "label": "TB", "x": "dort_streams", "ys": ["tb_v", "tb_h"]}],
        quantities=["TB (K)"], controls=["snow fixed"], metrics=["difference"],
        diagnostics=["convergence"], success_criteria=["stable"], stop_conditions=["QC"],
        assumptions=["dry snow"], limitations=["single model"], baseline_run_id="tb",
    )

    assert result["status"] == "needs_input"
    assert box["research"]["plan"]["runs"][0]["parameters"]["sweep_points"] == 8
    assert any(item["field"] == "sweep_points" for item in box["research"]["plan"]["automatic_repairs"])


def test_failed_figure_quality_reopens_and_repairs_the_plan():
    box = session.new_session("m")
    _proposal(box)
    project = box["research"]
    run = project["plan"]["runs"][0]
    run["parameters"].update(
        output="coefficients", sweep_parameter="dort_streams",
        sweep_start=8.0, sweep_stop=32.0, sweep_points=3,
    )
    chart = project["plan"]["charts"][0]
    chart.update(x="dort_streams", y="ks_per_m", ys=["ks_per_m", "ka_per_m"])
    project["phase"] = "approved"
    project["selected_charts"] = [chart["id"]]
    box["figures"] = [{"planned_chart_id": chart["id"], "quality_review": {"reviewed": True, "passed": False}}]

    result = research.revise_after_figure_quality(box, chart["id"], ["only 3 points"])

    assert result["status"] == "needs_input"
    assert project["phase"] == "plan_review"
    assert run["parameters"]["sweep_parameter"] == "density_kg_m3"
    assert run["parameters"]["sweep_points"] == 10
    assert chart["x"] == "density_kg_m3"
    assert box["figures"] == []


def test_dort_failure_creates_a_consistent_human_reviewed_recovery_plan():
    box = session.new_session("m")
    _proposal(box)
    project = box["research"]
    first = project["plan"]["runs"][0]
    first.update(id="qca_sigma", label="QCA sigma")
    first["parameters"].update(
        electromagnetic_model="dmrt_qca_shortrange",
        microstructure_model="sticky_hard_spheres",
        output="sigma",
        radius_m=0.00015,
    )
    second = {
        **first,
        "id": "qcacp_sigma",
        "label": "QCA-CP sigma",
        "parameters": {
            **first["parameters"],
            "electromagnetic_model": "dmrt_qcacp_shortrange",
        },
    }
    project["plan"]["runs"].append(second)
    project["phase"] = "approved"
    project["selected_charts"] = ["density_curve"]
    box["figures"] = [{"planned_chart_id": "density_curve"}]
    failures = [
        {
            "run_id": "qca_sigma",
            "spec": dict(first["parameters"]),
            "error_code": "dort_diagonalization",
            "recoverable": True,
            "error": "failed at density_kg_m3=450",
        }
    ]

    result = research.revise_after_run_failures(box, failures)

    assert result["status"] == "needs_input"
    assert project["phase"] == "plan_review"
    assert project["plan_version"] == 2
    assert all(
        run["parameters"]["radius_m"] == pytest.approx(0.00012)
        for run in project["plan"]["runs"]
    )
    assert project["recovery"]["failed_run_ids"] == ["qca_sigma"]
    assert project["recovery"]["requires_human_review"] is True
    assert project["selected_charts"] == []
    assert box["figures"] == []


def test_execution_gaps_expose_failed_planned_runs_by_exact_spec():
    box = session.new_session("m")
    _proposal(box)
    run = box["research"]["plan"]["runs"][0]
    box["failed_runs"].append(
        {
            "run_id": run["id"],
            "spec": dict(run["parameters"]),
            "error_code": "dort_diagonalization",
            "recoverable": True,
        }
    )

    gaps = research.execution_gaps(box)

    assert gaps["failed_run_ids"] == [run["id"]]
    assert gaps["failed_runs"][0]["error_code"] == "dort_diagonalization"


def test_abrupt_figure_jump_auto_repairs_inside_the_approved_execution():
    box = session.new_session("m")
    _proposal(box)
    project = box["research"]
    run = project["plan"]["runs"][0]
    run["parameters"]["sweep_points"] = 10
    project["phase"] = "approved"
    project["selected_charts"] = ["density_curve"]
    box["figures"] = [{"planned_chart_id": "density_curve"}]

    result = research.revise_after_figure_quality(
        box,
        "density_curve",
        ["curve has an abrupt adjacent jump between x=400 and x=450"],
    )

    assert result["status"] == "success"
    assert project["phase"] == "approved"
    assert project["selected_charts"] == ["density_curve"]
    assert result["data"]["next"] == "rerun_repaired_runs"
    assert result["data"]["affected_run_ids"] == ["smrt_density"]
    assert run["parameters"]["sweep_points"] == 20
    assert any(
        item.get("reason") == "refine the grid around a possible numerical discontinuity"
        for item in project["plan"]["automatic_repairs"]
    )


def test_unresolved_figure_quality_pauses_without_regenerating_the_plan():
    box = session.new_session("m")
    _proposal(box)
    project = box["research"]
    project["phase"] = "approved"
    project["selected_charts"] = ["density_curve"]
    project["plan"]["runs"][0]["parameters"]["sweep_points"] = 40
    version = project["plan_version"]

    box["figures"] = [
        {
            "planned_chart_id": "density_curve",
            "quality_review": {"reviewed": True, "passed": False, "warnings": []},
        }
    ]
    result = research.revise_after_figure_quality(
        box,
        "density_curve",
        ["curve has an abrupt adjacent jump between x=400 and x=450"],
    )

    assert result["status"] == "success"
    assert result["data"]["next"] == "continue_with_qualified_figure"
    assert project["phase"] == "approved"
    assert project["plan_version"] == version
    assert project["selected_charts"] == ["density_curve"]
    assert box["figures"][0]["quality_review"]["passed"] is True
    assert box["figures"][0]["quality_review"]["passed_with_warning"] is True
    assert project["scientific_anomalies"][0]["kind"] == "persistent_discontinuity"


def test_approved_research_refuses_an_unplanned_successful_configuration():
    box = session.new_session("m")
    box["research_required"] = True
    _proposal(box)
    research.approve_plan(box)
    research.pseudo_preview(box)
    research.choose_chart(box, "density_curve")
    research.confirm_charts(box)
    research.approve_execution(box)

    result = tools.call(
        "run_model",
        {"model": "smrt", "parameters": {"output": "tb"}},
        owner=box["id"],
        session=box,
    )
    assert result["status"] == "needs_input"
    assert "not one of the approved" in result["summary"]
    assert box["model_runs"] == 0


def test_planned_run_id_executes_exact_approved_spec_and_reuses_handle():
    box = session.new_session("m")
    box["research_required"] = True
    _proposal(box)
    research.approve_plan(box)
    research.pseudo_preview(box)
    research.choose_chart(box, "density_curve")
    research.confirm_charts(box)
    research.approve_execution(box)
    planned = box["research"]["plan"]["runs"][0]

    first = tools.call(
        "run_planned_model",
        {"run_id": planned["id"]},
        owner=box["id"],
        session=box,
    )
    assert first["status"] == "success"
    assert first["data"]["spec"] == planned["parameters"]
    assert first["data"]["reused"] is False
    agent._record_tool_result("run_planned_model", first, session.new_state(box), [])

    second = tools.call(
        "run_planned_model",
        {"run_id": planned["id"]},
        owner=box["id"],
        session=box,
    )
    assert second["status"] == "success"
    assert second["data"]["reused"] is True
    assert second["data"]["handle"] == first["data"]["handle"]


def test_cached_result_is_registered_for_a_second_planned_run_id_without_looping():
    box = session.new_session("m")
    box["research_required"] = True
    _proposal(box)
    original = box["research"]["plan"]["runs"][0]
    duplicate = dict(original, id="validation_baseline", label="Validation baseline")
    duplicate["parameters"] = dict(original["parameters"])
    box["research"]["plan"]["runs"].append(duplicate)
    research.approve_plan(box)
    research.pseudo_preview(box)
    research.confirm_charts(box)
    research.approve_execution(box)

    first = tools.call(
        "run_planned_model", {"run_id": original["id"]}, owner=box["id"], session=box
    )
    state = session.new_state(box)
    agent._record_tool_result("run_planned_model", first, state, [])
    reused = tools.call(
        "run_planned_model", {"run_id": duplicate["id"]}, owner=box["id"], session=box
    )
    assert reused["data"]["reused"] is True
    agent._record_tool_result("run_planned_model", reused, state, [])

    gaps = research.execution_gaps(box)
    assert gaps["missing_run_ids"] == []
    assert {row["run_id"] for row in gaps["matched_runs"]} == {
        original["id"], duplicate["id"]
    }
    requirement = gaps["chart_requirements"][0]
    assert len(requirement["series"]) == 1


def test_planned_chart_expands_multiple_compatible_outputs_and_completes():
    box = session.new_session("m")
    box["research_required"] = True
    _proposal(box)
    box["research"]["plan"]["runs"][0]["label"] = (
        "SMRT density sweep with a deliberately long publication legend label"
    )
    box["research"]["plan"]["charts"][0]["ys"] = ["ks_per_m", "ka_per_m"]
    research.approve_plan(box)
    research.pseudo_preview(box)
    research.confirm_charts(box)
    research.approve_execution(box)

    run = tools.call(
        "run_planned_model", {"run_id": "smrt_density"}, owner=box["id"], session=box
    )
    state = session.new_state(box)
    agent._record_tool_result("run_planned_model", run, state, [])
    figure = tools.call(
        "plot_planned_chart", {"chart_id": "density_curve"}, owner=box["id"], session=box
    )
    assert figure["status"] == "success"
    assert [item["y"] for item in figure["ui"]["figure"]["series"]] == [
        "ks_per_m", "ka_per_m"
    ]
    agent._record_tool_result("plot_planned_chart", figure, state, [])
    review = tools.call(
        "plot_planned_chart",
        {"chart_id": "density_curve", "action": "review"},
        owner=box["id"], session=box,
    )
    assert review["status"] == "success"
    assert review["data"]["quality_review"]["passed"] is True
    assert review["data"]["quality_review"]["redrawn"] is True
    agent._record_tool_result("plot_planned_chart", review, state, [])
    assert research.complete(box)["status"] == "success"


def test_preview_figures_are_removed_when_figure_package_is_confirmed():
    box = session.new_session("m")
    _proposal(box)
    research.approve_plan(box)
    research.pseudo_preview(box)
    assert box["figures"] and all(figure.get("research_preview") for figure in box["figures"])

    research.confirm_charts(box)

    assert box["research"]["phase"] == "chart_selected"
    assert box["figures"] == []


def test_multiple_formal_figures_require_numbered_report_explanations():
    box = session.new_session("m")
    _proposal(box)
    box["figures"] = [
        {"figure_number": 1, "preview": False},
        {"figure_number": 2, "preview": False},
    ]
    assert "Figure 2" in research.report_problem(box, "Figure 1 shows the baseline.")
    assert research.report_problem(
        box,
        "Figure 1 shows the baseline trend. Figure 2 shows the sensitivity result. "
        "Therefore, the results show that the response is sensitive to the tested control.",
    ) == ""


def test_figure_qa_status_message_is_not_accepted_as_final_scientific_report():
    box = session.new_session("m")
    _proposal(box)
    box["figures"] = [
        {"figure_number": 1, "preview": False},
        {"figure_number": 2, "preview": False},
    ]
    problem = research.report_warnings(
        box,
        "Figure 1 passed QA. Figure 2 passed QA. The formal execution and QA phase is "
        "complete. The final scientific report can now be delivered.",
    )
    assert "not the final scientific report" in problem
    assert not research.report_problem(
        box,
        "Figure 1 shows a rising baseline while Figure 2 shows the transfer test diverging. "
        "The results show that the calibrated relationship is condition dependent. Therefore, "
        "we conclude that the hypothesis is supported within the tested range; the limited "
        "frequency range remains a limitation.",
    )


def test_named_literature_model_without_adapter_forces_partial_scope():
    box = session.new_session("m")
    result = _proposal(
        box,
        "How closely do SMRT and MEMLS reproduce the same scattering coefficient?",
    )
    assert result["status"] == "needs_input"
    plan = box["research"]["plan"]
    assert plan["outcome_scope"] == "partial"
    assert "MEMLS" in plan["capability_gaps"]
    assert research.report_problem(box, "The SMRT curve is shown.")
    assert not research.report_problem(
        box, "This is a partial reproduction: MEMLS is not registered and was not run."
    )


def test_coefficients_run_cannot_promise_a_brightness_temperature_chart():
    box = session.new_session("m")
    result = research.propose(
        box,
        question="Plot brightness temperature",
        objective="Plot brightness temperature",
        hypothesis="It changes",
        steps=["inspect", "run", "plot"],
        runs=[{
            "id": "coeff",
            "label": "coefficients only",
            "model": "smrt",
            "parameters": {
                "output": "coefficients",
                "sweep_parameter": "density_kg_m3",
                "sweep_start": 100,
                "sweep_stop": 500,
                "sweep_points": 10,
            },
        }],
        charts=[{"id": "tb", "label": "TB", "x": "density_kg_m3", "y": "tb_v"}],
        quantities=["tb_v (K)"], controls=["frequency fixed"], metrics=["bias"],
        diagnostics=["finite values"], success_criteria=["valid curve"],
        stop_conditions=["baseline failure"], assumptions=["dry snow"],
        limitations=["single model"], baseline_run_id="coeff",
    )
    assert result["status"] == "terminal_error"
    assert "no planned run produces tb_v" in result["summary"]


def test_safe_report_never_claims_unavailable_cross_model_result():
    box = session.new_session("m")
    _proposal(box, "Compare SMRT and MEMLS scattering coefficients")
    planned = box["research"]["plan"]["runs"][0]
    box["successful_runs"].append(
        {"model": planned["model"], "spec": planned["parameters"], "handle": "res-safe"}
    )
    box["models_run"].add("smrt@1.5.1")
    report = research.safe_report(box)
    assert "partial reproduction" in report
    assert "MEMLS" in report and "not run" in report
    assert "no cross-model agreement metric" in report


def test_question_coverage_gate_rejects_single_curve_for_multi_stage_attribution():
    box = session.new_session("m")
    result = _proposal(
        box,
        "When SMRT and MEMLS use the same properties, compare electromagnetic coefficients "
        "and brightness temperatures and attribute the difference to the IBA absorption "
        "formulation versus the DORT solver.",
    )
    assert result["status"] == "terminal_error"
    assert "ka_per_m" in result["summary"]
    assert "tb_v" in result["summary"] and "tb_h" in result["summary"]
    assert "dort_streams" in result["summary"]
