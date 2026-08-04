"""The EarthModel contract.

A registered model is a directory holding two things:

    model_card.yaml   identity, capability declaration, resource profile
    <module>.py       a module exposing run(spec) -> dict

Everything the harness needs is declared in the card. The card is the single
source of truth: the system prompt, the tool schema and the parameter
validation are all generated from it, so a model cannot be validated against
one description and executed against another.
"""

REQUIRED_TOP_LEVEL = ("name", "version", "description", "citation", "license", "tier", "entrypoint")
REQUIRED_PARAMETER_FIELDS = ("type", "unit", "description")
NUMERIC_TYPES = ("number", "integer")
ALLOWED_TYPES = NUMERIC_TYPES + ("string", "boolean")
TIERS = ("demo", "local")


class DeclarationError(Exception):
    """Raised when a model card cannot be trusted to drive validation."""


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _fail(problems, message):
    problems.append(message)


def validate_card(card):
    """Return a list of problems. An empty list means the card can be registered."""
    problems = []
    if not isinstance(card, dict):
        return ["model card is not a mapping"]

    for field in REQUIRED_TOP_LEVEL:
        if not card.get(field):
            _fail(problems, "missing required field %r" % field)

    tier = card.get("tier")
    if tier and tier not in TIERS:
        _fail(problems, "tier %r must be one of %s" % (tier, ", ".join(TIERS)))
    if tier == "local" and not card.get("requires_import"):
        _fail(
            problems,
            "a local model must declare requires_import: the module whose presence decides "
            "whether it can run on a given host",
        )
    if card.get("requires_import") and tier != "local":
        _fail(problems, "requires_import only applies to a local model")

    parameters = card.get("parameters")
    if not isinstance(parameters, dict) or not parameters:
        _fail(problems, "parameters must be a non-empty mapping")
        parameters = {}

    for name, spec in parameters.items():
        problems.extend(_validate_parameter(name, spec))

    outputs = card.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        _fail(problems, "outputs must be a non-empty mapping")
    else:
        for name, spec in outputs.items():
            if not isinstance(spec, dict) or not spec.get("unit"):
                _fail(problems, "output %r must declare a unit" % name)

    for index, rule in enumerate(card.get("combinations") or []):
        problems.extend(_validate_combination(index, rule, parameters))

    return problems


def _validate_parameter(name, spec):
    problems = []
    if not isinstance(spec, dict):
        return ["parameter %r is not a mapping" % name]
    for field in REQUIRED_PARAMETER_FIELDS:
        if field not in spec:
            _fail(problems, "parameter %r is missing %r" % (name, field))
    kind = spec.get("type")
    if kind not in ALLOWED_TYPES:
        _fail(problems, "parameter %r has type %r, expected one of %s" % (name, kind, ", ".join(ALLOWED_TYPES)))
        return problems
    if kind in NUMERIC_TYPES:
        low, high = spec.get("minimum"), spec.get("maximum")
        if low is None or high is None:
            _fail(
                problems,
                "numeric parameter %r must declare minimum and maximum; without a range the "
                "physical domain check silently passes everything" % name,
            )
        elif not _is_number(low) or not _is_number(high):
            _fail(
                problems,
                "parameter %r has a non-numeric bound (minimum=%r, maximum=%r). In YAML an "
                "exponent needs an explicit sign, so write 1.0e+9 rather than 1.0e9, "
                "otherwise the bound is loaded as text and the range check is meaningless"
                % (name, low, high),
            )
        elif low > high:
            _fail(problems, "parameter %r has minimum %s above maximum %s" % (name, low, high))
    for bound in ("default", "minimum", "maximum"):
        if kind in NUMERIC_TYPES and spec.get(bound) is not None and not _is_number(spec[bound]):
            _fail(problems, "parameter %r has a non-numeric %s: %r" % (name, bound, spec[bound]))
    if kind == "string" and spec.get("enum") is not None and not spec["enum"]:
        _fail(problems, "parameter %r declares an empty enum" % name)
    return problems


def _validate_combination(index, rule, parameters):
    problems = []
    if not isinstance(rule, dict):
        return ["combination %d is not a mapping" % index]
    for side in ("when", "allow"):
        if side not in rule:
            _fail(problems, "combination %d is missing %r" % (index, side))
            return problems
    for side in ("when", "allow"):
        for key, values in (rule[side] or {}).items():
            if key not in parameters:
                _fail(problems, "combination %d refers to unknown parameter %r" % (index, key))
            elif not isinstance(values, list) or not values:
                _fail(problems, "combination %d must give a non-empty list for %r" % (index, key))
    if not rule.get("reason"):
        _fail(problems, "combination %d must carry a reason the agent can be told" % index)
    return problems
