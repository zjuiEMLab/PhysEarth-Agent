import re

from physearth import switches

CITATION_PATTERN = re.compile(r"\[([a-z0-9-]+)#(\d{1,3})\]")
MODEL_PATTERN = re.compile(r"\[(?:model:)?([A-Za-z0-9_-]+)@([^\]\s]+)\]")
DATA_PATTERN = re.compile(r"\[data:([a-z0-9-]+)\]")
ABSTRACT_PATTERN = re.compile(r"\[abs:(10\.\d{4,9}/[^\]\s]+)\]", re.I)
SKILL_PATTERN = re.compile(r"\[skill:([a-z0-9-]+)\]")
UNCITED_ANSWER_CHARS = 400
MAX_INTERVENTIONS = 3

# What an abstract-level citation is not allowed to carry. These are the units of a
# result, not of a configuration: an abstract may well say a study was at 37 GHz and 55
# degrees, and citing it for that is honest. Saying the brightness temperature was 213 K
# on the strength of an abstract is not, because the number was never read in context and
# cannot be checked against anything this system holds.
RESULT_UNIT = re.compile(
    r"(?<![\w.])\d+(?:\.\d+)?\s*(?:K\b|kelvin\b|dB\b|decibels?\b|m3\s*m-3|m\^?3\s*m\^?-3)",
    re.I,
)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+|\n+")


def find_markers(text):
    return ["%s#%s" % (slug, sid) for slug, sid in CITATION_PATTERN.findall(text or "")]


def find_model_markers(text):
    return ["%s@%s" % (name, version) for name, version in MODEL_PATTERN.findall(text or "")]


def find_data_markers(text):
    return DATA_PATTERN.findall(text or "")


def find_abstract_markers(text):
    return [d.lower() for d in ABSTRACT_PATTERN.findall(text or "")]


def find_skill_markers(text):
    return SKILL_PATTERN.findall(text or "")


def check_citations(
    text,
    sections_read,
    models_run=(),
    datasets_read=(),
    abstracts_seen=(),
    skills_read=(),
):
    text = text or ""
    # An [abs:doi] marker also matches the literature pattern's shape in some DOIs, so it
    # is removed before the other markers are counted.
    plain = ABSTRACT_PATTERN.sub(" ", text)
    markers = find_markers(plain)
    model_markers = find_model_markers(plain)
    data_markers = find_data_markers(plain)
    abstract_markers = find_abstract_markers(text)
    skill_markers = find_skill_markers(text)
    unresolved = sorted({m for m in markers if m not in sections_read})
    unresolved += sorted({m for m in model_markers if m not in set(models_run)})
    unresolved += sorted({m for m in data_markers if m not in set(datasets_read)})
    unresolved += sorted(
        {"abs:" + m for m in abstract_markers if m not in {a.lower() for a in abstracts_seen}}
    )
    # "I followed the comparison protocol" is a claim like any other. It resolves only for
    # a method note this conversation actually opened, which turns a piece of self-praise
    # into a fact the run trace can confirm.
    unresolved += sorted({"skill:" + m for m in skill_markers if m not in set(skills_read)})
    return {
        "rule": "citation_integrity",
        "markers": markers
        + ["model:" + m for m in model_markers]
        + ["data:" + m for m in data_markers]
        + ["abs:" + m for m in abstract_markers]
        + ["skill:" + m for m in skill_markers],
        "unresolved": unresolved,
        "passed": not unresolved,
    }


def check_abstract_depth(text):
    """An abstract-level citation may not carry a result value.

    The tier exists so that "the paper reports doing X" and "the value is Y" cannot be
    supported by the same evidence. Enforcing it in the harness rather than asking for it
    in the prompt is the difference between a rule and a request.
    """
    offending = []
    for sentence in SENTENCE_SPLIT.split(text or ""):
        dois = find_abstract_markers(sentence)
        if not dois:
            continue
        value = RESULT_UNIT.search(ABSTRACT_PATTERN.sub(" ", sentence))
        if value:
            offending.append({"doi": dois[0], "value": value.group(0).strip()})
    if not offending:
        return {"rule": "abstract_depth", "passed": True, "reason": "", "offending": []}
    return {
        "rule": "abstract_depth",
        "passed": False,
        "offending": offending,
        "reason": "%d claim(s) state a result value on the strength of an abstract: %s"
        % (
            len(offending),
            "; ".join("%s cited for %s" % (o["doi"], o["value"]) for o in offending[:3]),
        ),
    }


def abstract_depth_correction(result):
    return (
        "Your answer was blocked by the abstract depth rule: %s. A marker of the form "
        "[abs:doi] means you have seen the paper's metadata and abstract, not its text, so "
        "it can support a statement that the study exists and what it was about, but never "
        "a number in kelvin, decibels or volumetric soil moisture. Either take the number "
        "out and keep the qualitative statement, or read the paper: call ingest_paper with "
        "that DOI if it is open access, and then cite the section you actually read. "
        "Re-send the full answer." % result["reason"]
    )


def check_evidence(text, sections_read, model_runs=0):
    if sections_read or model_runs:
        return {"rule": "evidence_gate", "passed": True, "reason": ""}
    stripped = (text or "").strip()
    if len(stripped) <= UNCITED_ANSWER_CHARS:
        return {"rule": "evidence_gate", "passed": True, "reason": "short reply, not a claim"}
    return {
        "rule": "evidence_gate",
        "passed": False,
        "reason": "answer of %d characters produced without reading any literature section "
        "or running any physical model" % len(stripped),
    }


def citation_correction(result):
    return (
        "Your answer was blocked by the citation integrity check. These markers resolve to "
        "nothing you did in this conversation: %s. A marker of the form [slug#id] must name "
        "a section you opened with read_literature, and a marker of the form "
        "[model:name@version] must name a model you actually ran or whose declaration you read, "
        "and a marker of the form [data:slug] must name a reference dataset you actually "
        "queried, and a marker of the form [skill:slug] must name a method note you actually "
        "opened with read_literature. Note that a model name is not a paper slug. Fix or drop "
        "each one and re-send the full answer."
        % ", ".join(result["unresolved"])
    )


def evidence_correction(result):
    return (
        "Your answer was blocked by the evidence gate: %s. Gather evidence first: read the "
        "sections you need with read_literature, and run the physical model with run_model "
        "if the question asks what a model predicts. Then answer." % result["reason"]
    )


def check_budget(state):
    """Two ceilings. The turn's is soft: it ends this answer and the visitor can ask
    again. The session's is hard: it ends the conversation until the session is
    cleared, and it is what actually protects the shared quota."""
    session = state.get("session") or {}
    for name, label in (("model_calls", "model call"), ("tool_calls", "tool call")):
        cap = session.get("max_%s" % name)
        if cap is not None and session.get(name, 0) >= cap:
            return {
                "rule": "budget",
                "passed": False,
                "scope": "session",
                "reason": "session %s budget reached (%d of %d)"
                % (label, session.get(name, 0), cap),
            }
    for name, label in (("model_calls", "model call"), ("tool_calls", "tool call")):
        if state.get(name, 0) >= state["max_%s" % name]:
            return {
                "rule": "budget",
                "passed": False,
                "scope": "turn",
                "reason": "%s budget for this question reached (%d of %d)"
                % (label, state.get(name, 0), state["max_%s" % name]),
            }
    return {"rule": "budget", "passed": True, "scope": "", "reason": ""}


def review_final(text, state):
    if not switches.resolve(state.get("switches"))["harness"]:
        return (
            {"rule": "citation_integrity", "passed": True, "markers": find_markers(text), "off": True},
            None,
        )
    checks = [
        check_evidence(
            text,
            state["sections_read"],
            state.get("model_runs", 0) + len(state.get("datasets_read", ())),
        ),
        check_citations(
            text,
            state["sections_read"],
            state.get("models_run", ()),
            state.get("datasets_read", ()),
            state.get("abstracts_seen", ()),
            state.get("skills_read", ()),
        ),
        check_abstract_depth(text),
    ]
    corrections = {
        "evidence_gate": evidence_correction,
        "citation_integrity": citation_correction,
        "abstract_depth": abstract_depth_correction,
    }
    for check in checks:
        if not check["passed"]:
            return check, corrections[check["rule"]](check)
    return checks[1], None
