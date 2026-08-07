from pathlib import Path

from physearth import research, session, tools
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
    assert "data-chart-id='density_curve' disabled" in card
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
    # A button may not silently choose between chart alternatives.
    research.review_action(box, "primary")
    assert box["research"]["phase"] == "pseudo_preview"


def test_complete_requires_real_model_run_and_figure():
    box = session.new_session("m")
    _proposal(box)
    research.approve_plan(box)
    research.pseudo_preview(box)
    research.choose_chart(box, "density_curve")
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

    box["figures"].append({"id": "figure-1", "series": [{"handle": "res-1"}]})
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
    box["figures"].append({"series": [{"handle": "res-1"}]})
    result = research.complete(box)
    assert result["status"] == "needs_input"
    assert "Second theory" in result["summary"]


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
    )
    assert result["status"] == "terminal_error"
    assert "no planned run produces" in result["summary"]


def test_approved_research_refuses_an_unplanned_successful_configuration():
    box = session.new_session("m")
    box["research_required"] = True
    _proposal(box)
    research.approve_plan(box)
    research.pseudo_preview(box)
    research.choose_chart(box, "density_curve")
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


def test_named_literature_model_without_adapter_forces_partial_scope():
    box = session.new_session("m")
    result = _proposal(
        box,
        "How closely do SMRT and MEMLS reproduce the same brightness temperatures?",
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
    )
    assert result["status"] == "terminal_error"
    assert "no planned run produces tb_v" in result["summary"]


def test_safe_report_never_claims_unavailable_cross_model_result():
    box = session.new_session("m")
    _proposal(box, "Compare SMRT and MEMLS brightness temperatures")
    planned = box["research"]["plan"]["runs"][0]
    box["successful_runs"].append(
        {"model": planned["model"], "spec": planned["parameters"], "handle": "res-safe"}
    )
    box["models_run"].add("smrt@1.5.1")
    report = research.safe_report(box)
    assert "partial reproduction" in report
    assert "MEMLS" in report and "not run" in report
    assert "no cross-model agreement metric" in report
