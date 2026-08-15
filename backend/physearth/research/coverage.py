"""Whether the runs and charts actually cover the reproduction targets."""

from physearth.models import registry


def _target_coverage(targets, runs, charts, session=None):
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
        reference_models = {
            str(model).strip()
            for model in target.get("reference_models") or ()
            if str(model).strip()
        }
        requested_outputs = {
            str(output).strip()
            for output in target.get("requested_outputs") or ()
            if str(output).strip()
        }
        if reference_models:
            for run_id in target.get("run_ids") or ():
                run = next((item for item in runs if item.get("id") == run_id), None)
                if run is None:
                    continue
                run_model = str(run.get("model") or "").strip()
                if run_model not in reference_models:
                    problems.append(
                        "target %s run %s uses %s, not one of reference_models: %s"
                        % (target_id, run_id, run_model, ", ".join(sorted(reference_models)))
                    )
                if requested_outputs:
                    parameters = run.get("resolved_parameters") or run.get("parameters") or {}
                    output_group = str(parameters.get("output") or "").strip()
                    entry = registry.get(run_model, session)
                    output_groups = (entry.card.get("output_groups") or {}) if entry else {}
                    declared_outputs = set(output_groups.get(output_group) or ())
                    if not declared_outputs.intersection(requested_outputs):
                        problems.append(
                            "target %s run %s does not declare a requested output: %s"
                            % (target_id, run_id, ", ".join(sorted(requested_outputs)))
                        )
            if (
                target.get("status") not in ("partial", "unavailable")
                and not any(
                    (run.get("model") in reference_models)
                    for run in runs
                    if run.get("id") in (target.get("run_ids") or ())
                )
            ):
                problems.append(
                    "target %s has no run coverage for reference_models: %s"
                    % (target_id, ", ".join(sorted(reference_models)))
                )
        for run_id in target.get("run_ids") or ():
            if run_id in linked_runs:
                linked_runs[run_id].append(target_id)
        for chart_id in target.get("chart_ids") or ():
            if chart_id in linked_charts:
                linked_charts[chart_id].append(target_id)
    return problems, linked_runs, linked_charts
