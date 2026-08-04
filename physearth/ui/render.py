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
BOLD = re.compile(r"\*\*([^*]+)\*\*")
CODE = re.compile(r"`([^`]+)`")
SECTION_PREVIEW_CHARS = 620

EXAMPLES = [
    "Run SMRT to show how 37 GHz brightness temperature changes as snow density goes from "
    "100 to 700 kg/m3 for a 1 m layer, plot it, and explain the trend.",
    "At Trail Valley Creek, what Ku-band backscatter was actually measured, and how does "
    "SMRT compare at the same incidence angles? Plot both.",
    "How does L-band brightness temperature respond to soil moisture from 0.05 to 0.45, and "
    "how much does vegetation optical depth change that?",
    "Compare what tau_omega and water_cloud predict as soil moisture rises. Are the two "
    "results comparable?",
    "Simulate a snowpack at 37 GHz with a density of 2000 kg/m3.",
    "Do not use any tools. From your own knowledge, write a full paragraph explaining how "
    "snow density affects 37 GHz brightness temperature.",
]

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

    def section(match):
        key = "%s#%s" % (match.group(1), match.group(2))
        return (
            "<a class='cite' href='#' data-jump='sec-%s' data-tab='pe-tab-sources'>%s</a>"
            % (_e(key), _e(key))
        )

    def model(match):
        key = "%s@%s" % (match.group(1), match.group(2))
        return (
            "<a class='cite cite--model' href='#' data-jump='model-%s' "
            "data-tab='pe-tab-models'>%s</a>" % (_e(match.group(1)), _e(key))
        )

    def data(match):
        slug = match.group(1)
        return (
            "<a class='cite cite--data' href='#' data-jump='data-%s' "
            "data-tab='pe-tab-sources'>%s</a>" % (_e(slug), _e(slug))
        )

    def abstract(match):
        doi = match.group(1)
        return (
            "<a class='cite cite--abs' href='#' data-jump='abs-%s' "
            "data-tab='pe-tab-sources' title='abstract level: metadata only, never a "
            "measured or computed value'>abs:%s</a>" % (_e(doi), _e(doi))
        )

    # The abstract form goes first: some DOIs would otherwise be eaten by the model pattern.
    text = ABS_CITE.sub(abstract, text)
    text = CITE.sub(section, text)
    text = MODEL_CITE.sub(model, text)
    return DATA_CITE.sub(data, text)


def answer_html(text, running=False):
    """Escape first, then apply a deliberately small markdown subset."""
    if not (text or "").strip():
        return "<p class='hint'>Waiting for the first token.</p>" if running else ""
    blocks = []
    for raw in re.split(r"\n\s*\n", text.strip()):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if lines and all(line.startswith(("- ", "* ")) for line in lines):
            items = "".join("<li>%s</li>" % _inline(line[2:]) for line in lines)
            blocks.append("<ul>%s</ul>" % items)
        else:
            blocks.append("<p>%s</p>" % _inline(" ".join(lines)))
    body = "".join(blocks)
    if running:
        body += "<span class='caret'></span>"
    return body


def _inline(text):
    out = _e(text)
    out = CODE.sub(lambda m: "<code>%s</code>" % m.group(1), out)
    out = BOLD.sub(lambda m: "<b>%s</b>" % m.group(1), out)
    return _markers(out)


# ---------------------------------------------------------------- hero


def hero(model_id=None, running=False, status=""):
    chosen = model_id or agent.default_model()
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
    used, cap = budget.used()
    return (
        "<header class='hero'>"
        "<div class='hero-brand'>"
        "<svg class='hero-mark' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
        "stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'>"
        "<circle cx='12' cy='12' r='3.2'/><path d='M12 2v3.2M12 18.8V22M2 12h3.2M18.8 12H22"
        "M4.9 4.9l2.3 2.3M16.8 16.8l2.3 2.3M19.1 4.9l-2.3 2.3M7.2 16.8l-2.3 2.3'/></svg>"
        "<span class='hero-title'>PhysEarth-Agent</span>"
        "<span class='hero-sep'>/</span>"
        "<span class='hero-sub'>physical Earth models you can trust yourself to configure"
        "</span></div>"
        "<div class='hero-spacer'></div>"
        "<div class='hero-right'>"
        "<span class='status'><span class='status-dot'></span><span>%s</span></span>"
        "<div class='segment segment--model'>%s</div>"
        "<a class='tag' href='https://github.com/zjuiEMLab/PhysEarth-Agent' target='_blank' "
        "rel='noopener'>GitHub</a>"
        "<span class='tag'>%d/%d this hour</span>"
        "<span class='tag'>Apache-2.0</span>"
        "</div></header>%s"
        % (
            _e(status or ("Running" if running else "Idle")),
            buttons,
            used,
            cap,
            "<span data-running='1' hidden></span>" if running else "",
        )
    )


# ---------------------------------------------------------------- conversation


def conversation_head(count):
    return (
        "<div class='subpanel' style='padding-bottom:0'><div class='sec-head'>%s"
        "<span class='sec-title'>Conversation</span>"
        "<span class='sec-count'>%d question%s</span></div></div>"
        % (_svg("chat", "sec-icon"), count, "" if count == 1 else "s")
    )


def history(turns):
    """The session so far. It keeps growing until the visitor clears it."""
    if not turns:
        return (
            "<div class='msg-group'><div class='pane-empty'>"
            "<div class='pane-empty__title'>Ask a question, or use an example below</div>"
            "<div class='pane-empty__hint'>Every answer is checked against what the agent "
            "actually read and ran. The run trace in the middle shows each check, including "
            "the refusals.</div></div></div>"
        )
    out = []
    for turn in turns:
        out.append(_message("you", turn["question"], user=True))
        out.append(_message("physearth", turn["answer"], faulted=turn.get("faulted")))
    return "<div class='msg-group'>%s</div>" % "".join(out)


def _message(who, text, user=False, running=False, faulted=False):
    body = _e(text).replace("\n", "<br>") if user else answer_html(text, running)
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


def chips():
    items = "".join(
        "<button type='button' class='chip' data-example=\"%s\">"
        "<span class='dot'></span>%s</button>" % (_e(text), _e(_short(text)))
        for text in EXAMPLES
    )
    return (
        "<div class='subpanel' style='padding-top:11px'><div class='chips'>%s</div></div>" % items
    )


def _short(text, limit=44):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


# ---------------------------------------------------------------- run trace


BADGES = {
    "model_call": ("badge--mono", "MODEL CALL", "step-card--model"),
    "tool_call": ("badge--model", "TOOL", "step-card--tool"),
    "tool_start": ("badge--step", "RUNNING", "step-card--thinking"),
    "harness_block": ("badge--block", "BLOCKED", "step-card--block"),
    "harness_pass": ("badge--ok", "PASSED", "step-card--pass"),
    "harness_stop": ("badge--warn", "STOPPED", "step-card--warn"),
    "harness_giveup": ("badge--warn", "GAVE UP", "step-card--warn"),
    "untrusted_content": ("badge--warn", "BOUNDARY", "step-card--warn"),
    "empty_response": ("badge--mute", "UPSTREAM RETRY", "step-card--muted"),
    "literature_tier": ("badge--model", "LITERATURE TIER", "step-card--tool"),
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
    return (
        "<div class='meter'><div class='meter__head'><span>%s</span><b>%s / %s</b></div>"
        "<div class='meter__track'><div class='meter__fill %s' style='width:%d%%'></div></div>"
        "%s</div>"
        % (
            _e(label),
            value,
            cap,
            tone,
            pct,
            "<div class='meter__note'>%s</div>" % _e(note) if note else "",
        )
    )


def trace(events, state, running=False):
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

    used, cap = budget.used()
    # The meters read the session, not the turn: the budget that actually stops the
    # conversation is cumulative, and so is the evidence the citation check resolves against.
    session = state.get("session") or state
    turns = session.get("turns", 0)
    meters = "".join(
        [
            _meter(
                "model calls",
                session.get("model_calls", 0),
                session.get("max_model_calls", 1),
                note="%d this question, cap %d"
                % (state.get("model_calls", 0), state.get("max_model_calls", 0)),
            ),
            _meter(
                "tool calls",
                session.get("tool_calls", 0),
                session.get("max_tool_calls", 1),
                "is-violet",
                note="%d this question, cap %d"
                % (state.get("tool_calls", 0), state.get("max_tool_calls", 0)),
            ),
            _meter(
                "context",
                state.get("prompt_tokens", 0),
                state.get("context_ceiling", 1),
                "is-ok",
            ),
            _meter("hourly quota", used, cap, "is-ok", note="shared by every visitor"),
        ]
    )
    counters = "".join(
        [
            "<span class='badge badge--mono'>%d question%s in this session</span>"
            % (turns, "" if turns == 1 else "s"),
            "<span class='badge badge--%s'>%d blocked</span>"
            % (
                "block" if session.get("interventions") else "mute",
                session.get("interventions", 0),
            ),
            "<span class='badge badge--%s'>%d boundary</span>"
            % (
                "warn" if session.get("boundary_flags") else "mute",
                session.get("boundary_flags", 0),
            ),
            "<span class='badge badge--%s'>%d QC failure%s</span>"
            % (
                "block" if session.get("qc_failures") else "ok",
                session.get("qc_failures", 0),
                "" if session.get("qc_failures") == 1 else "s",
            ),
            "<span class='badge badge--src'>%d model run%s</span>"
            % (session.get("model_runs", 0), "" if session.get("model_runs") == 1 else "s"),
            "<span class='badge badge--src'>%d section%s read</span>"
            % (
                len(session.get("sections_read") or ()),
                "" if len(session.get("sections_read") or ()) == 1 else "s",
            ),
        ]
    )
    return (
        "%s<div class='subpanel grow'><div class='subpanel__scroll'>%s</div></div>"
        "<div class='subpanel'><div class='meters'>%s</div>"
        "<div class='counters'>%s</div></div>" % (head, body, meters, counters)
    )


# ---------------------------------------------------------------- evidence


def _figure_card(figure, index):
    sources = figure.get("provenance") or ["model_run"]
    ribbon = "fig-ribbon--measured" if "measured" in sources else "fig-ribbon--computed"
    label = " + ".join("model run" if s == "model_run" else s for s in sources)
    legend = "".join(
        "<span class='badge badge--%s'>%s</span> %s "
        % (
            "ok" if item["source"] == "measured" else "model",
            "measured" if item["source"] == "measured" else "model run",
            _e("%s, %s, %d points" % (item["label"], item["origin"], item["n_points"])),
        )
        for item in figure.get("series") or []
    )
    return (
        "<div class='fig-card' data-anchor='fig-%d'>"
        "<div class='fig-ribbon %s'>%s<span class='handle'>%s</span></div>"
        "<div class='fig-body'><img alt='%s' src='%s'>"
        "<div class='fig-cap'>%s</div></div></div>"
        % (
            index,
            ribbon,
            _e(label),
            _e((figure.get("series") or [{}])[0].get("handle", "")),
            _e(figure.get("title") or "chart"),
            _e(figure.get("png", "")),
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


_ENVIRONMENT = None


def environment_card(report=None):
    """The startup self-check, on screen instead of only on stdout.

    It answers, for anyone looking at the deployed Studio, the questions a reviewer would
    otherwise have to take on trust: which Python and which package versions are actually
    running, whether the temporary directory survives a restart, which outbound hosts this
    instance can reach, and which models registered and which were refused and why.
    """
    global _ENVIRONMENT
    if report is None:
        if _ENVIRONMENT is None:
            from physearth import diagnostics

            _ENVIRONMENT = diagnostics.collect()
        report = _ENVIRONMENT

    packages = "".join(
        "<div class='info-row'><span class='k'>%s</span><span class='v'>%s</span></div>"
        % (_e(name), _e(version))
        for name, version in (report.get("packages") or {}).items()
    )
    probes = "".join(
        "<tr><td class='name'>%s</td><td><span class='badge badge--%s'>%s</span></td>"
        "<td class='num'>%s s</td></tr>"
        % (
            _e(probe["name"]),
            "ok" if probe["ok"] else "block",
            _e(probe["status"]),
            _e(probe["elapsed_s"]),
        )
        for probe in (report.get("network") or [])
    )
    models = report.get("models") or {}
    registered = ", ".join(
        "%s v%s" % (row["name"], row["version"]) for row in models.get("registered") or []
    )
    rejected = models.get("rejected") or []
    rejected_html = (
        "".join(
            "<div class='info-row'><span class='k'>rejected</span><span class='v'>%s</span></div>"
            % _e(item["reason"])
            for item in rejected
        )
        or "<div class='info-row'><span class='k'>rejected</span><span class='v'>none</span>"
        "</div>"
    )
    boot = report.get("boot") or {}
    runtime = report.get("runtime") or {}
    smrt = report.get("smrt") or {}
    return (
        "<div class='ev-card' data-anchor='environment'>"
        "<div class='ev-card__head'><span class='badge badge--mono'>environment</span>"
        "<span class='ev-card__title'>What this instance actually is</span></div>"
        "<div class='info-card'>"
        "<div class='info-row'><span class='k'>python</span><span class='v'>%s</span></div>"
        "<div class='info-row'><span class='k'>cores</span><span class='v'>%s</span></div>"
        "<div class='info-row'><span class='k'>temp dir writable</span><span class='v'>%s</span>"
        "</div>"
        "<div class='info-row'><span class='k'>process boot</span><span class='v'>%s</span></div>"
        "<div class='info-row'><span class='k'>online literature</span><span class='v'>%s</span>"
        "</div>"
        "<div class='info-row'><span class='k'>models</span><span class='v'>%s</span></div>"
        "%s"
        "<div class='info-row'><span class='k'>smrt warm-up</span><span class='v'>%s</span></div>"
        "</div>"
        "<table class='table'><thead><tr><th>outbound host</th><th>reachable</th>"
        "<th>elapsed</th></tr></thead><tbody>%s</tbody></table>"
        "<div class='info-card'>%s</div>"
        "<div class='pane-note' style='margin:8px 0 0'>Collected once when this process "
        "started. The reachability of the literature hosts is what decides whether the "
        "online layer can work at all; when it cannot, the agent is told the service was "
        "unreachable and never that nothing was found.</div>"
        "</div>"
        % (
            _e(runtime.get("python", "?")),
            _e(runtime.get("cpu_count", "?")),
            _e(boot.get("writable")),
            _e(boot.get("boot_count", "?")),
            _e("on" if report.get("online") else "off"),
            _e(registered or "none"),
            rejected_html,
            _e(
                "%s K V-pol in %s s" % (smrt.get("tb_v"), smrt.get("cold_call_s"))
                if smrt.get("available")
                else smrt.get("error", "not available")
            ),
            probes,
            packages,
        )
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
    corpus += environment_card()

    opened = len(sections) + len(datasets)
    sources_pane = (
        "<input class='scope-input' type='radio' name='pe-scope' id='pe-scope-read' checked>"
        "<input class='scope-input' type='radio' name='pe-scope' id='pe-scope-all'>"
        "<div class='scope'><label for='pe-scope-read'>Opened here (%d)</label>"
        "<label for='pe-scope-all'>Corpus and environment (%d)</label></div>"
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
