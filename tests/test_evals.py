import json
import re
from pathlib import Path

import yaml

from evaluation.metrics import robustness, score
from evaluation.runners import llm_robustness, model_registration
from physearth import evals


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
    assert all("Reproduce Figure" in case["question"] or "Reproduce Figures" in case["question"] for case in cases)
    assert "DMRT-ML" in cases[1]["question"]
    assert "MEMLS" in cases[2]["question"]


def test_guided_demos_are_data_driven_q1_and_q2_cards():
    cases = evals.guided_demo_cases()
    q1_card = evals.demo_card(cases[0])
    q2_card = evals.demo_card(cases[1])

    assert len(cases) == 2
    assert cases[0]["id"] == "smrt-q1-guided"
    assert cases[1]["id"] == "smrt-q2-guided"
    assert cases[0]["button_label"] == "Start guided Q1 reproduction"
    assert cases[1]["button_label"] == "Start guided Q2 reproduction"
    assert "doi.org/10.5194/gmd-11-2763-2018" in q1_card
    assert "Paper context" in q1_card
    assert "Reproduce:" in q1_card
    assert "Paper section:</b> 3.1.1" in q1_card
    assert "Figure 3" in q1_card
    assert "smrt-v1#08" not in q1_card
    assert len(cases[0]["required_runs"]) == 6
    assert cases[0]["fixed"]["radius_m"] == 0.0001
    assert "Paper section:</b> 3.1.2" in q2_card
    assert "Figures 4 and 5" in q2_card
    assert "DMRT-ML" in q2_card and "DMRT-QMS" in q2_card
    assert "smrt-v1#08" not in q2_card

    # The question copied into Live Agent must identify the paper and the source
    # figures explicitly, rather than relying on the card that the user just left.
    assert cases[0]["question"].startswith("Reproduce Figure 3: Sparse-medium scattering coefficient comparison")
    assert "SMRT:" in cases[0]["question"]
    assert "DOI: 10.5194/gmd-11-2763-2018" in cases[0]["question"]
    assert "Section 3.1.1" in cases[0]["question"]
    assert "Answer the following question:" in cases[0]["question"]
    assert "Use the six legal" not in cases[0]["question"]
    assert "registered model" not in cases[0]["question"]
    assert cases[1]["question"].startswith("Reproduce Figure 4:")
    assert "Figure 5: Radius and stickiness sensitivity" in cases[1]["question"]
    assert "Section 3.1.2" in cases[1]["question"]
    assert "Answer the following question:" in cases[1]["question"]
    assert "under identical snow and observation conditions" not in cases[1]["question"]


def test_q1_comparison_rejects_stale_question_and_accepts_shared_pair(monkeypatch):
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
    assert evals._q1_comparison_sets({"tasks": {"t1-smrt-fig4-passive": task}, "runs": [stale]}) == []

    records = [dict(base, config="full"), dict(base, config="no-harness")]
    scored = []
    for config_name in ("full", "no-harness"):
        scored.append(
            {
                "task": "t1-smrt-fig4-passive",
                "config": config_name,
                "llm": "test-model",
                "build": "current-build",
                "repeat": 1,
                "completed": True,
                "citations": {"resolved_fraction": 1.0},
                "config_match": {"fraction": 1.0},
                "illegal_call_rate": 0.0,
            }
        )
    data = {"tasks": {"t1-smrt-fig4-passive": task}, "runs": records, "scored": scored}
    monkeypatch.setattr(evals, "snapshot", lambda: data)
    page = evals.q1_comparison()
    assert "LLM + RAG + registered model tool" in page
    assert "Current PhysEarth-Agent" in page
    assert "Q1 comparison not recorded yet" not in page


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
    import app

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
    assert "How to read the counts:" in page_html
    assert "LLM robustness" not in page_html
    assert "What the evaluation shows" not in page_html
    assert "Inspect the recorded score tables" not in page_html
    assert "RUNNABLE MODELS" not in page_html
    assert "LLM + RAG + registered model tool" in page_html
    assert "Current PhysEarth-Agent" in page_html
    css = Path("assets/ui.css").read_text(encoding="utf-8")
    workflow_css = re.search(r"\.eval-workflow\s*\{(?P<body>.*?)\}", css, re.DOTALL)
    assert workflow_css and "font-size: 14px" in workflow_css.group("body")
    assert len(app.basic_evaluation_cases) == 3
    assert len(app.evaluation_cases) == 4
    assert len(app.guided_evaluation_cases) == 2
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
