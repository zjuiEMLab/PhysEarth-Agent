import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "evaluation"

sys.path.insert(0, str(EVAL / "runners"))
sys.path.insert(0, str(EVAL))

from metrics import competition_score, figure3, judge  # noqa: E402


def _load_runner(name):
    path = EVAL / "runners" / (name + ".py")
    spec = importlib.util.spec_from_file_location(f"evaluation_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_competition_matrix_is_one_main_llm_plus_a_robustness_pair():
    competition = _load_runner("competition")
    cells = competition.matrix(
        type(
            "Args",
            (),
            {"tasks": None, "profiles": None, "configs": None, "llm": None, "repeats": None},
        )()
    )
    main = [cell for cell in cells if cell[3] == "openai/gpt-5.6-luna"]
    robustness = [cell for cell in cells if cell[3] != "openai/gpt-5.6-luna"]
    assert len(main) == 2 * 1 * 2 * 1 * 3
    assert {cell[0]["id"] for cell in main} == {"q1-sparse-medium", "p-smrt-density-above-ice"}
    assert {cell[1]["id"] for cell in cells} == {"p1-reproduction-first"}
    assert {cell[2]["name"] for cell in main} == {"full", "no-harness"}
    assert sorted((cell[0]["id"], cell[2]["name"], cell[3], cell[4]) for cell in robustness) == [
        ("q1-sparse-medium", "full", "deepseek/deepseek-v4.1-flash", 1),
        ("q1-sparse-medium", "full", "qwen/qwen3.8-flash", 1),
    ]


def test_competition_matrix_can_run_a_bounded_ablation_pair():
    competition = _load_runner("competition")
    cells = competition.matrix(
        type(
            "Args",
            (),
            {
                "tasks": ["q1-sparse-medium"],
                "profiles": ["p1-reproduction-first"],
                "configs": ["full", "no-harness"],
                "llm": ["qwen-plus"],
                "repeats": 1,
            },
        )()
    )

    assert len(cells) == 2
    assert {cell[2]["name"] for cell in cells} == {"full", "no-harness"}


def test_harness_and_direct_llm_runs_use_balanced_repeat_order():
    competition = _load_runner("competition")
    cells = competition.matrix(
        type(
            "Args",
            (),
            {
                "tasks": ["q1-sparse-medium"],
                "profiles": ["p1-reproduction-first"],
                "configs": ["full", "no-harness"],
                "llm": ["qwen-plus"],
                "repeats": 3,
            },
        )()
    )
    pending = [
        ("record", task, profile, config, llm, repeat)
        for task, profile, config, llm, repeat in cells
    ]
    ordered = competition._balanced_pending_order(pending)
    assert [(item[5], item[3]["name"]) for item in ordered] == [
        (1, "full"),
        (1, "no-harness"),
        (2, "no-harness"),
        (2, "full"),
        (3, "full"),
        (3, "no-harness"),
    ]


def test_execute_without_batch_approval_stops_before_any_paid_call(capsys):
    competition = _load_runner("competition")
    result = competition.main(
        [
            "--execute",
            "--force",
            "--tasks",
            "q1-sparse-medium",
            "--profiles",
            "p1-reproduction-first",
            "--configs",
            "full",
            "no-harness",
            "--llm",
            "qwen-plus",
            "--repeats",
            "3",
        ]
    )
    output = capsys.readouterr().out
    assert result == 3
    assert "candidate sessions: 6" in output
    assert "full | qwen-plus | r1" in output
    assert "no-harness | qwen-plus | r1" in output
    assert "30 maximum" in output
    assert "No LLM or physical-model call was made" in output


def test_llm_usage_sums_billable_tokens_and_provider_cost():
    competition = _load_runner("competition")
    usage = competition._llm_usage(
        [
            {
                "kind": "model_call",
                "turn": 1,
                "index": 1,
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "cost_usd": 0.001,
            },
            {
                "kind": "model_call",
                "turn": 2,
                "index": 2,
                "prompt_tokens": 130,
                "completion_tokens": 30,
                "cost_usd": 0.002,
            },
        ]
    )
    assert usage["calls"] == 2
    assert usage["prompt_tokens"] == 230
    assert usage["completion_tokens"] == 50
    assert usage["total_tokens"] == 280
    assert usage["cost_usd"] == 0.003
    assert usage["cost_complete"] is True


def test_event_summary_keeps_bounded_upstream_error_without_secrets(monkeypatch):
    competition = _load_runner("competition")
    monkeypatch.setattr(competition.config, "llm_api_key", lambda: "candidate-secret")
    monkeypatch.setattr(competition.config, "eval_llm_api_key", lambda: "judge-secret")
    summary = competition._event_summary(
        [
            {
                "kind": "empty_response",
                "upstream": (
                    "HTTP 400 authorization: Bearer candidate-secret; "
                    "judge-secret invalid_parameter_error"
                ),
            }
        ]
    )
    assert summary[0]["upstream"].startswith("HTTP 400")
    assert "candidate-secret" not in summary[0]["upstream"]
    assert "judge-secret" not in summary[0]["upstream"]
    assert len(summary[0]["upstream"]) <= 800


def test_event_summary_keeps_what_the_trace_view_redraws_without_secrets(monkeypatch):
    competition = _load_runner("competition")
    monkeypatch.setattr(competition.config, "llm_api_key", lambda: "candidate-secret")
    monkeypatch.setattr(competition.config, "eval_llm_api_key", lambda: "judge-secret")
    (call, block) = competition._event_summary(
        [
            {
                "kind": "tool_call",
                "name": "run_model",
                "summary": "ran smrt; token candidate-secret",
                "arguments": {"model": "smrt", "note": "judge-secret"},
            },
            {"kind": "harness_block", "tool": "run_model", "problems": ["density too high"]},
        ]
    )
    assert call["arguments"]["model"] == "smrt"
    assert "secret" not in json.dumps(call)
    assert call["summary"].startswith("ran smrt")
    assert block["problems"] == ["density too high"]


def _perfect_figure3_record(tmp_path):
    gold = figure3.reference()
    axis = [float(value) for value in gold["recipe"]["densities_kg_m3"]]
    oracle = {
        "smrt_version": "test",
        "axis": {"name": "density_kg_m3", "values": axis},
        "series": {},
    }
    numeric = []
    figure_series = []
    for index, curve in enumerate(gold["curves"], 1):
        values = [index * value / 100000.0 for value in axis]
        oracle["series"][curve["id"]] = values
        spec = {
            "electromagnetic_model": curve["electromagnetic_model"],
            "microstructure_model": curve["microstructure_model"],
            "frequency_ghz": gold["recipe"]["frequency_ghz"],
            "radius_m": gold["recipe"]["radius_m"],
        }
        if curve.get("stickiness") is not None:
            spec["stickiness"] = curve["stickiness"]
        handle = f"res_{index}"
        numeric.append(
            {
                "handle": handle,
                "model": "smrt",
                "version": "test",
                "spec": spec,
                "axis": {"name": "density_kg_m3", "values": axis},
                "series": {"ks_per_m": list(values)},
                "units": {"ks_per_m": "m-1"},
            }
        )
        figure_series.append(
            {
                "handle": handle,
                "label": curve["label"],
                "x": "density_kg_m3",
                "y": "ks_per_m",
            }
        )
    image = tmp_path / "figure.png"
    image.write_bytes(b"x" * 3000)
    record = {
        "numeric_results": numeric,
        "figures": [
            {
                "title": "Sparse-medium scattering comparison",
                "subtitle": "Sphere radius: 100 micrometres",
                "x_label": "Density (kg m-3)",
                "y_label": "Scattering coefficient (m-1)",
                "series": figure_series,
                "archived_image_path": str(image),
                "quality_review": {"reviewed": True, "passed": True},
            }
        ],
    }
    return record, oracle


def test_figure3_fixture_pins_the_official_notebook_recipe():
    gold = figure3.reference()
    assert gold["source"]["commit"] == "fb60a037a290c0add016d45f354cea37816b1515"
    assert gold["source"]["notebook"] == "fig03_sparse_medium.ipynb"
    assert gold["recipe"]["source_sensor"] == "AMSR-E 37V"
    assert gold["recipe"]["frequency_ghz"] == 36.5
    assert gold["recipe"]["densities_kg_m3"] == list(range(1, 100, 5))
    assert gold["scoring_policy"] == {
        "notebook_recipe": "diagnostic_only",
        "numeric_reference": "not_scoreable",
        "caption": "advisory",
    }
    assert [item["label"] for item in gold["curves"]] == [
        "Independent spheres (Rayleigh)",
        "Independent spheres (IBA)",
        "Non-sticky hard spheres (DMRT QCA-CP)",
        "Non-sticky hard spheres (IBA)",
        "Sticky hard spheres (DMRT QCA-CP)",
        "Sticky hard spheres (IBA)",
    ]


def test_human_editable_standards_are_loaded_by_figure_and_report_evaluators():
    assert figure3.evaluation_standard()["figure"]["notebook_recipe"] == "diagnostic_only"
    assert figure3.evaluation_standard()["figure"]["numeric_reference"] == "not_scoreable"
    assert (
        judge.standard_figure()["figure"]["visual_judge"]["pass"]["required_scores"][
            "patterns"
        ]
        == 1
    )
    assert judge.pass_rule(judge.standard()) == (8, {"factuality": 1}, True)
    assert judge.dimensions(judge.standard()) == (
        "source_fidelity", "answer", "factuality", "technical_completeness",
        "assumed_parameters", "evidence", "calibration", "clarity",
    )
    v1 = judge.standard(EVAL / "standards" / "report_judge_v1.yaml")
    assert judge.pass_rule(v1) == (8, {"factuality": 2}, True)
    assert len(judge.dimensions(v1)) == 5


def test_competition_archives_named_figures_and_editable_reports(monkeypatch, tmp_path):
    competition = _load_runner("competition")
    monkeypatch.setattr(competition.common, "REPO", tmp_path)
    monkeypatch.setattr(competition, "FIGURES", tmp_path / "figures")
    monkeypatch.setattr(competition, "REPORTS", tmp_path / "reports")
    source = tmp_path / "generated.png"
    source.write_bytes(b"png-bytes")

    full = {
        "task": "q1-sparse-medium",
        "prompt_profile": "p1-reproduction-first",
        "llm": "qwen-plus",
        "repeat": 1,
        "config": "full",
        "answer": "Full report",
        "figures": [{"image_path": str(source)}],
    }
    competition.archive_record_artifacts(full)
    assert full["figures"][0]["archived_image_path"].endswith("_full.png")
    assert full["archived_report_path"].endswith("_full.md")
    assert (tmp_path / full["figures"][0]["archived_image_path"]).is_file()
    report = tmp_path / full["archived_report_path"]
    assert report.read_text(encoding="utf-8").endswith("Full report\n")
    assert full["report_artifact"]["editable"] is True
    original_image_path = full["figures"][0]["archived_image_path"]
    full["figures"][0].pop("image_path")
    competition.archive_record_artifacts(full)
    assert full["figures"][0]["archived_image_path"] == original_image_path

    baseline = dict(full, config="no-harness", figures=[{"image_path": str(source)}])
    competition.archive_record_artifacts(baseline)
    assert baseline["figures"][0]["archived_image_path"].endswith("_baseline.png")
    assert baseline["archived_report_path"].endswith("_baseline.md")


def test_figure3_score_separates_structural_checks_from_diagnostic_recipe(tmp_path):
    record, oracle = _perfect_figure3_record(tmp_path)
    scored = figure3.score(record, oracle)
    assert scored["passed"] is None
    assert scored["status"] == "not_scoreable"
    assert scored["structural_passed"] is True
    assert scored["recipe"]["status"] == "diagnostic_only"
    assert scored["numeric"]["status"] == "not_scoreable"
    assert scored["plot"]["passed"] is True

    record["numeric_results"][0]["series"]["ks_per_m"][-1] *= 2
    wrong = figure3.score(record, oracle)
    assert wrong["status"] == "not_scoreable"
    assert wrong["numeric"]["curves"][0]["within"] is False

    record["numeric_results"] = record["numeric_results"][:-1]
    missing = figure3.score(record, oracle)
    assert missing["passed"] is False
    assert missing["status"] == "fail"
    assert missing["structural_passed"] is False
    assert missing["numeric"]["curves"][-1]["within"] is None

    record, oracle = _perfect_figure3_record(tmp_path)
    record["numeric_results"][0]["spec"]["frequency_ghz"] = 19.0
    wrong_configuration = figure3.score(record, oracle)
    assert wrong_configuration["status"] == "not_scoreable"
    assert wrong_configuration["recipe"]["curves"][0]["experiment_exact"] is False

    record, oracle = _perfect_figure3_record(tmp_path)
    record["figures"][0]["subtitle"] = ""
    missing_caption = figure3.score(record, oracle)
    assert missing_caption["plot"]["checks"]["caption"] is False
    assert missing_caption["plot"]["passed"] is True


def test_figure3_numeric_thresholds_apply_to_every_curve(tmp_path):
    record, oracle = _perfect_figure3_record(tmp_path)
    wanted = oracle["series"]["independent_rayleigh"]
    span = max(wanted) - min(wanted)
    record["numeric_results"][0]["series"]["ks_per_m"] = [
        value + 0.019 * span for value in wanted
    ]
    inside = figure3.score(record, oracle)
    assert inside["numeric"]["curves"][0]["within"] is True

    record["numeric_results"][0]["series"]["ks_per_m"] = [
        value + 0.051 * span for value in wanted
    ]
    outside = figure3.score(record, oracle)
    assert outside["numeric"]["curves"][0]["within"] is False


def test_report_checks_reject_unresolved_evidence_and_unsupported_success_claim():
    base = {
        "answer": (
            "Picard Figure 3 was exactly reproduced with SMRT version 1.5.1 "
            "[smrt-v1#08] [model:smrt@1.5.1]."
        ),
        "switches": {"paper_access": "structured_figures"},
        "markers": {
            "literature": ["smrt-v1#08"],
            "model": ["smrt@1.5.1"],
            "data": [],
        },
        "citation_check": {"passed": True, "unresolved": []},
        "numeric_results": [{"handle": "result"}],
        "reproduction_outcome": "reproduced",
    }
    unsupported = figure3.deterministic_report_checks(base, {"passed": False})
    assert unsupported["passed"] is False
    assert unsupported["checks"]["calibrated_outcome"] is False

    unresolved_record = {
        **base,
        "answer": "The partial result uses SMRT version 1.5.1.",
        "citation_check": {"passed": False, "unresolved": ["smrt-v1#99"]},
        "reproduction_outcome": "partial",
    }
    unresolved = figure3.deterministic_report_checks(unresolved_record, {"passed": False})
    assert unresolved["passed"] is False
    assert unresolved["checks"]["evidence_resolved"] is False


def test_visual_figure_review_can_validate_success_when_metadata_check_differs():
    base = {
        "answer": (
            "The figure is qualitatively reproduced after visual review; the unspecified "
            "execution parameters are listed as assumptions. SMRT version 1.5.1."
        ),
        "switches": {"paper_access": "structured_figures"},
        "markers": {
            "literature": ["smrt-v1#08"],
            "model": ["smrt@1.5.1"],
            "data": [],
        },
        "citation_check": {"passed": True, "unresolved": []},
        "numeric_results": [{"handle": "result"}],
        "reproduction_outcome": "reproduced",
        "evidence": {"sections": ["smrt-v1#08"]},
    }
    checked = figure3.deterministic_report_checks(
        base,
        {"passed": False, "status": "not_scoreable", "plot": {"passed": False}},
        {"status": "pass", "passed": True},
    )
    assert checked["checks"]["calibrated_outcome"] is True
    assert checked["visual_validation"] == "pass"
    assert checked["plot_checks_are_diagnostic"] is True


def test_judge_uses_only_eval_settings_and_counts_retry_usage(monkeypatch):
    monkeypatch.setattr(judge.config, "eval_llm_api_key", lambda: "judge-secret")
    monkeypatch.setattr(judge.config, "eval_llm_api_base", lambda: "https://judge.invalid/v1")
    monkeypatch.setattr(judge.config, "eval_llm_model", lambda: "judge-model")
    assert judge.settings(("candidate-model",))["model"] == "judge-model"
    with pytest.raises(RuntimeError, match="must differ"):
        judge.settings(("judge-model",))
    with pytest.raises(RuntimeError, match="must differ"):
        judge.settings(("provider/judge-model",))
    assert judge.REPORT_RESPONSE_FORMAT["type"] == "json_schema"
    assert judge.REPORT_RESPONSE_FORMAT["json_schema"]["strict"] is True

    names = judge.dimensions(judge.standard())
    assert set(judge.REPORT_RESPONSE_FORMAT["json_schema"]["schema"]["properties"]["scores"][
        "required"
    ]) == set(names)
    valid = {
        "scores": {name: 2 if name == "factuality" else 1 for name in names},
        "factual_errors": [],
        "summary": "accurate",
    }
    valid["scores"].update(answer=2, evidence=2, calibration=2)
    calls = []

    def fake_request(messages, candidate_models=(), max_tokens=1200, response_format=None):
        calls.append(messages)
        if len(calls) == 1:
            raise judge.JudgeResponseError(
                "truncated JSON",
                {
                    "model": "judge-model",
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 2,
                        "total_tokens": 12,
                    },
                },
            )
        return valid, {
            "model": "judge-model",
            "usage": {"prompt_tokens": 20, "completion_tokens": 4, "total_tokens": 24},
        }

    monkeypatch.setattr(judge, "_request", fake_request)
    judged = judge.judge_report(
        {"answer": "A calibrated report.", "config": "secret-scenario-label"},
        {"question": "question"},
        {"passed": True, "recipe": {}, "numeric": {}, "plot": {}},
        {"passed": True},
        candidate_models=("candidate-model",),
    )
    assert judged["passed"] is True
    assert (judged["total"], judged["maximum"]) == (12, 16)
    assert judged["usage"]["total_tokens"] == 36
    assert "secret-scenario-label" not in json.dumps(calls)
    assert "Previous output was invalid" in calls[1][0]["content"]
    assert "judge-secret" not in json.dumps(judged)
    assert "judge-secret" not in judge._safe_error(
        RuntimeError("request included judge-secret"), "judge-secret"
    )


def test_report_judge_pass_rule_comes_from_the_standard(monkeypatch):
    monkeypatch.setattr(judge.config, "eval_llm_api_key", lambda: "judge-secret")
    monkeypatch.setattr(judge.config, "eval_llm_api_base", lambda: "https://judge.invalid/v1")
    monkeypatch.setattr(judge.config, "eval_llm_model", lambda: "judge-model")
    scores = {"factuality": 0}
    seen = {}

    def fake_request(messages, candidate_models=(), max_tokens=1200, response_format=None):
        names = response_format["json_schema"]["schema"]["properties"]["scores"]["required"]
        seen["names"] = names
        return {
            "scores": {name: scores.get(name, 2) for name in names},
            "factual_errors": ["one"],
            "summary": "s",
        }, {"model": "judge-model", "usage": {}}

    monkeypatch.setattr(judge, "_request", fake_request)
    args = (
        {"answer": "report"},
        {"question": "q"},
        {"passed": True, "recipe": {}, "numeric": {}, "plot": {}},
        {"passed": True},
    )
    current = judge.judge_report(*args, candidate_models=("c",))
    assert len(seen["names"]) == 8 and current["total"] == 14
    assert current["passed"] is False
    older = judge.judge_report(
        *args, candidate_models=("c",),
        standard_path=EVAL / "standards" / "report_judge_v1.yaml",
    )
    assert len(seen["names"]) == 5 and older["maximum"] == 10 and older["passed"] is False


def test_figure_judge_compares_images_without_text_or_numeric_matching(monkeypatch, tmp_path):
    monkeypatch.setattr(judge.config, "eval_llm_api_key", lambda: "judge-secret")
    monkeypatch.setattr(judge.config, "eval_llm_api_base", lambda: "https://judge.invalid/v1")
    monkeypatch.setattr(judge.config, "eval_llm_model", lambda: "judge-model")
    reference_image = tmp_path / "reference.png"
    candidate_image = tmp_path / "candidate.png"
    reference_image.write_bytes(b"reference")
    candidate_image.write_bytes(b"candidate")
    monkeypatch.setattr(
        figure3,
        "reference",
        lambda: {
            "visual_reference": {
                "image_path": "reference.png",
                "expected_line_count": 6,
            }
        },
    )
    monkeypatch.setattr(judge, "REPO", tmp_path)
    calls = []

    def fake_request(messages, candidate_models=(), max_tokens=1200, response_format=None):
        calls.append((messages, response_format))
        return (
            {
                "scores": {
                    "line_count": 2,
                    "patterns": 2,
                    "grouping": 2,
                    "visual_correspondence": 2,
                },
                "observations": ["Six qualitative curve families are visible."],
                "summary": "The candidate conveys the same qualitative figure.",
            },
            {
                "model": "judge-model",
                "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
            },
        )

    monkeypatch.setattr(judge, "_request", fake_request)
    result = judge.judge_figure(
        {"figures": [{"archived_image_path": str(candidate_image)}]},
        candidate_models=("candidate-model",),
    )
    assert result["complete"] is True
    assert result["passed"] is True
    assert result["total"] == 8
    assert result["usage"]["total_tokens"] == 14
    assert calls[0][1] == judge.FIGURE_RESPONSE_FORMAT
    content = calls[0][0][1]["content"]
    assert content[1]["type"] == "image_url"
    assert content[2]["type"] == "image_url"
    assert "Do not score exact title/caption wording" in calls[0][0][0]["content"]
    assert "RMSE" in calls[0][0][0]["content"]


def test_provenance_schema_and_gold_use_only_declared_source_kinds():
    schema = json.loads((EVAL / "provenance" / "schema.json").read_text(encoding="utf-8"))
    allowed = set(schema["items"]["properties"]["source_kind"]["enum"])
    gold = yaml.safe_load((EVAL / "provenance" / "gold_fields.yaml").read_text(encoding="utf-8"))
    for task in gold["tasks"].values():
        for rule in task["fields"].values():
            assert set(rule["accepted_kinds"]) <= allowed


def test_provenance_score_penalises_paper_label_on_user_only_value():
    task = {"id": "t1-smrt-fig4-passive"}
    record = {
        "parameter_provenance": [
            {
                "field": "sweep_start",
                "value": 0.0,
                "source_kind": "paper",
                "source_ref": "smrt-v1#08",
            }
        ],
        "provenance_parse_error": None,
    }
    scored = competition_score.provenance_score(record, task)
    detail = next(item for item in scored["details"] if item["field"] == "sweep_start")
    assert detail["value_ok"] is True
    assert detail["kind_ok"] is False
    assert detail["source_ref_ok"] is False
    assert "sweep_start" in scored["unsupported_attributions"]


def test_workflow_score_requires_planned_execution_and_reviewed_figure():
    record = {
        "workflow": {
            "research_required": True,
            "review_actions": [{"before": "plan_review", "after": "plan_approved"}],
            "final_phase": "completed",
        },
        "research": {"plan": {"runs": [{"id": "r"}], "charts": [{"id": "c"}]}},
        "tool_log": [{"name": "run_planned_model", "status": "success"}],
        "figures": [
            {
                "planned_chart_id": "c",
                "quality_review": {"reviewed": True, "passed": True},
            }
        ],
    }
    scored = competition_score.workflow_score(record)
    assert scored["passed"] is True
    assert scored["fraction"] == 1.0


def test_planned_run_legality_is_scored_from_frozen_spec_not_run_id():
    entry = {
        "name": "run_planned_model",
        "arguments": {"run_id": "approved_1"},
        "status": "success",
        "model": "smrt",
        "spec": {
            "electromagnetic_model": "dmrt_qcacp_shortrange",
            "microstructure_model": "sticky_hard_spheres",
            "output": "tb",
            "frequency_ghz": 37.0,
            "angle_deg": 55.0,
            "thickness_m": 10.0,
            "density_kg_m3": 300.0,
            "temperature_k": 256.0,
            "radius_m": 0.0001,
            "stickiness": 0.5,
            "dort_streams": 32,
            "sweep_parameter": "angle_deg",
            "sweep_start": 0.0,
            "sweep_stop": 60.0,
            "sweep_points": 13,
        },
    }
    assert competition_score.score.call_problems(entry) == []


def test_false_premise_can_end_safely_without_a_completed_plan():
    record = {
        "workflow": {"research_required": False, "review_actions": [], "final_phase": None},
        "research": None,
        "answer": "The requested density exceeds the 917 kg/m3 physical limit.",
        "tool_log": [],
    }
    task = {
        "quality": "false_premise",
        "false_premise": {"answer_should_mention": ["density", "917"]},
    }
    workflow = competition_score.workflow_score(record, task)
    assert workflow["passed"] is True
    assert workflow["checks"]["planning_skipped_for_impossible_premise"] is True


def test_false_premise_runner_disables_research_plan_gate(monkeypatch, tmp_path):
    competition = _load_runner("competition")
    # The runner archives each report; keep this fake one out of the committed results.
    monkeypatch.setattr(competition.common, "REPO", tmp_path)
    monkeypatch.setattr(competition, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(competition, "FIGURES", tmp_path / "figures")
    captured = {}

    def fake_run(prompt, model, session, switches):
        captured["research_required"] = session["research_required"]
        return (
            "density exceeds 917 kg/m3\n"
            "<parameter_provenance>[]</parameter_provenance>\n"
            "<reproduction_outcome>failed</reproduction_outcome>",
            [],
            {},
        )

    monkeypatch.setattr(competition.agent, "run", fake_run)
    monkeypatch.setattr(competition.approval, "set_mode", lambda *args: None)
    record = competition.run_one(
        {
            "id": "false-premise",
            "suite": "probe",
            "quality": "false_premise",
            "question": "invalid density",
        },
        {
            "id": "p3",
            "version": "1",
            "title": "uncertainty",
            "instructions": "reject invalid premises",
            "_path": "prompt.yaml",
        },
        {"name": "full", "switches": {}},
        "model",
        1,
        "build",
    )
    assert captured["research_required"] is False
    assert record["workflow"]["approval_policy"] == "not_applicable_safe_refusal"
    assert record["workflow"]["review_actions"] == []


def test_full_reproduction_is_ineligible_when_provenance_is_missing():
    task = {
        "id": "t1-smrt-fig4-passive",
        "quality": "complete",
        "reference": {"model": "smrt"},
    }
    gates = competition_score.reproduction_hard_gates(
        legacy={
            "calls": {"illegal_executed": 0},
            "config_match": {"fraction": 1.0},
            "citations": {"unresolved": 0},
        },
        workflow={"passed": True},
        provenance={"attribution_accuracy": 0.0},
        independent={"within": True},
        task=task,
    )
    assert gates["provenance_failure"] is True
    assert sum(gates.values()) == 1


def _planned_record(runs, mapping=(), conditions=None, repairs=()):
    return {
        "research": {
            "plan": {
                "runs": runs,
                "parameter_mapping": list(mapping),
                "condition_provenance": conditions or {},
                "automatic_repairs": list(repairs),
            }
        },
        "parameter_provenance": [],
    }


def _sticky_run(defaulted, **parameters):
    spec = {
        "electromagnetic_model": "iba",
        "microstructure_model": "sticky_hard_spheres",
        "output": "coefficients",
        "frequency_ghz": 37.0,
        "angle_deg": 55.0,
        "radius_m": 0.0001,
        "stickiness": 0.2,
        "density_kg_m3": 300.0,
        **parameters,
    }
    return {"id": "run_1", "model": "smrt", "resolved_parameters": spec,
            "defaulted_parameters": defaulted}


def test_a_default_labelled_as_paper_evidence_is_mislabelled():
    from metrics import provenance_check

    record = _planned_record(
        [_sticky_run(["frequency_ghz", "angle_deg"])],
        mapping=[
            {"model": "smrt", "model_input": "stickiness", "provenance_class": "backend_default"},
            {"model": "smrt", "model_input": "radius_m", "provenance_class": "paper_explicit"},
        ],
        conditions={
            "frequency_ghz": "paper_inferred",
            "electromagnetic_model": "smrt-v1#fig03",
            "microstructure_model": "smrt-v1#fig03",
            "output": "smrt-v1#fig03",
            "density_kg_m3": "smrt-v1#fig03",
        },
    )
    result = provenance_check.check(record)
    assert [item["parameter"] for item in result["mislabelled"]] == ["frequency_ghz"]
    assert result["unlabelled"] == []
    assert "angle_deg" in result["inert"]
    assert result["passed"] is False


def test_a_label_the_planner_filled_in_is_not_credited_to_the_agent():
    from metrics import provenance_check

    record = _planned_record(
        [_sticky_run([])],
        mapping=[
            {"model": "smrt", "model_input": "stickiness", "provenance_class": "backend_default"},
        ],
        repairs=[{"field": "parameter_mapping.smrt.stickiness", "from": "", "to": "stickiness"}],
    )
    result = provenance_check.check(record)
    assert {"parameter": "stickiness", "card_default": False, "run": "run_1"} in result[
        "unlabelled"
    ]


def test_outcome_tag_is_computed_from_the_record():
    figure = {"complete": True, "passed": True, "summary": "same figure"}
    report = {"complete": True, "passed": False, "summary": "never answers the question"}
    ran = {
        "numeric_results": [{"handle": "h"}],
        "figures": [{"preview": False}],
        "event_log": [
            {"kind": "harness_stop", "turn": 1, "rule": "research_approval_required"},
            {"kind": "harness_pass", "turn": 2},
        ],
        "dashboard_metrics": {"figure_judgement": figure, "report_judgement": report},
    }
    task = {"quality": "complete"}
    partial = competition_score.outcome_tag(ran, task, {"passed": True})
    assert partial["tag"] == "Partial"
    assert partial["reasons"] == ["report judge fail: never answers the question"]

    report["passed"] = True
    assert competition_score.outcome_tag(ran, task, {"passed": True})["tag"] == "Success"

    stopped = dict(ran, event_log=[{"kind": "harness_stop", "turn": 1, "rule": "no_progress",
                                    "reason": "Stopped after 3 failed calls"}])
    failed = competition_score.outcome_tag(stopped, task, None)
    assert failed["tag"] == "Failed"
    assert failed["reasons"] == ["stopped by no_progress: Stopped after 3 failed calls"]

    nothing = {"numeric_results": [], "figures": [], "event_log": []}
    assert competition_score.outcome_tag(nothing, task, None)["reasons"] == [
        "no successful physical model run",
        "no figure",
    ]
    assert competition_score.outcome_tag(nothing, {"quality": "false_premise"}, None) is None


def test_b3_separates_the_agent_s_settings_from_the_model():
    oracle = json.loads(
        (EVAL / "results" / "competition" / "q1_figure3_oracle.json").read_text(encoding="utf-8")
    )
    records = json.loads(
        (EVAL / "results" / "competition" / "scored_runs.json").read_text(encoding="utf-8")
    )
    record = next(item["raw"] for item in records if item["raw"].get("numeric_results"))
    curves = {row["curve"]: row for row in figure3.numeric_error(record, oracle)["curves"]}
    assert len(curves) == 6 and all(row["present"] for row in curves.values())
    sticky = curves["sticky_iba"]
    assert sticky["as_chosen"]["normalized_rmse"] > 0.1
    assert sticky["as_chosen"]["points_compared"] == 20
    for row in curves.values():
        assert row["notebook_settings"]["normalized_rmse"] < 0.01


def test_report_checks_read_the_task_s_own_reference_terms():
    record = {
        "answer": "pyet release 1.5.0 reproduces the documented example [pyet-docs#ex1].",
        "switches": {"paper_access": "raw_pdf"},
        "evidence": {"raw_pdf_pages": ["p1"]},
        "markers": {"literature": [], "model": [], "data": []},
        "citation_check": {"passed": True, "unresolved": []},
        "numeric_results": [{"handle": "result"}],
        "reproduction_outcome": "partial",
    }
    fixture = {"report_terms": {"source": ["pyet-docs"], "version": ["release 1.5.0"]}}
    own = figure3.deterministic_report_checks(record, {"passed": None}, fixture=fixture)
    assert own["checks"]["evidence_resolved"] is True
    assert own["checks"]["model_version_qualified"] is True

    q1 = figure3.deterministic_report_checks(record, {"passed": None})
    assert q1["checks"]["evidence_resolved"] is False
    assert q1["checks"]["model_version_qualified"] is False


def test_the_model_grid_runs_one_reproduction_task_per_registered_model():
    competition = _load_runner("competition")
    cells = competition.matrix(
        type(
            "Args",
            (),
            {"tasks": None, "profiles": None, "configs": None, "llm": None, "repeats": None,
             "grid": True},
        )()
    )
    models = sorted(model for cell in cells for model in cell[0]["models"])
    assert models == ["prosail", "pyet", "pywatershed", "smrt", "tau_omega", "water_cloud"]
    assert {cell[2]["name"] for cell in cells} == {"full"}
    for task, *_ in cells:
        assert (ROOT / task["reference_fixture"]).is_file()
        assert task["capability"]["reference_models"]


def _record_from_oracle(fixture, oracle, scale=1.0):
    results = []
    for curve in fixture["curves"]:
        results.append(
            {
                "model": curve["model"],
                "spec": dict(curve.get("match") or {}),
                "axis": oracle["axis"],
                "series": {curve["output"]: [v * scale for v in oracle["series"][curve["id"]]]},
            }
        )
    return {"numeric_results": results, "figures": [{"title": "candidate"}]}


@pytest.mark.parametrize(
    "fixture_name",
    [
        "prosail_lai_reference.yaml",
        "pyet_fao56_example18_reference.yaml",
        "pywatershed_sagehen_wy1981_reference.yaml",
    ],
)
def test_reference_series_scores_a_run_against_the_committed_oracle(fixture_name):
    from metrics import reference_series

    fixture = reference_series.load_fixture(EVAL / "fixtures" / fixture_name)
    oracle = reference_series.load_oracle(fixture)
    assert oracle and oracle["adapter_independent"] and not oracle["paper_digitization"]
    assert (ROOT / fixture["visual_reference"]["image_path"]).is_file()

    exact = reference_series.score(_record_from_oracle(fixture, oracle), fixture, oracle)
    assert exact["status"] == "pass"
    assert all(row["normalized_rmse"] < 1e-12 for row in exact["numeric_b3"]["curves"])

    off = reference_series.score(_record_from_oracle(fixture, oracle, 1.2), fixture, oracle)
    assert off["status"] == "fail"

    missing = reference_series.score({"numeric_results": [], "figures": []}, fixture, oracle)
    assert missing["status"] == "not_scoreable"


def test_reference_series_compares_the_published_value_without_typing_the_agent_answer():
    from metrics import reference_series

    fixture = reference_series.load_fixture(
        EVAL / "fixtures" / "pyet_fao56_example18_reference.yaml"
    )
    oracle = reference_series.load_oracle(fixture)
    scored = reference_series.score(_record_from_oracle(fixture, oracle), fixture, oracle)
    (published,) = scored["numeric_b3"]["published"]
    assert published["published_value"] == 3.9
    assert abs(published["agent_minus_published"]) < 0.05
    assert published["agent_value"] == published["oracle_value"]


def test_capability_gate_counts_missing_forcing_as_a_correct_refusal():
    gate = _load_runner("capability_gate")
    tasks = {task["id"]: task for task in gate.common.load_tasks("tier2")}
    refused = gate.verdict(tasks["water-cloud-modanesi2021-fig11"])
    assert refused["verdict"] == "cannot"
    assert any(reason.startswith("forcing Noah-MP") for reason in refused["reasons"])
    assert not any("not registered" in reason for reason in refused["reasons"])
    assert gate.verdict(tasks["tau-omega-lv2020-fig9"])["verdict"] == "can"


def test_a_point_run_beside_a_sweep_is_not_compared_and_does_not_crash():
    from metrics import reference_series

    gold = figure3.reference()
    axis = [float(value) for value in gold["recipe"]["densities_kg_m3"]]
    oracle = {"smrt_version": "test", "axis": {"name": "density_kg_m3", "values": axis},
              "series": {curve["id"]: [0.01] * len(axis) for curve in gold["curves"]}}
    point_run = {
        "model": "smrt",
        "spec": {"electromagnetic_model": "rayleigh", "microstructure_model": "independent_sphere"},
        "axis": None,
        "series": {"ks_per_m": [0.01]},
    }
    rows = figure3.numeric_error({"numeric_results": [point_run]}, oracle)["curves"]
    assert rows[0]["present"] and rows[0]["as_chosen"]["points_compared"] == 0

    fixture = reference_series.load_fixture(EVAL / "fixtures" / "prosail_lai_reference.yaml")
    prosail_oracle = reference_series.load_oracle(fixture)
    point = {"model": "prosail", "spec": {}, "axis": None,
             "series": {name: [0.1] for name in prosail_oracle["series"]}}
    scored = reference_series.score({"numeric_results": [point], "figures": []}, fixture,
                                    prosail_oracle)
    assert scored["status"] == "not_scoreable"
