"""Several direct runs under one approval: run_models."""

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
