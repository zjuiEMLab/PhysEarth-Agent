"""Does the source a parameter cites support the label it was given?

A plan says where each value came from. Two labels are checked against the text they point at,
because a wrong one reads as stronger evidence than the plan has:

* ``paper_explicit`` -- the cited section must state the value, and state it for this
  experiment. A paper quotes many configurations: a worked example, another figure's setup. A
  sentence that gives the value but is scoped to one of those describes a different experiment, so
  it is context, not evidence for this one.
* ``user_specified`` -- the number must be in what the user asked.

A claim the text does not support is relabelled, not refused: the registered model's own default
when the value is the default, otherwise an assumption. The repair is recorded with the reason, so
the reviewer sees the label change and why. Nothing here knows a paper, a figure or a value.
"""

import re
from decimal import Decimal, InvalidOperation

from physearth.corpus import knowledge
from physearth.research import asked
from physearth.research.common import _provenance_confidence

_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_FIGURE = re.compile(
    r"\bfig(?:ure)?s?\.?\s*(\d+)(?:\s*(?:-|–|to|and|,)\s*(\d+))?", re.IGNORECASE
)
_ILLUSTRATIVE = re.compile(r"\b(?:code\s+example|example|for\s+instance|illustrat\w*|tutorial)\b", re.IGNORECASE)


def _significand(value):
    """The digits of a number without its magnitude: 0.0001, 100 and 1e-4 all give "1".

    A paper writes a length in micrometres and a model takes metres; comparing digits finds the
    value either way. The cost is that unrelated numbers can share digits, which only ever lets a
    claim stand, never wrongly rejects it.
    """
    try:
        digits = Decimal(str(value)).normalize().as_tuple().digits
    except (InvalidOperation, ValueError):
        return None
    return "".join(map(str, digits)).rstrip("0") or "0"


def _numbers(text):
    return {_significand(match) for match in _NUMBER.findall(str(text or ""))}


def _figures(text):
    """Figure numbers a passage names, with ranges and lists expanded."""
    found = set()
    for first, second in _FIGURE.findall(str(text or "")):
        low = int(first)
        found.update(range(low, int(second) + 1) if second and int(second) >= low else {low})
        if second:
            found.add(int(second))
    return found


def target_figures(targets):
    """Figure numbers the plan's reproduction targets name."""
    found = set()
    for target in targets or ():
        if not isinstance(target, dict):
            continue
        for key in ("id", "source_id", "label"):
            match = re.search(r"(?:figure|fig)[^0-9]*(\d+)", str(target.get(key) or ""), re.IGNORECASE)
            if match:
                found.add(int(match.group(1)))
    return found


def _section_text(ref):
    slug, _, section_id = str(ref or "").partition("#")
    if not section_id or section_id.lower().startswith("fig"):
        return None
    section = knowledge.read_section(slug, section_id)
    return (section or {}).get("text") or None


def _scoped_elsewhere(sentence, target_figs):
    """True when the sentence describes a different experiment than the one being reproduced."""
    if _ILLUSTRATIVE.search(sentence):
        return True
    named = _figures(sentence)
    return bool(named and target_figs and not (named & target_figs))


def _names_the_quantity(sentence, name, unit):
    """The sentence speaks of this parameter, by name or by its unit, not just of a like number."""
    lowered = sentence.lower()
    stem = re.split(r"[_\W]+", str(name or "").lower())[0][:5]
    if len(stem) >= 4 and stem in lowered:
        return True
    token = (str(unit or "").split() or [""])[0]
    return token not in ("", "none", "count") and bool(
        re.search(r"(?<![A-Za-z])" + re.escape(token) + r"(?![A-Za-z])", sentence)
    )


def paper_claim_problem(ref, value, target_figs, name="", unit=""):
    """Why the cited section does not support the value, or "" when it does or cannot be told."""
    text = _section_text(ref)
    if text is None:
        return ""
    wanted = _significand(value)
    if wanted is None:
        return ""
    stating = [
        s for s in asked._sentences(text)
        if wanted in _numbers(s) and (not name or _names_the_quantity(s, name, unit))
    ]
    if not stating:
        return "the cited section does not state this value"
    if all(_scoped_elsewhere(s, target_figs) for s in stating):
        return "the cited section states this value for a different experiment (an example or another figure)"
    return ""


def user_claim_problem(question_text, value):
    wanted = _significand(value)
    if wanted is None or not str(question_text or "").strip():
        return ""
    return "" if wanted in _numbers(question_text) else "the user's question does not contain this value"


def _question_text(session):
    context = (session or {}).get("research_context") or {}
    project = (session or {}).get("research") or {}
    return " ".join(
        str(part) for part in (context.get("question"), project.get("question")) if part
    )


def audit(session, mappings, targets, spec_of, paper_conditions, condition_provenance, repairs):
    """Relabel mappings whose cited source does not support the label. Returns the count."""
    figures = target_figures(targets)
    first_plan = not (session.get("research") or {}).get("plan")
    question = _question_text(session)
    changed = 0
    for item in mappings:
        label = item.get("provenance_class")
        value = item.get("mapped_value")
        if label not in ("paper_explicit", "user_specified"):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        spec = spec_of(item.get("model"), item.get("model_input")) or {}
        if spec.get("type") not in ("number", "integer"):
            continue
        name = str(item.get("model_input") or "")
        if name.startswith("sweep") or str(spec.get("unit") or "") in ("count", "same as the swept parameter"):
            continue
        if label == "paper_explicit":
            problem = paper_claim_problem(
                item.get("evidence_ref"), value, figures, name, spec.get("unit")
            )
        elif first_plan:
            problem = user_claim_problem(question, value)
        else:
            problem = ""
        if not problem:
            continue
        default = spec.get("default")
        is_default = isinstance(default, (int, float)) and float(default) == float(value)
        new_label = "backend_default" if is_default else "model_assumption"
        before = dict(item)
        item["provenance_class"] = new_label
        item["evidence_ref"] = ""
        item["paper_value"] = None
        item["confidence"], item["confidence_basis"] = _provenance_confidence(new_label)
        item["rationale"] = (
            "Labelled %s by the plan, but %s; relabelled %s." % (label, problem, new_label)
        )
        paper_conditions.pop(name, None)
        condition_provenance.pop(name, None)
        repairs.append({
            "field": "parameter_mapping.%s.%s.provenance_class" % (item.get("model"), name),
            "from": label,
            "to": new_label,
            "reason": problem,
            "provenance": new_label,
            "source": "cited_source_check",
            "evidence": before.get("evidence_ref"),
        })
        changed += 1
    return changed


def relabel_defaults(mappings, spec_of, repairs):
    """An assumption whose value is the model card's own default is a default, not an assumption.

    The reviewer is asked to decide on assumptions. A value the card would have supplied anyway is
    not a decision, and listing it as one buries the values that are. Only a numeric physical
    value is relabelled: a choice of formulation is a design decision even when it matches the
    default, and a sweep's sampling is numerics.
    """
    changed = 0
    for item in mappings:
        value = item.get("mapped_value")
        if item.get("provenance_class") != "model_assumption":
            continue
        if item.get("evidence_ref") or item.get("paper_value") not in (None, ""):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        spec = spec_of(item.get("model"), item.get("model_input")) or {}
        name = str(item.get("model_input") or "")
        if spec.get("type") not in ("number", "integer") or name.startswith("sweep"):
            continue
        if str(spec.get("unit") or "") in ("count", "same as the swept parameter"):
            continue
        default = spec.get("default")
        if not isinstance(default, (int, float)) or isinstance(default, bool) or float(default) != float(value):
            continue
        item["provenance_class"] = "backend_default"
        item["confidence"], item["confidence_basis"] = _provenance_confidence("backend_default")
        item["rationale"] = "The value is the registered model card's default; it is not a decision."
        repairs.append({
            "field": "parameter_mapping.%s.%s.provenance_class" % (item.get("model"), name),
            "from": "model_assumption",
            "to": "backend_default",
            "reason": "the value equals the model card's default",
            "provenance": "backend_default",
            "source": "registered_model_declaration",
        })
        changed += 1
    return changed


_SEMI_INFINITE = re.compile(r"semi[- ]infinite|infinitely\s+(?:deep|thick)", re.IGNORECASE)
STAND_IN_RATIO = 10


def semi_infinite_stated(session, target_figs):
    """The opened section that states a semi-infinite medium for this experiment, or None.

    A sentence counts when it is about the comparison in general or about the target's own
    figure. One about a worked example, or about another figure's setup, does not.
    """
    for key in sorted((session or {}).get("sections_read") or ()):
        slug, _, section_id = str(key).partition("#")
        section = knowledge.read_section(slug, section_id) if section_id else None
        for sentence in asked._sentences((section or {}).get("text")):
            if _SEMI_INFINITE.search(sentence) and not _scoped_elsewhere(sentence, target_figs):
                return key
    return None


def stands_in_for_semi_infinite(spec):
    """True for a parameter whose card says a large value stands in for a semi-infinite medium."""
    return bool(_SEMI_INFINITE.search(str((spec or {}).get("description") or "")))


def semi_infinite_unopened(session, target_figs):
    """A section of an opened paper that states a semi-infinite medium and has not been read."""
    opened = set((session or {}).get("sections_read") or ())
    for slug in sorted({str(key).partition("#")[0] for key in opened}):
        for item in knowledge.section_index(slug) or ():
            key = "%s#%s" % (slug, item["id"])
            if key in opened:
                continue
            section = knowledge.read_section(slug, item["id"])
            for sentence in asked._sentences((section or {}).get("text")):
                if _SEMI_INFINITE.search(sentence) and not _scoped_elsewhere(sentence, target_figs):
                    return key, sentence[: asked.MAX_PASSAGE_CHARS]
    return None
