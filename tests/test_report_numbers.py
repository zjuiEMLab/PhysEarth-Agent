"""A report may state the paper's numbers, but not in a run's place.

The reproduction of Figure 6 wrote the default-IBA absorption coefficient as 0.3426 m-1 --
the paper's value -- where the run had returned 0.3428, then quoted the paper's 0.3426 in
brackets, so the agreement read as exact. These tests pin both halves: that claim is refused,
and the rest of a real report's numbers are not.
"""

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from physearth import artifacts, config  # noqa: E402
from physearth.research import numbers  # noqa: E402

PROJECT = "ses_test_numbers"


@pytest.fixture
def recorded(monkeypatch, tmp_path):
    """A session whose research has one recorded run: kappa_a = 0.34278589 m-1."""
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    run = {
        "handle": "res_default",
        "model": "smrt",
        "version": "1.5.1",
        "spec": {
            "electromagnetic_model": "iba",
            "microstructure_model": "exponential",
            "output": "coefficients",
            "frequency_ghz": 37.0,
            "thickness_m": 100.0,
            "density_kg_m3": 300.0,
            "temperature_k": 265.0,
            "corr_length_m": 0.0001,
            "dort_streams": 32,
        },
        "series": {
            "ks_per_m": [0.20570654743561653],
            "ka_per_m": [0.34278589545917054],
            "effective_permittivity": [1.5238598740331406],
        },
        "points": [],
        "diagnostics": {},
    }
    # The same session recorded both IBA variants and both polarizations: a report is only
    # checked against what its own runs hold, so the fixture holds what the real one did.
    original = json.loads(json.dumps(run))
    original["handle"] = "res_original"
    original["spec"]["electromagnetic_model"] = "iba_original"
    original["series"] = {
        "ks_per_m": [0.20570654743561653],
        "ka_per_m": [0.30888501185354406],
        "effective_permittivity": [1.5238598740331406],
    }
    artifacts.persist_run(PROJECT, PROJECT, "res_original", original)
    artifacts.persist_run(PROJECT, PROJECT, "res_default", run)
    artifacts.persist_figure(PROJECT, PROJECT, 1, {
        "figure_number": 1,
        "comparisons": [
            {"quantity": "tb_v", "bias": 1.2639, "rmse": 1.2644, "r": 0.9999},
            {"quantity": "tb_h", "bias": 1.3752, "rmse": 1.3758, "r": 0.9999},
        ],
    })
    return {"id": PROJECT, "research": {"research_id": PROJECT}}


def test_the_papers_value_is_refused_in_the_runs_place(recorded):
    report = (
        "SMRT IBA default smrt@1.5.1: - Scattering coefficient: ks = 0.2057 m-1 "
        "(unchanged from original) - Absorption coefficient: ka = 0.3426 m-1 "
        "(paper: 0.3426 m-1) - Effective permittivity: 1.5239 (paper: 1.5236)."
    )
    findings = numbers.unsupported(recorded, report)
    assert [item["number"] for item in findings] == ["0.3426"]
    assert findings[0]["recorded"] == "0.3428"
    assert "ka = 0.3426" in findings[0]["context"]


def test_the_runs_own_numbers_and_the_records_are_all_accepted(recorded):
    report = (
        "The absorption coefficient ka = 0.3428 m-1 is higher than the original IBA's "
        "0.3089 m-1, while ks = 0.2057 m-1 and the effective permittivity 1.5239 are unchanged.\n"
        "The run used 37.0 GHz, 300.0 kg m-3, 265.0 K, a 100 m layer, a 100 um correlation "
        "length and 32 DORT streams.\n"
        "The bias is 1.2639 K and the correlation 0.9999."
    )
    assert numbers.unsupported(recorded, report) == []


def test_quoting_the_paper_is_not_a_claim_about_the_run(recorded):
    """A reproduction quotes the paper; the paper's numbers are theirs to state."""
    for report in (
        "The paper reports a difference of 1.2 and 1.6 K at V and H polarization "
        "respectively, and ka = 0.3092 m-1 for MEMLS.",
        "Absorption coefficient: ka = 0.3428 m-1 (paper: 0.3426 m-1).",
        "SMART reports ka (see the publication, 2018) as 0.3426 m-1.",
    ):
        assert numbers.unsupported(recorded, report) == [], report


def test_identifiers_and_rounding_are_not_measurements(recorded):
    report = (
        "Section 3.1.1 compares the two formulations; Figure 6 shows the result. "
        "The difference is about 1.2 K at V and 1.4 K at H, that is 1.26 and 1.38 K."
    )
    assert numbers.unsupported(recorded, report) == []


def test_a_run_value_is_refused_when_no_run_is_recorded(monkeypatch, tmp_path):
    """Nothing recorded cannot account for a number stated as a run's own."""
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    empty = {"id": "ses_nothing_recorded", "research": {"research_id": "ses_nothing_recorded"}}
    findings = numbers.unsupported(empty, "The run returned ka = 0.3426 m-1.")
    assert [item["number"] for item in findings] == ["0.3426"]


def test_the_correction_names_the_number_and_the_recorded_value(recorded):
    findings = numbers.unsupported(recorded, "ka = 0.3426 m-1")
    text = numbers.correction(findings)
    assert "0.3426" in text and "0.3428" in text
    assert "Never change a run's number to match the paper" in text
    assert "0.3426" in numbers.summary(findings)


def test_the_report_contract_asks_for_the_runs_own_numbers(recorded):
    """The gate is a net under a rule the model is told, not a surprise after writing."""
    from physearth.research.report import report_generation_prompt

    prompt = report_generation_prompt(recorded)
    assert "quote the number the run returned" in prompt.lower()


def test_a_real_report_of_this_reproduction_is_refused_only_for_its_wrong_number():
    """The Figure 6 report as delivered, kept as a fixture.

    Its own numbers -- the ks and ka of the original IBA, the effective permittivity, the
    figure's bias and correlation -- are accepted, and the two places that state 0.3426 as
    the run's are refused. That silence about everything else is the point: a check that
    cries wolf on a correct report would be turned off.
    """
    fixture = json.loads(
        (Path(__file__).parent / "fixtures" / "report-numbers-fig06.json").read_text(
            encoding="utf-8"
        )
    )
    assert [item["number"] for item in fixture["findings"]] == ["0.3426", "0.3426"]
    assert {item["recorded"] for item in fixture["findings"]} == {"0.3428"}
    assert re.search(r"0\.3426", fixture["report"])


def test_the_check_reads_the_recorded_parameters_not_only_the_outputs(recorded):
    """A run's own inputs are its numbers too, so a report may quote them."""
    assert numbers.unsupported(recorded, "The layer is 300.0 kg m-3 at 265.0 K.") == []
    assert numbers.unsupported(recorded, "The layer is 900.0 kg m-3 at 265.0 K.") != []
