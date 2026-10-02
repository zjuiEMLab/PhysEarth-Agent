"""A plan and its report answer the question that was asked, along the axis it named."""

from physearth import research, session
from physearth.research.charts import (
    _asked_sweep_axes,
    _asked_values,
    _question_coverage_problems,
)

from tests.test_plan_first_time import _plan, _session
from tests.test_research import _proposal

SMRT = [{"model": "smrt"}]


def test_the_axis_a_question_asks_along_is_found_from_the_card():
    assert _asked_sweep_axes(
        "Under what snow-density range do the theories converge, and at what density do "
        "they diverge?", SMRT,
    ) == ["density_kg_m3"]
    assert _asked_sweep_axes("Plot backscatter against incidence angle at 37 GHz.", SMRT) == [
        "angle_deg"
    ]
    assert _asked_sweep_axes(
        "How does brightness temperature change with soil moisture?", [{"model": "tau_omega"}]
    ) == ["soil_moisture"]


def test_a_named_value_is_not_an_axis():
    assert _asked_sweep_axes("What brightness temperature would you expect from snow?", SMRT) == []
    assert _asked_sweep_axes("Run SMRT at a density of 300 kg m-3 and 37 GHz.", SMRT) == []


def test_a_plan_along_the_wrong_axis_is_refused():
    charts = [{"id": "c", "x": "angle_deg", "y": "sigma_vv_db", "required": True}]
    problems = _question_coverage_problems(
        "At what density do the theories diverge?", SMRT, charts,
    )
    assert any("x=density_kg_m3" in item for item in problems)
    charts = [{"id": "c", "x": "density_kg_m3", "y": "ks_per_m", "required": True}]
    assert not _question_coverage_problems("At what density do they diverge?", SMRT, charts)


def test_the_report_contract_asks_for_the_value_the_question_asks():
    box = session.new_session("m")
    _proposal(box, question="At what density does scattering stop growing linearly?")
    assert _asked_values(box["research"]["question"], box["research"]["plan"]["runs"]) == [
        "density_kg_m3"
    ]
    contract = research.report_generation_prompt(box)
    assert "value or range of density (density_kg_m3, in kg m-3)" in contract
    assert "exactly as the ledger records it" in contract


def test_the_parameter_sources_come_from_the_ledger():
    box = _session()
    from physearth import tools

    tools.call("research_plan", _plan(), session=box)
    table = research.parameter_sources_table(box)
    assert table.startswith("**Parameter sources**")
    assert "| smrt | density_kg_m3 | 300.0 | paper_inferred | smrt-v1#08 |" in table
    ledger = box["research"]["plan"]["parameter_mapping"]
    assert table.count("\n| smrt |") == len(ledger)


def test_the_user_question_decides_the_axis_not_the_restated_one():
    box = _session()
    box.setdefault("research_context", {})["question"] = (
        "At what density do the scattering theories diverge?"
    )
    from physearth import tools

    refused = tools.call(
        "research_plan",
        _plan(question="Reproduce Figure 3 of the paper across frequency."),
        session=box,
    )
    assert refused["status"] == "needs_input", refused["summary"]
    box = _session()
    box.setdefault("research_context", {})["question"] = (
        "Under what snow-density range do the theories converge?"
    )
    plan = _plan(question="Reproduce Figure 3 of the paper.")
    plan["runs"][0]["parameters"].update(
        sweep_parameter="frequency_ghz", sweep_start=10, sweep_stop=40
    )
    plan["charts"] = [{"id": "density", "label": "f", "x": "frequency_ghz", "y": "ks_per_m"}]
    refused = tools.call("research_plan", plan, session=box)
    assert refused["status"] == "terminal_error"
    assert "x=density_kg_m3" in refused["summary"]


def test_a_comparison_the_user_asked_for_survives_a_restated_question():
    runs = [{"model": "pyet", "parameters": {"method": "penman"}}]
    charts = [{"id": "c", "x": "air_temperature_c", "y": "et0_mm_day", "required": True}]
    asked = "Compute ET0 with each formulation, compare them and explain why they disagree."
    assert not _question_coverage_problems("Compute ET0 for the example.", runs, charts)
    problems = _question_coverage_problems("Compute ET0 for the example.", runs, charts, asked)
    assert any("formulation attribution" in item for item in problems)
