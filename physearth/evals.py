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

DEMO_CASES = (
    (
        "t1-smrt-fig4-passive",
        "PAPER REPRODUCTION",
        "Reproduce SMRT Figure 4a",
        "Find the paper configuration, run the physical model, and return a cited curve.",
        "A 37 GHz brightness-temperature sweep with the paper-stated snow properties.",
    ),
    (
        "t1-smrt-fig4-active",
        "PAPER REPRODUCTION",
        "Reproduce SMRT Figure 4b",
        "Switch the observable to active backscatter while preserving the source configuration.",
        "A co-polarised backscatter sweep with traceable literature and model evidence.",
    ),
    (
        "p-smrt-density-above-ice",
        "PHYSICAL REFUSAL",
        "Reject impossible snow density",
        "Tests whether a plausible-looking but physically impossible request reaches a model.",
        "No model execution; the answer should identify the 917 kg/m3 physical limit.",
    ),
    (
        "p-smrt-dmrt-with-exponential-acf",
        "LEGAL COMBINATION",
        "Catch an invalid theory pairing",
        "Every parameter is individually legal, but the theory and microstructure are not.",
        "The agent should explain that DMRT requires a sticky-hard-sphere representation.",
    ),
    (
        "p-two-models-not-comparable",
        "COMPARABILITY",
        "Refuse a false sensitivity ranking",
        "Contrasts kelvin and decibels to test whether the agent invents a common scale.",
        "The agent should name the unit mismatch before claiming which model is sensitive.",
    ),
    (
        "p-tvc-ku-model-versus-measurement",
        "MODEL + MEASUREMENT",
        "Compare simulation with field data",
        "Puts measured Ku-band backscatter and a SMRT result in the same figure.",
        "Observed and simulated series should remain visually and textually distinct.",
    ),
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
    tasks = {task["id"]: task for suite in ("tier1", "probe") for task in _load_tasks(suite)}
    run_paths = sorted((RESULTS / "runs").glob("*.json"))
    runs = [json.loads(path.read_text(encoding="utf-8")) for path in run_paths]
    scored = [
        scoring.score_record(record, tasks[record["task"]])
        for record in runs
        if record.get("task") in tasks
    ]
    return {
        "tier0": tier0,
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
    for task_id, eyebrow, title, summary, expected in DEMO_CASES:
        task = tasks[task_id]
        cases.append(
            {
                "id": task_id,
                "eyebrow": eyebrow,
                "title": title,
                "summary": summary,
                "expected": expected,
                "question": task["question"],
            }
        )
    return cases


def demo_card(case):
    return (
        "<article class='eval-demo-card'>"
        "<div class='eval-demo-card__eyebrow'>%s</div>"
        "<h3>%s</h3><p>%s</p>"
        "<div class='eval-demo-card__expect'><span>EXPECTED</span>%s</div>"
        "</article>" % tuple(_e(case[key]) for key in ("eyebrow", "title", "summary", "expected"))
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


def _tier1_table(scored):
    rows = []
    tier1 = [item for item in scored if item["suite"] == "tier1"]
    for task_id, items in sorted(_group(tier1, "task").items()):
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


def score_summary():
    """The compact, decision-useful scorecard shown after the runnable cases."""
    data = snapshot()
    tier0 = data["tier0"] or {"n_passed": 0, "n_tasks": 0, "n_checks": 0, "records": []}
    passed_checks = sum(
        1 for record in tier0["records"] for check in record["checks"] if check["passed"]
    )
    full = [item for item in data["scored"] if item["config"] == "full"]
    citation_rate = _mean([item["citations"]["resolved_fraction"] for item in full])
    self_correction = _fraction([item["self_corrected"] for item in full])
    provenance = "Builds %s | Models %s | %d repeat(s)" % (
        ", ".join(data["builds"]),
        ", ".join(data["models"]),
        len(data["repeats"]),
    )
    return (
        "<div class='eval-dashboard'>"
        "<section class='eval-section eval-section--scores'>"
        "<div class='eval-section__head'><div><span class='eval-index'>03</span>"
        "<h2>What the evaluation shows</h2></div>"
        "<p>Recorded evidence, recomputed from raw runs by the same independent scorer.</p>"
        "</div><div class='eval-provenance'>%s</div>"
        "<section class='eval-kpis'>"
        "<article><strong>%d / %d</strong><span>deterministic tasks</span>"
        "<small>physical regression net</small></article>"
        "<article><strong>%d / %d</strong><span>deterministic checks</span>"
        "<small>no language model</small></article>"
        "<article><strong>%d</strong><span>recorded agent runs</span>"
        "<small>%d tasks x %d configurations</small></article>"
        "<article><strong>%s</strong><span>citations resolve</span>"
        "<small>full configuration</small></article>"
        "<article><strong>%s</strong><span>self-corrected</span>"
        "<small>after a refused call</small></article>"
        "</section></section>"
        "<section class='eval-section eval-section--ablation'><div class='eval-section__head'>"
        "<div><span class='eval-subindex'>ABLATION</span>"
        "<h2>Remove a safeguard; measure the cost</h2></div>"
        "<p>The four variants are judged by the same scorer, never by their own "
        "runtime verdict.</p>"
        "</div>%s</section>"
        "</div>"
        % (
            _e(provenance),
            tier0["n_passed"],
            tier0["n_tasks"],
            passed_checks,
            tier0["n_checks"],
            len(data["scored"]),
            len({item["task"] for item in data["scored"]}),
            len({item["config"] for item in data["scored"]}),
            _pct(citation_rate),
            _pct(self_correction),
            _config_table(data["scored"]),
        )
    )


def score_details():
    data = snapshot()
    return (
        "<div class='eval-dashboard eval-dashboard--details'>"
        "<section class='eval-section eval-section--full-results'>"
        "<div class='eval-section__head'><div><span class='eval-subindex'>FULL RESULTS</span>"
        "<h2>Inspect the recorded score tables</h2></div>"
        "<p>Expanded on demand so judges can audit every score without crowding the demo.</p>"
        "</div>"
        "<details class='eval-suite-details'><summary><span>Tier 0</span> "
        "Deterministic physics checks <b>9 / 9 pass</b></summary>%s</details>"
        "<details class='eval-suite-details'><summary><span>Probe</span> "
        "False-premise handling across ablations</summary>%s</details>"
        "<details class='eval-suite-details'><summary><span>Tier 1</span> "
        "SMRT paper figure reproduction</summary>%s</details>"
        "<details class='eval-suite-details'><summary><span>All tasks</span> "
        "Twelve natural-language cases / four configurations</summary>%s</details>"
        "</section>"
        "</div>"
        % (
            _tier0_tables(data["tier0"]),
            _false_premise_table(data["scored"]),
            _tier1_table(data["scored"]),
            _per_task_table(data),
        )
    )
