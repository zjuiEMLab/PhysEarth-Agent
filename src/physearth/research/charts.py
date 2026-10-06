"""Consistency between a chart and the runs that are supposed to feed it."""

import re

from physearth import plotting, registry
from physearth.corpus import knowledge


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
    run_ids = {run.get("id") for run in runs}
    for chart in charts:
        unknown = [name for name in chart.get("runs") or () if name not in run_ids]
        if unknown:
            problems.append(
                "%s names runs that are not planned: %s; use run ids from the plan's runs"
                % (chart["label"], ", ".join(unknown))
            )
        units = set()
        series = 0
        for y_name in _chart_y_names(chart):
            producers = [run["id"] for run in runs if _run_produces_chart(run, chart, y_name)]
            series += len(producers)
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
        if series > plotting.MAX_SERIES:
            # The renderer refuses it, so an approved plan with this chart can never
            # produce its figure; say so while the plan can still change.
            problems.append(
                "%s would draw %d series (each producing run times each y), more than the "
                "%d one chart can hold; give each chart its own run ids in its runs field, "
                "split it into separate charts, or plot fewer outputs"
                % (chart["label"], series, plotting.MAX_SERIES)
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
    chosen = chart.get("runs")
    if chosen and run.get("id") not in chosen:
        return False
    x_matches = chart.get("x") == "index" or spec.get("sweep_parameter") == chart.get("x")
    wanted = [y_name] if y_name else _chart_y_names(chart)
    return bool(x_matches and any(name in available for name in wanted))


def _normal_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _parameter_phrase(name):
    """How a question names a declared parameter: its name without the unit suffix."""
    tokens = str(name or "").split("_")
    while len(tokens) > 1 and (len(tokens[-1]) <= 3 or any(c.isdigit() for c in tokens[-1])):
        tokens.pop()
    return " ".join(tokens)


def _asked_values(question, runs):
    """Swept parameters the question asks a value of: at what X, an X range or threshold."""
    text = " ".join(str(question or "").lower().split())
    asked = []
    for name in _asked_sweep_axes(question, runs):
        bare = re.escape(_parameter_phrase(name)).replace(r"\ ", r"[- ]")
        named = r"(?:[a-z]+-)?" + bare
        if any(re.search(item, text) for item in (
            r"\bat\s+(?:what|which)\s+" + named + r"\b",
            r"\b" + bare + r"[- ](?:range|threshold)\b",
        )):
            asked.append(name)
    return asked


def _asked_sweep_axes(question, runs):
    """Sweepable parameters of the planned models that the question asks results along.

    Only the declared sweep_parameter values count, named the way the card names them
    without units (density_kg_m3 is "density"), and only in a phrase that asks for a
    dependence: against, versus, as X rises, changes with X, at what X, an X range. A
    parameter merely mentioned, or held at a value, is not an axis.
    """
    text = " ".join(str(question or "").lower().split())
    asked = []
    for model in dict.fromkeys(str(run.get("model") or "").strip() for run in runs or ()):
        entry = registry.get(model)
        if entry is None:
            continue
        declared = (entry.card.get("parameters") or {}).get("sweep_parameter") or {}
        for name in declared.get("enum") or ():
            phrase = _parameter_phrase(name)
            if name == "none" or len(phrase) < 5:
                continue
            bare = re.escape(phrase).replace(r"\ ", r"[- ]")
            named = r"(?:[a-z]+-)?" + bare
            # After "against" or "versus" a qualifier may precede it: incidence angle.
            qualified = r"(?:[a-z]+[- ])?" + bare
            patterns = (
                r"\bat\s+(?:what|which)\s+" + named + r"\b",
                r"\b(?:what|which)\s+" + named + r"[- ](?:range|threshold)\b",
                r"\b" + bare + r"[- ](?:range|sweep|dependence|threshold|axis)\b",
                r"\b(?:versus|vs\.?|against|function of|across the|over the|range of|sweep)\s+"
                r"(?:the\s+)?" + qualified + r"\b",
                r"\b(?:increasing|decreasing|varying|changing)\s+" + named + r"\b",
                r"\b(?:changes?|varies|vary|varying)\s+with\s+(?:the\s+)?" + named + r"\b",
                r"\b" + bare + r"\s+(?:increases|decreases|varies|changes|rises|falls)\b",
            )
            if name not in asked and any(re.search(item, text) for item in patterns):
                asked.append(name)
    return asked


def _question_coverage_problems(question, runs, charts, asked_question=""):
    """Reject polished-looking plans that omit an observable named in the question.

    It reads the user's own question as well: the plan's question is the model's
    restatement, and one run restated a density question into a frequency sweep, another
    a six-formulation comparison into a single Penman run.
    """
    question = "%s\n%s" % (question or "", asked_question or "")
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
    axes = {chart.get("x") for chart in required_charts}
    for name in _asked_sweep_axes(question, runs):
        if name not in axes:
            problems.append(
                "the question asks how results change with %s, but no required chart has "
                "x=%s; sweep %s in the compared runs and plot against it"
                % (_parameter_phrase(name), name, name)
            )
    if "dort" in text:
        has_stream_sweep = any(
            (run.get("parameters") or {}).get("sweep_parameter") == "dort_streams"
            for run in runs
        )
        if not has_stream_sweep:
            problems.append("DORT attribution requires a dort_streams convergence run")
    if any(word in text for word in ("formulation", "theory", "solver")):
        # Which parameter selects a model's formulation is the card's declaration, not a
        # name this check knows: SMRT's is electromagnetic_model, pyet's is method.
        formulations = set()
        for run in runs:
            entry = registry.get(run.get("model"))
            declared = (entry.card.get("formulation_parameters") or ()) if entry else ()
            choice = tuple((run.get("parameters") or {}).get(name) for name in declared)
            if any(value is not None for value in choice):
                formulations.add((run.get("model"), choice))
        if len(formulations) < 2 and ("compare" in text or "difference" in text or "versus" in text):
            problems.append(
                "formulation attribution requires at least two executable runs that differ in "
                "a formulation parameter the model card declares"
            )
    return problems


def _capability_gaps(question, session=None):
    """Reference models the question names that no registered card can answer.

    This used to scan a `model_names` list carried by each bundled paper -- a hardcoded
    alias table -- and report an entry when the question text happened to contain it. Two
    things were wrong with that. It fired on a string match against the question rather
    than on what the work actually needed, so reproducing figure 3 could raise figure 4's
    reference models; and it made a paper's card the authority on what is supported, when
    the registry is.

    Support is now decided where it is declared. The agent names the models the figure
    requires, `research_capability_check` resolves each against the registered cards, and
    a name no card can account for is reported as unavailable. Nothing is inferred from
    the question text.
    """
    return []
