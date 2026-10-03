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
    """Lower-case, ASCII exponents and no spaces, so 'kg m-3', 'kg m⁻³' and 'kg/m3' meet."""
    text = str(text or "").translate(_SUPERSCRIPTS).lower()
    text = re.sub(r"[\^·*_]", " ", text)
    text = re.sub(r"([a-z]+)\s*-\s*(\d)", r"/\1\2", text)
    return re.sub(r"\s+", "", text)


def _raw(text):
    """Only case, exponents and spaces normalised: PDF text often runs units together, 'kgm-3'."""
    return re.sub(r"\s+", "", str(text or "").translate(_SUPERSCRIPTS).lower())


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


def source_passages(session, quantity, limit=MAX_PASSAGES):
    """Sentences from the sections this session opened that give the quantity as a number.

    A sentence qualifies when it carries a number with the quantity's unit and names the
    quantity, so a passage about something else that happens to quote a density is not
    offered. Sentences that speak of a range, threshold or limit come first. Each comes
    with the marker the report must cite it by.
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
    return [(key, sentence) for _, key, sentence in found[:limit]]


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
    """The gate: every asked quantity is stated with its unit, or honestly left open.

    'Left open' is accepted only when the opened sources hold no passage that gives it.
    """
    if not applies(session, state):
        return {"rule": "asked_value", "passed": True, "skipped": True, "missing": []}
    missing = []
    for quantity in asked_quantities(session):
        if states_value(text, quantity["unit"]):
            continue
        passages = source_passages(session, quantity)
        if not passages and declares_unidentified(text):
            continue
        missing.append({**quantity, "passages": passages})
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
            part += " State that value with its marker, labelled as the paper's, and give " \
                    "the value the recorded results show separately."
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
