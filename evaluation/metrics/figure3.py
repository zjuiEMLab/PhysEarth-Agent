"""Version-matched scientific and presentation scoring for the Q1 Figure 3 task."""

import importlib
import importlib.metadata
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_PATH = ROOT / "fixtures" / "q1_figure3_reference.yaml"
STANDARD_PATH = ROOT / "standards" / "q1_figure3.yaml"
ORACLE_PATH = ROOT / "results" / "competition" / "q1_figure3_oracle.json"


def reference():
    return yaml.safe_load(REFERENCE_PATH.read_text(encoding="utf-8"))


def evaluation_standard():
    return yaml.safe_load(STANDARD_PATH.read_text(encoding="utf-8"))


def _ensure_smrt_importable():
    if sys.version_info < (3, 13) or "smrt.core.lib" in sys.modules:
        return
    missing = object()
    previous = sys.modules.get("numba", missing)
    sys.modules["numba"] = None
    try:
        importlib.import_module("smrt.core.lib")
    finally:
        if previous is missing:
            sys.modules.pop("numba", None)
        else:
            sys.modules["numba"] = previous


def build_oracle():
    """Execute the pinned notebook recipe with the installed upstream SMRT package."""
    _ensure_smrt_importable()
    from smrt import make_snow_layer, sensor_list
    from smrt.core.plugin import import_class

    gold = reference()
    recipe = gold["recipe"]
    sensor = sensor_list.amsre("37V")
    curves = {}
    for curve in gold["curves"]:
        values = []
        for density in recipe["densities_kg_m3"]:
            kwargs = {"radius": float(recipe["radius_m"])}
            oracle_stickiness = curve.get("oracle_stickiness", curve.get("stickiness"))
            if oracle_stickiness is not None:
                kwargs["stickiness"] = float(oracle_stickiness)
            layer = make_snow_layer(
                1.0,
                curve.get("oracle_microstructure_model", curve["microstructure_model"]),
                float(density),
                **kwargs,
            )
            model = import_class("emmodel", curve["electromagnetic_model"])(sensor, layer)
            value = getattr(model, "_ks", None)
            if value is None:
                raise RuntimeError(f"{curve['id']} did not expose its scattering coefficient")
            values.append(float(value))
        curves[curve["id"]] = values
    return {
        "schema_version": "q1-figure3-oracle-v1",
        "reference": gold["source"],
        "smrt_version": importlib.metadata.version("smrt"),
        "axis": {
            "name": "density_kg_m3",
            "values": [float(value) for value in recipe["densities_kg_m3"]],
        },
        "series": curves,
    }


def _same_number(left, right, tolerance=1.0e-9):
    return isinstance(left, (int, float)) and math.isclose(
        float(left), float(right), rel_tol=tolerance, abs_tol=tolerance
    )


def _run_identity(item):
    spec = item.get("spec") or {}
    microstructure_parameters = spec.get("microstructure_parameters") or {}
    return {
        "electromagnetic_model": str(spec.get("electromagnetic_model") or "").lower(),
        "microstructure_model": str(spec.get("microstructure_model") or "").lower(),
        "stickiness": spec.get("stickiness", microstructure_parameters.get("stickiness")),
    }


def _curve_matches(item, curve):
    identity = _run_identity(item)
    if identity["electromagnetic_model"] != curve["electromagnetic_model"]:
        return False
    micro = identity["microstructure_model"]
    accepted = {
        curve["microstructure_model"],
        *(curve.get("accepted_microstructure_aliases") or []),
    }
    if micro not in accepted:
        return False
    # Stickiness is retained as a diagnostic.  The paper does not define the pinned
    # notebook's numeric recipe sufficiently to make this value a pass/fail criterion.
    # The electromagnetic/microstructure identity still distinguishes the six curves.
    return True


def _stickiness_matches(item, curve):
    wanted_stickiness = curve.get("stickiness")
    if wanted_stickiness is None:
        return True
    identity = _run_identity(item)
    if identity["microstructure_model"] in set(curve.get("accepted_microstructure_aliases") or []):
        return True
    return _same_number(identity["stickiness"], wanted_stickiness)


def _experiment_matches(item, gold):
    spec = item.get("spec") or {}
    return (
        _same_number(spec.get("frequency_ghz"), gold["recipe"]["frequency_ghz"])
        and _same_number(spec.get("radius_m"), gold["recipe"]["radius_m"])
        and str((item.get("axis") or {}).get("name") or "") == "density_kg_m3"
        and (item.get("units") or {}).get("ks_per_m") == "m-1"
    )


def _normalised_errors(got, wanted):
    if len(got) != len(wanted) or not wanted:
        return None, None
    span = max(wanted) - min(wanted)
    scale = span if span > 0 else max(abs(value) for value in wanted) or 1.0
    errors = [abs(float(a) - float(b)) for a, b in zip(got, wanted, strict=True)]
    rmse = math.sqrt(sum(error * error for error in errors) / len(errors)) / scale
    return rmse, max(errors) / scale


def _plot_score(record, gold):
    figures = [item for item in record.get("figures") or [] if not item.get("preview")]
    candidates = sorted(figures, key=lambda item: len(item.get("series") or []), reverse=True)
    if not candidates:
        return {
            "passed": False,
            "status": "fail",
            "checks": {
                "rendered": False,
                "title": False,
                "caption": False,
                "axes": False,
                "legend": False,
                "quality": False,
            },
            "detail": "no rendered chart",
        }
    figure = candidates[0]
    title = str(figure.get("title") or "").lower()
    caption = str(figure.get("subtitle") or figure.get("caption") or "").lower()
    x_label = str(figure.get("x_label") or "").lower()
    y_label = str(figure.get("y_label") or "").lower()
    labels = [str(item.get("label") or "").lower() for item in figure.get("series") or []]
    expected_labels = [str(item["label"]).lower() for item in gold["curves"]]
    image = Path(str(figure.get("archived_image_path") or figure.get("image_path") or ""))
    quality = figure.get("quality_review") or {}
    checks = {
        "rendered": image.is_file() and image.stat().st_size >= 2000,
        "title": all(term in title for term in gold["plot"]["title_terms"]),
        # Captions/subtitles are useful evidence, but their wording is not a formal
        # correctness gate.  Keep the observation for audit without failing the plot.
        "caption": all(term in caption for term in gold["plot"]["caption_terms"])
        and any(term in caption for term in gold["plot"]["caption_value_terms"]),
        "axes": all(term in x_label for term in gold["plot"]["x_terms"])
        and all(term in y_label for term in gold["plot"]["y_terms"]),
        "legend": len(labels) == 6
        and all(
            any(wanted in label or label in wanted for label in labels)
            for wanted in expected_labels
        ),
        "quality": bool(quality.get("passed")) if quality.get("reviewed") else image.is_file(),
    }
    standard = evaluation_standard().get("figure") or {}
    formal_names = standard.get("formal_checks") or [
        name for name in checks if name != "caption"
    ]
    formal_checks = {name: checks[name] for name in formal_names if name in checks}
    return {
        "passed": all(formal_checks.values()),
        "status": "pass" if all(formal_checks.values()) else "fail",
        "checks": checks,
        "figure": figure,
    }


def score(record, oracle=None):
    """Score curve identity and chart semantics, with underdetermined recipe diagnostics."""
    gold = reference()
    if oracle is None:
        return {
            "passed": None,
            "complete": False,
            "status": "not_scoreable",
            "recipe": {"passed": None, "status": "not_scoreable", "curves": []},
            "numeric": {"passed": None, "status": "not_scoreable", "curves": []},
            "plot": _plot_score(record, gold),
        }
    expected_axis = [float(value) for value in oracle["axis"]["values"]]
    scoring_policy = evaluation_standard().get("figure") or gold.get("scoring_policy") or {}
    thresholds = scoring_policy.get("numeric_thresholds") or gold["thresholds"]
    available = record.get("numeric_results") or []
    recipe_rows = []
    numeric_rows = []
    used = set()
    for curve in gold["curves"]:
        match_index = next(
            (
                index
                for index, item in enumerate(available)
                if index not in used and _curve_matches(item, curve)
            ),
            None,
        )
        if match_index is None:
            recipe_rows.append({"curve": curve["id"], "present": False, "axis_exact": False})
            numeric_rows.append(
                {"curve": curve["id"], "within": None, "detail": "missing curve"}
            )
            continue
        used.add(match_index)
        item = available[match_index]
        axis = [float(value) for value in ((item.get("axis") or {}).get("values") or [])]
        experiment_exact = _experiment_matches(item, gold)
        axis_exact = experiment_exact and len(axis) == len(expected_axis) and all(
            _same_number(left, right) for left, right in zip(axis, expected_axis, strict=True)
        )
        version_matched = str(item.get("version") or "") == str(oracle.get("smrt_version") or "")
        recipe_rows.append(
            {
                "curve": curve["id"],
                "present": True,
                "experiment_exact": experiment_exact,
                "axis_exact": axis_exact,
                "version_matched": version_matched,
                "stickiness_match": _stickiness_matches(item, curve),
            }
        )
        got = [float(value) for value in ((item.get("series") or {}).get("ks_per_m") or [])]
        wanted = [float(value) for value in oracle["series"][curve["id"]]]
        comparable = axis_exact and version_matched
        nrmse, nmax = (
            _normalised_errors(got, wanted) if comparable else (None, None)
        )
        within = (
            nrmse <= thresholds["normalized_rmse"]
            and nmax <= thresholds["normalized_max_absolute_error"]
            if nrmse is not None and nmax is not None
            else None
        )
        numeric_rows.append(
            {
                "curve": curve["id"],
                "normalized_rmse": nrmse,
                "normalized_max_absolute_error": nmax,
                "within": within,
                "comparable": comparable,
            }
        )
    plot = _plot_score(record, gold)
    structural_passed = len(used) == 6 and all(item["present"] for item in recipe_rows)
    structural_passed = structural_passed and plot["passed"]
    recipe_diagnostic = len(used) == 6 and all(
        item["experiment_exact"] and item["axis_exact"] and item["version_matched"]
        for item in recipe_rows
    )
    numeric_comparable = len(numeric_rows) == 6 and all(
        item.get("comparable") and item.get("within") is not None for item in numeric_rows
    )
    recipe_status = (
        "diagnostic_only"
        if scoring_policy.get("notebook_recipe") == "diagnostic_only"
        else "pass" if recipe_diagnostic else "fail"
    )
    numeric_policy = scoring_policy.get("numeric_reference")
    numeric_status = (
        "not_scoreable"
        if numeric_policy == "not_scoreable"
        else "pass" if numeric_comparable and all(item["within"] for item in numeric_rows)
        else "fail" if numeric_comparable
        else "not_scoreable"
    )
    status = "pass" if structural_passed and numeric_policy != "not_scoreable" else (
        "not_scoreable" if structural_passed else "fail"
    )
    return {
        "passed": True if status == "pass" else False if status == "fail" else None,
        "complete": True,
        "status": status,
        "structural_passed": structural_passed,
        "oracle_smrt_version": oracle.get("smrt_version"),
        "recipe": {
            "passed": True if recipe_status == "pass" else None,
            "status": recipe_status,
            "curves": recipe_rows,
        },
        "numeric": {
            "passed": (
                True if numeric_status == "pass" else False if numeric_status == "fail" else None
            ),
            "status": numeric_status,
            "curves": numeric_rows,
        },
        "plot": plot,
    }


def write_aspect_diagnostic(record, output_path):
    """Render candidate curves with the reference plot geometry.

    This is an evaluation-only visual aid. It does not compare values, calculate an
    error metric, or change any figure-judge result. The limits and axes box ratio
    live in the versioned Q1 fixture rather than in production planning code.
    """
    gold = reference()
    diagnostic = (gold.get("visual_reference") or {}).get("diagnostic") or {}
    available = record.get("numeric_results") or []
    if not available:
        return {"status": "skipped", "reason": "missing_numeric_results"}
    x_limits = diagnostic.get("x_limits")
    y_limits = diagnostic.get("y_limits")
    axes_box_ratio = diagnostic.get("axes_box_ratio")
    if (
        not isinstance(x_limits, (list, tuple))
        or len(x_limits) != 2
        or not isinstance(y_limits, (list, tuple))
        or len(y_limits) != 2
        or not isinstance(axes_box_ratio, (int, float))
        or axes_box_ratio <= 0
    ):
        return {"status": "skipped", "reason": "missing_fixture_geometry"}

    curves = []
    used = set()
    for curve in gold.get("curves") or []:
        match_index = next(
            (
                index
                for index, item in enumerate(available)
                if index not in used and _curve_matches(item, curve)
            ),
            None,
        )
        if match_index is None:
            continue
        item = available[match_index]
        axis = [float(value) for value in ((item.get("axis") or {}).get("values") or [])]
        values = [
            float(value) for value in ((item.get("series") or {}).get("ks_per_m") or [])
        ]
        if not axis or len(axis) != len(values):
            continue
        used.add(match_index)
        curves.append((curve.get("label") or curve.get("id") or "candidate", axis, values))
    if not curves:
        return {"status": "skipped", "reason": "no_usable_numeric_curves"}

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure_width = 8.0
    axes_width = 0.72
    axes_height = axes_width / float(axes_box_ratio)
    figure_height = max(4.5, axes_height + 1.0)
    figure = plt.figure(figsize=(figure_width, figure_height))
    axes = figure.add_axes([0.14, 0.16, axes_width, axes_height])
    for label, axis, values in curves:
        axes.plot(axis, values, linewidth=1.8, label=label)
    axes.set_xlim(float(x_limits[0]), float(x_limits[1]))
    axes.set_ylim(float(y_limits[0]), float(y_limits[1]))
    axes.set_xlabel("Density (kg m$^{-3}$)")
    axes.set_ylabel("Scattering coefficient (m$^{-1}$)")
    axes.set_title("Evaluation-only shape diagnostic")
    axes.grid(alpha=0.2)
    axes.legend(fontsize=7, loc="best")
    figure.savefig(destination, dpi=150)
    plt.close(figure)
    return {
        "status": "written",
        "path": str(destination),
        "curves": [label for label, _axis, _values in curves],
        "x_limits": [float(value) for value in x_limits],
        "y_limits": [float(value) for value in y_limits],
        "axes_box_ratio": float(axes_box_ratio),
    }


def deterministic_report_checks(record, figure_score, figure_judgement=None):
    answer = str(record.get("answer") or "")
    raw_mode = (record.get("switches") or {}).get("paper_access") == "raw_pdf"
    markers = record.get("markers") or {}
    literature_markers = {str(value) for value in markers.get("literature", [])}
    model_markers = {str(value) for value in markers.get("model", [])}
    citation_check = record.get("citation_check") or {}
    unresolved = list(citation_check.get("unresolved") or [])
    declared = str(record.get("reproduction_outcome") or "")
    judged_figure_status = (figure_judgement or {}).get("status")
    visual_validation_passed = judged_figure_status == "pass"
    overclaim = any(
        phrase in answer.lower()
        for phrase in ("exact reproduction", "exactly reproduced", "quantitatively reproduced")
    )
    source_evidence = (
        bool((record.get("evidence") or {}).get("raw_pdf_pages"))
        and citation_check.get("passed") is True
        and (
            "10.5194/gmd-11-2763-2018" in answer
            or "picard" in answer.lower()
            or "soil moisture and ocean salinity" in answer.lower()
        )
    ) if raw_mode else (
        bool(literature_markers)
        and bool(model_markers)
        and citation_check.get("passed") is True
    )
    checks = {
        "report_exists": bool(answer.strip()),
        "outcome_declared": declared in {"reproduced", "partial", "not_identifiable", "failed"},
        "evidence_resolved": source_evidence,
        "computed_result_identified": bool(record.get("numeric_results")),
        "model_version_qualified": any(
            phrase in answer.lower() for phrase in ("version", "1.5.1", "2018")
        ),
        # Metadata/recipe checks remain audit diagnostics. A passed visual review is the
        # primary figure gate when the paper leaves execution parameters unspecified.
        "calibrated_outcome": not overclaim
        and (visual_validation_passed or declared != "reproduced"),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "unresolved_markers": unresolved,
        "visual_validation": "pass" if visual_validation_passed else "not_passed",
        "plot_checks_are_diagnostic": True,
    }
