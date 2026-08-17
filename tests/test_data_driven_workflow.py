from pathlib import Path

from physearth.corpus import live

from frontend.views import evaluation as evals
from physearth import harness, prompt, research, session, tools
from physearth.ingest import jats

FIXTURE = Path(__file__).parent / "fixtures" / "jats_sample.xml"


def _valid_plan(box, question="How does density affect the registered model output?"):
    return tools.call(
        "research_plan",
        {
            "action": "propose",
            "question": question,
            "objective": "Quantify the density response.",
            "hypothesis": "The response changes across the density range.",
            "steps": ["read resources", "run the sweep", "review the figure"],
            "runs": [{
                "id": "density",
                "label": "Density response",
                "model": "smrt",
                "parameters": {
                    "output": "coefficients",
                    "sweep_parameter": "density_kg_m3",
                    "sweep_start": 10,
                    "sweep_stop": 100,
                    "sweep_points": 12,
                },
            }],
            "charts": [{
                "id": "density", "label": "Density", "x": "density_kg_m3", "y": "ks_per_m"
            }],
            "quantities": ["ks_per_m"],
            "controls": ["frequency fixed"],
            "metrics": ["trend"],
            "diagnostics": ["finite outputs"],
            "success_criteria": ["finite outputs"],
            "stop_conditions": ["quality-control failure"],
            "assumptions": ["homogeneous layer"],
            "limitations": ["single model"],
            "baseline_run_id": "density",
        },
        session=box,
    )


def test_prompt_is_general_and_does_not_embed_smrt_protocols():
    text = prompt.build(session.new_state(session.new_session("m")))
    assert "Earth-science physical-modeling agent" in text
    assert "axes, units, legends, panels, annotations" in text
    assert "separately identified reference-data artifact" in text
    assert "visual-similarity claim" in text
    assert "Q1 sparse-medium requires exactly six" not in text
    assert "radius_m=0.0001" not in text
    assert "smrt-v1#08" not in text


def test_reproduction_detection_is_generic_and_case_validator_is_removed():
    assert not (Path(__file__).parents[1] / "physearth" / "reproduction.py").exists()
    assert research.is_reproduction_question(
        "Can the paper reproduce the published soil-model figure?"
    )
    assert not research.is_reproduction_question("What is the model output?")


def test_paper_figure_inspection_records_visual_provenance_without_digitization():
    box = session.new_session("m")
    box["corpus"]["uploaded-paper"] = {
        "slug": "uploaded-paper",
        "kind": "paper",
        "title": "Uploaded paper",
        "figures": [{
            "id": "fig-1",
            "caption": "Figure 1. Scattering coefficient versus density.",
            "page": 3,
            "asset_bytes": b"not-a-real-image",
            "asset_format": "png",
        }],
    }
    result = tools.call(
        "inspect_paper_figure",
        {"paper": "uploaded-paper", "figure_id": "fig-1", "focus": "axes and trends"},
        session=box,
    )
    assert result["status"] == "success"
    assert result["data"]["numeric_digitization"] == "not performed"
    assert result["data"]["visual_observations"]["caption_context"].startswith("Figure 1")
    assert "uploaded-paper#fig-1" in box["paper_figures_inspected"]
    assert any(item["kind"] == "figure_inspection" for item in box["evidence_ledger"])


def test_compact_multi_figure_plans_bind_each_target_to_its_source_figure():
    from physearth.research.evidence import _is_figure_target
    from physearth.research.metadata import _figure_ref_for_target

    refs = ["smrt-v1#fig04", "smrt-v1#fig05"]
    assert _figure_ref_for_target({"source_id": "fig04.png"}, refs) == refs[0]
    assert _figure_ref_for_target({"source_id": "Figure 5"}, refs) == refs[1]
    assert _is_figure_target({"source_id": "fig04"}, {refs[0]}, refs) is True


def test_figure_target_cannot_pass_without_source_figure_inspection():
    from physearth.research.evidence import _evidence_plan_problems

    box = session.new_session("m")
    box["sections_read"].add("smrt-v1#08")
    box["paper_figures_read"].add("smrt-v1#fig03")
    problems = _evidence_plan_problems(
        box,
        "Can the paper's Figure 3 coefficient result be reproduced?",
        [{"evidence_ref": "smrt-v1#08", "purpose": "method"}],
        [{
            "source_type": "figure", "source_id": "fig03", "evidence_refs": ["smrt-v1#fig03"],
            "status": "planned",
        }],
        [], [], [], [], [], [],
    )

    assert any(item["field"] == "reproduction_targets[0].figure_inspection" for item in problems)


def test_missing_paper_figure_inspection_is_explicitly_unavailable():
    box = session.new_session("m")
    box["corpus"]["paper"] = {"slug": "paper", "kind": "paper", "figures": []}
    result = tools.call(
        "inspect_paper_figure", {"paper": "paper", "figure_id": "fig-3"}, session=box
    )
    assert result["status"] == "terminal_error"
    assert any(
        item["kind"] == "figure_inspection" and item["analysis_status"] == "unavailable"
        for item in box["evidence_ledger"]
    )


def test_research_plan_requires_guideline_and_model_instruction():
    box = session.new_session("m")
    blocked = _valid_plan(box)
    assert blocked["status"] == "needs_input"
    assert blocked["data"]["error_code"] == "research_guideline_read_required"

    assert tools.call("read_research_guideline", {}, session=box)["status"] == "success"
    blocked = _valid_plan(box)
    assert blocked["data"]["error_code"] == "model_instruction_read_required"

    assert tools.call("list_models", {"model": "smrt"}, session=box)["status"] == "success"
    assert tools.call("read_model_instruction", {"model": "smrt"}, session=box)["status"] == "success"
    accepted = _valid_plan(box)
    assert accepted["status"] == "needs_input"
    assert box["research"]["phase"] == "plan_review"


def _reproduction_resources(box):
    box["sections_read"].add("smrt-v1#08")
    box["paper_figures_read"].add("smrt-v1#fig03")
    tools.call("read_research_guideline", {}, session=box)
    tools.call("list_models", {"model": "smrt"}, session=box)
    tools.call("read_model_instruction", {"model": "smrt"}, session=box)
    capability = tools.call(
        "research_capability_check",
        {
            "action": "check",
            "reference_models": ["smrt"],
            "requested_outputs": ["ks_per_m"],
            "local_models": ["smrt"],
        },
        session=box,
    )
    if capability["status"] == "needs_input":
        tools.call("research_capability_check", {"action": "confirm_partial"}, session=box)


def _reproduction_plan_fields():
    return {
        "literature_evidence": [
            {"evidence_ref": "smrt-v1#08", "purpose": "methods and source result"},
            {"evidence_ref": "smrt-v1#fig03", "purpose": "source figure target"},
        ],
        "reproduction_targets": [{
            "id": "fig03-result",
            "source_type": "figure",
            "source_id": "fig03",
            "target_quantity": "ks_per_m",
            "evidence_refs": ["smrt-v1#08", "smrt-v1#fig03"],
            "expected_comparison": "compare the coefficient trend with Figure 3",
            "reference_models": ["smrt"],
            "requested_outputs": ["ks_per_m"],
            "run_ids": ["density"],
            "chart_ids": ["density"],
        }],
        "selected_models": [{
            "model": "smrt",
            "purpose": "reproduce the paper coefficient calculation",
            "capability_status": "runnable",
            "instruction_ref": "guideline:smrt@1.0",
        }],
        "parameter_mapping": [
            {"paper_concept": key, "paper_value": value, "model_input": key,
             "mapped_value": value, "units": "declared", "provenance_class": "paper_inferred",
             "evidence_ref": "smrt-v1#08", "rationale": "mapped from the opened paper evidence"}
            for key, value in {
                "electromagnetic_model": "iba", "microstructure_model": "exponential",
                "output": "coefficients", "frequency_ghz": 37.0, "angle_deg": 55.0,
                "thickness_m": 1.0, "density_kg_m3": 300.0, "temperature_k": 265.0,
                "corr_length_m": 0.00015, "radius_m": 0.0002, "stickiness": 0.2,
                "dort_streams": 32, "sweep_parameter": "density_kg_m3",
                "sweep_start": 10, "sweep_stop": 100, "sweep_points": 12,
            }.items()
        ],
        "outputs": ["ks_per_m"],
    }


def test_reproduction_plan_requires_explicit_targets_and_parameter_mapping():
    box = session.new_session("m")
    _reproduction_resources(box)
    base = _valid_plan(box, "Can the paper's Figure 3 coefficient result be reproduced?")
    # The ordinary plan is valid, but a paper reproduction must name the evidence target
    # and map its paper concepts to exact registered inputs.
    assert base["status"] == "terminal_error"
    assert base["data"]["error_code"] == "reproduction_evidence_incomplete"
    assert any(item["field"] == "reproduction_targets" for item in base["data"]["problems"])


def test_reproduction_plan_links_target_to_runs_and_charts_and_revalidates_revisions():
    box = session.new_session("m")
    _reproduction_resources(box)
    fields = _reproduction_plan_fields()
    tools.call(
        "inspect_paper_figure",
        {"paper": "smrt-v1", "figure_id": "fig03", "focus": "title, axes, and legend"},
        session=box,
    )
    result = tools.call(
        "research_plan",
        {
            **fields,
            "action": "propose",
            "question": "Can the paper's Figure 3 coefficient result be reproduced?",
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
        },
        session=box,
    )
    assert result["status"] == "needs_input", result["summary"]
    plan = box["research"]["plan"]
    assert plan["reproduction_targets"][0]["chart_ids"] == ["density"]
    assert plan["runs"][0]["target_ids"] == ["fig03-result"]
    assert plan["charts"][0]["target_ids"] == ["fig03-result"]
    version = box["research"]["plan_version"]
    revised = tools.call(
        "research_plan",
        {"action": "revise_plan", "changes": {"parameter_mapping": []}},
        session=box,
    )
    assert revised["status"] == "terminal_error"
    assert revised["data"]["error_code"] == "reproduction_evidence_incomplete"
    assert box["research"]["plan_version"] == version


def test_research_plan_generates_a_reviewable_protocol_yaml_and_revision():
    box = session.new_session("m")
    tools.call("read_research_guideline", {}, session=box)
    tools.call("list_models", {"model": "smrt"}, session=box)
    tools.call("read_model_instruction", {"model": "smrt"}, session=box)

    accepted = _valid_plan(box)
    assert accepted["status"] == "needs_input"
    assert accepted["data"]["protocol"]["format"] == "phys-earth/research-protocol"
    assert "runs:" in accepted["data"]["protocol_yaml"]
    assert "protocols.yaml" not in accepted["data"]["protocol_yaml"]

    revised = tools.call(
        "research_plan",
        {
            "action": "revise_plan",
            "changes": {
                "paper_conditions": {"frequency_ghz": 37.0, "radius_m": 0.0001},
                "condition_provenance": {
                    "frequency_ghz": "paper:smrt-v1#08",
                    "radius_m": "paper:smrt-v1#08",
                },
            },
        },
        session=box,
    )
    assert revised["status"] == "needs_input"
    assert box["research"]["plan_version"] == 2
    assert "frequency_ghz: 37.0" in revised["data"]["protocol_yaml"]
    assert box["research"]["phase"] == "plan_review"


def test_plan_revision_returns_field_diff_and_invalidated_review_state():
    box = session.new_session("m")
    tools.call("read_research_guideline", {}, session=box)
    tools.call("list_models", {"model": "smrt"}, session=box)
    tools.call("read_model_instruction", {"model": "smrt"}, session=box)
    accepted = _valid_plan(box)
    assert accepted["status"] == "needs_input"

    revised = tools.call(
        "research_plan",
        {"action": "revise_plan", "changes": {"assumptions": ["updated assumption"]}},
        session=box,
    )

    assert revised["status"] == "needs_input"
    summary = revised["data"]["revision_summary"]
    assert (summary["from_version"], summary["to_version"]) == (1, 2)
    assert any(item["field"] == "assumptions" for item in summary["changed"])
    assert summary["invalidated"] == ["pseudo_preview", "chart_selection", "execution_approval"]
    assert summary["next_phase"] == "plan_review"
    assert box["research"]["plan"]["revision_summary"] == summary
    assert "Plan revised from v001 to v002" in revised["summary"]


def _q1_resources(box):
    tools.call("read_research_guideline", {}, session=box)
    tools.call("read_literature", {"slug": "smrt-v1", "section_id": "08"}, session=box)
    tools.call("list_models", {"model": "smrt"}, session=box)
    tools.call("read_model_instruction", {"model": "smrt"}, session=box)
    capability = tools.call(
        "research_capability_check",
        {
            "action": "check",
            "reference_models": ["smrt"],
            "requested_outputs": ["ks_per_m"],
            "local_models": ["smrt"],
        },
        session=box,
    )
    if capability["status"] == "needs_input":
        tools.call("research_capability_check", {"action": "confirm_partial"}, session=box)


def _q1_runs(radius=0.0001):
    combinations = [
        ("independent_rayleigh", "independent_sphere", "rayleigh"),
        ("independent_iba", "independent_sphere", "iba"),
        ("nonsticky_qca_cp", "non_sticky_hard_spheres", "dmrt_qcacp_shortrange"),
        ("nonsticky_iba", "non_sticky_hard_spheres", "iba"),
        ("sticky_qca_cp", "sticky_hard_spheres", "dmrt_qcacp_shortrange"),
        ("sticky_iba", "sticky_hard_spheres", "iba"),
    ]
    return [
        {
            "id": run_id,
            "label": run_id,
            "model": "smrt",
            "parameters": {
                "electromagnetic_model": theory,
                "microstructure_model": microstructure,
                "output": "coefficients",
                "frequency_ghz": 37.0,
                "radius_m": radius,
                "sweep_parameter": "density_kg_m3",
                "sweep_start": 10.0,
                "sweep_stop": 50.0,
                "sweep_points": 9,
            },
        }
        for run_id, microstructure, theory in combinations
    ]


def _q1_plan_fields(runs):
    return {
        "action": "propose",
        "question": (
            "Under what snow-density range do independent spheres, non-sticky hard spheres "
            "and sticky hard spheres with Rayleigh, DMRT QCA-CP, and IBA converge to the same "
            "first-order scattering behavior, and where do they diverge?"
        ),
        "objective": "Reproduce Q1 sparse-medium scattering behavior",
        "hypothesis": "The six configurations converge at sparse density and diverge as correlations grow.",
        "steps": ["read the paper result", "run the six configurations", "review the comparison"],
        "charts": [{"id": "q1_scattering", "x": "density_kg_m3", "y": "ks_per_m"}],
        "quantities": ["ks_per_m"],
        "controls": ["frequency and radius held fixed"],
        "metrics": ["convergence and divergence of the trend"],
        "diagnostics": ["finite coefficient outputs"],
        "success_criteria": ["the sparse-medium trend is comparable"],
        "stop_conditions": ["invalid model output"],
        "assumptions": ["homogeneous snow layer"],
        "limitations": ["bundled source Figure 3 asset is unavailable"],
        "baseline_run_id": "independent_rayleigh",
        "paper_conditions": {"radius_m": 0.0001},
        "condition_provenance": {"radius_m": "smrt-v1#08"},
        "reproduction_targets": [{
            "id": "scattering-result",
            "source_type": "result",
            "source_id": "paper-result",
            "target_quantity": "ks_per_m",
            "evidence_refs": ["smrt-v1#08"],
            "expected_comparison": "Compare the planned model curves with the opened paper result.",
            "reference_models": ["smrt"],
            "requested_outputs": ["ks_per_m"],
        }],
        "runs": runs,
    }


def test_q1_metadata_repair_uses_opened_evidence_and_keeps_six_runs():
    box = session.new_session("m")
    _q1_resources(box)
    result = tools.call("research_plan", _q1_plan_fields(_q1_runs()), session=box)

    assert result["status"] == "needs_input", result
    plan = box["research"]["plan"]
    assert [run["id"] for run in plan["runs"]] == [run["id"] for run in _q1_runs()]
    assert plan["reproduction_targets"][0]["source_type"] == "result"
    assert plan["reproduction_targets"][0]["source_id"] == "paper-result"
    assert plan["reproduction_targets"][0]["status"] == "planned"
    assert plan["reproduction_targets"][0]["evidence_refs"] == ["smrt-v1#08"]
    assert any(
        item["provenance_class"] == "backend_default"
        for item in plan["parameter_mapping"]
    )
    assert not any(
        item["field"] == "reproduction_targets"
        for item in plan["automatic_repairs"]
    )
    assert all(
        run["parameters"]["radius_m"] == 0.0001
        for run in plan["runs"]
    )


def test_q1_mapping_aliases_and_missing_metadata_are_repaired_from_registry():
    box = session.new_session("m")
    _q1_resources(box)
    fields = _q1_plan_fields(_q1_runs())
    fields["parameter_mapping"] = [
        {
            "paper_concept": "snow density",
            "model_input": "density",
            "mapped_value": 300.0,
        },
        {
            "paper_concept": "particle radius",
            "model_input": "radius",
            "mapped_value": 0.0001,
            "provenance_class": "paper_explicit",
            "evidence_ref": "smrt-v1#08",
        },
    ]

    result = tools.call("research_plan", fields, session=box)

    assert result["status"] == "needs_input", result
    plan = box["research"]["plan"]
    density = next(item for item in plan["parameter_mapping"] if item.get("model_input") == "density_kg_m3")
    radius = next(item for item in plan["parameter_mapping"] if item.get("model_input") == "radius_m")
    assert density["model"] == "smrt"
    assert density["provenance_class"] == "backend_default"
    assert density["confidence"] == "medium"
    assert density["paper_concept"] == "snow density"
    assert density["rationale"]
    assert radius["model"] == "smrt"
    assert radius["units"] == "m"
    assert radius["confidence"] == "high"
    assert any(
        item["field"].endswith(".model_input")
        and item["from"] in {"density", "radius"}
        for item in plan["automatic_repairs"]
    )
    assert len(plan["runs"]) == 6


def test_unknown_mapping_alias_returns_registered_candidates_and_keeps_plan_uncreated():
    box = session.new_session("m")
    _q1_resources(box)
    fields = _q1_plan_fields(_q1_runs())
    fields["parameter_mapping"] = [{
        "paper_concept": "snow density",
        "model_input": "snow_density",
        "mapped_value": 300.0,
        "provenance_class": "model_assumption",
        "rationale": "unverified mapping",
    }]

    result = tools.call("research_plan", fields, session=box)

    assert result["status"] == "terminal_error"
    assert result["data"]["error_code"] == "reproduction_evidence_incomplete"
    problem = next(
        item for item in result["data"]["problems"]
        if item.get("field") == "parameter_mapping[0].model_input"
    )
    assert problem["source"] == "registered_model_declaration"
    assert problem["actual"] == "snow_density"
    assert "density_kg_m3" in problem["allowed_values"]
    assert problem["blocking"] is True
    assert "parameter_mapping[0].model_input" in result["summary"]
    assert not (box.get("research") or {}).get("plan", {}).get("approval_state") == "plan_review"


def test_paper_conditions_only_tag_parameters_and_never_block_registered_runs():
    box = session.new_session("m")
    _q1_resources(box)
    fields = _q1_plan_fields(_q1_runs())
    fields["paper_conditions"] = {
        "stickiness": 0.5,
        "radius_m": 0.0001,
    }
    fields["condition_provenance"] = {
        "stickiness": "smrt-v1#08",
        "radius_m": "smrt-v1#08",
    }

    result = tools.call("research_plan", fields, session=box)

    assert result["status"] == "needs_input", result
    assert "paper_condition_conflict" not in result["summary"]
    plan = box["research"]["plan"]
    stickiness = next(
        item for item in plan["parameter_mapping"]
        if item.get("model_input") == "stickiness"
    )
    assert stickiness["paper_value"] == 0.5
    assert stickiness["provenance_class"] == "backend_default"
    assert stickiness["confidence"] == "medium"
    assert all(
        warning.get("blocking") is False
        for warning in plan.get("validation_warnings") or []
        if warning.get("code") == "paper_context_difference"
    )


def test_q1_paper_radius_difference_is_a_nonblocking_context_warning():
    box = session.new_session("m")
    _q1_resources(box)
    result = tools.call("research_plan", _q1_plan_fields(_q1_runs(radius=0.0002)), session=box)

    assert result["status"] == "needs_input", result
    warnings = box["research"]["plan"]["validation_warnings"]
    warning = next(item for item in warnings if item["field"].endswith("parameters.radius_m"))
    assert warning["expected"] == 0.0001
    assert warning["actual"] == 0.0002
    assert warning["code"] == "paper_context_difference"
    assert warning["blocking"] is False
    mapping = next(
        item for item in box["research"]["plan"]["parameter_mapping"]
        if item.get("model_input") == "radius_m"
    )
    assert mapping["provenance_class"] == "user_specified"


def test_reproduction_revision_accepts_user_range_inside_registered_model_bounds():
    box = session.new_session("m")
    _q1_resources(box)
    proposed = tools.call("research_plan", _q1_plan_fields(_q1_runs()), session=box)
    assert proposed["status"] == "needs_input", proposed

    expanded = _q1_runs()
    for run in expanded:
        run["parameters"]["sweep_start"] = 1.0
        run["parameters"]["sweep_stop"] = 300.0
    revised = tools.call(
        "research_plan",
        {"action": "revise_plan", "changes": {"runs": expanded}},
        session=box,
    )

    assert revised["status"] == "needs_input", revised
    assert box["research"]["plan_version"] == 2
    assert all(
        run["parameters"]["sweep_start"] == 1.0
        and run["parameters"]["sweep_stop"] == 300.0
        for run in box["research"]["plan"]["runs"]
    )
    assert all(
        item["provenance_class"] == "user_specified"
        for item in box["research"]["plan"]["parameter_mapping"]
        if item.get("model_input") in {"sweep_start", "sweep_stop"}
    )


def test_bundled_smrt_figures_are_readable_and_not_digitized_automatically():
    box = session.new_session("m")
    _q1_resources(box)
    read = tools.call(
        "read_paper_figure",
        {"paper": "smrt-v1", "figure_id": "fig03"},
        session=box,
    )
    assert read["status"] == "success", read
    figure = read["data"]["figure"]
    assert figure["asset_path"] == "figures/fig03.png"
    assert figure["original_asset_path"] == "figures/fig03.pdf"
    assert figure["source_uri"].endswith("gmd-11-2763-2018-f03.pdf")

    inspected = tools.call(
        "inspect_paper_figure",
        {"paper": "smrt-v1", "figure_id": "fig03", "focus": "axes, legend, and trends"},
        session=box,
    )
    assert inspected["status"] == "success", inspected
    assert inspected["data"]["title"] == "Sparse-medium scattering coefficient comparison"
    assert inspected["data"]["visual_observations"]["title"] == inspected["data"]["title"]
    assert inspected["data"]["asset_available"] is True
    assert inspected["data"]["numeric_digitization"] == "not performed"
    assert inspected["data"]["analysis_status"] in {"vision_payload_ready", "text_extracted"}
    assert any("Density" in axis for axis in inspected["data"]["visual_observations"]["axes"])
    assert any("Scattering coefficient" in axis for axis in inspected["data"]["visual_observations"]["axes"])
    assert len(inspected["data"]["visual_observations"]["legend"]) >= 6
    assert inspected["data"].get("image_data_url", "").startswith("data:image/")
    assert inspected["data"]["visual_observations"]["dimensions_px"]["width"] > 0
    assert inspected["data"]["visual_observations"]["dimensions_px"]["height"] > 0
    assert "smrt-v1#fig03" in box["paper_figures_read"]
    assert "smrt-v1#fig03" in box["paper_figures_inspected"]


def test_paper_figure_ids_are_normalized_without_changing_the_source_identifier():
    box = session.new_session("m")
    read = tools.call(
        "read_paper_figure",
        {"paper": "smrt-v1", "figure_id": "fig-fig03.png"},
        session=box,
    )
    assert read["status"] == "success", read
    assert read["data"]["figure"]["id"] == "fig03"
    assert read["data"]["citation_key"] == "smrt-v1#fig-fig03"

    inspected = tools.call(
        "inspect_paper_figure",
        {"paper": "smrt-v1", "figure_id": "figure 3"},
        session=box,
    )
    assert inspected["status"] == "success", inspected
    assert inspected["data"]["figure_id"] == "fig03"
    assert inspected["data"]["asset_available"] is True


def test_bundled_smrt_card_declares_all_publisher_figures_with_assets():
    from physearth.corpus import knowledge

    card = knowledge.card("smrt-v1")
    assert [figure["id"] for figure in card["figures"]] == [
        "fig01", "fig02", "fig03", "fig04", "fig05", "fig06", "fig07", "fig08"
    ]
    for figure in card["figures"]:
        asset = card["_dir"] / figure["asset_path"]
        original = card["_dir"] / figure["original_asset_path"]
        assert asset.is_file(), asset
        assert original.is_file(), original
        assert figure["license"] == "CC-BY-4.0"


def test_research_workflow_does_not_offer_or_require_a_stored_paper_protocol():
    names = {item["function"]["name"] for item in tools.specs()}
    assert "read_paper_protocol" not in names
    assert "read_paper_protocol" not in prompt.build(
        session.new_state(session.new_session("m"))
    )


def test_smrt_protocol_is_data_and_contains_the_six_q1_runs():
    demo = evals.guided_demo()
    assert demo["fixed"]["radius_m"] == 0.0001
    task = evals.canonical_task("q1-sparse-medium")
    assert "six" in task["question"]
    assert len(demo["required_runs"]) == 6
    assert ["iba", "non_sticky_hard_spheres"] in demo["required_runs"]
    assert ["iba", "sticky_hard_spheres"] in demo["required_runs"]
    assert demo["task_id"] == "q1-sparse-medium"


def test_capability_checkpoint_rules_are_generic_and_not_in_global_prompt():
    assert "research_capability_check" in prompt.RESEARCH_WORKFLOW
    assert "DMRT" not in prompt.RESEARCH_WORKFLOW
    assert "SMRT" not in prompt.RESEARCH_WORKFLOW
    assert "Q1" not in prompt.RESEARCH_WORKFLOW
    assert "Q2" not in prompt.RESEARCH_WORKFLOW


def test_jats_assets_are_persisted_separately_from_section_text(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    box = session.new_session("m")
    parsed = jats.parse(FIXTURE.read_text(encoding="utf-8"))
    card = live.add(box, {
        "doi": "10.5194/test-assets-1-2026",
        "front": parsed["front"],
        "sections": parsed["sections"],
        "figures": parsed["figures"],
        "tables": parsed["tables"],
        "source": "fixture",
        "url": "https://tc.copernicus.org/articles/test.xml",
    })
    assert card["figures"][0]["source_uri"] == "fig03.png"
    assert card["tables"][0]["id"] == "t1"
    assert Path(card["artifact"]["manifest"]).is_file()
    assert "This caption must not appear" not in "\n".join(
        item["text"] for item in card["sections"]
    )


def test_user_guideline_is_project_scoped_and_readable(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    box = session.new_session("m")
    result = tools.call(
        "register_model_guideline",
        {
            "model": "smrt",
            "content": "Hold frequency fixed unless it is the independent variable.",
            "version": "2.0",
        },
        session=box,
    )
    assert result["status"] == "success"
    read = tools.call("read_model_instruction", {"model": "smrt"}, session=box)
    assert read["status"] == "success"
    assert read["data"]["version"] == "user"
    assert "Hold frequency fixed" in read["data"]["text"]


def test_guideline_and_paper_figure_markers_are_checked_by_the_harness():
    assert harness.check_citations(
        "I followed the model guidance [guideline:smrt@1.0].",
        set(), guidelines_read={"smrt@1.0"},
    )["passed"]
    assert harness.check_citations(
        "The source image is [figure:smrt-v1#fig03].",
        set(), paper_figures_read={"smrt-v1#fig03"},
    )["passed"]


def test_reading_a_section_says_what_the_paper_figures_are_called():
    """The reproduction gate demands a figure the agent opened; this makes that possible.

    A figure target must carry a reference from read_paper_figure, and that tool takes a
    figure_id. Nothing listed the ids, so the agent could only guess: it read a section,
    proposed, was refused for missing figure evidence, read another section, and gave up
    after five consecutive failures. The requirement was satisfiable only by luck.
    """
    from physearth.tools import literature

    from physearth import session as session_state

    box = session_state.new_session("m")
    result = literature.read_literature("smrt-v1", "03", _session=box)
    figures = result["data"]["figures"]
    assert figures, "reading a section must say which figures the paper declares"
    ids = {figure["figure_id"] for figure in figures}
    assert "fig03" in ids
    assert all(figure["title"] for figure in figures), "an id with no title cannot be chosen"

    # Titles, not captions. A caption carries the figure's scientific content, and
    # listing every one of them put figure 4's reference models -- DMRT-ML, DMRT-QMS --
    # into the answer to a question about figure 3, where they do not belong.
    import json as _json

    payload = _json.dumps(result)
    assert "DMRT-ML" not in payload and "DMRT-QMS" not in payload, (
        "another figure's caption leaked into this section read"
    )

    # and an id learned this way must actually open
    opened = literature.read_paper_figure("smrt-v1", sorted(ids)[2], _session=box)
    assert opened["status"] == "success", opened


def test_a_plan_thinner_than_the_figure_legend_is_flagged_at_review():
    """A figure is reproduced from its axes, labels and legend, not its caption alone.

    The legend says how many curves are on the figure, and the inspection already
    extracts it. A plan with one run against a legend of six is reproducing one line of
    that figure. Advisory, not blocking: a legend entry is not always a run.
    """
    from physearth.research import evidence
    from physearth.tools import literature

    from physearth import session as session_state

    box = session_state.new_session("m")
    literature.read_literature("smrt-v1", "03", _session=box)
    inspected = literature.inspect_paper_figure(
        "smrt-v1", "fig03", focus="axes and legend", _session=box
    )
    reference = inspected["citations"][0]
    legend = (inspected["data"].get("visual_observations") or {}).get("legend") or []
    assert len(legend) > 1, "this figure needs a multi-series legend for the test to mean anything"

    thin = [{"id": "t1", "status": "planned", "evidence_refs": [reference], "run_ids": ["r1"]}]
    warnings = evidence.legend_coverage_warnings(box, thin, [{"id": "r1"}])
    assert len(warnings) == 1, warnings
    assert "legend" in warnings[0] and legend[0] in warnings[0]

    covered = [dict(thin[0], run_ids=["r%d" % n for n in range(len(legend) + 1)])]
    assert evidence.legend_coverage_warnings(box, covered, []) == []

    unavailable = [dict(thin[0], status="unavailable")]
    assert evidence.legend_coverage_warnings(box, unavailable, []) == []
