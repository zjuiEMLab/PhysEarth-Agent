"""An unstated value is the card's default, and an assumption waits until the paper is read."""

from physearth import session as session_state
from physearth.corpus import knowledge
from physearth.research import evidence

RUNS = [{"id": "r1", "model": "smrt", "parameters": {"sweep_parameter": "density_kg_m3"}}]


def _mapping(value=50, provenance="model_assumption", **extra):
    return [{
        "model": "smrt", "model_input": "frequency_ghz", "mapped_value": value,
        "provenance_class": provenance, **extra,
    }]


def _session(sections):
    session = session_state.new_session()
    session["sections_read"] = set(sections)
    return session


def _all_sections(slug="smrt-v1"):
    return {"%s#%s" % (slug, item["id"]) for item in knowledge.section_index(slug)}


def test_an_assumed_value_that_is_not_the_card_default_is_refused_with_the_default():
    problems = evidence._unstated_value_problems(_session(_all_sections()), _mapping(50), RUNS)
    refused = [p for p in problems if p["field"].endswith("mapped_value")]
    assert len(refused) == 1
    assert "37.0" in refused[0]["repair"] and "backend_default" in refused[0]["repair"]


def test_the_card_default_itself_is_not_refused():
    problems = evidence._unstated_value_problems(_session(_all_sections()), _mapping(37.0), RUNS)
    assert problems == []


def test_an_assumption_is_refused_while_an_unopened_section_gives_a_value_in_that_unit():
    problems = evidence._unstated_value_problems(_session({"smrt-v1#08"}), _mapping(37.0), RUNS)
    sources = [p["source"] for p in problems]
    assert "smrt-v1#07" in sources
    repair = next(p["repair"] for p in problems if p["source"] == "smrt-v1#07")
    assert "37 GHz" in repair
    # The agent cited the section without reading it and was refused for that; name the call.
    assert "read_literature" in repair and "section_id=07" in repair


def test_a_section_that_only_mentions_the_parameter_is_not_required_reading():
    """Section 01 says 'frequencies below 19 GHz': a different number, so not the value in play."""
    problems = evidence._unstated_value_problems(_session({"smrt-v1#08"}), _mapping(37.0), RUNS)
    assert "smrt-v1#01" not in [p["source"] for p in problems]


def test_reading_the_sections_closes_the_second_refusal():
    problems = evidence._unstated_value_problems(_session(_all_sections()), _mapping(37.0), RUNS)
    assert not [p for p in problems if p["source"].startswith("smrt-v1#")]


def test_a_value_with_evidence_or_a_stronger_label_is_left_alone():
    session = _session({"smrt-v1#08"})
    assert evidence._unstated_value_problems(
        session, _mapping(50, evidence_ref="smrt-v1#07"), RUNS) == []
    assert evidence._unstated_value_problems(
        session, _mapping(50, provenance="paper_explicit"), RUNS) == []
    assert evidence._unstated_value_problems(session, _mapping(50, paper_value=37), RUNS) == []


def test_a_swept_parameter_is_not_a_default_question():
    swept = [{"id": "r1", "model": "smrt", "parameters": {"sweep_parameter": "frequency_ghz"}}]
    assert evidence._unstated_value_problems(_session({"smrt-v1#08"}), _mapping(50), swept) == []
