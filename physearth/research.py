"""Generic, human-reviewed research state for PhysEarth.

The four SMRT scientific questions are evaluation cases, not workflow templates.  A plan
enters this module only after the language model has analysed the user's question and
submitted a structured proposal through the research_plan tool.
"""

import math
import re

from physearth import knowledge, plotting, validation
from physearth.models import registry


PHASES = (
    "plan_review",
    "plan_approved",
    "pseudo_preview",
    "chart_selected",
    "approved",
    "completed",
)


def _clean_list(values, limit=20):
    return [str(value).strip() for value in (values or []) if str(value).strip()][:limit]


def _clean_charts(charts):
    cleaned = []
    for index, chart in enumerate(charts or []):
        if not isinstance(chart, dict):
            continue
        x = str(chart.get("x") or "").strip()
        y = str(chart.get("y") or "").strip()
        if not x or not y:
            continue
        cleaned.append(
            {
                "id": str(chart.get("id") or "chart_%d" % (index + 1)).strip(),
                "label": str(chart.get("label") or "%s versus %s" % (y, x)).strip(),
                "kind": str(chart.get("kind") or "line").strip(),
                "x": x,
                "y": y,
            }
        )
    return cleaned[:8]


def _clean_runs(runs):
    cleaned = []
    problems = []
    for index, run in enumerate(runs or []):
        if not isinstance(run, dict):
            problems.append("planned run %d is not an object" % (index + 1))
            continue
        model = str(run.get("model") or "").strip()
        entry = registry.get(model)
        if entry is None:
            problems.append("planned run %d uses unknown model %r" % (index + 1, model))
            continue
        parameters = dict(run.get("parameters") or {})
        resolved, run_problems = validation.resolve(entry.card, parameters, enforce=True)
        if run_problems:
            problems.extend("planned run %d: %s" % (index + 1, item) for item in run_problems)
            continue
        cleaned.append(
            {
                "id": str(run.get("id") or "run_%d" % (index + 1)).strip(),
                "label": str(run.get("label") or "%s run" % model).strip(),
                "model": model,
                "parameters": resolved,
            }
        )
    return cleaned[:8], problems


def propose(
    session,
    question,
    objective,
    hypothesis,
    steps,
    parameters=None,
    runs=None,
    charts=None,
    success_criteria=None,
    assumptions=None,
    limitations=None,
):
    """Store an LLM-authored proposal; never infer one from a question template."""
    question = str(question or "").strip()
    objective = str(objective or "").strip()
    hypothesis = str(hypothesis or "").strip()
    steps = _clean_list(steps)
    charts = _clean_charts(charts)
    runs, run_problems = _clean_runs(runs)
    if not question or not objective or not hypothesis:
        return _fail("A proposal requires question, objective and hypothesis.")
    if len(steps) < 3:
        return _fail("A proposal requires at least three executable research steps.")
    if not charts:
        return _fail("A proposal requires at least one chart option with x and y fields.")
    if run_problems:
        return _fail("The proposed execution plan is invalid: %s" % "; ".join(run_problems))
    if not runs:
        return _fail("A proposal requires at least one explicit registered physical-model run.")
    chart_problems = _validate_chart_runs(charts, runs)
    if chart_problems:
        return _fail("The proposed chart cannot be produced by the planned runs: %s" % "; ".join(chart_problems))
    plan = {
        "title": objective,
        "question": question,
        "objective": objective,
        "hypothesis": hypothesis,
        "steps": steps,
        "parameters": dict(parameters or {}),
        "runs": runs,
        "charts": charts,
        "success_criteria": _clean_list(success_criteria, 12),
        "assumptions": _clean_list(assumptions, 12),
        "limitations": _clean_list(limitations, 12),
        "capability_gaps": _capability_gaps(question),
    }
    plan["outcome_scope"] = "partial" if plan["capability_gaps"] else "full"
    session["research"] = {
        "question": question,
        "plan_version": 1,
        "phase": "plan_review",
        "plan": plan,
        "selected_chart": None,
        "pseudo": None,
        "preview_version": 0,
        "review_log": [],
        "proposed_by": "llm",
    }
    return _needs("LLM-authored research plan v001 is ready for human review.", _public(session["research"]))


def status(session):
    project = session.get("research")
    if not project:
        return _needs("No research proposal exists yet. Analyse the question and propose one.", {"phase": "analysis"})
    return _ok("Research project is in phase %s." % project["phase"], _public(project))


def revise(session, changes=None, note=""):
    project = _require(session)
    changes = changes or {}
    plan = project["plan"]
    for key in ("objective", "hypothesis"):
        if changes.get(key):
            plan[key] = str(changes[key]).strip()
            if key == "objective":
                plan["title"] = plan[key]
    if isinstance(changes.get("parameters"), dict):
        plan["parameters"].update(changes["parameters"])
    # Also accept parameter keys directly for concise model tool calls.
    for key, value in changes.items():
        if key not in ("objective", "hypothesis", "steps", "charts", "runs", "parameters", "success_criteria", "assumptions", "limitations"):
            plan["parameters"][key] = value
    if changes.get("steps"):
        plan["steps"] = _clean_list(changes["steps"])
    if changes.get("charts"):
        charts = _clean_charts(changes["charts"])
        if charts:
            plan["charts"] = charts
    if changes.get("runs"):
        runs, problems = _clean_runs(changes["runs"])
        if problems or not runs:
            raise ValueError("Invalid revised runs: %s" % "; ".join(problems or ["none supplied"]))
        plan["runs"] = runs
    for key in ("success_criteria", "assumptions", "limitations"):
        if changes.get(key):
            plan[key] = _clean_list(changes[key], 12)
    project["plan_version"] += 1
    project["review_log"].append(
        {"version": project["plan_version"], "note": note or "user-requested revision", "changes": changes}
    )
    project["phase"] = "plan_review"
    project["selected_chart"] = None
    project["pseudo"] = None
    return _needs("Plan revised to v%03d. Review it again." % project["plan_version"], _public(project))


def approve_plan(session):
    project = _require(session)
    if project["phase"] != "plan_review":
        return _fail("The plan cannot be approved in phase %s." % project["phase"])
    project["phase"] = "plan_approved"
    return _needs("Plan approved. Generate a pseudo-data chart preview next.", _public(project))


def pseudo_preview(session):
    """Generate deterministic display-only data from the proposed axes, never physics."""
    project = _require(session)
    if project["phase"] not in ("plan_approved", "pseudo_preview"):
        return _needs("Approve the plan before requesting pseudo-data.", _public(project))
    plan = project["plan"]
    parameters = plan.get("parameters") or {}
    start, stop = _preview_bounds(parameters, plan["charts"])
    count = max(5, min(20, int(parameters.get("sweep_points", 8) or 8)))
    xs = [start + (stop - start) * index / (count - 1) for index in range(count)]
    project["preview_version"] = int(project.get("preview_version", 0)) + 1
    preview_version = project["preview_version"]
    x_names = {chart["x"] for chart in plan["charts"]}
    x_name = next(iter(x_names)) if len(x_names) == 1 else "x"
    points = []
    for index, x_value in enumerate(xs):
        row = {x_name: round(x_value, 8)}
        fraction = index / max(1, count - 1)
        for chart_index, chart in enumerate(plan["charts"]):
            row[chart["y"]] = round(
                (chart_index + 1) * (0.15 + 0.7 * fraction)
                + 0.03 * math.sin(index + preview_version - 1),
                8,
            )
        points.append(row)
    project["pseudo"] = {
        "label": "PSEUDO-DATA — layout demonstration only · preview v%03d" % preview_version,
        "points": points,
    }
    # Replace this project's old previews rather than accumulating stale layouts.  These
    # curves are deliberately tagged and labelled as pseudo-data; completion never counts
    # them because they contain no real result handles.
    session["figures"] = [figure for figure in session.get("figures") or [] if not figure.get("research_preview")]
    for chart in plan["charts"]:
        preview_series = [
            {
                "handle": "",
                "label": chart["label"],
                "x": [row.get(chart["x"]) for row in points],
                "y": [row.get(chart["y"]) for row in points],
                "x_name": chart["x"],
                "y_name": chart["y"],
                "source": "model_run",
                "origin": "pseudo-data preview v%03d" % preview_version,
                "units": {},
            }
        ]
        figure = plotting.render(
            {"title": "%s — PSEUDO-DATA PREVIEW" % chart["label"], "kind": chart["kind"]},
            preview_series,
            preview=False,
        )
        figure["preview"] = True
        figure["research_preview"] = True
        session["figures"].append(figure)
    session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1
    project["phase"] = "pseudo_preview"
    return _needs(
        "Pseudo-data preview v%03d is ready. Ask the user which chart design to use."
        % preview_version,
        _public(project),
    )


def _preview_bounds(parameters, charts):
    """Read common generic range forms without embedding any domain/question template."""
    if "sweep_start" in parameters and "sweep_stop" in parameters:
        return float(parameters["sweep_start"]), float(parameters["sweep_stop"])
    x_names = [str(chart.get("x") or "").lower() for chart in charts]
    x_roots = {name.split("_")[0] for name in x_names if name}
    candidates = []
    for key, value in parameters.items():
        normalized = str(key).lower()
        if "range" in normalized or any(root and root in normalized for root in x_roots):
            candidates.append(value)
    for value in candidates:
        if isinstance(value, dict) and "start" in value and "end" in value:
            try:
                return float(value["start"]), float(value["end"])
            except (TypeError, ValueError):
                pass
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            try:
                return float(value[0]), float(value[1])
            except (TypeError, ValueError):
                pass
        numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", str(value))
        if len(numbers) >= 2:
            return float(numbers[0]), float(numbers[1])
    return 0.0, 1.0


def choose_chart(session, chart_id):
    project = _require(session)
    if project["phase"] != "pseudo_preview":
        return _needs("Generate the pseudo-data preview before selecting a chart.", _public(project))
    chart = next((item for item in project["plan"]["charts"] if item["id"] == chart_id), None)
    if chart is None:
        return _fail("Unknown chart option %r." % chart_id)
    project["selected_chart"] = dict(chart)
    project["review_log"].append(
        {
            "version": project["plan_version"],
            "note": "user selected chart %s" % chart_id,
            "changes": {"selected_chart": chart_id},
        }
    )
    project["phase"] = "chart_selected"
    return _needs("Chart selected. Ask the user to approve formal execution.", _public(project))


def approve_execution(session):
    project = _require(session)
    if project["phase"] != "chart_selected":
        return _needs("Select a chart after the pseudo-data preview first.", _public(project))
    project["phase"] = "approved"
    return _ok("Formal execution approved. The agent may now call registered physical models.", _public(project))


def complete(session):
    project = _require(session)
    gaps = execution_gaps(session)
    if gaps["missing_runs"]:
        return _needs(
            "The workflow cannot complete; planned runs still missing: %s."
            % ", ".join(gaps["missing_runs"]),
            _public(project),
        )
    if gaps["figure_problem"]:
        return _needs(
            gaps["figure_problem"],
            _public(project),
        )
    project["phase"] = "completed"
    scope = project.get("plan", {}).get("outcome_scope", "full")
    return _ok("Research workflow completed as %s." % scope, _public(project))


def execution_gaps(session):
    """Return unmet approved-plan outputs; failed or duplicate runs never count."""
    project = session.get("research") or {}
    planned = (project.get("plan") or {}).get("runs") or []
    successful = session.get("successful_runs") or []
    matched = []
    missing = []
    for wanted in planned:
        found = next(
            (
                actual
                for actual in successful
                if actual.get("model") == wanted.get("model")
                and all(actual.get("spec", {}).get(key) == value for key, value in wanted.get("parameters", {}).items())
                and actual.get("handle") not in matched
            ),
            None,
        )
        if found:
            matched.append(found.get("handle"))
        else:
            missing.append(wanted.get("label") or wanted.get("id") or wanted.get("model"))
    figures = session.get("figures") or []
    plotted = {item.get("handle") for figure in figures for item in figure.get("series") or []}
    figure_problem = ""
    if not figures:
        figure_problem = "The workflow cannot complete before actual model outputs are plotted."
    elif matched and not set(matched).issubset(plotted):
        figure_problem = "The final figure does not contain every successful planned run."
    return {"missing_runs": missing, "matched_handles": matched, "figure_problem": figure_problem}


def _validate_chart_runs(charts, runs):
    problems = []
    for chart in charts:
        producers = []
        for run in runs:
            entry = registry.get(run["model"])
            spec = run["parameters"]
            groups = entry.card.get("output_groups") or {}
            available = groups.get(spec.get("output"), list(entry.card.get("outputs", {})))
            if (chart["x"] == "index" or spec.get("sweep_parameter") == chart["x"]) and chart["y"] in available:
                producers.append(run["id"])
        if not producers:
            problems.append(
                "no planned run produces %s over x=%s" % (chart["y"], chart["x"])
            )
    for run in runs:
        entry = registry.get(run["model"])
        groups = entry.card.get("output_groups") or {}
        available = groups.get(run["parameters"].get("output"), list(entry.card.get("outputs", {})))
        if not any(
            (chart["x"] == "index" or run["parameters"].get("sweep_parameter") == chart["x"])
            and chart["y"] in available
            for chart in charts
        ):
            problems.append("%s contributes to none of the proposed charts" % run["label"])
    return problems


def _normal_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _capability_gaps(question):
    """Named literature models that have no executable registry entry."""
    text = _normal_name(question)
    registered = {_normal_name(name) for name in registry.names()}
    gaps = []
    for item in knowledge.catalogue():
        card = knowledge.card(item["slug"]) or {}
        for alias in card.get("model_names") or []:
            normalized = _normal_name(alias)
            if normalized and normalized in text and normalized not in registered:
                gaps.append(str(alias))
                break
    return sorted(set(gaps))


def report_problem(session, answer):
    plan = ((session.get("research") or {}).get("plan") or {})
    gaps = plan.get("capability_gaps") or []
    if not gaps:
        return ""
    lowered = str(answer or "").lower()
    names_present = all(_normal_name(name) in _normal_name(answer) for name in gaps)
    limitation_present = any(
        phrase in lowered
        for phrase in ("partial", "not run", "not available", "unavailable", "not registered", "未运行", "不可用", "未注册", "部分复现")
    )
    if names_present and limitation_present:
        return ""
    return (
        "This is only a partial reproduction because these named comparison models are not "
        "registered and were not run: %s. State that limitation explicitly; do not report "
        "cross-model agreement metrics or attribute causal differences to their solvers."
        % ", ".join(gaps)
    )


def safe_report(session):
    """Deterministic last resort: report only actions recorded in session state."""
    project = session.get("research") or {}
    plan = project.get("plan") or {}
    gaps = plan.get("capability_gaps") or []
    planned = plan.get("runs") or []
    successful = session.get("successful_runs") or []
    completed = []
    for run in planned:
        if any(
            actual.get("model") == run.get("model")
            and all(actual.get("spec", {}).get(key) == value for key, value in run.get("parameters", {}).items())
            for actual in successful
        ):
            completed.append(run.get("label") or run.get("id") or run.get("model"))
    markers = sorted(session.get("models_run") or ())
    model_note = (
        " Registered model evidence: %s." % ", ".join("[model:%s]" % marker for marker in markers)
        if markers
        else ""
    )
    figures = [figure for figure in session.get("figures") or [] if not figure.get("preview")]
    lines = [
        "Evidence-only fallback report",
        "The language-model narrative repeatedly failed evidence validation, so unsupported interpretation has been removed.",
        "Completed approved run(s): %s.%s" % (", ".join(completed) or "none", model_note),
        "Formal figure(s) generated from recorded result handles: %d." % len(figures),
    ]
    if gaps:
        lines.append(
            "This is a partial reproduction. %s %s not registered locally and %s not run; no cross-model agreement metric or solver-causality conclusion is available."
            % (", ".join(gaps), "is" if len(gaps) == 1 else "are", "was" if len(gaps) == 1 else "were")
        )
    else:
        lines.append("No additional scientific interpretation is published by this fallback.")
    return "\n\n".join(lines)


def planned_run_problem(session, model, spec):
    """Refuse successful-but-unplanned computations after formal approval."""
    project = session.get("research") or {}
    planned = (project.get("plan") or {}).get("runs") or []
    if any(run.get("model") == model and run.get("parameters") == spec for run in planned):
        return ""
    labels = [run.get("label") or run.get("id") for run in planned]
    return "This configuration is not one of the approved planned runs. Use exactly: %s." % ", ".join(labels)


def review_action(session, choice):
    """Apply one of the three persistent UI controls to the current review phase."""
    project = _require(session)
    phase = project["phase"]
    if choice == "primary":
        if phase == "plan_review":
            return approve_plan(session)
        if phase == "plan_approved":
            return pseudo_preview(session)
        if phase == "chart_selected":
            return approve_execution(session)
        if phase == "pseudo_preview":
            return _needs("Choose one chart option in Conversation before formal approval.", _public(project))
    if choice == "secondary":
        if phase == "pseudo_preview":
            return pseudo_preview(session)
        return _needs("Describe the requested revision in Conversation so the agent can update the plan.", _public(project))
    if choice == "pause":
        project["review_log"].append(
            {"version": project["plan_version"], "note": "user paused at %s" % phase, "changes": {}}
        )
        return _needs("Research remains paused at %s; no model call was authorized." % phase, _public(project))
    return _fail("No review action is available for phase %s." % phase)


def allow_model(session):
    return bool((session.get("research") or {}).get("phase") in ("approved", "completed"))


def _require(session):
    if not session.get("research"):
        raise ValueError("No LLM-authored research proposal exists yet.")
    return session["research"]


def _public(project):
    return {**project, "plan": {**project["plan"]}, "review_log": list(project["review_log"])}


def _ok(summary, data):
    return {"status": "success", "summary": summary, "data": data, "citations": [], "qc": None, "ui": None, "error": None}


def _needs(summary, data):
    return {"status": "needs_input", "summary": summary, "data": data, "citations": [], "qc": None, "ui": None, "error": summary}


def _fail(summary):
    return {"status": "terminal_error", "summary": summary, "data": {}, "citations": [], "qc": None, "ui": None, "error": summary}
