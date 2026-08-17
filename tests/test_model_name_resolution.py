"""A paper's spelling of a model name must reach the model, and no further.

A reproduction demo stopped and asked the user to confirm a partial scope because the
paper said `SMRT` and the card says `smrt`. The capability check reported it as "not
registered in the current model registry" -- next to MEMLS, which genuinely is not -- so
the one signal that check exists to give was buried under a false one.

The fix is a resolution step, not a looser lookup. These tests pin both halves: the
spellings that must resolve, and the names that must still fail.
"""

import pytest
from physearth.research import capability

from physearth import registry, tools
from physearth import session as session_state

# How a paper, a person or a filename writes it -> the registered card name.
SPELLINGS = [
    ("smrt", "smrt"),
    ("SMRT", "smrt"),
    ("Smrt", "smrt"),
    ("tau_omega", "tau_omega"),
    ("tau-omega", "tau_omega"),
    ("Tau Omega", "tau_omega"),
    ("TAU-OMEGA", "tau_omega"),
    ("water_cloud", "water_cloud"),
    ("Water Cloud", "water_cloud"),
    ("water-cloud", "water_cloud"),
]

# Names that must NOT resolve. The first three are real reference models this repository
# does not implement, and saying so is the point of the capability check. The rest guard
# against the fix becoming fuzzy matching.
MUST_NOT_RESOLVE = [
    "MEMLS",
    "DMRT-ML",
    "DMRT-QMS",
    "smrtt",
    "smr",
    "sm rt x",
    "",
    "   ",
    None,
]


@pytest.mark.parametrize("written,expected", SPELLINGS)
def test_a_papers_spelling_resolves_to_the_registered_model(written, expected):
    model, canonical = registry.resolve(written)
    assert model is not None, "%r did not resolve" % written
    assert canonical == expected
    assert model.name == expected


@pytest.mark.parametrize("written", MUST_NOT_RESOLVE)
def test_a_model_that_is_not_registered_still_does_not_resolve(written):
    """Loosening this into fuzzy matching would make the whole check worthless."""
    model, canonical = registry.resolve(written)
    assert model is None, "%r resolved to %s; resolution must not guess" % (written, canonical)
    assert canonical is None


def test_get_stays_exact():
    """Resolution is for names arriving from prose. Execution keeps an exact contract."""
    assert registry.get("smrt") is not None
    assert registry.get("SMRT") is None


def test_the_capability_check_no_longer_reports_a_registered_model_as_missing():
    box = session_state.new_session("m")
    report = capability.capability_check(
        box,
        question="Reproduce the SMRT figure 4 comparison",
        reference_models=["SMRT", "MEMLS", "tau-omega"],
    )
    missing = {item["model"] for item in report["unavailable"]}
    assert "MEMLS" in missing, "a genuinely unregistered reference model must be reported"
    assert "SMRT" not in missing, "SMRT is registered as `smrt` and must not be reported missing"
    assert "tau-omega" not in missing


def test_the_capability_check_says_which_name_it_matched():
    """Silently swapping a name the user wrote would be worse than refusing it."""
    box = session_state.new_session("m")
    report = capability.capability_check(
        box, question="", reference_models=["SMRT", "smrt"]
    )
    resolved = {item["asked"]: item["registered"] for item in report["resolved_names"]}
    assert resolved == {"SMRT": "smrt"}, resolved


def test_list_models_accepts_the_spelling_and_answers_with_the_registered_name():
    box = session_state.new_session("m")
    result = tools.call("list_models", {"model": "SMRT"}, session=box)
    assert result["status"] == "success", result
    assert result["data"]["name"] == "smrt"


def test_list_models_still_refuses_a_model_that_is_not_registered():
    box = session_state.new_session("m")
    result = tools.call("list_models", {"model": "MEMLS"}, session=box)
    assert result["status"] != "success"
    assert "MEMLS" in str(result.get("error") or result.get("summary"))


def test_a_planned_run_is_rewritten_to_the_registered_spelling():
    """The plan, the execution and the [model:...] marker must name the same thing."""
    from physearth.research.normalise import _clean_runs

    runs, problems = _clean_runs(
        [{"run_id": "r1", "model": "SMRT", "parameters": {}}]
    )[:2]
    assert not any("unknown model" in str(p) for p in problems), problems
    assert runs and runs[0]["model"] == "smrt"


# --- the plan must speak one spelling -----------------------------------------------
#
# The fix above canonicalised the run's model name, which made a second bug deterministic:
# reproduction_targets still carried the paper's spelling, so every downstream check
# compared `smrt` against `SMRT` and reported the model missing from its own coverage.
# That is where "4 target coverage issue(s), 1 parameter mapping issue(s)" came from.


def test_a_target_covered_by_its_own_run_reports_no_coverage_problem():
    from physearth.research.coverage import _target_coverage

    targets = [{
        "id": "t1", "status": "planned", "run_ids": ["r1"], "chart_ids": ["c1"],
        "reference_models": ["SMRT"], "requested_outputs": [],
    }]
    runs = [{"id": "r1", "model": "smrt", "parameters": {}}]
    problems, _, _ = _target_coverage(targets, runs, [{"id": "c1"}])
    assert problems == [], problems


def test_target_coverage_uses_opened_paper_identity_for_a_registered_model():
    from physearth.research.coverage import _target_coverage

    box = session_state.new_session("m")
    box["sections_read"].add("smrt-v1#08")
    targets = [{
        "id": "t1", "status": "planned", "run_ids": ["r1"], "chart_ids": [],
        "reference_models": ["smrt-v1"], "requested_outputs": [],
    }]
    runs = [{"id": "r1", "model": "smrt", "parameters": {}}]

    problems, _, _ = _target_coverage(targets, runs, [], box)

    assert problems == [], problems


def test_an_unregistered_reference_model_is_still_a_coverage_problem():
    """The tolerance must not swallow the signal the check exists to give."""
    from physearth.research.coverage import _target_coverage

    targets = [{
        "id": "t2", "status": "planned", "run_ids": ["r1"], "chart_ids": [],
        "reference_models": ["MEMLS"], "requested_outputs": [],
    }]
    runs = [{"id": "r1", "model": "smrt", "parameters": {}}]
    problems, _, _ = _target_coverage(targets, runs, [])
    assert any("MEMLS" in p for p in problems), problems


def test_the_plan_stores_one_spelling_for_every_model_it_names():
    from physearth.research.normalise import (
        _clean_parameter_mapping,
        _clean_reproduction_targets,
        _clean_selected_models,
    )

    targets = _clean_reproduction_targets(
        [{"id": "t1", "reference_models": ["SMRT", "tau-omega", "MEMLS"]}]
    )
    assert targets[0]["reference_models"] == ["smrt", "tau_omega", "MEMLS"], (
        "registered models take their registered spelling; MEMLS is not registered and "
        "must survive as written so it is still reported"
    )

    selected = _clean_selected_models([{"model": "SMRT"}, {"model": "Water Cloud"}])
    assert [item["model"] for item in selected] == ["smrt", "water_cloud"]

    mapping = _clean_parameter_mapping(
        [{"model": "SMRT", "paper_name": "density", "model_input": "density"}]
    )
    assert mapping and mapping[0]["model"] == "smrt"


def test_the_registered_parameter_index_finds_a_model_named_as_the_paper_names_it():
    from physearth.research.mapping import _registered_parameter_index

    index = _registered_parameter_index(None, ["SMRT"])
    assert index, "a paper-spelled model contributed no declared parameters"
    assert any("density_kg_m3" in params for params in index.values())
