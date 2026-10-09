"""Steps a question can need besides running a registered model, and which have a tool.

A reproduction is a model run plus whatever is done with the runs: sweep a parameter, plot,
compare with reference data -- or something with no tool behind it yet, such as solving for
the parameter value at which two results agree. The capability check asks the agent to say
which of these steps its plan needs; this module says which have a tool and, for those that
do not, what the user can choose instead.

Entries describe what a step does. They never name a paper, a figure or a model, and the
agent's own wording is matched on aliases of the step, not on the question.
"""

import re

AVAILABLE = "available"
MISSING = "missing"

OPERATIONS = (
    {
        "id": "sweep_parameter",
        "label": "sweep one parameter over a range",
        "status": AVAILABLE,
        "aliases": ("sweep", "parameter_sweep", "sensitivity", "grid"),
    },
    {
        "id": "plot_results",
        "label": "plot runs against each other or a reference",
        "status": AVAILABLE,
        "aliases": ("plot", "chart", "figure", "overlay"),
    },
    {
        "id": "compare_with_reference_data",
        "label": "compare runs with reference data or a summary statistic",
        "status": AVAILABLE,
        "aliases": ("compare", "reference_data", "rmsd", "rmse", "bias", "statistic", "metric"),
    },
    {
        "id": "solve_for_parameter",
        "label": "find the parameter value at which two results agree",
        "tool": "root-finding tool",
        "status": MISSING,
        "aliases": (
            "solve", "root_finding", "root_search", "equivalence", "match_target",
            "inverse_solve", "find_value_such_that",
        ),
        "reason": "no registered tool searches for a parameter value",
        "why": (
            "A model run maps inputs to outputs. This step needs the reverse: the input that gives a "
            "target result. A solver tries values and scores each against the target with a cost "
            "function (the gap between result and target) until the gap is zero."
        ),
        "options": (
            {"id": "A", "label": "Write and run a solver script", "available": True,
             "note": "available now, you approve the code first",
             "detail": "The agent writes a short Python script that runs the registered model for each "
             "trial value and applies a root-finding routine to the cost function. You read the code "
             "before it runs, and every model run is recorded so the report can cite how the value "
             "was found.",
             "function": "scipy.optimize.brentq",
             "reference": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html",
             "next": "Write the solver and call run_analysis_script; the person approves the code."},
            {"id": "B", "label": "Sweep and compare", "available": True, "note": "available now",
             "detail": "Run the sweeps the figure is built from and plot them together. The value is "
             "read off where the curves meet, not solved, so it is an approximation and the report "
             "says so.",
             "next": "Call research_capability_check(action='confirm_partial'), then propose a plan "
             "for the sweeps only."},
            {"id": "C", "label": "Upload your own function", "available": False, "note": "not supported yet",
             "detail": "A Python function that returns the cost for a trial value, or a complete solver. "
             "It would run in a sandbox after you approve it, and results would be marked as "
             "coming from a user-supplied function.",
             "next": "Not available yet: tell the person and ask them to choose A or B."},
        ),
    },
    {
        "id": "derive_quantity",
        "label": "compute a quantity that no registered model outputs",
        "tool": "way to compute it",
        "status": MISSING,
        "aliases": ("derive", "derived_quantity", "post_process", "postprocess", "compute_quantity"),
        "reason": "no registered model outputs this quantity",
        "why": (
            "A registered model returns only the outputs it declares. This quantity has to be derived "
            "from model runs by a method, such as an equation applied to several runs or a search, "
            "written as a script."
        ),
        "options": (
            {"id": "A", "label": "Write and run a script", "available": True,
             "note": "available now, you approve the code first",
             "detail": "The agent writes a short Python script that gets the model's outputs from "
             "run_model and derives the quantity from them by the method you name, or the one the "
             "paper describes. You read the code before it runs.",
             "next": "Write the script and call run_analysis_script; the person approves the code."},
            {"id": "B", "label": "Partial plan", "available": True, "note": "available now",
             "detail": "Run and plot only what the registered models output, and say the derived "
             "quantity was not computed.",
             "next": "Call research_capability_check(action='confirm_partial'), then propose a plan "
             "for the runnable part only."},
            {"id": "C", "label": "Upload your own function", "available": False, "note": "not supported yet",
             "detail": "Your own function for this quantity, run in a sandbox after you approve it.",
             "next": "Not available yet: tell the person and ask them to choose A or B."},
        ),
    },
    {
        "id": "fit_parameters",
        "label": "fit or calibrate parameters to observations",
        "tool": "optimization (fitting) tool",
        "status": MISSING,
        "aliases": ("fit", "calibrate", "calibration", "optimise", "optimize", "optimisation",
                    "optimization", "retrieve", "retrieval", "inversion", "inverse"),
        "reason": "no registered tool fits parameters to data or minimises a cost function",
        "why": (
            "Fitting needs the parameter values that make the model best match the observations. An "
            "optimizer adjusts the parameters to shrink a cost function (the distance between model "
            "and data)."
        ),
        "options": (
            {"id": "A", "label": "Write and run a fitting script", "available": True,
             "note": "available now, you approve the code first",
             "next": "Write the fit and call run_analysis_script; the person approves the code.",
             "detail": "The agent writes a short Python script that runs the registered model and "
             "applies a least-squares or minimisation routine to the cost function, with a stated "
             "stopping rule. You read the code before it runs, and every model run is recorded.",
             "function": "scipy.optimize.least_squares (or scipy.optimize.minimize)",
             "reference": "https://docs.scipy.org/doc/scipy/reference/optimize.html"},
            {"id": "B", "label": "Grid and compare", "available": True, "note": "available now",
             "detail": "Run the forward model over a grid of parameter values and show the misfit for "
             "each. No fitted value is reported."},
            {"id": "C", "label": "Upload your own function", "available": False, "note": "not supported yet",
             "detail": "Your own cost or fitting function, run in a sandbox after you approve it."},
        ),
    },
)


def _key(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _index():
    table = {}
    for entry in OPERATIONS:
        for name in (entry["id"], *entry.get("aliases", ())):
            table[_key(name)] = entry
    return table


def vocabulary():
    """The step ids the agent may name, with what each does, for the tool description."""
    return "; ".join("%s (%s)" % (entry["id"], entry["label"]) for entry in OPERATIONS)


def resolve(names):
    """Split what the agent listed into steps with a tool, steps without, and unknown words.

    Unknown words are reported, not blocked on: a step this registry does not know is not
    evidence that the plan cannot run.
    """
    if isinstance(names, str):
        names = [names]
    table = _index()
    available, missing, unknown = [], [], []
    for raw in names or ():
        details = {}
        if isinstance(raw, dict):
            details = {
                key: str(raw.get(key)).strip()
                for key in ("find", "must_match", "repeated_for") if raw.get(key)
            }
            raw = raw.get("step") or raw.get("operation") or raw.get("id") or ""
        text = str(raw or "").strip()
        if not text:
            continue
        entry = table.get(_key(text))
        if entry is None:
            # A phrase such as "find the stickiness at which the two agree" names its step
            # by a word it contains.
            tokens = [_key(part) for part in re.split(r"[\s,;/]+", text)]
            entry = next((table[t] for t in tokens if t in table), None)
        if entry is None:
            if text not in unknown:
                unknown.append(text)
        elif entry["status"] == AVAILABLE:
            if entry["id"] not in available:
                available.append(entry["id"])
        elif entry["id"] not in [item["id"] for item in missing]:
            missing.append({
                "id": entry["id"],
                "label": entry["label"],
                "reason": entry["reason"],
                "why": entry.get("why", entry["reason"]),
                "tool": entry.get("tool", "tool for this step"),
                "need": "A %s" % entry.get("tool", "tool for this step"),
                "options": [dict(option) for option in entry["options"]],
                "asked_as": text,
                "details": details,
            })
    return available, missing, unknown


def derive_item(outputs):
    """The missing step implied by outputs no registered model declares, when none was listed."""
    entry = next(item for item in OPERATIONS if item["id"] == "derive_quantity")
    named = ", ".join(str(item) for item in outputs)
    return {
        "id": entry["id"], "label": entry["label"], "reason": entry["reason"], "why": entry["why"],
        "tool": entry["tool"], "need": "A way to compute %s" % named,
        "options": [dict(option) for option in entry["options"]],
        "asked_as": "", "details": {"find": named},
    }


def next_steps(missing):
    """For the agent, not the person: what to do for each option the person might pick."""
    steps = {}
    for item in missing:
        for option in item.get("options") or ():
            steps.setdefault(option["id"], option.get("next", ""))
    return steps


def explain(item):
    """A missing step as short blocks: what is to be found, why, and the choices.

    What is to be found comes from the agent's own account. When it gave none, the text says so
    and asks the user, rather than inventing a reason.
    """
    details = item.get("details") or {}
    lines = []
    for key, label in (("find", "To find"), ("must_match", "Must match"), ("repeated_for", "Repeated for")):
        if details.get(key):
            lines.append("- %s: %s" % (label, details[key]))
    blocks = []
    if lines:
        blocks.append("**The problem**")
        blocks.append("\n".join(lines))
    else:
        blocks.append(
            "The agent could not tell what has to be found. Say which quantity is unknown and what "
            "it must match."
        )
    blocks.append("**Why:** " + item.get("why", item.get("reason", "")))
    option_lines = []
    for option in item.get("options") or ():
        parts = ["**%s. %s** (%s)." % (option["id"], option["label"], option.get("note", ""))]
        if option.get("detail"):
            parts.append(option["detail"])
        if option.get("function"):
            parts.append("Function: `%s`." % option["function"])
        if option.get("reference"):
            parts.append(option["reference"])
        option_lines.append("- " + " ".join(parts))
    blocks.append("**Options**")
    blocks.append("\n".join(option_lines))
    blocks.append(
        "For larger or open-ended analysis, the Claude Code or Codex plugin runs Python in your own "
        "environment, with your own packages."
    )
    return "\n\n".join(blocks)


_CHOICE = re.compile(r"^\s*(?:option\s+|choose\s+|pick\s+)?([abc])\s*[.)!]?\s*$", re.IGNORECASE)


def choice(review, text):
    """The option a one-letter reply picks: {"id", "available", "instruction"}, or None."""
    match = _CHOICE.match(str(text or ""))
    review = review or {}
    if not match or review.get("status") != "waiting_user":
        return None
    wanted = match.group(1).upper()
    for item in review.get("missing_operations") or ():
        for option in item.get("options") or ():
            if option["id"] != wanted:
                continue
            return {
                "id": wanted,
                "available": bool(option.get("available")),
                "instruction": (
                    "The person chose option %s for the step that has no tool (%s): %s. %s %s"
                    % (
                        wanted, item["label"], option["label"],
                        "It is available." if option.get("available") else "It is not available yet.",
                        option.get("next", ""),
                    )
                ),
            }
    return None


def choice_instruction(review, text):
    """The person's one-letter reply to the options, spelled out for the agent. None otherwise.

    "A" means nothing to a model that sees only the last message and a summary; what the option
    was, and what to do for it, is in the review the options came from.
    """
    picked = choice(review, text)
    return picked["instruction"] if picked else None
