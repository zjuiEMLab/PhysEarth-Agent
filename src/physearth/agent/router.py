"""Which kind of turn this is, decided before the model is offered a single tool.

A question is one of three things. A direct model question wants a prediction, a trend or a
comparison from the registered models. An explanation wants words, perhaps with sources. A
reproduction wants a paper's result rebuilt through the reviewed research workflow. Each needs
different tools and different instructions, and offering all of them to every question made a
direct run read literature and a research guideline it never used.

Three cheap rules settle most turns and cost nothing: the user forbade tools, a research project
is already under way, or the wording asks to reproduce a paper result. What is left goes to one
short model call with reasoning off. If that cannot be made, the turn keeps the full tool set and
the full prompt, which is what every turn had before this existed, so a failure here never makes
the agent less able, only less lean.

Set PHYSEARTH_ROUTER=rules to skip the model call, as the evaluation suite does to keep its
records comparable.
"""

import re

from physearth import config

ANSWER, RUN, REPRODUCE, AUTO = "answer", "run", "reproduce", "auto"
PATHS = (ANSWER, RUN, REPRODUCE)

CLASSIFIER_PROMPT = (
    "Classify the user's message for an assistant that can run registered physical models and read "
    "scientific papers. Reply with exactly one word.\n"
    "run: a new prediction, parameter sweep, trend or comparison of configurations that registered "
    "models can answer directly, without rebuilding a published result.\n"
    "answer: an explanation, definition, summary or interpretation that needs no new model run.\n"
    "reproduce: reproducing, replicating or checking a result, figure or table from a paper, or any "
    "task whose method has to be taken from a paper.\n"
    "If unsure between run and another, reply run."
)

_WORD = re.compile(r"\b(answer|run|reproduce)\b")


def mode():
    value = str(config.get("PHYSEARTH_ROUTER") or "model").strip().lower()
    return "rules" if value in ("rules", "off", "0") else "model"


def parse(text):
    """The path a classifier reply names, or None."""
    match = _WORD.search(str(text or "").lower())
    return match.group(1) if match else None


def decide(question, session, *, held=False, bypass=False, reproduction=False, classify=None):
    """The route for this turn: {"path", "source", "reason"}.

    `classify(question)` returns the model's one-word reply. It is called only when the rules
    cannot decide and the mode allows it.
    """
    session = session or {}
    if held:
        return session.get("route") or {"path": AUTO, "source": "rule", "reason": "continuing a held request"}
    if bypass:
        return {"path": ANSWER, "source": "rule", "reason": "the user ruled out tools"}
    project = session.get("research") or {}
    if project or session.get("research_required"):
        return {"path": REPRODUCE, "source": "rule", "reason": "a research project is under way"}
    if reproduction:
        return {"path": REPRODUCE, "source": "rule", "reason": "the wording asks to reproduce a paper result"}
    if mode() == "rules" or classify is None:
        return {"path": AUTO, "source": "rule", "reason": "no rule applied"}
    try:
        reply = classify(question)
    except Exception as exc:  # the route is an optimisation; never stop the turn for it
        return {"path": AUTO, "source": "fallback", "reason": "router unavailable: %s" % type(exc).__name__}
    path = parse(reply)
    if path is None:
        return {"path": AUTO, "source": "fallback", "reason": "unrecognised reply %r" % str(reply)[:40]}
    return {"path": path, "source": "model", "reason": "classified as %s" % path}
