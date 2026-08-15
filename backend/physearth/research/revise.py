"""Revising an existing plan: by request, after a bad figure, after a failed run."""

import copy
import json

from physearth import registry
from physearth.harness import audit
from physearth.research.approval import _clear_previews
from physearth.research.charts import _chart_y_names, _run_produces_chart, _validate_chart_runs
from physearth.research.common import _clean_list, _fail, _needs, _ok, _public, _require
from physearth.research.coverage import _target_coverage
from physearth.research.evidence import _evidence_plan_problems, _evidence_problem_summary
from physearth.research.mapping import _is_paper_context_problem, _mark_user_revised_inputs
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
    is_reproduction_question,
)

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
        targets, plan.get("runs") or [], plan.get("charts") or [], session
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
