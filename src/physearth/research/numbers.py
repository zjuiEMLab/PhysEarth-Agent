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
    """Every number the session's records hold, or that its own declarations state."""
    produced, configured = _sources(session)
    return produced + configured


def _sources(session):
    """(produced, configured): what the runs and figures gave, and what they were given.

    The distinction is the point. A produced value is a measurement the report may round; a
    configured value is what a run was handed, and a report that writes it differently is
    describing a different run. Matching both with a rounding tolerance made the check nearly
    vacuous: with thousands of recorded numbers, a two-decimal claim finds a neighbour
    somewhere. A report's "3.226" in a run's place was accepted because 3.2263157894736847 is
    a coordinate on its own stickiness sweep, and "1.66" because 1.6631578947368424 is
    another -- neither of them the figure's 3.280 and 1.658.
    """
    session = session if isinstance(session, dict) else {}
    project_id, research_id = _research_ids(session)
    produced = []
    configured = []
    for record in artifacts.recorded_runs(project_id, research_id):
        for key in ("series", "points", "diagnostics", "series_summary"):
            _walk(record.get(key), produced)
        for key in ("spec", "axis"):
            _walk(record.get(key), configured)
    for record in artifacts.recorded_figures(project_id, research_id):
        for key in ("series", "comparisons", "quality_review", "preview"):
            _walk(record.get(key), produced)
        _walk(record.get("provenance"), configured)
    # A figure of a computed quantity draws a saved script result, and the figure record
    # keeps only the handle. So the numbers on the figure were not in this check at all:
    # a report that quoted the eight scaling factors its own figure showed was refused for
    # four of them, while two wrong ones passed by coincidence. Read what the figure drew.
    _walk(_drawn_values(session), produced)
    try:
        cards = registry.all_models(session)
    except Exception:  # a registry that cannot be read is not a reason to skip the check
        cards = {}
    for model in cards.values():
        _walk(getattr(model, "card", None) or {}, configured)
    return produced, configured


def _drawn_values(session):
    """The arrays behind the figure handles this session holds, as numbers."""
    from physearth.harness import results

    owner = session.get("id")
    handles = []
    for figure in session.get("figures") or ():
        for item in figure.get("series") or ():
            if isinstance(item, dict) and item.get("handle"):
                handles.append(item["handle"])
    for record in session.get("analysis_runs") or ():
        for item in record.get("saved_results") or ():
            if isinstance(item, dict) and item.get("handle"):
                handles.append(item["handle"])
    values = []
    for handle in dict.fromkeys(handles):
        payload = results.get(handle, owner) or {}
        for key in ("series", "axis", "points", "units"):
            _walk(payload.get(key), values)
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


def _stated(literal, values):
    """Whether a configuration value is this number, as the record holds it.

    A produced value may be rounded by the report; a configured one may not, because writing
    it differently describes a different run. Only the unit conversions a reader makes are
    allowed, since 100 um and 1e-4 m are the same length however they are written.
    """
    wanted = float(literal)
    tolerance = abs(wanted) * 1e-9 + 1e-12
    for value in values:
        for scale in _UNIT_SCALES:
            if abs(value * scale - wanted) <= tolerance:
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
    produced, configured = _sources(session)
    if not produced and not configured:
        return []
    values = produced + configured
    findings = []
    seen = set()
    for raw in re.split(r"(?<=[.!?。！？])\s+|\n+", str(answer or "")):
        if not raw.strip():
            continue
        # A bracket that names the paper marks the number inside it as the paper's. It does
        # not mark the rest of the sentence: "ka = 0.3426 m-1 (paper: 0.3426 m-1)" states the
        # run's value outside the bracket and the paper's inside it, and reading the whole
        # sentence as the paper's would have missed the very mismatch this check exists for.
        paper_spans = [(item.start(), item.end()) for item in _PAPER_BRACKET.finditer(raw)]
        sentence = _PAPER_BRACKET.sub(" ", raw)
        if _PAPER_SENTENCE.search(sentence):
            continue  # a sentence about the paper is not a sentence about the runs
        for match in _MEASURED.finditer(sentence):
            literal = match.group(1)
            if _YEAR.match(literal):
                continue
            if _matches(literal, produced) or _stated(literal, configured):
                continue
            if _IDENTIFIER.search(sentence[: match.start()]):
                continue
            # "SMART reports ka (see the publication, 2018) as 0.3426": the marker sits in
            # the bracket between the claim and the number, and still attributes it.
            before = raw[max(0, match.start() - 60): match.start()]
            if _PAPER_SENTENCE.search(before) or any(
                start <= match.start() < end for start, end in paper_spans
            ):
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


# A number the report writes as the paper's, in a sentence that cites the paper, has to be a
# number that section states.
_CITATION = re.compile(r"\[([a-z0-9-]+)#([A-Za-z0-9_.-]+)\]")
# The paper has to be the subject of the claim, and the claim has to be next to the number:
# "Our curve gives 3.28, above the 2.1 the paper reports" attributes the second number, not
# the first, and a bare verb is not an attribution at all.
_ATTRIBUTION = re.compile(
    r"(?:the\s+paper|the\s+publication|the\s+article|the\s+study|论文|文献|原文|"
    r"section\s*[\d.]+|§\s*[\d.]+)[^.;!?]{0,60}?"
    r"(?:\bstate[sd]?|\breport(?:s|ed)?|\bgive[s]?|\bgave|\bpublish(?:es|ed)|"
    r"\bequivalent\s+to|指出|表明|报道|报告|给出|相当于|对应)",
    re.I,
)


def _section_numbers(key):
    """Every number the cited section text writes, or None when it cannot be read."""
    slug, _, section_id = key.partition("#")
    try:
        from physearth.corpus import knowledge
    except ImportError:
        return None
    section = knowledge.read_section(slug, section_id)
    if not section:
        return None
    return [
        float(match.group(0))
        for match in re.finditer(r"-?\d+(?:\.\d+)?", str(section.get("text") or ""))
    ]


def misattributed(session, answer):
    """Numbers written as the paper's that the section they cite does not state.

    A delivered report said Section 3.2 "states that higher scaling factors (up to 3.747)
    correspond to lower stickiness values approaching 0.1" [smrt-v1#09]. The section says
    3.5. The 3.747 is not a scaling factor at all: it is a coordinate on the stickiness sweep
    of the agent's own run, read out of a tool result and written into the paper's mouth. The
    sentence passed every check there was, because a citation was verified by whether the
    section had been opened, never by what it says.

    Returns [{"number", "section", "context"}], empty when there is nothing to check.
    """
    findings = []
    seen = set()
    for raw in re.split(r"(?<=[.!?。！？])\s+|\n+", str(answer or "")):
        if not raw.strip():
            continue
        keys = ["%s#%s" % pair for pair in _CITATION.findall(raw)]
        if not keys:
            continue
        stated = []
        readable = False
        for key in dict.fromkeys(keys):
            numbers = _section_numbers(key)
            if numbers is None:
                continue
            readable = True
            stated.extend(numbers)
        if not readable:
            continue  # a section this installation cannot read is not a section to police
        for match in _MEASURED.finditer(raw):
            literal = match.group(1)
            if _YEAR.match(literal) or _IDENTIFIER.search(raw[: match.start()]):
                continue
            before = raw[max(0, match.start() - 80): match.start()]
            if not _ATTRIBUTION.search(before):
                continue  # the number is the run's, not the paper's; `unsupported` owns it
            if _matches(literal, stated):
                continue
            key = (literal, raw.strip()[:80])
            if key in seen:
                continue
            seen.add(key)
            findings.append({
                "number": literal,
                "section": ", ".join(keys),
                "context": " ".join(raw.split())[:220],
            })
    return findings


def misattributed_correction(findings):
    """What the agent is told when the paper is made to say something it does not."""
    lines = [
        "- %s is written as the paper's in a sentence citing %s, and that section does not "
        "state it. The sentence: %s" % (item["number"], item["section"], item["context"])
        for item in findings[:4]
    ]
    return (
        "These numbers are attributed to the paper, but the section cited does not state "
        "them:\n%s\n"
        "Correct the report: quote the number the cited section actually states, or say the "
        "number is your own reading of a figure rather than a statement of the paper. A "
        "number that came from one of your own runs or a sweep is not the paper's, and saying "
        "the paper states it is worse than not quoting the paper at all." % "\n".join(lines)
    )


def misattributed_summary(findings):
    numbers = ", ".join(sorted({item["number"] for item in findings}))
    return (
        "The report attributes numbers to the paper that the cited section does not state: %s."
        % numbers
    )
