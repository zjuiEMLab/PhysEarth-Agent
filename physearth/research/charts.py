"""Consistency between a chart and the runs that are supposed to feed it."""

import re

from physearth import knowledge
from physearth.models import registry


def _figure_satisfies(figure, expected):
    """A planned chart is one figure containing every exact handle/x/y series."""
    return bool(expected) and all(
        _figure_has_series(figure, wanted)
        for wanted in expected
    )


def _figure_has_series(figure, wanted):
    return any(
        item.get("handle") == wanted.get("handle")
        and item.get("x") == wanted.get("x")
        and item.get("y") == wanted.get("y")
        for item in figure.get("series") or []
    )


def _run_can_output(run, y_name):
    entry = registry.get(run.get("model"))
    if entry is None:
        return False
    spec = run.get("parameters") or {}
    groups = entry.card.get("output_groups") or {}
    available = groups.get(spec.get("output"), list(entry.card.get("outputs", {})))
    return y_name in available


def _output_dependency_problems(charts, runs):
    problems = []
    coefficient_outputs = {
        "ks_per_m", "ka_per_m", "effective_permittivity", "single_scattering_albedo"
    }
    for chart in charts:
        if chart.get("x") != "dort_streams":
            continue
        coefficient_ys = coefficient_outputs.intersection(_chart_y_names(chart))
        if not coefficient_ys:
            continue
        for run in runs:
            spec = run.get("parameters") or {}
            if spec.get("output") == "coefficients" and spec.get("sweep_parameter") == "dort_streams":
                problems.append(
                    "%s sweeps DORT streams for %s, but coefficients are computed before the DORT solver"
                    % (run.get("label"), ", ".join(sorted(coefficient_ys)))
                )
    return problems


def _repair_sampling_density(charts, runs, minimum_points=8):
    """Densify an under-resolved trend before the human sees and approves the plan."""
    repairs = []
    repaired_ids = set()
    for chart in charts:
        if chart.get("kind", "line") not in ("line", "line+markers"):
            continue
        for run in runs:
            spec = run.get("parameters") or {}
            if run.get("id") in repaired_ids or not _run_produces_chart(run, chart):
                continue
            points = int(spec.get("sweep_points") or 0)
            if spec.get("sweep_parameter") in (None, "none") or points >= 6:
                continue
            spec["sweep_points"] = minimum_points
            repaired_ids.add(run.get("id"))
            repairs.append(
                {
                    "run_id": run.get("id"),
                    "field": "sweep_points",
                    "from": points,
                    "to": minimum_points,
                    "reason": "trend figures require at least 6 distinct samples",
                }
            )
    return repairs


def _repair_chart_axes(charts, runs):
    """Repair a categorical configuration name when one unambiguous numeric sweep exists.

    This changes only presentation metadata. It never changes a physical-model parameter,
    model combination, sampling range, or requested output, so the human still reviews the
    exact computation while avoidable schema mistakes do not consume more LLM calls.
    """
    repairs = []
    categorical = {"electromagnetic_model", "coefficient_type", "configuration", "model", "theory"}
    for chart in charts:
        if chart.get("x") not in categorical:
            continue
        axes_by_output = []
        for y_name in _chart_y_names(chart):
            axes = {
                (run.get("parameters") or {}).get("sweep_parameter")
                for run in runs
                if _run_can_output(run, y_name)
                and (run.get("parameters") or {}).get("sweep_parameter") not in (None, "none")
            }
            if axes:
                axes_by_output.append(axes)
        if not axes_by_output:
            continue
        common = set.intersection(*axes_by_output)
        if len(common) != 1:
            continue
        old_x = chart["x"]
        new_x = next(iter(common))
        chart["x"] = new_x
        if not chart.get("x_label") or old_x.replace("_", " ") in chart["x_label"].lower():
            chart["x_label"] = ""
        repairs.append(
            {
                "chart_id": chart.get("id"),
                "field": "x",
                "from": old_x,
                "to": new_x,
                "reason": "all compatible planned runs share this numeric sweep_parameter",
            }
        )
    return repairs


def _repair_required_companion_outputs(question, charts, runs):
    """Add a declared same-unit companion output omitted from presentation metadata.

    SMRT ``output=tb`` already computes both polarizations. When a question asks for
    brightness temperature/polarization but the planner puts only ``tb_v`` on a required
    chart, adding ``tb_h`` changes neither the experiment nor its cost. Rejecting the whole
    plan and asking the LLM to reproduce a large JSON object is both fragile and wasteful.
    """
    text = str(question or "").lower()
    if not ("brightness temperature" in text or re.search(r"\btb\b", text)):
        return []
    repairs = []
    for chart in charts:
        if not chart.get("required", True) or "tb_v" not in _chart_y_names(chart):
            continue
        if "tb_h" in _chart_y_names(chart):
            continue
        if not any(_run_produces_chart(run, chart, "tb_h") for run in runs):
            continue
        before = list(chart.get("ys") or [chart.get("y")])
        chart["ys"] = before + ["tb_h"]
        repairs.append(
            {
                "chart_id": chart.get("id"),
                "field": "ys",
                "from": before,
                "to": list(chart["ys"]),
                "reason": "the planned tb runs already produce both polarizations requested by the question",
            }
        )
        break
    return repairs


def _validate_chart_runs(charts, runs):
    """Validate figure producibility without confusing computation with presentation.

    Main/sensitivity/robustness runs carry scientific curves and must contribute to a
    required figure. A baseline may instead provide a scalar inversion target, and a
    diagnostic may only check solver convergence or numerical stability. Those auxiliary
    runs remain mandatory in ``execution_gaps`` but need not share a main plot's sweep axis.
    """
    problems = []
    for chart in charts:
        units = set()
        for y_name in _chart_y_names(chart):
            producers = [run["id"] for run in runs if _run_produces_chart(run, chart, y_name)]
            if not producers:
                problems.append(
                    "no planned run produces %s over x=%s" % (y_name, chart["x"])
                )
            for run in runs:
                entry = registry.get(run["model"])
                if entry and _run_produces_chart(run, chart, y_name):
                    unit = (entry.card.get("outputs", {}).get(y_name) or {}).get("unit")
                    if unit:
                        units.add(unit)
        if len(units) > 1:
            problems.append(
                "%s mixes incompatible y-axis units: %s; split it into separate charts"
                % (chart["label"], ", ".join(sorted(units)))
            )
    for run in runs:
        stage = str(run.get("stage") or "main").strip().lower()
        auxiliary = stage in ("baseline", "diagnostic")
        if not any(_run_produces_chart(run, chart) for chart in charts):
            if auxiliary:
                continue
            problems.append("%s contributes to none of the proposed charts" % run["label"])
        elif not any(
            chart.get("required", True) and _run_produces_chart(run, chart)
            for chart in charts
        ):
            if auxiliary:
                continue
            problems.append(
                "%s contributes only to optional layouts; add a required result or diagnostic chart"
                % run["label"]
            )
    return problems


def _chart_y_names(chart):
    return list(chart.get("ys") or ([chart.get("y")] if chart.get("y") else []))


def _run_produces_chart(run, chart, y_name=None):
    """Whether one approved run can supply the selected chart's exact axes."""
    entry = registry.get(run.get("model"))
    if entry is None:
        return False
    spec = run.get("parameters") or {}
    groups = entry.card.get("output_groups") or {}
    available = groups.get(spec.get("output"), list(entry.card.get("outputs", {})))
    x_matches = chart.get("x") == "index" or spec.get("sweep_parameter") == chart.get("x")
    wanted = [y_name] if y_name else _chart_y_names(chart)
    return bool(x_matches and any(name in available for name in wanted))


def _normal_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _question_coverage_problems(question, runs, charts):
    """Reject polished-looking plans that omit an observable named in the question."""
    text = str(question or "").lower()
    required_charts = [chart for chart in charts if chart.get("required", True)]
    outputs = {
        name
        for chart in required_charts
        for name in _chart_y_names(chart)
    }
    problems = []
    asks_tb = "brightness temperature" in text or re.search(r"\btb\b", text)
    asks_coefficients = "coefficient" in text
    asks_absorption = "absorption" in text
    asks_scattering = "scattering coefficient" in text
    asks_backscatter = "backscatter" in text or "sigma" in text
    if asks_tb:
        missing = {"tb_v", "tb_h"} - outputs
        if missing:
            problems.append("required brightness-temperature chart is missing %s" % ", ".join(sorted(missing)))
    if asks_coefficients and not outputs.intersection(
        {"ks_per_m", "ka_per_m", "effective_permittivity", "single_scattering_albedo"}
    ):
        problems.append("no required electromagnetic-coefficient chart")
    if asks_absorption and "ka_per_m" not in outputs:
        problems.append("absorption attribution requires ka_per_m")
    if asks_scattering and "ks_per_m" not in outputs:
        problems.append("scattering attribution requires ks_per_m")
    if asks_backscatter and not outputs.intersection({"sigma_vv_db", "sigma_hh_db", "sigma_hv_db"}):
        problems.append("no required backscatter chart")
    if "dort" in text:
        has_stream_sweep = any(
            (run.get("parameters") or {}).get("sweep_parameter") == "dort_streams"
            for run in runs
        )
        if not has_stream_sweep:
            problems.append("DORT attribution requires a dort_streams convergence run")
    if any(word in text for word in ("formulation", "theory", "solver")):
        configurations = {
            (
                (run.get("parameters") or {}).get("electromagnetic_model"),
                (run.get("parameters") or {}).get("output"),
            )
            for run in runs
        }
        electromagnetic_models = {item[0] for item in configurations if item[0]}
        if len(electromagnetic_models) < 2 and ("compare" in text or "difference" in text or "versus" in text):
            problems.append("formulation attribution requires at least two executable electromagnetic configurations")
    return problems


def _capability_gaps(question, session=None):
    """Named literature models that have no executable registry entry."""
    text = _normal_name(question)
    registered = {_normal_name(name) for name in registry.names(session=session)}
    gaps = []
    for item in knowledge.catalogue():
        card = knowledge.card(item["slug"]) or {}
        for alias in card.get("model_names") or []:
            normalized = _normal_name(alias)
            if normalized and normalized in text and normalized not in registered:
                gaps.append(str(alias))
    return sorted(set(gaps))
