"""The gates: approve a plan, preview it, choose a chart, approve execution, complete."""

import math
import re

from physearth import plotting
from physearth.research.charts import _chart_y_names, _run_produces_chart
from physearth.research.common import _fail, _needs, _ok, _public, _require
from physearth.research.execution import execution_gaps


def approve_plan(session):
    project = _require(session)
    if project["phase"] != "plan_review":
        return _fail("The plan cannot be approved in phase %s." % project["phase"])
    resource_gate = (project.get("plan") or {}).get("resource_gate")
    if resource_gate:
        return _needs(
            "The plan is structurally valid but cannot be approved until its research guideline, model instructions, and required paper evidence are read.",
            {**_public(project), "resource_gate": resource_gate},
        )
    project["phase"] = "plan_approved"
    return _needs(
        "Plan approved for preview only. No physical model run or scientific figure is approved yet; generate the display-only pseudo-data preview next.",
        _public(project),
    )


def pseudo_preview(session):
    """Generate deterministic display-only data from the proposed axes, never physics."""
    project = _require(session)
    if project["phase"] not in ("plan_approved", "pseudo_preview"):
        return _needs("Approve the plan before requesting pseudo-data.", _public(project))
    plan = project["plan"]
    project["preview_version"] = int(project.get("preview_version", 0)) + 1
    preview_version = project["preview_version"]
    preview_layouts = {}
    # Replace this project's old previews rather than accumulating stale layouts.  These
    # curves are deliberately tagged and labelled as pseudo-data; completion never counts
    # them because they contain no real result handles.
    session["figures"] = [figure for figure in session.get("figures") or [] if not figure.get("research_preview")]
    chart_axes = {chart["x"] for chart in plan["charts"]}
    for chart_index, chart in enumerate(plan["charts"]):
        producers = [run for run in plan["runs"] if _run_produces_chart(run, chart)]
        source_spec = (producers[0].get("parameters") or {}) if producers else {}
        plan_parameters = plan.get("parameters") or {}
        proposed_bounds = _preview_bounds_or_none(
            plan_parameters,
            [chart],
            allow_generic=(
                len(chart_axes) == 1
                or plan_parameters.get("sweep_parameter") == chart["x"]
            ),
        )
        if proposed_bounds is not None:
            start, stop = proposed_bounds
            count = int((plan.get("parameters") or {}).get("sweep_points", 8) or 8)
        elif source_spec.get("sweep_parameter") == chart["x"]:
            start = float(source_spec["sweep_start"])
            stop = float(source_spec["sweep_stop"])
            count = int(source_spec.get("sweep_points") or 8)
        else:
            start, stop = _preview_bounds(plan.get("parameters") or {}, [chart])
            count = int((plan.get("parameters") or {}).get("sweep_points", 8) or 8)
        count = max(5, min(20, count))
        xs = [start + (stop - start) * index / (count - 1) for index in range(count)]
        preview_series = []
        for producer_index, run in enumerate(producers or [{"id": "layout", "label": chart["label"]}]):
            for y_index, y_name in enumerate(_chart_y_names(chart)):
                if producers and not _run_produces_chart(run, chart, y_name):
                    continue
                ys = []
                for index in range(count):
                    fraction = index / max(1, count - 1)
                    ys.append(
                        round(
                            0.2 + 0.55 * fraction
                            + 0.11 * producer_index + 0.07 * y_index
                            + 0.025 * math.sin(index + preview_version + chart_index),
                            8,
                        )
                    )
                preview_series.append(
                    {
                        "handle": "",
                        "label": "%s · %s" % (run.get("label"), y_name),
                        "x": xs,
                        "y": ys,
                        "x_name": chart["x"],
                        "y_name": y_name,
                        "source": "model_run",
                        "origin": "pseudo-data preview v%03d" % preview_version,
                        "units": {},
                    }
                )
        preview_layouts[chart["id"]] = preview_series
        figure = plotting.render(
            {
                "title": "%s — PSEUDO-DATA PREVIEW" % chart["label"],
                "kind": chart["kind"],
                "x_label": chart.get("x_label") or None,
                "y_label": chart.get("y_label") or None,
            },
            preview_series,
            preview=False,
        )
        figure["preview"] = True
        figure["research_preview"] = True
        session["figures"].append(figure)
    first_series = next(iter(preview_layouts.values()), [])
    points = []
    if first_series:
        for index, x_value in enumerate(first_series[0]["x"]):
            row = {first_series[0]["x_name"]: round(x_value, 8)}
            for series_index, item in enumerate(first_series):
                row["%s_%s" % (series_index + 1, item["y_name"])] = item["y"][index]
            points.append(row)
    project["pseudo"] = {
        "label": "PSEUDO-DATA - layout demonstration only - preview v%03d" % preview_version,
        "points": points,
    }
    session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1
    project["phase"] = "pseudo_preview"
    required_ids = [chart["id"] for chart in plan["charts"] if chart.get("required", True)]
    project["selected_charts"] = required_ids
    project["selected_chart"] = next(
        (dict(chart) for chart in plan["charts"] if chart["id"] in required_ids),
        None,
    )
    return _needs(
        "Pseudo-data preview v%03d is ready for layout review only. It is not model output and must not support a scientific conclusion. Confirm the figure package, or revise the plan in chat."
        % preview_version,
        _public(project),
    )


def _preview_bounds(parameters, charts):
    """Read common generic range forms without embedding any domain/question template."""
    return _preview_bounds_or_none(parameters, charts) or (0.0, 1.0)


def _preview_bounds_or_none(parameters, charts, allow_generic=True):
    """Return a declared range for these chart axes, or ``None`` when none exists."""
    if allow_generic and "sweep_start" in parameters and "sweep_stop" in parameters:
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
    return None


def choose_chart(session, chart_id):
    project = _require(session)
    if project["phase"] != "pseudo_preview":
        return _needs("Generate the pseudo-data preview before selecting a chart.", _public(project))
    chart = next((item for item in project["plan"]["charts"] if item["id"] == chart_id), None)
    if chart is None:
        return _fail("Unknown chart option %r." % chart_id)
    selected = list(project.get("selected_charts") or [])
    if chart.get("required", True):
        if chart_id not in selected:
            selected.append(chart_id)
        action = "kept required"
    elif chart_id in selected:
        selected.remove(chart_id)
        action = "deselected"
    else:
        selected.append(chart_id)
        action = "selected"
    project["selected_charts"] = selected
    project["selected_chart"] = next(
        (dict(item) for item in project["plan"]["charts"] if item["id"] in selected),
        None,
    )
    project["review_log"].append(
        {
            "version": project["plan_version"],
            "note": "user %s chart %s" % (action, chart_id),
            "changes": {"selected_charts": list(selected)},
        }
    )
    if chart.get("required", True):
        project["phase"] = "chart_selected"
        _clear_previews(session)
        return _needs(
            "%d required chart(s) confirmed. The pseudo-data preview was discarded; ask the user to approve formal execution of the real runs."
            % len(project["selected_charts"]),
            _public(project),
        )
    return _needs(
        "Chart package updated. Confirm the selected figure set before formal execution.",
        _public(project),
    )


def confirm_charts(session):
    project = _require(session)
    if project["phase"] != "pseudo_preview":
        return _needs("Generate the pseudo-data preview before confirming charts.", _public(project))
    if not project.get("selected_charts"):
        return _needs("Select at least one chart before continuing.", _public(project))
    project["phase"] = "chart_selected"
    _clear_previews(session)
    return _needs(
        "%d chart(s) confirmed. The pseudo-data preview was discarded; ask the user to approve formal execution."
        % len(project["selected_charts"]),
        _public(project),
    )


def approve_execution(session):
    project = _require(session)
    if project["phase"] in ("approved", "completed"):
        return _ok(
            "Formal execution was already approved for the current plan; no second model continuation was scheduled.",
            _public(project),
        )
    if project["phase"] != "chart_selected":
        return _needs("Select a chart after the pseudo-data preview first.", _public(project))
    project["phase"] = "approved"
    project["execution_resume_sent"] = False
    _clear_previews(session)
    return _ok(
        "Formal execution approved. The agent may now call the registered physical models and must build the selected figures from their real outputs.",
        _public(project),
    )


def _clear_previews(session):
    """Remove demonstration figures as soon as the human confirms the figure package."""
    before = len(session.get("figures") or [])
    session["figures"] = [
        figure for figure in session.get("figures") or []
        if not figure.get("research_preview") and not figure.get("preview")
    ]
    if len(session["figures"]) != before:
        session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1


def complete(session):
    project = _require(session)
    gaps = execution_gaps(session)
    if gaps["missing_runs"]:
        return _needs(
            "The workflow cannot complete; planned runs still missing: %s."
            % ", ".join(gaps["missing_runs"]),
            _public(project),
        )
    if gaps.get("target_gaps"):
        return _needs(
            "The workflow cannot complete; reproduction targets still lack covered planned runs or reviewed charts: %s."
            % ", ".join(item.get("target_id") or "target" for item in gaps["target_gaps"]),
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
