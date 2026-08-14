"""Generic, human-reviewed research state for PhysEarth.

The four SMRT scientific questions are evaluation cases, not workflow templates.  A plan
enters this module only after the language model has analysed the user's question and
submitted a structured proposal through the research_plan tool.
"""

import copy
import json
import math
import re

import yaml

from physearth import audit, knowledge, plotting, validation
from physearth.models import registry

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


def is_reproduction_question(question, session=None):
    """Return whether the question asks for evidence-led paper reproduction.

    The detector is intentionally generic.  It selects the evidence-first workflow
    from the user's language, without identifying a benchmark case or supplying a
    paper-specific protocol.
    """
    context = (session or {}).get("research_context") or {}
    if context.get("reproduction_case") == "paper-reproduction":
        return True
    text = re.sub(r"\s+", " ", str(question or "").lower())
    return bool(
        re.search(r"\b(?:reproduce|reproduced|reproduction|replicate|replicated|replication|recreate|recreated)\b", text)
        and re.search(r"\b(?:paper|article|study|literature|published|figure|table|result)\b", text)
    )


def _clean_records(values, limit=32):
    if isinstance(values, dict):
        values = [values]
    elif isinstance(values, str):
        values = [{"reference": item} for item in _clean_list(values)]
    return [dict(item) for item in (values or []) if isinstance(item, dict)][:limit]


def _clean_literature_evidence(values):
    cleaned = []
    for item in _clean_records(values):
        reference = str(
            item.get("evidence_ref")
            or item.get("reference")
            or item.get("citation")
            or item.get("source_ref")
            or ""
        ).strip()
        if not reference:
            continue
        record = dict(item)
        record["evidence_ref"] = reference
        record["purpose"] = str(item.get("purpose") or item.get("role") or "source evidence").strip()
        cleaned.append(record)
    return cleaned


def _clean_reproduction_targets(values):
    cleaned = []
    for index, item in enumerate(_clean_records(values)):
        record = dict(item)
        source_type = str(
            item.get("source_type") or item.get("kind") or item.get("type") or "result"
        ).strip().lower()
        source_id = str(
            item.get("source_id")
            or item.get("figure_id")
            or item.get("table_id")
            or item.get("result_id")
            or item.get("identifier")
            or ""
        ).strip()
        evidence = item.get("evidence_refs") or item.get("evidence_ref") or item.get("evidence") or []
        if isinstance(evidence, str):
            evidence = [evidence]
        run_ids = item.get("run_ids") or item.get("runs") or []
        chart_ids = item.get("chart_ids") or item.get("charts") or []
        if isinstance(run_ids, str):
            run_ids = _clean_list(run_ids)
        if isinstance(chart_ids, str):
            chart_ids = _clean_list(chart_ids)
        covered_by = item.get("covered_by")
        if isinstance(covered_by, dict):
            run_ids = list(run_ids) + list(covered_by.get("run_ids") or covered_by.get("runs") or [])
            chart_ids = list(chart_ids) + list(covered_by.get("chart_ids") or covered_by.get("charts") or [])
        record.update(
            {
                "id": str(item.get("id") or "target_%d" % (index + 1)).strip(),
                "source_type": source_type,
                "source_id": source_id,
                "target_quantity": str(
                    item.get("target_quantity") or item.get("quantity") or item.get("output") or ""
                ).strip(),
                "evidence_refs": [str(ref).strip() for ref in evidence if str(ref).strip()],
                "expected_comparison": str(
                    item.get("expected_comparison") or item.get("comparison") or ""
                ).strip(),
                "status": str(item.get("status") or "planned").strip().lower(),
                "availability_reason": str(
                    item.get("availability_reason") or item.get("reason") or ""
                ).strip(),
                "run_ids": [str(run_id).strip() for run_id in run_ids if str(run_id).strip()],
                "chart_ids": [str(chart_id).strip() for chart_id in chart_ids if str(chart_id).strip()],
            }
        )
        cleaned.append(record)
    return cleaned


def _clean_selected_models(values, runs=None, derive=True):
    cleaned = []
    raw_values = [{"model": values}] if isinstance(values, str) else (values or [])
    for item in raw_values:
        record = {"model": item} if isinstance(item, str) else dict(item) if isinstance(item, dict) else {}
        if not record.get("model") and record.get("name"):
            record["model"] = record["name"]
        if record.get("model"):
            record["model"] = str(record["model"]).strip()
            cleaned.append(record)
    if not cleaned and derive:
        names = []
        for run in runs or []:
            name = str(run.get("model") or "").strip()
            if name and name not in names:
                names.append(name)
        cleaned = [{"model": name, "purpose": "planned model"} for name in names]
    return cleaned[:24]


def _enrich_selected_models(session, values):
    capabilities = ((session or {}).get("research_context") or {}).get("capabilities") or {}
    instructions = ((session or {}).get("research_context") or {}).get("instructions") or {}
    enriched = []
    for item in values or []:
        record = dict(item)
        model = record.get("model")
        capability = capabilities.get(model) or {}
        instruction = instructions.get(model) or {}
        record.setdefault("version", capability.get("version"))
        record.setdefault(
            "capability_status",
            "runnable" if capability.get("runnable_here") else "unavailable",
        )
        record.setdefault(
            "instruction_ref",
            "guideline:%s@%s" % (model, instruction.get("version") or capability.get("instruction_version") or "1.0"),
        )
        enriched.append(record)
    return enriched


def _clean_parameter_mapping(values):
    cleaned = []
    for item in _clean_records(values, 64):
        record = dict(item)
        model_input = str(
            item.get("model_input")
            or item.get("model_parameter")
            or item.get("input")
            or item.get("parameter")
            or ""
        ).strip()
        provenance = str(
            item.get("provenance_class") or item.get("provenance") or item.get("source_type") or ""
        ).strip().lower()
        evidence_ref = str(
            item.get("evidence_ref") or item.get("source_ref") or item.get("citation") or ""
        ).strip()
        record.update(
            {
                "model": str(item.get("model") or item.get("model_name") or "").strip(),
                "paper_concept": str(
                    item.get("paper_concept") or item.get("paper_parameter") or item.get("concept") or ""
                ).strip(),
                "paper_value": item.get("paper_value", item.get("source_value")),
                "model_input": model_input,
                "mapped_value": item.get("mapped_value", item.get("model_value")),
                "units": str(item.get("units") or item.get("unit") or "").strip(),
                "provenance_class": provenance,
                "confidence": str(item.get("confidence") or item.get("confidence_level") or "").strip().lower(),
                "confidence_basis": str(item.get("confidence_basis") or "").strip(),
                "evidence_ref": evidence_ref,
                "rationale": str(item.get("rationale") or item.get("reason") or "").strip(),
            }
        )
        cleaned.append(record)
    return cleaned


def _clean_outputs(values):
    if isinstance(values, dict):
        values = [values]
    if isinstance(values, str):
        return _clean_list(values, 24)
    return [dict(item) if isinstance(item, dict) else str(item).strip() for item in (values or []) if str(item).strip()][:24]


def _normalise_evidence_ref(value):
    text = str(value or "").strip().strip("[]")
    text = re.sub(r"^(?:paper|figure|table|result):", "", text, flags=re.I)
    return text.replace("#fig-", "#")


def _read_evidence_refs(session):
    sections = {_normalise_evidence_ref(item) for item in (session or {}).get("sections_read") or ()}
    figures = {_normalise_evidence_ref(item) for item in (session or {}).get("paper_figures_read") or ()}
    skill_refs = set()
    for item in (session or {}).get("evidence_ledger") or ():
        if not isinstance(item, dict):
            continue
        reference = _normalise_evidence_ref(item.get("reference"))
        if item.get("kind") == "section" and reference:
            sections.add(reference)
            if item.get("source") == "skill":
                skill_refs.add(reference)
        elif item.get("kind") in ("figure", "figure_inspection") and reference and item.get("asset_available", True) is not False:
            figures.add(reference)
    sections -= skill_refs
    return sections, figures


def _target_coverage(targets, runs, charts):
    run_ids = {run.get("id") for run in runs}
    chart_ids = {chart.get("id") for chart in charts}
    problems = []
    linked_runs = {run_id: [] for run_id in run_ids}
    linked_charts = {chart_id: [] for chart_id in chart_ids}
    for target in targets:
        target_id = target.get("id") or "target"
        bad_runs = sorted(set(target.get("run_ids") or ()) - run_ids)
        bad_charts = sorted(set(target.get("chart_ids") or ()) - chart_ids)
        if bad_runs:
            problems.append("target %s references unknown run_ids: %s" % (target_id, ", ".join(bad_runs)))
        if bad_charts:
            problems.append("target %s references unknown chart_ids: %s" % (target_id, ", ".join(bad_charts)))
        if target.get("status") not in ("partial", "unavailable") and not target.get("run_ids") and not target.get("chart_ids"):
            problems.append("target %s has no run_ids or chart_ids coverage" % target_id)
        if target.get("status") in ("partial", "unavailable") and not target.get("availability_reason"):
            problems.append("target %s is %s without an availability_reason" % (target_id, target.get("status")))
        for run_id in target.get("run_ids") or ():
            if run_id in linked_runs:
                linked_runs[run_id].append(target_id)
        for chart_id in target.get("chart_ids") or ():
            if chart_id in linked_charts:
                linked_charts[chart_id].append(target_id)
    return problems, linked_runs, linked_charts


def _ledger_entries(session, kind=None):
    return [
        item for item in (session or {}).get("evidence_ledger") or ()
        if isinstance(item, dict) and (kind is None or item.get("kind") == kind)
    ]


def _repair_item(field, before, after, reason, provenance=None, source=None):
    item = {
        "field": field,
        "from": before,
        "to": after,
        "reason": reason,
    }
    if provenance:
        item["provenance"] = provenance
    if source:
        item["source"] = source
    return item


def _model_parameter_spec(session, model, name):
    declaration = ((session or {}).get("model_declarations") or {}).get(model) or {}
    return (declaration.get("parameters") or {}).get(name) or {}


def _normalise_parameter_name(value):
    """Create a conservative comparison form for registered input names.

    This is intentionally only a name-shape comparison.  It does not use paper prose,
    Evaluation YAML, or a question-specific alias table to decide what a model input is.
    """
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(value or "").lower())).strip("_")


def _normalise_units(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _units_compatible(left, right):
    left = _normalise_units(left)
    right = _normalise_units(right)
    return not left or not right or left == right


def _registered_parameter_index(session, model_names):
    """Return declared parameter names grouped by registered model."""
    index = {}
    for model in sorted({str(name).strip() for name in model_names if str(name).strip()}):
        entry = registry.get(model, session)
        if entry:
            index[model] = dict(entry.card.get("parameters") or {})
    return index


def _mapping_candidates(raw_name, model_name, parameter_index, units=""):
    """Find exact or unambiguous registered candidates for one mapping name."""
    models = [model_name] if model_name else sorted(parameter_index)
    candidates = [
        (model, name)
        for model in models
        for name in parameter_index.get(model, {})
        if name == raw_name
    ]
    if candidates:
        return candidates

    normalised = _normalise_parameter_name(raw_name)
    if not normalised:
        return []
    candidates = [
        (model, name)
        for model in models
        for name, spec in parameter_index.get(model, {}).items()
        if _normalise_parameter_name(name) == normalised
        and _units_compatible(units, (spec or {}).get("unit"))
    ]
    if candidates:
        return candidates

    # Permit a short base name only when exactly one declared parameter has that
    # registered stem.  Thus ``density`` can resolve to a declaration such as
    # ``density_kg_m3`` without introducing a model-specific synonym table.
    candidates = [
        (model, name)
        for model in models
        for name, spec in parameter_index.get(model, {}).items()
        if _normalise_parameter_name(name).startswith(normalised + "_")
        and _units_compatible(units, (spec or {}).get("unit"))
    ]
    return candidates


def _is_paper_context_problem(problem):
    """Paper references may label a run, but never invalidate registered-model input."""
    field = str((problem or {}).get("field") or "")
    source = str((problem or {}).get("source") or "")
    return bool(
        (problem or {}).get("category") == "paper_context"
        or source.startswith("paper_conditions")
        or source.startswith("condition_provenance")
        or field.startswith("runs[") and ".parameters." in field
    )


def _expected_mapping_inputs(runs, parameter_resolution):
    """Return resolved run inputs keyed by their registered model and input name."""
    by_run = _parameter_resolution_by_run(parameter_resolution, runs)
    expected = {}
    defaulted = set()
    for run in runs or ():
        model = str(run.get("model") or "").strip()
        resolution = by_run.get(run.get("id")) or {}
        resolved = resolution.get("resolved_parameters") or run.get("parameters") or {}
        for name, value in resolved.items():
            key = (model, str(name))
            expected[key] = value
            if name in set(resolution.get("defaulted_parameters") or ()):
                defaulted.add(key)
    return expected, defaulted


def _repair_parameter_mappings(
    session,
    mappings,
    runs,
    parameter_resolution,
    paper_conditions,
    condition_provenance,
    evidence_refs,
):
    """Canonicalize mapping metadata using only registered model declarations.

    Physical run parameters are never changed here.  A mapping alias may be replaced by
    one unambiguous registered input; missing audit metadata is filled and surfaced as an
    automatic repair.  Unknown or ambiguous names remain blocking problems.
    """
    model_names = [run.get("model") for run in runs or ()]
    parameter_index = _registered_parameter_index(session, model_names)
    _expected, defaulted = _expected_mapping_inputs(runs, parameter_resolution)
    repaired = []
    problems = []
    canonical = []
    paper_conditions = dict(paper_conditions or {})
    condition_provenance = dict(condition_provenance or {})
    evidence_refs = set(evidence_refs or ())

    for index, item in enumerate(mappings or ()):
        record = dict(item)
        raw_name = str(record.get("model_input") or "").strip()
        model_name = str(record.get("model") or "").strip()
        if raw_name:
            candidates = _mapping_candidates(
                raw_name, model_name, parameter_index, record.get("units")
            )
            if len(candidates) == 1:
                candidate_model, candidate_name = candidates[0]
                if candidate_name != raw_name:
                    repaired.append(_repair_item(
                        "parameter_mapping[%d].model_input" % index,
                        raw_name,
                        candidate_name,
                        "replace an unambiguous alias with the exact registered model input",
                        "registered_model_declaration",
                        "registered_model_declaration",
                    ))
                    record["model_input"] = candidate_name
                if not model_name and candidate_model:
                    record["model"] = candidate_model
                    model_name = candidate_model
                    repaired.append(_repair_item(
                        "parameter_mapping[%d].model" % index,
                        "",
                        candidate_model,
                        "bind the mapping to the registered model that declares the input",
                        "registered_model_declaration",
                        "registered_model_declaration",
                    ))
                elif model_name and candidate_model != model_name:
                    problems.append({
                        "field": "parameter_mapping[%d].model" % index,
                        "source": model_name,
                        "actual": model_name,
                        "expected": candidate_model,
                        "allowed_values": [candidate_model],
                        "repair": "Use the registered model that declares this input.",
                        "blocking": True,
                    })
            else:
                if model_name:
                    candidate_values = sorted(parameter_index.get(model_name) or ())
                elif len(parameter_index) == 1:
                    candidate_values = sorted(next(iter(parameter_index.values()), {}).keys())
                else:
                    candidate_values = [
                        "%s.%s" % (model, name)
                        for model, names in parameter_index.items()
                        for name in names
                    ]
                if len(candidates) > 1:
                    candidate_values = ["%s.%s" % pair for pair in candidates]
                problems.append({
                    "field": "parameter_mapping[%d].model_input" % index,
                    "source": "registered_model_declaration",
                    "actual": raw_name,
                    "expected": "an exact registered model input",
                    "allowed_values": candidate_values,
                    "repair": (
                        "Replace the alias with one exact input from list_models."
                        if len(candidates) > 1
                        else "Replace the unknown input with an exact parameter returned by list_models."
                    ),
                    "blocking": True,
                })

        model_input = str(record.get("model_input") or "").strip()
        model_name = str(record.get("model") or "").strip()
        if not model_input or not model_name:
            canonical.append(record)
            continue

        key = (model_name, model_input)
        spec = parameter_index.get(model_name, {}).get(model_input) or {}
        if not record.get("units") and spec.get("unit"):
            record["units"] = str(spec.get("unit"))
            repaired.append(_repair_item(
                "parameter_mapping[%d].units" % index,
                "",
                record["units"],
                "copy the declared unit for the registered model input",
                "registered_model_declaration",
                "registered_model_declaration",
            ))
        if not record.get("paper_concept"):
            record["paper_concept"] = model_input
            repaired.append(_repair_item(
                "parameter_mapping[%d].paper_concept" % index,
                "",
                model_input,
                "use the registered input label when no paper-side concept was supplied",
                "model_assumption",
                "registered_model_declaration",
            ))

        provenance = str(record.get("provenance_class") or "").strip().lower()
        evidence_ref = _normalise_evidence_ref(record.get("evidence_ref"))
        if not provenance or provenance not in PARAMETER_PROVENANCE:
            if (
                model_input in paper_conditions
                and _normalise_evidence_ref(condition_provenance.get(model_input)) in evidence_refs
            ):
                provenance = "paper_inferred"
                if not evidence_ref:
                    evidence_ref = _normalise_evidence_ref(condition_provenance.get(model_input))
            elif key in defaulted:
                provenance = "backend_default"
            else:
                provenance = "model_assumption"
            before = record.get("provenance_class") or ""
            record["provenance_class"] = provenance
            repaired.append(_repair_item(
                "parameter_mapping[%d].provenance_class" % index,
                before,
                provenance,
                "classify mapping provenance from registered resolution and opened evidence",
                provenance,
                "registered_model_declaration",
            ))
        if evidence_ref != str(record.get("evidence_ref") or "").strip():
            record["evidence_ref"] = evidence_ref
        if not record.get("rationale"):
            if record.get("provenance_class") == "backend_default":
                rationale = "The registered backend supplied this default; it is not paper evidence."
            elif record.get("provenance_class") == "model_assumption":
                rationale = "The registered input was retained as a model assumption without paper evidence."
            else:
                rationale = "The registered input was mapped to the opened paper evidence."
            record["rationale"] = rationale
            repaired.append(_repair_item(
                "parameter_mapping[%d].rationale" % index,
                "",
                rationale,
                "add an auditable explanation for the paper-to-model mapping",
                record.get("provenance_class"),
                "registered_model_declaration",
            ))
        confidence, confidence_basis = _provenance_confidence(record.get("provenance_class"))
        if record.get("confidence") not in PARAMETER_CONFIDENCE:
            before = record.get("confidence") or ""
            record["confidence"] = confidence
            repaired.append(_repair_item(
                "parameter_mapping[%d].confidence" % index,
                before,
                confidence,
                "label confidence from the mapping provenance without changing the run value",
                record.get("provenance_class"),
                "provenance_classification",
            ))
        if not record.get("confidence_basis"):
            record["confidence_basis"] = confidence_basis
            repaired.append(_repair_item(
                "parameter_mapping[%d].confidence_basis" % index,
                "",
                confidence_basis,
                "explain why the mapping is paper-supported, user-specified, backend-provided, assumed, or guessed",
                record.get("provenance_class"),
                "provenance_classification",
            ))
        canonical.append(record)

    return canonical, repaired, problems, _expected, defaulted


def _parameter_resolution_by_run(parameter_resolution, runs):
    by_run = {
        item.get("run_id"): item for item in (parameter_resolution or ())
        if isinstance(item, dict) and item.get("run_id")
    }
    # Revisions from older sessions may not have the resolution ledger.  Treat the
    # stored parameters as requested in that case; this preserves the reviewed values
    # and still lets the validator report any missing metadata.
    for run in runs or ():
        run_id = run.get("id")
        if run_id not in by_run:
            params = dict(run.get("parameters") or {})
            by_run[run_id] = {
                "run_id": run_id,
                "model": run.get("model"),
                "requested_parameters": dict(params),
                "resolved_parameters": dict(params),
                "defaulted_parameters": [],
            }
    return by_run


def _same_value(left, right):
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-12)
    return left == right


def _mark_user_revised_inputs(plan, before_plan, changes):
    """Mark run parameters changed through a user revision as user-specified."""
    revised_runs = changes.get("runs")
    if not isinstance(revised_runs, list):
        return
    before_runs = {
        str(item.get("id")): item
        for item in before_plan.get("runs") or []
        if isinstance(item, dict) and item.get("id")
    }
    changed_inputs = set()
    for run in revised_runs:
        if not isinstance(run, dict) or not run.get("id"):
            continue
        old = before_runs.get(str(run.get("id"))) or {}
        old_parameters = old.get("parameters") or {}
        for name, value in (run.get("parameters") or {}).items():
            if not _same_value(old_parameters.get(name), value):
                changed_inputs.add(name)
    if not changed_inputs:
        return
    for mapping in plan.get("parameter_mapping") or []:
        if mapping.get("model_input") not in changed_inputs:
            continue
        mapping["provenance_class"] = "user_specified"
        mapping["rationale"] = (
            "This input was changed in the user-approved revision; any paper value "
            "remains comparison context rather than a model-validity constraint."
        )


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
    inspectable_figures = {
        _normalise_evidence_ref(item.get("reference"))
        for item in _ledger_entries(session, "figure")
        if item.get("asset_available", True) is not False and item.get("reference")
    }
    inspected_figures = {
        _normalise_evidence_ref(item.get("reference"))
        for item in _ledger_entries(session, "figure_inspection")
        if item.get("analysis_status") not in ("unavailable",) and item.get("reference")
    }
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

    for index, target in enumerate(reproduction_targets):
        refs = [_normalise_evidence_ref(ref) for ref in target.get("evidence_refs") or ()]
        if not refs and relevant_refs:
            before = list(refs)
            target["evidence_refs"] = [relevant_refs[0]]
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
        quantity = str(target.get("target_quantity") or "").lower()
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
        run_ids = [
            run.get("id") for run in runs or ()
            if not target_outputs or str((run.get("parameters") or {}).get("output") or "").lower() in target_outputs
        ]
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
        requested = resolution.get("requested_parameters") or {}
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


def _evidence_problem_summary(question, problems):
    label = "Reproduction"
    evidence = sum(
        1 for item in problems
        if any(token in str(item.get("field", "")) for token in ("evidence", "literature"))
    )
    coverage = sum(
        1 for item in problems
        if "coverage" in str(item.get("field", ""))
        or str(item.get("field", "")).startswith("reproduction_targets")
    )
    mappings = sum(1 for item in problems if "mapping" in str(item.get("field", "")))
    summary = "%s plan incomplete: %d evidence issue(s), %d target coverage issue(s), and %d parameter mapping issue(s)." % (
        label, evidence, coverage, mappings
    )
    mapping_details = []
    for item in problems:
        if "mapping" not in str(item.get("field", "")):
            continue
        detail = str(item.get("field") or "parameter_mapping")
        if item.get("actual") not in (None, ""):
            detail += " (actual=%r)" % item.get("actual")
        mapping_details.append(detail)
    if mapping_details:
        shown = mapping_details[:4]
        suffix = "; ".join(shown)
        if len(mapping_details) > len(shown):
            suffix += "; +%d more" % (len(mapping_details) - len(shown))
        summary += " Mapping fields: %s." % suffix
    return summary


def _evidence_plan_problems(session, question, literature_evidence, reproduction_targets,
                            selected_models, parameter_mapping, outputs, runs, charts,
                            parameter_resolution=None):
    if not is_reproduction_question(question, session):
        return []
    problems = []
    sections, figures = _read_evidence_refs(session)
    inspectable_figures = {
        _normalise_evidence_ref(item.get("reference"))
        for item in _ledger_entries(session, "figure")
        if item.get("asset_available", True) is not False and item.get("reference")
    }
    inspected_figures = {
        _normalise_evidence_ref(item.get("reference"))
        for item in _ledger_entries(session, "figure_inspection")
        if item.get("analysis_status") not in ("unavailable",) and item.get("reference")
    }
    if not sections:
        problems.append({
            "field": "literature_evidence",
            "source": "session.sections_read",
            "expected": "at least one opened paper section",
            "repair": "Call read_literature for the relevant paper section before proposing the plan.",
        })
    if not literature_evidence:
        problems.append({
            "field": "literature_evidence",
            "source": "research_plan",
            "expected": "opened section/figure references",
            "repair": "Add the paper section references and explain their role in the reproduction.",
        })
    for index, item in enumerate(literature_evidence):
        ref = _normalise_evidence_ref(item.get("evidence_ref"))
        if ref and ref not in sections and ref not in figures:
            problems.append({
                "field": "literature_evidence[%d].evidence_ref" % index,
                "source": ref,
                "expected": "a section or source figure opened in this session",
                "repair": "Read the cited section or figure, then use its returned citation reference.",
            })
    if not reproduction_targets:
        problems.append({
            "field": "reproduction_targets",
            "source": "research_plan",
            "expected": "at least one figure, table, or result target",
            "repair": "Record the paper result to reproduce, its evidence references, and its planned coverage.",
        })
    for index, target in enumerate(reproduction_targets):
        prefix = "reproduction_targets[%d]" % index
        if not target.get("source_id"):
            problems.append({"field": prefix + ".source_id", "source": "research_plan", "expected": "figure/table/result identifier", "repair": "Add the identifier from the paper."})
        if not target.get("target_quantity"):
            problems.append({"field": prefix + ".target_quantity", "source": "research_plan", "expected": "quantity or result being reproduced", "repair": "Name the paper quantity or result."})
        if not target.get("expected_comparison"):
            problems.append({"field": prefix + ".expected_comparison", "source": "research_plan", "expected": "comparison intent", "repair": "Explain how the model output will be compared with the paper result."})
        refs = {_normalise_evidence_ref(ref) for ref in target.get("evidence_refs") or ()}
        if not refs:
            problems.append({"field": prefix + ".evidence_refs", "source": "research_plan", "expected": "opened paper evidence", "repair": "Read and cite the relevant section, figure, or table."})
        elif not refs.intersection(sections | figures):
            problems.append({"field": prefix + ".evidence_refs", "source": ", ".join(sorted(refs)), "expected": "opened evidence reference", "repair": "Use the citation returned by read_literature or read_paper_figure."})
        if (
            target.get("source_type") == "figure"
            and not refs.intersection(figures)
            and target.get("status") not in ("partial", "unavailable")
        ):
            problems.append({"field": prefix + ".evidence_refs", "source": "paper_figures_read", "expected": "source figure opened with read_paper_figure", "repair": "Call read_paper_figure before proposing the reproduction."})
        if (
            target.get("source_type") == "figure"
            and refs.intersection(inspectable_figures)
            and not refs.intersection(inspected_figures)
            and target.get("status") not in ("partial", "unavailable")
        ):
            problems.append({
                "field": prefix + ".figure_inspection",
                "source": ", ".join(sorted(refs.intersection(inspectable_figures))),
                "expected": "visual inspection of the opened source figure",
                "repair": "Call inspect_paper_figure after read_paper_figure and record axes, legends, panels, and qualitative trends; do not digitize curves automatically.",
            })
    if not selected_models:
        problems.append({"field": "selected_models", "source": "research_plan", "expected": "each model used for reproduction", "repair": "List the selected model and its purpose after list_models/read_model_instruction."})
    planned_models = {str(run.get("model") or "").strip() for run in runs}
    selected_names = {str(item.get("model") or "").strip() for item in selected_models}
    for model in sorted(planned_models - selected_names):
        problems.append({"field": "selected_models", "source": model, "expected": "model used by a planned run", "repair": "Add this model to selected_models with its capability and instruction provenance."})
    if not parameter_mapping:
        problems.append({"field": "parameter_mapping", "source": "research_plan", "expected": "paper-to-model parameter mappings", "repair": "Map paper concepts to exact registered model input names and mark their provenance."})
    parameter_index = _registered_parameter_index(session, planned_models | selected_names)
    declared_inputs = {
        model: set(parameters)
        for model, parameters in parameter_index.items()
    }
    for index, item in enumerate(parameter_mapping):
        prefix = "parameter_mapping[%d]" % index
        if not item.get("paper_concept"):
            problems.append({"field": prefix + ".paper_concept", "source": "research_plan", "actual": "", "expected": "paper-side concept", "repair": "Name the concept used by the paper.", "blocking": True})
        if not item.get("model_input"):
            problems.append({"field": prefix + ".model_input", "source": "research_plan", "actual": "", "expected": "exact registered model input", "allowed_values": sorted({name for names in declared_inputs.values() for name in names}), "repair": "Use the parameter name returned by list_models.", "blocking": True})
        provenance = item.get("provenance_class")
        if provenance not in PARAMETER_PROVENANCE:
            problems.append({"field": prefix + ".provenance_class", "source": provenance or "missing", "actual": provenance or "", "expected": ", ".join(PARAMETER_PROVENANCE), "allowed_values": list(PARAMETER_PROVENANCE), "repair": "Choose one provenance class and explain the mapping.", "blocking": True})
        if not item.get("rationale"):
            problems.append({"field": prefix + ".rationale", "source": "research_plan", "actual": "", "expected": "mapping rationale", "repair": "Explain how the paper value becomes the model input value.", "blocking": True})
        model_name = str(item.get("model") or "").strip()
        model_input = item.get("model_input")
        if model_input and model_name and model_name in declared_inputs and model_input not in declared_inputs[model_name]:
            problems.append({
                "field": prefix + ".model_input",
                "source": "registered_model_declaration",
                "actual": model_input,
                "expected": "a parameter returned by list_models for %s" % model_name,
                "allowed_values": sorted(declared_inputs[model_name]),
                "repair": "Replace it with the exact registered input name.",
                "blocking": True,
            })
        if model_input and not model_name and len(planned_models | selected_names) > 1:
            problems.append({
                "field": prefix + ".model",
                "source": "research_plan",
                "actual": "",
                "expected": "the registered model declaring this input",
                "allowed_values": sorted(planned_models | selected_names),
                "repair": "Add model to every mapping so coverage is scoped to (model, model_input).",
                "blocking": True,
            })
        if provenance in ("paper_explicit", "paper_inferred") and not item.get("evidence_ref"):
            problems.append({"field": prefix + ".evidence_ref", "source": provenance, "actual": "", "expected": "paper evidence reference", "repair": "Attach the opened section, figure, or table reference.", "blocking": True})
    expected, defaulted = _expected_mapping_inputs(runs, parameter_resolution)
    mapped_keys = {
        (str(item.get("model") or "").strip(), item.get("model_input"))
        for item in parameter_mapping
        if item.get("model_input") and item.get("model")
    }
    missing_keys = sorted(set(expected) - mapped_keys)
    unresolved = [key for key in missing_keys if key not in defaulted]
    if unresolved:
        for model_name, model_input in unresolved:
            problems.append({
                "field": "parameter_mapping.%s.%s" % (model_name, model_input),
                "source": "resolved_run_parameters",
                "actual": None,
                "expected": "mapping or explicitly declared assumption for every run input",
                "allowed_values": sorted(declared_inputs.get(model_name) or ()),
                "repair": "Add one mapping entry for this exact registered model input.",
                "blocking": True,
            })
    for model_name, model_input in sorted(set(missing_keys) & defaulted):
        problems.append({
            "field": "parameter_mapping.%s.%s" % (model_name, model_input),
            "source": "backend_default",
            "actual": None,
            "expected": "an auditable backend_default mapping or an explicit paper/user value",
            "allowed_values": sorted(declared_inputs.get(model_name) or ()),
            "repair": "Review the inserted default and confirm it is acceptable; do not treat it as paper evidence.",
            "provenance": "backend_default",
            "blocking": False,
        })
    coverage_problems, _, _ = _target_coverage(reproduction_targets, runs, charts)
    for problem in coverage_problems:
        problems.append({"field": "reproduction_targets.coverage", "source": "runs/charts", "expected": "known run_ids or chart_ids", "repair": problem})
    if not outputs:
        problems.append({"field": "outputs", "source": "research_plan", "expected": "model outputs used to evaluate the target", "repair": "Declare the quantities/outputs that will be compared."})
    return problems


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


def _repair_missing_protocol_steps(steps, runs, charts):
    """Recover a semantically complete plan whose optional ``steps`` field was omitted.

    The executable run and chart declarations are the authoritative workflow.  Rejecting
    five valid runs merely because a provider omitted a redundant prose field turns a
    harmless formatting error into a planning loop.  We preserve any authored steps and
    append only the missing workflow stages, recording the change for human review.
    """
    if len(steps) >= 3 or not runs or not charts:
        return steps, []

    before = list(steps)
    defaults = [
        "Verify the cited paper evidence, registered-model capabilities, controlled conditions, and baseline configuration.",
        "Execute every declared baseline, main, and diagnostic physical-model run with output and numerical quality control.",
        "Render the required figures from actual outputs, calculate the declared comparison metrics, review figure quality, and report conclusions and limitations.",
    ]
    for item in defaults:
        if len(steps) >= 3:
            break
        if item not in steps:
            steps.append(item)
    return steps, [
        {
            "field": "steps",
            "from": before,
            "to": list(steps),
            "reason": (
                "the proposal already declared executable runs and charts; missing prose "
                "workflow stages were reconstructed for human review"
            ),
        }
    ]


def _clean_charts(charts):
    cleaned = []
    for index, chart in enumerate(charts or []):
        if not isinstance(chart, dict):
            continue
        x = str(chart.get("x") or "").strip()
        ys = _clean_list(chart.get("ys") or ([chart.get("y")] if chart.get("y") else []), 6)
        if not x or not ys:
            continue
        cleaned.append(
            {
                "id": str(chart.get("id") or "chart_%d" % (index + 1)).strip(),
                "label": str(chart.get("label") or "%s versus %s" % (", ".join(ys), x)).strip(),
                "kind": str(chart.get("kind") or "line").strip(),
                "x": x,
                "y": ys[0],
                "ys": ys,
                "required": bool(chart.get("required", True)),
                "purpose": str(chart.get("purpose") or "result").strip(),
                "x_label": str(chart.get("x_label") or "").strip(),
                "y_label": str(chart.get("y_label") or "").strip(),
            }
        )
    return cleaned[:8]


def _repair_sweep_bounds(model, parameters, card):
    """Leave sweep bounds unchanged so the registered validator can reject invalid input.

    Sweep bounds are user-authored physical conditions, not metadata that the planner may
    silently rewrite. The model contract remains the sole source of the hard range check;
    keeping the original values also makes the structured error actionable.
    """
    return dict(parameters), []


def _run_validation_details(model, parameters, problems, card):
    """Convert model-contract failures into field/source/action records for the UI."""
    details = []
    declared = card.get("parameters") or {}
    for message in problems:
        text = str(message)
        field = text.split(" = ", 1)[0].split(" must", 1)[0].split(" is", 1)[0].strip()
        spec = declared.get(field) or {}
        expected = "registered model declaration"
        if field in ("sweep_start", "sweep_stop"):
            sweep = parameters.get("sweep_parameter")
            target = declared.get(sweep) or {}
            expected = ("%s to %s %s" % (
                target.get("minimum"), target.get("maximum"), target.get("unit", "")
            )).strip()
        elif spec.get("minimum") is not None and spec.get("maximum") is not None:
            expected = ("%s to %s %s" % (
                spec.get("minimum"), spec.get("maximum"), spec.get("unit", "")
            )).strip()
        elif spec.get("enum"):
            expected = "one of %s" % ", ".join(map(str, spec.get("enum")))
        details.append(
            {
                "field": field or "parameters",
                "source": "registered_model_declaration",
                "expected": expected,
                "actual": parameters.get(field),
                "repair": "Use a value accepted by the registered model declaration; do not infer a limit from paper text.",
                "provenance": "registered_model_declaration",
                "blocking": True,
                "message": text,
            }
        )
    return details


def _clean_runs(runs):
    cleaned = []
    problems = []
    problem_details = []
    repairs = []
    resolutions = []
    for index, run in enumerate(runs or []):
        if not isinstance(run, dict):
            message = "planned run %d is not an object" % (index + 1)
            problems.append(message)
            problem_details.append({
                "field": "runs[%d]" % index,
                "source": "research_plan",
                "expected": "run object",
                "actual": type(run).__name__,
                "repair": "Submit the affected run as an object with model and parameters.",
                "blocking": True,
                "message": message,
            })
            continue
        model = str(run.get("model") or "").strip()
        entry = registry.get(model)
        if entry is None:
            message = "planned run %d uses unknown model %r" % (index + 1, model)
            problems.append(message)
            problem_details.append({
                "field": "runs[%d].model" % index,
                "source": "registered_model_registry",
                "expected": "a registered model name",
                "actual": model,
                "repair": "Call list_models and choose a registered model.",
                "blocking": True,
                "message": message,
            })
            continue
        requested_parameters = dict(run.get("parameters") or {})
        parameters, bound_repairs = _repair_sweep_bounds(
            model, requested_parameters, entry.card
        )
        for repair in bound_repairs:
            repairs.append({"run_id": str(run.get("id") or "run_%d" % (index + 1)), **repair})
        resolved, run_problems = validation.resolve(entry.card, parameters, enforce=True)
        if run_problems:
            problems.extend("planned run %d: %s" % (index + 1, item) for item in run_problems)
            for detail in _run_validation_details(model, parameters, run_problems, entry.card):
                detail["field"] = "runs[%d].parameters.%s" % (index, detail["field"])
                problem_details.append(detail)
            continue
        run_id = str(run.get("id") or "run_%d" % (index + 1)).strip()
        defaulted_parameters = sorted(set(resolved) - set(requested_parameters))
        resolutions.append(
            {
                "run_id": run_id,
                "model": model,
                "requested_parameters": requested_parameters,
                "resolved_parameters": dict(resolved),
                "defaulted_parameters": defaulted_parameters,
            }
        )
        cleaned.append(
            {
                "id": run_id,
                "label": str(run.get("label") or "%s run" % model).strip(),
                "model": model,
                "parameters": resolved,
                "requested_parameters": requested_parameters,
                "resolved_parameters": dict(resolved),
                "defaulted_parameters": defaulted_parameters,
                "stage": str(run.get("stage") or "main").strip(),
            }
        )
    # A multi-density/multi-microstructure experiment can legitimately require more than
    # eight configurations (Q4 uses a baseline plus two five-density families). Silently
    # dropping later runs changes the reviewed experiment and makes chart validation
    # inexplicable. Keep a generous explicit ceiling instead.
    if len(cleaned) > 24:
        message = "a proposal may contain at most 24 physical-model runs"
        problems.append(message)
        problem_details.append({
            "field": "runs",
            "source": "research_plan",
            "expected": "at most 24 physical-model runs",
            "actual": len(cleaned),
            "repair": "Remove unneeded runs or split the experiment into a new reviewed plan.",
            "blocking": True,
            "message": message,
        })
    return cleaned[:24], problems, repairs, resolutions[:24], problem_details


def propose(
    session,
    question,
    objective,
    hypothesis,
    steps,
    parameters=None,
    runs=None,
    charts=None,
    success_criteria=None,
    assumptions=None,
    limitations=None,
    quantities=None,
    controls=None,
    metrics=None,
    diagnostics=None,
    stop_conditions=None,
    baseline_run_id="",
    paper_conditions=None,
    condition_provenance=None,
    literature_evidence=None,
    reproduction_targets=None,
    selected_models=None,
    parameter_mapping=None,
    outputs=None,
):
    """Store an LLM-authored proposal; never infer one from a question template."""
    question = str(question or "").strip()
    objective = str(objective or "").strip()
    hypothesis = str(hypothesis or "").strip()
    steps = _clean_list(steps)
    charts = _clean_charts(charts)
    runs, run_problems, run_repairs, parameter_resolution, run_problem_details = _clean_runs(runs)
    quantities = _clean_list(quantities, 12)
    controls = _clean_list(controls, 12)
    metrics = _clean_list(metrics, 12)
    diagnostics = _clean_list(diagnostics, 12)
    stop_conditions = _clean_list(stop_conditions, 12)
    success_criteria = _clean_list(success_criteria, 12)
    assumptions = _clean_list(assumptions, 12)
    limitations = _clean_list(limitations, 12)
    baseline_run_id = str(baseline_run_id or "").strip()
    paper_conditions = dict(paper_conditions or {})
    condition_provenance = dict(condition_provenance or {})
    literature_evidence = _clean_literature_evidence(literature_evidence)
    reproduction_targets = _clean_reproduction_targets(reproduction_targets)
    selected_models = _clean_selected_models(
        selected_models,
        runs,
        derive=not is_reproduction_question(question, session),
    )
    selected_models = _enrich_selected_models(session, selected_models)
    parameter_mapping = _clean_parameter_mapping(parameter_mapping)
    outputs = _clean_outputs(outputs)
    if not question or not objective or not hypothesis:
        return _fail("A proposal requires question, objective and hypothesis.")
    if not charts:
        return _fail("A proposal requires at least one chart option with x and y fields.")
    if run_problems:
        return _fail(
            "The proposed execution plan is invalid: %s" % "; ".join(run_problems),
            {
                "error_code": "run_validation",
                "problems": run_problem_details,
                "repair_hints": [
                    "Use only model/microstructure combinations declared by list_models.",
                    "Do not preserve an invalid same-microstructure comparison by silently changing physics; remove the incompatible run or choose a declared compatible formulation.",
                ],
            },
        )
    if not runs:
        return _fail("A proposal requires at least one explicit registered physical-model run.")
    steps, structural_repairs = _repair_missing_protocol_steps(steps, runs, charts)
    if len(steps) < 3:
        return _fail(
            "A proposal requires at least three executable research steps.",
            {
                "error_code": "steps_missing",
                "repair_hints": [
                    "Describe model validation, formal execution, and figure/metric review as separate steps.",
                    "Keep the already declared runs and charts; this is a plan-format correction, not a new experiment.",
                ],
            },
        )
    # Paper reproduction is evidence-led.  The agent derives conditions and runs from the
    # literature sections it actually read; this validator never loads a pre-authored
    # protocols.yaml or silently repairs the proposal into a benchmark matrix.
    reference_repairs = []
    paper_session = (session.get("research_context") or {}).get("paper_session") or {}
    paper_section = paper_session.get("paper_section")
    (
        literature_evidence,
        reproduction_targets,
        selected_models,
        parameter_mapping,
        outputs,
        paper_conditions,
        condition_provenance,
        metadata_repairs,
        metadata_problems,
        context_warnings,
    ) = _repair_reproduction_metadata(
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
    )
    quality_problems = []
    for label, values in (
        ("quantities of interest", quantities),
        ("controlled conditions", controls),
        ("acceptance metrics", metrics),
        ("diagnostics or robustness checks", diagnostics),
        ("success criteria", success_criteria),
        ("stop conditions", stop_conditions),
        ("assumptions", assumptions),
        ("limitations", limitations),
    ):
        if not values:
            quality_problems.append(label)
    for problem in metadata_problems:
        if problem.get("blocking", True) and not str(problem.get("field", "")).startswith("parameter_mapping") and not _is_paper_context_problem(problem):
            quality_problems.append(
                "%s (expected %r; repair: %s)"
                % (problem.get("field"), problem.get("expected"), problem.get("repair"))
            )
    blocking_metadata_problems = [
        item for item in metadata_problems
        if item.get("blocking", True)
        and not str(item.get("field", "")).startswith("parameter_mapping")
        and not _is_paper_context_problem(item)
    ]
    if blocking_metadata_problems:
        return _fail(
            "The reproduction proposal contains non-model validation errors: %s"
            % "; ".join(problem.get("field", "unknown") for problem in blocking_metadata_problems),
            {
                "error_code": "research_plan_validation",
                "stage": "registered_model_validation",
                "problems": blocking_metadata_problems,
                "automatic_repairs": metadata_repairs,
                "repair_hints": [problem.get("repair") for problem in blocking_metadata_problems if problem.get("repair")],
            },
        )
    run_ids = [run["id"] for run in runs]
    if baseline_run_id not in run_ids:
        quality_problems.append("baseline_run_id naming one planned run")
    if quality_problems:
        provenance_missing = any(
            item.startswith("paper_conditions") or item.startswith("condition_provenance")
            for item in quality_problems
        )
        return _fail(
            "The proposal is a computation checklist, not yet a scientific protocol. Add: %s."
            % ", ".join(quality_problems),
            {
                "error_code": (
                    "paper_condition_provenance_missing"
                    if provenance_missing
                    else "plan_quality"
                ),
                "problems": quality_problems,
                "repair_hints": [
                    (
                        "Read the relevant paper section and add paper_conditions plus "
                        "condition_provenance before resubmitting the generated protocol."
                        if provenance_missing
                        else "Complete every required research-protocol field and resubmit the proposal."
                    )
                ],
            },
        )
    evidence_problems = _evidence_plan_problems(
        session,
        question,
        literature_evidence,
        reproduction_targets,
        selected_models,
        parameter_mapping,
        outputs,
        runs,
        charts,
        parameter_resolution,
    )
    evidence_problem_fields = {
        str(item.get("field", "")) for item in evidence_problems
    }
    for problem in metadata_problems:
        field = str(problem.get("field", ""))
        if field in evidence_problem_fields:
            # Prefer the metadata repair detail, which includes registered candidates and
            # the exact source of an alias/ambiguity failure.
            evidence_problems = [
                {**item, **problem} if str(item.get("field", "")) == field else item
                for item in evidence_problems
            ]
        else:
            evidence_problems.append(problem)
            evidence_problem_fields.add(field)
    evidence_problems.extend(blocking_metadata_problems)
    nonblocking_evidence_warnings = [
        item for item in evidence_problems if not item.get("blocking", True)
    ]
    if evidence_problems and any(item.get("blocking", True) for item in evidence_problems):
        return _fail(
            _evidence_problem_summary(
                question,
                [item for item in evidence_problems if item.get("blocking", True)],
            ),
            {
                "error_code": "reproduction_evidence_incomplete",
                "stage": "reproduction_metadata",
                "problem_count": sum(1 for item in evidence_problems if item.get("blocking", True)),
                "automatic_repairs": metadata_repairs,
                "problems": evidence_problems,
                "repair_hints": [item.get("repair") for item in evidence_problems if item.get("repair")],
            },
        )
    coverage_problems, linked_runs, linked_charts = _target_coverage(
        reproduction_targets, runs, charts
    )
    if not coverage_problems:
        for run in runs:
            run["target_ids"] = sorted(
                set(run.get("target_ids") or ()) | set(linked_runs.get(run["id"]) or ())
            )
        for chart in charts:
            chart["target_ids"] = sorted(
                set(chart.get("target_ids") or ()) | set(linked_charts.get(chart["id"]) or ())
            )
    automatic_repairs = list(run_repairs)
    automatic_repairs.extend(structural_repairs)
    automatic_repairs.extend(reference_repairs)
    automatic_repairs.extend(metadata_repairs)
    automatic_repairs.extend(_repair_required_companion_outputs(question, charts, runs))
    automatic_repairs.extend(_repair_sampling_density(charts, runs))
    automatic_repairs.extend(_repair_chart_axes(charts, runs))
    dependency_problems = _output_dependency_problems(charts, runs)
    if dependency_problems:
        return _fail(
            "The proposed experiment sweeps a parameter that cannot affect its output: %s"
            % "; ".join(dependency_problems),
            {
                "error_code": "output_independent_sweep",
                "problems": dependency_problems,
                "repair_hints": [
                    "DORT streams control the radiative-transfer solver and may be swept only for tb outputs.",
                    "For electromagnetic coefficients, sweep a medium/sensor variable such as density_kg_m3, angle_deg, frequency_ghz, corr_length_m, or radius_m.",
                    "Keep solver-convergence charts separate from electromagnetic-coefficient charts.",
                ],
            },
        )
    chart_problems = _validate_chart_runs(charts, runs)
    if chart_problems:
        candidate_axes = sorted(
            {
                (run.get("parameters") or {}).get("sweep_parameter")
                for run in runs
                if (run.get("parameters") or {}).get("sweep_parameter") not in (None, "none")
            }
        )
        return _fail(
            "The proposed chart cannot be produced by the planned runs: %s" % "; ".join(chart_problems),
            {
                "error_code": "chart_axis_mismatch",
                "problems": chart_problems,
                "candidate_numeric_axes": candidate_axes,
                "repair_hints": [
                    "A chart x must be the exact common sweep_parameter of its producing runs, not electromagnetic_model, coefficient_type, model, or configuration.",
                    "Use separate charts for coefficient outputs and brightness-temperature outputs when their runs use different output groups.",
                    "If no numeric sweep exists, add the same scientifically relevant sweep_parameter/start/stop/points to every compared run.",
                ],
            },
        )
    coverage_problems = _question_coverage_problems(question, runs, charts)
    if coverage_problems:
        return _fail(
            "The plan does not measure every quantity or attribution requested by the question: %s"
            % "; ".join(coverage_problems)
        )
    plan = {
        "plan_version": 1,
        "title": objective,
        "question": question,
        "objective": objective,
        "hypothesis": hypothesis,
        "steps": steps,
        "parameters": dict(parameters or {}),
        "paper_conditions": paper_conditions,
        "condition_provenance": condition_provenance,
        "literature_evidence": literature_evidence,
        "reproduction_targets": reproduction_targets,
        "selected_models": selected_models,
        "parameter_mapping": parameter_mapping,
        "parameter_resolution": parameter_resolution,
        "outputs": outputs,
        "runs": runs,
        "charts": charts,
        "quantities": quantities,
        "controls": controls,
        "metrics": metrics,
        "diagnostics": diagnostics,
        "success_criteria": success_criteria,
        "stop_conditions": stop_conditions,
        "assumptions": assumptions,
        "limitations": limitations,
        "baseline_run_id": baseline_run_id,
        "automatic_repairs": automatic_repairs,
        "validation_warnings": list(context_warnings) + nonblocking_evidence_warnings,
        "capability_gaps": _capability_gaps(question),
        "reference_sections": sorted(session.get("sections_read") or ()),
        "reference_paper_sections": [paper_section] if paper_section else [],
        "approval_state": "plan_review",
    }
    plan["outcome_scope"] = "partial" if plan["capability_gaps"] else "full"
    session["research"] = {
        "question": question,
        "plan_version": 1,
        "phase": "plan_review",
        "plan": plan,
        "selected_chart": None,
        "selected_charts": [],
        "pseudo": None,
        "preview_version": 0,
        # The initial plan is useful to inspect immediately. A successful chat
        # revision collapses the obsolete long body while keeping its new summary.
        "plan_card_expanded": True,
        "review_log": [],
        "execution_resume_sent": False,
        "proposed_by": "llm",
    }
    summary = "LLM-authored research plan v001 is ready for human review."
    if automatic_repairs:
        summary += (
            " Backend applied %d auditable reference/presentation repair(s); review them explicitly."
            % len(automatic_repairs)
        )
    return _needs(summary, _public(session["research"]))


def status(session):
    project = session.get("research")
    if not project:
        return _needs("No research proposal exists yet. Analyse the question and propose one.", {"phase": "analysis"})
    return _ok("Research project is in phase %s." % project["phase"], _public(project))


_REVISION_FIELDS = (
    "objective", "hypothesis", "steps", "parameters", "paper_conditions",
    "condition_provenance", "literature_evidence", "reproduction_targets",
    "selected_models", "parameter_mapping", "outputs", "runs", "charts",
    "quantities", "controls", "metrics", "diagnostics", "success_criteria",
    "stop_conditions", "assumptions", "limitations", "baseline_run_id",
)
_REVISION_SENTINEL = object()


def _revision_value(plan, field):
    value = plan
    for part in str(field).split("."):
        if not isinstance(value, dict) or part not in value:
            return _REVISION_SENTINEL
        value = value[part]
    return value


def _revision_value_text(value, limit=220):
    if value is _REVISION_SENTINEL:
        return "<missing>"
    if isinstance(value, (dict, list, tuple)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    else:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _revision_diff(before, after, requested):
    """Return a compact, field-level diff while preserving full plan values elsewhere."""
    fields = []
    for key, value in (requested or {}).items():
        if key in {"note", "reason"} or value is None:
            continue
        if key == "parameters" and isinstance(value, dict):
            fields.extend("parameters.%s" % name for name in value)
        elif key not in _REVISION_FIELDS:
            fields.append("parameters.%s" % key)
        else:
            fields.append(key)

    changed = []
    added = []
    removed = []
    for field in dict.fromkeys(fields):
        old = _revision_value(before, field)
        new = _revision_value(after, field)
        if old == new:
            continue
        item = {"field": field, "from": None if old is _REVISION_SENTINEL else old,
                "to": None if new is _REVISION_SENTINEL else new}
        if old is _REVISION_SENTINEL or old in (None, "", [], {}):
            added.append(item)
        elif new is _REVISION_SENTINEL or new in (None, "", [], {}):
            removed.append(item)
        else:
            changed.append(item)

    preserved = [
        field for field in ("runs", "charts", "literature_evidence", "reproduction_targets",
                            "selected_models", "outputs")
        if _revision_value(before, field) == _revision_value(after, field)
    ]
    return {"changed": changed, "added": added, "removed": removed, "preserved": preserved}


def revision_summary_text(summary):
    """Plain-text status for a successful revision; it contains no new scientific claim."""
    if not summary:
        return "The research plan was revised. Review the updated plan before continuing."
    changes = []
    for group in ("changed", "added", "removed"):
        for item in summary.get(group) or []:
            if group == "changed":
                changes.append(
                    "%s: %s -> %s" % (
                        item.get("field"), _revision_value_text(item.get("from")),
                        _revision_value_text(item.get("to")),
                    )
                )
            else:
                value = item.get("to") if group == "added" else item.get("from")
                changes.append("%s %s: %s" % (group[:-1], item.get("field"), _revision_value_text(value)))
    changed_text = "; ".join(changes) if changes else "no physical fields changed"
    preserved = ", ".join(summary.get("preserved") or []) or "none"
    invalidated = ", ".join(summary.get("invalidated") or []) or "none"
    return (
        "Plan revised from v%03d to v%03d. Changes: %s. Preserved: %s. "
        "Cleared: %s. Validation passed. Review the updated plan before approving it again."
        % (
            summary.get("from_version", 0), summary.get("to_version", 0),
            changed_text, preserved, invalidated,
        )
    )


def revise(session, changes=None, note=""):
    project = _require(session)
    changes = dict(changes or {})
    before_plan = copy.deepcopy(project["plan"])
    before_plan.pop("revision_summary", None)
    plan = copy.deepcopy(project["plan"])
    plan.pop("revision_summary", None)
    known_fields = {
        "objective", "hypothesis", "steps", "charts", "runs", "parameters",
        "paper_conditions", "condition_provenance",
        "literature_evidence", "reproduction_targets", "selected_models",
        "parameter_mapping", "outputs",
        "quantities", "controls", "metrics", "diagnostics", "success_criteria",
        "stop_conditions", "assumptions", "limitations", "baseline_run_id",
    }
    # Apply revisions to a copy. A provider can submit valid chart changes together with
    # invalid runs; mutating the live plan before run validation leaves a half-revised
    # package whose selected chart IDs no longer exist and causes a figure-gate loop.
    for key in ("objective", "hypothesis"):
        if key in changes and changes[key] is not None:
            plan[key] = str(changes[key]).strip()
            if key == "objective":
                plan["title"] = plan[key]
    if isinstance(changes.get("parameters"), dict):
        plan.setdefault("parameters", {}).update(changes["parameters"])
    if isinstance(changes.get("paper_conditions"), dict):
        plan["paper_conditions"] = dict(changes["paper_conditions"])
    if isinstance(changes.get("condition_provenance"), dict):
        plan["condition_provenance"] = dict(changes["condition_provenance"])
    if "literature_evidence" in changes:
        plan["literature_evidence"] = _clean_literature_evidence(changes.get("literature_evidence"))
    if "reproduction_targets" in changes:
        plan["reproduction_targets"] = _clean_reproduction_targets(changes.get("reproduction_targets"))
    if "selected_models" in changes:
        plan["selected_models"] = _clean_selected_models(
            changes.get("selected_models"), plan.get("runs"), derive=False
        )
    if "parameter_mapping" in changes:
        plan["parameter_mapping"] = _clean_parameter_mapping(changes.get("parameter_mapping"))
    if "outputs" in changes:
        plan["outputs"] = _clean_outputs(changes.get("outputs"))
    # Also accept parameter keys directly for concise model tool calls. Explicit plan
    # fields remain reserved, so they cannot be confused with model parameters.
    for key, value in changes.items():
        if key not in known_fields and key not in {"note", "reason"}:
            plan.setdefault("parameters", {})[key] = value
    if "steps" in changes and changes["steps"] is not None:
        plan["steps"] = _clean_list(changes["steps"])
    if "charts" in changes and changes["charts"] is not None:
        charts = _clean_charts(changes["charts"])
        if not charts:
            raise ValueError("A revised plan requires at least one chart option.")
        plan["charts"] = charts
    if "runs" in changes and changes["runs"] is not None:
        runs, problems, repairs, resolutions, problem_details = _clean_runs(changes["runs"])
        if problems or not runs:
            return _fail(
                "Invalid revised runs: %s" % "; ".join(problems or ["none supplied"]),
                {
                    "error_code": "run_validation",
                    "problems": problem_details,
                    "repair_hints": [item.get("repair") for item in problem_details if item.get("repair")],
                },
            )
        plan["runs"] = runs
        plan["parameter_resolution"] = resolutions
        if repairs:
            plan.setdefault("automatic_repairs", []).extend(
                {"run_id": repair.get("run_id"), **{k: v for k, v in repair.items() if k != "run_id"}}
                for repair in repairs
            )
    for key in ("quantities", "controls", "metrics", "diagnostics", "success_criteria", "stop_conditions", "assumptions", "limitations"):
        if key in changes and changes[key] is not None:
            plan[key] = _clean_list(changes[key], 12)
    if "baseline_run_id" in changes and changes["baseline_run_id"] is not None:
        wanted = str(changes["baseline_run_id"]).strip()
        if wanted not in [run["id"] for run in plan.get("runs") or []]:
            raise ValueError("baseline_run_id must name a planned run")
        plan["baseline_run_id"] = wanted
    chart_problems = _validate_chart_runs(plan.get("charts") or [], plan.get("runs") or [])
    if chart_problems:
        raise ValueError(
            "The revised chart cannot be produced by the planned runs: %s"
            % "; ".join(chart_problems)
        )
    if not plan.get("objective") or not plan.get("hypothesis"):
        raise ValueError("A revised plan must keep both an objective and a hypothesis.")
    if not plan.get("steps") or len(plan["steps"]) < 3:
        raise ValueError("A revised plan requires at least three executable research steps.")
    plan["literature_evidence"] = _clean_literature_evidence(plan.get("literature_evidence"))
    plan["reproduction_targets"] = _clean_reproduction_targets(plan.get("reproduction_targets"))
    plan["selected_models"] = _enrich_selected_models(
        session,
        _clean_selected_models(plan.get("selected_models"), plan.get("runs"), derive=False),
    )
    plan["parameter_mapping"] = _clean_parameter_mapping(plan.get("parameter_mapping"))
    plan["outputs"] = _clean_outputs(plan.get("outputs"))
    (
        plan["literature_evidence"],
        plan["reproduction_targets"],
        plan["selected_models"],
        plan["parameter_mapping"],
        plan["outputs"],
        plan["paper_conditions"],
        plan["condition_provenance"],
        metadata_repairs,
        metadata_problems,
        context_warnings,
    ) = _repair_reproduction_metadata(
        session,
        plan.get("question", project.get("question", "")),
        plan.get("literature_evidence"),
        plan.get("reproduction_targets"),
        plan.get("selected_models"),
        plan.get("parameter_mapping"),
        plan.get("outputs"),
        plan.get("runs") or [],
        plan.get("charts") or [],
        plan.get("paper_conditions") or {},
        plan.get("condition_provenance") or {},
        plan.get("parameter_resolution") or [],
    )
    # An explicit user deletion is different from an omitted field in an LLM
    # proposal.  Preserve the review contract: a user cannot approve a revision
    # after intentionally deleting every mapping; ask them to restore the metadata.
    if "parameter_mapping" in changes and not changes.get("parameter_mapping") and is_reproduction_question(plan.get("question", project.get("question", "")), session):
        plan["parameter_mapping"] = []
        metadata_repairs = [
            item for item in metadata_repairs
            if not str(item.get("field", "")).startswith("parameter_mapping")
        ]
        metadata_problems.append({
            "field": "parameter_mapping",
            "source": "user revision",
            "expected": "one auditable mapping for every resolved run input",
            "repair": "Restore the mappings or revise individual entries without deleting the complete mapping set.",
            "provenance": "user_specified",
            "blocking": True,
        })
    _mark_user_revised_inputs(plan, before_plan, changes)
    plan.setdefault("automatic_repairs", []).extend(metadata_repairs)
    evidence_problems = _evidence_plan_problems(
        session,
        plan.get("question", project.get("question", "")),
        plan.get("literature_evidence"),
        plan.get("reproduction_targets"),
        plan.get("selected_models"),
        plan.get("parameter_mapping"),
        plan.get("outputs"),
        plan.get("runs") or [],
        plan.get("charts") or [],
        plan.get("parameter_resolution") or [],
    )
    blocking_metadata_problems = [
        item for item in metadata_problems
        if item.get("blocking", True)
        and not _is_paper_context_problem(item)
    ]
    evidence_problems.extend(blocking_metadata_problems)
    nonblocking_evidence_warnings = [
        item for item in evidence_problems if not item.get("blocking", True)
    ]
    if evidence_problems and any(item.get("blocking", True) for item in evidence_problems):
        return _fail(
            _evidence_problem_summary(
                plan.get("question", project.get("question", "")),
                [item for item in evidence_problems if item.get("blocking", True)],
            ),
            {
                "error_code": "reproduction_evidence_incomplete",
                "stage": "reproduction_metadata",
                "problem_count": sum(1 for item in evidence_problems if item.get("blocking", True)),
                "automatic_repairs": metadata_repairs,
                "problems": evidence_problems,
                "repair_hints": [item.get("repair") for item in evidence_problems if item.get("repair")],
            },
        )
    targets = plan.get("reproduction_targets") or []
    coverage_problems, linked_runs, linked_charts = _target_coverage(
        targets, plan.get("runs") or [], plan.get("charts") or []
    )
    if not coverage_problems:
        for run in plan.get("runs") or []:
            run["target_ids"] = sorted(
                set(run.get("target_ids") or ()) | set(linked_runs.get(run.get("id")) or ())
            )
        for chart in plan.get("charts") or []:
            chart["target_ids"] = sorted(
                set(chart.get("target_ids") or ()) | set(linked_charts.get(chart.get("id")) or ())
            )
    project["plan_version"] += 1
    project["plan"] = plan
    project["plan"]["plan_version"] = project["plan_version"]
    project["plan"]["approval_state"] = "plan_review"
    project["review_log"].append(
        {
            "version": project["plan_version"],
            "note": note or changes.get("reason") or "user-requested revision",
            "changes": changes,
        }
    )
    project["phase"] = "plan_review"
    plan["validation_warnings"] = list(context_warnings) + nonblocking_evidence_warnings
    project["selected_chart"] = None
    project["selected_charts"] = []
    project["pseudo"] = None
    project["plan_card_expanded"] = False
    project["execution_resume_sent"] = False
    _clear_previews(session)
    summary = _revision_diff(before_plan, plan, changes)
    summary.update(
        {
            "from_version": project["plan_version"] - 1,
            "to_version": project["plan_version"],
            "invalidated": ["pseudo_preview", "chart_selection", "execution_approval"],
            "validation": "passed",
            "next_phase": "plan_review",
        }
    )
    plan["revision_summary"] = summary
    project["revision_summary"] = summary
    return _needs(revision_summary_text(summary), {**_public(project), "revision_summary": summary})


def revise_after_figure_quality(session, chart_id, issues=None):
    """Prepare a scientifically reviewable revision instead of terminating on Figure QA."""
    project = _require(session)
    plan = project["plan"]
    issues = list(issues or [])
    audit.emit(
        "figure_qa_repair_started",
        session=session,
        chart_id=chart_id,
        issues=issues,
    )
    chart = next((item for item in plan.get("charts") or [] if item.get("id") == chart_id), None)
    if chart is None:
        return _fail("Cannot revise unknown chart %r after Figure QA." % chart_id)
    repairs = []
    coefficient_outputs = {
        "ks_per_m", "ka_per_m", "effective_permittivity", "single_scattering_albedo"
    }
    coefficient_solver_axis = (
        chart.get("x") == "dort_streams"
        and bool(coefficient_outputs.intersection(_chart_y_names(chart)))
    )
    abrupt_jump = any("abrupt adjacent jump" in str(issue) for issue in issues)
    under_sampled = any(
        phrase in str(issue)
        for issue in issues
        for phrase in ("has only", "too few distinct x values")
    )
    for run in plan.get("runs") or []:
        if not _run_produces_chart(run, chart):
            continue
        spec = run.get("parameters") or {}
        old_points = int(spec.get("sweep_points") or 0)
        if abrupt_jump and old_points < 40:
            new_points = min(40, max(20, old_points * 2))
            spec["sweep_points"] = new_points
            repairs.append(
                {
                    "run_id": run.get("id"),
                    "field": "sweep_points",
                    "from": old_points,
                    "to": new_points,
                    "reason": "refine the grid around a possible numerical discontinuity",
                }
            )
        elif (under_sampled or old_points < 8) and old_points < 20:
            new_points = max(10, min(20, max(old_points * 2, 10)))
            spec["sweep_points"] = new_points
            repairs.append(
                {
                    "run_id": run.get("id"),
                    "field": "sweep_points",
                    "from": old_points,
                    "to": new_points,
                    "reason": "increase resolution after figure-quality review",
                }
            )
        if coefficient_solver_axis and spec.get("output") == "coefficients":
            entry = registry.get(run.get("model"))
            density = ((entry.card.get("parameters") or {}).get("density_kg_m3") or {}) if entry else {}
            centre = float(spec.get("density_kg_m3") or density.get("default") or 300.0)
            start = max(float(density.get("minimum", 1.0)), centre - 200.0)
            stop = min(float(density.get("maximum", 917.0)), centre + 200.0)
            old_axis = spec.get("sweep_parameter")
            spec.update(
                sweep_parameter="density_kg_m3",
                sweep_start=start,
                sweep_stop=stop,
                sweep_points=10,
            )
            repairs.append(
                {
                    "run_id": run.get("id"), "field": "sweep_parameter",
                    "from": old_axis, "to": "density_kg_m3",
                    "reason": "electromagnetic coefficients are independent of DORT streams",
                }
            )
    if coefficient_solver_axis:
        chart["x"] = "density_kg_m3"
        chart["x_label"] = ""
        repairs.append(
            {
                "chart_id": chart_id, "field": "x", "from": "dort_streams",
                "to": "density_kg_m3",
            }
        )
    if not repairs:
        only_persistent_jumps = bool(issues) and all(
            "abrupt adjacent jump" in str(issue) for issue in issues
        )
        matching_figure = next(
            (
                figure for figure in reversed(session.get("figures") or [])
                if not figure.get("preview")
                and figure.get("planned_chart_id") == chart_id
            ),
            None,
        )
        if only_persistent_jumps and matching_figure is not None:
            review = dict(matching_figure.get("quality_review") or {})
            review.update(
                reviewed=True,
                passed=True,
                passed_with_warning=True,
                scientific_anomaly=True,
                issues=[],
                warnings=list(dict.fromkeys((review.get("warnings") or []) + issues)),
            )
            matching_figure["quality_review"] = review
            anomaly = {
                "chart_id": chart_id,
                "kind": "persistent_discontinuity",
                "issues": issues,
                "sampling_points": max(
                    [
                        int((run.get("parameters") or {}).get("sweep_points") or 0)
                        for run in plan.get("runs") or []
                        if _run_produces_chart(run, chart)
                    ]
                    or [0]
                ),
                "interpretation_constraint": (
                    "Treat the persistent jump as a model-validity or numerical diagnostic, "
                    "not as a verified physical transition; report it explicitly."
                ),
            }
            project.setdefault("scientific_anomalies", []).append(anomaly)
            limitation = anomaly["interpretation_constraint"]
            if limitation not in plan.setdefault("limitations", []):
                plan["limitations"].append(limitation)
            project["qa_recovery"] = {
                **anomaly,
                "status": "accepted_with_scientific_warning",
                "automatic_attempts": int(
                    (project.get("qa_recovery") or {}).get("automatic_attempts", 0)
                ),
            }
            session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1
            audit.emit(
                "figure_qa_persistent_anomaly",
                session=session,
                level="WARNING",
                anomaly=anomaly,
            )
            return _ok(
                "Figure QA found a persistent discontinuity after maximum safe grid refinement. "
                "The Figure is retained as a qualified scientific diagnostic; the report must "
                "describe the discontinuity and may not call it a verified physical threshold.",
                {
                    **_public(project),
                    "next": "continue_with_qualified_figure",
                    "scientific_anomaly": anomaly,
                },
            )
        project["qa_recovery"] = {
            "chart_id": chart_id,
            "issues": issues,
            "status": "unresolved",
            "automatic_attempts": int((project.get("qa_recovery") or {}).get("automatic_attempts", 0)),
        }
        summary = (
            "Figure QA remains unresolved after safe automatic repair was exhausted for %s: %s. "
            "Execution is paused without reopening or regenerating the research plan."
            % (chart_id, "; ".join(issues) or "unspecified quality failure")
        )
        audit.emit(
            "figure_qa_repair_exhausted",
            session=session,
            level="WARNING",
            chart_id=chart_id,
            issues=issues,
        )
        return _fail(
            summary,
            {
                "error_code": "figure_quality_unresolved",
                "chart_id": chart_id,
                "issues": issues,
                "requires_user_revision": True,
            },
        )
    project["plan_version"] += 1
    plan["plan_version"] = project["plan_version"]
    project["execution_resume_sent"] = False
    plan.setdefault("automatic_repairs", []).extend(repairs)
    requires_human_review = coefficient_solver_axis
    project["review_log"].append(
        {
            "version": project["plan_version"],
            "note": (
                "automatic scientific-axis revision after Figure QA"
                if requires_human_review
                else "automatic in-plan sampling repair after Figure QA"
            ),
            "changes": {"chart_id": chart_id, "repairs": repairs, "issues": issues},
        }
    )
    affected_run_ids = sorted({item.get("run_id") for item in repairs if item.get("run_id")})
    previous_attempts = int((project.get("qa_recovery") or {}).get("automatic_attempts", 0))
    project["qa_recovery"] = {
        "chart_id": chart_id,
        "issues": issues,
        "repairs": repairs,
        "affected_run_ids": affected_run_ids,
        "automatic_attempts": previous_attempts + (0 if requires_human_review else 1),
        "status": "awaiting_human_review" if requires_human_review else "rerun_required",
    }
    project["pseudo"] = None
    # Any formal figure can contain a repaired run, so withdraw the package and recreate
    # it from the denser outputs. Old successful handles remain as provenance but no longer
    # match the revised exact run specification and therefore cannot satisfy execution_gaps.
    session["figures"] = []
    session["failed_runs"] = [
        item for item in session.get("failed_runs") or []
        if item.get("run_id") not in affected_run_ids
    ]
    session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1
    if requires_human_review:
        project["phase"] = "plan_review"
        project["selected_chart"] = None
        project["selected_charts"] = []
        summary = (
            "Figure QA generated plan v%03d with %d scientific-axis repair(s). Human review "
            "is required because the independent variable changed."
            % (project["plan_version"], len(repairs))
        )
        audit.emit(
            "figure_qa_scientific_revision_required",
            session=session,
            level="WARNING",
            chart_id=chart_id,
            repairs=repairs,
        )
        return _needs(summary, _public(project))

    # Increasing resolution does not alter the approved question, controls, model, range,
    # or output. Keep formal execution approved and let the agent rerun only changed specs.
    project["phase"] = "approved"
    summary = (
        "Figure QA applied %d safe sampling repair(s) in plan v%03d. Formal execution remains "
        "approved; rerun affected run IDs and regenerate/review the selected figure package."
        % (len(repairs), project["plan_version"])
    )
    audit.emit(
        "figure_qa_auto_repair_applied",
        session=session,
        chart_id=chart_id,
        repairs=repairs,
        affected_run_ids=affected_run_ids,
    )
    return _ok(
        summary,
        {
            **_public(project),
            "next": "rerun_repaired_runs",
            "affected_run_ids": affected_run_ids,
            "repairs": repairs,
        },
    )


def revise_after_run_failures(session, failures):
    """Create a reviewable recovery plan instead of retrying a broken run forever.

    The SMRT adapter exhausts numerical DORT alternatives first. Reaching this function
    means the next remedy changes the physical experiment, so it becomes a new plan version
    and cannot execute until the user reviews it again.
    """
    project = _require(session)
    plan = project["plan"]
    failures = list(failures or [])
    repairs = []
    recovery_rounds = sum(
        1 for item in project.get("review_log") or []
        if item.get("note") == "automatic recovery proposal after model failure"
    )

    if recovery_rounds < 2:
        unstable = [
            item for item in failures
            if item.get("error_code") == "dort_diagonalization" and item.get("recoverable")
        ]
        affected_radii = {
            (item.get("spec") or {}).get("radius_m")
            for item in unstable
            if isinstance((item.get("spec") or {}).get("radius_m"), (int, float))
        }
        for old_radius in sorted(affected_radii):
            new_radius = max(1.0e-6, float(old_radius) * 0.8)
            if new_radius == old_radius:
                continue
            # Keep the controlled comparison consistent: all sticky-sphere runs that
            # shared the failed radius receive the same proposed radius.
            for run in plan.get("runs") or []:
                spec = run.get("parameters") or {}
                if (
                    run.get("model") == "smrt"
                    and spec.get("microstructure_model") == "sticky_hard_spheres"
                    and spec.get("radius_m") == old_radius
                ):
                    spec["radius_m"] = new_radius
                    repairs.append(
                        {
                            "run_id": run.get("id"),
                            "field": "radius_m",
                            "from": old_radius,
                            "to": new_radius,
                            "reason": (
                                "DORT remained unstable after all numerical fallbacks; "
                                "a smaller sphere radius is proposed across the whole comparison"
                            ),
                        }
                    )
            if plan.get("parameters", {}).get("radius_m") == old_radius:
                plan["parameters"]["radius_m"] = new_radius

    project["plan_version"] += 1
    plan["plan_version"] = project["plan_version"]
    if repairs:
        plan.setdefault("automatic_repairs", []).extend(repairs)
        note = "automatic recovery proposal after model failure"
        summary = (
            "Model failure generated plan v%03d with %d controlled repair(s). "
            "Human review is required before rerunning."
            % (project["plan_version"], len(repairs))
        )
    else:
        note = "model failure requires a user-selected recovery"
        limitation = (
            "Execution failed after numerical recovery; choose a revised physical range "
            "or parameter set before continuing."
        )
        if limitation not in plan.setdefault("limitations", []):
            plan["limitations"].append(limitation)
        summary = (
            "Model failure reopened plan v%03d. No safe automatic physical repair remains; "
            "review the failure and revise the plan before rerunning."
            % project["plan_version"]
        )
    project.setdefault("review_log", []).append(
        {
            "version": project["plan_version"],
            "note": note,
            "changes": {
                "failed_run_ids": [item.get("run_id") for item in failures],
                "repairs": repairs,
                "errors": [item.get("error") for item in failures],
            },
        }
    )
    project["recovery"] = {
        "failed_run_ids": [item.get("run_id") for item in failures],
        "repairs": repairs,
        "requires_human_review": True,
    }
    project["phase"] = "plan_review"
    project["selected_chart"] = None
    project["selected_charts"] = []
    project["pseudo"] = None
    project["execution_resume_sent"] = False
    session["figures"] = []
    session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1
    return _needs(summary, _public(project))


def approve_plan(session):
    project = _require(session)
    if project["phase"] != "plan_review":
        return _fail("The plan cannot be approved in phase %s." % project["phase"])
    resource_gate = (project.get("plan") or {}).get("resource_gate")
    if resource_gate:
        return _needs(
            "The plan is structurally valid but cannot be approved until its research guideline, model instructions, and required paper evidence are read.",
            {**_public(project), "resource_gate": resource_gate},
        )
    project["phase"] = "plan_approved"
    return _needs(
        "Plan approved for preview only. No physical model run or scientific figure is approved yet; generate the display-only pseudo-data preview next.",
        _public(project),
    )


def pseudo_preview(session):
    """Generate deterministic display-only data from the proposed axes, never physics."""
    project = _require(session)
    if project["phase"] not in ("plan_approved", "pseudo_preview"):
        return _needs("Approve the plan before requesting pseudo-data.", _public(project))
    plan = project["plan"]
    project["preview_version"] = int(project.get("preview_version", 0)) + 1
    preview_version = project["preview_version"]
    preview_layouts = {}
    # Replace this project's old previews rather than accumulating stale layouts.  These
    # curves are deliberately tagged and labelled as pseudo-data; completion never counts
    # them because they contain no real result handles.
    session["figures"] = [figure for figure in session.get("figures") or [] if not figure.get("research_preview")]
    chart_axes = {chart["x"] for chart in plan["charts"]}
    for chart_index, chart in enumerate(plan["charts"]):
        producers = [run for run in plan["runs"] if _run_produces_chart(run, chart)]
        source_spec = (producers[0].get("parameters") or {}) if producers else {}
        plan_parameters = plan.get("parameters") or {}
        proposed_bounds = _preview_bounds_or_none(
            plan_parameters,
            [chart],
            allow_generic=(
                len(chart_axes) == 1
                or plan_parameters.get("sweep_parameter") == chart["x"]
            ),
        )
        if proposed_bounds is not None:
            start, stop = proposed_bounds
            count = int((plan.get("parameters") or {}).get("sweep_points", 8) or 8)
        elif source_spec.get("sweep_parameter") == chart["x"]:
            start = float(source_spec["sweep_start"])
            stop = float(source_spec["sweep_stop"])
            count = int(source_spec.get("sweep_points") or 8)
        else:
            start, stop = _preview_bounds(plan.get("parameters") or {}, [chart])
            count = int((plan.get("parameters") or {}).get("sweep_points", 8) or 8)
        count = max(5, min(20, count))
        xs = [start + (stop - start) * index / (count - 1) for index in range(count)]
        preview_series = []
        for producer_index, run in enumerate(producers or [{"id": "layout", "label": chart["label"]}]):
            for y_index, y_name in enumerate(_chart_y_names(chart)):
                if producers and not _run_produces_chart(run, chart, y_name):
                    continue
                ys = []
                for index in range(count):
                    fraction = index / max(1, count - 1)
                    ys.append(
                        round(
                            0.2 + 0.55 * fraction
                            + 0.11 * producer_index + 0.07 * y_index
                            + 0.025 * math.sin(index + preview_version + chart_index),
                            8,
                        )
                    )
                preview_series.append(
                    {
                        "handle": "",
                        "label": "%s · %s" % (run.get("label"), y_name),
                        "x": xs,
                        "y": ys,
                        "x_name": chart["x"],
                        "y_name": y_name,
                        "source": "model_run",
                        "origin": "pseudo-data preview v%03d" % preview_version,
                        "units": {},
                    }
                )
        preview_layouts[chart["id"]] = preview_series
        figure = plotting.render(
            {
                "title": "%s — PSEUDO-DATA PREVIEW" % chart["label"],
                "kind": chart["kind"],
                "x_label": chart.get("x_label") or None,
                "y_label": chart.get("y_label") or None,
            },
            preview_series,
            preview=False,
        )
        figure["preview"] = True
        figure["research_preview"] = True
        session["figures"].append(figure)
    first_series = next(iter(preview_layouts.values()), [])
    points = []
    if first_series:
        for index, x_value in enumerate(first_series[0]["x"]):
            row = {first_series[0]["x_name"]: round(x_value, 8)}
            for series_index, item in enumerate(first_series):
                row["%s_%s" % (series_index + 1, item["y_name"])] = item["y"][index]
            points.append(row)
    project["pseudo"] = {
        "label": "PSEUDO-DATA - layout demonstration only - preview v%03d" % preview_version,
        "points": points,
    }
    session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1
    project["phase"] = "pseudo_preview"
    required_ids = [chart["id"] for chart in plan["charts"] if chart.get("required", True)]
    project["selected_charts"] = required_ids
    project["selected_chart"] = next(
        (dict(chart) for chart in plan["charts"] if chart["id"] in required_ids),
        None,
    )
    return _needs(
        "Pseudo-data preview v%03d is ready for layout review only. It is not model output and must not support a scientific conclusion. Confirm the figure package, or revise the plan in chat."
        % preview_version,
        _public(project),
    )


def _preview_bounds(parameters, charts):
    """Read common generic range forms without embedding any domain/question template."""
    return _preview_bounds_or_none(parameters, charts) or (0.0, 1.0)


def _preview_bounds_or_none(parameters, charts, allow_generic=True):
    """Return a declared range for these chart axes, or ``None`` when none exists."""
    if allow_generic and "sweep_start" in parameters and "sweep_stop" in parameters:
        return float(parameters["sweep_start"]), float(parameters["sweep_stop"])
    x_names = [str(chart.get("x") or "").lower() for chart in charts]
    x_roots = {name.split("_")[0] for name in x_names if name}
    candidates = []
    for key, value in parameters.items():
        normalized = str(key).lower()
        if "range" in normalized or any(root and root in normalized for root in x_roots):
            candidates.append(value)
    for value in candidates:
        if isinstance(value, dict) and "start" in value and "end" in value:
            try:
                return float(value["start"]), float(value["end"])
            except (TypeError, ValueError):
                pass
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            try:
                return float(value[0]), float(value[1])
            except (TypeError, ValueError):
                pass
        numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", str(value))
        if len(numbers) >= 2:
            return float(numbers[0]), float(numbers[1])
    return None


def choose_chart(session, chart_id):
    project = _require(session)
    if project["phase"] != "pseudo_preview":
        return _needs("Generate the pseudo-data preview before selecting a chart.", _public(project))
    chart = next((item for item in project["plan"]["charts"] if item["id"] == chart_id), None)
    if chart is None:
        return _fail("Unknown chart option %r." % chart_id)
    selected = list(project.get("selected_charts") or [])
    if chart.get("required", True):
        if chart_id not in selected:
            selected.append(chart_id)
        action = "kept required"
    elif chart_id in selected:
        selected.remove(chart_id)
        action = "deselected"
    else:
        selected.append(chart_id)
        action = "selected"
    project["selected_charts"] = selected
    project["selected_chart"] = next(
        (dict(item) for item in project["plan"]["charts"] if item["id"] in selected),
        None,
    )
    project["review_log"].append(
        {
            "version": project["plan_version"],
            "note": "user %s chart %s" % (action, chart_id),
            "changes": {"selected_charts": list(selected)},
        }
    )
    if chart.get("required", True):
        project["phase"] = "chart_selected"
        _clear_previews(session)
        return _needs(
            "%d required chart(s) confirmed. The pseudo-data preview was discarded; ask the user to approve formal execution of the real runs."
            % len(project["selected_charts"]),
            _public(project),
        )
    return _needs(
        "Chart package updated. Confirm the selected figure set before formal execution.",
        _public(project),
    )


def confirm_charts(session):
    project = _require(session)
    if project["phase"] != "pseudo_preview":
        return _needs("Generate the pseudo-data preview before confirming charts.", _public(project))
    if not project.get("selected_charts"):
        return _needs("Select at least one chart before continuing.", _public(project))
    project["phase"] = "chart_selected"
    _clear_previews(session)
    return _needs(
        "%d chart(s) confirmed. The pseudo-data preview was discarded; ask the user to approve formal execution."
        % len(project["selected_charts"]),
        _public(project),
    )


def approve_execution(session):
    project = _require(session)
    if project["phase"] in ("approved", "completed"):
        return _ok(
            "Formal execution was already approved for the current plan; no second model continuation was scheduled.",
            _public(project),
        )
    if project["phase"] != "chart_selected":
        return _needs("Select a chart after the pseudo-data preview first.", _public(project))
    project["phase"] = "approved"
    project["execution_resume_sent"] = False
    _clear_previews(session)
    return _ok(
        "Formal execution approved. The agent may now call the registered physical models and must build the selected figures from their real outputs.",
        _public(project),
    )


def _clear_previews(session):
    """Remove demonstration figures as soon as the human confirms the figure package."""
    before = len(session.get("figures") or [])
    session["figures"] = [
        figure for figure in session.get("figures") or []
        if not figure.get("research_preview") and not figure.get("preview")
    ]
    if len(session["figures"]) != before:
        session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1


def complete(session):
    project = _require(session)
    gaps = execution_gaps(session)
    if gaps["missing_runs"]:
        return _needs(
            "The workflow cannot complete; planned runs still missing: %s."
            % ", ".join(gaps["missing_runs"]),
            _public(project),
        )
    if gaps.get("target_gaps"):
        return _needs(
            "The workflow cannot complete; reproduction targets still lack covered planned runs or reviewed charts: %s."
            % ", ".join(item.get("target_id") or "target" for item in gaps["target_gaps"]),
            _public(project),
        )
    if gaps["figure_problem"]:
        return _needs(
            gaps["figure_problem"],
            _public(project),
        )
    project["phase"] = "completed"
    scope = project.get("plan", {}).get("outcome_scope", "full")
    return _ok("Research workflow completed as %s." % scope, _public(project))


def execution_gaps(session):
    """Return unmet approved-plan outputs; failed or duplicate runs never count."""
    project = session.get("research") or {}
    planned = (project.get("plan") or {}).get("runs") or []
    successful = session.get("successful_runs") or []
    failed = session.get("failed_runs") or []
    matched = []
    matched_success_indexes = set()
    matched_runs = []
    missing = []
    missing_ids = []
    current_failures = []
    for wanted in planned:
        candidates = [
            (index, actual)
            for index, actual in enumerate(successful)
            if index not in matched_success_indexes
            and actual.get("model") == wanted.get("model")
            and all(
                actual.get("spec", {}).get(key) == value
                for key, value in wanted.get("parameters", {}).items()
            )
        ]
        # Prefer the explicit plan association written by run_planned_model.  The fallback
        # keeps older sessions and direct test fixtures compatible.
        exact = [item for item in candidates if item[1].get("planned_run_id") == wanted.get("id")]
        selected = (exact or candidates)
        found_index, found = selected[0] if selected else (None, None)
        if found:
            matched_success_indexes.add(found_index)
            matched.append(found.get("handle"))
            matched_runs.append(
                {
                    "run_id": wanted.get("id"),
                    "label": wanted.get("label") or wanted.get("id") or wanted.get("model"),
                    "handle": found.get("handle"),
                    "run": wanted,
                }
            )
        else:
            missing.append(wanted.get("label") or wanted.get("id") or wanted.get("model"))
            missing_ids.append(wanted.get("id"))
            current_failures.extend(
                item for item in failed
                if item.get("run_id") == wanted.get("id")
                and item.get("spec") == wanted.get("parameters")
            )
    figures = [figure for figure in session.get("figures") or [] if not figure.get("preview")]
    charts = (project.get("plan") or {}).get("charts") or []
    selected_ids = list(project.get("selected_charts") or [])
    if not selected_ids and project.get("selected_chart"):
        selected_ids = [project["selected_chart"].get("id")]
    selected_charts = [chart for chart in charts if chart.get("id") in selected_ids]
    chart_requirements = []
    missing_charts = []
    unreviewed_charts = []
    failed_reviews = []
    for chart in selected_charts:
        expected = []
        for item in matched_runs:
            for y_name in _chart_y_names(chart):
                if _run_produces_chart(item["run"], chart, y_name):
                    series = {
                        "run_id": item["run_id"],
                        "label": "%s · %s" % (item["label"], y_name),
                        "handle": item["handle"],
                        "x": chart.get("x"),
                        "y": y_name,
                    }
                    # Two plan roles may intentionally share one cached physical run (for
                    # example a separately named validation baseline).  It satisfies both
                    # run IDs but should appear only once in the figure.
                    if not any(
                        row["handle"] == series["handle"]
                        and row["x"] == series["x"]
                        and row["y"] == series["y"]
                        for row in expected
                    ):
                        expected.append(series)
        requirement = {"chart": chart, "series": expected}
        chart_requirements.append(requirement)
        matching_figure = next(
            (figure for figure in figures if _figure_satisfies(figure, expected)),
            None,
        )
        if matching_figure is None:
            missing_charts.append(requirement)
        elif matching_figure.get("planned_chart_id"):
            review = matching_figure.get("quality_review") or {}
            if not review.get("reviewed"):
                unreviewed_charts.append(requirement)
            elif not review.get("passed"):
                failed_reviews.append(
                    {
                        "requirement": requirement,
                        "issues": review.get("issues") or ["unspecified figure-quality failure"],
                    }
                )
    first_missing = missing_charts[0] if missing_charts else None
    focus = first_missing or (chart_requirements[0] if chart_requirements else {"chart": {}, "series": []})
    expected_series = focus["series"]
    expected_handles = [item["handle"] for item in expected_series if item.get("handle")]
    missing_figure_series = (
        [item for item in expected_series if not any(_figure_has_series(figure, item) for figure in figures)]
        if first_missing else []
    )
    figure_problem = ""
    if not selected_charts:
        figure_problem = "The workflow cannot complete before a planned chart package is selected."
    elif not figures:
        figure_problem = "The workflow cannot complete before actual model outputs are plotted."
    elif missing_charts:
        figure_problem = (
            "Required planned chart(s) are missing or incomplete: %s."
            % ", ".join(
                "%s [%s]"
                % (
                    item["chart"].get("id"),
                    ", ".join(
                        "%s=%s" % (series["run_id"], series["handle"])
                        for series in item["series"]
                    ),
                )
                for item in missing_charts
            )
        )
    elif unreviewed_charts:
        figure_problem = (
            "Formal figure quality review is still required for: %s."
            % ", ".join(item["chart"].get("id") for item in unreviewed_charts)
        )
    elif failed_reviews:
        figure_problem = (
            "Formal figure quality review failed for %s: %s."
            % (
                failed_reviews[0]["requirement"]["chart"].get("id"),
                "; ".join(failed_reviews[0]["issues"]),
            )
            )
    target_statuses = []
    for target in (project.get("plan") or {}).get("reproduction_targets") or []:
        run_ids = set(target.get("run_ids") or ())
        chart_ids = set(target.get("chart_ids") or ())
        matched_ids = {item.get("run_id") for item in matched_runs}
        complete_by_run = bool(run_ids) and run_ids.issubset(matched_ids)
        complete_by_chart = bool(chart_ids) and not (
            chart_ids
            & (
                set(item["chart"].get("id") for item in missing_charts)
                | set(item["chart"].get("id") for item in unreviewed_charts)
                | set(item["requirement"]["chart"].get("id") for item in failed_reviews)
            )
        ) and chart_ids.issubset(set(item.get("id") for item in selected_charts))
        target_status = target.get("status") if target.get("status") in ("partial", "unavailable") else (
            "covered" if complete_by_run or complete_by_chart else "pending"
        )
        target_statuses.append(
            {
                "target_id": target.get("id"),
                "source_type": target.get("source_type"),
                "source_id": target.get("source_id"),
                "run_ids": sorted(run_ids),
                "chart_ids": sorted(chart_ids),
                "status": target_status,
            }
        )
    return {
        "missing_runs": missing,
        "missing_run_ids": missing_ids,
        "failed_runs": current_failures,
        "failed_run_ids": sorted(
            {item.get("run_id") for item in current_failures if item.get("run_id")}
        ),
        "matched_handles": matched,
        "matched_runs": matched_runs,
        "expected_figure_handles": expected_handles,
        "expected_figure_series": expected_series,
        "missing_figure_series": missing_figure_series,
        "selected_chart": focus["chart"],
        "selected_charts": selected_charts,
        "chart_requirements": chart_requirements,
        "missing_chart_ids": [item["chart"].get("id") for item in missing_charts],
        "unreviewed_chart_ids": [item["chart"].get("id") for item in unreviewed_charts],
        "failed_figure_reviews": failed_reviews,
        "figure_problem": figure_problem,
        "reproduction_targets": target_statuses,
        "target_gaps": [item for item in target_statuses if item["status"] == "pending"],
    }


def _figure_satisfies(figure, expected):
    """A planned chart is one figure containing every exact handle/x/y series."""
    return bool(expected) and all(
        _figure_has_series(figure, wanted)
        for wanted in expected
    )


def _figure_has_series(figure, wanted):
    return any(
        item.get("handle") == wanted.get("handle")
        and item.get("x") == wanted.get("x")
        and item.get("y") == wanted.get("y")
        for item in figure.get("series") or []
    )


def planned_chart_series(session, chart_id):
    """Return the exact stored result series for one selected approved chart."""
    for requirement in execution_gaps(session).get("chart_requirements") or []:
        if requirement["chart"].get("id") == str(chart_id or "").strip():
            return requirement
    return None


def planned_chart_ids(session, missing_only=False):
    gaps = execution_gaps(session)
    if missing_only:
        return gaps.get("missing_chart_ids") or []
    return [item["chart"].get("id") for item in gaps.get("chart_requirements") or []]


def _run_can_output(run, y_name):
    entry = registry.get(run.get("model"))
    if entry is None:
        return False
    spec = run.get("parameters") or {}
    groups = entry.card.get("output_groups") or {}
    available = groups.get(spec.get("output"), list(entry.card.get("outputs", {})))
    return y_name in available


def _output_dependency_problems(charts, runs):
    problems = []
    coefficient_outputs = {
        "ks_per_m", "ka_per_m", "effective_permittivity", "single_scattering_albedo"
    }
    for chart in charts:
        if chart.get("x") != "dort_streams":
            continue
        coefficient_ys = coefficient_outputs.intersection(_chart_y_names(chart))
        if not coefficient_ys:
            continue
        for run in runs:
            spec = run.get("parameters") or {}
            if spec.get("output") == "coefficients" and spec.get("sweep_parameter") == "dort_streams":
                problems.append(
                    "%s sweeps DORT streams for %s, but coefficients are computed before the DORT solver"
                    % (run.get("label"), ", ".join(sorted(coefficient_ys)))
                )
    return problems


def _repair_sampling_density(charts, runs, minimum_points=8):
    """Densify an under-resolved trend before the human sees and approves the plan."""
    repairs = []
    repaired_ids = set()
    for chart in charts:
        if chart.get("kind", "line") not in ("line", "line+markers"):
            continue
        for run in runs:
            spec = run.get("parameters") or {}
            if run.get("id") in repaired_ids or not _run_produces_chart(run, chart):
                continue
            points = int(spec.get("sweep_points") or 0)
            if spec.get("sweep_parameter") in (None, "none") or points >= 6:
                continue
            spec["sweep_points"] = minimum_points
            repaired_ids.add(run.get("id"))
            repairs.append(
                {
                    "run_id": run.get("id"),
                    "field": "sweep_points",
                    "from": points,
                    "to": minimum_points,
                    "reason": "trend figures require at least 6 distinct samples",
                }
            )
    return repairs


def _repair_chart_axes(charts, runs):
    """Repair a categorical configuration name when one unambiguous numeric sweep exists.

    This changes only presentation metadata. It never changes a physical-model parameter,
    model combination, sampling range, or requested output, so the human still reviews the
    exact computation while avoidable schema mistakes do not consume more LLM calls.
    """
    repairs = []
    categorical = {"electromagnetic_model", "coefficient_type", "configuration", "model", "theory"}
    for chart in charts:
        if chart.get("x") not in categorical:
            continue
        axes_by_output = []
        for y_name in _chart_y_names(chart):
            axes = {
                (run.get("parameters") or {}).get("sweep_parameter")
                for run in runs
                if _run_can_output(run, y_name)
                and (run.get("parameters") or {}).get("sweep_parameter") not in (None, "none")
            }
            if axes:
                axes_by_output.append(axes)
        if not axes_by_output:
            continue
        common = set.intersection(*axes_by_output)
        if len(common) != 1:
            continue
        old_x = chart["x"]
        new_x = next(iter(common))
        chart["x"] = new_x
        if not chart.get("x_label") or old_x.replace("_", " ") in chart["x_label"].lower():
            chart["x_label"] = ""
        repairs.append(
            {
                "chart_id": chart.get("id"),
                "field": "x",
                "from": old_x,
                "to": new_x,
                "reason": "all compatible planned runs share this numeric sweep_parameter",
            }
        )
    return repairs


def _repair_required_companion_outputs(question, charts, runs):
    """Add a declared same-unit companion output omitted from presentation metadata.

    SMRT ``output=tb`` already computes both polarizations. When a question asks for
    brightness temperature/polarization but the planner puts only ``tb_v`` on a required
    chart, adding ``tb_h`` changes neither the experiment nor its cost. Rejecting the whole
    plan and asking the LLM to reproduce a large JSON object is both fragile and wasteful.
    """
    text = str(question or "").lower()
    if not ("brightness temperature" in text or re.search(r"\btb\b", text)):
        return []
    repairs = []
    for chart in charts:
        if not chart.get("required", True) or "tb_v" not in _chart_y_names(chart):
            continue
        if "tb_h" in _chart_y_names(chart):
            continue
        if not any(_run_produces_chart(run, chart, "tb_h") for run in runs):
            continue
        before = list(chart.get("ys") or [chart.get("y")])
        chart["ys"] = before + ["tb_h"]
        repairs.append(
            {
                "chart_id": chart.get("id"),
                "field": "ys",
                "from": before,
                "to": list(chart["ys"]),
                "reason": "the planned tb runs already produce both polarizations requested by the question",
            }
        )
        break
    return repairs


def _validate_chart_runs(charts, runs):
    """Validate figure producibility without confusing computation with presentation.

    Main/sensitivity/robustness runs carry scientific curves and must contribute to a
    required figure. A baseline may instead provide a scalar inversion target, and a
    diagnostic may only check solver convergence or numerical stability. Those auxiliary
    runs remain mandatory in ``execution_gaps`` but need not share a main plot's sweep axis.
    """
    problems = []
    for chart in charts:
        units = set()
        for y_name in _chart_y_names(chart):
            producers = [run["id"] for run in runs if _run_produces_chart(run, chart, y_name)]
            if not producers:
                problems.append(
                    "no planned run produces %s over x=%s" % (y_name, chart["x"])
                )
            for run in runs:
                entry = registry.get(run["model"])
                if entry and _run_produces_chart(run, chart, y_name):
                    unit = (entry.card.get("outputs", {}).get(y_name) or {}).get("unit")
                    if unit:
                        units.add(unit)
        if len(units) > 1:
            problems.append(
                "%s mixes incompatible y-axis units: %s; split it into separate charts"
                % (chart["label"], ", ".join(sorted(units)))
            )
    for run in runs:
        stage = str(run.get("stage") or "main").strip().lower()
        auxiliary = stage in ("baseline", "diagnostic")
        if not any(_run_produces_chart(run, chart) for chart in charts):
            if auxiliary:
                continue
            problems.append("%s contributes to none of the proposed charts" % run["label"])
        elif not any(
            chart.get("required", True) and _run_produces_chart(run, chart)
            for chart in charts
        ):
            if auxiliary:
                continue
            problems.append(
                "%s contributes only to optional layouts; add a required result or diagnostic chart"
                % run["label"]
            )
    return problems


def _chart_y_names(chart):
    return list(chart.get("ys") or ([chart.get("y")] if chart.get("y") else []))


def _run_produces_chart(run, chart, y_name=None):
    """Whether one approved run can supply the selected chart's exact axes."""
    entry = registry.get(run.get("model"))
    if entry is None:
        return False
    spec = run.get("parameters") or {}
    groups = entry.card.get("output_groups") or {}
    available = groups.get(spec.get("output"), list(entry.card.get("outputs", {})))
    x_matches = chart.get("x") == "index" or spec.get("sweep_parameter") == chart.get("x")
    wanted = [y_name] if y_name else _chart_y_names(chart)
    return bool(x_matches and any(name in available for name in wanted))


def _normal_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _question_coverage_problems(question, runs, charts):
    """Reject polished-looking plans that omit an observable named in the question."""
    text = str(question or "").lower()
    required_charts = [chart for chart in charts if chart.get("required", True)]
    outputs = {
        name
        for chart in required_charts
        for name in _chart_y_names(chart)
    }
    problems = []
    asks_tb = "brightness temperature" in text or re.search(r"\btb\b", text)
    asks_coefficients = "coefficient" in text
    asks_absorption = "absorption" in text
    asks_scattering = "scattering coefficient" in text
    asks_backscatter = "backscatter" in text or "sigma" in text
    if asks_tb:
        missing = {"tb_v", "tb_h"} - outputs
        if missing:
            problems.append("required brightness-temperature chart is missing %s" % ", ".join(sorted(missing)))
    if asks_coefficients and not outputs.intersection(
        {"ks_per_m", "ka_per_m", "effective_permittivity", "single_scattering_albedo"}
    ):
        problems.append("no required electromagnetic-coefficient chart")
    if asks_absorption and "ka_per_m" not in outputs:
        problems.append("absorption attribution requires ka_per_m")
    if asks_scattering and "ks_per_m" not in outputs:
        problems.append("scattering attribution requires ks_per_m")
    if asks_backscatter and not outputs.intersection({"sigma_vv_db", "sigma_hh_db", "sigma_hv_db"}):
        problems.append("no required backscatter chart")
    if "dort" in text:
        has_stream_sweep = any(
            (run.get("parameters") or {}).get("sweep_parameter") == "dort_streams"
            for run in runs
        )
        if not has_stream_sweep:
            problems.append("DORT attribution requires a dort_streams convergence run")
    if any(word in text for word in ("formulation", "theory", "solver")):
        configurations = {
            (
                (run.get("parameters") or {}).get("electromagnetic_model"),
                (run.get("parameters") or {}).get("output"),
            )
            for run in runs
        }
        electromagnetic_models = {item[0] for item in configurations if item[0]}
        if len(electromagnetic_models) < 2 and ("compare" in text or "difference" in text or "versus" in text):
            problems.append("formulation attribution requires at least two executable electromagnetic configurations")
    return problems


def _capability_gaps(question):
    """Named literature models that have no executable registry entry."""
    text = _normal_name(question)
    registered = {_normal_name(name) for name in registry.names()}
    gaps = []
    for item in knowledge.catalogue():
        card = knowledge.card(item["slug"]) or {}
        for alias in card.get("model_names") or []:
            normalized = _normal_name(alias)
            if normalized and normalized in text and normalized not in registered:
                gaps.append(str(alias))
    return sorted(set(gaps))


def report_warnings(session, answer):
    """Return advisory report-completeness findings.

    These findings help the model and the reviewer improve a scientific report, but they
    are not evidence failures.  Citation, evidence, abstract-depth and model validation
    remain enforced by ``harness.review_final`` and the research execution gates.
    """
    plan = ((session.get("research") or {}).get("plan") or {})
    gaps = plan.get("capability_gaps") or []
    problems = []
    anomalies = ((session.get("research") or {}).get("scientific_anomalies") or [])
    if anomalies:
        normalized_answer = str(answer or "").lower()
        if not any(
            word in normalized_answer
            for word in (
                "discontinuity", "abrupt jump", "numerical", "validity", "不连续", "突变", "数值", "适用范围"
            )
        ):
            problems.append(
                "Figure QA retained a persistent discontinuity as a qualified diagnostic. "
                "The report must identify it and state that it may be numerical or a model-validity "
                "boundary rather than a verified physical transition."
            )
    formal_figures = [
        figure for figure in session.get("figures") or [] if not figure.get("preview")
    ]
    normalized_report = str(answer or "").strip()
    lowered_report = normalized_report.lower()
    # A workflow-status message is not a scientific report.  Models sometimes stop after
    # QA with "the report can now be delivered"; previously that passed citation checks
    # and marked the project complete despite containing no interpretation or conclusion.
    status_only_phrases = (
        "can now be delivered", "will now be delivered", "ready to deliver",
        "final report can", "final report will", "正式报告现在可以", "可以交付最终",
    )
    conclusion_signals = (
        "therefore", "we conclude", "the results show", "indicates that",
        "supports the hypothesis", "does not support", "conclusion", "结论",
        "因此", "结果表明", "说明了", "支持假设", "不支持",
    )
    if formal_figures and (
        any(phrase in lowered_report for phrase in status_only_phrases)
        or not any(signal in lowered_report for signal in conclusion_signals)
    ):
        problems.append(
            "The response is only a workflow/QA status update, not the final scientific report. "
            "Interpret the plotted trends and comparisons, relate them to the hypothesis and "
            "success criteria, state limitations, and give an explicit scientific conclusion."
        )
    if len(formal_figures) > 1:
        missing_numbers = []
        for index, figure in enumerate(formal_figures, 1):
            number = figure.get("figure_number") or index
            if not re.search(r"(?:figure|fig\.?|图)\s*%d\b" % number, str(answer or ""), re.I):
                missing_numbers.append(str(number))
        if missing_numbers:
            problems.append(
                "The report must explain each formal output by Figure number. Add explicit "
                "interpretation for Figure %s; do not discuss several plots as an unnamed group."
                % ", Figure ".join(missing_numbers)
            )
    if not gaps:
        return " ".join(problems)
    lowered = lowered_report
    names_present = all(_normal_name(name) in _normal_name(answer) for name in gaps)
    limitation_present = any(
        phrase in lowered
        for phrase in ("partial", "not run", "not available", "unavailable", "not registered", "未运行", "不可用", "未注册", "部分复现")
    )
    if not (names_present and limitation_present):
        problems.append(
            "This is only a partial reproduction because these named comparison models are not "
            "registered and were not run: %s. State that limitation explicitly; do not report "
            "cross-model agreement metrics or attribute causal differences to their solvers."
            % ", ".join(gaps)
        )
    return " ".join(problems)


def report_problem(session, answer):
    """Backward-compatible name for callers that still inspect report findings."""
    return report_warnings(session, answer)


def safe_report(session):
    """Deterministic last resort: report only actions recorded in session state."""
    project = session.get("research") or {}
    plan = project.get("plan") or {}
    gaps = plan.get("capability_gaps") or []
    planned = plan.get("runs") or []
    successful = session.get("successful_runs") or []
    completed = []
    for run in planned:
        if any(
            actual.get("model") == run.get("model")
            and all(actual.get("spec", {}).get(key) == value for key, value in run.get("parameters", {}).items())
            for actual in successful
        ):
            completed.append(run.get("label") or run.get("id") or run.get("model"))
    markers = sorted(session.get("models_run") or ())
    model_note = (
        " Registered model evidence: %s." % ", ".join("[model:%s]" % marker for marker in markers)
        if markers
        else ""
    )
    figures = [figure for figure in session.get("figures") or [] if not figure.get("preview")]
    lines = [
        "Evidence-only fallback report",
        "The language-model narrative repeatedly failed evidence validation, so unsupported interpretation has been removed.",
        "Completed approved run(s): %s.%s" % (", ".join(completed) or "none", model_note),
        "Formal figure(s) generated from recorded result handles: %d." % len(figures),
    ]
    if gaps:
        lines.append(
            "This is a partial reproduction. %s %s not registered locally and %s not run; no cross-model agreement metric or solver-causality conclusion is available."
            % (", ".join(gaps), "is" if len(gaps) == 1 else "are", "was" if len(gaps) == 1 else "were")
        )
    else:
        lines.append("No additional scientific interpretation is published by this fallback.")
    return "\n\n".join(lines)


def planned_run_problem(session, model, spec):
    """Refuse successful-but-unplanned computations after formal approval."""
    project = session.get("research") or {}
    planned = (project.get("plan") or {}).get("runs") or []
    if any(run.get("model") == model and run.get("parameters") == spec for run in planned):
        return ""
    ids = [run.get("id") for run in planned]
    return (
        "This configuration is not one of the approved planned runs. Do not reconstruct "
        "approved parameters. Call run_planned_model with one of these run_id values: %s."
        % ", ".join(ids)
    )


def planned_run(session, run_id):
    project = session.get("research") or {}
    return next(
        (
            run
            for run in (project.get("plan") or {}).get("runs") or []
            if run.get("id") == str(run_id or "").strip()
        ),
        None,
    )


def planned_run_ids(session, missing_only=False):
    project = session.get("research") or {}
    runs = (project.get("plan") or {}).get("runs") or []
    if missing_only:
        return execution_gaps(session).get("missing_run_ids") or []
    return [run.get("id") for run in runs]


def review_action(session, choice):
    """Apply one of the two user-facing review controls to the current phase.

    Plan edits are made in Conversation. The second control is final figure
    confirmation, not a second plan-approval or regeneration path. Legacy
    ``secondary``/``pause`` values remain accepted for old callers but are not
    rendered by the current UI.
    """
    project = _require(session)
    phase = project["phase"]
    if choice == "primary":
        if phase in ("approved", "completed"):
            return _ok(
                "Formal execution is already approved for the current plan; the duplicate review action was ignored.",
                _public(project),
            )
        if phase == "plan_review":
            return approve_plan(session)
        if phase == "plan_approved":
            return pseudo_preview(session)
        if phase == "chart_selected":
            return approve_execution(session)
        if phase == "pseudo_preview":
            return confirm_charts(session)
    if choice == "satisfied_figures":
        if phase in ("approved", "completed"):
            return _ok(
                "Formal execution is already approved for the current plan; the duplicate figure confirmation was ignored.",
                _public(project),
            )
        if phase == "pseudo_preview":
            # The required charts are part of the reviewed plan.  Treat the user's
            # explicit figure confirmation as the chart-package confirmation when no
            # optional chart was selected, so the workflow has one figure approval
            # rather than an invisible extra click on a required-chart button.
            selected = list(project.get("selected_charts") or [])
            if not selected:
                selected = [
                    chart.get("id")
                    for chart in project.get("plan", {}).get("charts") or []
                    if chart.get("required", True) and chart.get("id")
                ]
                project["selected_charts"] = selected
                project["selected_chart"] = next(
                    (
                        dict(chart)
                        for chart in project.get("plan", {}).get("charts") or []
                        if chart.get("id") in selected
                    ),
                    None,
                )
                project.setdefault("review_log", []).append(
                    {
                        "version": project["plan_version"],
                        "note": "user confirmed the required figure package",
                        "changes": {"selected_charts": list(selected)},
                    }
                )
            if not selected:
                return _needs(
                    "The plan has no required figure to confirm. Select a chart or revise the plan in Conversation.",
                    _public(project),
                )
            confirm_charts(session)
            return approve_execution(session)
        if phase == "chart_selected":
            return approve_execution(session)
        return _needs(
            "Satisfied with figures is available after the required chart package has been selected. "
            "Revise the plan in Conversation or approve the plan first.",
            _public(project),
        )
    if choice == "secondary":
        if phase == "pseudo_preview":
            return _needs(
                "To change the pseudo-data axes, range, variables, or figure design, describe the requested plan revision in Conversation. The next revision becomes a new plan version and returns to plan review. To redraw the same layout only, ask the agent to regenerate the preview.",
                _public(project),
            )
        return _needs(
            "Describe the requested revision in Conversation. The agent will update the plan, create a new version, clear any preview, and return it to plan review.",
            _public(project),
        )
    if choice == "pause":
        project["review_log"].append(
            {"version": project["plan_version"], "note": "user paused at %s" % phase, "changes": {}}
        )
        return _needs("Research remains paused at %s; no model call was authorized." % phase, _public(project))
    return _fail("No review action is available for phase %s." % phase)


def allow_model(session):
    return bool((session.get("research") or {}).get("phase") in ("approved", "completed"))


def _require(session):
    if not session.get("research"):
        raise ValueError("No LLM-authored research proposal exists yet.")
    return session["research"]


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


def target_ids_for_run(session, run_id):
    run = planned_run(session, run_id)
    return list((run or {}).get("target_ids") or [])


def target_ids_for_chart(session, chart_id):
    project = session.get("research") or {}
    chart = next(
        (
            item for item in (project.get("plan") or {}).get("charts") or []
            if item.get("id") == str(chart_id or "").strip()
        ),
        None,
    )
    return list((chart or {}).get("target_ids") or [])


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
