"""The research panel: where the plan stands, and what the agent is doing now."""

from frontend.views.parts import _reproduction_state
from frontend.views.review import approval_bar
from frontend.views.text import _e


def research_context(session):
    """Render only the embedded research-plan/approval card.

    Capability and paper progress is rendered above Conversation, not as a persistent
    panel beside the composer.
    """
    from physearth.api import approval as gate

    session = session if isinstance(session, dict) else {}
    project = session.get("research") or {}
    waiting = gate.pending(session)
    if session.get("approval_resuming") and waiting and not project:
        # ``review_click`` signals the waiting agent before approval.wait() clears the
        # pending request. Do not leave the already-approved call on screen during that
        # small hand-off window; the next generator frame will render a genuinely pending
        # second single-run request, if one exists.
        return "<div class='research-context' hidden></div>"
    if not project and not waiting:
        return "<div class='research-context' hidden></div>"
    return (
        "<div class='research-context'>%s</div>"
        % approval_bar(session)
    )


def current_activity_status(session, events=None, state=None):
    """Render only the latest model/tool activity above the transcript."""
    session = session if isinstance(session, dict) else {}
    events = events or []
    state = state if isinstance(state, dict) else {}
    event = events[-1] if events else {}
    kind = event.get("kind")
    if kind == "model_call":
        activity = "Model call"
    elif kind in ("tool_start", "tool_call"):
        activity = "Tool call%s" % (
            " · %s" % event.get("name") if event.get("name") else ""
        )
    elif kind == "approval_wait":
        activity = "Waiting for approval"
    elif kind in ("harness_block", "research_block", "harness_stop"):
        activity = "Validation stopped"
    elif kind == "research_mode_selected":
        activity = "Research mode selected"
    elif state.get("phase") == "running_tool":
        activity = "Tool call"
    elif state.get("phase") == "calling_model":
        activity = "Model call"
    elif (session.get("research") or {}).get("phase") == "plan_review":
        activity = "Waiting for plan review"
    else:
        activity = "Idle"
    return (
        "<div class='conversation-research-status' data-key='conversation-research-status' "
        "role='status' aria-live='polite'>"
        "<span class='badge badge--model'>LIVE RESEARCH STATUS</span>"
        "<span class='conversation-research-status__activity'>%s</span></div>"
        % _e(activity)
    )
