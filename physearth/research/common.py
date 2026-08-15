"""Phases, provenance vocabulary, the result shapes, and the protocol document."""

import re

import yaml

PHASES = (
    "plan_review",
    "plan_approved",
    "pseudo_preview",
    "chart_selected",
    "approved",
    "completed",
)

PARAMETER_PROVENANCE = (
    "paper_explicit",
    "paper_inferred",
    "user_specified",
    "model_assumption",
    "backend_default",
)

PARAMETER_CONFIDENCE = ("high", "medium", "low")


def _provenance_confidence(provenance):
    return {
        "paper_explicit": ("high", "explicitly supported by opened paper evidence"),
        "paper_inferred": ("medium", "inferred from opened paper evidence"),
        "user_specified": ("high", "directly specified by the user"),
        "backend_default": ("medium", "provided by the registered model backend, not by the paper"),
        "model_assumption": ("low", "not supported by paper or user evidence; requires review"),
    }.get(
        provenance,
        ("low", "source provenance is incomplete and requires review"),
    )


def _clean_list(values, limit=20):
    if isinstance(values, str):
        # Some OpenAI-compatible providers occasionally serialize an array as a
        # numbered multi-line string.  Treat it as prose/list items instead of
        # iterating over individual characters.
        parts = re.split(r"(?:\r?\n)+|\s*;\s*", values)
        values = [re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", item) for item in parts]
    elif isinstance(values, dict):
        values = list(values.values())
    return [str(value).strip() for value in (values or []) if str(value).strip()][:limit]


def protocol_document(project):
    """Return the generated, session-scoped research protocol for human review.

    This is deliberately derived from the LLM proposal and current plan version.  It is
    not read from the paper corpus and is never used as hidden instruction text.
    """
    plan = project.get("plan") or {}
    return {
        "format": "phys-earth/research-protocol",
        "version": int(project.get("plan_version", 1)),
        "plan_version": int(project.get("plan_version", 1)),
        "phase": project.get("phase", "plan_review"),
        "question": plan.get("question", ""),
        "objective": plan.get("objective", ""),
        "hypothesis": plan.get("hypothesis", ""),
        "paper_evidence": list(plan.get("reference_sections") or []),
        "paper_sections": list(plan.get("reference_paper_sections") or []),
        "literature_evidence": list(plan.get("literature_evidence") or []),
        "reproduction_targets": list(plan.get("reproduction_targets") or []),
        "selected_models": list(plan.get("selected_models") or []),
        "parameter_mapping": list(plan.get("parameter_mapping") or []),
        "parameter_resolution": list(plan.get("parameter_resolution") or []),
        "paper_conditions": dict(plan.get("paper_conditions") or {}),
        "condition_provenance": dict(plan.get("condition_provenance") or {}),
        "parameters": dict(plan.get("parameters") or {}),
        "outputs": list(plan.get("outputs") or []),
        "assumptions": list(plan.get("assumptions") or []),
        "runs": list(plan.get("runs") or []),
        "charts": list(plan.get("charts") or []),
        "quantities": list(plan.get("quantities") or []),
        "controls": list(plan.get("controls") or []),
        "metrics": list(plan.get("metrics") or []),
        "diagnostics": list(plan.get("diagnostics") or []),
        "success_criteria": list(plan.get("success_criteria") or []),
        "stop_conditions": list(plan.get("stop_conditions") or []),
        "limitations": list(plan.get("limitations") or []),
        "baseline_run_id": plan.get("baseline_run_id", ""),
        "approval_state": project.get("phase", "plan_review"),
        "automatic_repairs": list(plan.get("automatic_repairs") or []),
        "validation_warnings": list(plan.get("validation_warnings") or []),
        "revision_summary": dict(plan.get("revision_summary") or project.get("revision_summary") or {}),
    }


def protocol_yaml(project):
    """Serialize the generated protocol without writing a persistent protocol.yaml."""
    return yaml.safe_dump(
        protocol_document(project),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def _require(session):
    if not session.get("research"):
        raise ValueError("No LLM-authored research proposal exists yet.")
    return session["research"]


def _public(project):
    public = {**project, "plan": {**project["plan"]}, "review_log": list(project["review_log"])}
    public["protocol"] = protocol_document(public)
    public["protocol_yaml"] = protocol_yaml(public)
    return public


def _ok(summary, data):
    return {"status": "success", "summary": summary, "data": data, "citations": [], "qc": None, "ui": None, "error": None}


def _needs(summary, data):
    return {"status": "needs_input", "summary": summary, "data": data, "citations": [], "qc": None, "ui": None, "error": summary}


def _fail(summary, data=None):
    return {"status": "terminal_error", "summary": summary, "data": data or {}, "citations": [], "qc": None, "ui": None, "error": summary}


def status(session):
    project = session.get("research")
    if not project:
        return _needs("No research proposal exists yet. Analyse the question and propose one.", {"phase": "analysis"})
    return _ok("Research project is in phase %s." % project["phase"], _public(project))
