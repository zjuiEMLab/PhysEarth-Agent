import json
from pathlib import Path

import yaml

from evaluation.metrics import score
from evaluation.runners import llm_robustness, model_registration
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
    assert "DMRT-ML" in cases[1]["question"]
    assert "MEMLS" in cases[2]["question"]


def test_basic_cases_restore_the_six_original_live_prompts():
    cases = evals.basic_cases()

    assert len(cases) == 6
    assert cases[0]["question"].startswith("Run SMRT to show how 37 GHz")
    assert "Trail Valley Creek" in cases[1]["question"]
    assert "tau_omega and water_cloud" in cases[3]["question"]
    assert "2000 kg/m3" in cases[4]["question"]


def test_architecture_image_is_embedded_from_the_presentation_export():
    page = evals.architecture()

    assert "How the agent is built" in page
    assert "data:image/png;base64," in page
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


def test_gradio_exposes_two_tabs_and_demo_prefill_handlers():
    import app

    assert app.main_tabs.get_config()["selected"] == "evaluation"
    assert any(
        "Register a physical model" in str(component.get_config().get("value", ""))
        for component in app.demo.blocks.values()
        if component.__class__.__name__ == "HTML"
    )
    assert len(app.basic_evaluation_cases) == 6
    assert len(app.evaluation_cases) == 4
    demo_handlers = [
        dependency
        for dependency in app.demo.fns.values()
        if getattr(getattr(dependency, "fn", None), "__name__", "") == "<lambda>"
    ]
    assert len(demo_handlers) >= 10


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
