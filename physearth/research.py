"""Generic, human-reviewed research state for PhysEarth.

The four SMRT scientific questions are evaluation cases, not workflow templates.  A plan
enters this module only after the language model has analysed the user's question and
submitted a structured proposal through the research_plan tool.
"""

import copy
import math
import re

from physearth import audit, knowledge, plotting, reproduction, validation
from physearth.models import registry


PHASES = (
    "plan_review",
    "plan_approved",
    "pseudo_preview",
    "chart_selected",
    "approved",
    "completed",
)


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
        "Verify the cited reference protocol, registered-model capabilities, controlled conditions, and baseline configuration.",
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
    """Clamp only sweep bounds to an already-declared physical parameter range.

    This does not invent physics: the model chose the parameter and interval, while the
    registered capability declaration supplies the hard legal bounds. The exact change is
    retained for human review. Ordinary fixed parameter values remain strict failures.
    """
    repaired = dict(parameters)
    sweep = repaired.get("sweep_parameter")
    target = (card.get("parameters") or {}).get(sweep)
    if sweep in (None, "none") or not target or target.get("type") not in ("number", "integer"):
        return repaired, []
    changes = []
    low, high = target.get("minimum"), target.get("maximum")
    for field in ("sweep_start", "sweep_stop"):
        value = repaired.get(field)
        if not isinstance(value, (int, float)):
            continue
        bounded = max(low, min(high, value))
        if bounded != value:
            repaired[field] = int(bounded) if target.get("type") == "integer" else float(bounded)
            changes.append(
                {
                    "field": field,
                    "from": value,
                    "to": repaired[field],
                    "reason": "%s sweep bound was clamped to the declared %s range" % (model, sweep),
                }
            )
    return repaired, changes


def _clean_runs(runs):
    cleaned = []
    problems = []
    repairs = []
    for index, run in enumerate(runs or []):
        if not isinstance(run, dict):
            problems.append("planned run %d is not an object" % (index + 1))
            continue
        model = str(run.get("model") or "").strip()
        entry = registry.get(model)
        if entry is None:
            problems.append("planned run %d uses unknown model %r" % (index + 1, model))
            continue
        parameters, bound_repairs = _repair_sweep_bounds(
            model, dict(run.get("parameters") or {}), entry.card
        )
        for repair in bound_repairs:
            repairs.append({"run_id": str(run.get("id") or "run_%d" % (index + 1)), **repair})
        resolved, run_problems = validation.resolve(entry.card, parameters, enforce=True)
        if run_problems:
            problems.extend("planned run %d: %s" % (index + 1, item) for item in run_problems)
            continue
        cleaned.append(
            {
                "id": str(run.get("id") or "run_%d" % (index + 1)).strip(),
                "label": str(run.get("label") or "%s run" % model).strip(),
                "model": model,
                "parameters": resolved,
                "stage": str(run.get("stage") or "main").strip(),
            }
        )
    # A multi-density/multi-microstructure experiment can legitimately require more than
    # eight configurations (Q4 uses a baseline plus two five-density families). Silently
    # dropping later runs changes the reviewed experiment and makes chart validation
    # inexplicable. Keep a generous explicit ceiling instead.
    if len(cleaned) > 24:
        problems.append("a proposal may contain at most 24 physical-model runs")
    return cleaned[:24], problems, repairs


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
):
    """Store an LLM-authored proposal; never infer one from a question template."""
    question = str(question or "").strip()
    read_problem = reproduction.required_read_problem(session, question)
    if read_problem:
        return _fail(read_problem["message"], read_problem)
    objective = str(objective or "").strip()
    hypothesis = str(hypothesis or "").strip()
    steps = _clean_list(steps)
    charts = _clean_charts(charts)
    runs, run_problems, run_repairs = _clean_runs(runs)
    quantities = _clean_list(quantities, 12)
    controls = _clean_list(controls, 12)
    metrics = _clean_list(metrics, 12)
    diagnostics = _clean_list(diagnostics, 12)
    stop_conditions = _clean_list(stop_conditions, 12)
    success_criteria = _clean_list(success_criteria, 12)
    assumptions = _clean_list(assumptions, 12)
    limitations = _clean_list(limitations, 12)
    baseline_run_id = str(baseline_run_id or "").strip()
    if not question or not objective or not hypothesis:
        return _fail("A proposal requires question, objective and hypothesis.")
    if not charts:
        return _fail("A proposal requires at least one chart option with x and y fields.")
    if run_problems:
        return _fail(
            "The proposed execution plan is invalid: %s" % "; ".join(run_problems),
            {
                "error_code": "run_validation",
                "problems": run_problems,
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
    reference_repairs = reproduction.repair(question, runs, charts)
    reproduction_case, reproduction_problems = reproduction.validate(
        question, runs, charts, limitations
    )
    if reproduction_problems:
        return _fail(
            "The proposed plan does not reproduce the paper's %s protocol: %s"
            % (reproduction_case.upper(), "; ".join(reproduction_problems)),
            {
                "error_code": "reference_protocol_mismatch",
                "case_id": reproduction_case,
                "reference_section": reproduction.CASES[reproduction_case]["section"],
                "problems": reproduction_problems,
                "repair_hints": [
                    "Keep the independent variable and common physical conditions from the paper section.",
                    "Use separate passive, active, coefficient, and solver-diagnostic runs when their outputs differ.",
                    "Declare unavailable external reference models as a partial reproduction; never replace them with another SMRT run.",
                ],
            },
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
    run_ids = [run["id"] for run in runs]
    if baseline_run_id not in run_ids:
        quality_problems.append("baseline_run_id naming one planned run")
    if quality_problems:
        return _fail(
            "The proposal is a computation checklist, not yet a scientific protocol. Add: %s."
            % ", ".join(quality_problems)
        )
    automatic_repairs = list(run_repairs)
    automatic_repairs.extend(structural_repairs)
    automatic_repairs.extend(reference_repairs)
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
        "title": objective,
        "question": question,
        "objective": objective,
        "hypothesis": hypothesis,
        "steps": steps,
        "parameters": dict(parameters or {}),
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
        "capability_gaps": _capability_gaps(question),
        "reproduction_case": reproduction_case,
        "reference_sections": [reproduction.CASES[reproduction_case]["section"]]
        if reproduction_case else [],
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
        "review_log": [],
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


def revise(session, changes=None, note=""):
    project = _require(session)
    changes = dict(changes or {})
    plan = copy.deepcopy(project["plan"])
    known_fields = {
        "objective", "hypothesis", "steps", "charts", "runs", "parameters",
        "quantities", "controls", "metrics", "diagnostics", "success_criteria",
        "stop_conditions", "assumptions", "limitations", "baseline_run_id",
    }
    for key in ("objective", "hypothesis"):
        if key in changes and changes[key] is not None:
            plan[key] = str(changes[key]).strip()
            if key == "objective":
                plan["title"] = plan[key]
    if isinstance(changes.get("parameters"), dict):
        plan.setdefault("parameters", {}).update(changes["parameters"])
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
        runs, problems, repairs = _clean_runs(changes["runs"])
        if problems or not runs:
            raise ValueError("Invalid revised runs: %s" % "; ".join(problems or ["none supplied"]))
        plan["runs"] = runs
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
    project["plan_version"] += 1
    project["plan"] = plan
    project["review_log"].append(
        {
            "version": project["plan_version"],
            "note": note or changes.get("reason") or "user-requested revision",
            "changes": changes,
        }
    )
    project["phase"] = "plan_review"
    project["selected_chart"] = None
    project["selected_charts"] = []
    project["pseudo"] = None
    _clear_previews(session)
    return _needs("Plan revised to v%03d. Review it again." % project["plan_version"], _public(project))


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
    session["figures"] = []
    session["evidence_revision"] = int(session.get("evidence_revision", 0)) + 1
    return _needs(summary, _public(project))


def approve_plan(session):
    project = _require(session)
    if project["phase"] != "plan_review":
        return _fail("The plan cannot be approved in phase %s." % project["phase"])
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
    if project["phase"] != "chart_selected":
        return _needs("Select a chart after the pseudo-data preview first.", _public(project))
    project["phase"] = "approved"
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
    }


def _figure_satisfies(figure, expected):
    """A planned chart is one figure containing every exact handle/x/y series."""
    actual = figure.get("series") or []
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


def report_problem(session, answer):
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
    """Apply one of the three persistent UI controls to the current review phase."""
    project = _require(session)
    phase = project["phase"]
    if choice == "primary":
        if phase == "plan_review":
            return approve_plan(session)
        if phase == "plan_approved":
            return pseudo_preview(session)
        if phase == "chart_selected":
            return approve_execution(session)
        if phase == "pseudo_preview":
            return confirm_charts(session)
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


def _public(project):
    return {**project, "plan": {**project["plan"]}, "review_log": list(project["review_log"])}


def _ok(summary, data):
    return {"status": "success", "summary": summary, "data": data, "citations": [], "qc": None, "ui": None, "error": None}


def _needs(summary, data):
    return {"status": "needs_input", "summary": summary, "data": data, "citations": [], "qc": None, "ui": None, "error": summary}


def _fail(summary, data=None):
    return {"status": "terminal_error", "summary": summary, "data": data or {}, "citations": [], "qc": None, "ui": None, "error": summary}
