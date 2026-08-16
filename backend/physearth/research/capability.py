"""Whether the registered models can answer the question that was asked."""

from physearth import registry
from physearth.research.charts import _capability_gaps


def _capability_strings(values):
    if isinstance(values, str):
        values = [values]
    return list(dict.fromkeys(
        str(value).strip() for value in (values or ()) if str(value).strip()
    ))


def _scope_signature(unavailable, not_comparable, unavailable_outputs):
    """Exactly what the user was asked to accept when they confirmed a partial scope."""
    return {
        "unavailable": sorted(
            str(item.get("model") or "") for item in unavailable or ()
        ),
        "not_comparable": sorted(
            "%s/%s" % (item.get("reference_model") or "", item.get("local_model") or "")
            for item in not_comparable or ()
        ),
        "outputs": sorted(str(item) for item in unavailable_outputs or ()),
    }


def _within_confirmed_scope(signature, confirmed):
    """True when nothing has become unavailable since the user decided.

    A capability check is recomputed every time the agent calls it, and it used to reset
    the decision each time: the user confirmed a partial scope, the agent checked again
    before proposing, and the confirmation was gone, so the plan was refused and the same
    question asked again. The decision stands until the scope actually widens -- and if a
    reference model that was available has since become unavailable, that is a different
    question and worth asking again.
    """
    if not confirmed:
        return False
    return all(
        set(signature.get(key) or ()) <= set(confirmed.get(key) or ())
        for key in ("unavailable", "not_comparable", "outputs")
    )


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
        report.update({
            "status": "confirmed",
            "user_decision": "partial",
            # What was accepted, so a later re-check can tell whether it is still the
            # same question. Without this the decision is forgotten on the next check.
            "confirmed_scope": _scope_signature(
                current.get("unavailable"),
                current.get("not_comparable"),
                current.get("unavailable_outputs"),
            ),
        })
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
    resolved_names = []
    for name in refs:
        # A paper writes SMRT and the card says `smrt`; it writes SMRT IBA and the card
        # says electromagnetic_model: iba. Resolving either is not guessing: the spelling
        # match ignores only case and separators, and the formulation must be a value the
        # card actually declares. MEMLS and DMRT-QMS still report as unregistered, which
        # is what this check exists to say.
        entry, canonical, configuration, options = registry.resolve_configuration(name, session)
        if entry is None:
            unavailable.append({
                "model": name,
                "reason": "not registered in the current model registry",
                "source": "registered_model_registry",
            })
            continue
        if canonical != name:
            resolved_names.append({
                "asked": name,
                "registered": canonical,
                # Named so a reader can object: this says which configuration of the
                # registered model the paper's name was taken to mean, or -- when the
                # name did not pin one -- which configurations it could have meant.
                "configuration": configuration or None,
                "configuration_options": options or None,
            })
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
            "configuration": configuration or {},
            # An under-specified name is still this model. The plan has to choose one of
            # these before it runs; the check's job is to say so, not to call the model
            # missing.
            "configuration_options": options or [],
        }
        if entry.runnable and not model_resources_missing:
            # One row per model, not one per paper name. Six legend entries naming six
            # configurations of one model listed that model six times, with identical
            # output lists, which reads as noise and hides the two names that actually
            # did not resolve.
            existing = next(
                (
                    item for item in supported
                    if item.get("model") == entry.name and item.get("reference_model")
                ),
                None,
            )
            if existing is None:
                supported.append({
                    **detail,
                    "reference_model": True,
                    "configurations": [configuration] if configuration else [],
                    "asked_as": [name],
                })
                continue
            if configuration and configuration not in existing["configurations"]:
                existing["configurations"].append(configuration)
            if name not in existing["asked_as"]:
                existing["asked_as"].append(name)
            for option in options or ():
                if option not in existing["configurations"]:
                    existing["configurations"].append(option)
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
        entry, canonical = registry.resolve(name, session)
        if entry is None:
            continue
        # Already reported as a reference model, under whatever the paper called it.
        # Listing it a second time as a local candidate is the same model twice.
        if any(item.get("model") == entry.name for item in supported):
            continue
        if canonical != name:
            resolved_names.append({"asked": name, "registered": canonical})
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
    signature = _scope_signature(unavailable, not_comparable, unavailable_outputs)
    previous = current or {}
    confirmed_scope = previous.get("confirmed_scope")
    decision = None
    if (
        status == "waiting_user"
        and previous.get("user_decision") == "partial"
        and _within_confirmed_scope(signature, confirmed_scope)
    ):
        status = "confirmed"
        decision = "partial"
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
        # Visible rather than silent: if the paper's spelling was not the registered one,
        # the report says which name it was matched to, so a reader can object.
        "resolved_names": resolved_names,
        "evidence": evidence,
        "targets": _capability_strings(
            item.get("id") for item in (targets or ()) if isinstance(item, dict)
        ),
        "user_decision": decision,
        "confirmed_scope": confirmed_scope if decision else None,
    }
    if session is not None:
        session["capability_review"] = report
    return report
