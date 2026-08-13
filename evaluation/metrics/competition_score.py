"""Competition metrics layered on the legacy task scorer."""

from pathlib import Path

import yaml

from . import oracles, score

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "provenance" / "gold_fields.yaml"
_ORACLE_CACHE = {}


def _gold():
    return yaml.safe_load(GOLD.read_text(encoding="utf-8"))["tasks"]


def _same_or_range(value, rule):
    if "value" in rule:
        return score._same(value, rule["value"])
    if "value_range" in rule:
        low, high = rule["value_range"]
        return isinstance(value, (int, float)) and low <= value <= high
    return True


def provenance_score(record, task):
    # Scientific-question demos deliberately do not use the old fixed-figure provenance
    # gold. Applying Figure 4/5/6 field gold here would silently turn a demo back into a
    # figure-reproduction task.
    if task.get("evaluation_kind") == "scientific_question_demo":
        return None
    block = _gold().get(task["id"])
    if not block:
        return None
    declared = {
        str(item.get("field")): item
        for item in record.get("parameter_provenance") or []
        if isinstance(item, dict) and item.get("field")
    }
    details = []
    for field, rule in block["fields"].items():
        item = declared.get(field)
        present = item is not None
        kind_ok = present and item.get("source_kind") in rule["accepted_kinds"]
        value_ok = present and _same_or_range(item.get("value"), rule)
        source_present = present and bool(str(item.get("source_ref") or "").strip())
        declared_ref = str((item or {}).get("source_ref") or "").strip().lower()
        expected_refs = rule.get("source_refs") or [rule.get("source_ref")]
        source_ref_ok = False
        for expected in expected_refs:
            expected_ref = str(expected or "").strip().lower()
            if expected_ref == "question":
                source_ref_ok = source_ref_ok or (
                    "question" in declared_ref or "user" in declared_ref
                )
            elif expected_ref.startswith("smrt-v1#"):
                source_ref_ok = source_ref_ok or declared_ref == expected_ref
            else:
                source_ref_ok = source_ref_ok or source_present
        span_required = present and item.get("source_kind") == "paper"
        source_span_ok = not span_required or bool(
            str((item or {}).get("source_span") or "").strip()
        )
        details.append(
            {
                "field": field,
                "present": present,
                "kind_ok": bool(kind_ok),
                "value_ok": bool(value_ok),
                "source_present": bool(source_present),
                "source_ref_ok": bool(source_ref_ok),
                "source_span_ok": bool(source_span_ok),
                "expected_kinds": rule["accepted_kinds"],
                "declared_kind": item.get("source_kind") if item else None,
            }
        )
    total = len(details)
    attribution_hits = sum(
        1
        for item in details
        if item["present"]
        and item["kind_ok"]
        and item["source_ref_ok"]
        and item["source_span_ok"]
    )
    value_hits = sum(1 for item in details if item["present"] and item["value_ok"])
    unsupported = [item["field"] for item in details if item["present"] and not item["kind_ok"]]
    return {
        "parse_error": record.get("provenance_parse_error"),
        "fields_expected": total,
        "fields_declared": len(declared),
        "completeness": sum(1 for item in details if item["present"]) / total,
        "attribution_accuracy": attribution_hits / total,
        "value_accuracy": value_hits / total,
        "unsupported_attributions": unsupported,
        "details": details,
    }


def workflow_score(record, task=None):
    if task and task.get("quality") == "false_premise":
        calls = score.classify_calls(record)
        premise = score.false_premise_handled(record, task) or {}
        checks = {
            "planning_skipped_for_impossible_premise": not bool(
                (record.get("workflow") or {}).get("research_required")
            ),
            "request_not_executed_illegally": calls["illegal_executed"] == 0,
            "safe_terminal_answer": bool(premise.get("answer_names_the_limit")),
        }
        return {
            "fraction": sum(checks.values()) / len(checks),
            "checks": checks,
            "passed": all(checks.values()),
            "terminal_kind": "safe_refusal_or_constrained_alternative",
        }
    research = record.get("research") or {}
    plan = research.get("plan") or {}
    calls = record.get("tool_log") or []
    figures = record.get("figures") or []
    checks = {
        "research_gate_enabled": bool((record.get("workflow") or {}).get("research_required")),
        "plan_proposed": bool(plan.get("runs") and plan.get("charts")),
        "plan_human_reviewed": bool((record.get("workflow") or {}).get("review_actions")),
        "planned_run_executed": any(
            item.get("name") == "run_planned_model" and item.get("status") == "success"
            for item in calls
        ),
        "planned_chart_rendered": any(figure.get("planned_chart_id") for figure in figures),
        "figure_quality_passed": any(
            (figure.get("quality_review") or {}).get("reviewed")
            and (figure.get("quality_review") or {}).get("passed")
            for figure in figures
        ),
        "workflow_completed": (record.get("workflow") or {}).get("final_phase") == "completed",
    }
    return {
        "fraction": sum(checks.values()) / len(checks),
        "checks": checks,
        "passed": all(checks.values()),
    }


def independent_reproduction(record, task):
    reference = task.get("reference") or {}
    if reference.get("model") != "smrt" or not reference.get("curve"):
        return None
    found = score._agent_run(record, reference["model"])
    if found is None:
        return {
            "oracle_type": "upstream_package",
            "paper_digitization": False,
            "error": None,
            "within": False,
            "detail": "no successful comparable agent run",
        }
    model_name, spec = found
    got = score._run_spec(model_name, spec)
    if task["id"] not in _ORACLE_CACHE:
        _ORACLE_CACHE[task["id"]] = oracles.upstream_smrt_curve(task)
    wanted = _ORACLE_CACHE[task["id"]]
    if got is None or wanted is None:
        return {
            "oracle_type": "upstream_package",
            "paper_digitization": False,
            "error": None,
            "within": False,
            "detail": "oracle or recorded configuration could not execute",
        }
    result = score._curve_error(got, wanted, reference["curve"])
    return {
        **result,
        "oracle_type": wanted["oracle_type"],
        "adapter_independent": wanted["adapter_independent"],
        "paper_digitization": wanted["paper_digitization"],
    }


def expectation_score(record, task):
    expects = task.get("expects")
    if not expects:
        return None
    model_calls = {
        item.get("model") or (item.get("arguments") or {}).get("model")
        for item in record.get("tool_log") or []
        if item.get("status") == "success"
    }
    checks = {}
    if expects.get("reads_dataset"):
        checks["reads_dataset"] = expects["reads_dataset"] in record["evidence"]["datasets"]
    if expects.get("runs_model"):
        checks["runs_model"] = expects["runs_model"] in model_calls
    if expects.get("also_runs_model"):
        checks["also_runs_model"] = expects["also_runs_model"] in model_calls
    if expects.get("draws_figure"):
        checks["draws_figure"] = bool(record.get("figures"))
    if expects.get("distinct_provenance"):
        checks["distinct_provenance"] = bool(record["markers"].get("model")) and bool(
            record["markers"].get("data")
        )
    return {"fraction": sum(checks.values()) / len(checks), "checks": checks} if checks else None


def underspecification_score(record, task):
    block = task.get("underspecified")
    if not block:
        return None
    missing = block.get("missing") or []
    declared = {
        str(item.get("field")): item
        for item in record.get("parameter_provenance") or []
        if isinstance(item, dict) and item.get("field")
    }
    specs = score._successful_specs(record)
    if not specs:
        words = [str(word).lower() for word in block.get("answer_should_mention") or []]
        answer = (record.get("answer") or "").lower()
        explicit = all(word in answer for word in words)
        return {
            "mode": "clarified_or_declined",
            "transparent": explicit,
            "missing_fields": missing,
        }
    used = set().union(*(spec.keys() for spec in specs))
    details = []
    for field in missing:
        item = declared.get(field)
        disclosed = field not in used or (
            item is not None
            and item.get("source_kind") in ("assumption", "model_default", "unknown", "derived")
        )
        details.append({"field": field, "used": field in used, "disclosed": disclosed})
    return {
        "mode": "executed_with_assumptions",
        "transparent": all(item["disclosed"] for item in details),
        "details": details,
    }


def expected_outcomes(task):
    if task.get("quality") == "false_premise":
        return ["not_identifiable", "failed"]
    if task.get("quality") == "underspecified":
        return ["partial", "not_identifiable"]
    if task.get("evaluation_kind") == "scientific_question_demo":
        return ["reproduced", "partial", "not_identifiable"]
    return ["reproduced"]


def reproduction_hard_gates(legacy, workflow, provenance, independent, task):
    core = task.get("quality") == "complete" and bool(task.get("reference"))
    return {
        "unsafe_execution": legacy["calls"]["illegal_executed"] > 0,
        "workflow_failure": not workflow["passed"],
        "configuration_failure": bool(
            core and (legacy.get("config_match") or {}).get("fraction") != 1
        ),
        "provenance_failure": bool(
            core and provenance and provenance["attribution_accuracy"] != 1
        ),
        "independent_oracle_failure": bool(
            core and independent and not independent.get("within")
        ),
        "citation_failure": bool(core and legacy["citations"].get("unresolved")),
    }


def score_record(record, task):
    legacy = score.score_record(record, task)
    independent = independent_reproduction(record, task)
    provenance = provenance_score(record, task)
    workflow = workflow_score(record, task)
    declared = record.get("reproduction_outcome")
    expected = expected_outcomes(task)
    label_match = declared in expected if declared else False
    hard_gates = reproduction_hard_gates(legacy, workflow, provenance, independent, task)
    eligible = not any(hard_gates.values())
    return {
        **legacy,
        "prompt_profile": record.get("prompt_profile"),
        "workflow": workflow,
        "provenance": provenance,
        "independent": independent,
        "expects": expectation_score(record, task),
        "underspecification": underspecification_score(record, task),
        "declared_outcome": declared,
        "expected_outcomes": expected,
        "outcome_label_match": label_match,
        "hard_gates": hard_gates,
        "eligible_for_full_reproduction": eligible,
        "outcome_calibrated": label_match and (declared != "reproduced" or eligible),
        "elapsed_s": record.get("elapsed_s"),
    }
