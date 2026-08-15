"""Build dimension D from the archived, like-for-like paper-reproduction runs."""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

REPRODUCTION = common.RESULTS / "reproduction"


def _load_records():
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(REPRODUCTION.glob("*/*/record.json"))
    ]


def _median(values):
    values = [float(value) for value in values if value is not None]
    return round(statistics.median(values), 2) if values else None


def _mean(values):
    values = [float(value) for value in values if value is not None]
    return round(sum(values) / len(values), 4) if values else None


def _root_cause(record):
    if not record or record.get("completed"):
        return None
    if any(
        event.get("kind") == "research_revision"
        and event.get("rule") == "model_failure_recovery"
        for event in record.get("events") or []
    ):
        return "physical_model_failure"
    return record.get("stop_reason") or "unknown"


def evaluate(records=None, design=None):
    design = design or yaml.safe_load(
        (common.ROOT / "llm_robustness.yaml").read_text(encoding="utf-8")
    )
    records = list(records if records is not None else _load_records())
    provider_by_llm = {
        item["id"]: item.get("provider") or "unrecorded" for item in design.get("llms") or []
    }
    profile = (design.get("prompt_profiles") or [{"id": "unrecorded"}])[0]["id"]
    expected = [
        (task, llm["id"], repeat)
        for task in design.get("tasks") or []
        for llm in design.get("llms") or []
        for repeat in range(1, int(design.get("repeats") or 1) + 1)
    ]
    by_cell = {(row.get("task"), row.get("llm"), 1): row for row in records}
    cells = []
    for task, llm, repeat in expected:
        record = by_cell.get((task, llm, repeat))
        protocol = ((record or {}).get("protocol") or {}).get("paper_protocol_similarity")
        cells.append(
            {
                "task": task,
                "prompt_profile": profile,
                "llm": llm,
                "provider": provider_by_llm.get(llm, "unrecorded"),
                "repeat": repeat,
                "recorded": record is not None,
                "build": (record or {}).get("build"),
                "completed": bool(record and record.get("completed") and record.get("figure_count")),
                "phase": (record or {}).get("phase"),
                "figures": int((record or {}).get("figure_count") or 0),
                "protocol_similarity": protocol,
                "elapsed_s": (record or {}).get("elapsed_s"),
                "tokens": ((record or {}).get("tokens") or {}).get("total"),
                "peak_prompt": ((record or {}).get("tokens") or {}).get("peak_prompt"),
                "model_calls": (record or {}).get("model_calls"),
                "tool_calls": (record or {}).get("tool_calls"),
                "stop_reason": (record or {}).get("stop_reason"),
                "root_cause": _root_cause(record),
                "raw_sha256": (record or {}).get("raw_sha256"),
            }
        )

    task_groups = defaultdict(list)
    model_groups = defaultdict(list)
    for cell in cells:
        if cell["recorded"]:
            task_groups[cell["task"]].append(cell)
            model_groups[cell["llm"]].append(cell)

    task_summary = []
    comparable_groups = 0
    for task in design.get("tasks") or []:
        rows = task_groups.get(task, [])
        builds = {row["build"] for row in rows if row.get("build")}
        models = {row["llm"] for row in rows}
        comparable = len(rows) >= 2 and len(builds) == 1 and len(models) >= 2
        comparable_groups += int(comparable)
        task_summary.append(
            {
                "task": task,
                "recorded": len(rows),
                "expected": len(design.get("llms") or []) * int(design.get("repeats") or 1),
                "comparable": comparable,
                "success_rate": _mean([1.0 if row["completed"] else 0.0 for row in rows]),
                "mean_protocol_similarity": _mean([row["protocol_similarity"] for row in rows]),
                "median_elapsed_s": _median([row["elapsed_s"] for row in rows]),
                "build": next(iter(builds)) if len(builds) == 1 else "mixed",
            }
        )

    model_summary = []
    for llm in [item["id"] for item in design.get("llms") or []]:
        rows = model_groups.get(llm, [])
        model_summary.append(
            {
                "llm": llm,
                "provider": provider_by_llm.get(llm, "unrecorded"),
                "recorded": len(rows),
                "success_rate": _mean([1.0 if row["completed"] else 0.0 for row in rows]),
                "mean_protocol_similarity": _mean([row["protocol_similarity"] for row in rows]),
                "median_elapsed_s": _median([row["elapsed_s"] for row in rows]),
                "total_tokens": sum(int(row["tokens"] or 0) for row in rows),
                "peak_context": max([int(row["peak_prompt"] or 0) for row in rows] or [0]),
                "failures": sum(not row["completed"] for row in rows),
            }
        )

    recorded = sum(cell["recorded"] for cell in cells)
    expected_count = len(expected)
    complete = sum(cell["completed"] for cell in cells)
    same_build = len({cell["build"] for cell in cells if cell["recorded"]}) == 1
    enough_models = len({cell["llm"] for cell in cells if cell["recorded"]}) >= 2
    status = "passed" if recorded == expected_count and same_build and enough_models else "insufficient_data"
    return {
        "schema_version": "llm-robustness-v2",
        "suite": "D_LLM_robustness",
        "status": status,
        "comparison_rule": design.get("comparison_rule"),
        "prompt_profile": profile,
        "coverage": {"recorded": recorded, "expected": expected_count},
        "completed": complete,
        "success_rate": round(complete / expected_count, 4) if expected_count else None,
        "comparable_groups": comparable_groups,
        "models": len(model_summary),
        "tasks": len(task_summary),
        "repeats": int(design.get("repeats") or 1),
        "same_build": same_build,
        "limitations": [
            "One repeat per cell: stochastic repeatability and within-model IQR are not estimated.",
            "Protocol similarity measures workflow coverage; it is not a physical curve-error metric.",
            "A recorded physical-model failure remains a failed outcome, not missing data; the terminal stop and root cause are both shown.",
        ],
        "model_summary": model_summary,
        "task_summary": task_summary,
        "cells": cells,
    }


def main():
    payload = evaluate()
    path = common.write_json("llm_robustness.json", payload)
    coverage = payload["coverage"]
    print("status: %s" % payload["status"])
    print("coverage: %d/%d planned cells" % (coverage["recorded"], coverage["expected"]))
    print("successful: %d/%d" % (payload["completed"], coverage["expected"]))
    print("comparable groups: %d" % payload["comparable_groups"])
    print("-> %s" % path.name)
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
