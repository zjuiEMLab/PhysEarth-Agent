"""The report's parameter_provenance block must agree with the plan's ledger."""

import json

from physearth import session as session_state
from physearth.harness import gates
from physearth.research import consistency


def _session():
    session = session_state.new_session()
    session["research"] = {
        "phase": "approved",
        "question": "q",
        "plan": {"question": "q", "runs": [], "parameter_mapping": [
            {"model": "smrt", "model_input": "microstructure_model", "provenance_class": "model_assumption"},
            {"model": "smrt", "model_input": "frequency_ghz", "provenance_class": "backend_default"},
            {"model": "smrt", "model_input": "radius_m", "provenance_class": "paper_explicit"},
        ]},
    }
    session["model_runs"] = 3
    return session


def _report(*items):
    block = json.dumps([{"field": f, "source_kind": k} for f, k in items])
    return "Report.\n<parameter_provenance>\n%s\n</parameter_provenance>" % block


def test_a_block_that_agrees_with_the_ledger_passes():
    text = _report(("microstructure_model", "assumption"), ("frequency_ghz", "model_default"),
                   ("radius_m", "paper"))
    assert consistency.check(text, _session())["passed"]


def test_a_source_that_contradicts_the_ledger_is_refused_with_the_allowed_words():
    result = consistency.check(_report(("microstructure_model", "user")), _session())
    assert not result["passed"]
    assert result["mismatches"][0]["ledger"] == "model_assumption"
    assert "assumption" in consistency.correction(result)


def test_it_only_applies_when_the_report_carries_the_block_and_the_plan_ran():
    assert consistency.check("No appendix.", _session())["skipped"]
    session = _session()
    session["research"]["phase"] = "plan_review"
    assert consistency.check(_report(("radius_m", "user")), session)["skipped"]


def test_the_gate_carries_it_and_knows_its_correction():
    session = _session()
    state = session_state.new_state(session)
    state["model_runs"] = 3
    checks = gates.final_checks(_report(("radius_m", "user")), state)
    bad = [c for c in checks if c["rule"] == "provenance_consistency"]
    assert bad and not bad[0]["passed"]
    assert "Revise the parameter_provenance block" in gates.correction(bad[0])


REQUEST = (
    "Reproduce the figure.\nEnd the report with these tags:\n"
    "<parameter_provenance>[{\"field\":\"x\"}]</parameter_provenance>\n"
    "<reproduction_outcome>reproduced|partial</reproduction_outcome>"
)


def _asked_for_appendix():
    session = _session()
    session["research_context"] = {"question": REQUEST}
    return session


def test_the_tags_the_request_spelled_out_are_required_in_the_report():
    session = _asked_for_appendix()
    assert set(consistency.required_appendix(session)) == {"parameter_provenance", "reproduction_outcome"}
    result = consistency.check_appendix("A report with no tags.", session)
    assert not result["passed"] and set(result["missing"]) == {
        "parameter_provenance", "reproduction_outcome"}
    assert "<reproduction_outcome>reproduced|partial</reproduction_outcome>" in (
        consistency.appendix_correction(result))


def test_a_report_with_the_tags_passes_and_a_request_without_tags_asks_for_nothing():
    session = _asked_for_appendix()
    text = _report(("radius_m", "paper")) + "\n<reproduction_outcome>partial</reproduction_outcome>"
    assert consistency.check_appendix(text, session)["passed"]
    assert consistency.check_appendix("No tags.", _session())["skipped"]


def test_the_gate_carries_the_appendix_check():
    session = _asked_for_appendix()
    state = session_state.new_state(session)
    state["model_runs"] = 3
    failed = [c for c in gates.final_checks("No tags.", state) if c["rule"] == "required_appendix"]
    assert failed and not failed[0]["passed"]
    assert "tagged blocks" in gates.correction(failed[0])
