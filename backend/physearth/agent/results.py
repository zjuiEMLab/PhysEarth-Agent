"""Reading a tool result back into session state, and what the trace says about it."""

from physearth import artifacts
from physearth import session as session_state
from physearth.agent.trace import _event


def _handle_line(name, data):
    """One line describing a stored result, for the session's `already held` block."""
    if name in ("run_model", "run_planned_model"):
        axis = data.get("axis") or {}
        span = (
            "%d points over %s" % (data.get("n_points", 0), axis["name"])
            if axis.get("name")
            else "%d point(s)" % data.get("n_points", 0)
        )
        return "%s@%s, %s, columns %s" % (
            data.get("model"),
            data.get("version"),
            span,
            ", ".join(sorted(data.get("series_summary") or {})) or "none",
        )
    return "measured %s, %d row(s), columns %s" % (
        data.get("dataset"),
        data.get("n_rows", 0),
        ", ".join(sorted(data.get("summary") or {})) or "none",
    )


def _allowed_marker_correction(state, unresolved):
    """A strict citation whitelist for a from-scratch report rewrite."""
    allowed = []
    allowed.extend("[%s]" % key for key in sorted(state.get("sections_read") or ()))
    allowed.extend("[model:%s]" % key for key in sorted(state.get("models_run") or ()))
    allowed.extend("[data:%s]" % key for key in sorted(state.get("datasets_read") or ()))
    allowed.extend("[skill:%s]" % key for key in sorted(state.get("skills_read") or ()))
    allowed.extend("[abs:%s]" % key for key in sorted(state.get("abstracts_seen") or ()))
    allowed.extend("[guideline:%s]" % key for key in sorted(state.get("guidelines_read") or ()))
    allowed.extend("[figure:%s]" % key for key in sorted(state.get("paper_figures_read") or ()))
    return (
        "Rewrite the entire report from scratch. The previous draft is discarded. Invalid "
        "markers were: %s. The complete marker whitelist for this conversation is: %s. "
        "Use only markers in that whitelist; it is also valid to make a clearly labelled "
        "interpretation without a marker. Do not invent paper sections, datasets, skills, or "
        "model names, and remove any factual claim that depended only on an invalid marker."
        % (", ".join(unresolved) or "unknown", ", ".join(allowed) or "none")
    )


def _record_tool_result(name, result, state, events):
    for key in result.get("citations", []):
        state["sections_read"].add(key)
    data = result.get("data") or {}
    session = state.get("session") or {}
    context = session.setdefault("research_context", {})
    if name == "list_models" and result["status"] == "success" and data.get("name"):
        context.setdefault("capabilities", {})[data["name"]] = {
            "name": data.get("name"),
            "version": data.get("version"),
            "runnable_here": data.get("runnable_here"),
            "tier": data.get("tier"),
            "outputs": list((data.get("outputs") or {}).keys())
            if isinstance(data.get("outputs"), dict)
            else list(data.get("outputs") or []),
            "instruction_available": data.get("instruction_available"),
            "instruction_version": data.get("instruction_version"),
            "parameters": sorted((data.get("parameters") or {}).keys()),
            "parameter_options": {
                key: list(spec.get("enum") or [])
                for key, spec in (data.get("parameters") or {}).items()
                if isinstance(spec, dict) and spec.get("enum")
            },
            "combinations": list(data.get("combinations") or []),
        }
    if name == "read_model_instruction" and result["status"] == "success" and data.get("model"):
        context.setdefault("instructions", {})[data["model"]] = {
            "version": data.get("version") or "1.0",
            "instruction_id": data.get("instruction_id") or data["model"],
        }
    if name == "read_literature" and result["status"] == "success" and data.get("section_id"):
        context.setdefault("sections", []).append(
            "%s#%s" % (data.get("slug"), data.get("section_id"))
        )
        context.setdefault("paper_evidence", []).append(
            {
                "kind": "section",
                "reference": "%s#%s" % (data.get("slug"), data.get("section_id")),
                "title": data.get("title", ""),
            }
        )
        context["paper_session"] = {
            "paper": data.get("slug"),
            "title": data.get("title"),
            "doi": data.get("doi", ""),
            "source_section": "%s#%s" % (data.get("slug"), data.get("section_id")),
            "paper_section": data.get("title", ""),
        }
    if name == "read_literature" and result["status"] == "success" and data.get("section_id"):
        if data.get("source") == "skill":
            state["skills_read"].add(data["slug"])
            events.append(
                _event(
                    "protocol",
                    rule="skill_followed",
                    detail="%s is now open, so [skill:%s] resolves in this answer."
                    % (data["slug"], data["slug"]),
                )
            )
    if name == "read_research_guideline" and result["status"] == "success":
        guideline_id = data.get("guideline_id") or "research-planning"
        state.setdefault("research_guidelines_read", set()).add(guideline_id)
        state.setdefault("skills_read", set()).add(guideline_id)
    if name == "read_model_instruction" and result["status"] == "success":
        model = data.get("model")
        version = data.get("version")
        if model:
            context.setdefault("instructions", {})[model] = {
                "version": version or "1.0",
                "instruction_id": data.get("instruction_id") or model,
            }
            state.setdefault("model_instructions_read", set()).add(
                "%s@%s" % (model, version or "1.0")
            )
            state.setdefault("guidelines_read", set()).add(
                "%s@%s" % (model, version or "1.0")
            )
    if name == "read_paper_figure" and result["status"] == "success":
        key = data.get("citation_key")
        if key:
            state.setdefault("paper_figures_read", set()).add(key.replace("#fig-", "#"))
            context.setdefault("paper_evidence", []).append(
                {
                    "kind": "figure",
                    "reference": key.replace("#fig-", "#"),
                    "paper": data.get("paper"),
                    "figure": (data.get("figure") or {}).get("id"),
                    "caption": (data.get("figure") or {}).get("caption", ""),
                }
            )
    if name == "inspect_paper_figure" and result["status"] == "success":
        key = data.get("citation_key")
        if key:
            state.setdefault("paper_figures_inspected", set()).add(key.replace("#fig-", "#"))
            context.setdefault("paper_evidence", []).append(
                {
                    "kind": "figure_inspection",
                    "reference": key,
                    "paper": data.get("paper"),
                    "figure": data.get("figure_id"),
                    "analysis_status": data.get("analysis_status"),
                    "visual_observations": data.get("visual_observations") or {},
                }
            )
    if name == "discover_literature" and result["status"] == "success":
        for item in data.get("candidates") or []:
            state["abstracts_seen"].add(item["doi"])
        events.append(
            _event(
                "literature_tier",
                rule="abstract_level",
                detail="%d candidate(s) recorded at abstract level; none of them is full text."
                % len(data.get("candidates") or []),
            )
        )
    if name == "ingest_paper" and result["status"] == "success" and data.get("fetched_from"):
        events.append(
            _event(
                "literature_tier",
                rule="session_full_text",
                detail="%s arrived from %s as %s, %d section(s), licensed %s."
                % (
                    data["doi"],
                    data["fetched_from"],
                    data["slug"],
                    len(data.get("sections") or []),
                    data.get("license") or "unknown",
                ),
            )
        )
    if name == "list_models" and result["status"] == "success":
        if data.get("version"):
            state["models_run"].add("%s@%s" % (data["name"], data["version"]))
        for row in data.get("models") or []:
            state["models_run"].add("%s@%s" % (row["name"], row["version"]))
    for finding in data.get("external_source_findings") or []:
        session_state.bump(state, "boundary_flags")
        events.append(
            _event(
                "untrusted_content",
                rule="external_source_boundary",
                detail="%s: %s" % (finding["kind"], finding["excerpt"]),
            )
        )
    if name == "read_reference_dataset" and result["status"] == "success":
        if data.get("dataset"):
            state["datasets_read"].add(data["dataset"])
        for row in data.get("datasets") or []:
            state["datasets_read"].add(row["slug"])
    if name in ("run_model", "run_planned_model"):
        if result["status"] == "success":
            if not data.get("reused"):
                session_state.bump(state, "model_runs")
            state["models_run"].add("%s@%s" % (data["model"], data["version"]))
            # A cached physical result still fulfils the *current* planned run.  Previously
            # reused results were deliberately not counted as new computations, but their
            # planned_run_id was never registered either.  execution_gaps then requested the
            # same run forever: run -> reuse -> still missing.  Store one lightweight plan
            # association per run ID while keeping model_runs limited to real executions.
            successful = state["session"].setdefault("successful_runs", [])
            record = {
                "model": data["model"],
                "spec": dict(data.get("spec") or {}),
                "handle": data.get("handle"),
                "planned_run_id": data.get("planned_run_id"),
            }
            if not any(
                item.get("model") == record["model"]
                and item.get("spec") == record["spec"]
                and item.get("handle") == record["handle"]
                and item.get("planned_run_id") == record["planned_run_id"]
                for item in successful
            ):
                successful.append(record)
            planned_id = data.get("planned_run_id")
            if planned_id:
                state["session"]["failed_runs"] = [
                    item for item in state["session"].setdefault("failed_runs", [])
                    if item.get("run_id") != planned_id
                    or item.get("spec") != dict(data.get("spec") or {})
                ]
            if result.get("qc") and not result["qc"]["passed"]:
                session_state.bump(state, "qc_failures")
        elif result["status"] == "needs_input":
            session_state.bump(state, "rejected_calls")
        elif name == "run_planned_model" and data.get("planned_run_id"):
            failures = state["session"].setdefault("failed_runs", [])
            run_id = data["planned_run_id"]
            spec = dict(data.get("spec") or {})
            previous = next(
                (
                    item for item in failures
                    if item.get("run_id") == run_id and item.get("spec") == spec
                ),
                None,
            )
            if previous is None:
                previous = {"run_id": run_id, "spec": spec, "attempts": 0}
                failures.append(previous)
            previous.update(
                attempts=int(previous.get("attempts", 0)) + 1,
                model=data.get("model"),
                error_code=data.get("error_code") or "model_execution_error",
                recoverable=bool(data.get("recoverable")),
                repair_hints=list(data.get("repair_hints") or []),
                error=result.get("error") or result.get("summary"),
            )
    if data.get("handle") and result["status"] == "success":
        session_state.remember_handle(state, data["handle"], _handle_line(name, data))
    if name in ("plot", "plot_planned_chart") and result["status"] == "success":
        figure = (result.get("ui") or {})["figure"]
        session_state.remember_figure(state, figure)
        session = state.get("session") or {}
        if not session.get("ephemeral"):
            try:
                artifacts.persist_figure(
                    session.get("id") or "shared",
                    (session.get("research") or {}).get("research_id") or session.get("id") or "shared",
                    figure.get("figure_number") or 1,
                    figure,
                )
            except (OSError, ValueError):
                pass
