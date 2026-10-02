"""Every pixel of the interface, as plain strings.

Nothing here imports Gradio, so all of it is testable without a browser. Every value
that reaches the page goes through `html.escape` first: literature text, dataset rows
and model output are all untrusted input on a public deployment.

This module is the bottom of that: escaping, icons, citation markers, prose.
"""

import html
import re

from physearth.api import agent

CITE = re.compile(r"\[([a-z0-9][a-z0-9-]*)#(\d{1,3})\]")
MODEL_CITE = re.compile(r"\[model:([A-Za-z0-9_-]+)@([^\]\s]+)\]")
DATA_CITE = re.compile(r"\[data:([a-z0-9][a-z0-9-]*)\]")
ABS_CITE = re.compile(r"\[abs:(10\.\d{4,9}/[^\]\s]+)\]", re.I)
SKILL_CITE = re.compile(r"\[skill:([a-z0-9][a-z0-9-]*)\]")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
CODE = re.compile(r"`([^`]+)`")
SAFE_SUB = re.compile(r"&lt;(/?)(sub|sup)&gt;", re.I)
SECTION_PREVIEW_CHARS = 620


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
