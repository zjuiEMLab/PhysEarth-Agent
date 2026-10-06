"""A chart can name the runs it draws, so several sweeps over one axis can be split."""

from physearth.research import charts as charts_module
from physearth.research import mapping, normalise


def _run(run_id, start, stop):
    return {
        "id": run_id, "label": run_id, "model": "smrt", "stage": "main",
        "parameters": {"output": "coefficients", "sweep_parameter": "density_kg_m3",
                       "sweep_start": start, "sweep_stop": stop},
    }


FULL = [_run("full_%d" % i, 1, 100) for i in range(6)]
WINDOW = [_run("window_%d" % i, 1, 30) for i in range(6)]
RUNS = FULL + WINDOW


def _chart(chart_id, **extra):
    return {"id": chart_id, "label": chart_id, "kind": "line", "x": "density_kg_m3",
            "y": "ks_per_m", "ys": ["ks_per_m"], "required": True, **extra}


def test_two_sweeps_over_one_axis_overflow_one_chart():
    problems = charts_module._validate_chart_runs([_chart("both")], RUNS)
    assert any("12 series" in problem and "runs field" in problem for problem in problems)


def test_naming_the_runs_splits_the_sweeps_into_charts_that_fit():
    split = [_chart("full", runs=[r["id"] for r in FULL]),
             _chart("window", runs=[r["id"] for r in WINDOW])]
    assert charts_module._validate_chart_runs(split, RUNS) == []


def test_a_chart_only_draws_the_runs_it_names():
    chart = _chart("full", runs=["full_0", "full_1"])
    drawn = [r["id"] for r in RUNS if charts_module._run_produces_chart(r, chart)]
    assert drawn == ["full_0", "full_1"]


def test_a_chart_naming_an_unplanned_run_is_refused():
    problems = charts_module._validate_chart_runs([_chart("x", runs=["full_0", "ghost"])], RUNS)
    assert any("ghost" in problem for problem in problems)


def test_the_runs_field_survives_normalisation():
    cleaned = normalise._clean_charts(
        [{"id": "c", "x": "density_kg_m3", "y": "ks_per_m", "runs": ["full_0", "full_1"]}]
    )
    assert cleaned[0]["runs"] == ["full_0", "full_1"]
    assert "runs" not in normalise._clean_charts([{"id": "d", "x": "density_kg_m3", "y": "ks_per_m"}])[0]


def test_a_combined_mapping_row_is_told_to_become_one_row_per_input():
    from physearth import session as session_state
    session = session_state.new_session()
    runs = [{"id": "r1", "model": "smrt", "parameters": {"sweep_parameter": "density_kg_m3"}}]
    _, _, problems, _, _ = mapping._repair_parameter_mappings(
        session,
        [{"model": "smrt", "model_input": "thickness_m / angle_deg", "mapped_value": 1.0,
          "provenance_class": "backend_default"}],
        runs, [], {}, {}, set(),
    )
    assert problems and "one row per input" in problems[0]["repair"]
    assert "thickness_m, angle_deg" in problems[0]["repair"]
