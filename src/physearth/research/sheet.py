"""A plan as a conditions sheet and a run matrix, for a reviewer.

A plan stores every run as its own object, so the same fifteen or twenty parameters repeat in every
run and the source of each value is not on the page. This reads a plan and lays it out the way a
methods section would: what is the same in every run of a model, once, with where it came from; what
differs between runs, as a matrix; and what needs a decision.

It reads the plan only. Nothing here names a model, a parameter or a benchmark: the grouping is by
the model a run names, "the same" means equal across that model's runs, units come from the model
card, and sources come from the plan's own parameter mapping.
"""

import json

from physearth import registry

_SWEEP_FIELDS = ("sweep_parameter", "sweep_start", "sweep_stop", "sweep_points")

# How a recorded provenance class reads to a person. The last two tags are the ones a reviewer
# decides: a value the agent chose with no source, with or without a stated reason.
TAGS = {
    "paper_explicit": "extracted",
    "paper_inferred": "derived",
    "user_specified": "user",
    "backend_default": "default",
    "model_assumption": "assumed",
}
DECIDE = ("assumed", "guessed", "unlabelled")
_NOTE_CHARS = 140


def _same(left, right):
    if isinstance(left, (int, float)) and isinstance(right, (int, float)) and not isinstance(left, bool):
        return abs(left - right) <= 1e-12 * max(1.0, abs(left), abs(right))
    return left == right


def fmt(value):
    """A value the way a person reads it."""
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return "%.6g" % value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _params(run):
    return run.get("parameters") or run.get("resolved_parameters") or {}


def _tag_from_label(label):
    text = str(label or "").lower()
    if "#" in text or text.startswith(("paper", "figure", "section")):
        return "extracted"
    if "question" in text or "user" in text:
        return "user"
    if "default" in text:
        return "default"
    if "assum" in text or "guess" in text:
        return "assumed"
    return None


def _index_mapping(plan):
    index = {}
    for item in plan.get("parameter_mapping") or ():
        if isinstance(item, dict) and item.get("model_input"):
            index.setdefault((str(item.get("model") or ""), str(item["model_input"])), []).append(item)
    return index


def _source(plan, mapping, model, name, group_runs):
    """The tag, reference and note for one parameter of one model."""
    entries = mapping.get((model, name)) or mapping.get(("", name)) or []
    if entries:
        tags = []
        for item in entries:
            tag = TAGS.get(str(item.get("provenance_class") or ""))
            if tag == "assumed" and not str(item.get("rationale") or "").strip():
                tag = "guessed"
            tags.append(tag or "unlabelled")
        tag = tags[0] if len(set(tags)) == 1 else "mixed"
        first = entries[0]
        ref = next((str(item["evidence_ref"]) for item in entries if item.get("evidence_ref")), "")
        note = str(first.get("rationale") or "").strip()
        if not note and first.get("paper_value") not in (None, ""):
            note = "paper value: %s" % fmt(first.get("paper_value"))
        return tag, ref, note[:_NOTE_CHARS]
    if group_runs and all(name in (run.get("defaulted_parameters") or ()) for run in group_runs):
        return "default", "", "the model card's default"
    label = (plan.get("condition_provenance") or {}).get(name)
    tag = _tag_from_label(label)
    if tag:
        return tag, "", str(label)[:_NOTE_CHARS]
    return "unlabelled", "", ""


def _spec(model, name):
    entry = registry.get(model)
    return ((entry.card.get("parameters") or {}).get(name) or {}) if entry else {}


def _sweep_text(params):
    name = params.get("sweep_parameter")
    if name in (None, "", "none"):
        return ""
    points = params.get("sweep_points")
    return "%s %s to %s%s" % (
        name, fmt(params.get("sweep_start")), fmt(params.get("sweep_stop")),
        " (%s points)" % fmt(points) if points not in (None, "") else "",
    )


def _group(plan, mapping, charts, model, runs):
    all_params = [_params(run) for run in runs]
    names = []
    for params in all_params:
        for name in params:
            if name not in names:
                names.append(name)
    swept = {
        str(p.get("sweep_parameter")) for p in all_params if p.get("sweep_parameter") not in (None, "", "none")
    }
    conditions, varying = [], []
    for name in names:
        if name in _SWEEP_FIELDS or name in swept:
            continue
        values = [p.get(name) for p in all_params]
        if all(_same(value, values[0]) for value in values):
            tag, ref, note = _source(plan, mapping, model, name, runs)
            spec = _spec(model, name)
            conditions.append({
                "name": name, "value": values[0], "unit": spec.get("unit") or "",
                "tag": tag, "ref": ref, "note": note,
            })
        else:
            varying.append(name)
    sweeps = {_sweep_text(p) for p in all_params}
    sweep = sweeps.pop() if len(sweeps) == 1 else None
    columns = []
    for name in varying:
        tag, ref, note = _source(plan, mapping, model, name, runs)
        columns.append({"name": name, "unit": _spec(model, name).get("unit") or "", "tag": tag, "ref": ref})
    rows = []
    from physearth.research.charts import _run_produces_chart

    for run in runs:
        params = _params(run)
        rows.append({
            "id": run.get("id") or "",
            "label": run.get("label") or "",
            "stage": run.get("stage") or "",
            "values": {name: params.get(name) for name in varying},
            "sweep": "" if sweep is not None else _sweep_text(params),
            "feeds": [c.get("id") for c in charts if _run_produces_chart(run, c)],
        })
    entry = registry.get(model)
    return {
        "model": model,
        "version": (entry.card.get("version") if entry else "") or "",
        "conditions": conditions,
        "sweep": sweep or "",
        "sweep_varies": sweep is None,
        "columns": columns,
        "runs": rows,
    }


def build(plan):
    """The sheet for a plan: one group per model, the decisions, and the charts."""
    plan = plan or {}
    runs = [run for run in plan.get("runs") or () if isinstance(run, dict)]
    charts = [chart for chart in plan.get("charts") or () if isinstance(chart, dict)]
    mapping = _index_mapping(plan)
    models = list(dict.fromkeys(str(run.get("model") or "") for run in runs))
    groups = [
        _group(plan, mapping, charts, model, [run for run in runs if str(run.get("model") or "") == model])
        for model in models
    ]
    decisions = []
    for group in groups:
        for item in group["conditions"]:
            if item["tag"] in DECIDE:
                decisions.append({"model": group["model"], **item})
        for column in group["columns"]:
            if column["tag"] in DECIDE:
                decisions.append({"model": group["model"], "value": "varies by run", **column, "note": ""})
    return {
        "groups": groups,
        "decisions": decisions,
        "charts": [
            {"id": c.get("id"), "label": c.get("label"), "x": c.get("x"), "ys": c.get("ys") or [c.get("y")],
             "required": c.get("required", True),
             "runs": [r["id"] for g in groups for r in g["runs"] if c.get("id") in r["feeds"]]}
            for c in charts
        ],
        "run_count": len(runs),
    }
