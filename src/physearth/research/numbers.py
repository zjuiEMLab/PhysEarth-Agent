"""Every number a report states as a run's own must be a number that run produced.

A reproduction report presented the default-IBA absorption coefficient as 0.3426 m-1, the
value the paper prints, while the run it cited had returned 0.3428. The paper's number was
written into the run's place and then quoted again in brackets as the paper's, so the
agreement looked exact. Nothing checked it: the record held 0.3428 the whole time.

This reads the recorded runs and the recorded figures and refuses that claim, rather than the
report. A number is accepted when a recorded value equals it at the precision it was written
-- rounding or truncating to the written digits, and allowing the unit scales a person
converts between, so 100 um and 1e-4 m are the same length. Numbers in a sentence that
attributes them to the paper are left alone, since quoting the paper is the point of a
reproduction, as are the values the model cards document and the identifiers a report uses
(Section 3.1.1, Fig. 6). The check is about the slot a number is written into, not about the
number itself.
"""

import re

from physearth import artifacts, registry

# Precise enough to be a measurement rather than a count: a decimal point, or three digits.
_MEASURED = re.compile(r"(?<![\w.])(\d+\.\d+|\d{3,}(?!\.\d))(?![\w.])")
# The paper's own values sit in brackets after the run's, and are theirs to state.
_PAPER_BRACKET = re.compile(r"\([^()]*\b(?:paper|publication|论文)\b[^()]*\)", re.I)
# A sentence that is about the paper is not a sentence about the runs.
_PAPER_SENTENCE = re.compile(r"\b(?:paper|publication|文献|论文|et al\.?|doi)\b", re.I)
# Numbers that name something rather than measure it.
_IDENTIFIER = re.compile(
    r"(?:\b(?:section|sec|fig|figure|table|eq|equation|chapter|appendix|version|v)\b\.?\s*"
    r"|§\s*|#\s*)$",
    re.I,
)
_YEAR = re.compile(r"^(?:19|20)\d\d$")
# Unit conversions a reader makes between the paper and the model's own units.
_UNIT_SCALES = (1.0, 1e-3, 1e-6, 1e-9, 1e3, 1e6, 1e9)


def _walk(value, found):
    if isinstance(value, bool) or value is None:
        return found
    if isinstance(value, (int, float)):
        found.append(float(value))
    elif isinstance(value, str):
        # A quantity written into a spec or a description as text still counts: a named
        # level, a substrate, the density the model documents for its own correction.
        for match in re.finditer(r"-?\d+(?:\.\d+)?", value):
            found.append(float(match.group(0)))
    elif isinstance(value, dict):
        for item in value.values():
            _walk(item, found)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _walk(item, found)
    return found


def _research_ids(session):
    session = session if isinstance(session, dict) else {}
    project = session.get("research") or {}
    return session.get("id") or "shared", project.get("research_id") or session.get("id")


def known_values(session):
    """Every number the session's records hold, or that its own declarations state.

    Three sources, in the order a report draws on them: what the runs produced or were given,
    what the figures' own comparisons and checks measured, and what the registered model
    cards document. A number from the paper is handled by the sentence it appears in.
    """
    project_id, research_id = _research_ids(session)
    values = []
    for record in artifacts.recorded_runs(project_id, research_id):
        for key in ("spec", "axis", "series", "points", "diagnostics", "series_summary"):
            _walk(record.get(key), values)
    for record in artifacts.recorded_figures(project_id, research_id):
        for key in ("series", "comparisons", "quality_review", "provenance", "preview"):
            _walk(record.get(key), values)
    try:
        cards = registry.all_models(session if isinstance(session, dict) else None)
    except Exception:  # a registry that cannot be read is not a reason to skip the check
        cards = {}
    for model in cards.values():
        _walk(getattr(model, "card", None) or {}, values)
    return values


def _matches(literal, values):
    """Whether a recorded value equals this written number at the precision written."""
    decimals = len(literal.split(".", 1)[1]) if "." in literal else 0
    wanted = float(literal)
    # Written to `decimals` digits, a value is the same measurement whether it was rounded
    # or truncated -- but two units in the last digit is a different number.
    tolerance = 10.0 ** -decimals
    for value in values:
        for scale in _UNIT_SCALES:
            scaled = value * scale
            if abs(scaled - wanted) <= tolerance:
                return True
    return False


def _nearest(literal, values):
    """The recorded value closest to this number, for the correction to name."""
    wanted = float(literal)
    if not values:
        return None
    closest = min(values, key=lambda value: abs(value - wanted))
    if closest == 0:
        return "0"
    magnitude = abs(closest)
    digits = 4 if magnitude < 1 else (3 if magnitude < 100 else 1)
    return ("%.*f" % (digits, closest)).rstrip("0").rstrip(".")


def unsupported(session, answer):
    """Numbers the report states as a run's, that no recorded value accounts for.

    Returns [{"number", "context", "recorded"}], empty when there is nothing to say or
    nothing recorded to check against.
    """
    values = known_values(session)
    if not values:
        return []
    text = _PAPER_BRACKET.sub(" ", str(answer or ""))
    findings = []
    seen = set()
    for sentence in re.split(r"(?<=[.!?。！？])\s+|\n+", text):
        if not sentence.strip() or _PAPER_SENTENCE.search(sentence):
            continue
        for match in _MEASURED.finditer(sentence):
            literal = match.group(1)
            if _YEAR.match(literal) or _matches(literal, values):
                continue
            if _IDENTIFIER.search(sentence[: match.start()]):
                continue
            key = (literal, sentence.strip()[:80])
            if key in seen:
                continue
            seen.add(key)
            findings.append({
                "number": literal,
                "context": " ".join(sentence.split())[:200],
                "recorded": _nearest(literal, values),
            })
    return findings


def correction(findings):
    """What the agent is told when a report's numbers are not the runs' numbers."""
    lines = []
    for item in findings[:6]:
        recorded = item.get("recorded")
        lines.append(
            "- %s is not accounted for by any recorded run or figure%s. The sentence: %s"
            % (
                item["number"],
                "; the nearest recorded value is %s" % recorded if recorded else "",
                item["context"],
            )
        )
    return (
        "These numbers in your report are stated as the runs' own, but no recorded run or "
        "figure accounts for them:\n%s\n"
        "Rewrite the report: quote each run's value as the tool returned it, and if you are "
        "quoting the paper instead, say so in the sentence and put the paper's value in "
        "brackets after the run's. Never change a run's number to match the paper."
        % "\n".join(lines)
    )


def summary(findings):
    """The warning recorded when the report was delivered anyway."""
    numbers = ", ".join(sorted({item["number"] for item in findings}))
    return (
        "The report states numbers no recorded run or figure accounts for: %s. Quote the run's "
        "own value, and mark a value quoted from the paper as the paper's." % numbers
    )
