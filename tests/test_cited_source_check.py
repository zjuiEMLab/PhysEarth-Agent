"""A parameter's label has to be supported by the text it cites."""

from physearth.research import claims

THIRD = {3}


def test_a_value_in_a_worked_example_is_not_evidence_for_the_experiment():
    assert "different experiment" in claims.paper_claim_problem("smrt-v1#06", 270, THIRD, "temperature_k", "K")
    assert "different experiment" in claims.paper_claim_problem("smrt-v1#06", 100, THIRD, "thickness_m", "m")


def test_a_value_stated_for_another_figure_is_not_evidence_for_this_one():
    assert "different experiment" in claims.paper_claim_problem("smrt-v1#08", 256, THIRD, "temperature_k", "K")


def test_the_same_sentence_supports_the_figure_it_names():
    assert claims.paper_claim_problem("smrt-v1#08", 256, {4}, "temperature_k", "K") == ""


def test_a_general_statement_supports_any_figure():
    assert claims.paper_claim_problem("smrt-v1#07", 37, THIRD, "frequency_ghz", "GHz") == ""


def test_a_value_the_section_does_not_state_is_unsupported():
    assert "does not state" in claims.paper_claim_problem("smrt-v1#07", 123456, THIRD, "temperature_k", "K")


def test_micrometres_in_the_text_match_metres_in_the_model():
    assert claims.paper_claim_problem("smrt-v1#08", 0.0001, {4}, "radius_m", "m") == ""


def test_a_figure_reference_or_unreadable_section_is_not_judged():
    assert claims.paper_claim_problem("smrt-v1#fig03", 999, THIRD) == ""
    assert claims.paper_claim_problem("nope#00", 999, THIRD) == ""


def test_a_user_value_must_be_in_the_question():
    assert claims.user_claim_problem("Run it at 37 GHz and 55 degrees", 37) == ""
    assert "does not contain" in claims.user_claim_problem("Run it at 37 GHz", 0.5)
    assert claims.user_claim_problem("", 0.5) == ""


def test_figure_lists_and_ranges_are_expanded():
    assert claims._figures("Figures 3-5 show") >= {3, 4, 5}
    assert claims._figures("Figs. 3 and 5") >= {3, 5}


def _audit(mappings, question="", targets=({"id": "smrt-v1#fig03"},), plan=False):
    session = {"research_context": {"question": question}, "research": {"plan": {"runs": [1]}} if plan else {}}
    specs = {
        "temperature_k": {"type": "number", "unit": "K", "default": 265.0},
        "thickness_m": {"type": "number", "unit": "m", "default": 1.0},
        "stickiness": {"type": "number", "unit": "none", "default": 0.2},
        "density_kg_m3": {"type": "number", "unit": "kg m-3", "default": 300.0},
    }
    repairs, conditions, provenance = [], {}, {}
    count = claims.audit(
        session, mappings, list(targets), lambda model, name: specs.get(name),
        conditions, provenance, repairs,
    )
    return count, repairs


def test_an_unsupported_paper_label_becomes_an_assumption_and_says_why():
    mapping = {"model": "smrt", "model_input": "temperature_k", "mapped_value": 270,
               "provenance_class": "paper_explicit", "evidence_ref": "smrt-v1#06"}
    count, repairs = _audit([mapping])
    assert count == 1
    assert mapping["provenance_class"] == "model_assumption"
    assert mapping["evidence_ref"] == ""
    assert "different experiment" in repairs[0]["reason"]


def test_a_value_equal_to_the_card_default_becomes_a_default():
    mapping = {"model": "smrt", "model_input": "temperature_k", "mapped_value": 265.0,
               "provenance_class": "paper_explicit", "evidence_ref": "smrt-v1#07"}
    _audit([mapping])
    assert mapping["provenance_class"] == "backend_default"


def test_a_user_label_without_the_value_in_the_question_is_relabelled():
    mapping = {"model": "smrt", "model_input": "stickiness", "mapped_value": 0.5,
               "provenance_class": "user_specified", "evidence_ref": "smrt-v1#08"}
    _audit([mapping], question="Reproduce the scattering coefficient against density")
    assert mapping["provenance_class"] == "model_assumption"


def test_a_user_label_is_left_alone_when_revising_an_existing_plan():
    mapping = {"model": "smrt", "model_input": "stickiness", "mapped_value": 0.5,
               "provenance_class": "user_specified", "evidence_ref": ""}
    count, _ = _audit([mapping], question="reproduce it", plan=True)
    assert count == 0


def test_sweeps_and_non_numbers_are_not_judged():
    mappings = [
        {"model": "smrt", "model_input": "density_kg_m3", "mapped_value": {"sweep_start": 1},
         "provenance_class": "paper_explicit", "evidence_ref": "smrt-v1#06"},
        {"model": "smrt", "model_input": "electromagnetic_model", "mapped_value": "iba",
         "provenance_class": "paper_explicit", "evidence_ref": "smrt-v1#06"},
    ]
    assert _audit(mappings)[0] == 0


def _relabel(mapping):
    specs = {
        "temperature_k": {"type": "number", "unit": "K", "default": 265.0},
        "electromagnetic_model": {"type": "string", "unit": "none", "default": "iba"},
        "sweep_points": {"type": "integer", "unit": "count", "default": 10},
    }
    repairs = []
    count = claims.relabel_defaults([mapping], lambda model, name: specs.get(name), repairs)
    return count, repairs


def test_an_assumption_equal_to_the_card_default_becomes_a_default():
    mapping = {"model": "smrt", "model_input": "temperature_k", "mapped_value": 265,
               "provenance_class": "model_assumption", "evidence_ref": ""}
    count, repairs = _relabel(mapping)
    assert count == 1 and mapping["provenance_class"] == "backend_default"
    assert repairs[0]["reason"] == "the value equals the model card's default"


def test_an_assumption_that_differs_from_the_default_stays_an_assumption():
    mapping = {"model": "smrt", "model_input": "temperature_k", "mapped_value": 270,
               "provenance_class": "model_assumption", "evidence_ref": ""}
    assert _relabel(mapping)[0] == 0


def test_choices_sweeps_and_sourced_values_are_not_relabelled():
    for mapping in (
        {"model": "smrt", "model_input": "electromagnetic_model", "mapped_value": "iba",
         "provenance_class": "model_assumption", "evidence_ref": ""},
        {"model": "smrt", "model_input": "sweep_points", "mapped_value": 10,
         "provenance_class": "model_assumption", "evidence_ref": ""},
        {"model": "smrt", "model_input": "temperature_k", "mapped_value": 265,
         "provenance_class": "model_assumption", "evidence_ref": "smrt-v1#07"},
    ):
        assert _relabel(mapping)[0] == 0


def test_a_citation_from_another_experiment_does_not_excuse_an_assumed_value():
    from physearth import registry
    from physearth.research import evidence

    box = {"models_inspected": set()}
    box["model_declarations"] = {"smrt": {"parameters": registry.get("smrt").card["parameters"]}}
    mapping = [{"model": "smrt", "model_input": "temperature_k", "mapped_value": 270,
                "provenance_class": "model_assumption", "evidence_ref": "smrt-v1#06"}]
    runs = [{"id": "r1", "model": "smrt", "parameters": {"temperature_k": 270}}]
    problems = evidence._unstated_value_problems(box, mapping, runs, [{"id": "smrt-v1#fig03"}])
    assert any("card default" in str(p.get("expected")) for p in problems)
    # the same citation stands when the target is the figure the sentence belongs to
    mapping[0]["mapped_value"] = 256
    mapping[0]["evidence_ref"] = "smrt-v1#08"
    assert not evidence._unstated_value_problems(box, mapping, runs, [{"id": "smrt-v1#fig04"}])


def _semi_session(sections):
    from physearth import registry

    return {"sections_read": set(sections),
            "model_declarations": {"smrt": {"parameters": registry.get("smrt").card["parameters"]}}}


def test_a_general_semi_infinite_statement_applies_to_any_figure_but_a_worked_example_does_not():
    assert claims.semi_infinite_stated(_semi_session({"smrt-v1#07"}), {6}) == "smrt-v1#07"
    assert claims.semi_infinite_stated(_semi_session({"smrt-v1#06"}), {6}) is None  # worked example
    assert claims.semi_infinite_stated(_semi_session({"smrt-v1#08"}), {6}) is None  # another figure
    assert claims.semi_infinite_stated(_semi_session({"smrt-v1#08"}), {4}) == "smrt-v1#08"


def test_a_default_layer_where_the_paper_states_a_semi_infinite_medium_is_flagged():
    from physearth.research import evidence

    box = _semi_session({"smrt-v1#07"})
    thin = [{"model": "smrt", "model_input": "thickness_m", "mapped_value": 1.0,
             "provenance_class": "backend_default", "evidence_ref": ""}]
    problems = evidence._semi_infinite_problems(box, thin, [{"id": "smrt-v1#fig06"}])
    assert problems and "semi-infinite" in problems[0]["repair"]
    thick = [dict(thin[0], mapped_value=500.0, provenance_class="model_assumption")]
    assert evidence._semi_infinite_problems(box, thick, [{"id": "smrt-v1#fig06"}]) == []
    assert evidence._semi_infinite_problems(_semi_session(set()), thin, []) == []


def test_a_thick_layer_assumption_is_accepted_when_the_paper_states_the_medium():
    from physearth.research import evidence

    box = _semi_session({"smrt-v1#07"})
    mapping = [{"model": "smrt", "model_input": "thickness_m", "mapped_value": 500.0,
                "provenance_class": "model_assumption", "evidence_ref": ""}]
    runs = [{"id": "r1", "model": "smrt", "parameters": {"thickness_m": 500.0}}]
    assert evidence._unstated_value_problems(box, mapping, runs, [{"id": "smrt-v1#fig06"}]) == []
    box["sections_read"] = set()
    assert evidence._unstated_value_problems(box, mapping, runs, [{"id": "smrt-v1#fig06"}]) != []


def test_a_run_that_asks_only_for_coefficients_does_not_depend_on_depth():
    from physearth.research import evidence

    box = _semi_session({"smrt-v1#07"})
    thin = [{"model": "smrt", "model_input": "thickness_m", "mapped_value": 1.0,
             "provenance_class": "backend_default", "evidence_ref": ""}]
    coefficients = [{"id": "r", "model": "smrt", "parameters": {"output": "coefficients"}}]
    brightness = [{"id": "r", "model": "smrt", "parameters": {"output": "tb"}}]
    figs = [{"id": "smrt-v1#fig03"}]
    assert evidence._semi_infinite_problems(box, thin, figs, coefficients) == []
    assert evidence._semi_infinite_problems(box, thin, figs, brightness) != []


def test_an_unread_section_that_states_the_medium_is_named_when_a_thick_layer_is_assumed():
    from physearth.research import evidence

    box = _semi_session({"smrt-v1#05"})
    mapping = [{"model": "smrt", "model_input": "thickness_m", "mapped_value": 10.0,
                "provenance_class": "model_assumption", "evidence_ref": ""}]
    runs = [{"id": "r1", "model": "smrt", "parameters": {"thickness_m": 10.0}}]
    problems = evidence._unstated_value_problems(box, mapping, runs, [{"id": "smrt-v1#fig06"}])
    assert problems and "read_literature" in problems[0]["repair"] and "smrt-v1#07" in problems[0]["repair"]
    box["sections_read"].add("smrt-v1#07")
    assert evidence._unstated_value_problems(box, mapping, runs, [{"id": "smrt-v1#fig06"}]) == []
