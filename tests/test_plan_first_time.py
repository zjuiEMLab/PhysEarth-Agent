"""A plan should need as few refusals as the information allows.

Traced runs spent seven refused research_plan calls per run on average: the checks
stopped at the first failure, so each repair exposed the next; fields the session
already knew had to be typed again; and a repair that named one run replaced the whole
run list.
"""

import copy

from physearth import session, tools
from physearth.research import capability

from tests.test_data_driven_workflow import (
    _reproduction_plan_fields,
    _reproduction_resources,
)

QUESTION = "Can the paper's Figure 3 coefficient result be reproduced?"


def _plan(**overrides):
    plan = {
        **_reproduction_plan_fields(),
        "action": "propose",
        "question": QUESTION,
        "objective": "Reproduce the paper coefficient result",
        "hypothesis": "The registered model follows the published trend.",
        "steps": ["read evidence", "run the mapped model", "review the target figure"],
        "runs": [{
            "id": "density", "label": "density reproduction", "model": "smrt",
            "parameters": {
                "output": "coefficients", "sweep_parameter": "density_kg_m3",
                "sweep_start": 10, "sweep_stop": 100, "sweep_points": 12,
            },
        }],
        "charts": [{"id": "density", "label": "density", "x": "density_kg_m3", "y": "ks_per_m"}],
        "quantities": ["ks_per_m"], "controls": ["frequency fixed"], "metrics": ["trend"],
        "diagnostics": ["finite outputs"], "success_criteria": ["trend is comparable"],
        "stop_conditions": ["quality-control failure"], "assumptions": ["homogeneous layer"],
        "limitations": ["one registered model"], "baseline_run_id": "density",
    }
    plan.update(overrides)
    return plan


def _session():
    box = session.new_session("m")
    _reproduction_resources(box)
    tools.call(
        "inspect_paper_figure",
        {"paper": "smrt-v1", "figure_id": "fig03", "focus": "title, axes, and legend"},
        session=box,
    )
    return box


def test_the_complete_plan_is_still_accepted():
    box = _session()
    result = tools.call("research_plan", _plan(), session=box)
    assert result["status"] == "needs_input", result["summary"]


def test_every_failing_check_is_reported_in_one_refusal():
    box = _session()
    result = tools.call(
        "research_plan",
        _plan(
            limitations=[],
            charts=[{"id": "density", "label": "density", "x": "angle_deg", "y": "ks_per_m"}],
        ),
        session=box,
    )
    assert result["status"] == "terminal_error"
    codes = [item["error_code"] for item in result["data"]["checks"]]
    assert codes == ["plan_quality", "chart_axis_mismatch"]
    assert result["data"]["error_code"] == "plan_quality"
    assert "limitations (limitations)" in result["data"]["problems"]
    assert any("angle_deg" in str(item) for item in result["data"]["problems"])
    assert "Also failing" in result["summary"]


def test_a_missing_baseline_is_filled_from_the_runs_and_shown_at_review():
    box = _session()
    result = tools.call("research_plan", _plan(baseline_run_id=""), session=box)
    assert result["status"] == "needs_input", result["summary"]
    plan = box["research"]["plan"]
    assert plan["baseline_run_id"] == "density"
    assert any(item["field"] == "baseline_run_id" for item in plan["automatic_repairs"])


def test_target_fields_the_session_already_holds_are_filled_not_refused():
    box = _session()
    fields = _reproduction_plan_fields()
    target = fields["reproduction_targets"][0]
    for name in ("source_type", "source_id", "target_quantity", "expected_comparison",
                 "reference_models", "requested_outputs"):
        target.pop(name)
    result = tools.call(
        "research_plan", _plan(reproduction_targets=[target]), session=box,
    )
    assert result["status"] == "needs_input", result["summary"]
    filled = box["research"]["plan"]["reproduction_targets"][0]
    assert filled["reference_models"] == ["smrt"]
    assert filled["requested_outputs"] == ["ks_per_m"]
    assert filled["source_id"] == "smrt-v1#fig03"
    assert filled["target_quantity"] == "ks_per_m"
    assert "smrt-v1#fig03" in filled["expected_comparison"]
    repaired = {item["field"] for item in box["research"]["plan"]["automatic_repairs"]}
    assert "reproduction_targets[0].source_id" in repaired


def test_an_unopened_evidence_reference_lists_the_opened_ones():
    box = _session()
    fields = _reproduction_plan_fields()
    fields["literature_evidence"].append({"evidence_ref": "smrt-v1#99", "purpose": "invented"})
    result = tools.call(
        "research_plan", _plan(literature_evidence=fields["literature_evidence"]), session=box,
    )
    assert result["status"] == "terminal_error"
    problem = next(
        item for item in result["data"]["problems"]
        if isinstance(item, dict) and item.get("source") == "smrt-v1#99"
    )
    assert "smrt-v1#08" in problem["allowed_values"]


def test_a_draft_repair_patches_runs_by_id_and_keeps_the_rest():
    box = _session()
    second = {
        "id": "angle", "label": "angle check", "model": "smrt",
        "parameters": {
            "output": "coefficients", "sweep_parameter": "density_kg_m3",
            "sweep_start": 10, "sweep_stop": 10, "sweep_points": 12,
        },
    }
    plan = _plan()
    plan["runs"] = plan["runs"] + [second]
    refused = tools.call("research_plan", plan, session=box)
    assert refused["status"] == "terminal_error"
    revised = tools.call(
        "research_plan",
        {"action": "revise_plan", "changes": {"runs": [
            {"id": "angle", "parameters": {"sweep_stop": 100}},
        ]}},
        session=box,
    )
    assert revised["status"] == "needs_input", revised["summary"]
    runs = {run["id"]: run for run in box["research"]["plan"]["runs"]}
    assert set(runs) == {"density", "angle"}
    assert runs["angle"]["parameters"]["sweep_stop"] == 100
    assert runs["angle"]["parameters"]["sweep_start"] == 10


def test_a_draft_repair_can_remove_one_item():
    from physearth.research import merge_items as _merge_items

    retained = [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}]
    merged = _merge_items(copy.deepcopy(retained), [{"id": "b", "remove": True}], ("id",))
    assert merged == [{"id": "a", "label": "A"}]
    replaced = _merge_items(copy.deepcopy(retained), [{"label": "no id"}], ("id",))
    assert replaced == [{"label": "no id"}]


def test_a_list_of_complete_items_replaces_and_drops_what_it_leaves_out():
    from physearth.research import ITEM_COMPLETE, ITEM_IDENTITY
    from physearth.research import merge_items as _merge_items

    retained = [
        {"model": "smrt", "model_input": "density_kg_m3", "provenance_class": "paper_explicit"},
        {
            "model": "smrt", "model_input": "registered defaults",
            "provenance_class": "backend_default",
        },
    ]
    corrected = [retained[0]]
    keys, complete = ITEM_IDENTITY["parameter_mapping"], ITEM_COMPLETE["parameter_mapping"]
    assert _merge_items(copy.deepcopy(retained), corrected, keys, complete) == corrected
    patch = [{"model": "smrt", "model_input": "density_kg_m3", "paper_value": 300}]
    merged = _merge_items(copy.deepcopy(retained), patch, keys, complete)
    assert len(merged) == 2 and merged[0]["paper_value"] == 300


def test_a_renamed_target_still_finds_its_capability_check():
    reports = [{"id": "fig04.png", "label": "Figure 4", "target_key": "figure:4"}]
    planned = [{"id": "reproduce_fourth", "evidence_refs": ["smrt-v1#fig04"]}]
    assert capability.match_capability_targets(planned, reports) == {0: reports[0]}
    assert capability.match_capability_targets(
        [{"id": "anything"}], reports
    ) == {0: reports[0]}
    assert capability.match_capability_targets(
        [{"id": "anything"}, {"id": "else"}], reports + [{"id": "fig05.png"}]
    ) == {}


def test_a_reviewed_plan_is_patched_by_id_and_keeps_its_defaults():
    from physearth import research

    box = _session()
    plan = _plan()
    plan["runs"] = plan["runs"] + [{
        "id": "angle", "label": "angle check", "model": "smrt",
        "parameters": {
            "output": "coefficients", "sweep_parameter": "density_kg_m3",
            "sweep_start": 10, "sweep_stop": 100, "sweep_points": 12,
        },
    }]
    assert tools.call("research_plan", plan, session=box)["status"] == "needs_input"
    defaulted = box["research"]["plan"]["runs"][1]["defaulted_parameters"]
    result = research.revise(box, {"runs": [{"id": "angle", "parameters": {"sweep_stop": 80}}]})
    assert result["status"] == "needs_input", result["summary"]
    runs = {run["id"]: run for run in box["research"]["plan"]["runs"]}
    assert set(runs) == {"density", "angle"}
    assert runs["angle"]["parameters"]["sweep_stop"] == 80
    assert runs["angle"]["defaulted_parameters"] == defaulted


def test_a_revision_sent_as_top_level_fields_is_applied():
    box = _session()
    refused = tools.call("research_plan", _plan(metrics=[]), session=box)
    assert refused["status"] == "terminal_error"
    revised = tools.call(
        "research_plan", {"action": "revise_plan", "metrics": ["trend agreement"]}, session=box,
    )
    assert revised["status"] == "needs_input", revised["summary"]
    assert box["research"]["plan"]["metrics"] == ["trend agreement"]


def test_a_run_patch_drops_the_undeclared_parameter_that_refused_it():
    box = _session()
    plan = _plan()
    plan["runs"][0]["parameters"]["paper_condition_set"] = "figure 3"
    refused = tools.call("research_plan", plan, session=box)
    assert refused["status"] == "terminal_error"
    revised = tools.call(
        "research_plan",
        {"action": "revise_plan", "changes": {"runs": [
            {"id": "density", "parameters": {"sweep_points": 12}},
        ]}},
        session=box,
    )
    assert revised["status"] == "needs_input", revised["summary"]
    parameters = box["research"]["plan"]["runs"][0]["requested_parameters"]
    assert "paper_condition_set" not in parameters
    assert parameters["sweep_stop"] == 100
