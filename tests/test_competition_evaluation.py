import importlib.util
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "evaluation"

sys.path.insert(0, str(EVAL / "runners"))
sys.path.insert(0, str(EVAL))

from metrics import competition_score  # noqa: E402


def _load_runner(name):
    path = EVAL / "runners" / (name + ".py")
    spec = importlib.util.spec_from_file_location("evaluation_%s" % name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_competition_matrix_is_four_llms_three_prompts_two_repeats():
    competition = _load_runner("competition")
    cells = competition.matrix(
        type("Args", (), {"tasks": None, "profiles": None, "llm": None, "repeats": None})()
    )
    assert len(cells) == 5 * 3 * 1 * 4 * 2
    assert {cell[0]["id"] for cell in cells} == {
        "q1-sparse-medium",
        "q2-dmrt-comparison",
        "q3-memls-comparison",
        "q4-microstructure-equivalence",
        "p-smrt-density-above-ice",
    }
    assert {cell[1]["id"] for cell in cells} == {
        "p0-explore-refine-produce",
        "p1-reproduction-first",
        "p3-uncertainty-aware",
    }
    assert {cell[3] for cell in cells} == {
        "qwen/qwen3.5-122b-a10b",
        "deepseek/deepseek-v4-flash-0731",
        "openai/gpt-5.6-luna",
        "z-ai/glm-4.7-flash",
    }


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


def test_false_premise_runner_disables_research_plan_gate(monkeypatch):
    competition = _load_runner("competition")
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


def test_empty_dashboard_is_self_contained():
    dashboard = _load_runner("dashboard")
    page = dashboard.build_html([], registry={}, demo={})
    assert 'id="registration"' in page
    assert 'id="paper"' in page
    assert "SMRT" in page
    assert "OpenRouter" not in page
    assert "ModelScope" not in page
    assert "provider" not in page.lower()
    assert "smoke" not in page.lower()
    assert "usage ledger" not in page.lower()
    assert "tier 0" not in page.lower()
    assert "tier 1" not in page.lower()
    assert "tier 2" not in page.lower()
    assert "__REGISTERED__" not in page
    assert "__MODEL_ROWS__" not in page
    assert "__PAPER_ROWS__" not in page


def test_registration_demo_result_is_explicit_about_default_runs():
    payload = json.loads(
        (EVAL / "results" / "registration_demo.json").read_text(encoding="utf-8")
    )
    assert payload["schema_version"] == "registration-demo-v1"
    assert payload["execution"] == "deterministic"
    assert payload["n_models"] == 6
    assert {record["model"] for record in payload["records"]} == {
        "prosail",
        "pyet",
        "pywatershed",
        "smrt",
        "tau_omega",
        "water_cloud",
    }
    assert payload["n_passed"] == sum(record["passed"] for record in payload["records"])
    assert all("version" in record for record in payload["records"])


def test_dashboard_matrix_plan_separates_ranked_and_provider_diversity_cells():
    dashboard = _load_runner("dashboard")
    plan = dashboard.build_matrix_plan()
    assert len(plan["tasks"]) == 5
    assert len(plan["profiles"]) == 3
    assert len(plan["scenarios"]) == 15
    assert plan["main_cells"] == 120
    assert plan["diversity_cells"] == 15
    assert plan["total_cells"] == 135
    main = [model for model in plan["models"] if model["track"] == "main"]
    diversity = [
        model for model in plan["models"] if model["track"] == "provider_diversity"
    ]
    assert len(main) == 4
    assert all(model["provider"] == "openrouter" and model["ranked"] for model in main)
    assert diversity == [
        {
            "id": "Shanghai_AI_Laboratory/Intern-S2-Preview",
            "label": "Intern-S2 Preview",
            "provider": "modelscope",
            "track": "provider_diversity",
            "track_label": "ModelScope diversity",
            "repeats": 1,
            "ranked": False,
        }
    ]


def test_usage_ledger_includes_failures_and_leaves_unrun_models_na():
    dashboard = _load_runner("dashboard")
    readiness = {
        "providers": [
            {
                "provider": "openrouter",
                "models": [
                    {"id": "model-a", "available": True},
                    {"id": "model-b", "available": True},
                ],
            }
        ],
        "smoke": {
            "provider": "openrouter",
            "requested_model": "model-a",
            "llm_usage": {"total_tokens": 10, "cost_usd": 0.001},
        },
    }
    scored = [
        {
            "raw": {
                "provider": "openrouter",
                "llm": "model-a",
                "llm_usage": {"total_tokens": 20, "cost_usd": 0.002},
            }
        }
    ]
    failures = [
        {
            "provider": "openrouter",
            "llm": "model-a",
            "llm_usage": {"total_tokens": 30, "cost_usd": 0.003},
        }
    ]
    ledger = dashboard.build_usage_ledger(scored, readiness, failures)
    model_a = next(item for item in ledger if item["model"] == "model-a")
    model_b = next(item for item in ledger if item["model"] == "model-b")
    assert model_a["total_tokens"] == 60
    assert model_a["cost_usd"] == 0.006
    assert model_a["scored_cells"] == 1
    assert model_a["failed_attempts"] == 1
    assert model_a["smoke_attempts"] == 1
    assert model_b["total_tokens"] is None
    assert model_b["cost_usd"] is None


def test_llm_smoke_manifest_has_no_cross_provider_duplicates():
    smoke = _load_runner("llm_smoke")
    manifest = smoke.common.load_yaml(smoke.MANIFEST)
    specs = smoke._provider_specs(manifest)
    openrouter = set(next(x for x in specs if x["provider"] == "openrouter")["models"])
    modelscope = set(next(x for x in specs if x["provider"] == "modelscope")["models"])
    assert len(openrouter) == 4
    assert modelscope == {"Shanghai_AI_Laboratory/Intern-S2-Preview"}
    assert openrouter.isdisjoint(modelscope)


def test_registry_contract_covers_every_discovered_model():
    runner = _load_runner("registry_contract")
    from physearth.models import registry

    records = [runner.inspect_model(model) for model in registry.all_models().values()]
    assert records
    assert all(record["passed"] for record in records)
    for record in records:
        coverage = record["coverage"]
        checks = record["checks"]
        assert sum(check["check"] == "range_guard" for check in checks) == (
            2 * coverage["numeric_parameters"]
        )
        assert sum(check["check"] == "enum_guard" for check in checks) == (
            coverage["enum_parameters"]
        )
        assert sum(check["check"] == "combination_guard" for check in checks) == (
            coverage["combination_rules"]
        )
        assert sum(check["check"].startswith("sweep_") for check in checks) == (
            4 if coverage["sweep_contract"] else 0
        )


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
