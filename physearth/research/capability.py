"""Whether the registered models can answer the question that was asked."""

from physearth.models import registry
from physearth.research.charts import _capability_gaps


def _capability_strings(values):
    if isinstance(values, str):
        values = [values]
    return list(dict.fromkeys(
        str(value).strip() for value in (values or ()) if str(value).strip()
    ))


def capability_check(
    session,
    question="",
    reference_models=None,
    requested_outputs=None,
    local_models=None,
    targets=None,
    decision="check",
):
    """Create a session-scoped capability checkpoint before reproduction planning.

    The report is derived from resources already opened in this session.  It deliberately
    does not inspect Evaluation YAML or a stored protocol and it never treats a runnable
    local model as an alias for a different paper reference model.
    """
    decision = str(decision or "check").strip().lower()
    current = session.get("capability_review") if session else None
    if decision == "reject":
        report = dict(current or {})
        report.update({"status": "rejected", "user_decision": "reject"})
        if session is not None:
            session["capability_review"] = report
        return report
    if decision in ("confirm_partial", "confirm"):
        if not current or current.get("status") not in ("waiting_user", "ready"):
            return {
                "status": "error",
                "error_code": "capability_review_missing",
                "message": "Run the capability check before confirming a partial scope.",
            }
        report = dict(current)
        report.update({"status": "confirmed", "user_decision": "partial"})
        if session is not None:
            session["capability_review"] = report
        return report

    context = (session or {}).get("research_context") or {}
    refs = _capability_strings(reference_models)
    if not refs:
        refs = _capability_gaps(question, session)
    outputs = _capability_strings(requested_outputs)
    candidates = _capability_strings(local_models)
    if not candidates:
        candidates = _capability_strings((context.get("capabilities") or {}).keys())

    supported = []
    unavailable = []
    resource_gaps = []
    for name in refs:
        entry = registry.get(name, session)
        if entry is None:
            unavailable.append({
                "model": name,
                "reason": "not registered in the current model registry",
                "source": "registered_model_registry",
            })
            continue
        card = entry.card
        model_key = "%s@%s" % (entry.name, card.get("version", "1.0"))
        instruction = (context.get("instructions") or {}).get(entry.name) or {}
        instruction_key = "%s@%s" % (
            entry.name,
            instruction.get("version") or card.get("instruction_version") or "1.0",
        )
        model_resources_missing = False
        if model_key not in set(session.get("models_inspected") or ()):
            resource_gaps.append({"model": entry.name, "resource": "list_models", "expected": model_key})
            model_resources_missing = True
        if instruction_key not in set(session.get("model_instructions_read") or ()):
            resource_gaps.append({"model": entry.name, "resource": "read_model_instruction", "expected": instruction_key})
            model_resources_missing = True
        detail = {
            "model": entry.name,
            "version": card.get("version"),
            "runnable_here": bool(entry.runnable),
            "parameters": sorted((card.get("parameters") or {}).keys()),
            "combinations": list(card.get("combinations") or []),
            "outputs": sorted((card.get("outputs") or {}).keys()),
            "source": "list_models + read_model_instruction",
        }
        if entry.runnable and not model_resources_missing:
            supported.append({**detail, "reference_model": True})
        elif not entry.runnable:
            unavailable.append({
                **detail,
                "reference_model": True,
                "reason": entry.unavailable_reason,
                "source": "registered_model_declaration",
            })

    # Also report explicitly selected registered local candidates.  They are useful for a
    # partial exploratory plan, but their presence never upgrades an unavailable paper
    # reference target into a comparable result.
    for name in candidates:
        if name in refs:
            continue
        entry = registry.get(name, session)
        if entry is None:
            continue
        card = entry.card
        model_key = "%s@%s" % (entry.name, card.get("version", "1.0"))
        instruction = (context.get("instructions") or {}).get(entry.name) or {}
        instruction_key = "%s@%s" % (
            entry.name,
            instruction.get("version") or card.get("instruction_version") or "1.0",
        )
        model_resources_missing = False
        if model_key not in set(session.get("models_inspected") or ()):
            resource_gaps.append({"model": entry.name, "resource": "list_models", "expected": model_key})
            model_resources_missing = True
        if instruction_key not in set(session.get("model_instructions_read") or ()):
            resource_gaps.append({"model": entry.name, "resource": "read_model_instruction", "expected": instruction_key})
            model_resources_missing = True
        detail = {
            "model": entry.name,
            "version": card.get("version"),
            "runnable_here": bool(entry.runnable),
            "parameters": sorted((card.get("parameters") or {}).keys()),
            "combinations": list(card.get("combinations") or []),
            "outputs": sorted((card.get("outputs") or {}).keys()),
            "reference_model": False,
            "role": "local_candidate",
            "source": "list_models + read_model_instruction",
        }
        if entry.runnable and not model_resources_missing:
            supported.append(detail)
        elif not entry.runnable:
            unavailable.append({
                **detail,
                "reason": entry.unavailable_reason,
                "source": "registered_model_declaration",
            })

    supported_outputs = sorted({
        output
        for item in supported
        for output in item.get("outputs") or ()
    })
    unavailable_outputs = [
        output for output in outputs if output not in supported_outputs
    ]
    not_comparable = []
    if unavailable:
        for missing in unavailable:
            if missing.get("reference_model") is False:
                continue
            for local in candidates:
                if local != missing.get("model"):
                    not_comparable.append({
                        "reference_model": missing.get("model"),
                        "local_model": local,
                        "reason": "a local model/configuration is not an equivalent reference implementation",
                        "source": "registered_model_registry",
                    })

    evidence = [
        item.get("reference")
        for item in (session or {}).get("evidence_ledger") or ()
        if isinstance(item, dict) and item.get("reference")
        and item.get("kind") in ("section", "figure", "figure_inspection")
    ]
    evidence = list(dict.fromkeys(evidence))
    status = (
        "waiting_user"
        if unavailable or not_comparable or unavailable_outputs
        else "waiting_resources"
        if resource_gaps
        else "ready"
    )
    report = {
        "status": status,
        "supported": supported,
        "unavailable": unavailable,
        "not_comparable": not_comparable,
        "requested_models": refs,
        "requested_outputs": outputs,
        "supported_outputs": supported_outputs,
        "unavailable_outputs": unavailable_outputs,
        "resource_gaps": resource_gaps,
        "evidence": evidence,
        "targets": _capability_strings(
            item.get("id") for item in (targets or ()) if isinstance(item, dict)
        ),
        "user_decision": None,
    }
    if session is not None:
        session["capability_review"] = report
    return report
