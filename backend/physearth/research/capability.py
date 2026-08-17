"""Whether the registered models can answer the question that was asked."""

import re

from physearth import registry
from physearth.corpus import live
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



def _near_registered(name, session=None):
    """Registered models and declared formulations a name resembles without being.

    Token overlap only, and only whole tokens: `DMRT-QMS` shares `dmrt` with
    `dmrt_qca_shortrange`, which is worth saying. It shares nothing with `iba`, which is
    not. No edit distance -- a suggestion has to come from something the card declares.
    """
    tokens = {token for token in re.split(r"[^a-z0-9]+", str(name or "").lower()) if len(token) > 2}
    if not tokens:
        return []
    close = []
    for registered, model in sorted(registry.all_models(session).items()):
        candidates = {registered}
        for spec in (model.card.get("parameters") or {}).values():
            candidates.update(str(value) for value in (spec or {}).get("enum") or ())
        for candidate in candidates:
            other = {
                token for token in re.split(r"[^a-z0-9]+", candidate.lower()) if len(token) > 2
            }
            if tokens & other:
                close.append(candidate)
    return sorted(set(close))[:4]


_DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


def _identity_key(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _doi(value):
    match = _DOI_RE.search(str(value or ""))
    return match.group(0).rstrip(".,;)").lower() if match else ""


def _opened_paper_cards(session, targets=None):
    """Return paper cards named by evidence already opened in this session."""
    slugs = []

    def add_reference(reference):
        slug = str(reference or "").split("#", 1)[0].strip()
        if slug and slug not in slugs and live.card(session, slug):
            slugs.append(slug)

    context = (session or {}).get("research_context") or {}
    paper_session = context.get("paper_session") or {}
    add_reference(paper_session.get("paper") or paper_session.get("paper_slug"))
    for reference in (session or {}).get("sections_read") or ():
        add_reference(reference)
    for reference in (session or {}).get("paper_figures_read") or ():
        add_reference(reference)
    for item in (session or {}).get("evidence_ledger") or ():
        if isinstance(item, dict) and item.get("kind") in ("section", "figure", "figure_inspection"):
            add_reference(item.get("reference"))
    for target in targets or ():
        if not isinstance(target, dict):
            continue
        for reference in target.get("evidence_refs") or ():
            add_reference(reference)

    return [(slug, live.card(session, slug)) for slug in slugs]


def _paper_evidence_refs(session, paper_slug, targets=None):
    refs = []
    values = list((session or {}).get("sections_read") or ())
    values.extend((session or {}).get("paper_figures_read") or ())
    values.extend(
        item.get("reference")
        for item in (session or {}).get("evidence_ledger") or ()
        if isinstance(item, dict)
    )
    values.extend(
        reference
        for target in targets or ()
        if isinstance(target, dict)
        for reference in target.get("evidence_refs") or ()
    )
    for value in values:
        reference = str(value or "").strip()
        if reference.split("#", 1)[0] == paper_slug and reference not in refs:
            refs.append(reference)
    return refs


def _resolve_from_paper_evidence(name, session, targets=None):
    """Resolve a paper slug only through an opened paper and an explicit card relation."""
    requested_key = _identity_key(name)
    if not requested_key:
        return None
    for paper_slug, paper in _opened_paper_cards(session, targets):
        if _identity_key(paper_slug) != requested_key:
            continue
        paper_doi = _doi(paper.get("doi"))
        if not paper_doi:
            continue
        for registered, entry in sorted(registry.all_models(session).items()):
            card = entry.card
            # The DOI is the relation, and it is already declared: a model card cites the
            # paper it implements, and a literature card carries that paper's DOI. An
            # extra `paper_slugs` field would be a second place to state the same fact,
            # and no card declares one -- which is why this path never matched.
            card_doi = _doi(card.get("citation"))
            if not card_doi or card_doi != paper_doi:
                continue
            return (
                entry,
                registered,
                {},
                [],
                {
                    "match_basis": "opened paper slug + model card citing the matching DOI",
                    "paper_slug": paper_slug,
                    "doi": paper_doi,
                    "evidence": _paper_evidence_refs(session, paper_slug, targets)
                    + ["doi:%s" % paper_doi],
                },
            )
    return None


def _capability_check_one(
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
    does not inspect Evaluation YAML or a stored protocol. A runnable local model is only
    matched to a paper slug when the opened paper and the model card provide the same
    declared identity and DOI; a merely similar name remains unavailable.
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
        # is what this check exists to say. A paper slug can only take another route when
        # _resolve_from_paper_evidence has established the identity from opened evidence.
        entry, canonical, configuration, options = registry.resolve_configuration(name, session)
        evidence_resolution = None
        if entry is None:
            evidence_resolution = _resolve_from_paper_evidence(name, session, targets)
            if evidence_resolution:
                entry, canonical, configuration, options = evidence_resolution[:4]
        if entry is None:
            # Say when a name is merely close to something registered. `DMRT-QMS` and
            # `DMRT-ML` are separate packages and belong in the unavailable list, but a
            # reader deserves to know they resemble the declared dmrt_qca_shortrange
            # rather than discover the resemblance themselves and wonder which was meant.
            # Reported, not resolved: a name that is nearly a registered model is not
            # that model, and this must never quietly upgrade one into the other.
            near = _near_registered(name, session)
            unavailable.append({
                "model": name,
                "reason": (
                    "not registered in the current model registry; resembles %s, which is "
                    "not the same model -- confirm which was meant" % ", ".join(near)
                    if near
                    else "not registered in the current model registry"
                ),
                "resembles": near,
                "certainty": "unsure" if near else "unregistered",
                "source": "registered_model_registry",
            })
            continue
        if canonical != name:
            resolution = {
                "asked": name,
                "registered": canonical,
                # Named so a reader can object: this says which configuration of the
                # registered model the paper's name was taken to mean, or -- when the
                # name did not pin one -- which configurations it could have meant.
                "configuration": configuration or None,
                "configuration_options": options or None,
            }
            if evidence_resolution:
                resolution.update(evidence_resolution[-1])
            resolved_names.append(resolution)
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
        evidence_resolution = None
        if entry is None:
            evidence_resolution = _resolve_from_paper_evidence(name, session, targets)
            if evidence_resolution:
                entry, canonical = evidence_resolution[:2]
        if entry is None:
            continue
        # Already reported as a reference model, under whatever the paper called it.
        # Listing it a second time as a local candidate is the same model twice.
        if any(item.get("model") == entry.name for item in supported):
            continue
        if canonical != name:
            resolution = {"asked": name, "registered": canonical}
            if evidence_resolution:
                resolution.update(evidence_resolution[-1])
            resolved_names.append(resolution)
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


def _target_key(value):
    """Use a stable identity for a figure target without trusting its filename spelling."""
    text = str(value or "").strip().lower()
    match = re.search(r"(?:figure|fig)[^0-9]*(\d+)", text)
    if match:
        return "figure:%d" % int(match.group(1))
    return "target:%s" % _identity_key(text)


def _target_specs(targets, reference_models, requested_outputs, local_models):
    specs = []
    for index, item in enumerate(targets or ()):
        item = dict(item) if isinstance(item, dict) else {"id": item}
        raw_id = (
            item.get("id") or item.get("source_id") or item.get("figure_id")
            or (item.get("evidence_refs") or [None])[0] or "target-%d" % (index + 1)
        )
        specs.append({
            **item,
            "id": str(raw_id),
            "_key": _target_key(raw_id),
            "reference_models": _capability_strings(
                item.get("reference_models") or item.get("models") or reference_models
            ),
            "requested_outputs": _capability_strings(
                item.get("requested_outputs") or item.get("outputs") or requested_outputs
            ),
            "local_models": _capability_strings(item.get("local_models") or local_models),
        })
    return specs


def _expected_figure_targets(session):
    values = []
    for reference in (session or {}).get("paper_figures_read") or ():
        reference = str(reference or "").strip()
        if reference and reference not in values:
            values.append(reference)
    return values


def _merge_target_items(reports, field, identity_fields):
    merged = []
    index = {}
    list_fields = ("target_ids", "configurations", "configuration_options", "asked_as", "outputs")
    for report in reports:
        target_id = report.get("id")
        for item in report.get(field) or ():
            item = dict(item)
            key = tuple(str(item.get(name) or "") for name in identity_fields)
            existing_index = index.get(key)
            if existing_index is None:
                item["target_ids"] = [target_id] if target_id else []
                for name in list_fields:
                    if name in item and not isinstance(item[name], list):
                        item[name] = [item[name]] if item[name] else []
                index[key] = len(merged)
                merged.append(item)
                continue
            existing = merged[existing_index]
            for name in list_fields:
                values = item.get(name) or ()
                if name not in existing:
                    existing[name] = []
                for value in values:
                    if value not in existing[name]:
                        existing[name].append(value)
    return merged


def _aggregate_target_reports(reports, expected_targets, previous=None):
    """Combine per-target findings while retaining the evidence boundary for each figure."""
    by_key = {_target_key(item.get("id")): item for item in reports}
    missing = [
        reference for reference in expected_targets
        if _target_key(reference) not in by_key
    ]
    all_reports = list(reports)
    status = "incomplete" if missing else "ready"
    if not missing:
        statuses = {item.get("status") for item in all_reports}
        if "waiting_user" in statuses:
            status = "waiting_user"
        elif "waiting_resources" in statuses:
            status = "waiting_resources"
    supported = _merge_target_items(all_reports, "supported", ("model", "reference_model"))
    unavailable = _merge_target_items(all_reports, "unavailable", ("model", "reference_model"))
    not_comparable = _merge_target_items(
        all_reports, "not_comparable", ("reference_model", "local_model")
    )
    unavailable_outputs = sorted({
        str(output)
        for report in all_reports
        for output in report.get("unavailable_outputs") or ()
    })
    resource_gaps = []
    resolved_names = []
    evidence = []
    requested_models = []
    requested_outputs = []
    for report in all_reports:
        for field, destination in (
            ("resource_gaps", resource_gaps),
            ("resolved_names", resolved_names),
        ):
            for item in report.get(field) or ():
                if item not in destination:
                    destination.append(item)
        for value, destination in (
            (report.get("evidence") or (), evidence),
            (report.get("requested_models") or (), requested_models),
            (report.get("requested_outputs") or (), requested_outputs),
        ):
            for item in value:
                if item not in destination:
                    destination.append(item)
    result = {
        "status": status,
        "supported": supported,
        "unavailable": unavailable,
        "not_comparable": not_comparable,
        "requested_models": requested_models,
        "requested_outputs": requested_outputs,
        "supported_outputs": sorted({
            output for item in supported for output in item.get("outputs") or ()
        }),
        "unavailable_outputs": unavailable_outputs,
        "resource_gaps": resource_gaps,
        "resolved_names": resolved_names,
        "evidence": evidence,
        "targets": [item.get("id") for item in all_reports],
        "target_reports": all_reports,
        "target_check_complete": not missing,
        "missing_targets": missing,
        "user_decision": None,
        "confirmed_scope": None,
    }
    previous = previous or {}
    if (
        status == "waiting_user"
        and previous.get("user_decision") == "partial"
        and _within_confirmed_scope(
            _scope_signature(unavailable, not_comparable, unavailable_outputs),
            previous.get("confirmed_scope"),
        )
    ):
        result.update({
            "status": "confirmed",
            "user_decision": "partial",
            "confirmed_scope": previous.get("confirmed_scope"),
        })
    return result


def capability_check(
    session,
    question="",
    reference_models=None,
    requested_outputs=None,
    local_models=None,
    targets=None,
    decision="check",
):
    """Check every reproduction target, then publish one session-wide checkpoint.

    A multi-figure reproduction cannot become ``ready`` from a check for only one
    figure. Calls may provide all targets at once or accumulate one target at a time;
    the session retains the per-target reports until the complete aggregate exists.
    """
    current = session.get("capability_review") if session else None
    target_list = _target_specs(targets, reference_models, requested_outputs, local_models)
    expected = _expected_figure_targets(session)

    if not target_list and len(expected) <= 1:
        return _capability_check_one(
            session,
            question=question,
            reference_models=reference_models,
            requested_outputs=requested_outputs,
            local_models=local_models,
            targets=targets,
            decision=decision,
        )

    if decision == "reject":
        report = dict(current or {})
        report.update({"status": "rejected", "user_decision": "reject"})
        session["capability_review"] = report
        return report

    if decision in ("confirm_partial", "confirm"):
        if (
            not current
            or current.get("status") not in ("waiting_user", "ready")
            or not current.get("target_check_complete", True)
        ):
            return {
                "status": "error",
                "error_code": "capability_review_missing",
                "message": "Check every reproduction target before confirming a partial scope.",
            }
        report = dict(current)
        report.update({
            "status": "confirmed",
            "user_decision": "partial",
            "confirmed_scope": _scope_signature(
                current.get("unavailable"),
                current.get("not_comparable"),
                current.get("unavailable_outputs"),
            ),
        })
        session["capability_review"] = report
        return report

    if not target_list:
        # Multiple source figures were opened, but the caller did not identify the
        # reproduction targets. Keep the checkpoint incomplete instead of guessing.
        report = _aggregate_target_reports([], expected, current)
        report["requested_models"] = _capability_strings(reference_models)
        report["requested_outputs"] = _capability_strings(requested_outputs)
        session["capability_review"] = report
        return report

    previous_reports = {
        _target_key(item.get("id")): item
        for item in (current or {}).get("target_reports") or ()
    }
    reports = dict(previous_reports)
    session["capability_review"] = None
    for target in target_list:
        report = _capability_check_one(
            session,
            question=target.get("question") or question,
            reference_models=target.get("reference_models"),
            requested_outputs=target.get("requested_outputs"),
            local_models=target.get("local_models"),
            targets=[target],
            decision="check",
        )
        reports[target["_key"]] = {
            **report,
            "id": target["id"],
            "label": target.get("label") or target["id"],
            "target_key": target["_key"],
        }
    aggregate = _aggregate_target_reports(list(reports.values()), expected, current)
    session["capability_review"] = aggregate
    return aggregate
