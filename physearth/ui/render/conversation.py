"""The conversation itself: the hero, the composer, one message, the guided brief."""

from physearth import agent
from physearth.ui.render.context import current_activity_status
from physearth.ui.render.parts import _mapping_text, _reproduction_state
from physearth.ui.render.text import _e, _paragraphs, _svg, answer_html

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
    return (
        "<div class='subpanel' style='padding-bottom:0'><div class='sec-head'>%s"
        "<span class='sec-title'>Conversation</span>"
        "<span class='sec-count'>%d question%s</span></div></div>"
        "%s"
        % (
            _svg("chat", "sec-icon"),
            count,
            "" if count == 1 else "s",
            current_activity_status(session, events=events, state=state),
        )
    )


def _plan_run_rows(plan):
    rows = []
    for run in plan.get("runs") or []:
        spec = run.get("parameters") or {}
        theory = spec.get("electromagnetic_model", "")
        microstructure = spec.get("microstructure_model", "")
        output = spec.get("output", "")
        sweep = spec.get("sweep_parameter", "")
        rows.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (
                _e(run.get("id", "")),
                _e(run.get("label", "%s + %s" % (theory, microstructure))),
                _e(theory),
                _e(microstructure),
                _e("%s; sweep %s" % (output or "not specified", sweep or "none")),
            )
        )
    if not rows:
        return ""
    return (
        "<div class='research-context__label'>AGENT PLAN: RUNS</div>"
        "<table class='research-plan-runs'><thead><tr><th>ID</th><th>Run</th>"
        "<th>Theory</th><th>Microstructure</th><th>Output</th></tr></thead><tbody>%s</tbody></table>"
        % "".join(rows)
    )


def guided_brief(session):
    """Render agent-discovered paper state and the later agent-authored plan."""
    state = _reproduction_state(session)
    if not state:
        return ""
    plan = state["plan"]
    doi = state["doi"]
    paper_link = (
        "<a href='https://doi.org/%s' target='_blank' rel='noopener'>Open DOI / paper source</a>"
        % _e(doi)
        if doi
        else ""
    )
    source_fixed = plan.get("paper_conditions") or {}
    provenance = plan.get("condition_provenance") or {}
    plan_params = plan.get("parameters") or {}
    extra_params = {key: value for key, value in plan_params.items() if key not in source_fixed}
    assumptions = plan.get("assumptions") or []
    source_html = (
        "<p><b>From paper sections:</b> %s</p>"
        % _e(_mapping_text(source_fixed) or "not declared yet")
    )
    assumption_text = _mapping_text(extra_params)
    if assumptions:
        assumption_text = "; ".join(filter(None, [assumption_text] + [str(item) for item in assumptions]))
    assumption_html = (
        "<p><b>Agent/model assumptions to review:</b> %s</p>"
        % _e(assumption_text or "none declared outside the generated protocol")
    )
    provenance_html = (
        "<p><b>Condition evidence:</b> %s</p>"
        % _e(_mapping_text(provenance) or "not declared; review against the paper sections")
    )
    expected = list(plan.get("quantities") or [])
    for chart in plan.get("charts") or []:
        expected.extend(chart.get("ys") or ([chart.get("y")] if chart.get("y") else []))
    expected = list(dict.fromkeys(str(item) for item in expected))
    plan_html = ""
    if plan:
        plan_html = (
            _plan_run_rows(plan)
            + "<div class='research-context__label'>AGENT PLAN: EXPECTED OUTPUTS</div>"
            + "<p><b>Plan-declared quantities and chart outputs:</b> %s</p>"
            % _e(", ".join(expected) or "not specified")
        )
    return (
        "<article class='guided-brief'><div class='guided-brief__head'>"
        "<span class='badge badge--model'>PAPER SESSION · AGENT DISCOVERED</span>"
        "<span class='guided-brief__hint'>Plan values remain editable</span></div>"
        "<div class='guided-brief__body'><div class='research-context__label'>PAPER SESSION</div>"
        "<h3>%s</h3><p><b>Protocol:</b> %s; <b>Paper section:</b> %s%s</p>"
        "<p><b>Research question:</b> %s</p>"
        "<div class='research-context__label'>CONDITION PROVENANCE</div>%s%s%s%s"
        "</div></article>"
        % (
            _e(state["title"]),
            _e(state["source_section"] or "pending"),
            _e(state["paper_section"] or "pending"),
            " · " + paper_link if paper_link else "",
            _e(state["question"] or "pending plan question"),
            source_html,
            assumption_html,
            provenance_html,
            plan_html,
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
            out.append(_message("physearth", turn["answer"], faulted=turn.get("faulted")))
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


def _message(who, text, user=False, running=False, faulted=False):
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
        "<div class='msg__body'>%s</div></div>"
        % ("user" if user else "agent", " msg--fault" if faulted else "", _e(who), note, body)
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
