"""Human approval before a physical model runs.

The first volume settled that a confirmation button needs a state gate behind it and that
the model has no authority to confirm on its own behalf. This is that gate. It sits
between the agent's decision to call `run_model` and the call happening, so it cannot be
argued around: the model never sees a way to skip it, and a refusal comes back as an
ordinary tool result it has to deal with.

Two properties matter more than the feature itself.

It cannot hang. The wait is bounded, and when the bound passes the call proceeds with the
trace saying plainly that nobody answered. A reviewer who walks away from the page gets a
slow answer, not a dead one.

It cannot be forged. The verdict is written by the interface into the session, never by a
tool argument, and a verdict with no pending request is discarded.
"""

import threading
import time

TIMEOUT_S = 45.0
ASK = "ask"
ALWAYS = "always"


def gate(session):
    """The gate is off unless something switched it on.

    A library that blocks by default is a trap: the evaluation suite, a script and a test
    all drive the agent with nobody watching, and none of them should wait 45 seconds per
    model call to find that out. The interface turns it on when it starts, which is the
    one context where there is a person to ask.
    """
    if session is None:
        return {"mode": ALWAYS, "pending": None}
    return session.setdefault(
        "approval", {"mode": ALWAYS, "pending": None, "verdict": None, "event": None}
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


def request(session, name, arguments):
    entry = gate(session)
    entry["pending"] = {
        "tool": name,
        "arguments": arguments or {},
        "description": describe(name, arguments),
        "asked_at": time.time(),
    }
    entry["verdict"] = None
    entry["event"] = threading.Event()
    return entry["pending"]


def pending(session):
    return gate(session).get("pending")


def decide(session, decision, arguments=None):
    """Called by the interface. Returns True when a request was actually waiting."""
    entry = gate(session)
    if not entry.get("pending"):
        return False
    if decision == ALWAYS:
        entry["mode"] = ALWAYS
        decision = "approve"
    entry["verdict"] = {"decision": decision, "arguments": arguments}
    event = entry.get("event")
    if event is not None:
        event.set()
    return True


def wait(session, timeout=TIMEOUT_S):
    """Block until the interface decides, or until the bound passes."""
    entry = gate(session)
    event = entry.get("event")
    answered = event.wait(timeout) if event is not None else False
    verdict = entry.get("verdict") or {}
    entry["pending"] = None
    entry["event"] = None
    entry["verdict"] = None
    if not answered:
        return {"decision": "timeout", "arguments": None}
    return {
        "decision": verdict.get("decision") or "approve",
        "arguments": verdict.get("arguments"),
    }


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
