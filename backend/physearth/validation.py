"""Physical domain validation and result quality control.

Both work from a model's declared capability, so they apply unchanged to any
model registered through the contract. Neither is a tool the agent can choose
to skip: validation runs before the call and quality control runs after it.
"""

from physearth.models import contract


def _coerce(name, spec, value, problems):
    kind = spec["type"]
    if isinstance(value, (dict, list)):
        problems.append(
            "%s was given a %s, but it is a single %s. Every parameter goes as a flat "
            "key inside the parameters object, so write "
            '{"parameters": {"%s": <value>, "sweep_parameter": "...", "sweep_start": ...}}'
            % (name, type(value).__name__, kind, name)
        )
        return None
    if kind == "integer":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            problems.append("%s must be an integer, got %r" % (name, value))
            return None
        if float(value) != int(value):
            problems.append("%s must be a whole number, got %s" % (name, value))
            return None
        return int(value)
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            problems.append("%s must be a number, got %r" % (name, value))
            return None
        return float(value)
    if kind == "boolean":
        if not isinstance(value, bool):
            problems.append("%s must be true or false, got %r" % (name, value))
            return None
        return value
    return str(value)


def resolve(card, arguments, enforce=True):
    """Fill defaults, coerce types, and check ranges, enums and combinations.

    Returns (spec, problems). The spec is only usable when problems is empty.

    With `enforce` false a value that fails a range or enum check is written into the
    spec anyway and the problem is still reported. That is the harness ablation: the
    caller gets to see what the model would have run had nothing stopped it. Type
    coercion still applies, because a string where a float belongs is not a physical
    claim about the world, it is a malformed call.
    """
    problems = []
    declared = card["parameters"]
    spec = {}

    for name in arguments:
        if name not in declared:
            problems.append(
                "%s is not a parameter of %s. Declared parameters: %s."
                % (name, card["name"], ", ".join(sorted(declared)))
            )

    for name, param in declared.items():
        required = param.get("required", True)
        if name in arguments and arguments[name] is not None:
            value = _coerce(name, param, arguments[name], problems)
            if value is None and param["type"] != "boolean":
                continue
        elif "default" in param and param["default"] is not None:
            value = param["default"]
        elif required:
            problems.append("%s is required and has no default" % name)
            continue
        else:
            continue

        if param["type"] == "string" and param.get("enum") and value not in param["enum"]:
            problems.append(
                "%s must be one of %s, got %r" % (name, ", ".join(map(str, param["enum"])), value)
            )
            if enforce:
                continue
        if param["type"] in contract.NUMERIC_TYPES:
            low, high = param["minimum"], param["maximum"]
            if not low <= value <= high:
                problems.append(
                    "%s = %s is outside the physical range %s to %s %s"
                    % (name, value, low, high, param["unit"])
                )
                if enforce:
                    continue
        spec[name] = value

    problems.extend(_check_combinations(card, spec))
    problems.extend(_check_sweep(card, spec))
    return spec, problems


def _check_combinations(card, spec):
    problems = []
    for rule in card.get("combinations") or []:
        triggered = all(spec.get(key) in values for key, values in rule["when"].items())
        if not triggered:
            continue
        for key, allowed in rule["allow"].items():
            if key in spec and spec[key] not in allowed:
                problems.append(
                    "%s = %r is not allowed when %s. Allowed here: %s. %s"
                    % (
                        key,
                        spec[key],
                        ", ".join("%s = %r" % (k, spec.get(k)) for k in rule["when"]),
                        ", ".join(map(str, allowed)),
                        rule["reason"],
                    )
                )
    return problems


def _check_sweep(card, spec):
    swept = spec.get("sweep_parameter", "none")
    if swept in (None, "none"):
        return []
    problems = []
    declared = card["parameters"]
    if swept not in declared:
        return ["sweep_parameter %r is not a parameter of %s" % (swept, card["name"])]
    for bound in ("sweep_start", "sweep_stop"):
        if spec.get(bound) is None:
            problems.append("%s is required when sweep_parameter is set" % bound)
    if problems:
        return problems
    target = declared[swept]
    low, high = target["minimum"], target["maximum"]
    for bound in ("sweep_start", "sweep_stop"):
        value = spec[bound]
        if not low <= value <= high:
            problems.append(
                "%s = %s is outside the physical range of %s, which is %s to %s %s"
                % (bound, value, swept, low, high, target["unit"])
            )
    if spec["sweep_start"] == spec["sweep_stop"]:
        problems.append("sweep_start and sweep_stop are equal, which is not a sweep")
    return problems


def quality_control(card, result):
    """Check a model result against its declared outputs. Never raises."""
    checks = []
    outputs = card["outputs"]
    series = (result or {}).get("series") or {}

    if not series:
        return {
            "passed": False,
            "checks": [{"check": "non_empty", "passed": False, "detail": "the model returned no series"}],
        }

    for name, values in series.items():
        declared = outputs.get(name)
        if declared is None:
            checks.append(
                {"check": "declared_output", "output": name, "passed": False,
                 "detail": "%s is not a declared output of %s" % (name, card["name"])}
            )
            continue
        finite = [v for v in values if isinstance(v, (int, float)) and v == v and abs(v) != float("inf")]
        missing = len(values) - len(finite)
        if missing:
            checks.append(
                {"check": "finite", "output": name, "passed": False,
                 "detail": "%d of %d values are not finite" % (missing, len(values))}
            )
        if finite:
            low = declared.get("valid_min")
            high = declared.get("valid_max")
            out_of_range = [v for v in finite if (low is not None and v < low) or (high is not None and v > high)]
            checks.append(
                {
                    "check": "physical_range",
                    "output": name,
                    "passed": not out_of_range,
                    "detail": "%d of %d values outside %s to %s %s"
                    % (len(out_of_range), len(finite), low, high, declared["unit"]),
                    "min": min(finite),
                    "max": max(finite),
                    "unit": declared["unit"],
                }
            )

    axis = (result or {}).get("axis")
    if axis:
        lengths = {len(v) for v in series.values()}
        aligned = lengths == {len(axis["values"])}
        checks.append(
            {"check": "axis_alignment", "passed": aligned,
             "detail": "axis has %d values, series lengths %s" % (len(axis["values"]), sorted(lengths))}
        )

    return {"passed": all(c["passed"] for c in checks), "checks": checks}
