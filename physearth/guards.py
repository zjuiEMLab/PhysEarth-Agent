"""Loop-hygiene guards for the agent loop.

The most expensive failure this project observes is not a wrong answer but a turn that
keeps working without changing anything: the model calls the same tool with the same
arguments after the result has already answered its question, or it rewrites an
equivalent proposal that the harness rejects for the same reason again.

The guard here is advisory, deliberately.  It never blocks or rewrites a call; it adds a
message that names the repetition so the model can change approach, gather different
evidence, or finish with what it has.  Escalation is by threshold (3, 5, 8 by default):
the first reminder is short, later ones quote the repeated call.  Only when the chain
outlives the last threshold does the loop treat it as no progress and stop, which keeps
the hard stop as a backstop instead of the first response to a repeat.

Identity is the canonical rendering of the arguments: sorted keys, no insignificant
whitespace, so two calls that differ only in key order or number formatting count as one
chain, and any real change starts a new one.  Counting lives in the session rather than
in one turn, because a research question is usually advanced over several turns and a
per-turn counter would let the same loop restart for free after every user message.
"""

import fnmatch
import json

from physearth import config

DEFAULT_THRESHOLDS = (3, 5, 8)
DEFAULT_PREVIEW_CHARS = 500
STATE_KEY = "guard_repeats"


def _thresholds():
    raw = config.get("PHYSEARTH_REPEAT_GUARD_THRESHOLDS")
    values = []
    for item in str(raw or "").split(","):
        item = item.strip()
        if not item:
            continue
        try:
            value = int(item)
        except ValueError:
            continue
        if value >= 2:
            values.append(value)
    unique = sorted(set(values))
    return tuple(unique) if unique else DEFAULT_THRESHOLDS


def _patterns(name):
    raw = config.get("PHYSEARTH_REPEAT_GUARD_" + name)
    return tuple(item.strip() for item in str(raw or "").split(",") if item.strip())


def preview_chars():
    try:
        value = int(config.get("PHYSEARTH_REPEAT_GUARD_PREVIEW_CHARS") or DEFAULT_PREVIEW_CHARS)
    except (TypeError, ValueError):
        return DEFAULT_PREVIEW_CHARS
    return value if value > 0 else DEFAULT_PREVIEW_CHARS


def hard_stop_count():
    """How many identical calls the loop tolerates before it treats them as no progress.

    The guard spends its reminders first, so the hard stop sits one call past the last
    threshold.
    """
    return max(_thresholds()) + 1


def _normalise_values(value):
    """Render numbers by value, not by the literal the provider happened to emit.

    A tool call whose JSON says ``2.0`` and one that says ``2`` are the same call, and an
    argument order difference is not a different call either.  Normalising integral floats
    before serialisation keeps those from starting a new chain, while booleans stay
    booleans (``True`` is not the number 1).
    """
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {str(key): _normalise_values(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise_values(item) for item in value]
    return value


def canonical_arguments(arguments):
    """Deterministic identity for one call's arguments.

    The tool layer admits JSON-serializable dictionaries, so a sorted, value-normalised
    rendering is a complete identity for them: key order, whitespace and an integral float
    written as ``2.0`` cannot create a false "new" call, and any changed value produces a
    different chain.
    """
    if arguments is None:
        return "{}"
    try:
        return json.dumps(
            _normalise_values(arguments), sort_keys=True, ensure_ascii=False, default=str
        )
    except (TypeError, ValueError):
        return json.dumps(str(arguments), ensure_ascii=False)


def preview(text, cap=None):
    """Head-truncate the canonical arguments quoted in a detailed reminder."""
    cap = preview_chars() if cap is None else cap
    if len(text) <= cap:
        return text
    return "%s… (+%d more chars)" % (text[:cap], len(text) - cap)


def excluded(tool):
    return any(fnmatch.fnmatch(str(tool or ""), pattern) for pattern in _patterns("EXCLUDE"))


def included(tool):
    patterns = _patterns("INCLUDE")
    if not patterns:
        return True
    return any(fnmatch.fnmatch(str(tool or ""), pattern) for pattern in patterns)


def reset(session):
    """Clear the repeat chain. A new user question is never a continuation of a loop."""
    if session is None:
        return
    session.pop(STATE_KEY, None)


def observe(session, tool, arguments):
    """Count one executed call and return a reminder when a threshold is crossed.

    Excluded tools neither count nor reset the chain, so bookkeeping calls cannot hide a
    loop that is happening around them.  Returns ``None`` when no reminder is due.
    """
    if session is None or not included(tool) or excluded(tool):
        return None
    signature = "%s|%s" % (tool, canonical_arguments(arguments))
    state = session.get(STATE_KEY)
    if not isinstance(state, dict) or state.get("signature") != signature:
        state = {"signature": signature, "tool": tool, "count": 0, "reminded": []}
    state["count"] = int(state.get("count") or 0) + 1
    reminded = list(state.get("reminded") or [])
    thresholds = _thresholds()
    crossed = [
        value for value in thresholds
        if state["count"] >= value and value not in reminded
    ]
    session[STATE_KEY] = state
    if not crossed:
        return None
    threshold = max(crossed)
    reminded.extend(crossed)
    state["reminded"] = reminded
    canonical = canonical_arguments(arguments)
    if threshold == thresholds[0]:
        reminder = (
            "You have now called %s with identical arguments %d times. Read the result you "
            "already have before calling it again: change an argument, use a different tool, "
            "or finish with the evidence in hand."
            % (tool, state["count"])
        )
    else:
        reminder = (
            "You have called %s with identical arguments %d times. Repeating the exact call "
            "cannot produce a different result, so the loop is not making progress. "
            "Repeated arguments: %s\nEither change the approach (different parameters, model "
            "or tool), name what is blocking you and what you need, or report the partial "
            "result and stop."
            % (tool, state["count"], preview(canonical))
        )
    return {
        "rule": "repeat_tool_reminder",
        "tool": tool,
        "count": state["count"],
        "threshold": threshold,
        "detail": reminder,
    }
