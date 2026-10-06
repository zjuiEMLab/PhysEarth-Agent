"""What is missing before a plan can claim to be evidence-backed."""

import re

from physearth import registry
from physearth.corpus import knowledge
from physearth.research import asked
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


def _is_figure_target(target, evidence_refs, opened_figures):
    """Recognize a paper-figure target even when the model omits source_type."""
    if str(target.get("source_type") or "").strip().lower() == "figure":
        return True
    source_id = str(target.get("source_id") or "")
    if re.search(r"(?:fig(?:ure)?)[^0-9]*(\d+)", source_id, re.I):
        return True
    return bool(set(evidence_refs or ()) & set(opened_figures or ()))


def _evidence_plan_problems(session, question, literature_evidence, reproduction_targets,
                            selected_models, parameter_mapping, outputs, runs, charts,
                            parameter_resolution=None):
    if not is_reproduction_question(question, session):
        return []
    problems = []
    sections, figures = _read_evidence_refs(session)
    inspected_figures = {
        _normalise_evidence_ref(item.get("reference"))
        for item in _ledger_entries(session, "figure_inspection")
        if item.get("analysis_status") not in ("unavailable", "metadata_only")
        and item.get("reference")
    }
    opened_refs = sorted(sections | figures)
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
                "allowed_values": opened_refs,
                "repair": "Use one of allowed_values, or read the cited section or figure first and use its returned citation reference.",
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
        figure_target = _is_figure_target(target, refs, figures)
        if not refs:
            problems.append({"field": prefix + ".evidence_refs", "source": "research_plan", "expected": "opened paper evidence", "repair": "Read and cite the relevant section, figure, or table."})
        elif not refs.intersection(sections | figures):
            problems.append({"field": prefix + ".evidence_refs", "source": ", ".join(sorted(refs)), "expected": "opened evidence reference", "allowed_values": opened_refs, "repair": "Use one of allowed_values, or the citation returned by read_literature or read_paper_figure."})
        if (
            figure_target
            and not refs.intersection(figures)
            and target.get("status") not in ("partial", "unavailable")
        ):
            problems.append({"field": prefix + ".evidence_refs", "source": "paper_figures_read", "expected": "source figure opened with read_paper_figure", "repair": "Call read_paper_figure before proposing the reproduction."})
        if (
            figure_target
            and refs.intersection(figures)
            and not refs.intersection(inspected_figures)
            and target.get("status") not in ("partial", "unavailable")
        ):
            problems.append({
                "field": prefix + ".figure_inspection",
                "source": ", ".join(sorted(refs.intersection(figures))),
                "expected": "title, axes, legend, panels, and qualitative trends from an inspected source figure",
                "repair": "Call inspect_paper_figure after read_paper_figure for every figure target and record its title, axes, legend, panels, and qualitative trends; do not digitize curves automatically.",
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
                "repair": "Replace only the target coverage with runs using the exact reference model identity, or set the target's status to partial or unavailable and give its availability_reason.",
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
    problems.extend(_unstated_value_problems(session, parameter_mapping, runs))
    return problems


_MAX_UNOPENED_SECTIONS = 3


def _same_number(left, right):
    try:
        return abs(float(left) - float(right)) <= 1e-9 * max(1.0, abs(float(right)))
    except (TypeError, ValueError):
        return left == right


def _swept_names(runs, model):
    return {
        str((run.get("parameters") or {}).get("sweep_parameter") or "")
        for run in runs or ()
        if str(run.get("model") or "") == model
    }


def _gives_value(sentence, unit, numbers):
    """A sentence that gives the value in play: a number equal to the assumed value or the default.

    A number in the right unit is not enough, since a paper quotes many unrelated frequencies,
    lengths and temperatures ("below 19 GHz"), and naming the parameter is not enough either.
    The sentence must state the number the plan assumed or the number the card defaults to,
    which is the one case where an unread section decides what the plan should say.
    """
    if not asked.states_value(sentence, unit):
        return False
    for span in asked._spans(sentence, unit):
        if "-" in span:
            continue  # "37-89 GHz" is a range the paper mentions, not a value it states
        if any(_same_number(span, number) for number in numbers):
            return True
    return False


def _unopened_sections_naming(session, unit, numbers):
    """Sections of papers already opened that state the value in play and are still unopened."""
    if len(str(unit or "").strip()) < 2 or str(unit).strip().lower() == "none":
        return []
    opened = set(session.get("sections_read") or ())
    found = []
    for slug in sorted({str(key).partition("#")[0] for key in opened}):
        for item in knowledge.section_index(slug) or ():
            key = "%s#%s" % (slug, item["id"])
            if key in opened:
                continue
            section = knowledge.read_section(slug, item["id"])
            for sentence in asked._sentences((section or {}).get("text")):
                if _gives_value(sentence, unit, numbers):
                    found.append((key, sentence[: asked.MAX_PASSAGE_CHARS]))
                    break
    return found[:_MAX_UNOPENED_SECTIONS]


def _unstated_value_problems(session, parameter_mapping, runs):
    """A value the paper did not state is the card's default, not an invented one.

    A reproduction fills what the source leaves open, and the honest fill is the registered
    model's own default, labelled as such. Two things are refused before the plan runs: an
    assumed value that differs from the card's default without evidence, and an assumption
    made while unopened sections of the same paper still give a value in that parameter's unit.
    The second is closed by reading the section; nothing here knows which section or value.
    """
    problems = []
    for index, item in enumerate(parameter_mapping or ()):
        if not isinstance(item, dict) or item.get("provenance_class") != "model_assumption":
            continue
        if item.get("evidence_ref") or item.get("paper_value") not in (None, ""):
            continue
        name = str(item.get("model_input") or "")
        model = str(item.get("model") or "")
        entry = registry.get(model, session) if model else None
        spec = ((entry.card.get("parameters") or {}).get(name) or {}) if entry else {}
        if not spec or name in _swept_names(runs, model):
            continue
        if spec.get("type") not in ("number", "integer"):
            continue  # a choice of formulation is a design decision, not a value to default
        if name.startswith("sweep") or str(spec.get("unit") or "") in ("count", "same as the swept parameter"):
            continue  # how a sweep or a solver is sampled is numerics, not physics
        default = spec.get("default")
        value = item.get("mapped_value")
        unit = spec.get("unit") or ""
        numbers = [number for number in (value, default) if number is not None]
        for key, sentence in _unopened_sections_naming(session, unit, numbers):
            slug, _, section_id = key.partition("#")
            problems.append({
                "field": "parameter_mapping[%d]" % index,
                "source": key,
                "expected": "a section stating %s read before %s is assumed" % (unit, name),
                "repair": "%s is labelled model_assumption, but %s, which you have not opened, says: "
                "\"%s\". Call read_literature with slug=%s and section_id=%s first: citing it "
                "without reading it is refused. Then, if it states the value, set the mapping to "
                "paper_explicit with evidence_ref %s."
                % (name, key, sentence, slug, section_id, key),
            })
        if default is not None and value is not None and not _same_number(value, default):
            problems.append({
                "field": "parameter_mapping[%d].mapped_value" % index,
                "source": "registered_model_declaration",
                "actual": value,
                "expected": "the card default %s %s, or a value an opened source states" % (default, unit),
                "repair": "%s = %s is labelled model_assumption with no evidence. If an opened source "
                "states it (a figure caption, a section), change the mapping to paper_explicit and "
                "give its evidence_ref; otherwise use the card default %s with provenance_class "
                "backend_default."
                % (name, value, default),
            })
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
