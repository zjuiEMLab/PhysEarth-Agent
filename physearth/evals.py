"""Read and render the committed evaluation evidence for the competition UI."""

import html
import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import yaml

from evaluation.metrics import score as scoring

REPO = Path(__file__).resolve().parent.parent
EVALUATION = REPO / "evaluation"
TASKS = EVALUATION / "tasks"
RESULTS = EVALUATION / "results"
CONFIG_ORDER = ("full", "no-harness", "no-capability", "no-literature")

REPRESENTATIVE_TASK_IDS = (
    "t1-smrt-fig4-passive",
    "t1-smrt-fig4-active",
    "t1-smrt-fig5-iba-shs",
    "t1-smrt-fig6-memls-iba",
)


def _e(value):
    return html.escape(str(value), quote=True)


def _load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_tasks(suite):
    return [_load_yaml(path) for path in sorted((TASKS / suite).glob("*.yaml"))]


def _mean(values):
    values = [value for value in values if value is not None]
    return None if not values else sum(values) / len(values)


def _fraction(values):
    values = [value for value in values if value is not None]
    return None if not values else sum(1 for value in values if value) / len(values)


def _pct(value):
    return "-" if value is None else "%.0f%%" % (100 * value)


def _num(value, digits=1):
    return "-" if value is None else ("%.*f" % (digits, value))


def _group(items, key):
    grouped = defaultdict(list)
    for item in items:
        grouped[item[key]].append(item)
    return grouped


@lru_cache(maxsize=1)
def snapshot():
    """Recompute the displayed metrics from raw records, just like REPORT.md."""
    tier0_path = RESULTS / "tier0.json"
    tier0 = json.loads(tier0_path.read_text(encoding="utf-8")) if tier0_path.is_file() else None
    registry_path = RESULTS / "registry_contract.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.is_file() else None
    tasks = {task["id"]: task for suite in ("tier2", "probe") for task in _load_tasks(suite)}
    run_paths = sorted((RESULTS / "runs").glob("*.json"))
    runs = [json.loads(path.read_text(encoding="utf-8")) for path in run_paths]
    scored = [
        scoring.score_record(record, tasks[record["task"]])
        for record in runs
        if record.get("task") in tasks
    ]
    return {
        "tier0": tier0,
        "registry": registry,
        "tasks": tasks,
        "runs": runs,
        "scored": scored,
        "builds": sorted({run.get("build") or "unrecorded" for run in runs}),
        "models": sorted({run.get("llm") or "unrecorded" for run in runs}),
        "repeats": sorted({run.get("repeat") for run in runs}),
    }


def demo_cases():
    tasks = snapshot()["tasks"]
    cases = []
    for task_id in REPRESENTATIVE_TASK_IDS:
        task = tasks[task_id]
        source = task.get("source") or {}
        demo = task.get("demo") or {}
        expected_outputs = demo.get("expected_outputs") or []
        cases.append(
            {
                "id": task_id,
                "eyebrow": "SCIENTIFIC QUESTION DEMO · SECTION %s"
                % source.get("section", "3"),
                "title": task.get("title", task_id),
                "summary": demo.get("source_question") or task["question"],
                "expected": "; ".join(expected_outputs[:2])
                or "A bounded pilot with explicit limitations.",
                "pilot": demo.get("pilot") or {},
                # Keep the evaluation prompt for scoring, but expose the source
                # question separately for the public Live Agent prefill.
                "live_question": demo.get("source_question") or task["question"],
                "question": task["question"],
            }
        )
    return cases


def demo_card(case):
    return (
        "<article class='eval-demo-card'>"
        "<div class='eval-demo-card__eyebrow'>%s</div>"
        "<h3>%s</h3><p>%s</p>"
        "<div class='eval-demo-card__pilot'><span>PILOT</span>%s</div>"
        "<div class='eval-demo-card__expect'><span>EXPECTED</span>%s</div>"
        "</article>"
        % (
            _e(case["eyebrow"]),
            _e(case["title"]),
            _e(case["summary"]),
            _e(json.dumps(case["pilot"], ensure_ascii=False, sort_keys=True)),
            _e(case["expected"]),
        )
    )


def _table(headers, rows, classes=""):
    head = "".join("<th>%s</th>" % _e(header) for header in headers)
    body = "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % _e(cell) for cell in row) for row in rows
    )
    return (
        "<div class='eval-table-wrap'><table class='eval-table %s'>"
        "<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>" % (_e(classes), head, body)
    )


def _config_table(scored):
    by_config = _group(scored, "config")
    rows = []
    for name in CONFIG_ORDER:
        items = by_config.get(name, [])
        if not items:
            continue
        rows.append(
            [
                name,
                len(items),
                _pct(_fraction([item["completed"] for item in items])),
                _num(_mean([item["model_calls"] for item in items])),
                _pct(_mean([item["illegal_call_rate"] for item in items])),
                _pct(_mean([item["illegal_executed_rate"] for item in items])),
                _pct(_fraction([item["self_corrected"] for item in items])),
                _pct(_mean([item["citations"]["resolved_fraction"] for item in items])),
                _pct(
                    _mean(
                        [item["config_match"]["fraction"] for item in items if item["config_match"]]
                    )
                ),
            ]
        )
    return _table(
        [
            "Configuration",
            "Runs",
            "Completed",
            "LLM calls",
            "Illegal calls",
            "Illegal executed",
            "Self-corrected",
            "Citations resolve",
            "Config match",
        ],
        rows,
        "eval-table--ablation",
    )


def _tier0_tables(tier0):
    if not tier0:
        return "<p class='eval-empty'>Tier 0 has not been recorded.</p>"
    rows = [
        [
            record["id"],
            record["model"],
            len(record["checks"]),
            "PASS" if record["passed"] else "FAIL",
            record["title"],
        ]
        for record in tier0["records"]
    ]
    check_rows = []
    for record in tier0["records"]:
        for check in record["checks"]:
            label = check.get("name") or check.get("output") or check.get("check")
            check_rows.append(
                [
                    record["id"],
                    label,
                    "PASS" if check["passed"] else "FAIL",
                    check.get("detail", ""),
                ]
            )
    return (
        _table(["Task", "Model", "Checks", "Result", "What it pins"], rows)
        + "<details class='eval-details'><summary>Inspect all %d deterministic "
        "checks</summary>%s</details>"
        % (tier0["n_checks"], _table(["Task", "Check", "Result", "Detail"], check_rows))
    )


def _false_premise_table(scored):
    items = [item for item in scored if item["false_premise"]]
    by_config = _group(items, "config")
    rows = []
    for name in CONFIG_ORDER:
        group = by_config.get(name, [])
        if not group:
            continue
        rows.append(
            [
                name,
                len(group),
                _pct(_fraction([item["false_premise"]["handled"] for item in group])),
                _pct(_fraction([item["false_premise"]["executed_illegal"] for item in group])),
                _pct(_fraction([item["false_premise"]["refused_illegal"] for item in group])),
                _pct(
                    _fraction([item["false_premise"]["answer_names_the_limit"] for item in group])
                ),
            ]
        )
    return _table(
        ["Configuration", "Runs", "Handled", "Illegal executed", "Call refused", "Limit explained"],
        rows,
    )


def _tier2_table(scored):
    rows = []
    tier2 = [item for item in scored if item.get("config_match") is not None]
    for task_id, items in sorted(_group(tier2, "task").items()):
        for config_name in CONFIG_ORDER:
            subset = [item for item in items if item["config"] == config_name]
            if not subset:
                continue
            numeric = [item["numeric"] for item in subset if item["numeric"]]
            rows.append(
                [
                    task_id,
                    config_name,
                    len(subset),
                    _pct(
                        _mean(
                            [
                                item["config_match"]["fraction"]
                                for item in subset
                                if item["config_match"]
                            ]
                        )
                    ),
                    _num(_mean([item["error"] for item in numeric]), 2),
                    numeric[0]["unit"] if numeric else "-",
                    _pct(_fraction([item["within"] for item in numeric])),
                ]
            )
    return _table(
        ["Task", "Configuration", "Runs", "Config match", "Mean error", "Unit", "Within tolerance"],
        rows,
    )


def _per_task_table(data):
    scored = data["scored"]
    tasks = data["tasks"]
    rows = []
    for task_id, items in sorted(_group(scored, "task").items()):
        rows.append(
            [
                task_id,
                tasks[task_id].get("title", task_id),
                items[0]["suite"],
                items[0]["quality"] or "-",
                len(items),
                _pct(_fraction([item["completed"] for item in items])),
                _pct(_mean([item["illegal_call_rate"] for item in items])),
                _pct(_mean([item["citations"]["resolved_fraction"] for item in items])),
            ]
        )
    return _table(
        [
            "Task",
            "Case",
            "Suite",
            "Quality",
            "Runs",
            "Completed",
            "Illegal calls",
            "Citations resolve",
        ],
        rows,
    )


def dashboard():
    """Competition-facing introduction shown before cases and recorded scores."""
    return (
        "<div class='eval-dashboard'>"
        "<header class='eval-heading eval-heading--intro'><div>"
        "<span class='eval-kicker'>COMPETITION DEMONSTRATION</span>"
        "<h1>Physical Earth models, made auditable.</h1>"
        "<p>PhysEarth-Agent turns a research question into an evidence-backed physical "
        "model run. It finds the configuration in literature, checks whether the requested "
        "physics is legal, asks a human before execution, and keeps every claim traceable "
        "to what was actually read or run.</p></div>"
        "<aside class='eval-judge-note'><span>WHAT A JUDGE CAN VERIFY</span>"
        "<strong>One question. Three visible records.</strong>"
        "<ul><li>The conversation explains the result.</li>"
        "<li>The run trace exposes calls, checks, refusals, and approval.</li>"
        "<li>The evidence panel separates papers, models, data, and figures.</li></ul>"
        "</aside></header>"
        "<section class='eval-section eval-section--capabilities'>"
        "<div class='eval-section__head'><div><span class='eval-index'>01</span>"
        "<h2>What the agent does</h2></div>"
        "<p>A research workflow built around physics, evidence, and human control.</p>"
        "</div><div class='eval-capability-grid'>"
        "<article><span class='eval-capability-grid__number'>A</span>"
        "<h3>Research with evidence</h3>"
        "<p>Searches literature, opens relevant sections, and only resolves citations "
        "against evidence gathered in the current run.</p>"
        "<small>8 bundled papers / 79 citable sections / online discovery</small></article>"
        "<article><span class='eval-capability-grid__number'>B</span>"
        "<h3>Configure and run physics</h3>"
        "<p>Selects from six runnable Earth-system models, validates ranges and legal "
        "combinations, then waits for explicit human approval.</p>"
        "<small>microwave / optical / hydrology / evapotranspiration</small></article>"
        "<article><span class='eval-capability-grid__number'>C</span>"
        "<h3>Verify every result</h3>"
        "<p>Checks model outputs after execution, plots stored numeric arrays, and keeps "
        "measured and simulated series visibly distinct.</p>"
        "<small>quality control / provenance / reproducible figures</small></article>"
        "</div></section>"
        "<section class='eval-workflow' aria-label='Agent workflow'>"
        "<span>QUESTION</span><i></i><span>EVIDENCE</span><i></i><span>PLAN</span><i></i>"
        "<span>HUMAN APPROVAL</span><i></i><span>MODEL + QC</span><i></i><span>ANSWER</span>"
        "</section>"
        "<div class='eval-model-strip'><span>RUNNABLE MODELS</span>"
        "<b>SMRT</b><b>Tau-Omega</b><b>Water Cloud</b><b>PROSAIL</b>"
        "<b>PyET</b><b>PyWatershed</b></div>"
        "</div>"
    )


def _scientific_question_table():
    rows = []
    for case in demo_cases():
        rows.append(
            [
                case["id"],
                case["title"],
                "Not executed",
                "No fixed-figure score; pilot evidence will be recorded after execution.",
            ]
        )
    return _table(["Task", "Scientific question", "Status", "Public result rule"], rows)


def score_summary():
    """Show completed deterministic evidence and the current Tier 2 status."""
    data = snapshot()
    tier0 = data["tier0"] or {"n_passed": 0, "n_tasks": 0, "n_checks": 0, "records": []}
    registry = data["registry"] or {"n_models": 0, "n_passed": 0}
    passed_checks = sum(
        1 for record in tier0["records"] for check in record["checks"] if check["passed"]
    )
    return (
        "<div class='eval-dashboard'>"
        "<section class='eval-section eval-section--scores'>"
        "<div class='eval-section__head'><div><span class='eval-index'>03</span>"
        "<h2>What the evaluation shows</h2></div>"
        "<p>Completed registration evidence is shown separately from the four scientific-question "
        "demos, which have not been executed yet.</p>"
        "</div>"
        "<section class='eval-kpis'>"
        "<article><strong>%d / %d</strong><span>registered models</span>"
        "<small>contract checks</small></article>"
        "<article><strong>%d / %d</strong><span>deterministic tasks</span>"
        "<small>adapter checks</small></article>"
        "<article><strong>%d / %d</strong><span>deterministic checks</span>"
        "<small>no language model</small></article>"
        "<article><strong>0</strong><span>LLM calls</span>"
        "<small>registration evaluation</small></article>"
        "<article><strong>NOT EXECUTED</strong><span>scientific-question demos</span>"
        "<small>four SMRT pilots</small></article>"
        "</section></section>"
        "<section class='eval-section eval-section--ablation'><div class='eval-section__head'>"
        "<div><span class='eval-subindex'>PAPER-GROUNDED DEMOS</span>"
        "<h2>Four SMRT scientific questions</h2></div>"
        "<p>These cases assess research planning, legal execution, source linkage, pilot "
        "diagnostics, and limitation reporting. They do not regenerate fixed paper figures.</p>"
        "</div>%s</section>"
        "</div>"
        % (
            registry["n_passed"],
            registry["n_models"],
            tier0["n_passed"],
            tier0["n_tasks"],
            passed_checks,
            tier0["n_checks"],
            _scientific_question_table(),
        )
    )


def score_details():
    data = snapshot()
    return (
        "<div class='eval-dashboard eval-dashboard--details'>"
        "<section class='eval-section eval-section--full-results'>"
        "<div class='eval-section__head'><div><span class='eval-subindex'>FULL RESULTS</span>"
        "<h2>Inspect the completed registration evidence</h2></div>"
        "<p>Scientific-question runs will be added here only after their raw records and "
        "pilot evidence are available.</p>"
        "</div>"
        "<details class='eval-suite-details'><summary><span>Model registration tests</span> "
        "Deterministic physics and replay evidence <b>completed</b></summary>%s</details>"
        "<details class='eval-suite-details'><summary><span>Scientific-question demos</span> "
        "Four SMRT pilots <b>not executed</b></summary>%s</details>"
        "</section>"
        "</div>"
        % (
            _tier0_tables(data["tier0"]),
            _scientific_question_table(),
        )
    )
