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
_NOTE_CHARS = 400


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


# How a unit is spelled inside a parameter name, when that differs from how the card writes
# it: "latitude_deg" for degree, "temperature_c" for degC, "radiation_mj_m2_day" for d-1.
_UNIT_ALIASES = {"degree": ("deg",), "degc": ("c",), "d": ("day",), "percent": ("pct",)}
_UNIT_SHOWN = {"none": "", "count": "", "degree": "°", "percent": "%"}


def _unit_words(unit):
    words = set()
    for token in str(unit or "").lower().replace("/", " ").split():
        for form in (token, token.replace("-", ""), "".join(ch for ch in token if ch.isalpha())):
            words.add(form)
            words.update(_UNIT_ALIASES.get(form, ()))
    return words


def label(name, spec=None):
    """A parameter as a person names it: the card's label, or its name without its unit.

    Only words of the parameter's own declared unit are dropped, so "temperature_k" in K
    reads "temperature" while "coefficient_c", which has no unit, keeps its letter.
    """
    spec = spec or {}
    if str(spec.get("label") or "").strip():
        return str(spec["label"]).strip()
    words = str(name or "").split("_")
    unit_words = _unit_words(spec.get("unit"))
    while len(words) > 1 and words[-1].lower() in unit_words:
        words.pop()
    # "ks_per_m" in m-1: the unit went, so its "per" goes too.
    if len(words) > 1 and words[-1].lower() == "per" and words != str(name).split("_"):
        words.pop()
    return " ".join(words)


def unit_text(unit):
    """A unit as it is printed after a value; empty for none, counts and relative units."""
    unit = str(unit or "").strip()
    if unit.lower() in _UNIT_SHOWN:
        return _UNIT_SHOWN[unit.lower()]
    if unit.lower().startswith("same as"):
        return ""
    return unit


def with_unit(value, unit):
    """`12 m`, `55°`, `on` -- a value with the unit it was declared in."""
    shown, unit = fmt(value), unit_text(unit)
    if not unit or shown == "-" or isinstance(value, (str, bool)):
        return shown
    return "%s%s%s" % (shown, "" if unit in ("°", "%") else " ", unit)


def about(spec):
    """The card's description, cut to its first sentence."""
    text = " ".join(str((spec or {}).get("description") or "").split())
    if not text:
        return ""
    end = text.find(". ")
    text = text if end < 0 else text[: end + 1]
    return text if len(text) <= 120 else text[:119].rstrip() + "…"


def named(name, spec=None):
    """`depth (depth_m)`, or just the name when it already reads as words."""
    human = label(name, spec)
    return human if human == str(name) else "%s (%s)" % (human, name)


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
        return tag, ref, note if len(note) <= _NOTE_CHARS else note[: _NOTE_CHARS - 1].rstrip() + "…"
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


def _sweep_text(params, model=""):
    name = params.get("sweep_parameter")
    if name in (None, "", "none"):
        return ""
    points = params.get("sweep_points")
    spec = _spec(model, name) if model else {}
    return "%s from %s to %s%s" % (
        named(name, spec), fmt(params.get("sweep_start")), with_unit(params.get("sweep_stop"), spec.get("unit")),
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
                "label": named(name, spec), "about": about(spec),
                "shown": with_unit(values[0], spec.get("unit")),
            })
        else:
            varying.append(name)
    sweeps = {_sweep_text(p, model) for p in all_params}
    sweep = sweeps.pop() if len(sweeps) == 1 else None
    columns = []
    for name in varying:
        tag, ref, note = _source(plan, mapping, model, name, runs)
        spec = _spec(model, name)
        columns.append({
            "name": name, "unit": spec.get("unit") or "", "tag": tag, "ref": ref,
            "label": label(name, spec), "about": about(spec), "note": note,
        })
    rows = []
    from physearth.research.charts import _run_produces_chart

    for run in runs:
        params = _params(run)
        rows.append({
            "id": run.get("id") or "",
            "label": run.get("label") or "",
            "stage": run.get("stage") or "",
            "values": {name: params.get(name) for name in varying},
            "sweep": "" if sweep is not None else _sweep_text(params, model),
            "feeds": [c.get("id") for c in charts if _run_produces_chart(run, c)],
        })
    entry = registry.get(model)
    chosen = next(
        (item for item in plan.get("selected_models") or ()
         if isinstance(item, dict) and str(item.get("model") or "") == model),
        {},
    )
    return {
        "model": model,
        "version": (entry.card.get("version") if entry else "") or "",
        "purpose": str(chosen.get("purpose") or chosen.get("role") or "").strip(),
        "outputs": [
            named(name, ((entry.card.get("outputs") or {}).get(name) or {}) if entry else {})
            for name in chosen.get("outputs_used") or ()
        ],
        "status": str(chosen.get("capability_status") or "").strip(),
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


# ------------------------------------------------------------------ what a revision changed

_TEXT_LISTS = (
    ("assumptions", "assumption"),
    ("limitations", "limitation"),
    ("success_criteria", "success criterion"),
)
_TEXT_FIELDS = (("hypothesis", "hypothesis"), ("objective", "objective"))


def _clip(text, limit=160):
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _run_values(plan):
    runs = {}
    for run in plan.get("runs") or ():
        if isinstance(run, dict) and run.get("id"):
            runs[str(run["id"])] = run
    return runs


def changes(before, after):
    """What a revision changed, in sentences a reviewer reads without opening any JSON.

    Each item is {"kind": "changed"|"added"|"removed", "text": ...}. A value changed the same
    way in every run of a model is one line for the model, not one per run.
    """
    before, after = before or {}, after or {}
    out = []

    def say(kind, text):
        out.append({"kind": kind, "text": text})

    old_runs, new_runs = _run_values(before), _run_values(after)
    for run_id in new_runs.keys() - old_runs.keys():
        run = new_runs[run_id]
        say("added", "run %s (%s)%s" % (
            run_id, run.get("model") or "model",
            ": %s" % _clip(run.get("label"), 90) if run.get("label") else "",
        ))
    for run_id in old_runs.keys() - new_runs.keys():
        say("removed", "run %s" % run_id)

    # Parameter edits on runs present in both versions, grouped by model and edit.
    edits = {}
    for run_id in sorted(old_runs.keys() & new_runs.keys()):
        old, new = old_runs[run_id], new_runs[run_id]
        model = str(new.get("model") or old.get("model") or "")
        old_p, new_p = _params(old), _params(new)
        old_sweep, new_sweep = _sweep_text(old_p, model), _sweep_text(new_p, model)
        if old_sweep != new_sweep:
            swept = old_p.get("sweep_parameter")
            if swept and swept == new_p.get("sweep_parameter"):
                # The same sweep, a different range: name the parameter once.
                prefix = "%s from " % named(swept, _spec(model, swept))
                key = (model, "%s sweep" % named(swept, _spec(model, swept)),
                       old_sweep.replace(prefix, "", 1), new_sweep.replace(prefix, "", 1))
            else:
                key = (model, "sweep", old_sweep or "none", new_sweep or "none")
            edits.setdefault(key, []).append(run_id)
        for name in dict.fromkeys(list(old_p) + list(new_p)):
            if name in _SWEEP_FIELDS or _same(old_p.get(name), new_p.get(name)):
                continue
            spec = _spec(model, name)
            edits.setdefault(
                (model, named(name, spec), with_unit(old_p.get(name), spec.get("unit")),
                 with_unit(new_p.get(name), spec.get("unit"))),
                [],
            ).append(run_id)
    for (model, what, old, new), run_ids in edits.items():
        common = [i for i in old_runs.keys() & new_runs.keys()
                  if str(new_runs[i].get("model") or "") == model]
        where = ("every %s run" % (model or "model")) if len(run_ids) == len(common) and len(common) > 1 \
            else "run%s %s" % ("s" if len(run_ids) > 1 else "", ", ".join(run_ids))
        say("changed", "%s, %s: %s → %s" % (what, where, old, new))

    # Where a value comes from.
    old_map, new_map = _index_mapping(before), _index_mapping(after)
    for key in dict.fromkeys(list(old_map) + list(new_map)):
        model, name = key
        spec = _spec(model, name)
        def source(entries):
            if not entries:
                return ""
            item = entries[0]
            tag = TAGS.get(str(item.get("provenance_class") or ""), "unlabelled")
            ref = item.get("evidence_ref") or ""
            return "%s%s" % (tag, " (%s)" % ref if ref else "")
        old_s, new_s = source(old_map.get(key)), source(new_map.get(key))
        if old_s != new_s:
            if not old_s:
                say("added", "source of %s: %s" % (named(name, spec), new_s))
            elif not new_s:
                say("removed", "recorded source of %s" % named(name, spec))
            else:
                say("changed", "source of %s: %s → %s" % (named(name, spec), old_s, new_s))

    # Figures.
    old_charts = {c.get("id"): c for c in before.get("charts") or () if isinstance(c, dict)}
    new_charts = {c.get("id"): c for c in after.get("charts") or () if isinstance(c, dict)}
    def chart_text(chart):
        return "%s (%s against %s)" % (
            _clip(chart.get("label") or chart.get("id"), 80),
            ", ".join(str(y) for y in chart.get("ys") or [chart.get("y")] if y),
            chart.get("x"),
        )
    for chart_id in new_charts.keys() - old_charts.keys():
        say("added", "figure %s" % chart_text(new_charts[chart_id]))
    for chart_id in old_charts.keys() - new_charts.keys():
        say("removed", "figure %s" % chart_text(old_charts[chart_id]))
    for chart_id in new_charts.keys() & old_charts.keys():
        if chart_text(old_charts[chart_id]) != chart_text(new_charts[chart_id]):
            say("changed", "figure %s → %s" % (chart_text(old_charts[chart_id]), chart_text(new_charts[chart_id])))
        if bool(old_charts[chart_id].get("required", True)) != bool(new_charts[chart_id].get("required", True)):
            say("changed", "figure %s is now %s" % (
                _clip(new_charts[chart_id].get("label") or chart_id, 80),
                "required" if new_charts[chart_id].get("required", True) else "optional",
            ))

    for field, word in _TEXT_FIELDS:
        if _clip(before.get(field), 10000) != _clip(after.get(field), 10000) and after.get(field):
            say("changed", "%s now reads: %s" % (word, _clip(after.get(field))))
    for field, word in _TEXT_LISTS:
        old = [_clip(x) for x in before.get(field) or ()]
        new = [_clip(x) for x in after.get(field) or ()]
        for item in new:
            if item not in old:
                say("added", "%s: %s" % (word, item))
        for item in old:
            if item not in new:
                say("removed", "%s: %s" % (word, item))
    return out


def axis_name(plan, name):
    """A chart axis named by whichever model in the plan declares it, parameter or output."""
    for model in dict.fromkeys(str(r.get("model") or "") for r in (plan or {}).get("runs") or () if isinstance(r, dict)):
        entry = registry.get(model)
        if not entry:
            continue
        spec = (entry.card.get("parameters") or {}).get(name) or (entry.card.get("outputs") or {}).get(name)
        if spec:
            unit = unit_text(spec.get("unit"))
            return "%s%s" % (named(name, spec), " [%s]" % unit if unit else "")
    return str(name or "")
