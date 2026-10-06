"""Small builders shared by more than one panel."""

import json

from apps.studio.views.text import _e
from physearth.api import knowledge, research


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


def _disclosure_markup(key, label, markup):
    """Like `_disclosure`, for a body that is already rendered and already escaped.

    The plain one escapes its text into a <pre>, which is right for a JSON blob and
    wrong for a block of cards that were each escaped as they were built.
    """
    return (
        "<details class='disclosure disclosure--markup' data-key='%s'>"
        "<summary>%s</summary><div class='disclosure__body'>%s</div></details>"
        % (_e(key), _e(label), markup)
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


_TAG_HELP = {
    "extracted": "stated in the paper, or read off its figure",
    "derived": "follows from what the paper states",
    "user": "given in the question",
    "default": "the model card's default; the paper does not say",
    "assumed": "chosen by the agent, with a reason",
    "guessed": "chosen by the agent with no stated reason",
    "unlabelled": "no source recorded",
    "mixed": "differs between runs",
}


def _source_chip(tag, ref=""):
    return "<span class='src src--%s' title='%s'>%s</span>%s" % (
        _e(tag), _e(_TAG_HELP.get(tag, "")), _e(tag),
        " <span class='src-ref'>%s</span>" % _e(ref) if ref else "",
    )


def _breakable(text):
    """Escaped text that may wrap after an underscore, never inside a word."""
    return _e(text).replace("_", "_<wbr>")


def _parameter_cell(item):
    """`frequency` with its code name and the card's one-line description under it."""
    name = item["name"]
    shown = item.get("label") or name
    suffix = " (%s)" % name
    title = shown[: -len(suffix)] if shown.endswith(suffix) else shown
    return "<b>%s</b>%s%s" % (
        _e(title),
        " <code>%s</code>" % _e(name) if title != name else "",
        "<div class='plan-sheet__about'>%s</div>" % _e(item["about"]) if item.get("about") else "",
    )


def plan_sheet_html(plan, conditions=True):
    """The plan as conditions once, with their sources, and a matrix of what differs per run."""
    sheet = research.sheet.build(plan)
    if not sheet["groups"]:
        return ""
    out = ["<div class='plan-sheet'>"]
    if conditions and sheet["decisions"]:
        items = "".join(
            "<li><b>%s</b> = %s %s%s</li>" % (
                _e(d.get("label") or d["name"]),
                _e(d.get("shown") or research.sheet.fmt(d["value"])),
                _source_chip(d["tag"]),
                " <span class='plan-sheet__hint'>%s</span>" % _e(d["note"]) if d.get("note") else "",
            )
            for d in sheet["decisions"]
        )
        out.append(
            "<div class='plan-sheet__decide'><b>Needs your decision (%d)</b>"
            "<span class='plan-sheet__hint'> chosen without a source in the paper; approve, or ask for a change</span>"
            "<ul>%s</ul></div>" % (len(sheet["decisions"]), items)
        )
    for group in sheet["groups"]:
        title = "%s%s · %d run%s" % (
            group["model"] or "model", " v%s" % group["version"] if group["version"] else "",
            len(group["runs"]), "" if len(group["runs"]) == 1 else "s",
        )
        purpose = group.get("purpose") or ""
        if group.get("outputs"):
            purpose = "%s%sOutputs used: %s." % (
                purpose, " " if purpose else "", ", ".join(group["outputs"]),
            )
        out.append(
            "<div class='plan-sheet__group'><div class='plan-sheet__title'>%s</div>%s"
            % (_e(title), "<div class='plan-sheet__purpose'>%s</div>" % _e(purpose) if purpose else "")
        )
        if conditions:
            rows = [
                [
                    _parameter_cell(c),
                    _breakable(c.get("shown") or research.sheet.fmt(c["value"])),
                    _source_chip(c["tag"], c["ref"]),
                    _e(c["note"]) or "<span class='plan-sheet__hint'>-</span>",
                ]
                for c in group["conditions"]
            ]
            out.append(
                "<div class='plan-sheet__label'>Conditions, the same in every run</div>"
                + _plan_table(("Parameter", "Value", "Source", "Note"), rows, css="plan-sheet-table")
            )
            if group["sweep"]:
                out.append("<div class='plan-sheet__sweep'><b>Swept in every run:</b> %s</div>" % _e(group["sweep"]))
        columns = group["columns"]
        headers = ["Run"] + [
            (c.get("label") or c["name"])
            + (" (%s)" % research.sheet.unit_text(c["unit"]) if research.sheet.unit_text(c["unit"]) else "")
            for c in columns
        ]
        if group["sweep_varies"]:
            headers.append("Sweep")
        headers.append("Feeds")
        rows = []
        for run in group["runs"]:
            cells = ["<b>%s</b>%s%s" % (
                _e(run["id"]),
                " <span class='plan-sheet__stage'>%s</span>" % _e(run["stage"]) if run["stage"] and run["stage"] != "main" else "",
                "<div class='plan-sheet__about'>%s</div>" % _e(run["label"]) if run.get("label") and run["label"] != run["id"] else "",
            )]
            cells += [_breakable(research.sheet.fmt(run["values"].get(c["name"]))) for c in columns]
            if group["sweep_varies"]:
                cells.append(_e(run["sweep"]))
            cells.append(_e(", ".join(run["feeds"]) or "-"))
            rows.append(cells)
        out.append(
            "<div class='plan-sheet__label'>Runs, only what differs</div>"
            + _plan_table(headers, rows, css="plan-sheet-table")
        )
        if columns:
            out.append("<div class='plan-sheet__sources'>%s</div>" % " ".join(
                "<span>%s %s</span>" % (_e(c.get("label") or c["name"]), _source_chip(c["tag"], c["ref"])) for c in columns
            ))
        out.append("</div>")
    out.append("</div>")
    return "".join(out)
