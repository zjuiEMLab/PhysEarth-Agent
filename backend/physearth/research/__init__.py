"""Planning, revising, approving and reporting a piece of research.

Split by stage. Everything the tree imported from the single-module `research` is
re-exported here, including the private names the tests and the interface reach for,
so this split changes no import elsewhere.
"""

# ruff: noqa: F401

# The single-module `research` carried these as attributes of itself, and callers reach
# for them that way (research.registry). Keep the address.
from physearth import audit, knowledge, plotting, validation
from physearth.models import registry
from physearth.research.approval import (
    _clear_previews,
    _preview_bounds,
    _preview_bounds_or_none,
    approve_execution,
    approve_plan,
    choose_chart,
    complete,
    confirm_charts,
    pseudo_preview,
)
from physearth.research.capability import (
    _capability_strings,
    capability_check,
)
from physearth.research.charts import (
    _capability_gaps,
    _chart_y_names,
    _figure_has_series,
    _figure_satisfies,
    _normal_name,
    _output_dependency_problems,
    _question_coverage_problems,
    _repair_chart_axes,
    _repair_required_companion_outputs,
    _repair_sampling_density,
    _run_can_output,
    _run_produces_chart,
    _validate_chart_runs,
)
from physearth.research.common import (
    PARAMETER_CONFIDENCE,
    PARAMETER_PROVENANCE,
    PHASES,
    _clean_list,
    _fail,
    _needs,
    _ok,
    _provenance_confidence,
    _public,
    _require,
    protocol_document,
    protocol_yaml,
    status,
)
from physearth.research.coverage import (
    _target_coverage,
)
from physearth.research.evidence import (
    _evidence_plan_problems,
    _evidence_problem_summary,
)
from physearth.research.execution import (
    execution_gaps,
    planned_chart_ids,
    planned_chart_series,
    planned_run,
    planned_run_ids,
    planned_run_problem,
    target_ids_for_chart,
    target_ids_for_run,
)
from physearth.research.mapping import (
    _expected_mapping_inputs,
    _is_paper_context_problem,
    _ledger_entries,
    _mapping_candidates,
    _mark_user_revised_inputs,
    _model_parameter_spec,
    _normalise_parameter_name,
    _normalise_units,
    _parameter_resolution_by_run,
    _registered_parameter_index,
    _repair_item,
    _repair_parameter_mappings,
    _same_value,
    _units_compatible,
)
from physearth.research.metadata import (
    _repair_reproduction_metadata,
)
from physearth.research.normalise import (
    _clean_charts,
    _clean_literature_evidence,
    _clean_outputs,
    _clean_parameter_mapping,
    _clean_records,
    _clean_reproduction_targets,
    _clean_runs,
    _clean_selected_models,
    _enrich_selected_models,
    _normalise_evidence_ref,
    _read_evidence_refs,
    _repair_missing_protocol_steps,
    _repair_sweep_bounds,
    _run_validation_details,
    is_reproduction_question,
)
from physearth.research.propose import (
    propose,
)
from physearth.research.report import (
    report_problem,
    report_warnings,
    safe_report,
)
from physearth.research.review import (
    allow_model,
    review_action,
)
from physearth.research.revise import (
    _REVISION_FIELDS,
    _REVISION_SENTINEL,
    _revision_diff,
    _revision_value,
    _revision_value_text,
    revise,
    revise_after_figure_quality,
    revise_after_run_failures,
    revision_summary_text,
)
