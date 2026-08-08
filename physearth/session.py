"""Session-scoped state.

A turn is the wrong unit of memory. A section read while answering the first question
has to still resolve when the third answer cites it, or the citation check refuses a
marker the agent legitimately earned and the model is pushed into re-reading what it
already has. So the evidence sets, the result handles and the budget counters live in
one session object that the interface holds for the lifetime of a conversation, and
each turn gets a view over it.

The session is per visitor. Nothing here is module level, because one Studio process
serves every reviewer at once.
"""

import uuid

from physearth import config

MAX_MODEL_CALLS = config.nonnegative_int("PHYSEARTH_MAX_MODEL_CALLS")
MAX_TOOL_CALLS = config.nonnegative_int("PHYSEARTH_MAX_TOOL_CALLS")
MAX_SESSION_MODEL_CALLS = config.nonnegative_int("PHYSEARTH_MAX_SESSION_MODEL_CALLS")
MAX_SESSION_TOOL_CALLS = config.nonnegative_int("PHYSEARTH_MAX_SESSION_TOOL_CALLS")
CONTEXT_CEILING_TOKENS = 96000
MAX_HELD_HANDLES = 10
MAX_KEPT_HANDLES = 40
MAX_HELD_SECTIONS = 24

COUNTERS = (
    "model_calls",
    "tool_calls",
    "model_runs",
    "qc_failures",
    "rejected_calls",
    "interventions",
    "boundary_flags",
    "prompt_tokens",
    "completion_tokens",
)


def new_session(model=None):
    session = {
        "id": "ses_" + uuid.uuid4().hex[:12],
        "model": model,
        "turns": 0,
        "sections_read": set(),
        "models_run": set(),
        "datasets_read": set(),
        "skills_read": set(),
        "abstracts_seen": set(),
        "figures": [],
        "successful_runs": [],
        "evidence_revision": 0,
        "handles": [],
        "corpus": {},
        "abstracts": {},
        "research": None,
        "max_model_calls": MAX_SESSION_MODEL_CALLS,
        "max_tool_calls": MAX_SESSION_TOOL_CALLS,
    }
    session.update({name: 0 for name in COUNTERS})
    return session


def new_state(session=None, model=None):
    """A turn's view. Evidence containers are the session's; counters start at zero."""
    session = new_session(model) if session is None else session
    state = {
        "session": session,
        "model": model or session.get("model"),
        "phase": "idle",
        "max_model_calls": MAX_MODEL_CALLS,
        "max_tool_calls": MAX_TOOL_CALLS,
        "context_ceiling": CONTEXT_CEILING_TOKENS,
        "sections_read": session["sections_read"],
        "models_run": session["models_run"],
        "datasets_read": session["datasets_read"],
        "skills_read": session["skills_read"],
        "abstracts_seen": session["abstracts_seen"],
        "figures": [],
    }
    state.update({name: 0 for name in COUNTERS})
    return state


def bump(state, name, amount=1):
    """Move a counter in the turn and in the session it belongs to."""
    # prompt_tokens is the size of one request, not a consumable conversation budget.
    # Summing it across tool rounds made the UI report a fake context exhaustion even
    # when every individual request was still within the model's context window.
    if name == "prompt_tokens":
        state[name] = max(state.get(name, 0), amount)
    else:
        state[name] = state.get(name, 0) + amount
    session = state.get("session")
    if session is not None:
        if name == "prompt_tokens":
            session[name] = max(session.get(name, 0), amount)
        else:
            session[name] = session.get(name, 0) + amount


def remember_figure(state, figure):
    session = state.get("session")
    if session is None:
        state["figures"].append(figure)
        return

    figures = session["figures"]
    chart_id = figure.get("planned_chart_id")
    replace_at = next(
        (
            index for index, existing in enumerate(figures)
            if chart_id and existing.get("planned_chart_id") == chart_id
            and not existing.get("preview")
        ),
        None,
    )
    if replace_at is not None:
        figure["figure_number"] = figures[replace_at].get("figure_number")
        figures[replace_at] = figure
    else:
        if not figure.get("preview"):
            figure["figure_number"] = figure.get("figure_number") or 1 + sum(
                1 for existing in figures if not existing.get("preview")
            )
        figures.append(figure)
    state["figures"] = [
        existing for existing in state["figures"]
        if not chart_id or existing.get("planned_chart_id") != chart_id
    ]
    state["figures"].append(figure)
    session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1


def remember_handle(state, handle, line):
    session = state.get("session")
    if session is None or not handle:
        return
    session["handles"] = [item for item in session["handles"] if item["handle"] != handle]
    session["handles"].append({"handle": handle, "line": line})
    while len(session["handles"]) > MAX_KEPT_HANDLES:
        session["handles"].pop(0)


def held_block(session):
    """What the session already has, so the model reuses it instead of recomputing it.

    Bounded on both axes: only the newest handles and a capped list of sections reach
    the prompt. What drops out of this text stays in the session, so a marker for it
    still resolves.
    """
    if session is None or not session.get("turns"):
        return ""
    lines = []
    sections = sorted(session["sections_read"])
    if sections:
        shown = sections[-MAX_HELD_SECTIONS:]
        more = len(sections) - len(shown)
        lines.append(
            "Sections already read: %s%s."
            % (", ".join(shown), " and %d more" % more if more else "")
        )
    if session["models_run"]:
        lines.append("Models already run or declared: %s." % ", ".join(sorted(session["models_run"])))
    if session["datasets_read"]:
        lines.append("Reference datasets already read: %s." % ", ".join(sorted(session["datasets_read"])))
    if session["skills_read"]:
        lines.append("Method notes already read: %s." % ", ".join(sorted(session["skills_read"])))
    ingested = session.get("corpus") or {}
    if ingested:
        lines.append(
            "Papers taken into this conversation, readable and citable like the bundled "
            "ones: %s."
            % ", ".join("%s (%s)" % (slug, item["doi"]) for slug, item in ingested.items())
        )
    if session["abstracts_seen"]:
        lines.append(
            "Abstracts seen, citable as [abs:doi] and never for a value: %s."
            % ", ".join(sorted(session["abstracts_seen"])[:8])
        )
    if session.get("research"):
        project = session["research"]
        plan = project.get("plan") or {}
        charts = plan.get("charts") or []
        parameters = plan.get("parameters") or {}
        parameter_text = ", ".join(
            "%s=%s" % (key, parameters[key]) for key in sorted(parameters)[:16]
        ) or "none recorded"
        chart_text = "; ".join(
            "%s: %s (%s -> %s)"
            % (chart.get("id"), chart.get("label"), chart.get("x"), chart.get("y"))
            for chart in charts[:8]
        ) or "none recorded"
        selected = project.get("selected_chart") or {}
        selected_ids = project.get("selected_charts") or ([selected.get("id")] if selected else [])
        run_ids = ", ".join(
            str(run.get("id")) for run in (plan.get("runs") or []) if run.get("id")
        ) or "none"
        lines.append(
            "Research workflow: plan v%03d, phase %s. Objective: %s. Parameters: %s. "
            "Approved run IDs: %s. Chart choices: %s. Confirmed chart package: %s. Formal model calls remain blocked until "
            "the required human UI approvals are recorded; never approve a gate yourself."
            % (
                project.get("plan_version", 1),
                project.get("phase"),
                plan.get("objective") or "not recorded",
                parameter_text,
                run_ids,
                chart_text,
                ", ".join(selected_ids) or "none",
            )
        )
    handles = session["handles"][-MAX_HELD_HANDLES:]
    if handles:
        lines.append("Live result handles, oldest first:")
        lines.extend("  %s -- %s" % (item["handle"], item["line"]) for item in handles)
    if not lines:
        return ""
    return (
        "Already held in this conversation. Every marker below resolves without fetching "
        "anything again, and every handle can go straight into plot. Do not re-read a section "
        "or re-run a configuration that is already here unless you need something it does not "
        "cover.\n\n%s" % "\n".join(lines)
    )


def clear(session):
    """Wipe a session in place. The hourly deployment quota is deliberately untouched."""
    fresh = new_session(session.get("model"))
    fresh["id"] = session.get("id") or fresh["id"]
    session.clear()
    session.update(fresh)
    return session
