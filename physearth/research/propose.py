"""Turning a model's proposed plan into one the harness will accept."""

import copy

from physearth.research.charts import (
    _capability_gaps,
    _output_dependency_problems,
    _question_coverage_problems,
    _repair_chart_axes,
    _repair_required_companion_outputs,
    _repair_sampling_density,
    _validate_chart_runs,
)
from physearth.research.common import _clean_list, _fail, _needs, _public
from physearth.research.coverage import _target_coverage
from physearth.research.evidence import _evidence_plan_problems, _evidence_problem_summary
from physearth.research.mapping import _is_paper_context_problem
from physearth.research.metadata import _repair_reproduction_metadata
from physearth.research.normalise import (
    _clean_charts,
    _clean_literature_evidence,
    _clean_outputs,
    _clean_parameter_mapping,
    _clean_reproduction_targets,
    _clean_runs,
    _clean_selected_models,
    _enrich_selected_models,
    _repair_missing_protocol_steps,
    is_reproduction_question,
)


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
        reproduction_targets, runs, charts, session
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
        "capability_gaps": _capability_gaps(question, session),
        "capability_review": copy.deepcopy(session.get("capability_review") or {}),
        "reference_sections": sorted(session.get("sections_read") or ()),
        "reference_paper_sections": [paper_section] if paper_section else [],
        "approval_state": "plan_review",
    }
    capability_review = plan.get("capability_review") or {}
    plan["outcome_scope"] = (
        "partial"
        if plan["capability_gaps"]
        or capability_review.get("user_decision") == "partial"
        else "full"
    )
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
