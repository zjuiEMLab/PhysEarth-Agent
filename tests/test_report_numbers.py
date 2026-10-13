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


# ── a figure's own values are what a report quotes, and the paper is not made to say them ──
def test_the_values_a_figure_drew_are_accounted_for(recorded):
    """The figure of a computed quantity draws a saved result; its numbers are known.

    A report that quoted the eight scaling factors its own figure showed was refused for
    four of them, because the figure record kept only the handle and the check never read
    what the figure drew -- while two wrong numbers passed by coincidence with a sweep
    coordinate. The report here quotes what the figure drew, and one number it did not.
    """
    from physearth.harness import results

    values = [3.9633, 3.2797, 2.8845, 2.5325, 2.2110, 1.9054, 1.6584, 1.4588]
    handle = results.put({
        "model": "analysis_script", "version": "abc",
        "spec": {"script_sha256": "abc", "name": "scaling_factor"},
        "axis": {"name": "stickiness", "values": [0.08, 0.1, 0.12, 0.15, 0.2, 0.3, 0.5, 1.0]},
        "series": {"scaling_factor": values}, "points": [], "units": {},
    }, recorded["id"])
    recorded["figures"] = [{
        "figure_number": 1,
        "series": [{"handle": handle, "x": "stickiness", "y": "scaling_factor"}],
    }]
    report = (
        "The scaling factors are 3.96 at stickiness 0.08 and 1.46 at stickiness 1.0; the "
        "curve passes through 2.53, 2.21 and 1.91 on the way down."
    )
    assert numbers.unsupported(recorded, report) == []

    wrong = "The scaling factors are 3.226 at stickiness 0.1 and 3.28 at stickiness 0.12."
    # 3.226 is not the figure's 3.2797; it only looked accounted for because it is a
    # coordinate on the sweep. A bare "3" is not one of the measured numbers this reads.
    assert [item["number"] for item in numbers.unsupported(recorded, wrong)] == ["3.226"]


def test_a_configured_value_is_not_rounded_into_a_result(recorded):
    """3.2263 is a coordinate on a run's own sweep, not the 3.226 a report claims it measured."""
    run = {
        "handle": "res_sweep", "model": "smrt", "version": "1.5.1",
        "spec": {"frequency_ghz": 37.0},
        "axis": {"name": "stickiness", "values": [0.1, 3.2263157894736847, 1.6631578947368424]},
        "series": {"tb_v": [230.0, 261.1, 261.6]}, "points": [], "diagnostics": {},
    }
    artifacts.persist_run(PROJECT, PROJECT, "res_sweep", run)
    report = "The fitted scaling factor is 3.226 at the first point and 1.66 at the last."
    assert [item["number"] for item in numbers.unsupported(recorded, report)] == ["3.226", "1.66"]


def test_a_number_the_paper_is_made_to_say_is_refused():
    """The section cited has to state the number, not just have been opened."""
    session = {"id": "ses_paper_numbers", "research": {"research_id": "ses_paper_numbers"}}
    report = (
        "This reproduces the trend in SMRT v1.0 Section 3.2 [smrt-v1#09], which states that "
        "higher scaling factors (up to 3.747) correspond to lower stickiness values "
        "approaching 0.1."
    )
    findings = numbers.misattributed(session, report)
    assert [item["number"] for item in findings] == ["3.747"]
    assert "smrt-v1#09" in findings[0]["section"]

    # The section's own numbers are what a reproduction may quote.
    honest = (
        "The paper reports a grain size scaling factor of 2.1 for a stickiness of around 0.13 "
        "[smrt-v1#09], and up to 3.5 for stickiness approaching 0.1."
    )
    assert numbers.misattributed(session, honest) == []

    # A run's own number in a sentence that happens to cite the paper is not the paper's.
    run_claim = "Our curve gives 3.28 at 0.1, above the 2.1 the paper reports [smrt-v1#09]."
    assert numbers.misattributed(session, run_claim) == []
