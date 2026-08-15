"""A paper's spelling of a model name must reach the model, and no further.

A reproduction demo stopped and asked the user to confirm a partial scope because the
paper said `SMRT` and the card says `smrt`. The capability check reported it as "not
registered in the current model registry" -- next to MEMLS, which genuinely is not -- so
the one signal that check exists to give was buried under a false one.

The fix is a resolution step, not a looser lookup. These tests pin both halves: the
spellings that must resolve, and the names that must still fail.
"""

import pytest

from physearth import registry
from physearth import session as session_state
from physearth import tools
from physearth.research import capability

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
