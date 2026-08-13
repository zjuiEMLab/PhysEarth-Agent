import importlib.util
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVALUATION = ROOT / "evaluation"
sys.path.insert(0, str(EVALUATION / "runners"))


def _runner(name):
    path = EVALUATION / "runners" / (name + ".py")
    spec = importlib.util.spec_from_file_location("tier0_%s" % name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_tier0_task_declares_tier_kind_and_executable_checks():
    tasks = []
    for path in sorted((EVALUATION / "tasks" / "tier0").glob("*.yaml")):
        task = yaml.safe_load(path.read_text(encoding="utf-8"))
        tasks.append(task)
        assert task["tier"] == 0
        assert task["suite"] == "tier0"
        assert task["kind"]
        assert task["checks"]
        assert "quality_control" in task["kind"]
        assert task["checks"][-1] == "quality_control"
    assert len(tasks) == 9


def test_paper_tasks_are_tier2_while_historical_ids_remain_stable():
    paths = sorted((EVALUATION / "tasks" / "tier2").glob("*.yaml"))
    assert len(paths) == 4
    assert not list((EVALUATION / "tasks" / "tier1").glob("*.yaml"))
    for path in paths:
        task = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert task["tier"] == 2
        assert task["suite"] == "tier2"
        assert task["legacy_id"] == task["id"]


def test_tier0_records_are_versioned_replayable_and_have_no_llm_cost():
    payload = json.loads((EVALUATION / "results" / "tier0.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "tier0-adapter-record-v2"
    assert payload["execution"] == "deterministic"
    assert payload["n_tasks"] == payload["n_passed"] == payload["n_replayable"] == 9
    assert payload["n_checks"] == 38
    assert payload["llm_usage"] == {"calls": 0, "tokens": None, "cost_usd": None}
    for record in payload["records"]:
        assert record["tier"] == 0
        assert record["task_id"]
        assert record["model_version"]
        assert record["resolved_spec"]
        assert record["outputs"]
        assert record["check_configuration"]
        assert record["replayable"] is True
        assert record["replay_key"].startswith(
            "%s@%s:" % (record["model"], record["model_version"])
        )
        assert record["llm_usage"] == {"calls": 0, "tokens": None, "cost_usd": None}


def test_every_saved_tier0_record_can_be_replayed():
    runner = _runner("tier0")
    payload = json.loads((EVALUATION / "results" / "tier0.json").read_text(encoding="utf-8"))
    for record in payload["records"]:
        replayable, detail = runner.replay_record(record)
        assert replayable, "%s: %s" % (record["task_id"], detail)


def test_registry_result_has_exhaustive_coverage_and_zero_llm_usage():
    payload = json.loads(
        (EVALUATION / "results" / "registry_contract.json").read_text(encoding="utf-8")
    )
    assert payload["schema_version"] == "tier0-registry-contract-v2"
    assert payload["n_models"] == payload["n_passed"] == 6
    assert payload["n_checks"] >= 30
    assert payload["n_checks_passed"] == payload["n_checks"]
    assert payload["rejected_registrations"] == []
    assert payload["llm_usage"] == {"calls": 0, "tokens": None, "cost_usd": None}


def test_dashboard_explains_registration_and_holds_paper_reproduction():
    dashboard = _runner("dashboard")
    tier0 = json.loads((EVALUATION / "results" / "tier0.json").read_text(encoding="utf-8"))
    registry = json.loads(
        (EVALUATION / "results" / "registry_contract.json").read_text(encoding="utf-8")
    )
    demo = json.loads(
        (EVALUATION / "results" / "registration_demo.json").read_text(encoding="utf-8")
    )
    page = dashboard.build_html([], tier0, registry, demo=demo)
    assert 'id="registration"' in page
    assert 'id="paper"' in page
    assert "ProSAIL" in page
    assert "pywatershed" in page
    assert "SMRT" in page
    assert "OpenRouter" not in page
    assert "ModelScope" not in page
    assert "usage ledger" not in page.lower()
    assert "smoke" not in page.lower()
    assert "tier 0" not in page.lower()
    assert "tier 1" not in page.lower()
    assert "tier 2" not in page.lower()
