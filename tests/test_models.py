import copy

import pytest

from physearth import tools, validation
from physearth.models import contract, registry

EXAMPLE = __import__("pathlib").Path(__file__).resolve().parent.parent / "examples" / "toy_model"


@pytest.fixture
def card():
    return copy.deepcopy(registry.get("smrt").card)


def test_bundled_model_registers_cleanly():
    assert "smrt" in registry.names()
    assert registry.rejected() == []
    assert registry.get("smrt").runnable


def test_declaration_check_rejects_a_range_free_numeric_parameter(card):
    del card["parameters"]["frequency_ghz"]["minimum"]
    problems = contract.validate_card(card)
    assert any("minimum and maximum" in p for p in problems)


def test_declaration_check_rejects_a_bound_yaml_loaded_as_text(card):
    card["parameters"]["frequency_ghz"]["maximum"] = "1.0e9"
    problems = contract.validate_card(card)
    assert any("non-numeric bound" in p for p in problems)


def test_declaration_check_requires_a_reason_on_every_combination(card):
    del card["combinations"][0]["reason"]
    assert any("reason" in p for p in contract.validate_card(card))


def test_out_of_range_parameter_is_refused(card):
    _, problems = validation.resolve(card, {"density_kg_m3": 2000})
    assert problems and "outside the physical range" in problems[0]


def test_illegal_theory_and_microstructure_pair_is_refused(card):
    _, problems = validation.resolve(
        card, {"electromagnetic_model": "dmrt_qca_shortrange", "microstructure_model": "exponential"}
    )
    assert problems and "sticky_hard_spheres" in problems[0]


def test_sweep_bounds_are_checked_against_the_swept_parameter(card):
    _, problems = validation.resolve(
        card, {"sweep_parameter": "density_kg_m3", "sweep_start": 50, "sweep_stop": 1200}
    )
    assert problems and "physical range of density_kg_m3" in problems[0]


def test_defaults_are_filled_from_the_card(card):
    spec, problems = validation.resolve(card, {})
    assert not problems
    assert spec["frequency_ghz"] == 37.0
    assert spec["electromagnetic_model"] == "iba"


def test_quality_control_flags_values_outside_declared_bounds(card):
    result = {"axis": None, "points": [], "series": {"tb_v": [400.0]}}
    qc = validation.quality_control(card, result)
    assert not qc["passed"]


def test_quality_control_flags_an_undeclared_output(card):
    qc = validation.quality_control(card, {"axis": None, "points": [], "series": {"mystery": [1.0]}})
    assert not qc["passed"]


def test_run_model_rejects_before_running_and_says_why():
    result = tools.call("run_model", {"model": "smrt", "parameters": {"temperature_k": 400}})
    assert result["status"] == "needs_input"
    assert "273.15" in result["error"]


def test_run_model_returns_quality_controlled_output():
    result = tools.call("run_model", {"model": "smrt", "parameters": {"frequency_ghz": 19.0}})
    assert result["status"] == "success"
    assert result["qc"]["passed"]
    assert set(result["data"]["series"]) == {"tb_v", "tb_h"}


def test_an_external_model_registers_without_touching_the_harness(monkeypatch):
    monkeypatch.setenv(registry.EXTRA_DIRS_ENV, str(EXAMPLE))
    registry.reload()
    try:
        assert "toy_rayleigh" in registry.names()
        result = tools.call("run_model", {"model": "toy_rayleigh", "parameters": {"optical_depth": 1.0}})
        assert result["status"] == "success" and result["qc"]["passed"]
        refused = tools.call("run_model", {"model": "toy_rayleigh", "parameters": {"optical_depth": 999}})
        assert refused["status"] == "needs_input"
    finally:
        monkeypatch.delenv(registry.EXTRA_DIRS_ENV, raising=False)
        registry.reload()


def test_a_broken_card_is_rejected_without_breaking_startup(tmp_path, monkeypatch):
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "model_card.yaml").write_text("name: broken\ntier: demo\n", encoding="utf-8")
    monkeypatch.setenv(registry.EXTRA_DIRS_ENV, str(tmp_path))
    registry.reload()
    try:
        assert "smrt" in registry.names()
        assert any(item["directory"].endswith("broken") for item in registry.rejected())
    finally:
        monkeypatch.delenv(registry.EXTRA_DIRS_ENV, raising=False)
        registry.reload()
