"""Everything the model sends, reduced to the shape the rest of this package expects."""

import re

from physearth import registry
from physearth.harness import validation
from physearth.research.common import _clean_list


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
        and re.search(r"\b(?:papers?|articles?|stud(?:y|ies)|literature|published|figures?|tables?|results?)\b", text)
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
                "reference_models": [
                    str(model).strip()
                    for model in (
                        item.get("reference_models")
                        or item.get("comparison_models")
                        or item.get("models")
                        or []
                    )
                    if str(model).strip()
                ],
                "requested_outputs": [
                    str(output).strip()
                    for output in (
                        item.get("requested_outputs")
                        or item.get("outputs")
                        or []
                    )
                    if str(output).strip()
                ],
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
