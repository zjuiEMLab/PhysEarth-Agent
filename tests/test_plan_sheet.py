"""The plan as a conditions sheet and a run matrix, for any model and any plan."""

import glob
import json
from pathlib import Path

import pytest

from apps.studio.views.parts import plan_sheet_html
from physearth.research import sheet

ROOT = Path(__file__).resolve().parent.parent


def _run(run_id, model, **overrides):
    parameters = {"frequency_ghz": 37.0, "thickness_m": 1.0, "temperature_k": 265.0,
                  "sweep_parameter": "density_kg_m3", "sweep_start": 1, "sweep_stop": 100,
                  "sweep_points": 20, "density_kg_m3": 300.0}
    parameters.update(overrides)
    return {"id": run_id, "model": model, "label": run_id, "stage": "main", "parameters": parameters,
            "defaulted_parameters": ["thickness_m", "temperature_k", "density_kg_m3"]}


PLAN = {
    "runs": [_run("a", "smrt", electromagnetic_model="rayleigh"),
             _run("b", "smrt", electromagnetic_model="iba"),
             _run("c", "smrt", electromagnetic_model="iba", sweep_stop=30)],
    "charts": [{"id": "fig", "x": "density_kg_m3", "y": "ks_per_m", "ys": ["ks_per_m"], "required": True}],
    "parameter_mapping": [
        {"model": "smrt", "model_input": "frequency_ghz", "mapped_value": 37.0,
         "provenance_class": "paper_explicit", "evidence_ref": "paper#07"},
        {"model": "smrt", "model_input": "electromagnetic_model", "mapped_value": "iba",
         "provenance_class": "model_assumption", "rationale": "the paper compares both"},
    ],
}


def test_what_is_the_same_is_shown_once_and_what_differs_is_a_column():
    group = sheet.build(PLAN)["groups"][0]
    assert {c["name"] for c in group["conditions"]} == {"frequency_ghz", "thickness_m", "temperature_k"}
    assert [c["name"] for c in group["columns"]] == ["electromagnetic_model"]
    assert group["sweep_varies"] and [r["sweep"] for r in group["runs"]][0].endswith("(20 points)")


def test_each_value_carries_where_it_came_from():
    conditions = {c["name"]: c for c in sheet.build(PLAN)["groups"][0]["conditions"]}
    assert conditions["frequency_ghz"]["tag"] == "extracted" and conditions["frequency_ghz"]["ref"] == "paper#07"
    assert conditions["thickness_m"]["tag"] == "default"


def test_an_assumption_with_no_reason_is_guessed_and_asks_for_a_decision():
    plan = json.loads(json.dumps(PLAN))
    plan["parameter_mapping"][1].pop("rationale")
    sh = sheet.build(plan)
    assert [d["name"] for d in sh["decisions"]] == ["electromagnetic_model"]
    assert sh["decisions"][0]["tag"] == "guessed"


def test_a_value_with_no_recorded_source_is_unlabelled_not_hidden():
    plan = {"runs": [_run("a", "smrt"), _run("b", "smrt")], "charts": []}
    tags = {c["name"]: c["tag"] for c in sheet.build(plan)["groups"][0]["conditions"]}
    assert tags["frequency_ghz"] == "unlabelled"


def test_each_chart_lists_the_runs_that_feed_it():
    charts = sheet.build(PLAN)["charts"]
    assert charts[0]["runs"] == ["a", "b", "c"]


def test_two_models_get_two_groups():
    plan = {"runs": [_run("a", "smrt"), _run("b", "tau_omega")], "charts": []}
    assert [g["model"] for g in sheet.build(plan)["groups"]] == ["smrt", "tau_omega"]


def test_an_empty_plan_renders_nothing():
    assert plan_sheet_html({}) == "" and sheet.build({})["groups"] == []


def test_the_page_shows_sources_and_decisions():
    html = plan_sheet_html(PLAN)
    assert "src--extracted" in html and "src--default" in html and "Conditions, the same in every run" in html
    assert "Runs, only what differs" in html


def test_the_sheet_names_no_model_parameter_or_paper():
    """Nothing in the builder is specific to a benchmark; grouping and units come from the plan."""
    source = (ROOT / "src" / "physearth" / "research" / "sheet.py").read_text().lower()
    for word in ("smrt", "ghz", "density", "sticky", "rayleigh", "prosail", "pyet", "figure 3"):
        assert word not in source, word


RECORDS = [f for f in glob.glob(str(ROOT / "evaluation/results/competition/**/*.json"), recursive=True)
           if not f.endswith(("scores.json", "scored_runs.json")) and "oracle" not in f and "preflight" not in f]


def _committed_plans():
    for path in RECORDS:
        try:
            record = json.load(open(path))
        except (OSError, ValueError):
            continue
        plan = ((record.get("research") or {}).get("plan") or {}) if isinstance(record, dict) else {}
        if plan.get("runs"):
            yield plan


@pytest.mark.skipif(not RECORDS, reason="no committed evaluation records")
def test_every_committed_plan_lays_out_losslessly():
    """Across every recorded plan and every model: no error, and no parameter value is lost."""
    seen = 0
    for plan in _committed_plans():
        seen += 1
        sh = sheet.build(plan)
        plan_sheet_html(plan)
        for group in sh["groups"]:
            runs = [r for r in plan["runs"] if r.get("model") == group["model"]]
            shown = {c["name"] for c in group["conditions"]} | {c["name"] for c in group["columns"]}
            shown |= set(sheet._SWEEP_FIELDS)
            swept = {str((r.get("parameters") or {}).get("sweep_parameter")) for r in runs}
            for run in runs:
                for name in (run.get("parameters") or {}):
                    assert name in shown or name in swept, (group["model"], name)
    assert seen > 0
