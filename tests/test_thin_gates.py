"""What stops a run, a plan or a report, and what only advises.

The gates that stay are the ones that protect the model contract and the evidence: a value the
model's declaration rejects, a sweep that cannot move its output, a chart its runs cannot draw, a
citation that does not resolve, one approval before a physical run. Everything else is shown to the
person with the plan or the report and does not send the agent round again.
"""

import copy
import json
from pathlib import Path

import pytest

from integrations.physearth import service
from physearth import session as session_state
from physearth import tools
from physearth.harness import gates

ROOT = Path(__file__).resolve().parent.parent
RECORD = (
    ROOT / "evaluation" / "results" / "competition" / "batch-2026-10-06"
    / "q1-sparse-medium__p1-reproduction-first__full__openai-gpt-5.6-luna__r1.json"
)
needs_record = pytest.mark.skipif(not RECORD.is_file(), reason="the recorded Q1 run is not present")


@pytest.fixture()
def reviewable(monkeypatch):
    project = json.loads(RECORD.read_text())["research"]

    def make(phase="plan_review"):
        sid = "ses_thin_%s" % phase
        monkeypatch.setitem(
            service._SESSIONS, sid,
            {"id": sid, "research": {**copy.deepcopy(project), "phase": phase, "review_log": []}},
        )
        return sid

    return make


# ── one approval before a run, in the plugin as in the Studio ───────────────────────────────
@needs_record
def test_one_approval_covers_the_plan_its_figures_and_their_execution(reviewable):
    sid = reviewable()
    result = service.review(sid, "approve")
    assert result["status"] == "success"
    assert service._SESSIONS[sid]["research"]["phase"] == "approved"


@needs_record
def test_approving_twice_is_ignored_not_an_error(reviewable):
    sid = reviewable()
    service.review(sid, "approve")
    again = service.review(sid, "approve")
    assert again["status"] == "success" and "already approved" in again["summary"]


@needs_record
def test_a_layout_preview_is_only_drawn_when_asked_for(reviewable):
    sid = reviewable()
    result = service.review(sid, "preview")
    assert service._SESSIONS[sid]["research"]["phase"] == "pseudo_preview"
    assert "pseudo-data" in result["summary"].lower()


@needs_record
@pytest.mark.parametrize("choice", ["reject", "regenerate"])
def test_rejecting_a_plan_points_to_revising_it(reviewable, choice):
    sid = reviewable()
    result = service.review(sid, choice)
    assert result["status"] == "needs_input" and result["error"] == "revise_instead"
    assert "physearth_plan_apply" in result["summary"]
    assert service._SESSIONS[sid]["research"]["phase"] == "plan_review"


def test_reviewing_before_a_plan_exists_says_so(monkeypatch):
    monkeypatch.setitem(service._SESSIONS, "ses_thin_none", {"id": "ses_thin_none"})
    result = service.review("ses_thin_none", "approve")
    assert result["status"] == "needs_input" and result["error"] == "no_research_plan"


# ── a report is sent back for evidence, not for wording ─────────────────────────────────────
def _failing(rule):
    return {"rule": rule, "passed": False, "reason": "the %s check says so" % rule}


@pytest.mark.parametrize("rule", sorted(gates.ADVISORY_RULES))
def test_an_advisory_rule_does_not_send_the_report_back(monkeypatch, rule):
    name = {
        "asked_value": "check_asked_value",
        "required_appendix": "check_required_appendix",
        "provenance_consistency": "check_provenance_consistency",
    }[rule]
    monkeypatch.setattr(gates, name, lambda text, state: _failing(rule))
    monkeypatch.setattr(gates, "correction", lambda check: "fix %s" % check["rule"])
    state = session_state.new_state(session_state.new_session("m"))
    check, correction = gates.review_final("A short answer.", state)
    assert correction is None, "%s sent the report back for a rewrite" % rule
    assert [item["rule"] for item in gates.advisory_findings("A short answer.", state)] == [rule]


def test_a_citation_that_does_not_resolve_still_sends_the_report_back():
    state = session_state.new_state(session_state.new_session("m"))
    check, correction = gates.review_final("Snow is cold [smrt-v1#99].", state)
    assert check["rule"] == "citation_integrity" and correction


def test_the_advisory_and_blocking_rules_do_not_overlap():
    assert gates.ADVISORY_RULES == {"asked_value", "required_appendix", "provenance_consistency"}
    assert not gates.ADVISORY_RULES & {"citation_integrity", "evidence_gate", "abstract_depth"}


def test_the_plugin_passes_a_report_with_notes_and_fails_one_without_evidence(monkeypatch):
    box = session_state.new_session("m")
    box["id"] = "ses_thin_report"
    monkeypatch.setitem(service._SESSIONS, "ses_thin_report", box)
    monkeypatch.setattr(
        gates, "final_checks",
        lambda text, state: [
            {"rule": "evidence_gate", "passed": True},
            {"rule": "citation_integrity", "passed": True},
            _failing("required_appendix"),
        ],
    )
    monkeypatch.setattr(gates, "correction", lambda check: "fix %s" % check["rule"])
    noted = service.verify_report("ses_thin_report", "text", mode="lint")
    assert noted["passed"] is True and noted["notes"] == ["fix required_appendix"]
    assert noted["summary"].startswith("Passed. Notes:") and noted["corrections"] == []

    monkeypatch.setattr(
        gates, "final_checks",
        lambda text, state: [_failing("citation_integrity"), _failing("required_appendix")],
    )
    failed = service.verify_report("ses_thin_report", "text", mode="lint")
    assert failed["passed"] is False
    assert failed["corrections"] == ["fix citation_integrity"]
    assert failed["notes"] == ["fix required_appendix"]


# ── a plan is refused for a wrong name or an impossible figure, not for how a target is covered ──
def _q1_plan():
    from test_data_driven_workflow import _q1_plan_fields, _q1_resources, _q1_runs

    box = session_state.new_session("m")
    _q1_resources(box)
    return box, _q1_plan_fields(_q1_runs())


def test_a_target_whose_reference_models_differ_from_the_runs_is_advice_not_a_refusal():
    box, fields = _q1_plan()
    fields["reproduction_targets"][0]["reference_models"] = ["MEMLS-IBA"]
    result = tools.call("research_plan", fields, session=box)
    assert result["status"] == "needs_input", result["summary"]
    warned = result["data"]["plan"]["validation_warnings"]
    assert any(str(item.get("field", "")).startswith("reproduction_targets") for item in warned)


def test_a_mapping_to_an_input_the_model_does_not_declare_is_still_refused():
    box, fields = _q1_plan()
    fields["parameter_mapping"] = [{
        "paper_concept": "snow density", "model_input": "snow_density", "mapped_value": 300.0,
        "provenance_class": "model_assumption", "rationale": "unverified mapping",
    }]
    result = tools.call("research_plan", fields, session=box)
    assert result["status"] == "terminal_error"
    # The problem names the row by the input it submitted, so the same name comes back in a
    # patch and the merger can find the row again.
    assert any(
        item.get("field") == "parameter_mapping[snow_density].model_input"
        for item in result["data"]["problems"]
    )


# ── approving a plan covers the model runs, not the code of a script ─────────────────────────
def test_a_script_is_still_put_to_a_person_after_the_plan_is_approved():
    from physearth.harness import approval

    box = session_state.new_session("m")
    assert not approval.person_present(box)  # a library or test run has nobody to ask
    approval.set_mode(box, approval.ASK)  # what the interface does when it makes a session
    approval.set_mode(box, approval.ALWAYS)  # what approving a plan does for model runs
    assert approval.mode(box) == approval.ALWAYS
    assert approval.person_present(box)


def test_a_headless_session_never_asks_for_a_script():
    from physearth.harness import approval

    box = session_state.new_session("m")
    approval.set_mode(box, approval.ALWAYS)
    assert not approval.person_present(box)


def test_a_model_that_is_not_registered_is_not_asked_to_have_its_instruction_read():
    # Figure 6 compares SMRT with MEMLS-IBA, which is not registered. The agent may name it among
    # the plan's selected models; the plan must not then demand an instruction nobody can read.
    box, fields = _q1_plan()
    fields["selected_models"] = list(fields.get("selected_models") or []) + [
        {"model": "MEMLS-IBA", "purpose": "the paper's reference", "capability_status": "unavailable"}
    ]
    result = tools.call("research_plan", fields, session=box)
    code = (result.get("data") or {}).get("error_code")
    assert code != "model_instruction_read_required", result["summary"]


# ── a failed side check is reported, not retried until the plan is reopened ten times ────────
def _gaps_session(stage_of_failed):
    main = {"id": "main", "label": "main run", "model": "smrt", "stage": "main", "parameters": {"output": "tb"}}
    side = {"id": "side", "label": "convergence", "model": "smrt", "stage": stage_of_failed,
            "parameters": {"output": "tb", "dort_streams": 8}}
    box = session_state.new_session("m")
    box["research"] = {"plan": {"runs": [main, side], "charts": []}, "phase": "approved"}
    box["successful_runs"] = [{"model": "smrt", "spec": {"output": "tb"}, "handle": "h1", "planned_run_id": "main"}]
    box["failed_runs"] = [{"run_id": "side", "spec": side["parameters"], "error": "DORT streams too few"}]
    return box


def test_a_failed_diagnostic_run_is_waived_and_does_not_count_as_missing():
    from physearth import research

    gaps = research.execution_gaps(_gaps_session("diagnostic"))
    assert gaps["missing_runs"] == [] and gaps["failed_runs"] == []
    assert [item["run_id"] for item in gaps["waived_runs"]] == ["side"]
    assert "DORT streams too few" in gaps["waived_runs"][0]["error"]


def test_a_failed_run_that_feeds_a_required_figure_still_counts():
    from physearth import research

    gaps = research.execution_gaps(_gaps_session("main"))
    assert gaps["missing_run_ids"] == ["side"] and [i["run_id"] for i in gaps["failed_runs"]] == ["side"]
    assert gaps["waived_runs"] == []


def test_the_report_is_told_which_side_checks_were_left_out():
    from physearth import research

    box = _gaps_session("diagnostic")
    assert "were left out" in research.report_generation_prompt(box)
    assert "were left out" not in research.report_generation_prompt(_gaps_session("main"))


# ── a source label says who chose the value, and a thin layer is not a semi-infinite one ─────
def test_a_value_the_question_does_not_give_is_not_labelled_user_specified():
    import importlib

    propose = importlib.import_module("physearth.research.propose")
    mapping = [
        {"model": "smrt", "model_input": "stickiness", "mapped_value": 0.5, "provenance_class": "user_specified"},
        {"model": "smrt", "model_input": "frequency_ghz", "mapped_value": 37.0, "provenance_class": "user_specified"},
        {"model": "smrt", "model_input": "radius_m", "mapped_value": 0.0001, "provenance_class": "user_specified"},
    ]
    repairs = propose._ground_user_labels(mapping, "Run SMRT at 37 GHz with a 100 um radius.")
    labels = {item["model_input"]: item["provenance_class"] for item in mapping}
    assert labels == {"stickiness": "model_assumption", "frequency_ghz": "user_specified", "radius_m": "user_specified"}
    assert [item["field"] for item in repairs] == ["parameter_mapping[smrt.stickiness].provenance_class"]
    assert "not give this value" in mapping[0]["rationale"]


def test_a_thin_default_layer_where_the_paper_states_a_semi_infinite_medium_still_refuses_the_plan():
    from test_cited_source_check import _semi_session

    from physearth.research import evidence

    box = _semi_session({"smrt-v1#07"})
    thin = [{"model": "smrt", "model_input": "thickness_m", "mapped_value": 1.0,
             "provenance_class": "model_assumption", "evidence_ref": ""}]
    problems = evidence._semi_infinite_problems(box, thin, [{"id": "smrt-v1#fig06"}])
    assert problems and problems[0]["physical"] is True


def test_a_warning_that_repeats_for_every_condition_is_said_once():
    from physearth import documents

    note = "The run differs from the paper reference condition; it is an exploratory extension."
    plan = {"validation_warnings": [
        {"field": "parameter_mapping[%d].%s" % (i, name), "message": note}
        for i, name in enumerate(("density", "temperature", "thickness"))
    ] + [{"field": "plan"}, {"message": "ok"}]}
    lines = documents.things_to_check(plan)
    assert len(lines) == 1 and "density, temperature, thickness" in lines[0]


def test_a_change_the_planning_agent_makes_is_not_marked_as_the_users():
    from physearth.research import mapping

    before = {"runs": [{"id": "r1", "parameters": {"temperature_k": 256.0, "thickness_m": 1.0}}]}
    plan = {"parameter_mapping": [
        {"model_input": "temperature_k", "provenance_class": "model_assumption"},
        {"model_input": "thickness_m", "provenance_class": "model_assumption"},
    ]}
    changes = {"runs": [{"id": "r1", "parameters": {"temperature_k": 265.0, "thickness_m": 100.0}}]}
    mapping._mark_user_revised_inputs(plan, before, changes, "Reproduce Figure 6 at a thickness of 100 m")
    labels = {item["model_input"]: item["provenance_class"] for item in plan["parameter_mapping"]}
    assert labels == {"temperature_k": "model_assumption", "thickness_m": "user_specified"}


def test_a_report_with_figures_and_no_words_of_its_own_is_sent_back_once():
    from physearth import research

    box = session_state.new_session("m")
    box["figures"] = [{"title": "Figure 1"}]
    table_only = "\n\n**Parameter sources** (from the plan)\n\n| Model | Input |\n| --- | --- |\n| smrt | output |\n"
    assert research.lacks_narrative(box, table_only)
    assert research.lacks_narrative(box, "The final report can now be delivered.")
    written = "The figure shows that brightness temperature falls with angle for horizontal polarisation. " * 8
    assert not research.lacks_narrative(box, written)
    box["figures"] = []
    assert not research.lacks_narrative(box, "")
