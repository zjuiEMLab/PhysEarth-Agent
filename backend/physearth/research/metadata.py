"""Repairing the reproduction metadata a paper-grounded plan has to carry."""

import re

from physearth import registry
from physearth.research.common import _provenance_confidence
from physearth.research.mapping import (
    _ledger_entries,
    _model_parameter_spec,
    _parameter_resolution_by_run,
    _repair_item,
    _repair_parameter_mappings,
    _same_value,
)
from physearth.research.normalise import (
    _clean_outputs,
    _normalise_evidence_ref,
    _read_evidence_refs,
    is_reproduction_question,
)


def _figure_ref_for_target(target, refs):
    """Choose the opened source figure matching a target, if one can be identified.

    A compact multi-figure plan may omit redundant ``evidence_refs``. Falling back to the
    first opened reference used to attach Figure 5 to Figure 4 in that case. Match the
    target's figure number before using the ordinary first-reference fallback.
    """
    source_id = str((target or {}).get("source_id") or "").lower()
    source_match = re.search(r"(?:fig(?:ure)?)[^0-9]*(\d+)", source_id)
    if not source_match:
        return (list(refs or ()) or [None])[0]
    number = str(int(source_match.group(1)))
    for ref in refs or ():
        ref_match = re.search(r"(?:fig(?:ure)?)[^0-9]*(\d+)", str(ref).lower())
        if ref_match and str(int(ref_match.group(1))) == number:
            return ref
    return (list(refs or ()) or [None])[0]


def _repair_reproduction_metadata(
    session,
    question,
    literature_evidence,
    reproduction_targets,
    selected_models,
    parameter_mapping,
    outputs,
    runs,
    charts,
    paper_conditions,
    condition_provenance,
    parameter_resolution,
):
    """Complete review metadata from resources actually opened in this session.

    This function deliberately does not author physical runs.  It only binds an LLM
    proposal to evidence, declared inputs, and deterministic coverage relationships.
    Every change is returned for the plan-review card.
    """
    if not is_reproduction_question(question, session):
        return (
            literature_evidence, reproduction_targets, selected_models,
            parameter_mapping, outputs, paper_conditions, condition_provenance,
            [], [], [],
        )

    repairs = []
    problems = []
    sections, figures = _read_evidence_refs(session)
    ledger_sections = _ledger_entries(session, "section")
    ledger_figures = _ledger_entries(session, "figure") + _ledger_entries(session, "figure_inspection")
    opened = []
    seen = set()
    for item in ledger_sections + ledger_figures:
        if item.get("kind") == "section" and item.get("source") == "skill":
            continue
        if item.get("kind") == "figure" and item.get("asset_available", True) is False:
            continue
        ref = _normalise_evidence_ref(item.get("reference"))
        if ref and ref not in seen:
            opened.append(item)
            seen.add(ref)

    literature_evidence = list(literature_evidence or ())
    if not literature_evidence and opened:
        literature_evidence = [
            {
                "evidence_ref": _normalise_evidence_ref(item.get("reference")),
                "purpose": "paper evidence read during reproduction analysis",
                "source": item.get("source", "session evidence ledger"),
                "title": item.get("title", ""),
            }
            for item in opened
        ]
        repairs.append(_repair_item(
            "literature_evidence", [], literature_evidence,
            "bind the proposal to paper sections or figures opened in this session",
            "session_evidence_ledger",
        ))

    paper_session = ((session or {}).get("research_context") or {}).get("paper_session") or {}
    relevant_refs = [
        _normalise_evidence_ref(item.get("reference"))
        for item in opened
        if item.get("reference")
    ]
    if not relevant_refs:
        relevant_refs = [
            _normalise_evidence_ref(item)
            for item in (session or {}).get("sections_read") or ()
            if _normalise_evidence_ref(item)
        ]
    paper_slug = paper_session.get("paper_slug") or paper_session.get("paper")
    if paper_slug:
        paper_refs = [
            _normalise_evidence_ref(item.get("reference"))
            for item in opened
            if item.get("paper") == paper_slug
        ]
        if paper_refs:
            relevant_refs = paper_refs
    reproduction_targets = list(reproduction_targets or ())

    resolved_models = {
        str(item.get("asked") or "").strip(): str(item.get("registered") or "").strip()
        for item in ((session.get("capability_review") or {}).get("resolved_names") or ())
        if item.get("asked") and item.get("registered")
    }
    for index, target in enumerate(reproduction_targets):
        before = list(target.get("reference_models") or ())
        after = [resolved_models.get(str(model).strip(), model) for model in before]
        if after != before:
            target["reference_models"] = list(dict.fromkeys(after))
            repairs.append(_repair_item(
                "reproduction_targets[%d].reference_models" % index,
                before,
                target["reference_models"],
                "carry the evidence-backed capability resolution into the executable plan",
                "capability_review",
            ))

    for index, target in enumerate(reproduction_targets):
        refs = [_normalise_evidence_ref(ref) for ref in target.get("evidence_refs") or ()]
        if not refs and relevant_refs:
            before = list(refs)
            target["evidence_refs"] = [_figure_ref_for_target(target, relevant_refs)]
            repairs.append(_repair_item(
                "reproduction_targets[%d].evidence_refs" % index,
                before, target["evidence_refs"],
                "attach the target to evidence already opened in this session",
                "session_evidence_ledger",
            ))
        elif refs:
            target["evidence_refs"] = refs

    if not selected_models:
        seen_models = set()
        derived = []
        for run in runs or ():
            model = str(run.get("model") or "").strip()
            if model and model not in seen_models:
                seen_models.add(model)
                derived.append({"model": model, "purpose": "model used by the submitted reproduction runs"})
        if derived:
            selected_models = derived
            repairs.append(_repair_item(
                "selected_models", [], selected_models,
                "derive model identities from already submitted runs; capabilities remain session-gated",
                "submitted_run_models",
            ))

    if not outputs:
        derived_outputs = []
        for chart in charts or ():
            derived_outputs.extend(chart.get("ys") or ([chart.get("y")] if chart.get("y") else []))
        for run in runs or ():
            output = (run.get("parameters") or {}).get("output")
            if output:
                derived_outputs.append(output)
        outputs = _clean_outputs(sorted(set(str(item) for item in derived_outputs if item)))
        if outputs:
            repairs.append(_repair_item(
                "outputs", [], outputs,
                "derive compared outputs from declared charts and run inputs",
                "submitted_plan_fields",
            ))

    # Add only deterministic target coverage.  Physical runs and chart definitions are
    # never modified; only their relationship to a target is recorded.
    for index, target in enumerate(reproduction_targets):
        if target.get("run_ids") or target.get("chart_ids"):
            continue
        # A partial/unavailable reference target must remain visibly uncovered.  In
        # particular, a local exploratory chart must not be auto-attached to an external
        # paper model merely because it plots the same quantity.
        if target.get("status") in ("partial", "unavailable"):
            continue
        quantity = str(target.get("target_quantity") or "").lower()
        reference_models = {
            str(model).strip() for model in target.get("reference_models") or () if str(model).strip()
        }
        output_names = {
            str(value.get("name") or value.get("output") or "").lower()
            for value in outputs or () if isinstance(value, dict)
        }
        output_names.update(str(value).lower() for value in outputs or () if not isinstance(value, dict))
        target_outputs = {
            item for item in output_names
            if item and (item in quantity or quantity in item)
        }
        chart_ids = [
            chart.get("id") for chart in charts or ()
            if target_outputs.intersection({str(item).lower() for item in (chart.get("ys") or [chart.get("y")]) if item})
        ]
        if not chart_ids:
            chart_ids = [chart.get("id") for chart in charts or () if chart.get("purpose") in ("result", "comparison")]
        run_ids = []
        for run in runs or ():
            if not run.get("id"):
                continue
            if reference_models and str(run.get("model") or "").strip() not in reference_models:
                continue
            output_group = str((run.get("resolved_parameters") or run.get("parameters") or {}).get("output") or "").strip()
            entry = registry.get(str(run.get("model") or "").strip(), session)
            declared_outputs = set()
            if entry:
                declared_outputs.update(
                    str(value).lower()
                    for value in (entry.card.get("output_groups") or {}).get(output_group) or ()
                )
            declared_outputs.add(output_group.lower())
            if not target_outputs or target_outputs.intersection(declared_outputs):
                run_ids.append(run.get("id"))
        if run_ids or chart_ids:
            target["run_ids"] = [item for item in run_ids if item]
            target["chart_ids"] = [item for item in chart_ids if item]
            repairs.append(_repair_item(
                "reproduction_targets[%d].coverage" % index,
                {"run_ids": [], "chart_ids": []},
                {"run_ids": target["run_ids"], "chart_ids": target["chart_ids"]},
                "link the target to compatible declared run outputs and result charts",
                "deterministic_plan_coverage",
            ))

    by_run = _parameter_resolution_by_run(parameter_resolution, runs)
    mappings = list(parameter_mapping or ())
    paper_conditions = dict(paper_conditions or {})
    condition_provenance = dict(condition_provenance or {})
    # A paper mapping with a valid evidence reference is sufficient to expose the
    # condition in the plan, but not to change the resolved run value.
    for item in mappings:
        model_input = item.get("model_input")
        provenance = item.get("provenance_class")
        evidence_ref = _normalise_evidence_ref(item.get("evidence_ref"))
        if (
            model_input and provenance in ("paper_explicit", "paper_inferred")
            and evidence_ref and evidence_ref in sections | figures
            and model_input not in paper_conditions
            and item.get("mapped_value") is not None
        ):
            paper_conditions[model_input] = item.get("mapped_value")
            condition_provenance[model_input] = evidence_ref
            repairs.append(_repair_item(
                "paper_conditions.%s" % model_input,
                None, item.get("mapped_value"),
                "promote an evidence-backed paper mapping into the explicit condition ledger",
                provenance,
            ))

    mappings, mapping_repairs, mapping_problems, _expected_mappings, _defaulted_mappings = _repair_parameter_mappings(
        session,
        mappings,
        runs,
        parameter_resolution,
        paper_conditions,
        condition_provenance,
        sections | figures,
    )
    repairs.extend(mapping_repairs)
    problems.extend(mapping_problems)
    mapped = {
        (str(item.get("model") or "").strip(), item.get("model_input"))
        for item in mappings
        if item.get("model_input") and item.get("model")
    }

    for run in runs or ():
        run_id = run.get("id")
        run_model = str(run.get("model") or "").strip()
        resolution = by_run.get(run_id) or {}
        resolved = resolution.get("resolved_parameters") or run.get("parameters") or {}
        defaulted = set(resolution.get("defaulted_parameters") or ())
        for model_input, value in resolved.items():
            mapping_key = (run_model, model_input)
            if mapping_key in mapped:
                continue
            spec = _model_parameter_spec(session, run.get("model"), model_input)
            units = spec.get("unit", "") if isinstance(spec, dict) else ""
            evidence_ref = _normalise_evidence_ref(condition_provenance.get(model_input))
            if model_input in paper_conditions:
                provenance = "paper_explicit" if evidence_ref in sections | figures else "paper_inferred"
                paper_value = paper_conditions.get(model_input)
                rationale = "Paper condition mapped to the registered model input."
            elif model_input in defaulted:
                provenance = "backend_default"
                paper_value = None
                rationale = "The registered model inserted this value during parameter resolution; it is not paper evidence."
                evidence_ref = ""
            else:
                provenance = "model_assumption"
                paper_value = None
                rationale = "The submitted run retained this value without attached paper/user evidence; confirm it during plan review."
                evidence_ref = ""
            confidence, confidence_basis = _provenance_confidence(provenance)
            mapping = {
                "model": run_model,
                "paper_concept": model_input,
                "paper_value": paper_value,
                "model_input": model_input,
                "mapped_value": value,
                "units": units,
                "provenance_class": provenance,
                "confidence": confidence,
                "confidence_basis": confidence_basis,
                "evidence_ref": evidence_ref,
                "rationale": rationale,
            }
            mappings.append(mapping)
            mapped.add(mapping_key)
            repairs.append(_repair_item(
                "parameter_mapping.%s.%s" % (run_model, model_input),
                None, mapping,
                "map every resolved run input to an exact declared model parameter",
                provenance,
                "registered_model_declaration",
            ))

    # Paper conditions describe the source experiment; they are not model-validity
    # constraints.  A user may deliberately extend a paper sweep while remaining inside
    # the registered model declaration.  Keep the mismatch auditable as a warning and
    # never let an LLM-derived paper conclusion block that exploratory revision.
    context_warnings = []
    explicitly_requested = {
        (str(run.get("model") or "").strip(), key)
        for run in runs or ()
        for key in ((by_run.get(run.get("id")) or {}).get("requested_parameters") or {})
    }
    for run in runs or ():
        run_model = str(run.get("model") or "").strip()
        for key, expected in paper_conditions.items():
            actual = (run.get("parameters") or {}).get(key)
            if actual is not None and not _same_value(actual, expected):
                warning = {
                    "code": "paper_context_difference",
                    "field": "runs[%s].parameters.%s" % (run.get("id"), key),
                    "source": "paper_conditions.%s" % key,
                    "expected": expected,
                    "actual": actual,
                    "repair": "none",
                    "provenance": condition_provenance.get(key) or "paper evidence",
                    "category": "paper_context",
                    "blocking": False,
                    "message": (
                        "The run differs from the paper reference condition; it is an "
                        "exploratory extension and is not an exact reproduction of that "
                        "source condition."
                    ),
                }
                context_warnings.append(warning)
                # Keep the paper value for comparison context, but classify the effective
                # run input from its actual source. A backend default is not user evidence.
                for mapping in mappings:
                    if mapping.get("model_input") != key:
                        continue
                    if mapping.get("provenance_class") in ("paper_explicit", "paper_inferred"):
                        mapping_key = (str(mapping.get("model") or run_model).strip(), key)
                        provenance = (
                            "user_specified"
                            if mapping_key in explicitly_requested
                            else "backend_default"
                        )
                        mapping["provenance_class"] = provenance
                        mapping["rationale"] = (
                            "The submitted experiment differs from the paper condition; the "
                            "paper value remains comparison context."
                        )
                        confidence, confidence_basis = _provenance_confidence(provenance)
                        mapping["confidence"] = confidence
                        mapping["confidence_basis"] = confidence_basis

    # Add evidence references to paper mappings only when they are actually available.
    for index, item in enumerate(mappings):
        if item.get("provenance_class") in ("paper_explicit", "paper_inferred") and not item.get("evidence_ref") and relevant_refs:
            item["evidence_ref"] = relevant_refs[0]
            repairs.append(_repair_item(
                "parameter_mapping[%d].evidence_ref" % index,
                "", relevant_refs[0],
                "attach a paper mapping to the opened section evidence",
                item.get("provenance_class"),
            ))
    return (
        literature_evidence, reproduction_targets, selected_models,
        mappings, outputs, paper_conditions, condition_provenance,
        repairs, problems, context_warnings,
    )
