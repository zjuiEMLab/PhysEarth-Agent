import json
from pathlib import Path

import yaml

from evaluation.metrics import score
from physearth import evals


def test_evaluation_snapshot_covers_every_committed_case_and_run():
    data = evals.snapshot()

    assert data["tier0"]["n_tasks"] == 9
    assert data["tier0"]["n_checks"] == 38
    assert data["tier0"]["n_passed"] == 9
    assert len(data["tasks"]) == 12
    assert len(data["scored"]) == 48
    assert {item["config"] for item in data["scored"]} == set(evals.CONFIG_ORDER)


def test_evaluation_landing_page_orders_introduction_cases_and_scores():
    dashboard = evals.dashboard()
    summary = evals.score_summary()
    details = evals.score_details()

    assert "What the agent does" in dashboard
    assert "Research with evidence" in dashboard
    assert "Configure and run physics" in dashboard
    assert "Verify every result" in dashboard
    assert "9 / 9" in summary
    assert "38 / 38" in summary
    assert "NOT EXECUTED" in summary
    assert "Four SMRT scientific questions" in summary
    assert "Remove a safeguard" not in summary
    assert "Figure reproduction" not in details
    for task_id in evals.REPRESENTATIVE_TASK_IDS:
        assert task_id in details


def test_demo_cases_are_exact_prompts_from_the_evaluation_set():
    cases = evals.demo_cases()

    assert len(cases) == 4
    assert len({case["id"] for case in cases}) == len(cases)
    assert [case["id"] for case in cases] == list(evals.REPRESENTATIVE_TASK_IDS)
    for case in cases:
        assert case["question"] == evals.snapshot()["tasks"][case["id"]]["question"]
        assert case["live_question"] == evals.snapshot()["tasks"][case["id"]]["demo"]["source_question"]
        assert case["live_question"] != case["question"]
        assert case["eyebrow"].startswith("SCIENTIFIC QUESTION DEMO")


def test_old_recorded_specs_receive_new_model_defaults_when_replayed():
    task_path = Path("evaluation/tasks/tier2/smrt-q1-sparse-medium.yaml")
    task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    names = (
        "t1-smrt-fig4-passive__full__Qwen-Qwen3.5-35B-A3B__r1.json",
        "t1-smrt-fig4-passive__no-harness__Qwen-Qwen3.5-35B-A3B__r1.json",
    )
    for name in names:
        run_path = Path("evaluation/results/runs") / name
        record = json.loads(run_path.read_text(encoding="utf-8"))
        # These cached records predate the scientific-question demo revision. They must not
        # be mistaken for a fresh fixed-figure oracle result.
        assert task["figure_target"] == "none"
        assert score.numeric_error(record, task) is None


def test_gradio_exposes_two_tabs_and_demo_prefill_handlers():
    import app

    assert app.main_tabs.get_config()["selected"] == "evaluation"
    assert len(app.evaluation_cases) == 4
    demo_handlers = [
        dependency
        for dependency in app.demo.fns.values()
        if getattr(getattr(dependency, "fn", None), "__name__", "") == "<lambda>"
    ]
    assert len(demo_handlers) >= 4
