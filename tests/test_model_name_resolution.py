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


@pytest.mark.parametrize("written", ["pywatershed v3.0.0", "pywatershed 3.0.0", "SMRT v1.5.1"])
def test_a_name_with_the_cards_own_version_resolves(written):
    entry, canonical, configuration, options = registry.resolve_configuration(written)
    assert entry is not None and canonical == written.split()[0].lower()
    assert configuration == {} and options == []


@pytest.mark.parametrize("written", ["pywatershed v2.0.0", "SMRT 1.0"])
def test_a_name_with_another_version_does_not_resolve(written):
    assert registry.resolve_configuration(written)[0] is None


@pytest.mark.parametrize("written, configuration", [
    # How the SMRT paper names the configurations of its theory comparison: the model, the
    # release it describes, then the formulation it was run with. The connector and the
    # closing noun are grammar; leaving them to the vocabulary guard read every one of these
    # as an unregistered model, and the reproduction then stopped for a partial-scope
    # decision about a model that was in the registry, runnable, and named by the paper.
    ("SMRT v1.0 with Rayleigh theory", {"electromagnetic_model": "rayleigh"}),
    ("SMRT v1.0 with IBA theory", {"electromagnetic_model": "iba"}),
    ("SMRT v1.0 with DMRT QCA-CP theory",
     {"electromagnetic_model": "dmrt_qcacp_shortrange"}),
    ("SMRT with IBA theory", {"electromagnetic_model": "iba"}),
    ("SMRT with DMRT QCA-CP theory", {"electromagnetic_model": "dmrt_qcacp_shortrange"}),
    ("SMRT using the rayleigh theory", {"electromagnetic_model": "rayleigh"}),
    ("SMRT v1.0 with non-sticky hard spheres theory",
     {"microstructure_model": "non_sticky_hard_spheres"}),
])
def test_a_formulation_named_in_a_sentence_is_that_configuration(written, configuration):
    entry, canonical, found, options = registry.resolve_configuration(written)
    assert entry is not None and canonical == "smrt", written
    assert found == configuration, (written, found)
    assert options == []


@pytest.mark.parametrize("written", [
    # Another model described the same way is still another model: the name in front of
    # the connector has to resolve on its own.
    "MEMLS with IBA theory",
    "MEMLS v3 with IBA theory",
    # And a formulation no card declares is not a configuration of one that does.
    "SMRT v1.0 with nonsense theory",
    "SMRT v1.0 with DMRT-QMS theory",
])
def test_a_sentence_about_an_unregistered_model_still_does_not_resolve(written):
    model, canonical, configuration, options = registry.resolve_configuration(written)
    assert model is None and canonical is None, written
    assert configuration == {} and options == [], written


def test_a_sentence_that_names_only_half_a_choice_reports_the_choice():
    """A version and a connector are grammar; "QCA" still does not pick a QCA variant."""
    entry, canonical, configuration, options = registry.resolve_configuration(
        "SMRT v1.0 with QCA theory"
    )
    assert entry is not None and canonical == "smrt" and configuration == {}
    assert sorted(option["electromagnetic_model"] for option in options) == [
        "dmrt_qca_shortrange", "dmrt_qcacp_shortrange",
    ]


def test_the_papers_version_of_a_resolved_configuration_is_reported_not_enforced():
    """The formulation resolves; the release difference is stated in the resolution."""
    box = session_state.new_session("m")
    tools.call("list_models", {"model": "smrt"}, session=box)
    tools.call("read_model_instruction", {"model": "smrt"}, session=box)
    result = tools.call("research_capability_check", {
        "action": "check", "needed_operations": [], "question": "Reproduce Figure 3",
        "local_models": ["smrt"],
        "targets": [{
            "id": "fig03", "label": "Fig. 3",
            "reference_models": ["SMRT v1.0 with Rayleigh theory"],
            "requested_outputs": ["ks_per_m"],
        }],
    }, session=box)
    review = box["capability_review"]
    assert review["status"] == "ready" and review["unavailable"] == []
    resolved = review["resolved_names"][0]
    assert resolved["configuration"] == {"electromagnetic_model": "rayleigh"}
    assert resolved["asked_version"] == "1.0"
    assert "registry runs 1.5.1" in resolved["match_basis"]
    assert "source describes version 1.0 and the registry runs 1.5.1" in result["summary"]


def test_the_capability_summary_names_outputs_no_card_declares():
    session = session_state.new_session(None)
    owner = session["id"]
    for name in ("list_models", "read_model_instruction"):
        tools.call(name, {"model": "pyet"}, owner=owner, session=session)
    result = tools.call(
        "research_capability_check",
        {"needed_operations": [], "reference_models": ["pyet"], "requested_outputs": ["et0_mm_day", "published_et0"]},
        owner=owner,
        session=session,
    )
    # An output no model declares is computed by a script, so it is stated and does not stop the plan.
    assert result["status"] == "success"
    assert "Outputs no registered model declares: published_et0" in result["summary"]
    assert "Computed by script" in result["summary"]


def test_a_versioned_local_candidate_is_reported_as_supported():
    session = session_state.new_session(None)
    owner = session["id"]
    for name in ("list_models", "read_model_instruction"):
        tools.call(name, {"model": "pywatershed"}, owner=owner, session=session)
    report = capability.capability_check(
        session, question="Sagehen", reference_models=[], requested_outputs=["value"],
        local_models=["pywatershed@3.0.0"],
    )
    assert [item["model"] for item in report["supported"]] == ["pywatershed"]


@pytest.mark.parametrize("name", ["MEMLS-IBA (grain type 2, six-flux solver)", "MEMLS-IBA", "MEMLS-IBA (default)", "DMRT-QMS", "DMRT-ML"])
def test_another_model_that_shares_a_theory_word_does_not_resolve(name):
    """MEMLS uses IBA too; the shared word must not make MEMLS a configuration of smrt."""
    assert registry.resolve_configuration(name)[0] is None


@pytest.mark.parametrize("name, configuration", [
    ("Non-sticky hard spheres (DMRT QCA-CP)", {"microstructure_model": "non_sticky_hard_spheres"}),
    ("Independent spheres + Rayleigh", {"electromagnetic_model": "rayleigh", "microstructure_model": "independent_sphere"}),
    ("DMRT QCA-CP", {"electromagnetic_model": "dmrt_qcacp_shortrange"}),
    # "default" qualifies the configuration; it does not name another model.
    ("SMRT IBA default", {"electromagnetic_model": "iba"}),
    ("SMRT IBA original", {"electromagnetic_model": "iba_original"}),
])
def test_a_legend_written_in_the_cards_vocabulary_still_resolves(name, configuration):
    entry, canonical, found, _options = registry.resolve_configuration(name)
    assert canonical == "smrt" and found == configuration


def test_a_theory_written_out_with_its_own_initials_is_that_theory_but_another_models_note_is_not():
    from physearth.research import capability

    assert capability._spelled_out("Improved Born approximation (IBA)") == "IBA"
    assert capability._spelled_out("MEMLS (IBA)") is None
    assert capability._spelled_out("Rayleigh (independent spheres)") is None
