"""B4: check the declared source of every parameter against what the system recorded.

A run records which of its parameters the agent never set: `defaulted_parameters`, the
card defaults the validator filled in. A label is the agent's claim about where a value
came from, so a default labelled as read from the paper is mislabelled, and a parameter
that changed the result but carries no label from the agent is unlabelled.

Only the agent's own labels count. The planner fills in missing mapping entries and
provenance classes itself and records each fill in `automatic_repairs`; those are the
system describing itself, and crediting them to the agent would make the check circular.

Only parameters that matter are held to account. Whether one matters is computed, not
listed: the run is repeated with that one parameter moved to another legal value, and one
that leaves every output unchanged (the viewing angle of a scattering coefficient, say)
has nothing to disclose. That keeps the check true for any registered model without a
per-model list of which parameters count.
"""

import math

from physearth import registry
from physearth.harness import validation

SWEEP_FIELDS = ("sweep_parameter", "sweep_start", "sweep_stop", "sweep_points")
DEFAULT_WORDS = ("default", "assum", "unknown", "unstated", "not stated")
PAPER_WORDS = ("paper", "literature", "source")


def _label_kind(label):
    text = str(label or "").strip().lower()
    if not text:
        return None
    if any(word in text for word in DEFAULT_WORDS):
        return "default"
    if "#" in text or any(text.startswith(word) for word in PAPER_WORDS):
        return "paper"
    if "question" in text or "user" in text:
        return "question"
    return "other"


def _repaired_fields(plan):
    return {
        str(item.get("field") or ""): item
        for item in plan.get("automatic_repairs") or []
        if isinstance(item, dict)
    }


def declared_labels(record):
    """The source labels the agent itself wrote, in the plan and in the report appendix."""
    plan = (record.get("research") or {}).get("plan") or {}
    repaired = _repaired_fields(plan)
    labels = {}
    for name, label in (plan.get("condition_provenance") or {}).items():
        if f"paper_conditions.{name}" in repaired or f"condition_provenance.{name}" in repaired:
            continue
        labels.setdefault(str(name), []).append(str(label))
    for index, item in enumerate(plan.get("parameter_mapping") or []):
        if not isinstance(item, dict) or not item.get("model_input"):
            continue
        if f"parameter_mapping.{item.get('model')}.{item['model_input']}" in repaired:
            continue
        fill = repaired.get(f"parameter_mapping[{index}].provenance_class")
        label = (fill or {}).get("from") if fill else item.get("provenance_class")
        if label:
            labels.setdefault(str(item["model_input"]), []).append(str(label))
    for item in record.get("parameter_provenance") or []:
        if isinstance(item, dict) and item.get("field") and item.get("source_kind"):
            labels.setdefault(str(item["field"]), []).append(str(item["source_kind"]))
    return labels


def _alternative(spec, name, card):
    declared = (card.get("parameters") or {}).get(name) or {}
    value = spec.get(name)
    if declared.get("enum"):
        return [option for option in declared["enum"] if option != value]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return []
    low, high = declared.get("minimum"), declared.get("maximum")
    if declared.get("type") == "integer":
        candidates = [value + 1, value - 1]
    else:
        step = abs(value) * 0.1 or 0.1
        candidates = [value + step, value - step]
    return [
        item
        for item in candidates
        if (low is None or item >= low) and (high is None or item <= high)
    ]


def _outputs_differ(first, second):
    left = (first or {}).get("series") or {}
    right = (second or {}).get("series") or {}
    if left.keys() != right.keys():
        return True
    for key in left:
        a, b = left[key], right[key]
        if len(a) != len(b):
            return True
        for x, y in zip(a, b, strict=True):
            if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                if x != y:
                    return True
            elif not math.isclose(x, y, rel_tol=1.0e-9, abs_tol=1.0e-12):
                return True
    return False


def matters(model_name, spec, name):
    """True when moving this one parameter to another legal value changes an output."""
    entry = registry.get(model_name)
    if entry is None:
        return None
    base, problems = validation.resolve(entry.card, spec)
    if problems:
        return None
    try:
        reference = entry.run(base)
    except Exception:
        return None
    for value in _alternative(base, name, entry.card):
        moved, problems = validation.resolve(entry.card, dict(base, **{name: value}))
        if problems:
            continue
        try:
            if _outputs_differ(reference, entry.run(moved)):
                return True
        except Exception:
            continue
        return False
    return False


def check(record):
    """Mislabelled and unlabelled parameters of the planned runs, or None without a plan."""
    plan = (record.get("research") or {}).get("plan") or {}
    runs = plan.get("runs") or []
    if not runs:
        return None
    labels = declared_labels(record)
    relevant, defaulted, inert, unknown = {}, set(), set(), set()
    for run in runs:
        spec = dict(run.get("resolved_parameters") or run.get("parameters") or {})
        swept = spec.get("sweep_parameter")
        run_defaults = set(run.get("defaulted_parameters") or ())
        for name in spec:
            if name in SWEEP_FIELDS or name == swept:
                continue
            if name in relevant:
                if name in run_defaults:
                    defaulted.add(name)
                continue
            verdict = matters(run.get("model"), spec, name)
            if verdict is None:
                unknown.add(name)
            elif verdict:
                relevant[name] = run.get("id")
                if name in run_defaults:
                    defaulted.add(name)
            else:
                inert.add(name)
    mislabelled, unlabelled = [], []
    for name in sorted(relevant):
        kinds = {_label_kind(label) for label in labels.get(name, ())} - {None}
        if not kinds:
            unlabelled.append(
                {"parameter": name, "card_default": name in defaulted, "run": relevant[name]}
            )
        elif name in defaulted and kinds & {"paper", "question"} and "default" not in kinds:
            mislabelled.append(
                {"parameter": name, "labels": labels.get(name, []), "run": relevant[name]}
            )
    return {
        "relevant": sorted(relevant),
        "relevant_card_defaults": sorted(defaulted),
        "inert": sorted(inert - set(relevant)),
        "undetermined": sorted(unknown - set(relevant) - inert),
        "mislabelled": mislabelled,
        "unlabelled": unlabelled,
        "passed": not mislabelled and not unlabelled,
    }
