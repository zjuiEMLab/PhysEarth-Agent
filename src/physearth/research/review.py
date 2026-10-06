"""One human review action, dispatched to the gate it belongs to."""

from physearth.research.approval import (
    approve_execution,
    approve_plan,
    confirm_charts,
    pseudo_preview,
)
from physearth.research.common import _fail, _needs, _ok, _public, _require


def _select_required_charts(project, note):
    """The required charts are part of the reviewed plan; confirming it confirms them.

    Used when no optional chart was picked, so the workflow has one figure approval rather
    than an invisible extra click on a required-chart button.
    """
    selected = list(project.get("selected_charts") or [])
    if selected:
        return selected
    charts = project.get("plan", {}).get("charts") or []
    selected = [
        chart.get("id") for chart in charts if chart.get("required", True) and chart.get("id")
    ]
    project["selected_charts"] = selected
    project["selected_chart"] = next(
        (dict(chart) for chart in charts if chart.get("id") in selected), None
    )
    if selected:
        project.setdefault("review_log", []).append(
            {
                "version": project["plan_version"],
                "note": note,
                "changes": {"selected_charts": list(selected)},
            }
        )
    return selected


def review_action(session, choice):
    """Apply one of the two user-facing review controls to the current phase.

    Plan edits are made in Conversation. The second control is final figure
    confirmation; in plan review it approves the plan, its required figures and their
    execution in one step. It is never a regeneration path. Legacy
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
        if phase == "plan_review":
            # Approve and run: one human decision covers the plan, its required figures
            # and their execution, for a user who does not want the layout preview. The
            # approval is still the user's click; nothing here can be reached by the agent.
            approved = approve_plan(session)
            if project["phase"] != "plan_approved":
                return approved
            project["phase"] = "pseudo_preview"
            selected = _select_required_charts(project, "user approved the plan and its required figures for execution")
            if not selected:
                project["phase"] = "plan_approved"
                return _needs(
                    "The plan has no required figure to run. Preview the layout and select a "
                    "chart, or revise the plan in Conversation.",
                    _public(project),
                )
            confirm_charts(session)
            return approve_execution(session)
        if phase == "pseudo_preview":
            selected = _select_required_charts(
                project, "user confirmed the required figure package"
            )
            if not selected:
                return _needs(
                    "The plan has no required figure to confirm. Select a chart or revise the "
                    "plan in Conversation.",
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


# What a person types to act on a plan in Conversation. Only a whole message counts, so
# "approve, but change the density range" is a revision, not an approval -- and nothing
# the model writes ever passes through here: this reads the user's own message before the
# model sees it.
_APPROVE = frozenset({
    "approve", "approved", "i approve", "approve it", "approve plan", "approve the plan",
    "approve and run", "approve and run it", "approve the plan and run it",
    "approve the plan and run", "run it", "run the plan", "lgtm",
    "批准", "同意", "批准并运行", "批准运行", "确认运行", "开始运行",
})
_PREVIEW = frozenset({
    "preview", "preview it", "preview first", "show preview", "show the preview",
    "preview layout", "preview the layout", "approve for preview", "预览", "先预览",
})
_REVIEW_PHASES = ("plan_review", "plan_approved", "pseudo_preview", "chart_selected")


def _normalise_command(text):
    text = " ".join(str(text or "").strip().lower().split())
    return text.strip(" .!。！`'\"*")


def chat_command(session, text):
    """The review step a typed message asks for: "approve", "preview" or None.

    None means the message is not a review command and goes to the agent as usual, which
    treats it as a change to the plan.
    """
    phase = ((session or {}).get("research") or {}).get("phase")
    if phase not in _REVIEW_PHASES:
        return None
    command = _normalise_command(text)
    if command in _APPROVE:
        return "approve"
    if command in _PREVIEW and phase in ("plan_review", "plan_approved"):
        return "preview"
    return None


def apply_chat_command(session, command):
    """Apply a typed review command to the gate it belongs to. Returns the review result."""
    project = _require(session)
    phase = project["phase"]
    if command == "preview":
        if phase == "plan_review":
            approved = approve_plan(session)
            if project["phase"] != "plan_approved":
                return approved
        return pseudo_preview(session)
    if command == "approve":
        if phase == "plan_approved":
            pseudo_preview(session)
        return review_action(session, "satisfied_figures")
    return _fail("Unknown review command %r." % command)


def review_guidance(project):
    """What the person can type next, for the phase the plan is in."""
    phase = (project or {}).get("phase", "plan_review")
    version = int((project or {}).get("plan_version") or 1)
    if phase == "pseudo_preview":
        return (
            "The layout preview of plan v%03d is in Evidence → Figures. It is drawn from "
            "pseudo-data and shows layout only, not results.\n\n"
            "Reply **approve** to run the plan and draw its required figures from real model "
            "output, or describe what to change and the plan comes back as a new version."
            % version
        )
    if phase == "chart_selected":
        return (
            "The figure package of plan v%03d is confirmed. Reply **approve** to run the "
            "registered models, or describe what to change." % version
        )
    if phase == "plan_approved":
        return (
            "Plan v%03d is approved for a layout preview only. Reply **preview** to draw it "
            "from pseudo-data, **approve** to skip the preview and run, or describe what to "
            "change." % version
        )
    return (
        "Research plan v%03d is ready for your review. Nothing has been run yet.\n\n"
        "Open the plan from the card below to check it, then reply **approve** to run it, "
        "**preview** to see the figure layout first, or describe what to change."
        % version
    )


def execution_brief(session):
    """The approved plan and the paper's key statements, handed to the agent at approval.

    Everything the report needs from the paper should already be here -- the session's
    digest of it and the findings the plan recorded -- so a section is reopened only to
    check a detail, not to rediscover what the plan was built on.
    """
    from physearth.corpus import digest as paper_digest
    from physearth.research import sheet, templates

    project = (session or {}).get("research") or {}
    plan = project.get("plan") or {}
    lines = [
        "Basis of the report: the approved plan v%03d, the paper's key statements below, the "
        "generated figures and the recorded runs. Reopen a paper section only to check a detail."
        % int(project.get("plan_version") or 1),
        "Question: %s" % (plan.get("question") or project.get("question") or ""),
    ]
    if plan.get("hypothesis"):
        lines.append("Hypothesis: %s" % plan["hypothesis"])
    findings = [
        "- [%s] %s" % (item.get("evidence_ref"), item.get("finding"))
        for item in plan.get("literature_evidence") or ()
        if isinstance(item, dict) and item.get("finding") and item.get("evidence_ref")
    ]
    digested = ["- " + line for line in paper_digest.lines(session)]
    lines.append("What the paper states (the session's digest of it, and the plan's findings):")
    lines += (digested + findings) or ["- (nothing recorded; read the paper with read_paper_digest)"]
    built = sheet.build(plan)
    for group in built["groups"]:
        lines.append("Runs of %s v%s:" % (group["model"], group["version"]))
        lines.append("  same in every run: %s" % "; ".join(
            "%s = %s (%s%s)" % (c["label"], c["shown"], c["tag"], ", " + c["ref"] if c["ref"] else "")
            for c in group["conditions"]
        ))
        if group["sweep"]:
            lines.append("  swept: %s" % group["sweep"])
        for run in group["runs"]:
            lines.append("  %s: %s%s" % (
                run["id"],
                ", ".join("%s = %s" % (c["label"], sheet.fmt(run["values"].get(c["name"]))) for c in group["columns"]) or run["label"],
                "; " + run["sweep"] if run["sweep"] else "",
            ))
    for chart in plan.get("charts") or ():
        if isinstance(chart, dict):
            lines.append("Figure %s: %s, %s against %s%s" % (
                chart.get("id"), chart.get("label") or "", ", ".join(chart.get("ys") or [chart.get("y") or ""]),
                chart.get("x"), "" if chart.get("required", True) else " (optional)",
            ))
    if built["decisions"]:
        lines.append("Values chosen without a source in the paper: %s" % "; ".join(
            "%s = %s" % (d["label"], d.get("shown") or sheet.fmt(d["value"])) for d in built["decisions"]
        ))
    lines.append(templates.instructions(project))
    lines.append(
        "Order of work: run the planned runs, plot and review each planned figure, open the "
        "reporting guideline (read_research_guideline, topic research-reporting), then write "
        "the report in the layout above."
    )
    return "\n".join(lines)
