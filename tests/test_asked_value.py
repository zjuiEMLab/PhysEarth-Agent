"""The final report must state what the question asked a value of, from the opened sources."""

from physearth import session as session_state
from physearth.harness import gates
from physearth.research import asked, report

QUESTION = "Under what snow-density range do the formulations converge, and at what density do they diverge?"


def _session(phase="approved", sections=("smrt-v1#08",), runs=3, question=QUESTION):
    session = session_state.new_session()
    session["research"] = {
        "phase": phase,
        "question": question,
        "plan": {
            "question": question,
            "runs": [
                {
                    "id": "r1",
                    "model": "smrt",
                    "parameters": {"sweep_parameter": "density_kg_m3"},
                }
            ],
        },
    }
    session["model_runs"] = runs
    session["sections_read"] = set(sections)
    return session


def test_the_asked_quantity_comes_from_the_question_and_the_card():
    quantities = asked.asked_quantities(_session())
    assert [item["name"] for item in quantities] == ["density_kg_m3"]
    assert quantities[0]["unit"] == "kg m-3"


def test_a_value_is_recognised_whatever_way_the_unit_is_written():
    for text in (
        "about 10–20 kg m⁻³",
        "10 to 20 kg/m3",
        "10-20 kg m-3",
        "20 kg m^-3",
        "10–20 kgm-3",  # PDF text runs the unit together
    ):
        assert asked.states_value(text, "kg m-3"), text
    for text in ("density 300 only", "10–20", "300 kg", "ordered by theory"):
        assert not asked.states_value(text, "kg m-3"), text


def test_a_report_that_never_states_the_range_is_refused_with_the_source_passage():
    session = _session()
    result = asked.check("The IBA curves sit above the Rayleigh curves.", session)
    assert not result["passed"]
    text = asked.correction(result)
    assert "10–20" in text and "[smrt-v1#08]" in text


def test_a_report_that_states_the_value_passes():
    session = _session()
    assert asked.check("Valid for about 10–20 kg m⁻³ [smrt-v1#08].", session)["passed"]
    assert asked.check("Converges for densities of 10 to 20 kg/m3 [smrt-v1#08].", session)["passed"]


def test_the_reports_own_sweep_range_is_not_the_papers_value():
    """The first live check: every report quoted its 1-100 kg m-3 sweep, which is a number
    with the right unit, and the gate let it through while the paper's 10-20 never appeared."""
    session = _session()
    text = "The sweep ran from 1.0 to 100.0 kg m-3 and the curves separate as density grows."
    assert asked.states_value(text, "kg m-3")
    assert not asked.check(text, session)["passed"]
    assert asked.required_spans(session, asked.asked_quantities(session)[0]) == ["10-20"]


def test_the_question_survives_a_later_approval_turn():
    session = session_state.new_session()
    asked.remember_question(session, "Reproduce Figure 3 and say under what density range curves converge.")
    asked.remember_question(session, "The reviewer approved the plan; proceed with execution.")
    assert "density range" in session["research_context"]["question"]
    asked.remember_question(session, "Reproduce Figure 4 of the same paper at 37 GHz.")
    assert "Figure 4" in session["research_context"]["question"]


def test_not_identifiable_is_accepted_only_when_no_opened_source_gives_a_value():
    # The section was opened and holds the range: declining to give it is not honest.
    assert not asked.check("The range is not identifiable.", _session())["passed"]
    # Nothing opened gives it: saying so is the right answer.
    nothing = _session(sections=())
    assert asked.check("The range is not identifiable from the evidence gathered.", nothing)["passed"]
    assert not asked.check("Everything went well.", nothing)["passed"]


def test_the_gate_only_applies_to_the_report_of_an_approved_plan_that_ran():
    assert asked.check("No range.", _session(phase="plan_review"))["passed"]
    assert asked.check("No range.", _session(runs=0))["passed"]
    assert asked.check("No range.", session_state.new_session())["passed"]


def test_the_final_checks_carry_the_gate_and_know_its_correction():
    session = _session()
    state = session_state.new_state(session)
    state["model_runs"] = 3
    checks = gates.final_checks("A report with no number.", state)
    failed = [check for check in checks if check["rule"] == "asked_value"]
    assert failed and not failed[0]["passed"]
    assert "Revise the final report" in gates.correction(failed[0])


def test_the_report_prompt_offers_the_passage_the_report_must_carry():
    prompt = report.report_generation_prompt(_session())
    assert "PAPER PASSAGES THAT GIVE WHAT THE QUESTION ASKS FOR" in prompt
    assert "10–20" in prompt and "[smrt-v1#08]" in prompt
