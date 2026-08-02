import re

CITATION_PATTERN = re.compile(r"\[([a-z0-9-]+)#(\d{1,3})\]")
MODEL_PATTERN = re.compile(r"\[(?:model:)?([A-Za-z0-9_-]+)@([^\]\s]+)\]")
UNCITED_ANSWER_CHARS = 220
MAX_INTERVENTIONS = 3


def find_markers(text):
    return ["%s#%s" % (slug, sid) for slug, sid in CITATION_PATTERN.findall(text or "")]


def find_model_markers(text):
    return ["%s@%s" % (name, version) for name, version in MODEL_PATTERN.findall(text or "")]


def check_citations(text, sections_read, models_run=()):
    markers = find_markers(text)
    model_markers = find_model_markers(text)
    unresolved = sorted({m for m in markers if m not in sections_read})
    unresolved += sorted({m for m in model_markers if m not in set(models_run)})
    return {
        "rule": "citation_integrity",
        "markers": markers + ["model:" + m for m in model_markers],
        "unresolved": unresolved,
        "passed": not unresolved,
    }


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
        "[model:name@version] must name a model you actually ran with run_model. Note that "
        "a model name is not a paper slug. Fix or drop each one and re-send the full answer."
        % ", ".join(result["unresolved"])
    )


def evidence_correction(result):
    return (
        "Your answer was blocked by the evidence gate: %s. Gather evidence first: read the "
        "sections you need with read_literature, and run the physical model with run_model "
        "if the question asks what a model predicts. Then answer." % result["reason"]
    )


def check_budget(state):
    if state["model_calls"] >= state["max_model_calls"]:
        return {"rule": "budget", "passed": False, "reason": "model call budget reached"}
    if state["tool_calls"] >= state["max_tool_calls"]:
        return {"rule": "budget", "passed": False, "reason": "tool call budget reached"}
    return {"rule": "budget", "passed": True, "reason": ""}


def review_final(text, state):
    checks = [
        check_evidence(text, state["sections_read"], state.get("model_runs", 0)),
        check_citations(text, state["sections_read"], state.get("models_run", ())),
    ]
    for check in checks:
        if not check["passed"]:
            correction = (
                evidence_correction(check)
                if check["rule"] == "evidence_gate"
                else citation_correction(check)
            )
            return check, correction
    return checks[-1], None
