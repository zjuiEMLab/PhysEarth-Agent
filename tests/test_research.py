from pathlib import Path

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
    assert "data-research-phase='plan_review'" in card
    assert "data-chart-id='density_curve'" in card and "disabled" in card
    research.approve_plan(box)
    research.pseudo_preview(box)
    card = render.approval_bar(box)
    assert "PSEUDO-DATA" in card
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
        box, "Figure 1 shows the baseline. Figure 2 shows the sensitivity result."
    ) == ""


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
