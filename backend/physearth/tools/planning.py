"""The research_plan tool: the model proposes, the harness disposes."""

from physearth import registry, research
from physearth.corpus import model_guidelines


def research_plan(
    action,
    question="",
    objective="",
    hypothesis="",
    steps=None,
    parameters=None,
    paper_conditions=None,
    condition_provenance=None,
    literature_evidence=None,
    reproduction_targets=None,
    selected_models=None,
    parameter_mapping=None,
    outputs=None,
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
    chart_id="",
    changes=None,
    note="",
    _session=None,
    **supplemental_metadata,
):
    if _session is None:
        return research._fail("research_plan requires a session.")
    if action in ("propose", "revise_plan"):
        # A direct research_plan call is itself the agent's generic research-mode
        # selection.  No paper/model-specific case is inferred here.
        _session["research_required"] = True
        if (
            research.is_reproduction_question(question)
            or literature_evidence
            or reproduction_targets
            or paper_conditions
            or condition_provenance
        ):
            _session.setdefault("research_context", {})["reproduction_case"] = "paper-reproduction"

    if action == "propose" and research.is_reproduction_question(question, _session):
        capability_review = _session.get("capability_review") or {}
        if capability_review.get("status") not in ("ready", "confirmed"):
            return research._fail(
                "A capability checkpoint is required before proposing a reproduction plan.",
                {
                    "error_code": "capability_review_required",
                    "source": "session.capability_review",
                    "expected": "ready or confirmed capability checkpoint",
                    "actual": capability_review.get("status") or "missing",
                    "repair": (
                        "Call research_capability_check after the paper/model resources are read. "
                        "If a required reference is unavailable, ask the user to confirm a partial scope."
                    ),
                    "blocking": True,
                    "capability_review": capability_review,
                },
            )

    def resource_gate():
        """Require data resources to be opened before a proposal can be accepted."""
        if action not in ("propose", "revise_plan"):
            return None
        if action == "revise_plan" and not runs:
            candidate_runs = (changes or {}).get("runs") or ((_session.get("research") or {}).get("plan") or {}).get("runs") or []
            candidate_runs = candidate_runs or ((_session.get("research_draft") or {}).get("proposal") or {}).get("runs") or []
        else:
            candidate_runs = runs or []
        candidate_models = selected_models or []
        if action == "revise_plan" and not candidate_models:
            candidate_models = (changes or {}).get("selected_models") or ((_session.get("research") or {}).get("plan") or {}).get("selected_models") or []
        model_names = {
            str(item.get("model") or "").strip()
            for item in candidate_runs
            if isinstance(item, dict)
        }
        model_names.update(
            str(item.get("model") or item.get("name") or "").strip()
            for item in candidate_models
            if isinstance(item, dict)
        )
        model_names = sorted(name for name in model_names if name)
        # Let the normal validator explain an empty/malformed draft.  Resource gating is
        # for an otherwise executable proposal and must not hide its structural error.
        if not model_names:
            return None
        if "research-planning" not in set(_session.get("research_guidelines_read") or ()):
            return {
                "error_code": "research_guideline_read_required",
                "message": "Read the research guideline with read_research_guideline before proposing executable research.",
                "repair_hints": ["Call read_research_guideline(topic='planning'), then submit the complete proposal again."],
            }
        missing_models = []
        missing_instructions = []
        for model_name in model_names:
            entry, _canonical = registry.resolve(model_name, _session)
            instruction = model_guidelines.read(entry.name, entry.card, _session) if entry else None
            version = instruction.get("version", "1.0") if instruction else "?"
            key = "%s@%s" % (model_name, version)
            inspected_key = "%s@%s" % (model_name, entry.card.get("version") if entry else "?")
            if inspected_key not in set(_session.get("models_inspected") or ()):
                missing_models.append("%s (call list_models first)" % inspected_key)
            if key not in set(_session.get("model_instructions_read") or ()):
                missing_models.append(key)
                missing_instructions.append({"model": model_name, "version": version})
        if missing_models:
            return {
                "error_code": "model_instruction_read_required",
                "missing_models": missing_models,
                "required_resources": {
                    "list_models": [
                        {"model": model_name}
                        for model_name in model_names
                        if "%s@%s (call list_models first)" % (
                            model_name,
                            (registry.get(model_name, _session).card.get("version")
                             if registry.get(model_name, _session) else "?"),
                        ) in missing_models
                    ],
                    "read_model_instruction": missing_instructions,
                },
                "message": "Read every selected model instruction before proposing: %s." % ", ".join(missing_models),
                "repair_hints": ["Call list_models for each selected model, then read_model_instruction(model=...) and resubmit the complete proposal."],
            }
        return None

    gate = resource_gate()
    if gate and action in ("propose", "revise_plan"):
        draft = {
            "question": question,
            "objective": objective,
            "hypothesis": hypothesis,
            "steps": list(steps or []),
            "parameters": dict(parameters or {}),
            "paper_conditions": dict(paper_conditions or {}),
            "condition_provenance": dict(condition_provenance or {}),
            "literature_evidence": list(literature_evidence or []),
            "reproduction_targets": list(reproduction_targets or []),
            "selected_models": list(selected_models or []),
            "parameter_mapping": list(parameter_mapping or []),
            "outputs": list(outputs or []),
            "runs": list(runs or []),
            "charts": list(charts or []),
            "success_criteria": list(success_criteria or []),
            "assumptions": list(assumptions or []),
            "limitations": list(limitations or []),
            "quantities": list(quantities or []),
            "controls": list(controls or []),
            "metrics": list(metrics or []),
            "diagnostics": list(diagnostics or []),
            "stop_conditions": list(stop_conditions or []),
            "baseline_run_id": baseline_run_id,
        }
        if action == "revise_plan" and not draft["question"]:
            retained = ((_session.get("research_draft") or {}).get("proposal") or {})
            current = ((_session.get("research") or {}).get("plan") or {})
            base = {**retained, **current}
            for key, value in (changes or {}).items():
                if value is not None:
                    base[key] = value
            draft = {**base, **{key: value for key, value in draft.items() if value}}
        proposal_result = research.propose(
            _session,
            draft.get("question", ""), draft.get("objective", ""), draft.get("hypothesis", ""),
            draft.get("steps"), draft.get("parameters"), draft.get("runs"), draft.get("charts"),
            draft.get("success_criteria"), draft.get("assumptions"), draft.get("limitations"),
            draft.get("quantities"), draft.get("controls"), draft.get("metrics"),
            draft.get("diagnostics"), draft.get("stop_conditions"), draft.get("baseline_run_id", ""),
            paper_conditions=draft.get("paper_conditions"),
            condition_provenance=draft.get("condition_provenance"),
            literature_evidence=draft.get("literature_evidence"),
            reproduction_targets=draft.get("reproduction_targets"),
            selected_models=draft.get("selected_models"),
            parameter_mapping=draft.get("parameter_mapping"),
            outputs=draft.get("outputs"),
        )
        if _session.get("research"):
            _session["research"]["plan"]["resource_gate"] = gate
            if supplemental_metadata:
                _session["research"]["plan"]["supplemental_metadata"] = {
                    str(key): value for key, value in supplemental_metadata.items()
                }
        _session["research_draft"] = {"proposal": draft, "error": gate["message"], "data": gate}
        response = research._needs(gate["message"], {**gate, "proposal": (proposal_result.get("data") if proposal_result else None)})
        return response

    def propose_with_recovery_draft():
        draft = {
            "question": question,
            "objective": objective,
            "hypothesis": hypothesis,
            "steps": list(steps or []),
        "parameters": dict(parameters or {}),
        "paper_conditions": dict(paper_conditions or {}),
        "condition_provenance": dict(condition_provenance or {}),
        "literature_evidence": list(literature_evidence or []),
        "reproduction_targets": list(reproduction_targets or []),
        "selected_models": list(selected_models or []),
        "parameter_mapping": list(parameter_mapping or []),
        "outputs": list(outputs or []),
        "runs": list(runs or []),
            "charts": list(charts or []),
            "success_criteria": list(success_criteria or []),
            "assumptions": list(assumptions or []),
            "limitations": list(limitations or []),
            "quantities": list(quantities or []),
            "controls": list(controls or []),
            "metrics": list(metrics or []),
            "diagnostics": list(diagnostics or []),
            "stop_conditions": list(stop_conditions or []),
            "baseline_run_id": baseline_run_id,
        }
        result = research.propose(
            _session, question, objective, hypothesis, steps, parameters, runs, charts,
            success_criteria, assumptions, limitations, quantities, controls, metrics,
            diagnostics, stop_conditions, baseline_run_id,
            paper_conditions=paper_conditions,
            condition_provenance=condition_provenance,
            literature_evidence=literature_evidence,
            reproduction_targets=reproduction_targets,
            selected_models=selected_models,
            parameter_mapping=parameter_mapping,
            outputs=outputs,
        )
        if result.get("status") in ("success", "needs_input") and _session.get("research"):
            if supplemental_metadata:
                # Some OpenAI-compatible providers emit useful protocol annotations such
                # as ``units`` or ``variables`` even when they are not part of the strict
                # function schema.  They must not bypass validation, but neither should
                # they crash an otherwise complete plan before validation starts.
                _session["research"]["plan"]["supplemental_metadata"] = {
                    str(key): value for key, value in supplemental_metadata.items()
                }
            _session.pop("research_draft", None)
        else:
            _session["research_draft"] = {
                "proposal": draft,
                "error": result.get("error") or result.get("summary"),
                "data": dict(result.get("data") or {}),
            }
            result.setdefault("data", {})["recovery"] = (
                "The rejected proposal is retained. Submit a corrected complete proposal; "
                "research_plan(action='status') can retrieve its structured failure context."
            )
        return result

    def status_with_draft():
        if _session.get("research"):
            return research.status(_session)
        draft = _session.get("research_draft")
        if draft:
            return research._needs(
                "No approved proposal exists yet; the most recent rejected draft and validation error are retained.",
                {"phase": "draft_recovery", **draft},
            )
        return research.status(_session)

    def revise_with_recovery_draft():
        """Revise a rejected proposal without requiring an approved project first.

        Providers commonly respond to a validation error with ``revise_plan``.  Before
        approval there is no ``session['research']`` yet, so routing that action through
        ``research.revise`` used to discard an otherwise complete retained proposal and
        trigger repeated full-plan regeneration.  Merge the supplied fields into the
        retained proposal and run the normal proposal validator again instead.
        """
        if _session.get("research"):
            return research.revise(_session, changes, note)
        retained = (_session.get("research_draft") or {}).get("proposal")
        if not retained:
            return research._fail("No LLM-authored research proposal exists yet.")
        corrected = dict(retained)
        supplied = dict(changes or {})
        for key, value in supplied.items():
            if key == "parameters" and isinstance(value, dict):
                corrected[key] = {**dict(corrected.get(key) or {}), **value}
            elif value is not None:
                corrected[key] = value
        return research_plan(action="propose", _session=_session, **corrected)

    handlers = {
        "propose": propose_with_recovery_draft,
        "status": status_with_draft,
        "revise_plan": revise_with_recovery_draft,
        "preview": lambda: research.pseudo_preview(_session),
        "choose_chart": lambda: research.choose_chart(_session, chart_id),
        "complete": lambda: research.complete(_session),
    }
    handler = handlers.get(action)
    if handler is None:
        return research._fail("Unknown research_plan action %r." % action)
    try:
        return handler()
    except ValueError as exc:
        return research._fail(str(exc))
