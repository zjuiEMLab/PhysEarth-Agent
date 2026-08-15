"""Small builders shared by more than one panel."""

import json

from frontend.views.text import _e
from physearth.api import knowledge


def _reproduction_state(session):
    """Return paper state discovered through literature reads and the generated plan."""
    session = session if isinstance(session, dict) else {}
    context = session.get("research_context") or {}
    project = session.get("research") or {}
    plan = project.get("plan") or {}
    paper_session = context.get("paper_session") or {}
    if not context.get("reproduction_case") and not paper_session and not plan:
        return None
    paper_slug = paper_session.get("paper") or ""
    card = knowledge.card(paper_slug) if paper_slug else {}
    paper_section = paper_session.get("paper_section") or ""
    source_section = paper_session.get("source_section") or ""
    return {
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
