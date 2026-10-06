"""The conversation itself: the hero, the composer, one message, the guided brief."""

from apps.studio.views.context import current_activity_status
from apps.studio.views.parts import _reproduction_state, plan_sheet_html
from apps.studio.views.text import _e, _paragraphs, _svg, answer_html
from physearth.api import agent

PLACEHOLDER = (
    "Run a small SMRT pilot at 37 GHz for snow densities 1, 25, 50, 75 and 96 kg/m3, "
    "compare legal scattering configurations, and explain what the pilot cannot establish."
)


def hero(model_id=None, running=False, status=""):
    # The same fallback the agent applies to whatever the bridge sent. Without it the
    # switcher can show nothing selected while a real model is running.
    chosen = agent.resolve_model(model_id) if model_id else agent.default_model()
    buttons = "".join(
        "<button type='button' data-model='%s' class='%s' title='%s'>%s</button>"
        % (
            _e(item["id"]),
            "is-active" if item["id"] == chosen else "",
            _e("%s -- %s" % (item["id"], item["note"])),
            _e(item["label"]),
        )
        for item in agent.CATALOGUE
    )
    return (
        "<header class='hero'>"
        "<div class='hero-brand'>"
        "<svg class='hero-mark' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
        "stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'>"
        "<circle cx='12' cy='12' r='3.2'/><path d='M12 2v3.2M12 18.8V22M2 12h3.2M18.8 12H22"
        "M4.9 4.9l2.3 2.3M16.8 16.8l2.3 2.3M19.1 4.9l-2.3 2.3M7.2 16.8l-2.3 2.3'/></svg>"
        "<span class='hero-title'>PhysEarth-Agent</span>"
        "<span class='hero-sep'>/</span>"
        "<span class='hero-sub'>Trusted Geophysical Agent</span></div>"
        "<div class='hero-spacer'></div>"
        "<div class='hero-right'>"
        "<span class='status'><span class='status-dot'></span><span>%s</span></span>"
        "<div class='segment segment--model'>%s</div>"
        "<a class='tag' href='https://github.com/zjuiEMLab/PhysEarth-Agent' target='_blank' "
        "rel='noopener'>GitHub</a>"
        "</div></header>%s"
        % (
            _e(status or ("Running" if running else "Idle")),
            buttons,
            "<span data-running='1' hidden></span>" if running else "",
        )
    )


# ---------------------------------------------------------------- conversation


def conversation_head(count, session=None, events=None, state=None):
    # The suggestion rides on the head because the head is re-rendered on a phase
    # change, which is exactly when the suggestion changes. ui.js reads the attribute
    # and fills the composer only if it is empty and unfocused.
    running = bool(state) and state.get("phase") not in (None, "done")
    suggestion = "" if running else next_step(session, state)
    return (
        "<div class='subpanel' style='padding-bottom:0'%s><div class='sec-head'>%s"
        "<span class='sec-title'>Conversation</span>"
        "<span class='sec-count'>%d question%s</span></div></div>"
        "%s"
        % (
            " data-next-step='%s'" % _e(suggestion) if suggestion else "",
            _svg("chat", "sec-icon"),
            count,
            "" if count == 1 else "s",
            current_activity_status(session, events=events, state=state),
        )
    )


def _plan_run_rows(plan):
    """What differs between the plan's runs, whatever the model: the sheet's matrix."""
    matrix = plan_sheet_html(plan, conditions=False)
    return ("<div class='research-context__label'>AGENT PLAN: RUNS</div>" + matrix) if matrix else ""


def guided_brief(session):
    """The paper this session reproduces, and nothing of the plan.

    The plan's conditions, sources and runs are on the plan page the review card links to;
    repeating them here put a second, narrower copy of the plan above the conversation.
    """
    state = _reproduction_state(session)
    if not state:
        return ""
    doi = state["doi"]
    paper_link = (
        "<a href='https://doi.org/%s' target='_blank' rel='noopener'>Open DOI / paper source</a>"
        % _e(doi)
        if doi
        else ""
    )
    return (
        "<article class='guided-brief'><div class='guided-brief__head'>"
        "<span class='badge badge--model'>PAPER SESSION</span></div>"
        "<div class='guided-brief__body'>"
        "<h3>%s</h3><p><b>Section:</b> %s%s</p>"
        "<p><b>Research question:</b> %s</p>"
        "</div></article>"
        % (
            _e(state["title"]),
            _e(state["paper_section"] or state["source_section"] or "pending"),
            " · " + paper_link if paper_link else "",
            _e(state["question"] or "pending plan question"),
        )
    )


def history(turns, pending=False, session=None):
    """The session so far. It keeps growing until the visitor clears it.

    `pending` means a question is in flight. The opening hint belongs to an empty
    conversation, not to one that is busy answering its first question underneath it.
    """
    brief = guided_brief(session)
    if not turns:
        if pending:
            empty = "<div class='msg-group'></div>"
        else:
            empty = (
            "<div class='msg-group'><div class='pane-empty'>"
            "<div class='pane-empty__title'>Ask a question to begin</div>"
            "<div class='pane-empty__hint'>Every answer is checked against what the agent "
            "actually read and ran. The run trace in the middle shows each check, including "
            "the refusals.</div></div></div>"
            )
    else:
        out = []
        for turn in turns:
            out.append(_message("you", turn["question"], user=True))
            # A finished study keeps its full report in `answer`, which later turns send
            # to the model; what the conversation shows is `display`, its findings.
            out.append(
                _message(
                    "physearth",
                    turn.get("display") or turn["answer"],
                    faulted=turn.get("faulted"),
                    links=turn.get("links"),
                )
            )
        empty = "<div class='msg-group'>%s</div>" % "".join(out)
    return brief + empty


def _user_body(text):
    """Render long pasted revisions without collapsing their structure or trusting HTML."""
    text = str(text or "")
    lines = text.splitlines()
    structured = (
        len(lines) >= 8
        or "```" in text
        or any(line.lstrip().startswith(("format:", "plan_version:", "runs:", "charts:")) for line in lines)
    )
    if not structured:
        return _paragraphs(text)
    return (
        "<details class='msg-paste' open><summary>Pasted revision text · %d lines</summary>"
        "<pre>%s</pre></details>" % (len(lines), _e(text))
    )


def _links_html(links):
    """Download and open links under a message. Only URLs the interface wrote get here."""
    items = []
    for link in links or ():
        url = str(link.get("url") or "")
        if not url.startswith("/gradio_api/file="):
            continue
        download = link.get("download")
        items.append(
            "<a href='%s'%s>%s</a>"
            % (
                _e(url),
                " download='%s'" % _e(download) if download else " target='_blank' rel='noopener'",
                _e(link.get("label") or "Open"),
            )
        )
    return "<div class='report-downloads'>%s</div>" % "".join(items) if items else ""


def _message(who, text, user=False, running=False, faulted=False, links=None):
    # Render user text through the same small, escaped Markdown subset as answers. This
    # keeps long research questions readable and avoids exposing literal ** markers in the
    # conversation bubble.
    body = _user_body(text) if user else answer_html(text, running)
    note = (
        "<span class='badge badge--warn'>not an answer</span><span class='msg__rule'></span>"
        if faulted
        else "<span class='msg__rule'></span>"
    )
    return (
        "<div class='msg msg--%s%s'><div class='msg__head'>"
        "<span class='msg__who'>%s</span>%s</div>"
        "<div class='msg__body'>%s%s</div></div>"
        % (
            "user" if user else "agent", " msg--fault" if faulted else "", _e(who), note, body,
            _links_html(links),
        )
    )


def live(question, answer, running=False):
    """The turn in flight. Once it finishes it moves into the history and this empties."""
    if not question:
        return "<div class='msg-group'></div>"
    return "<div class='msg-group'>%s%s</div>" % (
        _message("you", question, user=True),
        _message("physearth", answer, running=running),
    )


def live_result(answer, running=False):
    """Render an internal continuation without adding a synthetic user bubble."""
    if not answer and not running:
        return "<div class='msg-group'></div>"
    return "<div class='msg-group'>%s</div>" % _message(
        "physearth", answer, running=running
    )

# What to type next, given where the session actually is. The gates themselves are
# buttons in the review card -- this is for the moments where the next move is a
# sentence, and the composer is empty because the turn just ended.
NEXT_STEP = {
    "completed": "Explain what this result does and does not establish, and what would "
    "make it stronger.",
    "approved": "Run the approved plan and report the result.",
    "chart_selected": "",
    "pseudo_preview": "",
    "plan_approved": "",
    # Empty on purpose: the plan card says what to type, and a prefilled sentence would
    # sit in the way of the one-word approval.
    "plan_review": "",
}


def next_step(session, state=None):
    """A suggested next message, or "" when the next move is not a message.

    Deliberately empty while a gate is open. If the interface is waiting for a decision
    on an approval card, putting a sentence in the composer invites the user to type
    past the thing that is actually blocking them.
    """
    session = session or {}
    capability = session.get("capability_review") or {}
    if capability.get("status") == "waiting_user":
        return ""
    project = session.get("research") or {}
    phase = project.get("phase")
    if phase == "completed" and project.get("scripts_offered"):
        # The last message asked whether to write the scripts; the composer stays empty
        # for the answer rather than suggesting a different question.
        return ""
    if phase in NEXT_STEP:
        return NEXT_STEP[phase]
    if session.get("research_required") and not project:
        return "Propose a research plan for this question."
    if session.get("turns"):
        return ""
    return ""
