"""Archived with reproduction_eval and llm_robustness, and with the
run records, tier0.json, the Q2 demo and the no-figures condition removed in 35eee2c."""

import json
from pathlib import Path

import yaml

from evaluation.metrics import score
from evaluation.runners import llm_robustness, reproduction_eval
from frontend.views import evaluation as evals


def test_reproduction_visual_checks_follow_each_planned_figure_target():
    session = {
        "research": {
            "plan": {
                "charts": [{"id": "fig05-radius", "target_ids": ["fig05.png"]}],
                "reproduction_targets": [
                    {"id": "fig04.png", "source_id": "smrt-v1#fig04"},
                    {"id": "fig05.png", "source_id": "smrt-v1#fig05"},
                ],
            }
        }
    }
    candidates, linked = reproduction_eval._paper_figures_for_generated(
        {"planned_chart_id": "fig05-radius"}, session, ["fig04.png", "fig05.png"]
    )

    assert candidates == ["fig05.png"]
    assert linked is True


def test_dimension_d_never_mixes_legacy_or_different_builds():
    design = {
        "comparison_rule": "same condition", "repeats": 1, "tasks": ["task"],
        "prompt_profiles": [{"id": "P1"}],
        "llms": [{"id": "a", "provider": "one"}, {"id": "b", "provider": "two"}],
    }
    base = {
        "task": "task", "build": "same", "completed": True, "figure_count": 1,
        "protocol": {"paper_protocol_similarity": 1.0}, "elapsed_s": 10,
        "tokens": {"total": 100, "peak_prompt": 20},
    }
    records = [dict(base, llm="a"), dict(base, llm="b")]
    report = llm_robustness.evaluate(records, design)

    assert report["status"] == "passed"
    assert report["coverage"] == {"recorded": 2, "expected": 2}
    assert report["comparable_groups"] == 1

    records[1]["build"] = "different"
    report = llm_robustness.evaluate(records, design)
    assert report["comparable_groups"] == 0


def test_dimension_d_uses_archived_reproduction_records_and_exposes_failure():
    report = llm_robustness.evaluate()

    assert report["status"] == "passed"
    assert report["coverage"] == {"recorded": 12, "expected": 12}
    assert report["completed"] == 11
    assert report["models"] == 3
    assert report["tasks"] == 4
    assert report["repeats"] == 1
    failed = [cell for cell in report["cells"] if not cell["completed"]]
    assert len(failed) == 1
    assert failed[0]["llm"] == "qwen-plus"
    assert failed[0]["stop_reason"] == "evaluation_turn_limit"
    assert failed[0]["root_cause"] == "physical_model_failure"


def test_evaluation_snapshot_covers_every_committed_case_and_run():
    data = evals.snapshot()

    assert data["tier0"]["n_tasks"] == 9
    assert data["tier0"]["n_checks"] == 38
    assert data["tier0"]["n_passed"] == 9
    assert len(data["tasks"]) == 12
    assert len(data["scored"]) == 50
    assert {item["config"] for item in data["scored"]} == set(evals.CONFIG_ORDER)


def test_evaluation_landing_page_orders_introduction_cases_and_scores():
    dashboard = evals.dashboard()
    summary = evals.score_summary()
    details = evals.score_details()
    required = evals.required_evaluations()

    assert "What the agent does" in dashboard
    assert "Reproduce papers" in dashboard
    assert "Run real experiments" in dashboard
    assert "Register your own model" in dashboard
    assert "9 / 9" in summary
    assert "38 / 38" in summary
    assert "Remove a safeguard" in summary
    assert "Register a physical model" in required
    assert "20 / 20" not in required  # section totals remain decomposed and auditable
    assert "LLM robustness" in required
    assert "12 / 12" in required
    assert "92%" in required
    assert "qwen-max" in required
    assert "physical_model_failure" in required
    for config in evals.CONFIG_ORDER:
        assert config in summary
    for task_id in evals.snapshot()["tasks"]:
        assert task_id in details


def test_demo_cases_are_exact_prompts_from_the_evaluation_set():
    cases = evals.demo_cases()

    assert len(cases) == 4
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(case["id"].startswith("q") for case in cases)
    assert all(case["paper"] == "smrt-v1" for case in cases)
    assert all("SMRT:" in case["paper_title"] for case in cases)
    assert all(case["paper_doi"] == "10.5194/gmd-11-2763-2018" for case in cases)
    assert [case["paper_section"] for case in cases] == ["3.1.1", "3.1.2", "3.1.3", "3.2"]
    assert [case["paper_figures"] for case in cases] == [
        ["fig03.png"],
        ["fig04.png", "fig05.png"],
        ["fig06.png"],
        ["fig07.png", "fig08.png"],
    ]
    figure_root = Path("catalog/knowledge/literature/smrt-v1/figures")
    assert all(
        (figure_root / figure).is_file()
        for case in cases
        for figure in case["paper_figures"]
    )
    assert all(
        "Reproduce Figure" in case["question"] or "Reproduce Figures" in case["question"]
        for case in cases
    )
    assert "DMRT-ML" in cases[1]["question"]
    assert "MEMLS" in cases[2]["question"]


def test_q2_keeps_figure_four_and_five_checks_separate():
    """A two-figure demo must name both figures, and the figures must differ.

    This test used to assert reference_models == ["DMRT-ML", "DMRT-QMS"] for figure 4.
    That is demo knowledge written into a test: it pins an answer rather than a
    mechanism, it goes stale the moment the figure or the registry changes, and it is
    what AGENTS.md now warns against. Which names are unsupported is the registry's
    verdict, computed from each figure's own legend in the literature card.

    So this checks the two things the task is actually responsible for: that it asks for
    both figures, and that the card can tell them apart.
    """
    from physearth.corpus import knowledge

    task = evals.canonical_task("q2-dmrt-comparison")
    figures = task.get("paper_figures") or []
    assert len(figures) >= 2, f"a two-figure demo has to name both: {figures}"

    card = knowledge.card("smrt-v1") or {}
    declared = {item["id"]: item for item in card.get("figures") or [] if item.get("id")}
    ids = [str(name).split(".")[0] for name in figures]
    assert all(figure_id in declared for figure_id in ids), (
        f"the task names figures the card does not declare: {ids}"
    )

    # The demo only means something if the two figures ask different questions, and that
    # difference has to be legible from the card rather than asserted here.
    legends = [tuple(declared[figure_id].get("legend") or ()) for figure_id in ids]
    assert all(legends), "a figure with no extracted legend cannot be checked against"
    assert len(set(legends)) == len(legends), (
        "the figures carry identical legends, so nothing would notice them being merged"
    )


def test_q1_comparison_rejects_stale_question_and_accepts_shared_three_way_group():
    task = yaml.safe_load(
        Path("evaluation/tasks/tier2/smrt-q1-sparse-medium.yaml").read_text(encoding="utf-8")
    )
    base = {
        "task": "t1-smrt-fig4-passive",
        "question": task["question"],
        "llm": "test-model",
        "build": "current-build",
        "repeat": 1,
        "answer": "result",
        "model_calls": 2,
        "tool_calls": 3,
        "figures": [{"provenance": ["model_run"]}],
        "evidence": {"sections": ["paper#section"]},
        "qc_failures": 0,
        "elapsed_s": 1.2,
        "stop_rule": None,
    }
    stale = dict(base, config="full", question="old Q1 question")
    assert evals._q1_comparison_sets(
        {"tasks": {"t1-smrt-fig4-passive": task}, "runs": [stale]}
    ) == []

    metrics = {
        "successful": True,
        "figure_result_correct": True,
        "report_correct": True,
        "overall_correct": True,
        "judge_usage": {"total_tokens": 30},
        "figure_judgement": {
            "complete": True,
            "scores": {key: 2 for key, _label, _description in evals.Q1_FIGURE_AXES},
            "observations": [],
        },
        "report_judgement": {
            "complete": True,
            "scores": {key: 2 for key, _label, _description in evals.Q1_REPORT_AXES},
            "factual_errors": [],
        },
    }
    records = [
        dict(
            base,
            task="q1-sparse-medium",
            config=config_name,
            prompt_profile="p1",
            dashboard_metrics=metrics,
            llm_usage={"total_tokens": 100},
        )
        for config_name in ("full", "no-harness", "no-figures")
    ]
    scored = []
    for config_name in ("full", "no-harness", "no-figures"):
        scored.append(
            {
                "task": "q1-sparse-medium",
                "config": config_name,
                "llm": "test-model",
                "build": "current-build",
                "repeat": 1,
                "prompt_profile": "p1",
                "completed": True,
                "workflow": {"passed": True, "checks": {"plan": True}},
                "calls": {"illegal_executed": 0},
            }
        )
    data = {"tasks": {"q1-sparse-medium": task}, "runs": records, "scored": scored}
    page = evals.q1_comparison(data)
    assert "Full harness" in page
    assert "Raw PDF + raw SMRT" in page
    assert "Text-only harness" not in page
    assert "Figure radar" in page
    assert "Report radar" in page
    assert page.count("eval-q1-radar__area") == 4
    assert "eval-q1-explanation-panel" not in page
    assert "eval-q1-overall-explanation" in page
    assert "eval-q1-run-explanation" not in page
    assert "<details class='eval-q1-explanation-details'>" in page
    assert "<summary>Figure explanation</summary>" in page
    assert "<summary>Report explanation</summary>" in page
    assert "<tspan" in page
    assert "<details class='eval-details' open>" in page
    assert "<details class='eval-run-artifact' open>" in page
    assert "eval-q1-run-explanation" not in page
    order = [
        page.find("Published paper Figure 3 and reference result"),
        page.find("eval-table--q1-comparison"),
        page.find("eval-q1-radar-layout"),
        page.find("eval-q1-overall-explanation"),
        page.find("Per-run figures and reports"),
    ]
    assert order == sorted(order)
    assert len(evals.Q1_FIGURE_AXES) == 4
    assert len(evals.Q1_REPORT_AXES) == 5
    assert "composite score" in page
    assert "Curve count" in page
    assert "Pattern fidelity" in page
    assert "Grouping/order" in page
    assert "Visual correspondence" in page
    assert "Factuality" in page
    assert "Completeness" in page
    assert "Evidence" in page
    assert "Calibration" in page
    assert "Clarity" in page
    assert "Correct figure / result" not in page
    assert "Correct reports" not in page
    assert "Overall correct runs" not in page
    assert "Published paper Figure 3 and reference result" in page
    assert "Reference curves" not in page
    assert "Comparison method:" in page
    assert "Per-run figures and reports" in page
    assert "eval-run-artifact" in page
    assert "eval-run-artifact__report-body" in page
    assert "<h1>Reproduction report</h1>" in page
    assert "eval-run-artifact__table-wrap" in page
    assert "Per-run audit details" not in page
    assert "Human-editable evaluation standards" not in page
    assert "workflow stages" not in page.lower()
    assert "awaiting approval" not in page.lower()


def test_q1_aspect_diagnostic_is_evaluation_only_and_skips_missing_numeric_results(tmp_path):
    from evaluation.metrics import figure3

    record_path = next(Path("evaluation/results/competition/runs").glob("*full*qwen-plus*r1.json"))
    record = json.loads(record_path.read_text(encoding="utf-8"), strict=False)
    destination = tmp_path / "shape-diagnostic.png"
    result = figure3.write_aspect_diagnostic(record, destination)

    assert result["status"] == "written"
    assert result["x_limits"] == [0.0, 100.0]
    assert result["y_limits"] == [0.0, 0.026]
    assert destination.is_file()
    assert "figure_judgement" not in result
    assert figure3.write_aspect_diagnostic({"numeric_results": []}, tmp_path / "missing.png") == {
        "status": "skipped",
        "reason": "missing_numeric_results",
    }


def test_old_recorded_specs_receive_new_model_defaults_when_replayed():
    task_path = Path("evaluation/tasks/tier1/smrt-fig4-passive.yaml")
    task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    names = (
        "t1-smrt-fig4-passive__full__Qwen-Qwen3.5-35B-A3B__r1.json",
        "t1-smrt-fig4-passive__no-harness__Qwen-Qwen3.5-35B-A3B__r1.json",
    )
    for name in names:
        run_path = Path("evaluation/results/runs") / name
        record = json.loads(run_path.read_text(encoding="utf-8"))
        numeric = score.numeric_error(record, task)

        assert numeric["error"] == 0
        assert numeric["within"] is True
