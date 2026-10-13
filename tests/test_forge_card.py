"""The forge registration of SMRT: constraints, physical expectations and their warnings.

These pin what the APGARSS comparisons established: a rise of brightness temperature against
snow water equivalent is never silent, wet snow is held at the melting point, and the new card
fields are validated rather than ignored.
"""

import copy

import pytest

from physearth import registry
from physearth import session as session_state
from physearth import tools
from physearth.harness import validation
from physearth.registry import contract

SMRT = registry.get("smrt")
pytestmark = pytest.mark.skipif(SMRT is None or not SMRT.runnable, reason="SMRT is not installed")

DEPTH = {"sweep_parameter": "thickness_m", "sweep_start": 0.05, "sweep_stop": 2.0, "sweep_points": 8}
SPHERES = {"microstructure_model": "sticky_hard_spheres", "radius_m": 2e-4, "stickiness": 0.2}


def _run(**parameters):
    return tools.run_model(model="smrt", parameters=parameters, _session=session_state.new_session())


def _warned(result):
    return {c["expectation"] for c in result["qc"]["checks"] if c.get("advisory") and not c["passed"]}


def test_the_card_validates_with_its_new_sections():
    assert contract.validate_card(SMRT.card) == []
    assert SMRT.card["parameters"]["substrate"]["default"] == "rough_soil"


def test_a_constraint_naming_an_unknown_parameter_is_rejected():
    card = copy.deepcopy(SMRT.card)
    card["constraints"].append({"when": {"nope": {"gt": 0}}, "require": {"temperature_k": {"eq": 1}}, "reason": "x"})
    assert any("unknown parameter 'nope'" in p for p in contract.validate_card(card))


def test_an_expectation_without_a_reason_is_rejected():
    card = copy.deepcopy(SMRT.card)
    card["physics"]["expectations"][0].pop("reason")
    assert any("reason" in p for p in contract.validate_card(card))


def test_wet_snow_below_the_melting_point_is_refused_with_the_reason():
    _, problems = validation.resolve(SMRT.card, {"volumetric_liquid_water": 0.01, "temperature_k": 265.0})
    assert problems and "273.15" in problems[0] and "melting point" in problems[0]


def test_a_wetness_sweep_from_dry_still_needs_the_melting_point():
    arguments = {"temperature_k": 265.0, "sweep_parameter": "volumetric_liquid_water",
                 "sweep_start": 0.0, "sweep_stop": 0.02}
    assert validation.resolve(SMRT.card, arguments)[1]


def test_every_tb_and_sigma_run_returns_swe():
    result = _run(**DEPTH)
    assert "swe_mm" in result["data"]["series_summary"]
    assert result["data"]["series_summary"]["swe_mm"]["last"] == pytest.approx(600.0)


def test_tb_rising_with_swe_on_a_flat_soil_is_warned():
    """APGARSS run 2, arm B: 0.2 mm spheres on a flat soil, TbH rose 9.8 K with no warning."""
    result = _run(**SPHERES, substrate="flat_soil", frequency_ghz=37.0, **DEPTH)
    assert "tb-h-falls-with-swe" in _warned(result)
    assert "over-polarised" in result["summary"] and "no further runs" in result["summary"]


def test_the_default_rough_soil_at_37_ghz_is_not_warned():
    assert not _warned(_run(**SPHERES, frequency_ghz=37.0, **DEPTH))


def test_a_slow_rise_is_warned_on_its_net_change():
    result = _run(**SPHERES, frequency_ghz=18.7, **DEPTH)
    assert {"tb-v-falls-with-swe", "tb-h-falls-with-swe"} & _warned(result)


def test_a_rise_against_swe_from_a_density_sweep_is_warned():
    result = _run(microstructure_model="sticky_hard_spheres", radius_m=3e-4, frequency_ghz=37.0,
                  thickness_m=1.0, sweep_parameter="density_kg_m3", sweep_start=100.0,
                  sweep_stop=500.0, sweep_points=6)
    assert "tb-v-falls-with-swe" in _warned(result)


def test_a_warning_never_fails_quality_control():
    result = _run(substrate="none", frequency_ghz=37.0, **DEPTH)
    assert _warned(result) and result["qc"]["passed"]


def test_the_summary_says_the_soil_followed_a_snow_temperature_sweep():
    result = _run(thickness_m=1.0, sweep_parameter="temperature_k", sweep_start=230.0,
                  sweep_stop=273.15, sweep_points=4)
    assert "soil_temperature_k was not set, so it followed temperature_k" in result["summary"]
    held = _run(thickness_m=1.0, soil_temperature_k=265.0, sweep_parameter="temperature_k",
                sweep_start=230.0, sweep_stop=273.15, sweep_points=4)
    assert "followed" not in held["summary"]


def test_an_unexplained_rise_keeps_the_explicit_warning(monkeypatch):
    card = copy.deepcopy(SMRT.card)
    for item in card["physics"]["expectations"]:
        item.pop("causes", None)
    monkeypatch.setattr(SMRT, "card", card)
    result = _run(substrate="none", frequency_ghz=37.0, **DEPTH)
    assert "WARNING" in result["summary"]


def test_backscatter_outside_the_rough_soil_model_validity_is_refused_with_the_reason():
    """Demo 1 ran sigma at 37 GHz; SMRT's IEM only printed a validity warning and returned numbers."""
    result = _run(output="sigma", angle_deg=40.0, frequency_ghz=37.0, **DEPTH)
    assert not result["qc"]["passed"]
    assert "outside its validity at 37 GHz" in result["summary"]
    assert _run(output="sigma", angle_deg=40.0, frequency_ghz=17.2, **DEPTH)["qc"]["passed"]
