"""A partial-scope decision is made once.

The capability check is recomputed whenever the agent calls it, and it used to reset
`user_decision` every time. So the user confirmed a partial scope, the agent checked
again before proposing, the confirmation was gone, and research_plan was refused with a
request for the same decision that had just been given.
"""

from physearth import session as session_state
from physearth.research import capability


def _confirmed_session():
    box = session_state.new_session("m")
    capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    capability.capability_check(box, decision="confirm_partial")
    return box


def test_the_first_check_asks():
    box = session_state.new_session("m")
    report = capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    assert report["status"] == "waiting_user"
    assert report["user_decision"] is None


def test_a_confirmed_decision_survives_the_next_check():
    box = _confirmed_session()
    again = capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    assert again["status"] == "confirmed", "the user was asked to decide twice"
    assert again["user_decision"] == "partial"


def test_the_session_keeps_the_confirmation():
    """research_plan reads it off the session, so that is what has to hold it."""
    box = _confirmed_session()
    capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    assert (box.get("capability_review") or {}).get("status") == "confirmed"


def test_a_wider_scope_asks_again():
    """The decision covers what was shown. Something newly unavailable is a new question."""
    box = _confirmed_session()
    wider = capability.capability_check(
        box,
        question="Reproduce SMRT figure 4",
        reference_models=["SMRT", "MEMLS", "DMRT-ML"],
    )
    assert wider["status"] == "waiting_user"
    assert wider["user_decision"] is None


def test_a_narrower_scope_still_stands():
    box = _confirmed_session()
    narrower = capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT"]
    )
    assert narrower["status"] in ("confirmed", "ready", "waiting_resources")
    assert narrower["status"] != "waiting_user"


def test_a_rejection_is_not_treated_as_a_confirmation():
    box = session_state.new_session("m")
    capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    capability.capability_check(box, decision="reject")
    again = capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    assert again["status"] == "waiting_user"
    assert again["user_decision"] is None


# --- a formulation is a configuration, not a missing model ---------------------------
#
# A paper names the theory: "SMRT IBA", "SMRT QCA short range". The card names one model
# with electromagnetic_model set two ways. Treating the paper's names as unregistered
# models made the check report that smrt "is not an equivalent implementation of SMRT
# IBA", which is backwards -- it is that implementation, configured.


def _session_with_smrt_resources():
    from physearth import registry

    box = session_state.new_session("m")
    card = registry.get("smrt").card
    box["models_inspected"] = {"smrt@%s" % card["version"]}
    box["model_instructions_read"] = {
        "smrt@%s" % (card.get("instruction_version") or "1.0")
    }
    return box


def test_a_declared_formulation_resolves_to_the_model_that_declares_it():
    from physearth import registry

    for name, expected in (
        ("SMRT IBA", {"electromagnetic_model": "iba"}),
        ("SMRT QCA short range", {"electromagnetic_model": "dmrt_qca_shortrange"}),
        ("SMRT exponential", {"microstructure_model": "exponential"}),
    ):
        model, canonical, configuration, options = registry.resolve_configuration(name)
        assert model is not None and canonical == "smrt", name
        assert configuration == expected, (name, configuration)
        assert options == [], name


def test_an_unregistered_model_still_does_not_resolve():
    """The whole point of the check. DMRT-QMS is a different package, not a setting."""
    from physearth import registry

    for name in ("DMRT-QMS", "MEMLS", "DMRT-ML"):
        model, canonical, configuration, options = registry.resolve_configuration(name)
        assert model is None and canonical is None, name
        assert configuration == {} and options == [], name


def test_smrt_formulations_are_supported_not_incomparable():
    box = _session_with_smrt_resources()
    report = capability.capability_check(
        box,
        question="Reproduce SMRT figure 3",
        reference_models=["SMRT QCA short range", "SMRT IBA", "DMRT-QMS"],
        local_models=["smrt"],
    )
    unavailable = {item["model"] for item in report["unavailable"]}
    assert unavailable == {"DMRT-QMS"}, unavailable
    incomparable = {item["reference_model"] for item in report["not_comparable"]}
    assert incomparable == {"DMRT-QMS"}, incomparable
    # One row per model, carrying every configuration the paper's names asked for.
    configured = [
        option
        for item in report["supported"]
        for option in (item.get("configurations") or [])
    ]
    assert {"electromagnetic_model": "iba"} in configured
    assert {"electromagnetic_model": "dmrt_qca_shortrange"} in configured
    assert len([i for i in report["supported"] if i["model"] == "smrt"]) == 1, (
        "one model listed once, however many of its formulations were asked for"
    )


def test_the_report_says_which_configuration_each_name_was_taken_to_mean():
    """Visible rather than silent: a reader has to be able to object to the match."""
    box = _session_with_smrt_resources()
    report = capability.capability_check(
        box,
        question="Reproduce SMRT figure 3",
        reference_models=["SMRT IBA"],
        local_models=["smrt"],
    )
    resolved = {item["asked"]: item for item in report["resolved_names"]}
    assert resolved["SMRT IBA"]["registered"] == "smrt"
    assert resolved["SMRT IBA"]["configuration"] == {"electromagnetic_model": "iba"}


def test_an_underspecified_formulation_is_still_its_model():
    """A paper's shorthand that does not pin one declared value still names the model.

    "SMRT QCA" matches two declared electromagnetic models. Refusing it made the report
    say the model was not registered, and then that smrt is not an equivalent
    implementation of it -- wrong twice, about a model sitting in the registry. The name
    resolves; the choice is what is left open.
    """
    from physearth import registry

    model, canonical, configuration, options = registry.resolve_configuration("SMRT QCA")
    assert model is not None and canonical == "smrt"
    assert configuration == {}, "an ambiguous name must not silently pick one"
    assert len(options) == 2, options
    assert all(len(option) == 1 for option in options)


def test_a_name_that_only_starts_like_a_model_still_does_not_resolve():
    """The prefix is not enough. The remainder has to be something the card declares."""
    from physearth import registry

    model, canonical, configuration, options = registry.resolve_configuration("SMRT nonsense")
    assert model is None and canonical is None and configuration == {} and options == []


def test_an_underspecified_reference_is_supported_not_missing():
    box = _session_with_smrt_resources()
    report = capability.capability_check(
        box,
        question="Reproduce figures 4 and 5",
        reference_models=["SMRT QCA", "DMRT-ML", "DMRT-QMS"],
        local_models=["smrt"],
    )
    assert {item["model"] for item in report["unavailable"]} == {"DMRT-ML", "DMRT-QMS"}
    assert {item["reference_model"] for item in report["not_comparable"]} == {
        "DMRT-ML",
        "DMRT-QMS",
    }
    offered = [
        item["configuration_options"]
        for item in report["supported"]
        if item.get("configuration_options")
    ]
    assert offered and len(offered[0]) == 2, "the plan is not told what it must choose between"


def test_mapping_an_output_as_an_input_says_it_is_an_output():
    """Naming the mistake, not just rejecting the value.

    A plan mapped ks_per_m -- a declared output -- as a model input. The error said only
    "an exact registered model input" and listed the inputs, so the agent swapped one
    output name for another and failed five times in a row. The quantity was real and
    belonged in the plan; it belonged under outputs.
    """
    from physearth import session as session_state
    from physearth.research import mapping

    box = session_state.new_session("m")
    result = mapping._repair_parameter_mappings(
        box,
        [{"paper_name": "scattering coefficient", "model_input": "ks_per_m",
          "model": "smrt", "value": 1.0}],
        [{"id": "r1", "model": "smrt", "parameters": {}}],
        {}, {}, {}, set(),
    )

    def walk(value):
        if isinstance(value, dict) and "field" in value:
            yield value
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from walk(item)

    hits = [p for p in walk(result) if "model_input" in str(p.get("field"))]
    assert hits, "an output used as an input must still be refused"
    assert hits[0]["expected"] == "an input, not a declared output"
    assert "is an output of" in hits[0]["repair"]
    assert "outputs" in hits[0]["repair"]


def test_a_figure_legend_resolves_entry_by_entry():
    """A legend writes the theory without the package, and often two values at once.

    Figure 3's legend is six SMRT series -- "Independent spheres (Rayleigh)",
    "Non-sticky hard spheres (DMRT QCA-CP)" and so on. Requiring the model name in front
    meant every one of them read back as an unregistered model, and then as something
    smrt "is not an equivalent implementation of".
    """
    from physearth import registry

    legend = [
        ("Independent spheres (Rayleigh)",
         {"microstructure_model": "independent_sphere", "electromagnetic_model": "rayleigh"}),
        ("Independent spheres (IBA)",
         {"microstructure_model": "independent_sphere", "electromagnetic_model": "iba"}),
        ("Non-sticky hard spheres (IBA)",
         {"microstructure_model": "non_sticky_hard_spheres", "electromagnetic_model": "iba"}),
        ("Sticky hard spheres (IBA)",
         {"microstructure_model": "sticky_hard_spheres", "electromagnetic_model": "iba"}),
    ]
    for name, expected in legend:
        model, canonical, configuration, _options = registry.resolve_configuration(name)
        assert canonical == "smrt", name
        assert configuration == expected, (name, configuration)


def test_the_more_specific_declared_value_wins():
    """`sticky_hard_spheres` is a substring of `non_sticky_hard_spheres`."""
    from physearth import registry

    _m, _c, configuration, _o = registry.resolve_configuration("Non-sticky hard spheres")
    assert configuration == {"microstructure_model": "non_sticky_hard_spheres"}


def test_a_bare_name_no_card_declares_still_does_not_resolve():
    """Dropping the prefix requirement must not turn every string into a model."""
    from physearth import registry

    for name in ("DMRT-ML", "DMRT-QMS", "MEMLS", "nonsense"):
        model, canonical, configuration, options = registry.resolve_configuration(name)
        assert model is None and canonical is None, name
        assert configuration == {} and options == [], name


def test_a_rejected_proposal_survives_a_mixed_problem_list():
    """The problems are not all the same shape, and reading them as one shape crashed.

    The evidence checks append dicts carrying a `field`; the coverage checks append plain
    sentences. The recovery message names the fields to patch, and reading every entry as
    a dict raised AttributeError: 'str' object has no attribute 'get' -- from inside the
    handler for a rejected plan, so the whole turn died instead of returning the refusal
    it was in the middle of explaining.
    """
    from physearth import registry, session as session_state
    from physearth.research import capability
    from physearth.tools import planning

    box = session_state.new_session("m")
    box["research_required"] = True
    box["research_context"] = {"reproduction_case": "paper-reproduction"}
    box["research_guidelines_read"] = {"research-planning"}
    card = registry.get("smrt").card
    box["models_inspected"] = {"smrt@%s" % card["version"]}
    box["model_instructions_read"] = {"smrt@%s" % (card.get("instruction_version") or "1.0")}
    capability.capability_check(
        box, question="Reproduce figure 3", reference_models=["SMRT"], local_models=["smrt"]
    )

    result = planning.research_plan(
        action="propose",
        question="Reproduce figure 3 of the SMRT paper",
        objective="Reproduce the sparse-medium comparison",
        hypothesis="Scattering rises with density",
        runs=[{"id": "r1", "model": "smrt", "parameters": {"frequency_ghz": 37.0}}],
        charts=[{"id": "c1", "title": "ks", "x": "density_kg_m3",
                 "y": ["ks_per_m"], "run_ids": ["r1"]}],
        reproduction_targets=[{"id": "t1"}],   # thin on purpose: this must be refused
        literature_evidence=["smrt-v1#03"],
        _session=box,
    )

    assert result["status"] != "success"
    recovery = (result.get("data") or {}).get("recovery") or ""
    assert "revise_plan" in recovery, "a refusal must still say how to correct it"

    problems = (result.get("data") or {}).get("problems") or []
    if problems:
        kinds = {type(problem).__name__ for problem in problems}
        assert kinds, "the refusal recorded no problems at all"
