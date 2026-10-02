"""Repairing a parameter mapping: names, units, provenance, and what the card allows."""

import math
import re

from physearth import registry
from physearth.research.common import (
    PARAMETER_CONFIDENCE,
    PARAMETER_PROVENANCE,
    _provenance_confidence,
)
from physearth.research.normalise import _normalise_evidence_ref


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
        # Through resolution, so a plan still holding the paper's spelling indexes the
        # model it names instead of contributing nothing and reporting every one of its
        # mappings as unmatched.
        entry, canonical = registry.resolve(model, session)
        if entry:
            index[model] = dict(entry.card.get("parameters") or {})
            if canonical != model:
                index[canonical] = index[model]
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
                # A name that is a declared *output* is the common mistake here, and it
                # is a different mistake: the quantity is real and belongs to the plan,
                # just under outputs rather than in the mapping. Saying only "not an
                # input" sent the agent round the same loop five times, replacing one
                # output name with another.
                produced_by = sorted(
                    model
                    for model, entry in (
                        (m, registry.resolve(m, session)[0]) for m in parameter_index
                    )
                    if entry is not None
                    and _normalise_parameter_name(raw_name)
                    in {
                        _normalise_parameter_name(output)
                        for output in (entry.card.get("outputs") or {})
                    }
                )
                if produced_by:
                    repair = (
                        "%s is an output of %s, not an input. Record it under outputs, "
                        "and map only the quantities the model is given."
                        % (raw_name, ", ".join(produced_by))
                    )
                    expected = "an input, not a declared output"
                elif len(candidates) > 1:
                    repair = "Replace the alias with one exact input from list_models."
                    expected = "an exact registered model input"
                else:
                    repair = (
                        "Replace the unknown input with an exact parameter returned by list_models."
                    )
                    expected = "an exact registered model input"
                problems.append({
                    "field": "parameter_mapping[%d].model_input" % index,
                    "source": "registered_model_declaration",
                    "actual": raw_name,
                    "expected": expected,
                    "allowed_values": candidate_values,
                    "repair": repair,
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
