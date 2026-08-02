import html
import json
import re

from physearth import knowledge

MARKER = re.compile(r"\[([a-z0-9-]+)#(\d{1,3})\]")

BADGES = {
    "model_call": ("model", "model"),
    "tool_call": ("tool", "tool"),
    "harness_block": ("block", "blocked"),
    "harness_pass": ("pass", "passed"),
    "harness_stop": ("stop", "stopped"),
    "harness_giveup": ("block", "gave up"),
    "empty_response": ("stop", "upstream retry"),
}

EMPTY_TRACE = (
    '<div class="pe-trace"><div class="pe-empty">Ask a question and every model call, '
    "tool call and system intervention will appear here.</div></div>"
)


def _code(text):
    return '<code>%s</code>' % html.escape(str(text))


def _detail(event):
    kind = event["kind"]
    if kind == "model_call":
        return "%.2fs &middot; %s prompt tokens &middot; %s completion tokens" % (
            event["elapsed_s"],
            event["prompt_tokens"],
            event["completion_tokens"],
        )
    if kind == "tool_call":
        arguments = json.dumps(event["arguments"], ensure_ascii=False)
        return "%s %s<br>%s <span style='opacity:.6'>(%.3fs)</span>" % (
            _code(event["name"]),
            _code(arguments),
            html.escape(event["summary"]),
            event["elapsed_s"],
        )
    if kind == "harness_block":
        return "<b>%s</b> refused the answer: %s" % (
            html.escape(event["rule"]),
            html.escape(str(event["detail"])),
        )
    if kind == "harness_pass":
        markers = sorted(set(event.get("markers", [])))
        chips = " ".join(_code(m) for m in markers) or "no markers to check"
        return "%s satisfied &middot; %s" % (html.escape(event["rule"]), chips)
    return html.escape(
        json.dumps({k: v for k, v in event.items() if k not in ("kind", "at")}, ensure_ascii=False)
    )


def trace(events, state):
    if not events:
        return EMPTY_TRACE
    rows = []
    for index, event in enumerate(events, 1):
        badge_class, badge_text = BADGES.get(event["kind"], ("stop", event["kind"]))
        step_class = "pe-step"
        if badge_class == "block":
            step_class += " is-block"
        elif badge_class == "pass":
            step_class += " is-pass"
        rows.append(
            '<div class="%s"><div class="n">%d</div><div class="body">'
            '<span class="pe-badge %s">%s</span>'
            '<div class="detail">%s</div></div></div>'
            % (step_class, index, badge_class, badge_text, _detail(event))
        )
    read = sorted(state["sections_read"])
    metrics = [
        ("model calls", "%d/%d" % (state["model_calls"], state["max_model_calls"])),
        ("tool calls", "%d/%d" % (state["tool_calls"], state["max_tool_calls"])),
        ("interventions", str(state["interventions"])),
        ("tokens", "%d in / %d out" % (state["prompt_tokens"], state["completion_tokens"])),
        ("sections read", ", ".join(read) if read else "none"),
    ]
    summary = "".join(
        '<span class="pe-metric">%s <b>%s</b></span>' % (html.escape(k), html.escape(v))
        for k, v in metrics
    )
    return '<div class="pe-trace">%s<div class="pe-summary">%s</div></div>' % (
        "".join(rows),
        summary,
    )


def hero(model_name):
    papers = len(knowledge.slugs())
    sections = len(knowledge.citation_keys())
    pills = [
        ("accent", "%d open-access papers" % papers),
        ("", "%d citable sections" % sections),
        ("", "CC-BY corpus"),
        ("", model_name),
        ("", "Apache-2.0"),
    ]
    pill_html = "".join(
        '<span class="pe-pill %s">%s</span>' % (cls, html.escape(text)) for cls, text in pills
    )
    return (
        '<div class="pe-hero">'
        "<h1>PhysEarth-Agent</h1>"
        '<p class="pe-sub">An open-source GeoAI agent for physical Earth models.</p>'
        '<p class="pe-claim">The point is not that it can talk about physics, but that it '
        "cannot assert physics it did not read. Every scientific claim carries a marker that "
        "must resolve to a section the agent actually opened in this conversation; the system "
        "checks each one after the answer is written and sends the answer back if a marker "
        "does not resolve. The run trace records every model call, every tool call, and every "
        "refusal.</p>"
        '<div class="pe-pills">%s</div>'
        "</div>" % pill_html
    )


def annotate_markers(answer):
    known = knowledge.citation_keys()

    def replace(match):
        key = "%s#%s" % (match.group(1), match.group(2))
        mark = "✓" if key in known else "✗"
        return "`%s %s`" % (mark, key)

    return MARKER.sub(replace, answer or "")
