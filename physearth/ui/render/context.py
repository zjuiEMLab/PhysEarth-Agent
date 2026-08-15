"""The research panel: where the plan stands, and what the agent is doing now."""

from physearth.ui.render.parts import _reproduction_state
from physearth.ui.render.review import approval_bar
from physearth.ui.render.text import _e


def research_context(session):
    """Render only the embedded research-plan/approval card.

    Capability and paper progress is rendered above Conversation, not as a persistent
    panel beside the composer.
    """
    from physearth import approval as gate

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

    capabilities = context.get("capabilities") or {}
    capability_cards = []
    for name, item in sorted(capabilities.items()):
        options = item.get("parameter_options") or {}
        theories = ", ".join(str(value) for value in options.get("electromagnetic_model", []))
        microstructures = ", ".join(str(value) for value in options.get("microstructure_model", []))
        outputs = ", ".join(str(value) for value in item.get("outputs") or []) or "not declared"
        status = "available here" if item.get("runnable_here") else "registered, unavailable here"
        reason = ""
        if not item.get("runnable_here"):
            reason = " The physical package is not installed in this environment."
        capability_cards.append(
            "<div class='research-capability'><b>%s v%s</b> · %s%s"
            "<br><span>Outputs: %s</span><br><span>Theories: %s</span>"
            "<br><span>Microstructures: %s</span></div>"
            % (
                _e(name),
                _e(item.get("version", "?")),
                _e(status),
                _e(reason),
                _e(outputs),
                _e(theories or "not declared"),
                _e(microstructures or "not declared"),
            )
        )
    capability_html = (
        "".join(capability_cards)
        if capability_cards
        else "<span class='badge badge--warn'>Capability check pending: the agent must call list_models.</span>"
    )
    instruction_names = sorted((context.get("instructions") or {}).keys())
    resource_note = (
        "Guideline read · model instruction read for %s · paper sections read%s"
        % (
            ", ".join(instruction_names) or "none yet",
            "" if context.get("paper_session") else " pending",
        )
    )
    capability_html = (
        "<section class='research-context__capability'><div class='research-context__label'>"
        "MODEL SUPPORT CHECK</div>%s<p class='research-context__resource'>%s</p></section>"
        % (capability_html, _e(resource_note))
    )
    paper_state = _reproduction_state(session)
    paper_status = ""
    if paper_state:
        paper_status = (
            "<section class='research-context__capability'><div class='research-context__label'>"
            "PAPER SESSION</div><p><b>Agent identified:</b> %s; source section %s; paper section %s.</p></section>"
            % (
                _e(paper_state.get("paper") or "pending"),
                _e(paper_state.get("source_section") or "pending"),
                _e(paper_state.get("paper_section") or "pending"),
            )
        )
    plan_html = approval_bar(session) if project or waiting else ""
    if not project and not waiting:
        plan_html = (
            "<p class='research-context__live-note'>The agent will read the required resources "
            "and generate the research plan after you send this question.</p>"
        )
    live_html = (
        "<section class='research-context__live'><div class='research-context__label'>"
        "LIVE RESEARCH STATUS</div>%s%s%s</section>"
        % (paper_status, capability_html, plan_html)
    )
    return (
        "<div class='research-context'><div class='research-context__head'>"
        "<span class='badge badge--model'>LIVE RESEARCH STATUS</span>"
        "<span class='research-context__hint'>The paper brief is at the top of the conversation</span>"
        "</div>%s</div>"
        % live_html
    )


def research_status(session):
    """Render the dynamic research status above the Conversation transcript."""
    from physearth import approval as gate

    session = session if isinstance(session, dict) else {}
    context = session.get("research_context") or {}
    project = session.get("research") or {}
    paper_state = _reproduction_state(session)
    waiting = gate.pending(session)
    if not project and not context.get("reproduction_case") and not paper_state and not waiting:
        return ""

    capabilities = context.get("capabilities") or {}
    capability_cards = []
    for name, item in sorted(capabilities.items()):
        options = item.get("parameter_options") or {}
        theories = ", ".join(str(value) for value in options.get("electromagnetic_model", []))
        microstructures = ", ".join(str(value) for value in options.get("microstructure_model", []))
        outputs = ", ".join(str(value) for value in item.get("outputs") or []) or "not declared"
        status = "available" if item.get("runnable_here") else "unavailable here"
        capability_cards.append(
            "<span class='conversation-research-status__model'><b>%s v%s</b> · %s · outputs: %s"
            " · theories: %s · microstructures: %s</span>"
            % (
                _e(name), _e(item.get("version", "?")), _e(status), _e(outputs),
                _e(theories or "not declared"), _e(microstructures or "not declared"),
            )
        )
    instruction_names = sorted((context.get("instructions") or {}).keys())
    resource_text = (
        "Guideline/model instruction: %s · paper evidence: %s"
        % (
            ", ".join(instruction_names) or "pending",
            "read" if context.get("paper_session") or session.get("sections_read") else "pending",
        )
    )
    paper_text = ""
    if paper_state:
        paper_text = " · paper: %s · section: %s" % (
            _e(paper_state.get("paper") or "pending"),
            _e(paper_state.get("paper_section") or paper_state.get("source_section") or "pending"),
        )
    phase = (project.get("phase") or "resource reading") if project else "resource reading"
    return (
        "<details class='conversation-research-status' data-key='conversation-research-status' open>"
        "<summary><span class='badge badge--model'>LIVE RESEARCH STATUS</span> · %s%s</summary>"
        "<div class='conversation-research-status__body'>"
        "<span class='conversation-research-status__label'>MODEL SUPPORT CHECK</span>"
        "<span>%s</span>%s</div></details>"
        % (_e(phase), paper_text, _e(resource_text), "".join(capability_cards))
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
