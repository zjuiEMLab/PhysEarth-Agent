"""Build the internal evaluation artifacts and the public English dashboard."""

import argparse
import json
import sys
from html import escape as html_escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

sys.path.insert(0, str(common.ROOT))
from metrics import competition_score  # noqa: E402

RUNS = common.RESULTS / "competition" / "runs"
OUT = common.RESULTS / "competition" / "dashboard.html"
SCORED = common.RESULTS / "competition" / "scored_runs.json"
TIER0_RESULT = common.RESULTS / "tier0.json"
REGISTRY_RESULT = common.RESULTS / "registry_contract.json"
LLM_READINESS_RESULT = common.RESULTS / "competition" / "llm_readiness.json"
FAILURES = common.RESULTS / "competition" / "failures"
PREFLIGHT_RESULT = common.RESULTS / "competition" / "preflight_attempts.json"
USAGE_LEDGER = common.RESULTS / "competition" / "usage_ledger.json"
MATRIX_PLAN_RESULT = common.RESULTS / "competition" / "matrix_plan.json"
REGISTRATION_DEMO_RESULT = common.RESULTS / "registration_demo.json"
MANIFEST = common.ROOT / "competition.yaml"
PROMPTS = common.ROOT / "prompts"


def task_index():
    tasks = {}
    for task in (item for suite in ("tier2", "probe") for item in common.load_tasks(suite)):
        tasks[task["id"]] = task
        if task.get("legacy_id"):
            tasks[task["legacy_id"]] = task
    return tasks


def load_json(path, fallback=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else fallback


def load_and_score():
    tasks = task_index()
    records = []
    for path in sorted(RUNS.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        task = tasks.get(raw.get("task"))
        if task is None:
            continue
        try:
            scored = competition_score.score_record(raw, task)
            records.append({"file": path.name, "raw": raw, "score": scored})
        except Exception as exc:
            records.append(
                {
                    "file": path.name,
                    "raw": raw,
                    "score_error": "%s: %s" % (type(exc).__name__, exc),
                }
            )
    return records


def _model_label(model):
    labels = {
        "qwen/qwen3.5-122b-a10b": "Qwen 3.5 122B",
        "deepseek/deepseek-v4-flash-0731": "DeepSeek V4 Flash",
        "openai/gpt-5.6-luna": "GPT-5.6 Luna",
        "z-ai/glm-4.7-flash": "GLM 4.7 Flash",
        "Shanghai_AI_Laboratory/Intern-S2-Preview": "Intern-S2 Preview",
    }
    return labels.get(model, model.rsplit("/", 1)[-1])


def build_matrix_plan(manifest=None):
    """Build the internal factorial plan; it is not embedded in the public page."""
    manifest = manifest or common.load_yaml(MANIFEST)
    required = manifest["competition_required"]["t2_paper_reconstruction"]
    task_ids = [*required["core_tasks"], *required["probe_tasks"]]
    tasks = task_index()
    profiles = {
        profile["id"]: profile
        for profile in (common.load_yaml(path) for path in sorted(PROMPTS.glob("*.yaml")))
    }
    execution = manifest["execution"]
    diversity = manifest["provider_diversity"]
    scenarios = []
    for task_id in task_ids:
        task = tasks[task_id]
        for profile_id in execution["prompt_profiles"]:
            profile = profiles[profile_id]
            scenarios.append(
                {
                    "id": "%s__%s" % (task_id, profile_id),
                    "task": task_id,
                    "task_title": task.get("title") or task_id,
                    "suite": task.get("suite"),
                    "quality": task.get("quality"),
                    "prompt_profile": profile_id,
                    "prompt_title": profile.get("title") or profile_id,
                    "philosophy": profile.get("philosophy"),
                }
            )
    models = [
        {
            "id": model,
            "label": _model_label(model),
            "provider": execution.get("provider", "openrouter"),
            "track": "main",
            "track_label": "Main model set",
            "repeats": execution["repeats"],
            "ranked": True,
        }
        for model in execution["llms"]
    ]
    models.extend(
        {
            "id": model,
            "label": _model_label(model),
            "provider": diversity["provider"],
            "track": "provider_diversity",
            "track_label": "ModelScope diversity",
            "repeats": diversity["repeats"],
            "ranked": bool(diversity.get("include_in_main_ranking")),
        }
        for model in diversity["llms"]
    )
    main_cells = len(scenarios) * sum(
        model["repeats"] for model in models if model["track"] == "main"
    )
    diversity_cells = len(scenarios) * sum(
        model["repeats"] for model in models if model["track"] == "provider_diversity"
    )
    return {
        "schema_version": "competition-matrix-plan-v1",
        "tasks": [
            {
                "id": task_id,
                "title": tasks[task_id].get("title") or task_id,
                "quality": tasks[task_id].get("quality"),
            }
            for task_id in task_ids
        ],
        "profiles": [
            {
                "id": profile_id,
                "title": profiles[profile_id].get("title") or profile_id,
                "philosophy": profiles[profile_id].get("philosophy"),
            }
            for profile_id in execution["prompt_profiles"]
        ],
        "models": models,
        "scenarios": scenarios,
        "main_cells": main_cells,
        "diversity_cells": diversity_cells,
        "total_cells": main_cells + diversity_cells,
    }


def _safe_json(value):
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def build_usage_ledger(records, readiness, failures=None, preflights=None):
    """Build an internal operational ledger; it is intentionally not public HTML."""
    failures = failures or []
    preflights = preflights or []
    rows = {}

    def row(provider, model):
        key = (provider or "unknown", model or "unknown")
        if key not in rows:
            rows[key] = {
                "provider": key[0],
                "model": key[1],
                "scored_cells": 0,
                "failed_attempts": 0,
                "smoke_attempts": 0,
                "attempts_with_usage": 0,
                "total_tokens": 0,
                "cost_usd": 0.0,
            }
        return rows[key]

    for provider in readiness.get("providers") or []:
        for model in provider.get("models") or []:
            row(provider.get("provider"), model.get("id"))

    def add(raw, kind):
        usage = raw.get("llm_usage") or {}
        target = row(
            raw.get("provider"),
            raw.get("llm") or raw.get("requested_model") or raw.get("model"),
        )
        target[kind] += 1
        tokens = usage.get("total_tokens")
        cost = usage.get("cost_usd")
        if isinstance(tokens, (int, float)) or isinstance(cost, (int, float)):
            target["attempts_with_usage"] += 1
        if isinstance(tokens, (int, float)):
            target["total_tokens"] += int(tokens)
        if isinstance(cost, (int, float)):
            target["cost_usd"] += float(cost)

    for record in records:
        add(record.get("raw") or {}, "scored_cells")
    for record in failures:
        add(record, "failed_attempts")
    if readiness.get("smoke"):
        add(readiness["smoke"], "smoke_attempts")
    for record in preflights:
        add(record, "smoke_attempts")

    result = []
    for value in rows.values():
        if not value["attempts_with_usage"]:
            value["total_tokens"] = None
            value["cost_usd"] = None
        else:
            value["cost_usd"] = round(value["cost_usd"], 10)
        result.append(value)
    return sorted(result, key=lambda item: (item["provider"], item["model"]))


def build_html(
    records=None,
    tier0=None,
    registry=None,
    readiness=None,
    usage_ledger=None,
    matrix_plan=None,
    demo=None,
):
    """Build the public page in English using only reviewer-facing evidence."""
    del records, tier0, readiness, usage_ledger, matrix_plan
    registry = (registry or {}).get("registry", registry or {})
    demo = demo or {}
    demo_records = demo.get("records") or []
    registry_records = registry.get("records") or []
    by_model = {record.get("model"): record for record in demo_records}

    names = []
    for record in registry_records + demo_records:
        name = record.get("model") or record.get("name")
        if name and name not in names:
            names.append(name)

    display_names = {
        "prosail": "ProSAIL",
        "pyet": "PyET",
        "pywatershed": "pywatershed",
        "smrt": "SMRT",
        "tau_omega": "tau-omega",
        "water_cloud": "water-cloud",
    }
    descriptions = {
        "prosail": "Optical canopy reflectance and NDVI",
        "pyet": "Reference evapotranspiration",
        "pywatershed": "Catchment hydrology",
        "smrt": "Snow microwave radiative transfer",
        "tau_omega": "Passive microwave emission from vegetated soil",
        "water_cloud": "Active microwave backscatter from vegetated soil",
    }

    def esc(value):
        return html_escape(str(value if value is not None else ""), quote=True)

    def ratio(passed, total):
        return "Not recorded" if total in (None, 0) else "%s / %s" % (passed, total)

    def output_text(record):
        values = record.get("output_summary") or {}
        if not values:
            return (
                "Default demo did not complete; review the local runtime"
                if record.get("error")
                else "No output summary"
            )
        return " · ".join(
            "%s = %s" % (key, value) for key, value in list(values.items())[:4]
        )

    def demo_status(record):
        if not record:
            return '<span class="status pending">Not run</span>'
        if record.get("passed"):
            return '<span class="status pass">Passed</span>'
        return '<span class="status warn">Attention</span>'

    contract_total = registry.get("n_checks", 0)
    contract_passed = registry.get("n_checks_passed", 0)
    registered_total = registry.get("n_models") or len(names)
    registered_passed = registry.get("n_passed", 0)
    demo_total = demo.get("n_models") or len(demo_records)
    demo_passed = demo.get("n_passed", 0)

    model_rows = []
    for name in names:
        demo_record = by_model.get(name) or {}
        version = demo_record.get("version")
        if not version:
            version = next(
                (
                    item.get("model_version") or item.get("version")
                    for item in registry_records
                    if item.get("model") == name
                ),
                "—",
            )
        parameters = demo_record.get("parameters") or {}
        parameter_html = html_escape(
            json.dumps(parameters, ensure_ascii=False, indent=2), quote=False
        )
        model_rows.append(
            "<tr>"
            "<td><strong>%s</strong><small>%s</small></td>"
            "<td>%s</td>"
            "<td><span class=\"description\">%s</span></td>"
            "<td>%s</td>"
            "<td><span class=\"output\">%s</span>"
            "<details><summary>View default parameters</summary><pre>%s</pre></details></td>"
            "</tr>"
            % (
                esc(display_names.get(name, name)),
                esc(name),
                esc(version),
                esc(descriptions.get(name, demo_record.get("description", ""))),
                demo_status(demo_record),
                esc(output_text(demo_record)),
                parameter_html,
            )
        )

    smrt_tasks = [
        task
        for task in task_index().values()
        if task.get("model") == "smrt" and not str(task.get("id", "")).startswith("t0-")
    ]
    smrt_tasks.sort(key=lambda task: task.get("id", ""))
    if not smrt_tasks:
        smrt_tasks = [{"id": "smrt-demos", "title": "SMRT scientific-question demos"}]
    paper_rows = "".join(
        '<tr><td><strong>%s</strong></td><td>%s</td><td><span class="status pending">Not executed</span></td></tr>'
                % (esc(task.get("id", "")), esc(task.get("title", "SMRT scientific-question demo")))
        for task in smrt_tasks
    )

    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PhysEarth-Agent · Evaluation</title>
<style>
:root{--ink:#172033;--muted:#657087;--line:#dce3ee;--panel:#fff;--soft:#f4f7fb;--blue:#2764d8;--green:#18794e;--amber:#9a6700;--navy:#101b33}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(135deg,#f7faff,#edf2f8);color:var(--ink);font:15px/1.65 Inter,Segoe UI,Arial,sans-serif}
.wrap{max-width:1220px;margin:0 auto;padding:34px 24px 72px}.top{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:28px}.eyebrow{color:var(--blue);font-size:12px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}.top h1{font-size:36px;line-height:1.15;margin:8px 0 12px;letter-spacing:-.03em}.top p{max-width:780px;color:var(--muted);margin:0}.plan-link{color:var(--blue);font-weight:700;text-decoration:none;white-space:nowrap}.plan-link:hover{text-decoration:underline}
nav{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0 30px}nav a{background:var(--navy);color:#fff;border-radius:999px;padding:8px 16px;text-decoration:none;font-weight:700;font-size:13px}nav a.secondary{background:#fff;color:var(--navy);border:1px solid var(--line)}
.hero{background:var(--navy);color:#fff;border-radius:22px;padding:26px 28px;box-shadow:0 16px 35px #101b3322;margin-bottom:26px}.hero h2{margin:0 0 7px;font-size:23px}.hero p{color:#c8d3e9;margin:0;max-width:850px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:22px}.metric{background:#ffffff1a;border:1px solid #ffffff26;border-radius:14px;padding:14px}.metric b{display:block;font-size:25px;line-height:1.15}.metric span{color:#c8d3e9;font-size:12px}
section{scroll-margin-top:20px;margin-top:34px}.section-head{margin-bottom:14px}.section-head h2{margin:0;font-size:26px;letter-spacing:-.02em}.section-head p{margin:7px 0 0;color:var(--muted);max-width:820px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 8px 22px #2d405e0d}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:860px}th{text-align:left;color:var(--muted);font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;padding:10px 12px;border-bottom:1px solid var(--line)}td{padding:14px 12px;border-bottom:1px solid #edf1f6;vertical-align:top}tr:last-child td{border-bottom:0}td strong{display:block}td small{display:block;color:var(--muted);font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:11px}.description{display:block;max-width:360px;color:#34415a}.output{display:block;max-width:390px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px;color:#34415a}.status{display:inline-flex;border-radius:999px;padding:3px 9px;font-size:12px;font-weight:800;white-space:nowrap}.status.pass{background:#e3f5eb;color:var(--green)}.status.warn{background:#fff4d6;color:var(--amber)}.status.pending{background:#edf1f7;color:#59677f}.panel details{margin-top:8px}.panel summary{cursor:pointer;color:var(--blue);font-size:12px;font-weight:700}.panel pre{background:var(--soft);border-radius:9px;padding:10px;max-height:170px;overflow:auto;font-size:11px;line-height:1.45}
.read-guide{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}.guide{background:var(--soft);border-radius:14px;padding:15px}.guide b{display:block;margin-bottom:5px}.guide p{color:var(--muted);font-size:13px;margin:0}.paper-state{display:flex;align-items:center;gap:14px;background:#fff8e5;border:1px solid #f0d58a;border-radius:14px;padding:16px;margin-bottom:16px}.paper-state b{color:var(--amber)}.paper-state span{color:#6f5a25;font-size:13px}.paper-copy{color:var(--muted);max-width:900px;margin:0 0 18px}.paper-table{min-width:700px}.paper-note{margin-top:16px;background:var(--soft);border-radius:12px;padding:14px;color:var(--muted);font-size:13px}.footer{color:var(--muted);font-size:12px;margin-top:30px}
@media(max-width:800px){.wrap{padding:24px 15px 50px}.top{display:block}.top h1{font-size:30px}.plan-link{display:inline-block;margin-top:14px}.metrics{grid-template-columns:repeat(2,1fr)}.read-guide{grid-template-columns:1fr}}
</style></head><body><main class="wrap">
<header class="top"><div><div class="eyebrow">PhysEarth-Agent · evaluation</div><h1>Model Registration Tests and SMRT Scientific Questions</h1><p>For first-time users and reviewers: first check whether the registered models are discoverable, valid, and runnable through a small bundled example. Then inspect four paper-grounded SMRT scientific-question demos. They are bounded pilots and are explicitly marked as not executed.</p></div><a class="plan-link" href="../../COMPETITION_EVAL_PLAN.html">Read the evaluation plan ↗</a></header>
<nav><a href="#registration">Model registration tests</a><a class="secondary" href="#paper">Paper reproduction results</a></nav>
<div class="hero"><h2>Current evaluation status</h2><p>Registration checks and bundled demos are repeatable local computations. The four SMRT scientific-question demos are the next work item and are not included in the completed result.</p><div class="metrics"><div class="metric"><b>__REGISTERED__</b><span>registered models passed</span></div><div class="metric"><b>__CONTRACT__</b><span>registration checks passed</span></div><div class="metric"><b>__DEMOS__</b><span>bundled demos passed</span></div><div class="metric"><b>Not executed</b><span>SMRT scientific-question demos</span></div></div></div>
<section id="registration"><div class="section-head"><h2>Model registration tests</h2><p>This section checks the model card, parameter constraints, adapter entrypoint, and one default run. A pass means the model is callable and auditable; it does not by itself establish a scientific conclusion.</p></div>
<div class="panel"><div class="table-wrap"><table><thead><tr><th>Registered model</th><th>Version</th><th>What it does</th><th>Bundled demo</th><th>Demo output</th></tr></thead><tbody>__MODEL_ROWS__</tbody></table></div></div>
<div class="read-guide"><div class="guide"><b>Model card</b><p>Defines inputs, defaults, valid domains, units, and outputs so users know what the model can answer.</p></div><div class="guide"><b>Registration checks</b><p>Exercise defaults, numeric boundaries, enum values, invalid combinations, and sweep contracts against the adapter.</p></div><div class="guide"><b>Bundled demo</b><p>Runs a minimal default case and displays a real output summary. A failed demo remains visible as an attention state.</p></div></div></section>
<section id="paper"><div class="section-head"><h2>Paper reproduction results</h2><p>Only four paper-grounded SMRT scientific-question demos are retained for now. They have not been executed, so planned work is not presented as completed evidence.</p></div>
<div class="panel"><div class="paper-state"><b>SMRT demos · Not executed</b><span>No pilot result, fixed-figure score, or provenance conclusion is available yet.</span></div><p class="paper-copy">When executed, the Agent must translate each scientific question into a bounded pilot, separate source facts from assumptions, run only legal local configurations, report external-model boundaries, and preserve limitations. The table lists planned cases only.</p><div class="table-wrap"><table class="paper-table"><thead><tr><th>Planned case</th><th>Question</th><th>Status</th></tr></thead><tbody>__PAPER_ROWS__</tbody></table></div><div class="paper-note">The “Not executed” state is intentional. It is not a model failure and does not imply an estimated score. Evidence, source spans, pilot outputs, and replay records will be added after the scientific-question runs.</div></div></section>
<div class="footer">Generated from local deterministic evaluation artifacts. Unfinished paper reproduction is excluded from completed-result statistics.</div>
</main></body></html>"""
    return (
        html.replace("__REGISTERED__", esc(ratio(registered_passed, registered_total)))
        .replace("__CONTRACT__", esc(ratio(contract_passed, contract_total)))
        .replace("__DEMOS__", esc(ratio(demo_passed, demo_total)))
        .replace("__MODEL_ROWS__", "".join(model_rows))
        .replace("__PAPER_ROWS__", paper_rows)
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args(argv)
    records = load_and_score()
    tier0 = load_json(TIER0_RESULT, {})
    registry = load_json(REGISTRY_RESULT, {})
    readiness = load_json(LLM_READINESS_RESULT, {})
    failures = [load_json(path, {}) for path in sorted(FAILURES.glob("*.json"))]
    preflights = (load_json(PREFLIGHT_RESULT, {}) or {}).get("records") or []
    usage_ledger = build_usage_ledger(records, readiness, failures, preflights)
    matrix_plan = build_matrix_plan()
    demo = load_json(REGISTRATION_DEMO_RESULT, {})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    SCORED.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    USAGE_LEDGER.write_text(json.dumps(usage_ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    MATRIX_PLAN_RESULT.write_text(json.dumps(matrix_plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    args.output.write_text(
        build_html(records, tier0, registry, readiness, usage_ledger, matrix_plan, demo),
        encoding="utf-8",
        newline="\n",
    )
    errors = sum(1 for record in records if record.get("score_error"))
    print(
        "dashboard: %d registered model(s), %d demo(s); SMRT scientific-question demos not executed; %d scoring error(s) -> %s"
        % (registry.get("n_models", 0), demo.get("n_passed", 0), errors, args.output)
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
