"""Several direct runs under one approval: run_models."""

import json

import pytest

from physearth import registry
from physearth import session as session_state
from physearth import tools
from physearth.harness import approval

SMRT = registry.get("smrt")
pytestmark = pytest.mark.skipif(SMRT is None or not SMRT.runnable, reason="SMRT is not installed")

DEPTH = {"sweep_parameter": "thickness_m", "sweep_start": 0.1, "sweep_stop": 1.0, "sweep_points": 4}
BATCH = [
    {"model": "smrt", "label": "tb %d K" % t, "parameters": dict(DEPTH, temperature_k=t)}
    for t in (240.0, 260.0)
] + [{"model": "smrt", "label": "sigma 240 K",
      "parameters": dict(DEPTH, output="sigma", angle_deg=40.0, frequency_ghz=17.2,
                         temperature_k=240.0)}]


def test_a_batch_runs_every_item_through_the_usual_checks():
    session = session_state.new_session()
    result = tools.run_models(runs=BATCH, _session=session)
    assert result["status"] == "success"
    runs = result["data"]["runs"]
    assert [item["status"] for item in runs] == ["success"] * 3
    assert len(set(result["data"]["handles"])) == 3
    assert all(item["qc"]["passed"] for item in runs)


def test_an_invalid_item_is_refused_without_losing_the_others():
    session = session_state.new_session()
    runs = BATCH[:1] + [{"model": "smrt", "parameters": {"volumetric_liquid_water": 0.01}}]
    result = tools.run_models(runs=runs, _session=session)
    assert result["status"] == "success"
    assert [item["status"] for item in result["data"]["runs"]] == ["success", "needs_input"]
    assert result["data"]["failed_runs"] == [2]


def test_one_approval_request_lists_every_run():
    described = approval.describe("run_models", {"runs": BATCH})
    assert described["shape"] == "a batch of 3 run(s)"
    assert list(described["parameters"]) == ["run 01", "run 02", "run 03"]
    assert described["parameters"]["run 01"].startswith("tb 240 K: ")
    assert "label" not in described["parameters"]["run 01"]
    assert "sweep thickness_m" in described["parameters"]["run 03"]


def test_the_studio_button_approves_the_whole_batch_at_once():
    from apps.studio import studio as app

    box = session_state.new_session("m")
    approval.set_mode(box, approval.ASK)
    approval.request(box, "run_models", {"runs": BATCH})
    command = app.review_click(box, "primary")[3]
    assert command == "Approved the run of smrt as a batch of 3 run(s)."
    assert approval.pending(box) is None


def test_the_run_path_offers_the_batch_tool():
    assert "run_models" in tools.RUN_PATH_TOOLS
    assert any(spec["function"]["name"] == "run_models" for spec in tools.SPECS)


SIX = [
    {"model": "smrt", "label": "tb %d K" % t, "parameters": dict(DEPTH, temperature_k=t)}
    for t in (240.0, 255.0, 265.0)
] + [
    {"model": "smrt", "label": "sigma %d K" % t,
     "parameters": dict(DEPTH, output="sigma", angle_deg=40.0, frequency_ghz=17.2, temperature_k=t)}
    for t in (240.0, 255.0, 265.0)
]


def test_the_batch_summary_carries_each_runs_numbers_not_only_a_handle():
    # Measured on a six-run snow study: the payload serialised to 33k characters, the transcript
    # keeps only the first 12k of a tool result, and the cut fell inside run 3 — so the model
    # never saw any backscatter number, wrote its answer around a handle and a "quality control
    # passed", and reported backscatter values that appear nowhere in the engine's output, with
    # the trend inverted. The summary is the part that always arrives.
    from physearth.tools.runs import _short_number

    result = tools.run_models(runs=BATCH, _session=session_state.new_session())
    summary = result["summary"]

    for item in result["data"]["runs"]:
        assert "handle %s" % item["data"]["handle"] in summary
        readings = item["data"]["series_summary"]
        named = [name for name in readings if name != "swe_mm"]
        assert named, item["label"]
        for name in named:
            entry = readings[name]
            assert "%s %s -> %s" % (
                name, _short_number(entry["first"]), _short_number(entry["last"]),
            ) in summary, name
            assert entry["monotonic"] in summary, name


def test_a_six_run_summary_survives_the_tool_result_budget():
    # The batch that failed: six runs, the numbers for the last three past the cut. Whatever the
    # payload's total length, the summary has to fit and keep every run's numbers.
    from physearth.agent.constants import MAX_KEPT_TOOL_CHARS
    from physearth.agent.messages import _short_content

    result = tools.run_models(runs=SIX, _session=session_state.new_session())
    summary = result["summary"]
    assert len(summary) < MAX_KEPT_TOOL_CHARS, "the summary alone must fit the budget"

    payload = {k: v for k, v in result.items() if k not in ("qc", "ui")}
    kept = _short_content(json.dumps(payload, ensure_ascii=False), MAX_KEPT_TOOL_CHARS)
    for label in ("tb 240 K", "tb 265 K", "sigma 240 K", "sigma 265 K"):
        assert "'%s'" % label in kept, label
    for name in ("sigma_vv_db", "sigma_hh_db", "sigma_hv_db"):
        assert name in kept, name
    assert "increasing" in kept


def test_each_run_keeps_its_quality_control_so_the_caveats_have_a_source():
    # The agent raising physical caveats is a feature, not noise: it flags, for instance, that
    # every run used the card's default 0.15 mm correlation length, that 17.2 GHz was chosen
    # because the rough-soil IEM substrate is only valid to there, and that a depth sweep this
    # short has not reached the semi-infinite limit. Those all trace back to the per-run quality
    # control and to `defaults_to_review`, so both travel with the batch.
    result = tools.run_models(runs=BATCH, _session=session_state.new_session())
    for item in result["data"]["runs"]:
        advisories = [check for check in (item["qc"] or {}).get("checks", []) if check.get("advisory")]
        assert advisories, item["label"]
        assert all(check.get("expectation") for check in advisories)
        assert "defaults_to_review" in item["data"]
