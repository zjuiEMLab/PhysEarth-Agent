"""The run trace: one card per event, including the refusals."""

import json

from apps.studio.views.parts import _disclosure, _disclosure_markup, _kv, _meter
from apps.studio.views.text import _e, _mono, _svg
from physearth.api import budget

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
    "research_mode_selected": ("badge--ok", "RESEARCH MODE", "step-card--pass"),
    "route": ("badge--ok", "ROUTE", "step-card--pass"),
}


def _badge(kind):
    """The badge for an event kind. An unlisted kind keeps its name, as words that wrap."""
    return BADGES.get(kind, ("badge--mute", kind.replace("_", " ").upper(), "step-card--muted"))

APPROVAL_WORDS = {
    "approve": "You approved this call.",
    "reject": "You declined this call. The refusal went back to the model as a tool result, "
    "so it has to answer without it or propose something different.",
    "superseded": "A new question arrived instead of an answer, so this call was dropped "
    "without running. A request that nobody answered is never treated as an approval.",
}


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
        if event.get("reasoning_tokens"):
            rows.append(("thinking", "%s tokens" % event["reasoning_tokens"], ""))
        if event.get("reasoning_chars"):
            rows.append(("reasoning", "%d characters, not shown" % event["reasoning_chars"], ""))
        if event.get("first_token_s") is not None:
            rows.append(("first token", "%.1fs after the request" % float(event["first_token_s"]), ""))
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
        from physearth.api import approval as gate

        described = gate.describe(event.get("name"), event.get("arguments"))
        rows = [(k, v, "") for k, v in sorted(described["parameters"].items())]
        return (
            "<div class='step-card__line'>The agent wants to run <b>%s</b> as %s. Nothing "
            "has been computed yet. The turn is paused until you run it or decline it.</div>"
            "%s" % (_e(described["model"]), _e(described["shape"]), _kv(rows) if rows else "")
        )

    if kind == "approval":
        return "<div class='step-card__line'>%s</div>" % _e(
            APPROVAL_WORDS.get(event.get("decision"), event.get("decision") or "")
        )

    if kind == "route":
        labels = {"run": "direct model question", "answer": "explanation", "reproduce": "paper reproduction",
                  "auto": "all tools"}
        return "<div class='step-card__line'>%s: %s (%s).</div>" % (
            _e(labels.get(event.get("path"), event.get("path"))), _e(event.get("reason") or ""),
            _e(event.get("source") or ""),
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
    badge_class, badge_text, card_class = _badge(event["kind"])
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


# The steps that are the machine doing its job. They stay in the trace -- nothing is
# hidden, and every one of them is one click away -- but they no longer compete for
# attention with the moments a human is being asked to act on. Everything not listed
# here renders expanded: the refusals, the gates, the boundary flags, the upstream
# faults. `harness_pass` is here because a check that passed is reassurance, not news;
# the collapsed row still counts them.
ROUTINE_KINDS = frozenset(
    {"model_call", "tool_call", "tool_start", "harness_pass", "literature_tier"}
)


def _step_line(event):
    """One routine step, in one line."""
    kind = event["kind"]
    if kind == "model_call":
        line = "%s prompt, %s completion tokens" % (
            event.get("prompt_tokens") or "?",
            event.get("completion_tokens") or "?",
        )
        if event.get("reasoning_tokens"):
            line += " (%s thinking)" % event["reasoning_tokens"]
        if event.get("first_token_s") is not None and event.get("elapsed_s"):
            line += " · first token at %.0fs" % float(event["first_token_s"])
        return line
    return str(event.get("summary") or event.get("detail") or "").strip()


def _routine_detail(event, index):
    """What is left of a routine step once its one line is already on the row.

    Not `_event_body`: that opens with the same summary the row now carries inline, and
    wraps the arguments in a disclosure of their own. Repeating the line and nesting the
    disclosure made the collapsed trace larger than the expanded one it replaced.
    """
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
        if event.get("reasoning_tokens"):
            rows.append(("thinking", "%s tokens" % event["reasoning_tokens"], ""))
        if event.get("reasoning_chars"):
            rows.append(("reasoning", "%d characters, not shown" % event["reasoning_chars"], ""))
        if event.get("first_token_s") is not None:
            rows.append(("first token", "%.1fs after the request" % float(event["first_token_s"]), ""))
        return _kv(rows)

    if kind == "tool_call":
        rows = []
        data = event.get("data") or {}
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
        arguments = event.get("arguments")
        return "%s%s" % (
            _kv(rows) if rows else "",
            "<pre>%s</pre>" % _e(json.dumps(arguments, ensure_ascii=False, indent=1))
            if arguments
            else "",
        )

    if kind == "harness_pass":
        markers = sorted(set(event.get("markers") or []))
        if not markers:
            return ""
        return "<div class='marker-list'>%s</div>" % "".join(
            "<span class='badge badge--mono'>%s</span>" % _e(m) for m in markers
        )

    if kind == "tool_start":
        return ""
    return _event_body(event, index)


def _step_row(event, index):
    """A routine step as a single row, with its detail behind a disclosure."""
    badge_class, badge_text, _card = _badge(event["kind"])
    row_class = "step-card--row-model" if event["kind"] == "model_call" else ""
    name = _mono(event.get("name") or event.get("rule") or "")
    right = ""
    if event.get("elapsed_s") is not None:
        right = "%.2fs" % event["elapsed_s"]
    body = _routine_detail(event, index)
    return (
        "<div class='step-card step-card--row %s'><div class='step-card__head'>"
        "<span class='step-card__n'>%02d</span>"
        "<span class='badge %s'>%s</span>%s"
        "<span class='step-card__line step-card__line--inline'>%s</span>"
        "<span class='step-card__time'>%s</span></div>"
        "%s</div>"
        % (
            row_class,
            index,
            badge_class,
            _e(badge_text),
            name,
            _e(_step_line(event)),
            _e(right),
            _disclosure_markup("step-%d" % index, "detail", body) if body else "",
        )
    )


def _step_group(events, first_index):
    """Consecutive steps of one kind, as a counted row that opens to the steps."""
    if len(events) == 1:
        return _step_row(events[0], first_index)
    badge_class, badge_text, _card = _badge(events[0]["kind"])
    named = [str(e.get("name") or e.get("rule") or "").strip() for e in events]
    trail = " → ".join(n for n in named if n) or "%d steps" % len(events)
    inner = "".join(
        _step_row(event, first_index + offset) for offset, event in enumerate(events)
    )
    return (
        "<details class='step-card step-card--group'>"
        "<summary class='step-card__head'>"
        "<span class='step-card__n'>%02d</span>"
        "<span class='badge %s'>%s ×%d</span>"
        "<span class='step-card__line step-card__line--inline'>%s</span>"
        "</summary><div class='step-card__group-body'>%s</div></details>"
        % (first_index, badge_class, _e(badge_text), len(events), _e(trail), inner)
    )


def _grouped(events):
    """Walk the trace, gathering consecutive same-kind routine steps.

    Same-kind only. Grouping across kinds collapsed more, but the summary line then had
    to describe a mixture and stopped being readable at a glance.
    """
    blocks, index, position = [], 0, 1
    while index < len(events):
        event = events[index]
        if event["kind"] not in ROUTINE_KINDS:
            blocks.append(_event_card(event, position))
            index += 1
            position += 1
            continue
        run = [event]
        cursor = index + 1
        while cursor < len(events) and events[cursor]["kind"] == event["kind"]:
            run.append(events[cursor])
            cursor += 1
        blocks.append(_step_group(run, position))
        position += len(run)
        index = cursor
    return "".join(blocks)


def _seconds(value):
    """A duration the way a person reads it: 48s, 5m 18s, 1h 04m."""
    total = max(0, int(round(float(value or 0))))
    hours, rest = divmod(total, 3600)
    minutes, seconds = divmod(rest, 60)
    if hours:
        return "%dh %02dm" % (hours, minutes)
    if minutes:
        return "%dm %02ds" % (minutes, seconds)
    return "%ds" % seconds


def turn_timing(events):
    """Where this question's time went, from the trace itself.

    "Before first token" is the part of the model time spent waiting for the first
    streamed character. With a thinking model that hides its reasoning, it is the
    reasoning, and it is usually most of the wait.
    """
    calls = [e for e in events or () if e.get("kind") == "model_call"]
    return {
        "model_s": sum(float(e.get("elapsed_s") or 0) for e in calls),
        "first_token_s": sum(float(e.get("first_token_s") or 0) for e in calls),
        "model_calls": len(calls),
        "output_tokens": sum(int(e.get("completion_tokens") or 0) for e in calls),
        "tool_s": sum(
            float(e.get("elapsed_s") or 0) for e in events or () if e.get("kind") == "tool_call"
        ),
    }


def _clock(seconds, since=None, base=0.0):
    """A duration, or a clock the page keeps running from `since` (epoch seconds)."""
    if since:
        return "<b data-clock-since='%.3f' data-clock-base='%.3f'>%s</b>" % (
            since, base, _e(_seconds(base)),
        )
    return "<b>%s</b>" % _e(_seconds(seconds))


def _timing_html(session, events, running):
    clock = session.get("turn_clock") or {}
    started = clock.get("started_at")
    if not started:
        return ""
    totals = session.get("timing_totals") or {}
    timing = turn_timing(events)
    if running:
        question = _clock(0, since=started)
        overall = _clock(0, since=started, base=float(totals.get("wall_s") or 0))
    else:
        wall = float(clock.get("finished_at") or started) - float(started)
        question = _clock(wall)
        overall = _clock(float(totals.get("wall_s") or 0))
    items = [
        ("this question", question),
        (
            "model · %d call%s" % (timing["model_calls"], "" if timing["model_calls"] == 1 else "s"),
            _clock(timing["model_s"]),
        ),
        ("before first token", _clock(timing["first_token_s"])),
        ("tools and model runs", _clock(timing["tool_s"])),
        ("session, agent time", overall),
    ]
    return "<div class='trace-timing'>%s</div>" % "".join(
        "<div class='trace-timing__item'><span>%s</span>%s</div>" % (_e(label), value)
        for label, value in items
    )


def _trace_metrics(state, events=None, running=False):
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
    return "<div class='trace-metrics'>%s<div class='meters'>%s</div><div class='counters'>%s</div></div>" % (
        _timing_html(session, events, running), meters, counters,
    )


def trace_metrics(state, events=None, running=False):
    return _trace_metrics(state, events, running)


def _header_clock(state, running):
    session = state.get("session") or {}
    clock = session.get("turn_clock") or {}
    started = clock.get("started_at")
    if not started:
        return ""
    if running:
        return "<span class='trace-clock' title='time on this question'>%s</span>" % _clock(
            0, since=started
        )
    if clock.get("finished_at"):
        return "<span class='trace-clock' title='time on the last question'>%s</span>" % _clock(
            float(clock["finished_at"]) - float(started)
        )
    return ""


def trace(events, state, running=False, include_footer=True):
    head = (
        "<div class='subpanel' style='padding-bottom:0'><div class='sec-head'>%s"
        "<span class='sec-title'>Run trace</span>"
        "<span class='sec-count'>%d event%s</span>%s</div></div>"
        % (
            _svg("trace", "sec-icon"), len(events), "" if len(events) == 1 else "s",
            _header_clock(state, running),
        )
    )
    if not events and not running:
        body = (
            "<div class='pane-empty'><div class='pane-empty__title'>Nothing has run yet</div>"
            "<div class='pane-empty__hint'>Every model call, every tool call and every system "
            "refusal appears here as it happens.</div></div>"
        )
    else:
        body = _grouped(events)
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

    footer = _trace_metrics(state, events, running) if include_footer else ""
    return "<div class='trace-layout trace-layout--events'>%s<div class='subpanel grow'><div class='subpanel__scroll'>%s</div></div>%s</div>" % (head, body, footer)
