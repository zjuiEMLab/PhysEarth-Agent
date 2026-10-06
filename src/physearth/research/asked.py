"""What the question asked a value of, and whether the final report answers it.

A report can describe a figure well and still never say what was asked. When a question asks
at what X, or over what X range, something happens, the answer is a number with X's unit, and
the opened paper evidence usually holds it. The failure this module closes is the report that
opened the section stating the range and then wrote about curve ordering instead.

Nothing here knows a benchmark, a paper or an expected value. The asked quantities come from
the question and the plan's swept parameters, the unit from the model card, and the passages
from the sections the session actually opened.
"""

import re

from physearth import registry
from physearth.corpus import knowledge
from physearth.research.charts import _asked_values, _parameter_phrase

MAX_PASSAGES = 4
MAX_PASSAGE_CHARS = 320

_UNIDENTIFIED = re.compile(
    r"not\s+(?:identifiable|identified|determinable|determined|stated|specified|reported|"
    r"given|available)|cannot\s+be\s+(?:identified|determined|established)|"
    r"does\s+not\s+(?:state|specify|report|identify|give)|no\s+(?:range|value|threshold)\s+"
    r"(?:is|was)\s+(?:stated|given|reported)",
    re.IGNORECASE,
)
_SUPERSCRIPTS = str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹−–—", "-0123456789---")


def _project(session):
    return (session or {}).get("research") or {}


def asked_quantities(session):
    """The swept quantities the question asks a value or range of, each with its unit."""
    project = _project(session)
    plan = project.get("plan") or {}
    text = "%s\n%s" % (
        project.get("question") or plan.get("question") or "",
        ((session or {}).get("research_context") or {}).get("question") or "",
    )
    quantities = []
    for name in _asked_values(text, plan.get("runs")):
        unit = ""
        for run in plan.get("runs") or ():
            entry = registry.get(str(run.get("model") or ""))
            spec = ((entry.card.get("parameters") or {}).get(name) or {}) if entry else {}
            unit = unit or spec.get("unit") or ""
        quantities.append({"name": name, "phrase": _parameter_phrase(name), "unit": unit})
    return quantities


def _compact(text):
    """Lower-case, ASCII exponents and no spaces, so 'm s-1', 'm s⁻¹' and 'm/s1' meet."""
    text = str(text or "").translate(_SUPERSCRIPTS).lower()
    text = re.sub(r"[\^·*_]", " ", text)
    text = re.sub(r"([a-z]+)\s*-\s*(\d)", r"/\1\2", text)
    return re.sub(r"(?<=\d)to(?=\d)", "-", re.sub(r"\s+", "", text))


def _raw(text):
    """Only case, exponents and spaces normalised: PDF text often runs units together, 'kgm-3'."""
    squeezed = re.sub(r"\s+", "", str(text or "").translate(_SUPERSCRIPTS).lower())
    return re.sub(r"(?<=\d)to(?=\d)", "-", squeezed)


def states_value(text, unit):
    """True when the text gives a number, or a range of numbers, with the unit."""
    if not str(unit or "").strip() or str(unit).strip() == "none":
        return bool(re.search(r"\d", str(text or "")))
    number = r"\d+(?:\.\d+)?"
    span = number + r"(?:(?:to|-)" + number + r")?"
    return any(
        re.search(span + re.escape(form(unit)), form(text))
        for form in (_compact, _raw)
    )


def declares_unidentified(text):
    return bool(_UNIDENTIFIED.search(str(text or "")))


def _sentences(text):
    flat = re.sub(r"\s+", " ", re.sub(r"[#>*`]", " ", str(text or "")))
    return [piece.strip() for piece in re.split(r"(?<=[.;])\s+(?=[A-Z(])", flat) if piece.strip()]


_CUES = re.compile(
    r"range|between|below|above|threshold|valid|up\s+to|tends?\s+to|converge|diverge|"
    r"only\s+for|\d\s*[-–]\s*\d",
    re.IGNORECASE,
)
_NUMBER = r"\d+(?:\.\d+)?"
_SPAN = r"(" + _NUMBER + r"(?:-" + _NUMBER + r")?)"


def _candidates(session, quantity):
    """(cue count, marker, sentence) for every opened-section sentence that gives the quantity.

    A sentence qualifies when it carries a number with the quantity's unit and names the
    quantity, so a passage about something else that happens to quote a number in that unit is not
    offered. Sentences that speak of a range, threshold or limit rank first.
    """
    stem = quantity["phrase"].lower().split()[0][:5]
    found = []
    for key in sorted((session or {}).get("sections_read") or ()):
        slug, _, section_id = str(key).partition("#")
        section = knowledge.read_section(slug, section_id) if section_id else None
        if not section:
            continue
        for sentence in _sentences(section["text"]):
            if stem in sentence.lower() and states_value(sentence, quantity["unit"]):
                found.append((len(_CUES.findall(sentence)), key, sentence[:MAX_PASSAGE_CHARS]))
    found.sort(key=lambda item: -item[0])
    return found


def source_passages(session, quantity, limit=MAX_PASSAGES):
    """The passages to offer: marker and sentence, range and threshold sentences first."""
    return [(key, sentence) for _, key, sentence in _candidates(session, quantity)[:limit]]


def _spans(text, unit):
    spans = []
    for form in (_compact, _raw):
        for match in re.finditer(_SPAN + re.escape(form(unit)), form(text)):
            if match.group(1) not in spans:
                spans.append(match.group(1))
    return spans


def required_spans(session, quantity):
    """The numbers the opened sources give for the quantity, e.g. '4-8' for a range.

    Taken from the sentences that speak of a range, threshold or limit when there are any,
    otherwise from the best sentence. A report that gives only the range it swept does not
    state what the paper says.
    """
    candidates = _candidates(session, quantity)
    cued = [item for item in candidates if item[0] > 0][:2] or candidates[:1]
    spans = []
    for _, _, sentence in cued:
        for span in _spans(sentence, quantity["unit"]):
            if span not in spans:
                spans.append(span)
    return spans


def states_source_value(text, spans, unit):
    return any(
        (span + form(unit)) in form(text) for span in spans for form in (_compact, _raw)
    )


def evidence_block(session):
    """A report-prompt block listing what the opened sources say about each asked quantity."""
    lines = []
    for quantity in asked_quantities(session):
        passages = source_passages(session, quantity)
        if not passages:
            continue
        lines.append("Asked: %s (%s)." % (quantity["phrase"], quantity["unit"] or "no unit"))
        lines.extend('- [%s] "%s"' % (key, sentence) for key, sentence in passages)
    if not lines:
        return ""
    return (
        "PAPER PASSAGES THAT GIVE WHAT THE QUESTION ASKS FOR (opened this session; state the "
        "value they give, with its marker, in the opening answer):\n" + "\n".join(lines)
    )


def applies(session, state=None):
    """Only a report for an approved plan that has run is held to the asked values."""
    project = _project(session)
    if project.get("phase") not in ("approved", "completed"):
        return False
    return bool((session or {}).get("model_runs") or (state or {}).get("model_runs"))


def check(text, session, state=None):
    """The gate: every asked quantity is answered from the evidence, or honestly left open.

    When an opened source gives the quantity as a number or range, the report must state that
    value with its unit; a different number with the same unit (the range it swept) does not
    count. When none does, any value with the unit, or an honest "not identifiable", will do.
    """
    if not applies(session, state):
        return {"rule": "asked_value", "passed": True, "skipped": True, "missing": []}
    missing = []
    for quantity in asked_quantities(session):
        spans = required_spans(session, quantity)
        if spans:
            if states_source_value(text, spans, quantity["unit"]):
                continue
        elif states_value(text, quantity["unit"]) or declares_unidentified(text):
            continue
        missing.append(
            {**quantity, "passages": source_passages(session, quantity), "spans": spans}
        )
    return {"rule": "asked_value", "passed": not missing, "missing": missing}


def correction(result):
    parts = []
    for item in result["missing"]:
        part = (
            "The question asks for the %s as a value or range in %s, and the report does not "
            "state one." % (item["phrase"], item["unit"] or "its unit")
        )
        if item["passages"]:
            part += " The sources opened in this session say: " + " ".join(
                '[%s] "%s"' % (key, sentence) for key, sentence in item["passages"]
            )
            part += (
                " State that value (%s) with its marker, labelled as the paper's, and give "
                "the value the recorded results show separately."
                % ", ".join("%s %s" % (span, item["unit"]) for span in item["spans"])
            )
        else:
            part += (
                " No opened source gives it; say plainly that it is not identifiable from the "
                "evidence gathered."
            )
        parts.append(part)
    return (
        "Revise the final report before finishing. " + " ".join(parts)
        + " Keep every other part of the report as it is."
    )


def remember_question(session, question):
    """Keep the user's reproduction question for as long as its project is in progress.

    The turns that follow a plan ("the plan is approved, execute every run") are not new
    questions, and the report is held to the question the project began with. A new question
    is remembered when none is held, or when the project it belonged to is finished.
    """
    context = session.setdefault("research_context", {})
    project = session.get("research") or {}
    if not context.get("question") or not project or project.get("phase") == "completed":
        context["question"] = question
