"""Drawing a chart from a declarative specification, and reviewing what came out."""

from pathlib import Path

from physearth import config, plotting, research
from physearth.tools.common import _fail, _ok


def _temporary_figure_dir(session):
    if not session or not session.get("ephemeral"):
        return None
    path = session.get("temporary_figure_dir")
    if not path:
        path = str(
            config.state_dir()
            / "evaluation"
            / str(session.get("id"))
            / "figures"
        )
        Path(path).mkdir(parents=True, exist_ok=True)
        session["temporary_figure_dir"] = path
    return path


def plot(
    series=None,
    kind="line",
    title=None,
    subtitle=None,
    x_label=None,
    y_label=None,
    dry_run=False,
    metrics=None,
    _owner=None,
    _session=None,
):
    spec = {
        "series": series or [],
        "kind": kind,
        "title": title,
        "subtitle": subtitle,
        "x_label": x_label,
        "y_label": y_label,
        "owner": _owner,
    }
    resolved, problems = (
        plotting.outline(spec) if dry_run else plotting.resolve(spec, _owner)
    )
    if problems:
        return {
            "status": "needs_input",
            "summary": "The chart was rejected: %d problem(s)." % len(problems),
            "data": {"rejected_spec": spec, "problems": problems},
            "citations": [],
            "qc": None,
            "ui": None,
            "error": "; ".join(problems),
        }
    try:
        figure = plotting.render(
            spec,
            resolved,
            preview=bool(dry_run),
            temporary_dir=_temporary_figure_dir(_session),
        )
    except Exception as exc:
        return _fail("The chart could not be drawn: %s: %s" % (type(exc).__name__, exc))

    described = [
        {
            "label": s["label"],
            "source": s["source"],
            "origin": s["origin"],
            "n_points": len(s["x"]),
            "x": s["x_name"],
            "y": s["y_name"],
            "y_unit": (s.get("units") or {}).get(s["y_name"], ""),
        }
        for s in resolved
    ]

    if dry_run:
        return _ok(
            "Preview only: a %s chart of %s against %s with %d series, drawn with its axes, "
            "units and legend and no data. Check it is the chart you want, then run what it "
            "needs and call plot again without dry_run."
            % (kind, resolved[0]["y_name"], resolved[0]["x_name"], len(resolved)),
            {"preview": True, "series": described},
            ui={"figure": figure},
        )

    data = {"preview": False, "series": described}
    summary = "Drew a %s chart with %d series over %d point(s). It is on screen; do not " "restate its values." % (
        figure["kind"],
        len(resolved),
        sum(len(s["x"]) for s in resolved),
    )
    if metrics is not None:
        values, refusals = plotting.agreement(resolved, metrics)
        if refusals:
            data["agreement_refused"] = refusals
            summary += (
                " Agreement statistics were refused: %s The chart is still on screen; report "
                "the two curves separately and say why they cannot be differenced."
                % " ".join(refusals)
            )
        else:
            data["agreement"] = values
            figure["agreement"] = values
            summary += " Agreement over %d overlapping point(s): %s." % (
                values["n_points"],
                ", ".join(
                    "%s %s" % (name, values[name])
                    for name in plotting.METRICS
                    if values.get(name) is not None
                ),
            )
    return _ok(summary, data, ui={"figure": figure})


def plot_planned_chart(chart_id, action="render", _owner=None, _session=None):
    if action == "review":
        return _review_planned_figure(chart_id, _owner=_owner, _session=_session)
    if _session is None or not _session.get("research_required"):
        return _fail("plot_planned_chart requires an active reviewed research session.")
    if not research.allow_model(_session):
        return _fail("Formal execution has not been approved by the user.")
    requirement = research.planned_chart_series(_session, chart_id)
    if requirement is None:
        ids = research.planned_chart_ids(_session)
        return {
            "status": "needs_input",
            "summary": "Unknown or unselected chart_id %r. Selected chart IDs: %s."
            % (chart_id, ", ".join(ids)),
            "data": {"chart_id": chart_id, "selected_chart_ids": ids},
            "citations": [], "qc": None, "ui": None,
            "error": "unknown planned chart_id",
        }
    if not requirement["series"]:
        return {
            "status": "needs_input",
            "summary": "Chart %s has no successful compatible planned runs yet." % chart_id,
            "data": {
                "chart_id": chart_id,
                "missing_run_ids": research.planned_run_ids(_session, missing_only=True),
            },
            "citations": [], "qc": None, "ui": None,
            "error": "planned chart data missing",
        }
    chart = requirement["chart"]
    series_specs = [
        {
            "handle": item["handle"],
            "x": item["x"],
            "y": item["y"],
            "label": item["label"],
        }
        for item in requirement["series"]
    ]
    planned_runs = [
        research.planned_run(_session, run_id)
        for run_id in sorted({item["run_id"] for item in requirement["series"]})
    ]
    planned_runs = [run for run in planned_runs if run]
    common = {}
    if planned_runs:
        first_spec = planned_runs[0].get("parameters") or {}
        for key, value in first_spec.items():
            if key in (
                "output", "electromagnetic_model", "sweep_parameter", "sweep_start",
                "sweep_stop", "sweep_points", chart.get("x"), "radius_m", "stickiness",
            ):
                continue
            if all((run.get("parameters") or {}).get(key) == value for run in planned_runs[1:]):
                common[key] = value
    subtitle = _condition_subtitle(common)
    selected_ids = research.planned_chart_ids(_session)
    figure_number = selected_ids.index(chart_id) + 1
    result = plot(
        series=series_specs,
        kind=chart.get("kind", "line"),
        title="Figure %d. %s" % (figure_number, chart.get("label")),
        subtitle=subtitle,
        x_label=chart.get("x_label") or None,
        y_label=chart.get("y_label") or None,
        _owner=_owner,
    )
    if result.get("status") == "success":
        resolved, comparison_problems = plotting.resolve({"series": series_specs}, _owner)
        comparisons = []
        if not comparison_problems:
            for y_name in dict.fromkeys(item["y_name"] for item in resolved):
                group = [item for item in resolved if item["y_name"] == y_name]
                if len(group) < 2:
                    continue
                baseline = group[0]
                for candidate in group[1:]:
                    values, refusals = plotting.agreement(
                        [candidate, baseline], ["bias", "rmse", "mae", "r"]
                    )
                    if not refusals:
                        comparisons.append({"quantity": y_name, **values})
        result["data"]["planned_chart_id"] = chart_id
        result["data"]["reproduction_target_ids"] = research.target_ids_for_chart(_session, chart_id)
        result["data"]["comparisons"] = comparisons
        result["summary"] = "Approved chart %s: %s" % (chart_id, result["summary"])
        if result.get("ui") and result["ui"].get("figure"):
            result["ui"]["figure"]["planned_chart_id"] = chart_id
            result["ui"]["figure"]["reproduction_target_ids"] = research.target_ids_for_chart(_session, chart_id)
            result["ui"]["figure"]["purpose"] = chart.get("purpose", "result")
            result["ui"]["figure"]["comparisons"] = comparisons
            result["ui"]["figure"]["figure_number"] = figure_number
            result["ui"]["figure"]["quality_review"] = {"reviewed": False, "passed": False}
    return result


def _review_planned_figure(chart_id, _owner=None, _session=None):
    if _session is None or not _session.get("research_required"):
        return _fail("Figure review requires an active reviewed research session.")
    requirement = research.planned_chart_series(_session, chart_id)
    if requirement is None:
        return _fail("Unknown or unselected planned chart_id %r." % chart_id)
    current = next(
        (
            figure for figure in reversed(_session.get("figures") or [])
            if not figure.get("preview") and figure.get("planned_chart_id") == chart_id
        ),
        None,
    )
    if current is None:
        return {
            "status": "needs_input",
            "summary": "Plot planned chart %s before reviewing it." % chart_id,
            "data": {"chart_id": chart_id}, "citations": [], "qc": None, "ui": None,
            "error": "formal figure missing",
        }
    series_specs = [
        {"handle": item["handle"], "x": item["x"], "y": item["y"], "label": item["label"]}
        for item in requirement["series"]
    ]
    resolved, problems = plotting.resolve({"series": series_specs}, _owner)
    if problems:
        return _fail("Figure quality review could not resolve its data: %s" % "; ".join(problems))
    spec = {
        "kind": requirement["chart"].get("kind", "line"),
        "title": current.get("title"),
        "subtitle": current.get("subtitle"),
        "x_label": current.get("x_label"),
        "y_label": current.get("y_label"),
    }
    review = plotting.review_quality(spec, resolved, current)
    reviewed_figure = dict(current)
    redrawn = False
    if review["redraw_reasons"] and not review["issues"]:
        reviewed_figure = plotting.render(
            {**spec, "quality_profile": "publication"},
            resolved,
            preview=False,
            temporary_dir=_temporary_figure_dir(_session),
        )
        reviewed_figure.update(
            planned_chart_id=chart_id,
            purpose=current.get("purpose", "result"),
            comparisons=current.get("comparisons") or [],
            figure_number=current.get("figure_number"),
        )
        redrawn = True
        review = plotting.review_quality(spec, resolved, reviewed_figure)
    review["redrawn"] = redrawn
    reviewed_figure["quality_review"] = review
    action = "redrawn with a publication layout and passed" if redrawn and review["passed"] else (
        "passed" if review["passed"] else "failed"
    )
    return _ok(
        "Figure %s quality review %s. %d series; point counts %s.%s"
        % (
            reviewed_figure.get("figure_number") or "?",
            action,
            review["n_series"],
            review["point_counts"],
            " Warnings: %s." % "; ".join(review["warnings"]) if review["warnings"] else "",
        ),
        {"chart_id": chart_id, "quality_review": review},
        ui={"figure": reviewed_figure},
    )


def _condition_subtitle(values):
    labels = {
        "frequency_ghz": ("f", "GHz", 1.0),
        "angle_deg": ("angle", "°", 1.0),
        "density_kg_m3": ("density", "kg m⁻³", 1.0),
        "temperature_k": ("T", "K", 1.0),
        "thickness_m": ("thickness", "m", 1.0),
        "corr_length_m": ("corr. length", "µm", 1e6),
        "dort_streams": ("DORT", "streams", 1.0),
    }
    parts = []
    for key in labels:
        if key not in values:
            continue
        label, unit, scale = labels[key]
        value = values[key] * scale if isinstance(values[key], (int, float)) else values[key]
        shown = "%g" % value if isinstance(value, (int, float)) else str(value)
        parts.append("%s %s %s" % (label, shown, unit))
    if values.get("microstructure_model"):
        parts.append(str(values["microstructure_model"]).replace("_", " "))
    return " · ".join(parts)
