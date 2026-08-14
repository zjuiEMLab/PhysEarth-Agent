"""Every pixel of the interface, as plain strings.

Nothing here imports Gradio, so all of it is testable without a browser. Every value
that reaches the page goes through `html.escape` first: literature text, dataset rows
and model output are all untrusted input on a public deployment.
"""

import html
import json
import re

from physearth import agent, budget, knowledge, reference
from physearth import live as literature
from physearth.models import registry

CITE = re.compile(r"\[([a-z0-9][a-z0-9-]*)#(\d{1,3})\]")
MODEL_CITE = re.compile(r"\[model:([A-Za-z0-9_-]+)@([^\]\s]+)\]")
DATA_CITE = re.compile(r"\[data:([a-z0-9][a-z0-9-]*)\]")
ABS_CITE = re.compile(r"\[abs:(10\.\d{4,9}/[^\]\s]+)\]", re.I)
SKILL_CITE = re.compile(r"\[skill:([a-z0-9][a-z0-9-]*)\]")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
CODE = re.compile(r"`([^`]+)`")
SAFE_SUB = re.compile(r"&lt;(/?)(sub|sup)&gt;", re.I)
SECTION_PREVIEW_CHARS = 620

# The composer's own greyed-out text, in place of a row of preset buttons. It is one
# question and nothing else: a visitor who types over it should be replacing a sentence,
# not editing an instruction. It shows without being told that a question here names a
# configuration and asks for a run rather than for an explanation.
PLACEHOLDER = (
    "Run a small SMRT pilot at 37 GHz for snow densities 1, 25, 50, 75 and 96 kg/m3, "
    "compare legal scattering configurations, and explain what the pilot cannot establish."
)

ICONS = {
    "chat": "<path d='M21 11.5a8.4 8.4 0 0 1-9 8.4 9.9 9.9 0 0 1-4.2-.9L3 20.5l1.5-4.4A8.4 8.4 "
    "0 0 1 12 3.1a8.4 8.4 0 0 1 9 8.4z'/>",
    "trace": "<path d='M4 20V10M10 20V4M16 20v-7M22 20H2'/>",
    "figure": "<path d='M3 3v18h18'/><path d='M6 15l4-5 3 3 5-7'/>",
    "sources": "<path d='M4 4.5A1.5 1.5 0 0 1 5.5 3H19v18H5.5A1.5 1.5 0 0 1 4 19.5z'/>"
    "<path d='M8 7.5h7M8 11h7'/>",
    "models": "<path d='M12 2.5l8 4.5v9l-8 4.5-8-4.5v-9z'/><path d='M12 11.5l8-4.5M12 11.5v9"
    "M12 11.5L4 7'/>",
    "check": "<path d='M4 12.5l5.2 5.2L20 7'/>",
    "block": "<circle cx='12' cy='12' r='9'/><path d='M6 6l12 12'/>",
}


def _svg(name, cls):
    return (
        "<svg class='%s' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
        "stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'>%s</svg>"
        % (cls, ICONS[name])
    )


def _e(value):
    return html.escape(str(value), quote=True)


def _mono(value):
    return "<span class='mono'>%s</span>" % _e(value)


# ---------------------------------------------------------------- answer text


def _markers(text):
    """Turn the four marker forms into chips that jump to the evidence they name."""

    # Every closure below runs over text that _inline has already escaped, so none of
    # them escapes again: a second pass turns an ampersand inside a DOI into &amp;amp;.
    def section(match):
        key = "%s#%s" % (match.group(1), match.group(2))
        return (
            "<a class='cite' href='#' data-jump='sec-%s' data-tab='pe-tab-sources'>%s</a>"
            % (key, key)
        )

    def model(match):
        key = "%s@%s" % (match.group(1), match.group(2))
        return (
            "<a class='cite cite--model' href='#' data-jump='model-%s' "
            "data-tab='pe-tab-models'>%s</a>" % (match.group(1), key)
        )

    def data(match):
        slug = match.group(1)
        return (
            "<a class='cite cite--data' href='#' data-jump='data-%s' "
            "data-tab='pe-tab-sources'>%s</a>" % (slug, slug)
        )

    def abstract(match):
        doi = match.group(1)
        return (
            "<a class='cite cite--abs' href='#' data-jump='abs-%s' "
            "data-tab='pe-tab-sources' title='abstract level: metadata only, never a "
            "measured or computed value'>abs:%s</a>" % (doi, doi)
        )

    def skill(match):
        slug = match.group(1)
        return (
            "<a class='cite cite--skill' href='#' data-jump='sec-%s#00' "
            "data-tab='pe-tab-sources' title='the agent opened this method note before "
            "writing this sentence'>%s</a>" % (slug, slug)
        )

    # The abstract form goes first: some DOIs would otherwise be eaten by the model pattern.
    text = ABS_CITE.sub(abstract, text)
    text = SKILL_CITE.sub(skill, text)
    text = CITE.sub(section, text)
    text = MODEL_CITE.sub(model, text)
    return DATA_CITE.sub(data, text)


def _paragraphs(text):
    blocks = []
    for raw in re.split(r"\n\s*\n", text.strip()):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            continue
        if len(lines) == 1:
            heading = re.match(r"^(#{1,3})\s+(.+)$", lines[0])
            if heading:
                level = len(heading.group(1))
                blocks.append(
                    "<h%d>%s</h%d>" % (level, _inline(heading.group(2)), level)
                )
                continue
        if all(line.startswith(("- ", "* ")) for line in lines):
            items = "".join("<li>%s</li>" % _inline(line[2:]) for line in lines)
            blocks.append("<ul>%s</ul>" % items)
        else:
            blocks.append("<p>%s</p>" % _inline(" ".join(lines)))
    return "".join(blocks)


def answer_html(text, running=False):
    """Escape first, then apply a deliberately small markdown subset.

    A turn can hold several stretches of prose, one before each round of tool calls. They
    arrive separated by the agent's segment break and are drawn as successive blocks, so a
    later thought lands underneath the earlier one instead of replacing it.
    """
    text = text or ""
    if not text.strip():
        return "<p class='hint'>Waiting for the first token.</p>" if running else ""
    segments = [part for part in text.split(agent.SEGMENT_BREAK) if part.strip()]
    body = "".join(
        "<div class='seg%s'>%s</div>"
        % (" seg--later" if n else "", _paragraphs(part))
        for n, part in enumerate(segments)
    )
    if running:
        body += "<span class='caret'></span>"
    return body


def _inline(text):
    out = _e(text)
    out = CODE.sub(lambda m: "<code>%s</code>" % m.group(1), out)
    out = BOLD.sub(lambda m: "<b>%s</b>" % m.group(1), out)
    # Allow only the two typographic equation tags after escaping. Attributes and every
    # other HTML tag remain escaped, so model output cannot inject markup or scripts.
    out = SAFE_SUB.sub(lambda m: "<%s%s>" % (m.group(1), m.group(2).lower()), out)
    return _markers(out)


# ---------------------------------------------------------------- hero


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


def _reproduction_state(session):
    """Return paper state discovered through literature reads and the generated plan."""
    session = session if isinstance(session, dict) else {}
    context = session.get("research_context") or {}
    project = session.get("research") or {}
    plan = project.get("plan") or {}
    case_id = context.get("reproduction_case") or plan.get("reproduction_case")
    paper_session = context.get("paper_session") or {}
    if not case_id and not paper_session and not plan:
        return None
    paper_slug = paper_session.get("paper") or ""
    card = knowledge.card(paper_slug) if paper_slug else {}
    paper_section = paper_session.get("paper_section") or ""
    source_section = paper_session.get("source_section") or ""
    if case_id:
        try:
            from physearth import reproduction

            case = reproduction.CASES.get(case_id) or {}
            paper_section = paper_section or case.get("paper_section", "")
            source_section = source_section or case.get("section", "")
        except (ImportError, KeyError, TypeError):
            pass
    return {
        "case_id": case_id,
        "paper_session": paper_session,
        "plan": plan,
        "question": project.get("question") or context.get("question") or "",
        "paper": paper_slug,
        "title": card.get("title") or paper_session.get("title") or paper_slug,
        "doi": card.get("doi") or paper_session.get("doi") or "",
        "paper_section": paper_section,
        "source_section": source_section,
    }


def _mapping_text(mapping):
    return ", ".join(
        "%s=%s" % (key, value) for key, value in sorted((mapping or {}).items())
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


# ---------------------------------------------------------------- run trace


BADGES = {
    "model_call": ("badge--mono", "MODEL CALL", "step-card--model"),
    "tool_call": ("badge--model", "TOOL", "step-card--tool"),
    "tool_start": ("badge--step", "RUNNING", "step-card--thinking"),
    "harness_block": ("badge--block", "BLOCKED", "step-card--block"),
    "harness_warning": ("badge--warn", "WARNING", "step-card--warn"),
    "harness_pass": ("badge--ok", "PASSED", "step-card--pass"),
    "harness_stop": ("badge--warn", "STOPPED", "step-card--warn"),
    "harness_giveup": ("badge--warn", "GAVE UP", "step-card--warn"),
    "harness_fallback": ("badge--warn", "SAFE FALLBACK", "step-card--warn"),
    "untrusted_content": ("badge--warn", "BOUNDARY", "step-card--warn"),
    "empty_response": ("badge--mute", "UPSTREAM RETRY", "step-card--muted"),
    "literature_tier": ("badge--model", "LITERATURE TIER", "step-card--tool"),
    "protocol": ("badge--ok", "PROTOCOL", "step-card--pass"),
    "approval_wait": ("badge--warn", "WAITING FOR YOU", "step-card--warn"),
    "approval": ("badge--ok", "APPROVAL", "step-card--pass"),
    "research_wait": ("badge--warn", "RESEARCH REVIEW", "step-card--warn"),
    "research_revision": ("badge--ok", "PLAN REVISED", "step-card--pass"),
    "research_block": ("badge--block", "RESEARCH GATE", "step-card--block"),
    "research_complete": ("badge--passed", "RESEARCH COMPLETE", "step-card--passed"),
    "tool_bypass_requested": ("badge--warn", "TOOLS DISABLED", "step-card--warn"),
    "tool_bypass_blocked": ("badge--block", "SAFE REFUSAL", "step-card--block"),
}

APPROVAL_WORDS = {
    "approve": "You approved this call.",
    "reject": "You declined this call. The refusal went back to the model as a tool result, "
    "so it has to answer without it or propose something different.",
    "timeout": "Nobody answered within the time limit, so the call went ahead. This is "
    "recorded here because an unanswered gate is not the same as an approved one.",
}


def _kv(rows):
    body = "".join(
        "<dt>%s</dt><dd class='%s'>%s</dd>" % (_e(k), cls, _e(v)) for k, v, cls in rows
    )
    return "<dl class='kv'>%s</dl>" % body


def _disclosure(key, label, text):
    return (
        "<details class='disclosure' data-key='%s'><summary>%s</summary><pre>%s</pre></details>"
        % (_e(key), _e(label), _e(text))
    )


def _event_body(event, index):
    kind = event["kind"]
    if kind == "research_revision":
        return (
            "<div class='step-card__line'>%s</div>"
            % _e(event.get("detail") or "The research plan was revised and returned to review.")
        )
    if kind == "model_call":
        rows = [
            (
                "tokens",
                "%s in / %s out"
                % (event.get("prompt_tokens") or "?", event.get("completion_tokens") or "?"),
                "",
            )
        ]
        if event.get("reasoning_chars"):
            rows.append(("reasoning", "%d characters, not shown" % event["reasoning_chars"], ""))
        return _kv(rows)

    if kind == "tool_call":
        lines = ["<div class='step-card__line'>%s</div>" % _e(event["summary"])]
        data = event.get("data") or {}
        rows = []
        if data.get("handle"):
            rows.append(("handle", data["handle"], ""))
        if event.get("qc") is not None:
            rows.append(
                (
                    "qc",
                    "declared units, range, missing values and axis alignment all checked",
                    "good" if event["qc"] else "bad",
                )
            )
        if rows:
            lines.append(_kv(rows))
        lines.append(
            _disclosure(
                "args-%d" % index,
                "arguments",
                json.dumps(event["arguments"], ensure_ascii=False, indent=1),
            )
        )
        return "".join(lines)

    if kind == "harness_block":
        lines = [
            "<div class='step-card__line'>%s</div>"
            % _e(
                "The call was refused before it ran. The reason went back to the model as a "
                "structured tool result."
                if event.get("tool")
                else "The answer was refused and sent back for correction."
            )
        ]
        problems = event.get("problems") or []
        if problems:
            lines.append(
                "".join(
                    "<div class='step-card__line'><span class='k'>%d</span>%s</div>"
                    % (n, _e(problem))
                    for n, problem in enumerate(problems[:4], 1)
                )
            )
        elif event.get("unresolved"):
            lines.append(
                "<div class='step-card__line'>These markers resolve to nothing: %s</div>"
                % ", ".join(_mono(m) for m in event["unresolved"][:6])
            )
        else:
            lines.append("<div class='step-card__line'>%s</div>" % _e(event.get("detail") or ""))
        return "".join(lines)

    if kind == "harness_warning":
        return (
            "<div class='step-card__line'>The report was delivered, but this advisory finding "
            "may improve its scientific completeness:</div>"
            "<div class='step-card__line'>%s</div>" % _e(event.get("detail") or "")
        )

    if kind == "harness_pass":
        markers = sorted(set(event.get("markers") or []))
        chips_html = (
            "".join("<span class='badge badge--mono'>%s</span>" % _e(m) for m in markers)
            or "<span class='badge badge--mute'>no markers to check</span>"
        )
        return (
            "<div class='step-card__line'>Every marker in the answer resolves to something "
            "done in this conversation.</div><div class='marker-list'>%s</div>" % chips_html
        )

    if kind == "untrusted_content":
        return (
            "<div class='step-card__line'>A passage in the retrieved source reads like an "
            "instruction. External content is evidence, never a command, and cannot trigger a "
            "tool call.</div>%s" % _disclosure("ext-%d" % index, "excerpt", event.get("detail", ""))
        )

    if kind == "approval_wait":
        from physearth import approval as gate

        described = gate.describe(event.get("name"), event.get("arguments"))
        rows = [(k, v, "") for k, v in sorted(described["parameters"].items())]
        return (
            "<div class='step-card__line'>The agent wants to run <b>%s</b> as %s. Nothing "
            "has been computed yet. Approve it, decline it, or let the time limit pass.</div>"
            "%s" % (_e(described["model"]), _e(described["shape"]), _kv(rows) if rows else "")
        )

    if kind == "approval":
        return "<div class='step-card__line'>%s</div>" % _e(
            APPROVAL_WORDS.get(event.get("decision"), event.get("decision") or "")
        )

    if kind == "tool_bypass_requested":
        return (
            "<div class='step-card__line'>The user explicitly asked the agent not to use "
            "evidence or model tools.</div>"
        )

    if kind == "tool_bypass_blocked":
        return (
            "<div class='step-card__line'>No tool was called. The request was refused because "
            "a scientific model claim cannot be verified with the required tools disabled.</div>"
        )

    if kind == "tool_start":
        return (
            "<div class='step-card__line thinking-dots'>"
            "<span></span><span></span><span></span></div>"
        )

    if kind in ("empty_response", "harness_stop") and event.get("upstream"):
        return "%s%s" % (
            "<div class='step-card__line'>%s on %s</div>"
            % (_e(event.get("detail") or event.get("reason") or ""), _mono(event.get("model", ""))),
            _disclosure("upstream-%d" % index, "what the endpoint said", event["upstream"]),
        )

    detail = event.get("reason") or event.get("detail") or ""
    return "<div class='step-card__line'>%s</div>" % _e(detail)


def _event_card(event, index):
    badge_class, badge_text, card_class = BADGES.get(
        event["kind"], ("badge--mute", event["kind"].upper(), "step-card--muted")
    )
    icon = ""
    if event["kind"] == "harness_block":
        icon = _svg("block", "")
    elif event["kind"] == "harness_pass":
        icon = _svg("check", "")
    right = ""
    if event.get("elapsed_s") is not None:
        right = "%.2fs" % event["elapsed_s"] if event["kind"] == "model_call" else (
            "%.3fs" % event["elapsed_s"]
        )
    elif event.get("intervention"):
        right = "intervention %d" % event["intervention"]
    name = (
        _mono(event.get("name") or event.get("rule") or "")
        if event["kind"] != "model_call"
        else ""
    )
    qc = ""
    if event.get("qc") is not None:
        qc = "<span class='badge badge--%s'>QC %s</span>" % (
            "ok" if event["qc"] else "block",
            "ok" if event["qc"] else "FAILED",
        )
    return (
        "<div class='step-card %s'><div class='step-card__head'>"
        "<span class='step-card__n'>%02d</span>"
        "<span class='badge %s'>%s%s</span>%s%s"
        "<span class='step-card__time'>%s</span></div>%s</div>"
        % (
            card_class,
            index,
            badge_class,
            icon,
            badge_text,
            name,
            qc,
            _e(right),
            _event_body(event, index),
        )
    )


def _meter(label, value, cap, tone="", note=""):
    pct = 0 if not cap else min(100, round(100.0 * value / cap))
    cap_label = cap if cap else "∞"
    return (
        "<div class='meter'><div class='meter__head'><span>%s</span><b>%s / %s</b></div>"
        "<div class='meter__track'><div class='meter__fill %s' style='width:%d%%'></div></div>"
        "%s</div>"
        % (
            _e(label),
            value,
            cap_label,
            tone,
            pct,
            "<div class='meter__note'>%s</div>" % _e(note) if note else "",
        )
    )


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


def _plan_cell(value, limit=None):
    if isinstance(value, (dict, list, tuple)):
        text = json.dumps(value, ensure_ascii=False, indent=1, default=str)
    else:
        text = str(value if value not in (None, "") else "—")
    if limit and len(text) > limit:
        text = text[: limit - 1] + "…"
    return _e(text)


def _plan_table(headers, rows, css="research-plan-table"):
    head = "".join("<th>%s</th>" % _e(header) for header in headers)
    body = "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % cell for cell in row)
        for row in rows
    )
    return (
        "<div class='%s-wrap'><table class='%s'><thead><tr>%s</tr></thead>"
        "<tbody>%s</tbody></table></div>" % (css, css, head, body or "<tr><td colspan='%d'>none</td></tr>" % len(headers))
    )


def _plan_disclosure(title, body, open=False):
    return (
        "<details class='research-plan-section'%s><summary>%s</summary>"
        "<div class='research-plan-section__body'>%s</div></details>"
        % (" open" if open else "", _e(title), body)
    )


def _revision_changes_html(summary):
    if not summary:
        return ""
    groups = []
    for name, label in (("changed", "Changed"), ("added", "Added"), ("removed", "Removed")):
        items = summary.get(name) or []
        if not items:
            continue
        rows = []
        for item in items:
            if name == "changed":
                text = "%s → %s" % (
                    _plan_cell(item.get("from"), 260), _plan_cell(item.get("to"), 260)
                )
            else:
                value = item.get("to") if name == "added" else item.get("from")
                text = _plan_cell(value, 260)
            rows.append("<li><b>%s</b><span>%s</span></li>" % (_e(item.get("field", "field")), text))
        groups.append(
            "<div class='research-plan-change-group'><b>%s</b><ul>%s</ul></div>"
            % (label, "".join(rows))
        )
    invalidated = ", ".join(summary.get("invalidated") or []) or "none"
    preserved = ", ".join(summary.get("preserved") or []) or "none"
    return (
        "<section class='research-plan-revision'>"
        "<div class='research-context__label'>REVISION SUMMARY · v%03d → v%03d</div>"
        "%s<div class='research-plan-revision__meta'><b>Cleared:</b> %s · <b>Preserved:</b> %s · <b>Next:</b> review plan</div>"
        "</section>"
        % (
            summary.get("from_version", 0), summary.get("to_version", 0),
            "".join(groups) or "<p>No physical fields changed.</p>",
            _e(invalidated), _e(preserved),
        )
    )


def _structured_approval_bar(session, project, research):
    plan = project.get("plan") or {}
    phase = project.get("phase", "plan_review")
    phase_labels = {
        "plan_review": "Review and revise the plan",
        "plan_approved": "Plan approved for preview",
        "pseudo_preview": "Review pseudo-data layout",
        "chart_selected": "Review final figure package",
    }
    phase_label = phase_labels.get(phase, phase)
    phase_index = {"plan_review": 0, "plan_approved": 1, "pseudo_preview": 2, "chart_selected": 3}.get(phase, 0)
    flow = "".join(
        "<span class='research-flow__step%s'>%d. %s</span>"
        % (" is-current" if index == phase_index else "", index + 1, _e(label))
        for index, label in enumerate(
            ("Review plan", "Preview layout", "Confirm figures", "Approve execution", "Run real model")
        )
    )
    guidance = {
        "plan_review": "Review the method, variables, runs, and acceptance criteria. No physical result is authorized.",
        "plan_approved": "Only a display-only preview is authorized. No physical model call is authorized.",
        "pseudo_preview": "Pseudo-data demonstrate layout only. Select the chart package or revise the plan.",
        "chart_selected": "The selected figure package is ready for formal execution approval.",
    }.get(phase, "Review the current research decision before continuing.")
    evidence_rows = [
        [_plan_cell(item.get("evidence_ref")), _plan_cell(item.get("purpose"), 260)]
        for item in plan.get("literature_evidence") or [] if isinstance(item, dict)
    ]
    target_rows = [
        [
            _plan_cell(item.get("id")), _plan_cell("%s:%s" % (item.get("source_type"), item.get("source_id"))),
            _plan_cell(item.get("target_quantity")), _plan_cell(item.get("status")),
            _plan_cell(", ".join(item.get("run_ids") or []) or "none"),
            _plan_cell(", ".join(item.get("chart_ids") or []) or "none"),
        ]
        for item in plan.get("reproduction_targets") or [] if isinstance(item, dict)
    ]
    model_rows = [
        [_plan_cell(item.get("model")), _plan_cell(item.get("version")), _plan_cell(item.get("purpose"), 260), _plan_cell(item.get("capability_status"))]
        for item in plan.get("selected_models") or [] if isinstance(item, dict)
    ]
    mapping_rows = [
        [_plan_cell(item.get("paper_concept")), _plan_cell(item.get("paper_value")), _plan_cell(item.get("model_input")), _plan_cell(item.get("mapped_value")), _plan_cell(item.get("provenance_class"))]
        for item in plan.get("parameter_mapping") or [] if isinstance(item, dict)
    ]
    run_rows = []
    for run in plan.get("runs") or []:
        parameters = run.get("resolved_parameters") or run.get("parameters") or {}
        run_rows.append([
            _plan_cell(run.get("id")), _plan_cell(run.get("label"), 220), _plan_cell(run.get("model")),
            _plan_cell(parameters, 520), _plan_cell(", ".join(run.get("target_ids") or []) or "none"),
        ])
    chart_rows = [
        [_plan_cell(item.get("id")), _plan_cell(item.get("label"), 220), _plan_cell(item.get("x")), _plan_cell(", ".join(item.get("ys") or [item.get("y") or ""])), _plan_cell(item.get("purpose"))]
        for item in plan.get("charts") or [] if isinstance(item, dict)
    ]
    condition_rows = [
        [_e("Paper context (non-blocking)"), _plan_cell(plan.get("paper_conditions") or {})],
        [_e("Paper context provenance"), _plan_cell(plan.get("condition_provenance") or {})],
        [_e("User/model parameters"), _plan_cell({key: value for key, value in (plan.get("parameters") or {}).items() if key not in (plan.get("paper_conditions") or {})})],
        [_e("Assumptions"), _plan_cell(plan.get("assumptions") or [])],
        [_e("Limitations"), _plan_cell(plan.get("limitations") or [])],
        [_e("Success criteria"), _plan_cell(plan.get("success_criteria") or [])],
    ]
    warning_rows = [
        [
            _plan_cell(item.get("code") or "warning"),
            _plan_cell(item.get("field")),
            _plan_cell(item.get("expected")),
            _plan_cell(item.get("actual")),
            _plan_cell("non-blocking" if item.get("blocking") is False else "blocking"),
        ]
        for item in plan.get("validation_warnings") or []
        if isinstance(item, dict)
    ]
    chart_buttons = "".join(
        "<button type='button' class='approve__chart%s' data-chart-id='%s'%s data-required='%s'>"
        "<b>[%s]</b> %s <span>(%s · %s: %s → %s%s)</span></button>"
        % (
            " is-selected" if item.get("id") in set(project.get("selected_charts") or []) else "",
            _e(item.get("id")), " disabled" if phase != "pseudo_preview" else "",
            "true" if item.get("required", True) else "false", _e(item.get("id")), _e(item.get("label")),
            _e(item.get("purpose", "result")), _e(item.get("kind")), _e(item.get("x")),
            _e(", ".join(item.get("ys") or [item.get("y") or ""])),
            " · required" if item.get("required", True) else " · optional",
        )
        for item in plan.get("charts") or []
    ) or "none"
    steps_html = "<ol class='research-steps'>%s</ol>" % "".join(
        "<li>%s</li>" % _e(step) for step in (plan.get("steps") or [])
    )
    pseudo = project.get("pseudo") or {}
    pseudo_html = ""
    if pseudo.get("points"):
        keys = list(pseudo["points"][0])
        pseudo_html = _plan_table(
            keys,
            [[_plan_cell(row.get(key)) for key in keys] for row in pseudo["points"][:8]],
            css="research-preview",
        )
    summary = plan.get("revision_summary") or project.get("revision_summary")
    protocol = _e(research.protocol_yaml(project))
    sections = (
        _plan_disclosure(
            "Question and hypothesis",
            "<div class='research-plan-prose'><b>Question:</b> %s</div><div class='research-plan-prose'><b>Hypothesis:</b> %s</div>"
            % (_e(plan.get("question", "")), _e(plan.get("hypothesis", ""))),
            open=True,
        )
        + _plan_disclosure("Literature evidence", _plan_table(("Evidence", "Purpose"), evidence_rows), open=True)
        + _plan_disclosure("Reproduction targets", _plan_table(("Target", "Source", "Quantity", "Status", "Runs", "Charts"), target_rows), open=True)
        + _plan_disclosure("Models and paper-to-model mappings", _plan_table(("Model", "Version", "Purpose", "Status"), model_rows) + _plan_table(("Paper concept", "Paper value", "Model input", "Mapped value", "Provenance"), mapping_rows))
        + _plan_disclosure(
            "Validation sources and warnings",
            "<div class='approve__note'>Registered model declarations and opened model instructions/user guidelines provide hard validity checks. Paper conditions are comparison context only.</div>"
            + _plan_table(("Field", "Value"), condition_rows)
            + _plan_table(("Code", "Field", "Paper context", "Actual", "Status"), warning_rows),
        )
        + _plan_disclosure("Planned runs", _plan_table(("ID", "Label", "Model", "Resolved parameters", "Targets"), run_rows), open=True)
        + _plan_disclosure("Outputs and charts", _plan_table(("Chart", "Label", "X", "Y", "Purpose"), chart_rows) + "<div class='approve__note'><b>Chart options</b></div><div class='approve__charts'>%s</div>" % chart_buttons, open=True)
        + _plan_disclosure("Preview", ("<div class='approve__note'><b>%s</b><br>Pseudo-data are deterministic layout demonstrations, not model results.</div>" % _e(pseudo.get("label", "PSEUDO-DATA · demonstration only")) + pseudo_html) if pseudo_html else "No pseudo-data preview has been generated.")
        + "<details class='research-protocol-yaml'><summary>Raw generated protocol YAML · plan v%03d</summary><pre class='research-plan-yaml'>%s</pre><p class='approve__note'>This is a session draft for review and copying. Edit the plan in Conversation; it is never loaded as hidden instructions.</p></details>" % (project.get("plan_version", 1), protocol)
    )
    return (
        "<details class='research-plan-details' data-key='research-plan' open>"
        "<summary>Research plan · v%03d · %s</summary>"
        "<div class='approve approve--research' data-research-phase='%s' data-selected-count='%d' data-run-count='%d' data-chart-count='%d' data-validation='evidence %d · mappings %d'>"
        "<div class='research-plan-summary'>%d runs · %d charts · evidence %d · mappings %d</div>"
        "<div class='approve__head'>Research review · <b>plan v%03d</b></div>"
        "<div class='research-plan-flow'><b>Research plan flow</b><span>%s</span></div>"
        "<div class='approve__note approve__note--guide'><b>Current stage:</b> %s. %s "
        "<b>How to edit this plan:</b> describe the change in Conversation; the agent will create a new version. "
        "For a figure or preview, use ‘Revise plan in chat’.</div>"
        "%s%s<div class='research-plan-steps'><b>Execution steps</b>%s</div></div></details>"
        % (
            project.get("plan_version", 1), _e(phase_label), _e(phase), len(project.get("selected_charts") or []),
            len(plan.get("runs") or []), len(plan.get("charts") or []), len(plan.get("literature_evidence") or []),
            len(plan.get("parameter_mapping") or []), len(plan.get("runs") or []), len(plan.get("charts") or []),
            len(plan.get("literature_evidence") or []), len(plan.get("parameter_mapping") or []), project.get("plan_version", 1), flow, _e(phase_label), _e(guidance),
            _revision_changes_html(summary), sections, steps_html,
        )
    )


def approval_bar(session):
    """Render either the research review card or the physical-run approval gate."""
    from physearth import approval as gate, research

    project = (session or {}).get("research") or {}
    if project and project.get("phase") not in ("approved", "completed"):
        return _structured_approval_bar(session, project, research)
    if project and project.get("phase") not in ("approved", "completed"):
        plan = project.get("plan") or {}
        phase = project.get("phase", "plan_review")
        phase_labels = {
            "plan_review": "Review and revise the plan",
            "plan_approved": "Plan approved for preview",
            "pseudo_preview": "Review pseudo-data layout",
            "chart_selected": "Review final figure package",
        }
        phase_label = phase_labels.get(phase, phase)
        phase_index = {
            "plan_review": 0,
            "plan_approved": 1,
            "pseudo_preview": 2,
            "chart_selected": 3,
        }.get(phase, 0)
        flow_html = (
            "<div class='research-flow'><b>Research plan flow</b>"
            + "".join(
                "<span class='research-flow__step%s'>%d. %s</span>"
                % (" is-current" if index == phase_index else "", index + 1, label)
                for index, label in enumerate(
                    ("Review plan", "Preview layout", "Confirm figures", "Approve execution", "Run real model")
                )
            )
            + "</div>"
        )
        review_guidance = {
            "plan_review": (
                "Approve plan reviews the method, variables, runs, and acceptance criteria. "
                "It does not approve pseudo-data or a final scientific figure."
            ),
            "plan_approved": (
                "The plan is approved only far enough to generate a display-only preview. "
                "No physical model call has been authorized."
            ),
            "pseudo_preview": (
                "Pseudo-data are deterministic layout demonstrations, not model results. "
                "If the axes, range, variables, or figure design are wrong, choose "
                "'Revise plan in chat' and describe the change."
            ),
            "chart_selected": (
                "The selected figure package is ready for final execution approval. "
                "Changing it requires a new plan revision."
            ),
        }.get(phase, "Review the current research decision before continuing.")
        revision_html = (
            "<div class='approve__note approve__note--guide'><b>How to edit this plan:</b> "
            "use Conversation to state the change, for example: "
            "'remove the optional chart', 'change the density range to 10-500 kg/m3', "
            "or 'plot tb_v and tb_h against angle'. The agent records a new plan version, "
            "clears stale pseudo-data, and returns the plan to review.</div>"
        )
        steps = "".join(
            "<li>%s</li>" % _e(step) for step in (plan.get("steps") or [])
        )
        protocol_fixed = plan.get("paper_conditions") or {}
        condition_provenance = plan.get("condition_provenance") or {}
        plan_parameters = plan.get("parameters") or {}
        agent_parameters = {
            key: value for key, value in plan_parameters.items() if key not in protocol_fixed
        }
        agent_assumptions = "; ".join(str(item) for item in plan.get("assumptions") or [])
        params = (
            "<div class='approve__p'><b>Conditions from paper sections:</b> %s</div>"
            "<div class='approve__p'><b>Condition evidence:</b> %s</div>"
            "<div class='approve__p'><b>Agent-selected conditions:</b> %s</div>"
            "<div class='approve__p'><b>Agent assumptions:</b> %s</div>"
            % (
                _e(_mapping_text(protocol_fixed) or "not declared from the source yet"),
                _e(_mapping_text(condition_provenance) or "not declared"),
                _e(_mapping_text(agent_parameters) or "none outside the source conditions"),
                _e(agent_assumptions or "none declared"),
            )
        )
        evidence_items = plan.get("literature_evidence") or []
        evidence_html = (
            "<div class='approve__p'><b>Literature evidence:</b> %s</div>"
            % _e(
                "; ".join(
                    "%s (%s)" % (item.get("evidence_ref"), item.get("purpose", "source evidence"))
                    for item in evidence_items
                    if isinstance(item, dict) and item.get("evidence_ref")
                )
                or "not declared"
            )
        )
        target_items = plan.get("reproduction_targets") or []
        target_html = (
            "<div class='approve__p'><b>Reproduction targets:</b> %s</div>"
            % _e(
                "; ".join(
                    "%s %s:%s [%s] -> runs=%s charts=%s%s"
                    % (
                        item.get("id"), item.get("source_type"), item.get("source_id"),
                        item.get("status", "planned"),
                        ",".join(item.get("run_ids") or []) or "none",
                        ",".join(item.get("chart_ids") or []) or "none",
                        " (%s)" % item.get("availability_reason") if item.get("availability_reason") else "",
                    )
                    for item in target_items
                    if isinstance(item, dict)
                )
                or "none"
            )
        )
        mapping_items = plan.get("parameter_mapping") or []
        mapping_html = (
            "<div class='approve__p'><b>Paper-to-model mapping:</b> %s</div>"
            % _e(
                "; ".join(
                    "%s -> %s=%s [%s]"
                    % (
                        item.get("paper_concept"), item.get("model_input"),
                        item.get("mapped_value"), item.get("provenance_class"),
                    )
                    for item in mapping_items
                    if isinstance(item, dict)
                )
                or "not declared"
            )
        )
        selected_model_items = plan.get("selected_models") or []
        models_html = (
            "<div class='approve__p'><b>Selected models:</b> %s</div>"
            % _e(
                "; ".join(
                    "%s (%s)" % (item.get("model"), item.get("purpose", "planned"))
                    for item in selected_model_items
                    if isinstance(item, dict)
                )
                or "not declared"
            )
        )
        gaps = plan.get("capability_gaps") or []
        scope_html = (
            "<div class='approve__note'><b>Expected outcome:</b> %s%s</div>"
            % (
                _e(plan.get("outcome_scope", "full")),
                _e(" — unavailable locally: " + ", ".join(gaps)) if gaps else "",
            )
        )
        repairs = plan.get("automatic_repairs") or []
        if repairs:
            scope_html += (
                "<div class='approve__note'><b>Proposed plan repairs — review required:</b> %s</div>"
                % _e(
                    "; ".join(
                        "%s.%s: %s → %s (%s)"
                        % (
                            item.get("chart_id") or item.get("run_id") or "plan",
                            item.get("field"), item.get("from"),
                            item.get("to"), item.get("reason"),
                        )
                        for item in repairs
                    )
                )
            )
        recovery = project.get("recovery") or {}
        if recovery:
            proposed = recovery.get("repairs") or []
            scope_html += (
                "<div class='approve__note approve__note--warning'>"
                "<b>Recovery review required:</b> failed runs %s. %s</div>"
                % (
                    _e(", ".join(recovery.get("failed_run_ids") or []) or "unknown"),
                    _e(
                        "; ".join(
                            "%s: %s %s → %s"
                            % (
                                item.get("run_id"), item.get("field"),
                                item.get("from"), item.get("to"),
                            )
                            for item in proposed
                        )
                        or "No automatic physical change was applied; revise the plan in chat."
                    ),
                )
            )
        scope_html = (
            flow_html
            + "<div class='approve__note approve__note--guide'><b>Current stage:</b> %s. %s</div>"
            % (_e(phase_label), _e(review_guidance))
            + revision_html
            + evidence_html
            + target_html
            + models_html
            + mapping_html
            + scope_html
        )
        protocol_rows = "".join(
            "<div class='research-protocol__row'><b>%s</b><span>%s</span></div>"
            % (_e(label), _e("; ".join(plan.get(key) or []) or "not specified"))
            for key, label in (
                ("quantities", "Quantities"),
                ("controls", "Controls"),
                ("metrics", "Metrics"),
                ("diagnostics", "Diagnostics"),
                ("success_criteria", "Acceptance"),
                ("stop_conditions", "Stop conditions"),
                ("limitations", "Limitations"),
            )
        )
        protocol_rows += (
            "<div class='research-protocol__row'><b>Baseline</b><span>%s</span></div>"
            % _e(plan.get("baseline_run_id") or "not specified")
        )
        generated_protocol_html = (
            "<details class='research-protocol-yaml'><summary>Generated protocol.yaml "
            "(session draft, plan v%03d)</summary><pre>%s</pre>"
            "<p class='approve__note'>This YAML is generated from the current agent plan. "
            "Edit it by describing changes in Conversation; the agent will create a new "
            "version through research_plan(action='revise_plan').</p></details>"
            % (project.get("plan_version", 1), _e(research.protocol_yaml(project)))
        )
        pseudo = project.get("pseudo") or {}
        pseudo_rows = pseudo.get("points") or []
        pseudo_html = ""
        if pseudo_rows:
            keys = list(pseudo_rows[0])
            header = "".join("<th>%s</th>" % _e(key) for key in keys)
            rows = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % _e(row.get(key, "")) for key in keys)
                for row in pseudo_rows[:6]
            )
            pseudo_html = (
                "<div class='approve__note'><b>%s</b></div>"
                "<table class='research-preview'><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
                % (_e(pseudo.get("label", "PSEUDO-DATA — demonstration only")), header, rows)
            )
        selected_ids = set(project.get("selected_charts") or [])
        charts = "".join(
            "<button type='button' class='approve__chart%s' data-chart-id='%s' data-required='%s'%s>"
            "<b>[%s]</b> %s <span>(%s · %s: %s → %s%s)</span></button>"
            % (
                " is-selected" if item.get("id") in selected_ids else "",
                _e(item.get("id")),
                "true" if item.get("required", True) else "false",
                " disabled" if project.get("phase") != "pseudo_preview" else "",
                _e(item.get("id")),
                _e(item.get("label")),
                _e(item.get("purpose", "result")),
                _e(item.get("kind")),
                _e(item.get("x")),
                _e(", ".join(item.get("ys") or [item.get("y")])),
                " · required" if item.get("required", True) else " · optional",
            )
            for item in (plan.get("charts") or [])
        )
        evidence_count = len(plan.get("literature_evidence") or [])
        mapping_count = len(plan.get("parameter_mapping") or [])
        run_count = len(plan.get("runs") or [])
        chart_count = len(plan.get("charts") or [])
        validation_label = "evidence %d · mappings %d" % (evidence_count, mapping_count)
        return (
            "<details class='research-plan-details' data-key='research-plan'>"
            "<summary>Research plan · v%03d · %s</summary>"
            "<div class='approve approve--research' data-research-phase='%s' data-selected-count='%d' "
            "data-run-count='%d' data-chart-count='%d' data-validation='%s'>"
            "<div class='research-plan-summary'>%d runs · %d charts · %s</div>"
            "<div class='approve__head'>Research review · <b>%s</b> · plan v%03d</div>"
            "<div class='approve__note'>Phase: %s. No formal physical result is authorized yet.</div>"
            "<div class='research-question'><b>Question:</b> %s<br><b>Hypothesis:</b> %s</div>"
            "%s"
            "%s"
            "<div class='research-protocol'>%s</div>"
            "<ol class='research-steps'>%s</ol>"
            "<div class='approve__params'>%s</div>"
            "%s"
            "<div class='approve__note'><b>Chart options</b></div><div class='approve__charts'>%s</div>"
            "<div class='approve__note'>必需科研图已锁定；可勾选其他可选图。确认整个图组后再批准正式计算。</div>"
            "</div></details>"
            % (project.get("plan_version", 1), _e(phase_label), _e(project.get("phase")), len(selected_ids), run_count, chart_count, _e(validation_label), run_count, chart_count, _e(validation_label), _e(plan.get("title", "Research plan")), project.get("plan_version", 1),
               _e(project.get("phase")), _e(plan.get("question", "")), _e(plan.get("hypothesis", "")),
               scope_html, generated_protocol_html, protocol_rows, steps, params, pseudo_html, charts or "none")
        )

    waiting = gate.pending(session)
    if not waiting:
        return "<div class='approve' hidden></div>"
    described = waiting["description"]
    rows = "".join(
        "<span class='approve__p'><b>%s</b> %s</span>" % (_e(k), _e(v))
        for k, v in sorted(described["parameters"].items())
    )
    return (
        "<div class='approve'>"
        "<div class='approve__head'>Run <b>%s</b> as %s?</div>"
        "<div class='approve__params'>%s</div>"
        "<div class='approve__note'>The model cannot answer this for itself. If nobody "
        "answers within %d seconds the call goes ahead and the trace says so.</div>"
        "</div>"
        % (
            _e(described["model"]),
            _e(described["shape"]),
            rows or "<span class='approve__p'>every parameter at its declared default</span>",
            int(gate.TIMEOUT_S),
        )
    )


def _trace_metrics(state):
    used, cap = budget.used()
    session = state.get("session") or state
    turns = session.get("turns", 0)
    meters = "".join(
        [
            _meter(
                "model calls", session.get("model_calls", 0), session.get("max_model_calls", 1),
                note=("%d this question, %s" % (state.get("model_calls", 0), "no hard cap" if not state.get("max_model_calls") else "cap %d" % state.get("max_model_calls"))),
            ),
            _meter(
                "tool calls", session.get("tool_calls", 0), session.get("max_tool_calls", 1), "is-violet",
                note=("%d this question, %s" % (state.get("tool_calls", 0), "no hard cap" if not state.get("max_tool_calls") else "cap %d" % state.get("max_tool_calls"))),
            ),
            _meter("context", state.get("prompt_tokens", 0), state.get("context_ceiling", 1), "is-ok"),
            _meter(
                "hourly quota", used, cap, "is-ok",
                note="shared by every visitor" if cap else "no hard cap",
            ),
        ]
    )
    counters = "".join(
        [
            "<span class='badge badge--mono'>%d question%s in this session</span>" % (turns, "" if turns == 1 else "s"),
            "<span class='badge badge--%s'>%d blocked</span>" % ("block" if session.get("interventions") else "mute", session.get("interventions", 0)),
            "<span class='badge badge--%s'>%d boundary</span>" % ("warn" if session.get("boundary_flags") else "mute", session.get("boundary_flags", 0)),
            "<span class='badge badge--%s'>%d QC failure%s</span>" % ("block" if session.get("qc_failures") else "ok", session.get("qc_failures", 0), "" if session.get("qc_failures") == 1 else "s"),
            "<span class='badge badge--src'>%d model run%s</span>" % (session.get("model_runs", 0), "" if session.get("model_runs") == 1 else "s"),
            "<span class='badge badge--src'>%d section%s read</span>" % (len(session.get("sections_read") or ()), "" if len(session.get("sections_read") or ()) == 1 else "s"),
        ]
    )
    return "<div class='trace-metrics'><div class='meters'>%s</div><div class='counters'>%s</div></div>" % (meters, counters)


def trace_metrics(state):
    return _trace_metrics(state)


def trace(events, state, running=False, include_footer=True):
    head = (
        "<div class='subpanel' style='padding-bottom:0'><div class='sec-head'>%s"
        "<span class='sec-title'>Run trace</span>"
        "<span class='sec-count'>%d event%s</span></div></div>"
        % (_svg("trace", "sec-icon"), len(events), "" if len(events) == 1 else "s")
    )
    if not events and not running:
        body = (
            "<div class='pane-empty'><div class='pane-empty__title'>Nothing has run yet</div>"
            "<div class='pane-empty__hint'>Every model call, every tool call and every system "
            "refusal appears here as it happens.</div></div>"
        )
    else:
        body = "".join(_event_card(event, n) for n, event in enumerate(events, 1))
        if running:
            body += (
                "<div class='step-card step-card--thinking' style='display:block'>"
                "<div class='step-card__head'><span class='step-card__n'>%02d</span>"
                "<span class='badge badge--step'>%s</span></div>"
                "<div class='step-card__line thinking-dots'><span></span><span></span>"
                "<span></span></div></div>"
                % (
                    len(events) + 1,
                    "RUNNING TOOL" if state.get("phase") == "running_tool" else "THINKING",
                )
            )

    footer = _trace_metrics(state) if include_footer else ""
    return "<div class='trace-layout trace-layout--events'>%s<div class='subpanel grow'><div class='subpanel__scroll'>%s</div></div>%s</div>" % (head, body, footer)


# ---------------------------------------------------------------- evidence


def _agreement_row(values):
    """Statistics under the chart they came from, never floating free of it."""
    stats = "".join(
        "<span class='stat'><b>%s</b>%s%s</span>"
        % (_e(name), _e(values[name]), _e(" " + values["unit"] if name != "r" else ""))
        for name in ("bias", "rmse", "mae", "r")
        if values.get(name) is not None
    )
    return (
        "<div class='fig-stats'>%s<span class='fig-stats__note'>%s against %s over %d "
        "overlapping point(s), %g to %g</span></div>"
        % (
            stats,
            _e(values.get("of", "")),
            _e(values.get("against", "")),
            values.get("n_points", 0),
            (values.get("overlap") or [0, 0])[0],
            (values.get("overlap") or [0, 0])[1],
        )
    )


def _comparison_table(rows):
    if not rows:
        return ""
    body = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (
            _e(row.get("quantity", "")),
            _e(row.get("of", "")),
            _e(row.get("against", "")),
            _e(row.get("bias", "")),
            _e(row.get("rmse", "")),
            _e(row.get("mae", "")),
        )
        for row in rows
    )
    return (
        "<div class='fig-comparisons'><b>Pairwise diagnostics</b>"
        "<table><thead><tr><th>quantity</th><th>series</th><th>baseline</th>"
        "<th>bias</th><th>RMSE</th><th>MAE</th></tr></thead><tbody>%s</tbody></table></div>"
        % body
    )


def _figure_card(figure, index):
    sources = figure.get("provenance") or ["model_run"]
    preview = bool(figure.get("preview"))
    ribbon = (
        "fig-ribbon--preview"
        if preview
        else "fig-ribbon--measured"
        if "measured" in sources
        else "fig-ribbon--computed"
    )
    label = (
        "pseudo-data preview"
        if preview
        else " + ".join("model run" if s == "model_run" else s for s in sources)
    )
    figure_number = figure.get("figure_number") or index
    if not preview:
        label = "Figure %d · %s" % (figure_number, label)
    legend = "".join(
        "<span class='badge badge--%s'>%s</span> %s "
        % (
            "ok" if item["source"] == "measured" else "model",
            "measured" if item["source"] == "measured" else "model run",
            _e(
                "%s, %s%s"
                % (
                    item["label"],
                    item["origin"],
                    "" if preview else ", %d points" % item["n_points"],
                )
            ),
        )
        for item in figure.get("series") or []
    )
    agreement = _agreement_row(figure["agreement"]) if figure.get("agreement") else ""
    comparisons = _comparison_table(figure.get("comparisons") or [])
    quality = figure.get("quality_review") or {}
    quality_html = ""
    if not preview and quality.get("reviewed"):
        quality_html = (
            "<div class='fig-quality %s'><b>Figure QA:</b> %s%s</div>"
            % (
                "is-passed" if quality.get("passed") else "is-failed",
                "passed" if quality.get("passed") else "failed",
                " · automatically redrawn for clarity" if quality.get("redrawn") else "",
            )
        )
    return (
        "<div class='fig-card%s' data-anchor='fig-%d'>"
        "<div class='fig-ribbon %s'>%s<span class='handle'>%s</span></div>"
        "<div class='fig-body'><img alt='%s' src='%s'>%s%s%s"
        "<div class='fig-cap'>%s</div></div></div>"
        % (
            " fig-card--preview" if preview else "",
            index,
            ribbon,
            _e(label),
            _e((figure.get("series") or [{}])[0].get("handle", "")),
            _e(figure.get("title") or "chart"),
            _e(figure.get("image_url") or figure.get("png", "")),
            agreement,
            comparisons,
            quality_html,
            legend or _e(figure.get("title") or ""),
        )
    )


SOURCE_BADGE = {
    "bundled": ("badge--src", "bundled"),
    "session": ("badge--model", "fetched in this conversation"),
    "skill": ("badge--mono", "method note"),
}


def _section_card(session, key):
    slug, _, section_id = key.partition("#")
    card = literature.card(session, slug)
    section = literature.read_section(session, slug, section_id) if card else None
    if not section:
        return ""
    origin = literature.source_of(session, slug)
    badge_class, badge_text = SOURCE_BADGE.get(origin, ("badge--src", origin or "source"))
    doi = card.get("doi", "")
    text = " ".join(section["text"].replace("#", " ").split())
    if len(text) > SECTION_PREVIEW_CHARS:
        body = (
            "%s<details class='disclosure' data-key='sec-%s'><summary>rest of the section, "
            "%d more characters</summary><div class='ev-card__text'>%s</div></details>"
        ) % (
            _e(text[:SECTION_PREVIEW_CHARS] + "..."),
            _e(key),
            len(text) - SECTION_PREVIEW_CHARS,
            _e(text[SECTION_PREVIEW_CHARS:]),
        )
    else:
        body = _e(text)
    return (
        "<div class='ev-card' data-anchor='sec-%s'>"
        "<div class='ev-card__head'><span class='badge badge--mono'>%s</span>"
        "<span class='ev-card__title'>%s</span>"
        "<span class='badge %s' style='margin-left:auto'>%s</span></div>"
        "<div class='ev-card__text'>%s</div>"
        "<div class='ev-card__foot'><span class='badge badge--src'>%s</span>"
        "<span>%s (%s)</span>%s</div></div>"
        % (
            _e(key),
            _e(key),
            _e(section["title"]),
            badge_class,
            _e(badge_text),
            body,
            _e(card.get("license", "")),
            _e(card.get("title", slug)),
            _e(card.get("year", "")),
            "<a href='https://doi.org/%s' target='_blank' rel='noopener'>doi.org/%s</a>"
            % (_e(doi), _e(doi))
            if doi
            else "",
        )
    )


def _abstract_card(doi, item):
    """Abstract level. Deliberately drawn as a thinner thing than a section card."""
    return (
        "<div class='ev-card ev-card--abs' data-anchor='abs-%s'>"
        "<div class='ev-card__head'><span class='badge badge--warn'>abstract only</span>"
        "<span class='ev-card__title'>%s</span></div>"
        "<div class='ev-card__text'>%s</div>"
        "<div class='ev-card__foot'><span class='badge badge--src'>%s</span>"
        "<span>%s &middot; %s</span>"
        "<a href='https://doi.org/%s' target='_blank' rel='noopener'>doi.org/%s</a></div>"
        "<div class='pane-note' style='margin:8px 0 0'>Not read. This can support what the "
        "study was about, never a value in kelvin, decibels or volumetric soil moisture.</div>"
        "</div>"
        % (
            _e(doi),
            _e(item.get("title") or doi),
            _e(item.get("abstract") or "No abstract was returned for this record."),
            _e(item.get("license") or "licence not stated"),
            _e(item.get("authors") or "unknown authors"),
            _e(item.get("year") or ""),
            _e(doi),
            _e(doi),
        )
    )


def _dataset_card(slug):
    card = reference.card(slug)
    if not card:
        return ""
    item = reference.provenance(slug)
    indices, _ = reference.query(slug)
    summary = reference.summarise(slug, indices)
    rows = "".join(
        "<tr><td class='name'>%s</td><td>%s</td><td class='num'>%s</td>"
        "<td><span class='badge badge--ok'>%s</span></td></tr>"
        % (
            _e(name),
            _e(spec.get("unit", "")),
            _e(
                "%s to %s" % (spec["min"], spec["max"])
                if "min" in spec
                else "%d value%s" % (spec.get("unique", 0), "" if spec.get("unique") == 1 else "s")
            ),
            _e(card["columns"][name]["source"]),
        )
        for name, spec in summary.items()
    )
    return (
        "<div class='ev-card' data-anchor='data-%s'>"
        "<div class='ev-card__head'><span class='badge badge--mono'>data:%s</span>"
        "<span class='ev-card__title'>%s</span></div>"
        "<table class='table'><thead><tr><th>column</th><th>unit</th><th>range</th>"
        "<th>source</th></tr></thead><tbody>%s</tbody></table>"
        "<div class='ev-card__foot'><span class='badge badge--src'>%s</span>"
        "<span>%d rows</span>"
        "<a href='https://doi.org/%s' target='_blank' rel='noopener'>doi.org/%s</a>"
        "</div></div>"
        % (
            _e(slug),
            _e(slug),
            _e(card["title"]),
            rows,
            _e(item["license"]),
            len(indices),
            _e(item["paper_doi"]),
            _e(item["paper_doi"]),
        )
    )


def _corpus_card(entry):
    card = knowledge.card(entry["slug"])
    doi = card.get("doi", "")
    sections = knowledge.section_index(entry["slug"]) or []
    return (
        "<div class='ev-card'><div class='ev-card__head'>"
        "<span class='badge badge--mono'>%s</span>"
        "<span class='ev-card__title'>%s</span></div>"
        "<div class='ev-card__text'>%s</div>"
        "<div class='ev-card__foot'><span class='badge badge--src'>%s</span>"
        "<span>%s &middot; %d sections</span>"
        "<a href='https://doi.org/%s' target='_blank' rel='noopener'>doi.org/%s</a>"
        "</div></div>"
        % (
            _e(entry["slug"]),
            _e(entry["title"]),
            _e(entry["description"]),
            _e(entry["license"]),
            _e(entry["year"]),
            len(sections),
            _e(doi),
            _e(doi),
        )
    )


def _model_card(row):
    entry = registry.get(row["name"])
    card = entry.card if entry else {}
    tier = "<span class='badge badge--%s' style='margin-left:auto'>%s</span>" % (
        "ok" if row["runnable"] else "mute",
        _e(row["tier"]),
    )
    profile = card.get("resource_profile") or {}
    rows = [
        ("outputs", ", ".join(row["outputs"])),
        ("parameters", "%d declared" % len(card.get("parameters") or {})),
        ("licence", card.get("license", "")),
        ("typical run", profile.get("typical_runtime", "")),
    ]
    info = "".join(
        "<div class='info-row'><span class='k'>%s</span><span class='v'>%s</span></div>"
        % (_e(k), _e(v))
        for k, v in rows
        if v
    )
    citation = card.get("citation", "")
    return (
        "<div class='model-card' data-anchor='model-%s'>"
        "<div class='model-card__head'><span class='model-card__name'>%s</span>"
        "<span class='model-card__ver'>%s</span>%s</div>"
        "<div class='model-card__desc'>%s</div>"
        "<div class='info-card'>%s</div>"
        "<div class='ev-card__foot'><span>%s</span><span>%s</span></div></div>"
        % (
            _e(row["name"]),
            _e(row["name"]),
            _e(row["version"]),
            tier,
            _e(row["description"]),
            info,
            _e(row["source"]),
            _e(citation),
        )
    )


def _rejected_card(item):
    return (
        "<div class='model-card model-card--local'><div class='model-card__head'>"
        "<span class='model-card__name'>%s</span>"
        "<span class='badge badge--mute' style='margin-left:auto'>rejected</span></div>"
        "<div class='model-card__desc'>%s</div></div>"
        % (_e(item["directory"].rsplit("\\", 1)[-1].rsplit("/", 1)[-1]), _e(item["reason"]))
    )


def evidence(session=None, figures=None, sections=None, datasets=None):
    """Everything the conversation holds. Defaults come from the session, so a figure
    drawn in the first question is still on screen during the third."""
    session = session or {}
    figures = list(session.get("figures") or [] if figures is None else figures)
    sections = sorted(session.get("sections_read") or () if sections is None else sections)
    datasets = sorted(session.get("datasets_read") or () if datasets is None else datasets)

    if figures:
        figures_pane = "".join(_figure_card(fig, n) for n, fig in enumerate(figures, 1))
    else:
        figures_pane = (
            "<div class='pane-empty'><div class='pane-empty__title'>No chart yet</div>"
            "<div class='pane-empty__hint'>Ask for a plot. The arrays go from the result store "
            "straight to the renderer, so the numbers never pass through the language "
            "model.</div></div>"
        )

    abstracts = literature.abstracts(session)
    read = "".join(_section_card(session, key) for key in sections)
    read += "".join(_dataset_card(slug) for slug in datasets)
    read += "".join(_abstract_card(doi, abstracts[doi]) for doi in sorted(abstracts))
    if not read:
        read = (
            "<div class='pane-empty'><div class='pane-empty__title'>Nothing opened yet</div>"
            "<div class='pane-empty__hint'>Whatever the agent reads appears here in full, with "
            "its licence and a link to the paper. Switch to the whole corpus to browse all of "
            "it.</div></div>"
        )
    corpus = "".join(_corpus_card(entry) for entry in knowledge.catalogue())

    opened = len(sections) + len(datasets)
    sources_pane = (
        "<input class='scope-input' type='radio' name='pe-scope' id='pe-scope-read' checked>"
        "<input class='scope-input' type='radio' name='pe-scope' id='pe-scope-all'>"
        "<div class='scope'><label for='pe-scope-read'>Opened here (%d)</label>"
        "<label for='pe-scope-all'>Whole corpus (%d)</label></div>"
        "<div class='scope-body'><div class='scope-pane'>%s</div>"
        "<div class='scope-pane'>%s</div></div>"
        "<div class='pane-note'>Every full card in the first list is a section the agent "
        "actually opened, whether it shipped with the system or was fetched during this "
        "conversation. A marker that does not resolve to one of them is refused before the "
        "answer reaches you. The thin cards marked <b>abstract only</b> are papers the agent "
        "has seen listed and has not read; they cannot support a number.</div>"
        % (opened + len(abstracts), len(knowledge.slugs()), read, corpus)
    )

    rows = registry.summary()
    models_pane = "".join(_model_card(row) for row in rows)
    models_pane += "".join(_rejected_card(item) for item in registry.rejected())
    models_pane += (
        "<div class='pane-note'>%d models, one tool. Registering another is a model card plus "
        "one <span class='mono'>run(spec)</span> function, and it inherits every check on this "
        "page without touching the harness. "
        "<a href='https://github.com/zjuiEMLab/PhysEarth-Agent#adding-your-own-model' "
        "target='_blank' rel='noopener'>Read the tutorial</a>.</div>" % len(rows)
    )

    def tab(index, key, icon, name, count):
        return (
            "<label class='tab' for='pe-tab-%s'>%s<span class='tab-name'>%s</span>"
            "<span class='tab-count'>%d</span></label>" % (key, _svg(icon, "tab-icon"), name, count)
        )

    return (
        "<div class='tabset'>"
        "<input class='tab-input' type='radio' name='pe-evtab' id='pe-tab-figures' checked>"
        "<input class='tab-input' type='radio' name='pe-evtab' id='pe-tab-sources'>"
        "<input class='tab-input' type='radio' name='pe-evtab' id='pe-tab-models'>"
        "<div class='tabbar'>%s%s%s</div>"
        "<div class='tab-panes'>"
        "<div class='tab-pane'><div class='pane-scroll'>%s</div></div>"
        "<div class='tab-pane'><div class='pane-scroll'>%s</div></div>"
        "<div class='tab-pane'><div class='pane-scroll'>%s</div></div>"
        "</div></div>"
        % (
            tab(1, "figures", "figure", "Figures", len(figures)),
            tab(2, "sources", "sources", "Sources", len(sections) + len(datasets)),
            tab(3, "models", "models", "Models", len(rows)),
            figures_pane,
            sources_pane,
            models_pane,
        )
    )
