"""One human review action, dispatched to the gate it belongs to."""

from physearth.research.approval import (
    approve_execution,
    approve_plan,
    confirm_charts,
    pseudo_preview,
)
from physearth.research.common import _fail, _needs, _ok, _public, _require


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
