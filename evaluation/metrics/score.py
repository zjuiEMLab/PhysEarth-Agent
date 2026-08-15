"""Score recorded runs.

Every metric here is recomputed from the record by this module, never read off what the
harness decided at run time. That is the whole point: a run with the harness switched off
records the calls it made and the markers it wrote, and this module judges them against
the same declaration the harness would have used. Otherwise the ablation would compare a
system to its own opinion of itself and every configuration would score perfectly.
"""

import math

from physearth import (
    harness,  # noqa: E402
    registry,  # noqa: E402
)
from physearth.harness import validation  # noqa: E402

NUMERIC_TOOLS = ("run_model", "run_planned_model")


def call_problems(entry):
    """What the declared capability says about one recorded run_model call.

    Recomputed from the model card, so it reads the same whether or not the harness was
    on when the call was made.
    """
    if entry["name"] not in NUMERIC_TOOLS:
        return None
    arguments = entry.get("arguments") or {}
    name = entry.get("model") or arguments.get("model") or (entry.get("spec") or {}).get("model")
    if entry["name"] == "run_planned_model":
        parameters = dict(entry.get("spec") or {})
    else:
        parameters = dict(arguments.get("parameters") or {})
        parameters.update({k: v for k, v in arguments.items() if k not in ("model", "parameters")})
        if not parameters and entry.get("spec"):
            parameters = dict(entry["spec"])
    model = registry.get(name)
    if model is None:
        return ["unknown model %r" % name]
    _, problems = validation.resolve(model.card, parameters)
    return problems


def classify_calls(record):
    """Split the run's model calls into legal, illegal-and-refused, illegal-and-executed."""
    legal, refused, executed = 0, 0, 0
    illegal_details = []
    for entry in record["tool_log"]:
        if entry["name"] not in NUMERIC_TOOLS:
            continue
        problems = call_problems(entry) or []
        ran = entry.get("status") == "success"
        if not problems:
            legal += 1
            continue
        illegal_details.append({"problems": problems[:3], "ran": ran})
        if ran:
            executed += 1
        else:
            refused += 1
    return {
        "legal": legal,
        "illegal_refused": refused,
        "illegal_executed": executed,
        "total": legal + refused + executed,
        "illegal_details": illegal_details,
    }


def citation_score(record):
    """How many markers in the delivered answer resolve to evidence the run gathered."""
    evidence = record["evidence"]
    check = harness.check_citations(
        record["answer"],
        set(evidence["sections"]),
        set(evidence["models"]),
        set(evidence["datasets"]),
    )
    total = len(check["markers"])
    unresolved = len(check["unresolved"])
    return {
        "markers": total,
        "unresolved": unresolved,
        "resolved_fraction": None if not total else (total - unresolved) / total,
        "unresolved_list": check["unresolved"][:6],
    }


def self_corrected(record):
    """After a refusal, did the run reach a legal successful call in the same turn?"""
    seen_refusal = False
    for entry in record["tool_log"]:
        if entry["name"] not in NUMERIC_TOOLS:
            continue
        problems = call_problems(entry) or []
        if problems and entry.get("status") != "success":
            seen_refusal = True
            continue
        if seen_refusal and not problems and entry.get("status") == "success":
            return True
    return False if seen_refusal else None


def _successful_specs(record, model_name=None):
    out = []
    for entry in record["tool_log"]:
        if entry["name"] not in NUMERIC_TOOLS or entry.get("status") != "success":
            continue
        spec = entry.get("spec") or {}
        name = entry.get("model") or (entry.get("arguments") or {}).get("model") or spec.get("model")
        if model_name and name != model_name:
            continue
        out.append(spec)
    return out


def config_match(record, task):
    """Field-by-field agreement with the reference configuration the source fixes."""
    reference = (task.get("reference") or {})
    fields = reference.get("graded_fields") or []
    if not fields:
        return None
    wanted = reference["parameters"]
    best = None
    for spec in _successful_specs(record, reference["model"]):
        hits = [f for f in fields if _same(spec.get(f), wanted.get(f))]
        score = len(hits) / len(fields)
        if best is None or score > best["fraction"]:
            best = {
                "fraction": score,
                "matched": hits,
                "missed": [
                    {"field": f, "wanted": wanted.get(f), "got": spec.get(f)}
                    for f in fields
                    if f not in hits
                ],
            }
    return best or {"fraction": 0.0, "matched": [], "missed": [{"field": f} for f in fields]}


def _same(got, wanted):
    if got is None:
        return False
    if isinstance(wanted, (int, float)) and not isinstance(wanted, bool):
        if not isinstance(got, (int, float)) or isinstance(got, bool):
            return False
        scale = max(abs(wanted), 1e-12)
        return abs(got - wanted) <= 1e-6 * scale
    return str(got) == str(wanted)


def reference_curve(task):
    """Run the fully specified reference configuration, with no agent between.

    Reported for provenance. It is not what the numeric metric compares against, for the
    reason set out under `numeric_error`.
    """
    reference = task.get("reference") or {}
    if not reference:
        return None
    model = registry.get(reference["model"])
    spec, problems = validation.resolve(model.card, reference["parameters"])
    if problems:
        raise ValueError("reference config for %s is illegal: %s" % (task["id"], problems))
    result = model.run(spec)
    return {"axis": result.get("axis"), "series": result["series"]}


def _run_spec(model_name, spec):
    model = registry.get(model_name)
    if model is None:
        return None
    try:
        resolved, _ = validation.resolve(
            model.card, {k: v for k, v in spec.items() if k != "model"}
        )
        # Replay the call even when today's card classifies an old recorded spec as
        # illegal. Legality is scored separately; this metric measures the numeric cost
        # of the configuration the agent actually executed.
        return model.run(resolved)
    except Exception:
        return None


def _agent_run(record, model_name):
    """The last successful run of the graded model, with the spec that produced it."""
    chosen = None
    for entry in record["tool_log"]:
        if entry["name"] not in NUMERIC_TOOLS or entry.get("status") != "success":
            continue
        spec = dict(entry.get("spec") or {})
        name = entry.get("model") or (entry.get("arguments") or {}).get("model") or spec.get("model")
        if name != model_name:
            continue
        chosen = (name, spec)
    return chosen


def numeric_error(record, task, reference=None):
    """How far the answer moves when only the graded fields are corrected.

    The comparison is not against the fully specified reference configuration. Doing that
    would measure the fields the source does not fix: for the Figure 6 task the paper
    states the theory, the microstructure and the correlation length but not the snow
    depth, and over a vacuum background depth moves brightness temperature by more than a
    hundred kelvin. The result would be a large error caused entirely by a free choice
    the task never asked the agent to make.

    So the target is the agent's own configuration with the graded fields forced to what
    the source says, and everything else left exactly as the agent chose it. The number
    then means what it should: how much the paper-stated physics the agent got wrong
    changed the answer, in the agent's own setting.
    """
    block = task.get("reference") or {}
    curve, point = block.get("curve"), block.get("point")
    if not (curve or point):
        return None
    found = _agent_run(record, block["model"])
    if found is None:
        return None
    model_name, agent_spec = found

    target_spec = dict(agent_spec)
    graded = block.get("graded_fields") or []
    for field in graded:
        if field in block["parameters"]:
            target_spec[field] = block["parameters"][field]
    if curve and target_spec.get("sweep_parameter") != agent_spec.get("sweep_parameter"):
        for field in ("sweep_start", "sweep_stop", "sweep_points"):
            if field in block["parameters"]:
                target_spec[field] = block["parameters"][field]

    got_result = _run_spec(model_name, agent_spec)
    want_result = _run_spec(model_name, target_spec)
    if got_result is None or want_result is None:
        return None

    if point:
        got = (got_result["series"].get(point["series"]) or [None])[0]
        want = (want_result["series"].get(point["series"]) or [None])[0]
        if got is None or want is None:
            return None
        error = abs(got - want)
        return {
            "kind": "point",
            "error": error,
            "got": got,
            "expected": want,
            "tolerance": point["tolerance"],
            "unit": point["unit"],
            "within": error <= point["tolerance"],
        }

    return _curve_error(got_result, want_result, curve)


def _curve_error(got_result, want_result, curve):
    want_axis = (want_result.get("axis") or {}).get("values")
    want_y = want_result["series"].get(curve["series"])
    got_axis = (got_result.get("axis") or {}).get("values")
    got_y = got_result["series"].get(curve["series"])
    if not (want_axis and want_y and got_axis and got_y):
        return {
            "kind": "curve",
            "error": None,
            "detail": "the agent did not produce a comparable sweep of %s" % curve["series"],
            "tolerance": curve["tolerance_rmse"],
            "unit": curve["unit"],
            "within": False,
        }
    interpolated = _interpolate(got_axis, got_y, want_axis)
    inside = [
        (a, b)
        for a, b, x in zip(interpolated, want_y, want_axis, strict=False)
        if a is not None and min(got_axis) <= x <= max(got_axis)
    ]
    if not inside:
        return {
            "kind": "curve",
            "error": None,
            "detail": "the two sweeps do not overlap",
            "tolerance": curve["tolerance_rmse"],
            "unit": curve["unit"],
            "within": False,
        }
    rmse = math.sqrt(sum((a - b) ** 2 for a, b in inside) / len(inside))
    return {
        "kind": "curve",
        "error": rmse,
        "n_compared": len(inside),
        "tolerance": curve["tolerance_rmse"],
        "unit": curve["unit"],
        "within": rmse <= curve["tolerance_rmse"],
    }


def _interpolate(axis, values, targets):
    """Linear interpolation onto the target axis; None outside the sampled span."""
    out = []
    pairs = sorted(zip(axis, values, strict=False))
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    for target in targets:
        if target < xs[0] or target > xs[-1]:
            out.append(None)
            continue
        lo = max(i for i in range(len(xs)) if xs[i] <= target)
        hi = min(len(xs) - 1, lo + 1)
        if hi == lo or abs(xs[hi] - xs[lo]) < 1e-15:
            out.append(ys[lo])
            continue
        weight = (target - xs[lo]) / (xs[hi] - xs[lo])
        out.append(ys[lo] + weight * (ys[hi] - ys[lo]))
    return out


def false_premise_handled(record, task):
    """Did the run avoid producing a number the premise cannot support?

    Judged on what executed, not on what the answer says: a successful model run whose
    configuration violates the declared domain is the failure, whatever prose surrounds
    it. The keyword check is reported alongside but does not decide the verdict.
    """
    premise = task.get("false_premise")
    if not premise:
        return None
    calls = classify_calls(record)
    words = [str(w).lower() for w in premise.get("answer_should_mention") or []]
    answer = (record["answer"] or "").lower()
    return {
        "executed_illegal": calls["illegal_executed"] > 0,
        "refused_illegal": calls["illegal_refused"] > 0,
        "answer_names_the_limit": all(w in answer for w in words) if words else None,
        "handled": calls["illegal_executed"] == 0 and bool(record["answer"]),
    }


def score_record(record, task, reference=None):
    calls = classify_calls(record)
    citations = citation_score(record)
    return {
        "task": record["task"],
        "suite": record["suite"],
        "quality": record.get("quality"),
        "config": record["config"],
        "repeat": record["repeat"],
        # Carried so the report can check that the four cells of a task share a model and
        # a build. A contrast that straddles two of either is comparing two things at once.
        "llm": record.get("llm"),
        "build": record.get("build"),
        "completed": bool(record["answer"]) and record["stop_rule"] in (None, "citation_integrity"),
        "stop_rule": record["stop_rule"],
        "model_calls": record["model_calls"],
        "tool_calls": record["tool_calls"],
        "calls": calls,
        "illegal_call_rate": None if not calls["total"] else
        (calls["illegal_refused"] + calls["illegal_executed"]) / calls["total"],
        "illegal_executed_rate": None if not calls["total"] else
        calls["illegal_executed"] / calls["total"],
        "self_corrected": self_corrected(record),
        "citations": citations,
        "config_match": config_match(record, task),
        "numeric": numeric_error(record, task, reference),
        "false_premise": false_premise_handled(record, task),
        "figures": len(record["figures"]),
        "read_sections": len(record["evidence"]["sections"]),
    }


def mean(values):
    values = [v for v in values if v is not None]
    return None if not values else sum(values) / len(values)


def fraction(values):
    values = [v for v in values if v is not None]
    return None if not values else sum(1 for v in values if v) / len(values)
