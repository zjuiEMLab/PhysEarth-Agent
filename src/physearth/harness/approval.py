"""Human approval before a physical model runs.

The first volume settled that a confirmation button needs a state gate behind it and that
the model has no authority to confirm on its own behalf. This is that gate. It sits
between the agent's decision to call `run_model` and the call happening, so it cannot be
argued around: the model never sees a way to skip it, and a refusal comes back as an
ordinary tool result it has to deal with.

Two properties matter more than the feature itself.

It never passes by default, and it never holds a worker. Asking ends the turn: the agent
pauses with the request and everything it needs to continue stored in the session, and
nothing has been computed. Only an explicit verdict continues it, however much later that
comes. A new question instead of a verdict drops the request, so a reviewer who walks
away from the page gets no result, never an unapproved one.

It cannot be forged. The verdict is written by the interface into the session, never by a
tool argument, and a verdict with no pending request is discarded.
"""

import threading
import time

_LOCK = threading.Lock()
ASK = "ask"
ALWAYS = "always"


def gate(session):
    """The gate is off unless something switched it on.

    A library that asks by default is a trap: the evaluation suite, a script and a test
    all drive the agent with nobody watching, and none of them should pause on every model
    call with nobody there to answer. The interface turns it on when it starts, which is the
    one context where there is a person to ask.
    """
    if session is None:
        return {"mode": ALWAYS, "pending": None}
    return session.setdefault(
        "approval", {"mode": ALWAYS, "pending": None, "verdict": None}
    )


def mode(session):
    return gate(session).get("mode", ASK)


def set_mode(session, value):
    gate(session)["mode"] = ALWAYS if value == ALWAYS else ASK
    return mode(session)


def required(session):
    return mode(session) == ASK


def describe(name, arguments):
    """What the person is being asked to approve, in their terms rather than the model's."""
    parameters = dict((arguments or {}).get("parameters") or {})
    parameters.update(
        {k: v for k, v in (arguments or {}).items() if k not in ("model", "parameters")}
    )
    sweep = parameters.get("sweep_parameter")
    if sweep and sweep != "none":
        shape = "sweep %s from %s to %s in %s points" % (
            sweep,
            parameters.get("sweep_start"),
            parameters.get("sweep_stop"),
            parameters.get("sweep_points", 10),
        )
    else:
        shape = "a single point"
    fixed = {
        k: v
        for k, v in parameters.items()
        if not k.startswith("sweep_") and k != "sweep_parameter"
    }
    return {
        "model": (arguments or {}).get("model", "?"),
        "shape": shape,
        "parameters": fixed,
        "raw": arguments or {},
    }


def request(session, name, arguments, resume=None):
    """Hold a call for a verdict. `resume` is what the agent needs to continue from it."""
    entry = gate(session)
    entry["pending"] = {
        "tool": name,
        "arguments": arguments or {},
        "description": describe(name, arguments),
        "asked_at": time.time(),
        "resume": resume,
    }
    entry["verdict"] = None
    return entry["pending"]


def pending(session):
    """The request still waiting for a person; a decided one is no longer on offer."""
    entry = gate(session)
    return entry.get("pending") if entry.get("verdict") is None else None


def decide(session, decision, arguments=None):
    """Called by the interface. Returns True only for the first verdict on a request."""
    entry = gate(session)
    with _LOCK:
        if not entry.get("pending") or entry.get("verdict") is not None:
            return False
        if decision == ALWAYS:
            entry["mode"] = ALWAYS
            decision = "approve"
        entry["verdict"] = {"decision": decision, "arguments": arguments}
    return True


def take(session):
    """Remove the held request and return it with its verdict, or None if nothing is held."""
    entry = gate(session)
    with _LOCK:
        held = entry.get("pending")
        verdict = entry.get("verdict")
        entry["pending"] = None
        entry["verdict"] = None
    if not held:
        return None
    return dict(held, verdict=verdict)


def declined_result(name, arguments):
    """A refusal shaped like every other tool refusal, so the model handles it normally."""
    return {
        "status": "needs_input",
        "summary": "The person running this declined the call to %s." % name,
        "data": {
            "tool": name,
            "rejected_parameters": arguments or {},
            "problems": [
                "a human reviewed this call and declined it. Do not repeat it unchanged. "
                "Either propose a different configuration and explain what you changed, or "
                "answer without running the model and say which part of the question you "
                "therefore cannot answer."
            ],
        },
        "citations": [],
        "qc": None,
        "ui": None,
        "error": "declined by the person running this",
    }
