"""Turn the recorded runs into evaluation/REPORT.md.

Reads results/tier0.json and every file under results/runs/, scores each run with
metrics/score.py and writes the tables. It never calls a language model, so the report
can be rebuilt from the cache as often as needed.

  python evaluation/runners/report.py
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

sys.path.insert(0, str(common.ROOT))
from metrics import score as scoring  # noqa: E402

RUNS = common.RESULTS / "runs"
CONFIG_ORDER = ["full", "no-harness", "no-capability", "no-literature"]


def load_runs():
    if not RUNS.is_dir():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RUNS.glob("*.json"))]


def pct(value, digits=0):
    return "-" if value is None else "%.*f%%" % (digits, 100.0 * value)


def num(value, digits=2):
    return "-" if value is None else "%.*f" % (digits, value)


def tier0_section():
    payload = common.read_json("tier0.json")
    if not payload:
        return "Tier 0 has not been run. `python evaluation/runners/tier0.py`\n"
    rows = []
    for record in payload["records"]:
        failed = [c for c in record["checks"] if not c["passed"]]
        rows.append([
            record["id"],
            record["model"],
            str(len(record["checks"])),
            "pass" if record["passed"] else "%d FAILED" % len(failed),
            record["title"],
        ])
    lines = [
        "%d of %d tasks pass, %d checks in total. Nothing here calls a language model, so "
        "re-running it costs nothing and it is the regression net under every other number "
        "on this page.\n" % (payload["n_passed"], payload["n_tasks"], payload["n_checks"]),
        common.table(["task", "model", "checks", "result", "what it pins"], rows),
    ]
    upstream = [
        c
        for r in payload["records"]
        for c in r["checks"]
        if c["check"] == "upstream" and c.get("abs_error") is not None
    ]
    if upstream:
        lines.append(
            "\nThe three SMRT tasks compare the adapter against the upstream `smrt` package "
            "driven directly with its own documented recipe. Largest absolute disagreement "
            "across %d compared outputs: %.2e."
            % (len(upstream), max(c["abs_error"] for c in upstream))
        )
    return "\n".join(lines) + "\n"


def group(scored, key):
    out = defaultdict(list)
    for item in scored:
        out[item[key]].append(item)
    return out


def ablation_table(scored):
    by_config = group(scored, "config")
    order = [c for c in CONFIG_ORDER if c in by_config] + sorted(
        c for c in by_config if c not in CONFIG_ORDER
    )
    rows = []
    for name in order:
        items = by_config[name]
        rows.append([
            name,
            str(len(items)),
            pct(scoring.fraction([i["completed"] for i in items])),
            num(scoring.mean([i["model_calls"] for i in items]), 1),
            pct(scoring.mean([i["illegal_call_rate"] for i in items])),
            pct(scoring.mean([i["illegal_executed_rate"] for i in items])),
            pct(scoring.fraction([i["self_corrected"] for i in items])),
            pct(scoring.mean([i["citations"]["resolved_fraction"] for i in items])),
            pct(scoring.mean([
                i["config_match"]["fraction"] for i in items if i["config_match"]
            ])),
        ])
    return common.table(
        ["config", "runs", "completed", "LLM calls", "illegal calls",
         "illegal executed", "self-corrected", "citations resolve", "config match"],
        rows,
    )


def false_premise_table(scored):
    items = [i for i in scored if i["false_premise"]]
    if not items:
        return "No false-premise task has been run yet.\n"
    by_config = group(items, "config")
    order = [c for c in CONFIG_ORDER if c in by_config]
    rows = []
    for name in order:
        group_items = by_config[name]
        rows.append([
            name,
            str(len(group_items)),
            pct(scoring.fraction([i["false_premise"]["handled"] for i in group_items])),
            pct(scoring.fraction([i["false_premise"]["executed_illegal"] for i in group_items])),
            pct(scoring.fraction([i["false_premise"]["refused_illegal"] for i in group_items])),
            pct(scoring.fraction([
                i["false_premise"]["answer_names_the_limit"] for i in group_items
            ])),
        ])
    return common.table(
        [
            "config",
            "runs",
            "handled",
            "ran the illegal call",
            "call refused",
            "answer names the limit",
        ],
        rows,
    )


def tier1_table(scored):
    items = [i for i in scored if i["suite"] == "tier1"]
    if not items:
        return "No Tier 1 task has been run yet.\n"
    rows = []
    for task, group_items in sorted(group(items, "task").items()):
        for config_name in [c for c in CONFIG_ORDER if c in {i["config"] for i in group_items}]:
            subset = [i for i in group_items if i["config"] == config_name]
            numeric = [i["numeric"] for i in subset if i["numeric"]]
            rows.append([
                task,
                config_name,
                str(len(subset)),
                pct(
                    scoring.mean(
                        [i["config_match"]["fraction"] for i in subset if i["config_match"]]
                    )
                ),
                num(scoring.mean([n["error"] for n in numeric])),
                numeric[0]["unit"] if numeric else "-",
                pct(scoring.fraction([n["within"] for n in numeric])),
            ])
    return common.table(
        ["task", "config", "runs", "config match", "mean error", "unit", "within tolerance"],
        rows,
    )


def per_task_table(scored):
    rows = []
    for task, items in sorted(group(scored, "task").items()):
        rows.append([
            task,
            items[0]["suite"],
            items[0]["quality"] or "-",
            str(len(items)),
            pct(scoring.fraction([i["completed"] for i in items])),
            pct(scoring.mean([i["illegal_call_rate"] for i in items])),
            pct(scoring.mean([i["citations"]["resolved_fraction"] for i in items])),
        ])
    return common.table(
        [
            "task",
            "suite",
            "question quality",
            "runs",
            "completed",
            "illegal calls",
            "citations resolve",
        ],
        rows,
    )


def build():
    runs = load_runs()
    tasks = {t["id"]: t for suite in ("tier1", "probe") for t in common.load_tasks(suite)}
    references = {}
    scored = []
    for record in runs:
        task = tasks.get(record["task"])
        if task is None:
            continue
        if task["id"] not in references:
            try:
                references[task["id"]] = scoring.reference_curve(task)
            except Exception:
                references[task["id"]] = None
        scored.append(scoring.score_record(record, task, references[task["id"]]))

    llms = sorted({r["llm"] for r in runs})
    repeats = sorted({r["repeat"] for r in runs})
    builds = sorted({r.get("build") or "unrecorded" for r in runs})
    header = [
        "# PhysEarth-Agent evaluation",
        "",
        "Generated by `python evaluation/runners/report.py` from the records in "
        "`evaluation/results/`. Every number below is reproducible from this repository: the "
        "task set, the ablation configurations, the runners and the raw per-run records are "
        "all committed.",
        "",
        "## Tier 0, self-consistency",
        "",
        tier0_section(),
    ]
    if not scored:
        header.append(
            "## Agent task set\n\nNo agent run has been recorded yet. "
            "`python evaluation/runners/agent_tasks.py`\n"
        )
        return "\n".join(header)

    header += [
        "## Agent task set",
        "",
        "%d recorded runs over %d tasks, %d configurations, %d repeat(s)."
        % (len(scored), len(set(s["task"] for s in scored)),
           len(set(s["config"] for s in scored)), len(repeats)),
        "",
    ]
    # The comparison this report makes is between configurations, within a task. That
    # contrast is only meaningful if the four cells of a task share a language model and a
    # build, which is what the runner's blocked design guarantees. Several models across
    # different tasks is by design, because the free quota is counted per model per day and
    # one model does not hold enough of it. Two models inside one task would not be.
    split = sorted(
        task
        for task, items in group(scored, "task").items()
        if len({(i.get("llm"), i.get("build")) for i in items}) > 1
    )
    header += [
        "Run as a blocked design: a task is a block, and all %d configurations of a task "
        "run on one language model at one build. Models differ between tasks because the "
        "free inference quota is counted per model per day, and no single model holds "
        "enough of it for the whole sweep. Every contrast below is therefore computed "
        "within a task and then averaged across tasks; none of them straddles two models."
        % len(set(s["config"] for s in scored)),
        "",
        "Builds: %s. Models: %s." % (", ".join(builds), ", ".join(llms)),
        "",
    ]
    if split:
        header += [
            "> **%d task(s) do not hold together: %s.** Their configurations were not all "
            "run on the same model and build, so the contrast for those tasks compares two "
            "things at once. Delete their records under `evaluation/results/runs/` and "
            "re-run `agent_tasks.py`, which will place each block on one model."
            % (len(split), ", ".join(split)),
            "",
        ]
    header += [
        "Every metric on this page is recomputed from the record by "
        "`evaluation/metrics/score.py`, never read off what the harness decided at run "
        "time. A call is illegal if the model card says so, whether or not the harness was "
        "switched on to notice; a marker resolves if the run actually gathered the evidence "
        "it names, whether or not the citation gate was there to check. Without that, an "
        "ablation would be comparing each configuration to its own opinion of itself.",
        "",
        "### The three ablations",
        "",
        ablation_table(scored),
        "",
        "### False-premise questions",
        "",
        "These are the questions whose stated configuration cannot exist: a snow density "
        "above solid ice, a theory paired with a microstructure it has no derivation for, a "
        "liquid-water dielectric model asked about frozen ground, a fitted operator asked "
        "outside the angles it was fitted over, and two models asked which is more sensitive "
        "when one answers in kelvin and the other in decibels.",
        "",
        false_premise_table(scored),
        "",
        "### Tier 1, reproducing the figures of the SMRT paper",
        "",
        "Configuration match is the fraction of the fields the paper actually states that "
        "the agent got right. The error column is what changes when only those fields are "
        "corrected and every free choice the agent made is left alone, so it reports the "
        "cost of the configuration mistakes rather than the cost of a snow depth the paper "
        "never fixed.",
        "",
        tier1_table(scored),
        "",
        "### Per task",
        "",
        per_task_table(scored),
        "",
    ]
    return "\n".join(header)


def main():
    text = build()
    path = common.ROOT / "REPORT.md"
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    print("wrote %s (%d characters)" % (path, len(text)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
