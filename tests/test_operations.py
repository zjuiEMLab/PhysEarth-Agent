"""Steps beyond a model run: which have a tool, and what the user is offered when one has not."""

from pathlib import Path

from physearth import registry, tools
from physearth import session as session_state
from physearth.research import capability, operations


def _session():
    box = session_state.new_session("m")
    card = registry.get("smrt").card
    box["models_inspected"] = {"smrt@%s" % card["version"]}
    box["model_instructions_read"] = {"smrt@%s" % (card.get("instruction_version") or "1.0")}
    return box


def _check(box, needed):
    return capability.capability_check(
        box, reference_models=["smrt"], requested_outputs=["tb_v"],
        local_models=["smrt"], needed_operations=needed,
    )


def test_steps_with_a_tool_do_not_stop_the_check():
    report = _check(_session(), ["sweep_parameter", "plot_results"])
    assert report["status"] == "ready"
    assert report["missing_operations"] == []


def test_an_empty_list_is_ready():
    assert _check(_session(), [])["status"] == "ready"


def test_a_step_with_no_tool_waits_for_the_user_and_offers_options():
    report = _check(_session(), ["sweep_parameter", "solve_for_parameter"])
    assert report["status"] == "waiting_user"
    missing = report["missing_operations"][0]
    assert missing["id"] == "solve_for_parameter"
    assert {option["id"] for option in missing["options"]} == {"A", "B", "C"}
    assert sum(option["available"] for option in missing["options"]) == 2
    assert not all(option["available"] for option in missing["options"])


def test_aliases_and_phrases_resolve_to_the_step():
    for wording in ("root_finding", "Optimize", "find the value, solve for it"):
        _available, missing, _unknown = operations.resolve([wording])
        assert missing, wording


def test_an_unknown_step_is_reported_not_blocked_on():
    report = _check(_session(), ["something_unlisted"])
    assert report["status"] == "ready"
    assert report["unrecognised_operations"] == ["something_unlisted"]


def test_the_decision_covers_the_steps_that_were_confirmed():
    box = _session()
    _check(box, ["solve_for_parameter"])
    assert capability.capability_check(box, decision="confirm_partial")["status"] == "confirmed"
    assert _check(box, ["solve_for_parameter"])["status"] == "confirmed"
    assert _check(box, ["solve_for_parameter", "fit_parameters"])["status"] == "waiting_user"


def test_the_check_requires_the_agent_to_answer():
    result = tools.call("research_capability_check", {"action": "check"}, session=_session())
    assert result["status"] == "terminal_error"
    assert "needed_operations" in result["error"] or "needed_operations" in result["summary"]


def test_the_message_names_the_step_and_what_can_go_ahead():
    box = _session()
    result = tools.call(
        "research_capability_check",
        {"action": "check", "needed_operations": ["solve_for_parameter"],
         "reference_models": ["smrt"], "requested_outputs": ["tb_v"], "local_models": ["smrt"]},
        session=box,
    )
    text = result["summary"]
    assert "needs what is not available" in text and "root-finding tool" in text
    assert "available now" in text and "not supported yet" in text
    assert "scipy.optimize.brentq" in text and "**Why:**" in text
    assert "A. Write and run a solver script" in text and "B. Sweep and compare" in text


def test_the_registry_names_no_model_or_benchmark_word():
    text = repr(operations.OPERATIONS).lower()
    for word in ("smrt", "memls", "dmrt", "stickiness", "snow", "fig3", "fig7"):
        assert word not in text, word


def test_the_agents_own_account_of_what_to_find_is_shown():
    detail = {"step": "solve_for_parameter", "find": "the stickiness for each grain size",
              "must_match": "the brightness temperature of the other configuration",
              "repeated_for": "five densities"}
    report = _check(_session(), [detail])
    text = operations.explain(report["missing_operations"][0])
    assert "To find: the stickiness for each grain size" in text
    assert "Must match: the brightness temperature" in text
    assert "Repeated for: five densities" in text


def test_without_details_the_message_asks_instead_of_guessing():
    report = _check(_session(), ["solve_for_parameter"])
    text = operations.explain(report["missing_operations"][0])
    assert "could not tell what has to be found" in text and "To find:" not in text


def test_every_block_is_separated_so_the_page_can_render_it():
    text = operations.explain(_check(_session(), ["solve_for_parameter"])["missing_operations"][0])
    assert "\n- **B." in text  # the options are one list, one line each
    assert text.count("\n\n") >= 3


def test_an_output_no_model_declares_gets_the_options_even_if_no_step_was_listed():
    box = _session()
    report = capability.capability_check(
        box, reference_models=["smrt"], requested_outputs=["a_quantity_no_model_outputs"],
        local_models=["smrt"], needed_operations=[],
    )
    assert report["status"] == "waiting_user"
    item = report["missing_operations"][0]
    assert item["id"] == "derive_quantity"
    assert item["details"]["find"] == "a_quantity_no_model_outputs"
    assert {option["id"] for option in item["options"]} == {"A", "B", "C"}


def test_the_message_for_that_case_offers_a_script_and_tells_the_agent_what_each_choice_means():
    box = _session()
    result = tools.call(
        "research_capability_check",
        {"action": "check", "needed_operations": [], "reference_models": ["smrt"],
         "requested_outputs": ["a_quantity_no_model_outputs"], "local_models": ["smrt"]},
        session=box,
    )
    text = result["summary"]
    assert "A way to compute a_quantity_no_model_outputs" in text
    assert "A. Write and run a script" in text and "B. Partial plan" in text
    steps = result["data"]["if_the_person_chooses"]
    assert "run_analysis_script" in steps["A"] and "confirm_partial" in steps["B"]


def test_a_one_letter_reply_is_spelled_out_for_the_agent():
    box = _session()
    _check(box, ["solve_for_parameter"])
    review = box["capability_review"]
    a = operations.choice_instruction(review, "A")
    assert "run_analysis_script" in a and "available" in a.lower()
    assert "confirm_partial" in operations.choice_instruction(review, " option b. ")
    assert "not available yet" in operations.choice_instruction(review, "c")
    assert operations.choice_instruction(review, "a longer sentence") is None
    assert operations.choice_instruction({"status": "ready"}, "A") is None


def test_a_specific_step_replaces_the_general_one():
    report = _check(_session(), ["solve_for_parameter", "derive_quantity"])
    assert [item["id"] for item in report["missing_operations"]] == ["solve_for_parameter"]
