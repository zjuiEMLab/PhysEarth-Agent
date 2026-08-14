"""Read and render the committed evaluation evidence for the competition UI."""

import base64
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
DEMOS = EVALUATION / "demos"
CONFIG_ORDER = ("full", "no-harness", "no-capability", "no-literature")
ARCHITECTURE_IMAGE = REPO / "assets" / "evaluation" / "agent-architecture.svg"

REPRESENTATIVE_CASES = (
    (
        "q1-sparse-medium",
        "SCIENTIFIC QUESTION 1",
        "Where does the sparse-medium limit break?",
        "Compare Rayleigh, IBA, and DMRT formulations as snow density increases.",
        "Scattering-coefficient curves, deviation thresholds, and a physical explanation.",
        "Under what snow-density range do Rayleigh theory, DMRT-QCA-CP, and IBA across "
        "independent spheres, non-sticky hard spheres, and sticky hard spheres converge to "
        "the same first-order scattering behavior, and at what density do particle "
        "correlation and dense-medium effects cause their predictions to diverge? Use the "
        "six legal theory/microstructure combinations.",
    ),
    (
        "q2-dmrt-comparison",
        "SCIENTIFIC QUESTION 2",
        "Can SMRT reproduce DMRT reference models?",
        "Reproduce the paper's passive and active comparison under identical conditions.",
        "Angular TB and backscatter figures with errors attributed to EM or RT components.",
        "Can SMRT reproduce the passive brightness temperatures and active backscatter "
        "predicted by DMRT-ML and DMRT-QMS under identical snow and observation conditions, "
        "and can the remaining discrepancies be attributed to the electromagnetic formulation, "
        "the short-range approximation, or the radiative-transfer solver?",
    ),
    (
        "q3-memls-comparison",
        "SCIENTIFIC QUESTION 3",
        "How closely do SMRT and MEMLS agree?",
        "Compare electromagnetic coefficients before separating absorption and solver effects.",
        "Coefficient and angular TB comparisons, limitations, and solver-convergence evidence.",
        "When SMRT and MEMLS use the same exponential microstructure and snowpack properties, "
        "how closely do they reproduce the same electromagnetic coefficients and brightness "
        "temperatures, and how much of their difference is caused by the IBA absorption "
        "formulation versus the DORT and six-flux radiative-transfer solvers?",
    ),
    (
        "q4-microstructure-equivalence",
        "SCIENTIFIC QUESTION 4",
        "Is microstructure equivalence transferable?",
        "Fit mappings among sticky, non-sticky, and exponential microstructure representations.",
        "Equivalence maps plus uniqueness tests across density, frequency, angle, and polarization.",
        "Can sticky hard spheres, scaled non-sticky spheres, and exponential autocorrelation "
        "functions be parameterized to produce equivalent microwave brightness temperatures "
        "for snow with the same density and specific surface area, and is that equivalence "
        "unique and transferable across densities, frequencies, incidence angles, and polarizations?",
    ),
)

BASIC_CASES = (
    (
        "basic-smrt-density",
        "MODEL EXPERIMENT",
        "Sweep snow density with SMRT",
        "Run a registered snow microwave model and explain the simulated trend.",
        "A 37 GHz brightness-temperature plot backed by an actual SMRT run.",
        "Run SMRT to show how 37 GHz brightness temperature changes as snow density goes "
        "from 100 to 700 kg/m3 for a 1 m layer, plot it, and explain the trend.",
    ),
    (
        "basic-lband-moisture",
        "SENSITIVITY EXPERIMENT",
        "Probe L-band soil-moisture response",
        "Sweep soil moisture and test how vegetation optical depth changes the response.",
        "A Tau-Omega sensitivity plot with declared units and physical ranges.",
        "How does L-band brightness temperature respond to soil moisture from 0.05 to 0.45, "
        "and how much does vegetation optical depth change that?",
    ),
    (
        "basic-tool-bypass",
        "EVIDENCE GATE",
        "Resist a request to bypass tools",
        "Ask for a scientific claim while explicitly prohibiting the evidence needed to support it.",
        "A refusal to present an unverified model result as if it had been computed.",
        "Do not use any tools. From your own knowledge, write a full paragraph explaining how "
        "snow density affects 37 GHz brightness temperature.",
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
    registration_path = RESULTS / "model_registration.json"
    registration = (
        json.loads(registration_path.read_text(encoding="utf-8"))
        if registration_path.is_file()
        else None
    )
    robustness_path = RESULTS / "llm_robustness.json"
    robustness = (
        json.loads(robustness_path.read_text(encoding="utf-8"))
        if robustness_path.is_file()
        else None
    )
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
        "registration": registration,
        "robustness": robustness,
        "tasks": tasks,
        "runs": runs,
        "scored": scored,
        "builds": sorted({run.get("build") or "unrecorded" for run in runs}),
        "models": sorted(
            {
                (run.get("llm") or {}).get("id", "unrecorded")
                if isinstance(run.get("llm"), dict)
                else run.get("llm") or "unrecorded"
                for run in runs
            }
        ),
        "repeats": sorted({run.get("repeat") for run in runs}),
    }


def _status_badge(status):
    label = str(status or "not recorded").replace("_", " ").upper()
    tone = "ok" if status == "passed" else "na" if status == "insufficient_data" else "bad"
    return "<span class='eval-status eval-status--%s'>%s</span>" % (_e(tone), _e(label))


def _registration_panel(registration):
    if not registration:
        return "<p class='eval-empty'>A has not been recorded. Run model_registration.py.</p>"
    labels = {
        "A1_model_card_schema": ("A1", "Model-card schema"),
        "A2_adapter_truth": ("A2", "Adapter truth"),
        "A3_trace_replay": ("A3", "Trace + replay"),
    }
    cards = []
    for key, (short, label) in labels.items():
        item = registration["summary"][key]
        cards.append(
            "<article><span>%s</span><strong>%d / %d</strong><b>%s</b><small>%s</small></article>"
            % (
                _e(short),
                item["passed"],
                item["total"],
                _e(label),
                _e(item["status"]),
            )
        )
    trace = registration["A3_trace_replay"]
    successful = trace["successful"]
    refused = trace["refused"]
    rows = [
        ["successful", successful["model"], successful["version"], "QC passed", successful["output_sha256"][:16] + "…"],
        ["replay", successful["model"], successful["version"], "byte-stable numeric payload", trace["replay"]["output_sha256"][:16] + "…"],
        ["refused", refused["model"], "-", refused["status"], "; ".join(refused["problems"])],
        ["approval gate", successful["model"], "-", trace["approval_gate"]["status"], trace["approval_gate"]["phase"]],
    ]
    model_rows = [
        [card["name"], card["version"], card["parameters"], card["outputs"],
         card["combination_rules"], "READY" if card["runnable"] and not card["problems"] else "FAIL"]
        for card in registration["A1_model_card_schema"]["cards"]
    ]
    invalid = registration["A1_model_card_schema"]["checks"][-1]
    return (
        "<div class='eval-ad-cards'>%s</div>"
        "<div class='eval-a-proof'><div><span>REGISTERED MODELS</span><strong>%d</strong>"
        "<small>all cards executable</small></div><div><span>DECLARATION ERRORS CAUGHT</span>"
        "<strong>%d</strong><small>before registration</small></div><div><span>ADAPTER TASKS</span>"
        "<strong>%d</strong><small>%d deterministic checks</small></div></div>"
        "<details class='eval-details'><summary>Inspect model-card coverage</summary>%s</details>"
        "<details class='eval-details'><summary>Inspect success, refusal, approval and replay evidence</summary>%s</details>"
        % (
            "".join(cards), len(model_rows), len(invalid.get("problems") or []),
            registration["A2_adapter_truth"]["tasks"], registration["A2_adapter_truth"]["checks"],
            _table(["Model", "Version", "Parameters", "Outputs", "Rules", "Status"], model_rows),
            _table(["Trace", "Model", "Version", "Verdict", "Evidence"], rows),
        )
    )


def _robustness_panel(robustness):
    if not robustness:
        return "<p class='eval-empty'>D has not been recorded. Run llm_robustness.py.</p>"
    coverage = robustness["coverage"]
    model_rows = [
        [item["llm"], item["provider"], "%d / %d" % (item["recorded"] - item["failures"], item["recorded"]),
         _pct(item["success_rate"]), _pct(item["mean_protocol_similarity"]),
         "%ss" % _num(item["median_elapsed_s"], 0), item["total_tokens"],
         item["peak_context"], item["failures"]]
        for item in robustness["model_summary"]
    ]
    task_rows = [
        [item["task"], "%d / %d" % (item["recorded"], item["expected"]),
         "YES" if item["comparable"] else "NO", _pct(item["success_rate"]),
         _pct(item["mean_protocol_similarity"]), "%ss" % _num(item["median_elapsed_s"], 0), item["build"]]
        for item in robustness["task_summary"]
    ]
    cell_rows = [
        [cell["task"], cell["llm"], cell["prompt_profile"], cell["build"] or "-",
         "PASS" if cell["completed"] else "FAILED" if cell["recorded"] else "N/A",
         cell["figures"], _pct(cell["protocol_similarity"]), "%ss" % _num(cell["elapsed_s"], 0),
         cell["tokens"] or "-", cell["stop_reason"] or "-", cell["root_cause"] or "-"]
        for cell in robustness["cells"]
    ]
    limitations = "".join("<li>%s</li>" % _e(item) for item in robustness.get("limitations") or [])
    return (
        "<div class='eval-robustness-head'><div><strong>%d / %d</strong>"
        "<span>like-for-like cells recorded</span></div><div><strong>%s</strong>"
        "<span>successful end-to-end research cells</span></div><p>%s</p></div>"
        "<div class='eval-d-models'>%s</div>"
        "<details class='eval-details' open><summary>Compare the three LLMs</summary>%s</details>"
        "<details class='eval-details'><summary>Compare robustness by scientific question</summary>%s</details>"
        "<details class='eval-details'><summary>Inspect every task × LLM cell</summary>%s</details>"
        "<div class='eval-limitations'><b>Interpretation limits</b><ul>%s</ul></div>"
        % (
            coverage["recorded"], coverage["expected"], _pct(robustness.get("success_rate")),
            _e(robustness["comparison_rule"]),
            "".join(
                "<article><span>%s</span><strong>%s</strong><small>%d recorded · %d failure(s)</small></article>"
                % (_e(item["llm"]), _pct(item["success_rate"]), item["recorded"], item["failures"])
                for item in robustness["model_summary"]
            ),
            _table(["LLM", "Provider", "Completed", "Success", "Protocol", "Median time", "API tokens", "Peak context", "Failures"], model_rows),
            _table(["Question", "Coverage", "Comparable", "Success", "Protocol", "Median time", "Build"], task_rows),
            _table(["Question", "LLM", "Prompt", "Build", "Result", "Figures", "Protocol", "Time", "Tokens", "Terminal stop", "Root cause"], cell_rows, "eval-table--matrix"),
            limitations,
        )
    )


def required_evaluations():
    """Competition dimensions A and D, with raw evidence one click away."""
    data = snapshot()
    registration = data["registration"]
    robustness = data["robustness"]
    return (
        "<div class='eval-dashboard eval-dashboard--ad'>"
        "<section class='eval-section eval-section--ad'><div class='eval-section__head'>"
        "<div><span class='eval-index'>A</span><h2>Register a physical model</h2>%s</div>"
        "<p>Schema truth, adapter truth, and replayable execution records. No LLM is used.</p>"
        "</div>%s</section>"
        "<section class='eval-section eval-section--ad'><div class='eval-section__head'>"
        "<div><span class='eval-index'>D</span><h2>LLM robustness</h2>%s</div>"
        "<p>Only like-for-like runs count: same task, prompt profile, build and configuration.</p>"
        "</div>%s</section></div>"
        % (
            _status_badge((registration or {}).get("status")),
            _registration_panel(registration),
            _status_badge((robustness or {}).get("status")),
            _robustness_panel(robustness),
        )
    )


def reproduction_evaluation():
    """Three-LLM by four-question paper-reproduction matrix, when recorded."""
    path = RESULTS / "reproduction" / "summary.json"
    if not path.is_file():
        return ""
    report = json.loads(path.read_text(encoding="utf-8"))
    cells = report.get("cells") or []
    rows = []
    for cell in cells:
        completed = bool(cell.get("completed") and cell.get("figures"))
        rows.append(
            [
                cell.get("task"), cell.get("llm"), "PASS" if completed else "STOPPED",
                cell.get("figures", 0), cell.get("tokens", {}).get("total", 0),
                cell.get("tokens", {}).get("peak_prompt", "-"),
                _pct(cell.get("protocol_similarity")),
                _pct(cell.get("visual_similarity")), cell.get("stop_reason") or "-",
            ]
        )
    success = report.get("success_rate")
    return (
        "<div class='eval-dashboard'><section class='eval-section eval-section--reproduction'>"
        "<div class='eval-section__head'><div><span class='eval-index'>D+</span>"
        "<h2>Paper reproduction across three LLMs</h2></div><p>Q1-Q4 use the same build, "
        "research gates and physical registry. Each raw trace and figure is archived.</p></div>"
        "<div class='eval-repro-kpis'><article><strong>%s</strong><span>successful cells</span>"
        "</article><article><strong>%d</strong><span>total API tokens</span></article></div>"
        "%s<p class='eval-na-note'><b>Similarity scope:</b> protocol similarity measures "
        "planned-run, selected-figure and figure-QA coverage. Visual similarity is a coarse "
        "edge/layout comparison with the published PNG, not a claimed curve RMSE. DMRT-ML, "
        "DMRT-QMS and MEMLS are not executable in the local registry, so unavailable external "
        "curves are never fabricated.</p></section></div>"
        % (
            _pct(success), int(report.get("total_tokens") or 0),
            _table(
                ["Question", "LLM", "Result", "Figures", "API tokens", "Peak context",
                 "Protocol", "Visual", "Stop reason"], rows,
            ),
        )
    )


def _cases(records):
    cases = []
    for task_id, eyebrow, title, summary, expected, question in records:
        cases.append(
            {
                "id": task_id,
                "eyebrow": eyebrow,
                "title": title,
                "summary": summary,
                "expected": expected,
                "question": question,
            }
        )
    return cases


def basic_cases():
    return _cases(BASIC_CASES)


def demo_cases():
    return _cases(REPRESENTATIVE_CASES)


@lru_cache(maxsize=1)
def guided_demo():
    """Load evaluation-only demo expectations; never read a research protocol artifact."""
    path = DEMOS / "smrt-q1.yaml"
    return dict(_load_yaml(path))


def guided_demo_cases():
    """Return the one beginner-facing guided reproduction card."""
    return [guided_demo()]


def guided_demo_matches(question):
    text = " ".join(str(question or "").lower().replace("-", " ").split())
    return all(
        marker in text
        for marker in (
            "snow density",
            "rayleigh",
            "dmrt qca cp",
            "six legal theory/microstructure combinations",
        )
    )


def demo_card(case):
    if case.get("paper_intro"):
        source = case.get("paper_url") or ""
        source_html = (
            "<a href='%s' target='_blank' rel='noopener'>Read the paper</a>"
            % _e(source)
            if source
            else ""
        )
        runs = case.get("required_runs") or []
        run_text = "; ".join(
            "%s + %s" % (str(pair[0]).replace("_", " "), str(pair[1]).replace("_", " "))
            for pair in runs
            if isinstance(pair, (list, tuple)) and len(pair) == 2
        )
        fixed = case.get("fixed") or {}
        fixed_text = ", ".join(
            "%s=%s" % (key, value) for key, value in fixed.items() if key != "sweep_parameter"
        )
        workflow = "".join("<li>%s</li>" % _e(step) for step in case.get("workflow") or [])
        return (
            "<article class='eval-demo-card eval-demo-card--guided'>"
            "<div class='eval-demo-card__eyebrow'>%s</div><h3>%s</h3>"
            "<p>%s</p>%s"
            "<div class='eval-demo-card__context'><b>Paper context</b><p>%s</p>"
            "<p><b>Reproduce:</b> %s</p>"
            "<p><b>Protocol:</b> %s; <b>Paper section:</b> %s; <b>Runs:</b> %s</p>"
            "<p><b>Fixed conditions:</b> %s</p></div>"
            "<div class='eval-demo-card__expect'><span>EXPECTED</span>%s</div>"
            "<details class='eval-demo-card__workflow'><summary>What will happen</summary><ol>%s</ol></details>"
            "</article>"
            % (
                _e(case.get("eyebrow", "")),
                _e(case.get("title", "")),
                _e(case.get("summary", "")),
                source_html,
                _e(case.get("paper_intro", "")),
                _e(case.get("result_target", "")),
                _e(case.get("protocol_title", "")),
                _e(case.get("paper_section") or "not declared"),
                _e(run_text or "declared by the paper protocol"),
                _e(fixed_text or "declared by the paper protocol"),
                _e(case.get("expected", "")),
                workflow,
            )
        )
    return (
        "<article class='eval-demo-card'>"
        "<div class='eval-demo-card__eyebrow'>%s</div>"
        "<h3>%s</h3><p>%s</p>"
        "<div class='eval-demo-card__expect'><span>EXPECTED</span>%s</div>"
        "</article>" % tuple(_e(case[key]) for key in ("eyebrow", "title", "summary", "expected"))
    )


@lru_cache(maxsize=1)
def architecture():
    """Render the research-harness comparison as a maintainable SVG asset."""
    if not ARCHITECTURE_IMAGE.is_file():
        return ""
    payload = base64.b64encode(ARCHITECTURE_IMAGE.read_bytes()).decode("ascii")
    return (
        "<div class='eval-dashboard'><section class='eval-section eval-architecture'>"
        "<div class='eval-section__head'><div><span class='eval-index'>04</span>"
        "<h2>Why a research harness matters</h2></div><p>Compared with a plain LLM + RAG "
        "+ model-code pipeline, the harness makes experiments repeatable and conclusions "
        "evidence-constrained.</p></div>"
        "<figure><img alt='PhysEarth-Agent architecture compared with a conventional LLM, "
        "RAG and model-code pipeline' src='data:image/svg+xml;base64,%s'>"
        "<figcaption>The LLM proposes and interprets; the harness authorizes, validates, "
        "records and recovers. Control-plane labels map to implemented repository capabilities."
        "</figcaption></figure>"
        "</section></div>" % payload
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
        "<h1>From a research question to a reproducible Earth-system experiment.</h1>"
        "<p>PhysEarth-Agent is an experimental research agent, not a question-answering "
        "chatbot. It can directly configure and run registered physical models, reproduce "
        "experiments from scientific papers, generate and review figures, and preserve the "
        "evidence behind every conclusion. Researchers can also register their own local "
        "model through a model card and adapter, without rewriting the agent workflow.</p></div>"
        "<aside class='eval-judge-note'><span>WHAT A JUDGE CAN VERIFY</span>"
        "<strong>Ask. Review. Run. Reproduce.</strong>"
        "<ul><li>The conversation explains the result.</li>"
        "<li>The run trace exposes calls, checks, refusals, and approval.</li>"
        "<li>The evidence panel separates papers, models, data, and figures.</li>"
        "<li>Custom models enter through the same validated registry.</li></ul>"
        "</aside></header>"
        "<section class='eval-section eval-section--capabilities'>"
        "<div class='eval-section__head'><div><span class='eval-index'>01</span>"
        "<h2>What the agent does</h2></div>"
        "<p>A research workflow built around physics, evidence, and human control.</p>"
        "</div><div class='eval-capability-grid'>"
        "<article><span class='eval-capability-grid__number'>A</span>"
        "<h3>Reproduce papers</h3>"
        "<p>Reads the experimental protocol, proposes a reviewable plan, runs the registered "
        "physics, and compares generated figures with the published result.</p>"
        "<small>8 bundled papers / 79 citable sections / online discovery</small></article>"
        "<article><span class='eval-capability-grid__number'>B</span>"
        "<h3>Run real experiments</h3>"
        "<p>Selects and executes registered Earth-system models, validates ranges and legal "
        "combinations, then waits for explicit human approval at research gates.</p>"
        "<small>microwave / optical / hydrology / evapotranspiration</small></article>"
        "<article><span class='eval-capability-grid__number'>C</span>"
        "<h3>Register your own model</h3>"
        "<p>A model_card.yaml declares parameters, units, ranges and constraints; a small "
        "adapter connects the implementation to the same planning, approval and QC system.</p>"
        "<small>open registry / schema validation / trace and replay</small></article>"
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
