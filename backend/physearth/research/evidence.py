"""What is missing before a plan can claim to be evidence-backed."""

from physearth.research.common import PARAMETER_PROVENANCE
from physearth.research.coverage import _target_coverage
from physearth.research.mapping import (
    _expected_mapping_inputs,
    _ledger_entries,
    _registered_parameter_index,
)
from physearth.research.normalise import (
    _normalise_evidence_ref,
    _read_evidence_refs,
    is_reproduction_question,
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
        if item.get("analysis_status") not in ("unavailable", "metadata_only")
        and item.get("reference")
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
        if not target.get("reference_models"):
            problems.append({
                "field": prefix + ".reference_models",
                "source": "opened_paper_evidence",
                "actual": [],
                "expected": "paper reference-model identity or an explicitly unavailable target",
                "repair": "Record the model identity named by the paper; do not let a different local model satisfy this target.",
                "blocking": True,
            })
        if not target.get("requested_outputs"):
            problems.append({
                "field": prefix + ".requested_outputs",
                "source": "opened_paper_evidence",
                "actual": [],
                "expected": "the output quantity represented by the paper target",
                "repair": "Record the requested paper output and validate it against the registered model declaration.",
                "blocking": True,
            })
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
    coverage_problems, _, _ = _target_coverage(reproduction_targets, runs, charts, session)
    for problem in coverage_problems:
        target_index = next(
            (
                index for index, target in enumerate(reproduction_targets)
                if str(target.get("id") or "target") in str(problem)
            ),
            None,
        )
        target = reproduction_targets[target_index] if target_index is not None else {}
        if "not one of reference_models" in problem or "no run coverage for reference_models" in problem:
            field = (
                "reproduction_targets[%d].run_ids" % target_index
                if target_index is not None else "reproduction_targets.coverage"
            )
            problems.append({
                "field": field,
                "source": "registered_model_declaration",
                "actual": target.get("run_ids") or [],
                "expected": "run.model must match the paper reference_models",
                "allowed_values": target.get("reference_models") or [],
                "repair": "Replace only the target coverage with runs using the exact reference model identity, or mark the target partial/unavailable.",
                "blocking": True,
                "message": problem,
            })
        elif "does not declare a requested output" in problem:
            field = (
                "reproduction_targets[%d].run_ids" % target_index
                if target_index is not None else "reproduction_targets.coverage"
            )
            problems.append({
                "field": field,
                "source": "registered_model_declaration",
                "actual": target.get("run_ids") or [],
                "expected": "run output must declare one of requested_outputs",
                "allowed_values": target.get("requested_outputs") or [],
                "repair": "Use a run whose registered output group contains the requested paper quantity; do not rename a local output.",
                "blocking": True,
                "message": problem,
            })
        else:
            problems.append({
                "field": "reproduction_targets.coverage",
                "source": "runs/charts",
                "expected": "known run_ids or chart_ids",
                "repair": problem,
                "blocking": True,
            })
    if not outputs:
        problems.append({"field": "outputs", "source": "research_plan", "expected": "model outputs used to evaluate the target", "repair": "Declare the quantities/outputs that will be compared."})
    return problems

def legend_coverage_warnings(session, targets, runs):
    """Say when a figure's legend names more series than the plan has runs.

    A figure is reproduced from its axes, its labels and its legend. The legend is what
    says how many curves are on it -- the inspection already extracts it -- and a plan
    with one run against a legend of five is not reproducing that figure, it is
    reproducing one line of it.

    Advisory rather than blocking. A legend entry is not always a run: some name a
    measurement, a shaded band, or the same model at a second frequency already covered
    by a sweep. So this is surfaced at review, where a human can see both lists and
    decide, rather than refused where it would have to guess.
    """
    inspected = {
        _normalise_evidence_ref(item.get("reference")): item
        for item in _ledger_entries(session, "figure_inspection")
        if item.get("reference")
    }
    if not inspected:
        return []
    warnings = []
    for target in targets or ():
        if target.get("status") in ("partial", "unavailable"):
            continue
        run_ids = [run_id for run_id in (target.get("run_ids") or ())]
        for ref in target.get("evidence_refs") or ():
            entry = inspected.get(_normalise_evidence_ref(ref))
            if not entry:
                continue
            legend = [
                str(item).strip()
                for item in ((entry.get("visual_observations") or {}).get("legend") or ())
                if str(item).strip()
            ]
            if len(legend) > max(len(run_ids), 1) and len(legend) > 1:
                warnings.append(
                    "target %s covers %d run(s) but the legend of %s names %d series: %s. "
                    "Check whether each is a separate run before approving."
                    % (
                        target.get("id") or "target",
                        len(run_ids),
                        entry.get("reference"),
                        len(legend),
                        "; ".join(legend[:6]) + ("; ..." if len(legend) > 6 else ""),
                    )
                )
    return warnings
