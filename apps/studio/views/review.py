"""The approval bar: what the human is being asked to approve, and in what words."""

from apps.studio.views.parts import (
    _mapping_text,
)
from apps.studio.views.text import _e
from physearth.api import research


def _revision_changes_html(summary):
    """What the last revision changed, as sentences; never the raw field values."""
    if not summary:
        return ""
    readable = summary.get("readable")
    if readable is None:
        # A summary written before readable diffs existed: name the fields only.
        readable = [
            {"kind": kind, "text": str(item.get("field") or "field")}
            for kind in ("changed", "added", "removed")
            for item in summary.get(kind) or []
        ]
    words = {"added": "Added", "removed": "Removed", "changed": "Changed"}
    items = "".join(
        "<li><span class='research-plan-change__kind research-plan-change__kind--%s'>%s</span> %s</li>"
        % (_e(item["kind"]), words.get(item["kind"], "Changed"), _e(item["text"]))
        for item in readable
    )
    return (
        "<section class='research-plan-revision'>"
        "<div class='research-context__label'>WHAT CHANGED · v%03d → v%03d</div>"
        "%s<div class='research-plan-revision__meta'>The layout preview and any figure "
        "selection were cleared.</div></section>"
        % (
            summary.get("from_version", 0), summary.get("to_version", 0),
            "<ul>%s</ul>" % items if items else "<p>Nothing a run or figure depends on changed.</p>",
        )
    )


_SWEEP_KEYS = ("sweep_parameter", "sweep_start", "sweep_stop", "sweep_points")


def _run_parameters(run):
    return run.get("resolved_parameters") or run.get("parameters") or {}


def _run_configuration(run):
    """What identifies the run's algorithm, with the swept axis removed."""
    parameters = _run_parameters(run)
    swept = str(parameters.get("sweep_parameter") or "none")
    return {
        key: value
        for key, value in parameters.items()
        if key not in _SWEEP_KEYS and key != swept
    }


def _algorithm_summary(runs, versions):
    if not runs:
        return "No model run is planned yet."
    models = sorted({str(run.get("model") or "") for run in runs} - {""})
    named = ", ".join(
        "%s%s" % (model, " v%s" % versions[model] if versions.get(model) else "")
        for model in models
    )
    configurations = [_run_configuration(run) for run in runs]
    shared_keys = sorted(
        key
        for key in set().union(*configurations)
        if all(item.get(key) == configurations[0].get(key) for item in configurations)
    )
    varying_keys = sorted(set().union(*configurations) - set(shared_keys))
    text = "Run %s: %d run(s)." % (named or "the selected model", len(runs))
    if varying_keys:
        variants = "; ".join(
            "%s = %s"
            % (
                run.get("id") or run.get("label") or "run",
                " + ".join("%s" % _run_configuration(run).get(key) for key in varying_keys),
            )
            for run in runs
        )
        text += (
            " Compared by %s -- %s." % (", ".join(varying_keys), variants)
            if len(runs) > 1
            else " Configuration: %s." % variants
        )
    elif len(runs) > 1:
        text += " Every run uses the same configuration."
    return text


def _changing_variables(runs):
    sweeps = []
    for run in runs:
        parameters = _run_parameters(run)
        swept = str(parameters.get("sweep_parameter") or "none")
        if swept in ("", "none"):
            continue
        descriptor = "%s from %s to %s over %s point(s)" % (
            swept,
            parameters.get("sweep_start"),
            parameters.get("sweep_stop"),
            parameters.get("sweep_points"),
        )
        if descriptor not in sweeps:
            sweeps.append(descriptor)
    if not sweeps:
        return "No variable is swept; every run holds its conditions fixed."
    return "; ".join(sweeps)


def _key_output(plan, runs):
    outputs = [str(item) for item in plan.get("outputs") or [] if item]
    quantities = [str(item) for item in plan.get("quantities") or [] if item]
    requested = sorted(
        {str(_run_parameters(run).get("output") or "") for run in runs} - {""}
    )
    named = outputs or quantities
    text = ", ".join(named) if named else "not declared"
    if requested:
        text += " (model output group: %s)" % ", ".join(requested)
    return text


def _figure_descriptions(charts):
    if not charts:
        return ["No figure is planned yet."]
    described = []
    for chart in charts:
        ys = ", ".join(chart.get("ys") or [chart.get("y") or ""]) or "not declared"
        described.append(
            "%s: %s against %s (%s, %s)"
            % (
                chart.get("label") or chart.get("id") or "figure",
                ys,
                chart.get("x") or "not declared",
                chart.get("kind") or "chart",
                "required" if chart.get("required", True) else "optional",
            )
        )
    return described


def _execution_steps_html(plan):
    """Describe the execution the current plan actually specifies.

    This used to print the free-text steps the model wrote when it first proposed. Those
    are authored once, so a revision that changed the runs left the steps describing the
    superseded plan, and they never said which model would run. Deriving them from the
    plan keeps them true after every revision by construction.
    """
    runs = [run for run in plan.get("runs") or [] if isinstance(run, dict)]
    charts = [chart for chart in plan.get("charts") or [] if isinstance(chart, dict)]
    versions = {
        str(item.get("model") or ""): str(item.get("version") or "")
        for item in plan.get("selected_models") or []
        if isinstance(item, dict)
    }
    figures = _figure_descriptions(charts)
    items = [
        ("Model run", _algorithm_summary(runs, versions)),
        ("Changing variables", _changing_variables(runs)),
        ("Key output", _key_output(plan, runs)),
        (
            "Figures",
            figures[0] if len(figures) == 1 else "%d figures -- %s" % (len(figures), "; ".join(figures)),
        ),
    ]
    return "<ol class='research-steps'>%s</ol>" % "".join(
        "<li><b>%s.</b> %s</li>" % (_e(label), _e(text)) for label, text in items
    )


def _chat_commands_html(phase):
    """What to type, since a research plan is approved in Conversation, not with a button."""
    if phase in ("plan_review", "plan_approved"):
        items = (
            "<li><code>approve</code> runs the plan as written and draws its required figures.</li>"
            "<li><code>preview</code> first draws the planned figures from pseudo-data, to check the layout.</li>"
            "<li>Anything else is a change to the plan, e.g. <i>change the density range to 10-500 kg/m3</i> "
            "or <i>drop the optional chart</i>. A new version comes back for review.</li>"
            "<li><code>protocol</code> gives you the generated protocol file, if you need it.</li>"
        )
    else:
        items = (
            "<li><code>approve</code> runs the registered models and draws the confirmed figures.</li>"
            "<li>Anything else is a change to the plan, and returns it to review as a new version.</li>"
        )
    return (
        "<div class='chat-commands'><b>Reply in Conversation to continue.</b>"
        "<ul>%s</ul>Only a message that is just the word acts as a command; "
        "<i>approve, but ...</i> is read as a change.</div>" % items
    )


def _structured_approval_bar(session, project, research):
    """The plan as it appears in Conversation: what it is, what to type, and a link.

    The plan itself is a page of its own (views/exports.py). A plan laid out inside the
    narrow conversation column was too wide to read and too long to scroll past; here it is
    summarised in a few lines, with the decisions that need the reviewer's attention.
    """
    plan = project.get("plan") or {}
    phase = project.get("phase", "plan_review")
    version = int(project.get("plan_version") or 1)
    phase_labels = {
        "plan_review": "waiting for your review",
        "plan_approved": "approved for a layout preview",
        "pseudo_preview": "layout preview ready",
        "chart_selected": "figures confirmed",
    }
    sheet = research.sheet.build(plan)
    models = "; ".join(
        "%s%s · %d run%s" % (
            group["model"], " v%s" % group["version"] if group["version"] else "",
            len(group["runs"]), "" if len(group["runs"]) == 1 else "s",
        )
        for group in sheet["groups"]
    ) or "no runs"
    charts = [c for c in plan.get("charts") or [] if isinstance(c, dict)]
    figures = "; ".join(
        "%s%s" % (c.get("label") or c.get("id"), "" if c.get("required", True) else " (optional)")
        for c in charts
    ) or "none"
    decisions = sheet["decisions"]
    decide_html = (
        "<div class='research-card__decide'><b>%d value%s chosen without a source in the paper:</b> %s. "
        "Check them in the plan.</div>"
        % (
            len(decisions), "" if len(decisions) == 1 else "s",
            _e(", ".join(
                "%s = %s" % (d.get("label") or d["name"], d.get("shown") or research.sheet.fmt(d["value"]))
                for d in decisions[:6]
            ) + (" and %d more" % (len(decisions) - 6) if len(decisions) > 6 else "")),
        )
        if decisions else ""
    )
    export = project.get("plan_export") or {}
    links = (
        "<div class='plan-downloads'><a href='%s' target='_blank' rel='noopener'>Open the plan</a>"
        "<a href='%s' download='research-plan-v%03d.html'>Download (HTML)</a></div>"
        % (_e(export["url"]), _e(export["url"]), version)
        if export.get("url") and export.get("version") == version
        else ""
    )
    chart_buttons = ""
    if phase == "pseudo_preview":
        chart_buttons = (
            "<div class='approve__note'><b>%s.</b> The layout preview is in Evidence → Figures. "
            "Pseudo-data are deterministic layout demonstrations, not model results.</div>"
            % _e((project.get("pseudo") or {}).get("label") or "PSEUDO-DATA · demonstration only")
        )
        selected = set(project.get("selected_charts") or [])
        chart_buttons += (
            "<div class='approve__note'><b>Figures to run</b> (required ones are always included):</div>"
            "<div class='approve__charts'>%s</div>"
            % "".join(
                "<button type='button' class='approve__chart%s' data-chart-id='%s' data-required='%s'>"
                "%s <span>(%s against %s%s)</span></button>"
                % (
                    " is-selected" if c.get("id") in selected else "", _e(c.get("id")),
                    "true" if c.get("required", True) else "false", _e(c.get("label") or c.get("id")),
                    _e(", ".join(c.get("ys") or [c.get("y") or ""])), _e(c.get("x")),
                    "" if c.get("required", True) else ", optional",
                )
                for c in charts
            )
        )
    return (
        "<div class='research-plan-details research-card' data-key='research-plan'>"
        "<div class='approve approve--research' data-research-phase='%s' data-selected-count='%d' "
        "data-run-count='%d' data-chart-count='%d'>"
        "<div class='approve__head'>Research plan <b>v%03d</b> · %s</div>"
        "<div class='research-card__facts'><div><b>Question.</b> %s</div>"
        "<div><b>Runs.</b> %s</div><div><b>Figures.</b> %s</div></div>"
        "%s%s%s%s%s</div></div>"
        % (
            _e(phase), len(project.get("selected_charts") or []), len(plan.get("runs") or []), len(charts),
            version, _e(phase_labels.get(phase, phase)),
            _e(plan.get("question") or project.get("question") or ""), _e(models), _e(figures),
            "",  # what changed is the reply above the card, and on the plan page
            decide_html, _chat_commands_html(phase), links, chart_buttons,
        )
    )


def approval_bar(session):
    """Render either the research review card or the physical-run approval gate."""
    from physearth.api import approval as gate

    project = (session or {}).get("research") or {}
    if project and project.get("phase") not in ("approved", "completed"):
        return _structured_approval_bar(session, project, research)
    if project and project.get("phase") not in ("approved", "completed"):
        plan = project.get("plan") or {}
        phase = project.get("phase", "plan_review")
        phase_labels = {
            "plan_review": "Review and revise the plan",
            "plan_approved": "Plan approved for preview",
            "pseudo_preview": "Review pseudo-data layout",
            "chart_selected": "Review final figure package",
        }
        phase_label = phase_labels.get(phase, phase)
        phase_index = {
            "plan_review": 0,
            "plan_approved": 1,
            "pseudo_preview": 2,
            "chart_selected": 3,
        }.get(phase, 0)
        flow_html = (
            "<div class='research-flow'><b>Research plan flow</b>"
            + "".join(
                "<span class='research-flow__step%s'>%d. %s</span>"
                % (" is-current" if index == phase_index else "", index + 1, label)
                for index, label in enumerate(
                    ("Review plan", "Preview layout", "Confirm figures", "Approve execution", "Run real model")
                )
            )
            + "</div>"
        )
        review_guidance = {
            "plan_review": (
                "Approve plan reviews the method, variables, runs, and acceptance criteria. "
                "It does not approve pseudo-data or a final scientific figure."
            ),
            "plan_approved": (
                "The plan is approved only far enough to generate a display-only preview. "
                "No physical model call has been authorized."
            ),
            "pseudo_preview": (
                "Pseudo-data are deterministic layout demonstrations, not model results. "
                "If the axes, range, variables, or figure design are wrong, choose "
                "'Revise plan in chat' and describe the change."
            ),
            "chart_selected": (
                "The selected figure package is ready for final execution approval. "
                "Changing it requires a new plan revision."
            ),
        }.get(phase, "Review the current research decision before continuing.")
        revision_html = (
            "<div class='approve__note approve__note--guide'><b>How to edit this plan:</b> "
            "use Conversation to state the change, for example: "
            "'remove the optional chart', 'change the density range to 10-500 kg/m3', "
            "or 'plot tb_v and tb_h against angle'. The agent records a new plan version, "
            "clears stale pseudo-data, and returns the plan to review.</div>"
        )
        steps = "".join(
            "<li>%s</li>" % _e(step) for step in (plan.get("steps") or [])
        )
        protocol_fixed = plan.get("paper_conditions") or {}
        condition_provenance = plan.get("condition_provenance") or {}
        plan_parameters = plan.get("parameters") or {}
        agent_parameters = {
            key: value for key, value in plan_parameters.items() if key not in protocol_fixed
        }
        agent_assumptions = "; ".join(str(item) for item in plan.get("assumptions") or [])
        params = (
            "<div class='approve__p'><b>Paper reference tags (not model constraints):</b> %s</div>"
            "<div class='approve__p'><b>Paper tag evidence:</b> %s</div>"
            "<div class='approve__p'><b>User/model inputs:</b> %s</div>"
            "<div class='approve__p'><b>Agent assumptions:</b> %s</div>"
            % (
                _e(_mapping_text(protocol_fixed) or "not declared from the source yet"),
                _e(_mapping_text(condition_provenance) or "not declared"),
                _e(_mapping_text(agent_parameters) or "none outside the source conditions"),
                _e(agent_assumptions or "none declared"),
            )
        )
        evidence_items = plan.get("literature_evidence") or []
        evidence_html = (
            "<div class='approve__p'><b>Literature evidence:</b> %s</div>"
            % _e(
                "; ".join(
                    "%s (%s)" % (item.get("evidence_ref"), item.get("purpose", "source evidence"))
                    for item in evidence_items
                    if isinstance(item, dict) and item.get("evidence_ref")
                )
                or "not declared"
            )
        )
        target_items = plan.get("reproduction_targets") or []
        target_html = (
            "<div class='approve__p'><b>Reproduction targets:</b> %s</div>"
            % _e(
                "; ".join(
                    "%s %s:%s [%s] -> runs=%s charts=%s%s"
                    % (
                        item.get("id"), item.get("source_type"), item.get("source_id"),
                        item.get("status", "planned"),
                        ",".join(item.get("run_ids") or []) or "none",
                        ",".join(item.get("chart_ids") or []) or "none",
                        " (%s)" % item.get("availability_reason") if item.get("availability_reason") else "",
                    )
                    for item in target_items
                    if isinstance(item, dict)
                )
                or "none"
            )
        )
        mapping_items = plan.get("parameter_mapping") or []
        mapping_html = (
            "<div class='approve__p'><b>Paper-to-model mapping:</b> %s</div>"
            % _e(
                "; ".join(
                    "%s (%s) -> %s=%s [%s, confidence=%s]"
                    % (
                        item.get("paper_concept"), item.get("model") or "registered model",
                        item.get("model_input"), item.get("mapped_value"),
                        item.get("provenance_class"), item.get("confidence") or "unclassified",
                    )
                    for item in mapping_items
                    if isinstance(item, dict)
                )
                or "not declared"
            )
        )
        selected_model_items = plan.get("selected_models") or []
        models_html = (
            "<div class='approve__p'><b>Selected models:</b> %s</div>"
            % _e(
                "; ".join(
                    "%s (%s)" % (item.get("model"), item.get("purpose", "planned"))
                    for item in selected_model_items
                    if isinstance(item, dict)
                )
                or "not declared"
            )
        )
        gaps = plan.get("capability_gaps") or []
        scope_html = (
            "<div class='approve__note'><b>Expected outcome:</b> %s%s</div>"
            % (
                _e(plan.get("outcome_scope", "full")),
                _e(" — unavailable locally: " + ", ".join(gaps)) if gaps else "",
            )
        )
        repairs = plan.get("automatic_repairs") or []
        if repairs:
            scope_html += (
                "<div class='approve__note'><b>Proposed plan repairs — review required:</b> %s</div>"
                % _e(
                    "; ".join(
                        "%s.%s: %s -> %s (%s; source=%s; provenance=%s)"
                        % (
                            item.get("chart_id") or item.get("run_id") or "plan",
                            item.get("field"), item.get("from"),
                            item.get("to"), item.get("reason"),
                            item.get("source") or "workflow metadata",
                            item.get("provenance") or "unspecified",
                        )
                        for item in repairs
                    )
                )
            )
        recovery = project.get("recovery") or {}
        if recovery:
            proposed = recovery.get("repairs") or []
            scope_html += (
                "<div class='approve__note approve__note--warning'>"
                "<b>Recovery review required:</b> failed runs %s. %s</div>"
                % (
                    _e(", ".join(recovery.get("failed_run_ids") or []) or "unknown"),
                    _e(
                        "; ".join(
                            "%s: %s %s → %s"
                            % (
                                item.get("run_id"), item.get("field"),
                                item.get("from"), item.get("to"),
                            )
                            for item in proposed
                        )
                        or "No automatic physical change was applied; revise the plan in chat."
                    ),
                )
            )
        scope_html = (
            flow_html
            + "<div class='approve__note approve__note--guide'><b>Current stage:</b> %s. %s</div>"
            % (_e(phase_label), _e(review_guidance))
            + revision_html
            + evidence_html
            + target_html
            + models_html
            + mapping_html
            + scope_html
        )
        protocol_rows = "".join(
            "<div class='research-protocol__row'><b>%s</b><span>%s</span></div>"
            % (_e(label), _e("; ".join(plan.get(key) or []) or "not specified"))
            for key, label in (
                ("quantities", "Quantities"),
                ("controls", "Controls"),
                ("metrics", "Metrics"),
                ("diagnostics", "Diagnostics"),
                ("success_criteria", "Acceptance"),
                ("stop_conditions", "Stop conditions"),
                ("limitations", "Limitations"),
            )
        )
        protocol_rows += (
            "<div class='research-protocol__row'><b>Baseline</b><span>%s</span></div>"
            % _e(plan.get("baseline_run_id") or "not specified")
        )
        generated_protocol_html = (
            "<details class='research-protocol-yaml'><summary>Generated protocol.yaml "
            "(session draft, plan v%03d)</summary><pre>%s</pre>"
            "<p class='approve__note'>This YAML is generated from the current agent plan. "
            "Edit it by describing changes in Conversation; the agent will create a new "
            "version through research_plan(action='revise_plan').</p></details>"
            % (project.get("plan_version", 1), _e(research.protocol_yaml(project)))
        )
        pseudo = project.get("pseudo") or {}
        pseudo_rows = pseudo.get("points") or []
        pseudo_html = ""
        if pseudo_rows:
            keys = list(pseudo_rows[0])
            header = "".join("<th>%s</th>" % _e(key) for key in keys)
            rows = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % _e(row.get(key, "")) for key in keys)
                for row in pseudo_rows[:6]
            )
            pseudo_html = (
                "<div class='approve__note'><b>%s</b></div>"
                "<table class='research-preview'><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
                % (_e(pseudo.get("label", "PSEUDO-DATA — demonstration only")), header, rows)
            )
        selected_ids = set(project.get("selected_charts") or [])
        charts = "".join(
            "<button type='button' class='approve__chart%s' data-chart-id='%s' data-required='%s'%s>"
            "<b>[%s]</b> %s <span>(%s · %s: %s → %s%s)</span></button>"
            % (
                " is-selected" if item.get("id") in selected_ids else "",
                _e(item.get("id")),
                "true" if item.get("required", True) else "false",
                " disabled" if project.get("phase") != "pseudo_preview" else "",
                _e(item.get("id")),
                _e(item.get("label")),
                _e(item.get("purpose", "result")),
                _e(item.get("kind")),
                _e(item.get("x")),
                _e(", ".join(item.get("ys") or [item.get("y")])),
                " · required" if item.get("required", True) else " · optional",
            )
            for item in (plan.get("charts") or [])
        )
        evidence_count = len(plan.get("literature_evidence") or [])
        mapping_count = len(plan.get("parameter_mapping") or [])
        run_count = len(plan.get("runs") or [])
        chart_count = len(plan.get("charts") or [])
        validation_label = "evidence %d · mappings %d" % (evidence_count, mapping_count)
        return (
            "<details class='research-plan-details' data-key='research-plan'>"
            "<summary>Research plan · v%03d · %s</summary>"
            "<div class='approve approve--research' data-research-phase='%s' data-selected-count='%d' "
            "data-run-count='%d' data-chart-count='%d' data-validation='%s'>"
            "<div class='research-plan-summary'>%d runs · %d charts · %s</div>"
            "<div class='approve__head'>Research review · <b>%s</b> · plan v%03d</div>"
            "<div class='approve__note'>Phase: %s. No formal physical result is authorized yet.</div>"
            "<div class='research-question'><b>Question:</b> %s<br><b>Hypothesis:</b> %s</div>"
            "%s"
            "%s"
            "<div class='research-protocol'>%s</div>"
            "<ol class='research-steps'>%s</ol>"
            "<div class='approve__params'>%s</div>"
            "%s"
            "<div class='approve__note'><b>Chart options</b></div><div class='approve__charts'>%s</div>"
            "<div class='approve__note'>必需科研图已锁定；可勾选其他可选图。确认整个图组后再批准正式计算。</div>"
            "</div></details>"
            % (project.get("plan_version", 1), _e(phase_label), _e(project.get("phase")), len(selected_ids), run_count, chart_count, _e(validation_label), run_count, chart_count, _e(validation_label), _e(plan.get("title", "Research plan")), project.get("plan_version", 1),
               _e(project.get("phase")), _e(plan.get("question", "")), _e(plan.get("hypothesis", "")),
               scope_html, generated_protocol_html, protocol_rows, steps, params, pseudo_html, charts or "none")
        )

    waiting = gate.pending(session)
    if not waiting:
        return "<div class='approve' hidden></div>"
    described = waiting["description"]
    if described.get("code") is not None:
        return _script_approval(described)
    rows = "".join(
        "<span class='approve__p'><b>%s</b> %s</span>" % (_e(k), _e(v))
        for k, v in sorted(described["parameters"].items())
    )
    return (
        "<div class='approve'>"
        "<div class='approve__head'>Run <b>%s</b> as %s?</div>"
        "<div class='approve__params'>%s</div>"
        "<div class='approve__note'>The model cannot answer this for itself. Nothing runs "
        "until you approve it, and the agent waits as long as it takes. Asking a new question "
        "instead drops this request.</div>"
        "</div>"
        % (
            _e(described["model"]),
            _e(described["shape"]),
            rows or "<span class='approve__p'>every parameter at its declared default</span>",
        )
    )


def _script_approval(described):
    """A script is approved by reading it: show the code, what it will import and install."""
    report = described.get("inspection") or {}
    installs = ", ".join(report.get("requirements") or ())
    missing = ", ".join(report.get("missing") or ())
    notes = []
    if missing:
        notes.append(
            "<div class='approve__note'><b>Packages not installed:</b> %s. Approving also "
            "installs <b>%s</b> into a folder used only for this session.</div>"
            % (_e(missing), _e(installs or "(none named: the script will fail on the import)"))
        )
    return (
        "<div class='approve'>"
        "<div class='approve__head'>Run this script? <b>%s</b></div>"
        "<div class='approve__params'><span class='approve__p'>%s</span></div>"
        "<details open class='approve__code'><summary>Code (%s)</summary><pre>%s</pre></details>"
        "%s"
        "<div class='approve__note'>The script calls registered models through the usual checks. "
        "It runs in a separate process with a time limit and no network, and it is not a security "
        "boundary: read the code. Nothing runs until you approve it. Asking a new question "
        "instead drops this request.</div>"
        "</div>"
        % (
            _e(described.get("purpose") or ""),
            _e(described.get("shape") or ""),
            _e(report.get("sha256", "")[:12]),
            _e(described.get("code") or ""),
            "".join(notes),
        )
    )
