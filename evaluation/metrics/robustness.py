"""Score dimension D without mixing incomparable language-model runs."""

import statistics
from collections import defaultdict


UNKNOWN = "unrecorded"


def model_metadata(record):
    raw = record.get("llm")
    if isinstance(raw, dict):
        return {
            "id": raw.get("id") or UNKNOWN,
            "provider": raw.get("provider") or UNKNOWN,
            "temperature": raw.get("temperature"),
            "seed": raw.get("seed"),
        }
    return {
        "id": raw or UNKNOWN,
        "provider": (record.get("provider") or {}).get("name")
        if isinstance(record.get("provider"), dict)
        else record.get("provider") or UNKNOWN,
        "temperature": record.get("temperature"),
        "seed": record.get("seed"),
    }


def prompt_profile(record):
    return record.get("prompt_profile") or "legacy_unprofiled"


def _quartiles(values):
    if not values:
        return None, None, None
    ordered = sorted(values)
    median = statistics.median(ordered)
    if len(ordered) == 1:
        return median, 0.0, 0.0
    quartiles = statistics.quantiles(ordered, n=4, method="inclusive")
    return median, quartiles[2] - quartiles[0], max(ordered) - min(ordered)


def run_score(scored):
    """A transparent 0-100 summary used only for robustness dispersion.

    Each available component has equal weight. Missing citation/configuration components
    are omitted rather than silently scored as zero, and the component count is exposed.
    """
    components = [1.0 if scored.get("completed") else 0.0]
    components.append(1.0 - float(scored.get("illegal_executed_rate") or 0.0))
    citations = (scored.get("citations") or {}).get("resolved_fraction")
    if citations is not None:
        components.append(float(citations))
    config_match = (scored.get("config_match") or {}).get("fraction")
    if config_match is not None:
        components.append(float(config_match))
    return round(100.0 * sum(components) / len(components), 2), len(components)


def analyse(records, scored_records, design):
    scored_by_key = {
        (item.get("task"), item.get("config"), item.get("llm"), item.get("repeat")): item
        for item in scored_records
    }
    rows = []
    groups = defaultdict(list)
    for record in records:
        meta = model_metadata(record)
        key = (record.get("task"), record.get("config"), meta["id"], record.get("repeat"))
        scored = scored_by_key.get(key)
        score, component_count = run_score(scored) if scored else (None, 0)
        row = {
            "run_id": record.get("run_id") or record.get("task") or UNKNOWN,
            "task": record.get("task") or UNKNOWN,
            "prompt_profile": prompt_profile(record),
            "build": record.get("build") or UNKNOWN,
            "configuration": record.get("config") or UNKNOWN,
            "llm": meta["id"],
            "provider": meta["provider"],
            "temperature": meta["temperature"],
            "seed": meta["seed"],
            "repeat": record.get("repeat"),
            "score": score,
            "score_components": component_count,
            "completed": bool(scored and scored.get("completed")),
            "stop_rule": record.get("stop_rule"),
        }
        rows.append(row)
        comparison_key = (
            row["task"],
            row["prompt_profile"],
            row["build"],
            row["configuration"],
        )
        groups[comparison_key].append(row)

    comparisons = []
    for key, items in sorted(groups.items()):
        by_llm = defaultdict(list)
        for item in items:
            by_llm[item["llm"]].append(item)
        valid_models = {
            model: model_rows
            for model, model_rows in by_llm.items()
            if model != UNKNOWN and all(row["score"] is not None for row in model_rows)
        }
        comparable = (
            key[1] != "legacy_unprofiled"
            and key[2] != UNKNOWN
            and len(valid_models) >= 2
        )
        models = []
        for model, model_rows in sorted(valid_models.items()):
            values = [row["score"] for row in model_rows]
            median, iqr, spread = _quartiles(values)
            models.append(
                {
                    "llm": model,
                    "n": len(values),
                    "median": median,
                    "iqr": iqr,
                    "spread": spread,
                }
            )
        comparisons.append(
            {
                "task": key[0],
                "prompt_profile": key[1],
                "build": key[2],
                "configuration": key[3],
                "comparable": comparable,
                "models": models,
                "reason": "ready"
                if comparable
                else "requires the same profiled prompt/build/configuration on at least two LLMs",
            }
        )

    expected = []
    existing = {
        (row["task"], row["prompt_profile"], row["llm"], row["repeat"])
        for row in rows
        if row["configuration"] == design.get("configuration", "full")
    }
    for task in design.get("tasks") or []:
        for profile in design.get("prompt_profiles") or []:
            for llm in design.get("llms") or []:
                for repeat in range(1, int(design.get("repeats") or 1) + 1):
                    cell = (task, profile["id"], llm["id"], repeat)
                    expected.append(
                        {
                            "task": task,
                            "prompt_profile": profile["id"],
                            "llm": llm["id"],
                            "provider": llm.get("provider") or UNKNOWN,
                            "repeat": repeat,
                            "recorded": cell in existing,
                        }
                    )
    recorded = sum(1 for cell in expected if cell["recorded"])
    ready = [item for item in comparisons if item["comparable"]]
    return {
        "suite": "D_LLM_robustness",
        "status": "passed" if recorded == len(expected) and ready else "insufficient_data",
        "comparison_rule": design.get("comparison_rule"),
        "coverage": {"recorded": recorded, "expected": len(expected)},
        "comparable_groups": len(ready),
        "expected_cells": expected,
        "comparisons": comparisons,
        "raw_runs": rows,
    }

