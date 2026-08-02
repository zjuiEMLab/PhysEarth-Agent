import re

CITATION_PATTERN = re.compile(r"\[([a-z0-9-]+)#(\d{1,3})\]")
UNCITED_ANSWER_CHARS = 220
MAX_INTERVENTIONS = 3


def find_markers(text):
    return ["%s#%s" % (slug, sid) for slug, sid in CITATION_PATTERN.findall(text or "")]


def check_citations(text, sections_read):
    markers = find_markers(text)
    unresolved = sorted({m for m in markers if m not in sections_read})
    return {
        "rule": "citation_integrity",
        "markers": markers,
        "unresolved": unresolved,
        "passed": not unresolved,
    }


def check_evidence(text, sections_read):
    if sections_read:
        return {"rule": "evidence_gate", "passed": True, "reason": ""}
    stripped = (text or "").strip()
    if len(stripped) <= UNCITED_ANSWER_CHARS:
        return {"rule": "evidence_gate", "passed": True, "reason": "short reply, not a claim"}
    return {
        "rule": "evidence_gate",
        "passed": False,
        "reason": "answer of %d characters produced without reading any literature section"
        % len(stripped),
    }


def citation_correction(result):
    return (
        "Your answer was blocked by the citation integrity check. These markers do not "
        "resolve to any section you read in this conversation: %s. Either read the section "
        "with read_literature and keep the marker, or remove the claim. Re-send the full "
        "answer." % ", ".join(result["unresolved"])
    )


def evidence_correction(result):
    return (
        "Your answer was blocked by the evidence gate: %s. Call list_literature and then "
        "read_literature on the sections you need, then answer with citation markers."
        % result["reason"]
    )


def check_budget(state):
    if state["model_calls"] >= state["max_model_calls"]:
        return {"rule": "budget", "passed": False, "reason": "model call budget reached"}
    if state["tool_calls"] >= state["max_tool_calls"]:
        return {"rule": "budget", "passed": False, "reason": "tool call budget reached"}
    return {"rule": "budget", "passed": True, "reason": ""}


def review_final(text, state):
    checks = [check_evidence(text, state["sections_read"]), check_citations(text, state["sections_read"])]
    for check in checks:
        if not check["passed"]:
            correction = (
                evidence_correction(check)
                if check["rule"] == "evidence_gate"
                else citation_correction(check)
            )
            return check, correction
    return checks[-1], None
