"""TODO: what this model is, and what it is not for.

Copy this file with model_card.yaml. By the time `run` is called the harness has already
checked every parameter against the ranges and combinations the card declares, so this
does not re-check them -- and must not accept anything the card does not declare.
"""


def run(spec):
    """Return a mapping of output name to a list of values.

    `spec` holds the validated parameters. For a `local` model, import the dependency
    here rather than at module level: the registry loads this file on hosts that do not
    have it. See models/CONTRACT.md.
    """
    temperature = float(spec["temperature"])
    formulation = spec.get("formulation", "simple")

    # TODO: replace with the physics. Return one entry per declared output; the names and
    # the number of values must match what the card declares.
    value = temperature if formulation == "simple" else temperature * 1.0

    return {"result": [value]}
