"""Score every competition record: A4, A5, B1-B6, C1, per repeat.

Reads the records under evaluation/results/competition/runs/, or the directory given,
recomputes every score from the record (never from what the harness decided at the
time), and writes one row per record plus per-condition summaries to scores.json beside
them (evaluation/results/competition/scores.json for the default). No language model:
the judge verdicts are read from the record, where the run stored them.

    python evaluation/runners/score_runs.py
    python evaluation/runners/score_runs.py evaluation/results/competition/final-2026-10-02
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import capability_gate  # noqa: E402
import common  # noqa: E402
import competition  # noqa: E402

sys.path.insert(0, str(common.ROOT))
from metrics import competition_score  # noqa: E402

OUTPUT = common.RESULTS / "competition" / "scores.json"


def _judgement(metrics, name):
    item = (metrics or {}).get(name) or {}
    return {
        "complete": bool(item.get("complete")),
        "status": item.get("status") or (
            ("pass" if item.get("passed") else "fail") if item.get("complete") else "not_scoreable"
        ),
        "passed": bool(item.get("passed")),
        "total": item.get("total"),
        "maximum": item.get("maximum"),
        "scores": item.get("scores"),
        "summary": item.get("summary"),
        "factual_errors": item.get("factual_errors"),
        "judge_model": item.get("judge_model"),
        "standard": item.get("standard"),
        "error": item.get("error"),
    }


def _b3(figure_result):
    figure_result = figure_result or {}
    b3 = figure_result.get("numeric_b3")
    if not b3:
        return None
    return {"scorer_status": figure_result.get("status"), **b3}


def row(path, record, task, gate):
    scored = competition_score.score_record(record, task)
    metrics = record.get("dashboard_metrics") or {}
    usage = record.get("llm_usage") or {}
    stop = competition_score.final_stop(record)
    provenance = scored.get("default_provenance")
    false_premise = task.get("quality") == "false_premise"
    return {
        "record": str(path.relative_to(common.REPO)).replace("\\", "/"),
        "task": record["task"],
        "models": task.get("models"),
        "config": record.get("config"),
        "llm": record.get("llm"),
        "repeat": record.get("repeat"),
        "build": record.get("build"),
        "tag": f"{record.get('config')} r{record.get('repeat')}",
        "A4_probe": scored["workflow"] if false_premise else None,
        "A5_safety": {
            "calls": scored["calls"],
            "false_premise": scored["false_premise"],
        },
        "A6": {"verdict": gate.get("verdict"), "reasons": gate.get("reasons")},
        "B1_execution": {
            "completed": bool(str(record.get("answer") or "").strip()) and stop is None,
            "final_stop": (stop or {}).get("rule"),
            "final_stop_reason": (stop or {}).get("reason") or (stop or {}).get("detail"),
            "successful_runs": len(record.get("numeric_results") or []),
            "figures": len([f for f in record.get("figures") or [] if not f.get("preview")]),
        },
        "B2_figure_judge": _judgement(metrics, "figure_judgement"),
        "B3_numeric": _b3(metrics.get("figure_result")),
        "B4_provenance": None if provenance is None else {
            "passed": provenance.get("passed"),
            "relevant": provenance.get("relevant"),
            "mislabelled": [item["parameter"] for item in provenance.get("mislabelled") or []],
            "unlabelled": [item["parameter"] for item in provenance.get("unlabelled") or []],
        },
        "B5_report_judge": _judgement(metrics, "report_judgement"),
        "B6_outcome": scored.get("outcome"),
        "declared_outcome": record.get("reproduction_outcome"),
        "C1_cost": {
            "llm_calls": usage.get("calls"),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "cost_usd": usage.get("cost_usd"),
            "tool_calls": record.get("tool_calls"),
            "elapsed_s": record.get("elapsed_s"),
            "judge_tokens": (metrics.get("judge_usage") or {}).get("total_tokens"),
        },
    }


def _mean(values):
    values = [value for value in values if isinstance(value, (int, float))]
    return sum(values) / len(values) if values else None


def summarise(rows):
    groups = {}
    for item in rows:
        groups.setdefault((item["task"], item["config"], item["llm"]), []).append(item)
    out = []
    for (task, config, llm), items in sorted(groups.items()):
        tags = [(item["repeat"], (item["B6_outcome"] or {}).get("tag")) for item in items]
        out.append(
            {
                "task": task,
                "config": config,
                "llm": llm,
                "repeats": len(items),
                "per_repeat_tags": [{"repeat": r, "tag": t} for r, t in sorted(tags)],
                "completed": sum(item["B1_execution"]["completed"] for item in items),
                "figure_judge_pass": sum(item["B2_figure_judge"]["passed"] for item in items),
                "report_judge_pass": sum(item["B5_report_judge"]["passed"] for item in items),
                "illegal_executed": sum(
                    item["A5_safety"]["calls"]["illegal_executed"] for item in items
                ),
                "mean_llm_calls": _mean([item["C1_cost"]["llm_calls"] for item in items]),
                "mean_total_tokens": _mean([item["C1_cost"]["total_tokens"] for item in items]),
                "mean_cost_usd": _mean([item["C1_cost"]["cost_usd"] for item in items]),
                "mean_elapsed_s": _mean([item["C1_cost"]["elapsed_s"] for item in items]),
            }
        )
    return out


def main(argv=None):
    runs_dir = Path(argv[0]).resolve() if argv else competition.RUNS
    tasks = competition.load_task_index()
    gates = {}
    rows = []
    for path in sorted(runs_dir.glob("*.json")):
        if path.name == "scores.json":
            continue
        record = json.loads(path.read_text(encoding="utf-8"), strict=False)
        task = tasks.get(record.get("task"))
        if task is None:
            print(f"skip {path.name}: unknown task {record.get('task')}")
            continue
        if task["id"] not in gates:
            gates[task["id"]] = capability_gate.verdict(task)
        rows.append(row(path, record, task, gates[task["id"]]))
    payload = {
        "schema_version": "competition-scores-v1",
        "source": str(runs_dir.relative_to(common.REPO)).replace("\\", "/"),
        "n_records": len(rows),
        "summary": summarise(rows),
        "records": rows,
    }
    output = OUTPUT if not argv else runs_dir / "scores.json"
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    for item in payload["summary"]:
        tags = ", ".join(f"r{t['repeat']} {t['tag']}" for t in item["per_repeat_tags"])
        print(f"{item['task']:<32} {item['config']:<10} {item['llm']:<30} {tags}")
    print(f"{len(rows)} record(s) scored -> {output.relative_to(common.REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
