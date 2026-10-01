"""A6: can the registered models run each task, and if not, why.

Each task describes what its target compares: the models named in the figure's legend or
title, and the outputs it plots, under `capability`. That is a description of the target,
not a verdict. The verdict comes from the same `research_capability_check` the agent
meets, which resolves every name against the registered cards. A correct refusal (a model
nobody registered, an output no card declares) is a result, not a failure.

Deterministic: no network, no language model.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
from physearth import research, tools  # noqa: E402
from physearth import session as session_state  # noqa: E402

SCHEMA_VERSION = "capability-gate-v1"
SUITES = ("tier1", "tier2", "probe")


def verdict(task):
    declared = task.get("capability") or {}
    models = list(declared.get("reference_models") or [])
    outputs = list(declared.get("outputs") or [])
    if not models:
        return {
            "task": task["id"],
            "verdict": "undeclared",
            "reasons": ["the task does not describe what its target compares"],
        }
    session = session_state.new_session(None)
    # The agent reads each card and its instruction before this check will vouch for a
    # model; do the same reads here, through the same tools.
    for model in task.get("models") or []:
        for name in ("list_models", "read_model_instruction"):
            tools.call(name, {"model": model}, owner=session["id"], session=session)
    report = research.capability_check(
        session,
        question=task.get("question", ""),
        reference_models=models,
        requested_outputs=outputs,
        local_models=task.get("models") or [],
    )
    unavailable = report.get("unavailable") or []
    output_gaps = report.get("unavailable_outputs") or []
    missing = {str(item.get("model")) for item in unavailable}
    reasons = [f"{item.get('model')}: {item.get('reason')}" for item in unavailable]
    reasons += [f"output {name}: no registered model declares it" for name in output_gaps]
    if output_gaps or missing >= set(models):
        result = "cannot"
    elif missing:
        result = "partial"
    else:
        result = "can"
    return {
        "task": task["id"],
        "suite": task.get("suite"),
        "models": task.get("models") or [],
        "reference_models": models,
        "outputs": outputs,
        "verdict": result,
        "reasons": reasons,
        "check_status": report.get("status"),
    }


def main():
    records = [verdict(task) for suite in SUITES for task in common.load_tasks(suite)]
    for record in records:
        print(f"{record['verdict']:<10} {record['task']:<40} {'; '.join(record['reasons'])[:110]}")
    counts = {}
    for record in records:
        counts[record["verdict"]] = counts.get(record["verdict"], 0) + 1
    payload = {
        "schema_version": SCHEMA_VERSION,
        "execution": "deterministic",
        "n_tasks": len(records),
        "verdicts": counts,
        "llm_usage": {"calls": 0, "tokens": None, "cost_usd": None},
        "records": records,
    }
    path = common.write_json("capability_gate.json", payload)
    print(f"{len(records)} tasks: {counts} -> {path}")
    return 0 if "undeclared" not in counts else 1


if __name__ == "__main__":
    raise SystemExit(main())
