"""What a plan still owes: gaps, and the runs and charts it named."""

from physearth.research.charts import (
    _chart_y_names,
    _figure_has_series,
    _figure_satisfies,
    _run_produces_chart,
)


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
