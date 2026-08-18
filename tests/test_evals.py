import json
import re
from pathlib import Path

import yaml

from evaluation.metrics import score
from evaluation.runners import llm_robustness, model_registration, reproduction_eval
from frontend.views import evaluation as evals


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
    figure_root = Path("knowledge/literature/smrt-v1/figures")
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
    assert "Correct figure / result" in page
    assert "Published paper Figure 3 and reference result" in page
    assert "Comparison method:" in page
    assert "Per-run figures and reports" in page
    assert "eval-run-artifact" in page
    assert "Per-run audit details" not in page
    assert "Human-editable evaluation standards" not in page
    assert "workflow stages" not in page.lower()
    assert "awaiting approval" not in page.lower()


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


def test_gradio_exposes_evaluation_upload_and_agent_tabs_and_demo_prefill_handlers():
    from frontend import studio as app

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
    css = Path("frontend/static/ui.css").read_text(encoding="utf-8")
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


def test_dimension_a_reexecutes_schema_adapter_and_trace_checks():
    evidence = model_registration.evaluate()

    assert evidence["status"] == "passed"
    assert evidence["n_passed"] == evidence["n_checks"] == 20
    assert evidence["summary"]["A1_model_card_schema"] == {
        "passed": 7,
        "total": 7,
        "status": "passed",
    }
    assert evidence["A3_trace_replay"]["replay"]["matches"] is True
    assert evidence["A3_trace_replay"]["refused"]["handle"] is None


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
