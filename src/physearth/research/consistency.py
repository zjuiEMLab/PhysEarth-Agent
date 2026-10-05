"""The report's parameter-source block must say what the plan's ledger says.

The plan records, per parameter, where its value came from. A report that restates those
sources in its own appendix can drift from it: one run called a parameter user_specified in the
appendix while the ledger and the report's own table called it a model assumption, and another
cited the same radius to two different places. A reader cannot repeat the run from sources
that disagree, so the appendix is held to the ledger, which is authoritative.
"""

import json
import re

from physearth.research import asked

_BLOCK = re.compile(r"<parameter_provenance>(.*?)</parameter_provenance>", re.DOTALL | re.IGNORECASE)

# The appendix vocabulary each ledger class may be written as.
_ALLOWED = {
    "paper_explicit": {"paper"},
    "paper_inferred": {"paper", "derived"},
    "user_specified": {"user"},
    "backend_default": {"model_default"},
    "model_assumption": {"assumption", "unknown"},
}


def _declared(text):
    match = _BLOCK.search(str(text or ""))
    if not match:
        return None
    try:
        items = json.loads(match.group(1))
    except (TypeError, ValueError):
        return None
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else None


def _ledger(session):
    plan = ((session or {}).get("research") or {}).get("plan") or {}
    return {
        str(item.get("model_input")): str(item.get("provenance_class") or "")
        for item in plan.get("parameter_mapping") or []
        if isinstance(item, dict) and item.get("model_input")
    }


def check(text, session, state=None):
    """Every parameter the appendix labels carries the ledger's source class."""
    declared = _declared(text)
    if declared is None or not asked.applies(session, state):
        return {"rule": "provenance_consistency", "passed": True, "skipped": True, "mismatches": []}
    ledger = _ledger(session)
    mismatches = []
    for item in declared:
        name = str(item.get("field") or "")
        recorded = ledger.get(name)
        kind = str(item.get("source_kind") or "").strip().lower()
        if recorded in _ALLOWED and kind not in _ALLOWED[recorded]:
            mismatches.append({"field": name, "written": kind, "ledger": recorded,
                               "allowed": sorted(_ALLOWED[recorded])})
    return {"rule": "provenance_consistency", "passed": not mismatches, "mismatches": mismatches}


def correction(result):
    lines = [
        "%s: the appendix says source_kind %r, the plan ledger records %s (write one of: %s)"
        % (item["field"], item["written"], item["ledger"], ", ".join(item["allowed"]))
        for item in result["mismatches"]
    ]
    return (
        "Revise the parameter_provenance block of the final report. It disagrees with the plan's "
        "parameter ledger, which is authoritative: " + "; ".join(lines) + ". Keep the rest of the "
        "report as it is, and make the report's own prose and table say the same."
    )
