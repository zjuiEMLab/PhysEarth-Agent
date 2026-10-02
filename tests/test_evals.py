import re
from pathlib import Path

from apps.studio.views import evaluation as evals


def test_guided_dashboard_is_bounded_to_q1_for_offline_testing():
    cases = evals.guided_demo_cases()
    q1_card = evals.demo_card(cases[0])

    assert len(cases) == 1
    assert cases[0]["id"] == "smrt-q1-guided"
    assert cases[0]["button_label"] == "Start guided Q1 reproduction"
    assert "doi.org/10.5194/gmd-11-2763-2018" in q1_card
    assert "Paper context" in q1_card
    assert "Reproduce:" in q1_card
    assert "Paper section:</b> 3.1.1" in q1_card
    assert "Figure 3" in q1_card
    assert "smrt-v1#08" not in q1_card
    assert len(cases[0]["required_runs"]) == 6
    assert cases[0]["fixed"]["radius_m"] == 0.0001

    # The question copied into Live Agent must identify the paper and the source
    # figures explicitly, rather than relying on the card that the user just left.
    assert cases[0]["question"].startswith(
        "Reproduce Figure 3: Sparse-medium scattering coefficient comparison"
    )
    assert "SMRT:" in cases[0]["question"]
    assert "DOI: 10.5194/gmd-11-2763-2018" in cases[0]["question"]
    assert "Section 3.1.1" in cases[0]["question"]
    assert "Answer the following question:" in cases[0]["question"]
    assert "Use the six legal" not in cases[0]["question"]
    assert "registered model" not in cases[0]["question"]


def test_q1_radar_aggregation_uses_median_range_and_keeps_na_out_of_scores():
    def record(figure_score, report_score=None):
        return {
            "dashboard_metrics": {
                "successful": True,
                "figure_judgement": {"scores": {"patterns": figure_score}}
                if figure_score is not None else {"status": "not_scoreable"},
                "report_judgement": {"scores": {"factuality": report_score}}
                if report_score is not None else {"status": "not_scoreable"},
            }
        }

    records = [record(0), record(2), record(None)]
    figure = evals._axis_aggregate(records, "figure_judgement", "patterns")
    report = evals._axis_aggregate(records, "report_judgement", "factuality")

    assert figure == {"median": 1.0, "minimum": 0.0, "maximum": 2.0, "count": 2, "total": 3}
    assert report["median"] is None
    assert report["count"] == 0
    assert evals._q1_axis_display(figure) == "1 / 2 (0-2; 2/3)"
    assert evals._q1_axis_display(report) == "N/A (3/3)"


def test_q1_radar_labels_have_gutter_and_readable_wrapped_spacing():
    axes = (
        ("line_count", "Curve count", ""),
        ("patterns", "Pattern fidelity", ""),
        ("grouping", "Grouping/order", ""),
        ("visual_correspondence", "Visual correspondence", ""),
    )
    svg = evals._q1_radar_svg(
        "Figure judge radar",
        axes,
        {
            "full": [{"aggregate": {"median": 2}} for _ in axes],
            "no-harness": [{"aggregate": {"median": 2}} for _ in axes],
        },
    )

    assert "viewBox='0 0 600 440'" in svg
    assert "x='141.0'" in svg  # 34px label gutter on the left axis
    assert "dy='20'" in svg  # wrapped labels are not vertically compressed


def test_q1_axis_reasons_use_saved_judgement_or_rubric_fallback():
    records = [{
        "dashboard_metrics": {
            "figure_judgement": {
                "scores": {"patterns": 1},
                "observations": ["The candidate is linear where the reference is convex."],
            },
            "report_judgement": {"scores": {"clarity": 1}, "factual_errors": []},
        }
    }]
    figure = evals._q1_axis_records(
        records,
        "figure_judgement",
        evals.Q1_FIGURE_AXES,
        evals.EVALUATION / "standards" / "q1_figure3.yaml",
        "visual_judge",
    )
    report = evals._q1_axis_records(
        records,
        "report_judgement",
        evals.Q1_REPORT_AXES,
        evals.EVALUATION / "standards" / "report_judge.yaml",
        "",
    )

    assert "linear" in next(item for item in figure if item["key"] == "patterns")["reason"]
    assert "versions" in next(item for item in report if item["key"] == "clarity")["reason"]


def test_basic_cases_keep_the_three_supported_live_prompts():
    cases = evals.basic_cases()

    assert len(cases) == 3
    assert cases[0]["question"].startswith("Run SMRT to show how 37 GHz")
    assert "soil moisture" in cases[1]["question"]
    assert "Do not use any tools" in cases[2]["question"]
    assert all(case["id"] != "basic-tvc-observation" for case in cases)


def test_architecture_comparison_is_embedded_as_a_maintainable_svg():
    page = evals.architecture()

    assert "Why a research harness matters" in page
    assert "plain LLM + RAG + model-code pipeline" in page
    assert "data:image/svg+xml;base64," in page
    assert "PhysEarth-Agent architecture" in page


def test_reproduction_evaluation_is_truthful_when_records_exist():
    page = evals.reproduction_evaluation()
    if page:
        assert "Paper reproduction across three LLMs" in page
        assert "Protocol" in page
        assert "Visual" in page
        assert "not a claimed curve RMSE" in page


def test_gradio_exposes_evaluation_upload_and_agent_tabs_and_demo_prefill_handlers():
    from apps.studio import studio as app

    assert app.main_tabs.get_config()["selected"] == "evaluation"
    upload_tabs = [
        component for component in app.demo.blocks.values()
        if hasattr(component, "get_config")
        and component.get_config().get("elem_id") == "pe-upload-tab"
    ]
    assert len(upload_tabs) == 1
    assert upload_tabs[0].get_config().get("visible") is False
    page_html = "\n".join(
        str(component.get_config().get("value", ""))
        for component in app.demo.blocks.values()
        if component.__class__.__name__ == "HTML"
    )
    assert "Register a model" in page_html  # remains implemented in the hidden workbench
    assert "Figure 3 reproduction: what users care about" in page_html
    assert "LLM robustness" not in page_html
    assert "What the evaluation shows" not in page_html
    assert "Inspect the recorded score tables" not in page_html
    assert "RUNNABLE MODELS" not in page_html
    assert "Raw PDF + raw SMRT" in page_html
    assert "Text-only harness" not in page_html
    css = Path("apps/studio/static/ui.css").read_text(encoding="utf-8")
    workflow_css = re.search(r"\.eval-workflow\s*\{(?P<body>.*?)\}", css, re.DOTALL)
    assert workflow_css and "font-size: 14px" in workflow_css.group("body")
    assert len(app.basic_evaluation_cases) == 3
    assert len(app.evaluation_cases) == 4
    assert len(app.guided_evaluation_cases) == 1
    demo_handlers = [
        dependency
        for dependency in app.demo.fns.values()
        if getattr(getattr(dependency, "fn", None), "__name__", "") == "<lambda>"
    ]
    assert len(demo_handlers) >= 4
