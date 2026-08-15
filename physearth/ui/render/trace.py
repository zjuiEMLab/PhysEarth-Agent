"""The run trace: one card per event, including the refusals."""

import json

from physearth import budget
from physearth.ui.render.parts import _disclosure, _kv, _meter
from physearth.ui.render.text import _e, _mono, _svg

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
