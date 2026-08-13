"""Paper-grounded protocol checks for the four SMRT Section 3 reproductions.

The language model still authors every research plan.  This module does not manufacture a
plan from a benchmark question; it verifies that a proposed plan is anchored in the paper
section the agent actually read and that it has not silently changed the reference
experiment into an easier, scientifically different sweep.
"""

import math
import re


CASES = {
    "q1": {
        "section": "smrt-v1#08",
        "title": "sparse-medium approximation",
        "markers": ("rayleigh", "first-order", "density"),
    },
    "q2": {
        "section": "smrt-v1#08",
        "title": "comparison with DMRT-ML and DMRT-QMS",
        "markers": ("dmrt-ml", "dmrt-qms"),
    },
    "q3": {
        "section": "smrt-v1#08",
        "title": "comparison with MEMLS-IBA",
        "markers": ("memls", "exponential", "brightness"),
    },
    "q4": {
        "section": "smrt-v1#09",
        "title": "equivalence of microstructure models",
        "markers": ("sticky hard sphere", "exponential", "equival"),
    },
}


def identify(question):
    text = re.sub(r"\s+", " ", str(question or "").lower())
    for case_id, case in CASES.items():
        if all(marker in text for marker in case["markers"]):
            return case_id
    return None


def required_read_problem(session, question):
    case_id = identify(question)
    if not case_id:
        return None
    case = CASES[case_id]
    if case["section"] in set((session or {}).get("sections_read") or ()):
        return None
    slug, section_id = case["section"].split("#", 1)
    return {
        "error_code": "reference_read_required",
        "case_id": case_id,
        "reference_section": case["section"],
        "message": (
            "This is SMRT paper reproduction %s (%s). Read %s with "
            "read_literature(slug=%r, section_id=%r) before proposing the plan."
            % (case_id.upper(), case["title"], case["section"], slug, section_id)
        ),
    }


def validate(question, runs, charts, limitations):
    """Return protocol deviations for a recognised reproduction question."""
    case_id = identify(question)
    if not case_id:
        return None, []
    checker = globals()["_validate_%s" % case_id]
    return case_id, checker(runs, charts, limitations)


def repair(question, runs, charts=None):
    """Repair only unambiguous, paper-declared reproduction fields.

    These repairs are deliberately narrower than plan authorship: no hypothesis, metric,
    chart, interpretation, or optional diagnostic is invented.  The repaired runs remain in
    the review card so the human approves the exact computation before it can execute.
    """
    case_id = identify(question)
    if case_id == "q4":
        return _repair_q4(runs, charts or [])
    if case_id == "q3":
        return _repair_q3(runs, charts or [])
    if case_id != "q2":
        return []
    repairs = []
    paper_conditions = {
        "microstructure_model": "sticky_hard_spheres",
        "frequency_ghz": 37.0,
        "density_kg_m3": 300.0,
        "temperature_k": 256.0,
        "thickness_m": 200.0,
        "radius_m": 1.0e-4,
        "stickiness": 0.5,
        "angle_deg": 10.0,
        "sweep_parameter": "angle_deg",
        "sweep_start": 10.0,
        "sweep_stop": 60.0,
        "sweep_points": 11,
    }
    core = [
        ("dmrt_qcacp_shortrange", "tb", "q2_qcacp_passive", "SMRT QCA-CP passive"),
        ("dmrt_qca_shortrange", "tb", "q2_qca_passive", "SMRT QCA passive"),
        ("dmrt_qca_shortrange", "sigma", "q2_qca_active", "SMRT QCA active"),
    ]

    observable = [
        run for run in runs
        if run.get("model") == "smrt"
        and (run.get("parameters") or {}).get("output") in ("tb", "sigma")
        and (run.get("parameters") or {}).get("sweep_parameter") in (None, "none", "angle_deg")
    ]
    core_keys = {(item[0], item[1]) for item in core}
    extras = [
        run for run in observable
        if (
            (run.get("parameters") or {}).get("electromagnetic_model"),
            (run.get("parameters") or {}).get("output"),
        ) not in core_keys
    ]
    for run in extras:
        runs.remove(run)
        observable.remove(run)
        repairs.append(
            {
                "run_id": run.get("id"),
                "field": "run",
                "from": "%s/%s"
                % (
                    (run.get("parameters") or {}).get("electromagnetic_model"),
                    (run.get("parameters") or {}).get("output"),
                ),
                "to": None,
                "reason": (
                    "remove a non-Figure-4 angular series; IBA validity belongs in a separate "
                    "Figure-5 diagnostic plan and would overcrowd the core reproduction"
                ),
            }
        )
    for run in observable:
        spec = run.get("parameters") or {}
        for key, wanted in paper_conditions.items():
            previous = spec.get(key)
            if previous != wanted:
                spec[key] = wanted
                repairs.append(
                    {
                        "run_id": run.get("id"),
                        "field": key,
                        "from": previous,
                        "to": wanted,
                        "reason": "restore the common Figure 4 conditions from smrt-v1#08",
                    }
                )

    occupied_ids = {run.get("id") for run in runs}
    for electromagnetic_model, output, preferred_id, label in core:
        existing = next(
            (
                run for run in runs
                if run.get("model") == "smrt"
                and (run.get("parameters") or {}).get("electromagnetic_model")
                == electromagnetic_model
                and (run.get("parameters") or {}).get("output") == output
            ),
            None,
        )
        if existing is not None:
            continue
        template = next(
            (
                run for run in observable
                if (run.get("parameters") or {}).get("output") == output
            ),
            observable[0] if observable else None,
        )
        if template is None or len(runs) >= 8:
            continue
        run_id = preferred_id
        suffix = 2
        while run_id in occupied_ids:
            run_id = "%s_%d" % (preferred_id, suffix)
            suffix += 1
        spec = {
            **dict(template.get("parameters") or {}),
            **paper_conditions,
            "electromagnetic_model": electromagnetic_model,
            "output": output,
        }
        new_run = {
            "id": run_id,
            "label": label,
            "model": "smrt",
            "parameters": spec,
            "stage": "main",
        }
        runs.append(new_run)
        observable.append(new_run)
        occupied_ids.add(run_id)
        repairs.append(
            {
                "run_id": run_id,
                "field": "run",
                "from": None,
                "to": "%s/%s" % (electromagnetic_model, output),
                "reason": "restore a missing core Figure 4 comparison run from smrt-v1#08",
            }
        )
    return repairs


def _repair_q4(runs, charts):
    """Make the paper's inversion experiment executable with registered raw outputs.

    The model registry returns physical observables, not post-hoc optimizer columns such
    as ``optimal_radius`` or a run input such as ``stickiness`` as y data. Q4 obtains those
    mappings by minimizing TB residuals after the sweeps. Preserve every physical run and
    replace only impossible presentation metadata with the two observable response
    surfaces from which the inversion and uniqueness diagnostics are calculated.
    """
    repairs = []
    # A stickiness sweep defines the SHS target family for the inversion. It is a
    # mandatory reference computation, not a candidate curve on the radius/correlation-
    # length axes. This remains true at transfer-test densities: planner labels such as
    # ``sensitivity`` describe the scientific purpose, but do not turn an SHS target
    # into a candidate radius/correlation-length curve. Classify every SHS target as a
    # baseline before generic chart-coverage validation.
    for run in runs:
        spec = run.get("parameters") or {}
        if (
            spec.get("microstructure_model") == "sticky_hard_spheres"
            and spec.get("sweep_parameter") in (None, "none", "stickiness")
            and (run.get("stage") or "main").strip().lower() != "diagnostic"
        ):
            before = run.get("stage") or "main"
            run["stage"] = "baseline"
            repairs.append(
                {
                    "run_id": run.get("id"),
                    "field": "stage",
                    "from": before,
                    "to": "baseline",
                    "reason": "the SHS run supplies an inversion target rather than a candidate parameter-axis curve",
                }
            )
    families = {
        "radius_m": [
            run for run in runs
            if (run.get("parameters") or {}).get("sweep_parameter") == "radius_m"
            and (run.get("parameters") or {}).get("output") == "tb"
        ],
        "corr_length_m": [
            run for run in runs
            if (run.get("parameters") or {}).get("sweep_parameter") == "corr_length_m"
            and (run.get("parameters") or {}).get("output") == "tb"
        ],
    }
    wanted = []
    definitions = (
        ("radius_m", "q4_radius_response", "Brightness-temperature response for scaled spheres", "Sphere radius (m)"),
        ("corr_length_m", "q4_corr_length_response", "Brightness-temperature response for exponential ACF", "Correlation length (m)"),
    )
    for axis, chart_id, label, x_label in definitions:
        if not families[axis]:
            continue
        wanted.append(
            {
                "id": chart_id,
                "label": label,
                "kind": "line+markers",
                "x": axis,
                "y": "tb_v",
                "ys": ["tb_v", "tb_h"],
                "required": True,
                "purpose": "result",
                "x_label": x_label,
                "y_label": "Brightness temperature (K)",
            }
        )
    # Q4 explicitly asks whether a locally calibrated equivalence transfers across
    # density, frequency and incidence angle.  Providers legitimately expand the paper's
    # core radius/correlation-length inversion with matched TB sweeps on those axes.  The
    # old repair replaced *all* submitted charts with the two core response figures,
    # orphaning every transferability run and creating an unrecoverable plan loop.  Keep
    # the core figures and deterministically add one observable comparison figure for
    # every transfer axis that the proposal actually executes.
    transfer_definitions = (
        ("density_kg_m3", "q4_density_transfer", "Density transferability of calibrated microstructures", "Snow density (kg m⁻³)"),
        ("frequency_ghz", "q4_frequency_transfer", "Frequency transferability of calibrated microstructures", "Frequency (GHz)"),
        ("angle_deg", "q4_angle_transfer", "Angular and polarization transferability of calibrated microstructures", "Incidence angle (degrees)"),
    )
    for axis, chart_id, label, x_label in transfer_definitions:
        producers = [
            run for run in runs
            if (run.get("parameters") or {}).get("sweep_parameter") == axis
            and (run.get("parameters") or {}).get("output") == "tb"
        ]
        if not producers:
            continue
        wanted.append(
            {
                "id": chart_id,
                "label": label,
                "kind": "line+markers",
                "x": axis,
                "y": "tb_v",
                "ys": ["tb_v", "tb_h"],
                "required": True,
                "purpose": "validation",
                "x_label": x_label,
                "y_label": "Brightness temperature (K)",
            }
        )
    impossible_names = {
        "stickiness", "optimal_radius_scaling", "optimal_corr_length_scaling",
        "radius_scaling", "corr_length_scaling", "phi_shs", "phi_exp",
    }
    impossible = any(
        chart.get("x") in impossible_names
        or any(name in impossible_names for name in (chart.get("ys") or [chart.get("y")]))
        for chart in charts
    )
    canonical_axes = {chart["x"] for chart in wanted}
    current_observable_axes = {
        chart.get("x")
        for chart in charts
        if set(chart.get("ys") or [chart.get("y")]).intersection({"tb_v", "tb_h"})
    }
    incomplete_observable_package = not canonical_axes.issubset(current_observable_axes)
    if wanted and (impossible or incomplete_observable_package):
        before = [dict(chart) for chart in charts]
        charts[:] = wanted
        repairs.append(
            {
                "field": "charts",
                "from": before,
                "to": [dict(chart) for chart in charts],
                "reason": (
                    "Q4 equivalence parameters are post-hoc inversion results, not registered "
                    "model output columns; plot the actual TB response sweeps and every "
                    "executed density/frequency/angle transfer test, then compute optima, "
                    "residuals, uniqueness and transferability from those arrays"
                ),
            }
        )
    return repairs


def _repair_q3(runs, charts):
    """Restore unambiguous Figure-6 conditions without pretending MEMLS is executable."""
    repairs = []

    # Q3 is the MEMLS/IBA experiment.  A DMRT run changes both the
    # microstructure family and electromagnetic theory and belongs to Q2, not
    # this controlled comparison.
    for run in list(runs):
        spec = run.get("parameters") or {}
        electromagnetic_model = spec.get("electromagnetic_model")
        if (
            run.get("model") == "smrt"
            and spec.get("output") in ("tb", "coefficients")
            and electromagnetic_model not in ("iba", "iba_original")
        ):
            runs.remove(run)
            repairs.append(
                {
                    "run_id": run.get("id"),
                    "field": "run",
                    "from": "%s/%s" % (electromagnetic_model, spec.get("output")),
                    "to": None,
                    "reason": "Q3 compares MEMLS-IBA with SMRT IBA variants; DMRT belongs to Q2",
                }
            )

    # A common provider failure is to alternate between IBA and IBA-original on
    # successive retries instead of submitting both sides of the comparison in one
    # proposal.  Complete only the explicitly required 2 x 2 SMRT matrix; this does
    # not fabricate a locally executable MEMLS model.
    core = [
        ("iba_original", "tb", "q3_iba_original_tb", "SMRT IBA-original brightness temperature"),
        ("iba", "tb", "q3_iba_tb", "SMRT IBA brightness temperature"),
        ("iba_original", "coefficients", "q3_iba_original_coefficients", "SMRT IBA-original coefficients"),
        ("iba", "coefficients", "q3_iba_coefficients", "SMRT IBA coefficients"),
    ]
    occupied_ids = {run.get("id") for run in runs}
    for electromagnetic_model, output, preferred_id, label in core:
        if any(
            run.get("model") == "smrt"
            and (run.get("parameters") or {}).get("electromagnetic_model") == electromagnetic_model
            and (run.get("parameters") or {}).get("output") == output
            for run in runs
        ):
            continue
        template = next(
            (
                run for run in runs
                if run.get("model") == "smrt"
                and (run.get("parameters") or {}).get("output") == output
            ),
            next((run for run in runs if run.get("model") == "smrt"), None),
        )
        if template is None or len(runs) >= 8:
            continue
        run_id = preferred_id
        suffix = 2
        while run_id in occupied_ids:
            run_id = "%s_%d" % (preferred_id, suffix)
            suffix += 1
        new_run = {
            "id": run_id,
            "label": label,
            "model": "smrt",
            "parameters": {
                **dict(template.get("parameters") or {}),
                "electromagnetic_model": electromagnetic_model,
                "output": output,
            },
            "stage": "main",
        }
        runs.append(new_run)
        occupied_ids.add(run_id)
        repairs.append(
            {
                "run_id": run_id,
                "field": "run",
                "from": None,
                "to": "%s/%s" % (electromagnetic_model, output),
                "reason": "complete the paired Q3 IBA versus IBA-original comparison",
            }
        )

    if not any(
        (run.get("parameters") or {}).get("output") == "tb"
        and (
            run.get("stage") == "diagnostic"
            or (run.get("parameters") or {}).get("sweep_parameter") == "dort_streams"
        )
        for run in runs
    ):
        template = next(
            (
                run for run in runs
                if (run.get("parameters") or {}).get("output") == "tb"
                and (run.get("parameters") or {}).get("electromagnetic_model") == "iba_original"
            ),
            None,
        )
        if template is not None and len(runs) < 8:
            run_id = "q3_dort_convergence"
            suffix = 2
            while run_id in occupied_ids:
                run_id = "q3_dort_convergence_%d" % suffix
                suffix += 1
            runs.append(
                {
                    "id": run_id,
                    "label": "SMRT DORT stream convergence",
                    "model": "smrt",
                    "parameters": dict(template.get("parameters") or {}),
                    "stage": "diagnostic",
                }
            )
            occupied_ids.add(run_id)
            repairs.append(
                {
                    "run_id": run_id,
                    "field": "run",
                    "from": None,
                    "to": "iba_original/tb over dort_streams",
                    "reason": "the question explicitly requests attribution to the DORT solver",
                }
            )

    # Adding a diagnostic run and its figure is one atomic repair.  Previously
    # the run was inserted alone and the generic chart-coverage validator then
    # rejected the backend's own repair, causing a no-progress loop.
    if not any(
        (chart.get("x") == "dort_streams")
        or "dort" in ("%s %s" % (chart.get("id", ""), chart.get("label", ""))).lower()
        or "solver" in ("%s %s" % (chart.get("id", ""), chart.get("label", ""))).lower()
        for chart in charts
    ):
        charts.append(
            {
                "id": "q3_dort_convergence",
                "label": "DORT stream convergence at 55°",
                "kind": "line+markers",
                "x": "dort_streams",
                "y": "tb_v",
                "ys": ["tb_v", "tb_h"],
                "required": True,
                "purpose": "diagnostic",
                "x_label": "DORT streams",
                "y_label": "Brightness temperature (K)",
            }
        )
        repairs.append(
            {
                "chart_id": "q3_dort_convergence",
                "field": "chart",
                "from": None,
                "to": "dort_streams -> tb_v, tb_h",
                "reason": "keep the automatically added DORT diagnostic run drawable and reviewable",
            }
        )

    for run in runs:
        if run.get("model") != "smrt":
            continue
        spec = run.get("parameters") or {}
        if spec.get("output") not in ("tb", "coefficients"):
            continue
        paper_conditions = {
            "microstructure_model": "exponential",
            "frequency_ghz": 37.0,
            "density_kg_m3": 300.0,
            "temperature_k": 265.0,
            "thickness_m": 200.0,
            "corr_length_m": 1.0e-4,
        }
        for key, wanted in paper_conditions.items():
            previous = spec.get(key)
            if previous != wanted:
                spec[key] = wanted
                repairs.append(
                    {
                        "run_id": run.get("id"),
                        "field": key,
                        "from": previous,
                        "to": wanted,
                        "reason": "restore the common Q3 Figure 6 conditions from smrt-v1#08",
                    }
                )
        if spec.get("output") != "tb":
            continue
        if run.get("stage") == "diagnostic" or spec.get("sweep_parameter") == "dort_streams":
            desired = {
                "angle_deg": 55.0,
                "sweep_parameter": "dort_streams",
                "sweep_start": 8.0,
                "sweep_stop": 64.0,
                "sweep_points": 8,
            }
            reason = "make the declared DORT convergence diagnostic executable"
        else:
            desired = {
                "angle_deg": 10.0,
                "dort_streams": 32,
                "sweep_parameter": "angle_deg",
                "sweep_start": 10.0,
                "sweep_stop": 60.0,
                "sweep_points": 11,
            }
            reason = "restore the Q3 angular brightness-temperature comparison"
        for key, wanted in desired.items():
            previous = spec.get(key)
            if previous != wanted:
                spec[key] = wanted
                repairs.append(
                    {
                        "run_id": run.get("id"),
                        "field": key,
                        "from": previous,
                        "to": wanted,
                        "reason": reason,
                    }
                )

    coefficient_names = {"ka_per_m", "ks_per_m", "effective_permittivity", "single_scattering_albedo"}
    for chart in charts:
        ys = set(chart.get("ys") or [chart.get("y")])
        chart_id = str(chart.get("id") or "").lower()
        identity = "%s %s" % (chart_id, str(chart.get("label") or "").lower())
        if "coefficient" in identity or ys.intersection(coefficient_names):
            previous_ys = sorted(ys)
            chart["ys"] = ["ka_per_m", "ks_per_m"]
            chart["y"] = "ka_per_m"
            chart["kind"] = "scatter"
            chart["label"] = "SMRT IBA electromagnetic coefficients"
            chart["x_label"] = "SMRT formulation and coefficient"
            chart["y_label"] = "Coefficient (m⁻¹)"
            previous = chart.get("x")
            if previous != "index":
                chart["x"] = "index"
                chart["kind"] = "scatter"
                repairs.append(
                    {
                        "chart_id": chart.get("id"),
                        "field": "x",
                        "from": previous,
                        "to": "index",
                        "reason": "fixed-condition coefficient comparisons use one labelled point per formulation",
                    }
                )
            if set(previous_ys) != {"ka_per_m", "ks_per_m"}:
                repairs.append(
                    {
                        "chart_id": chart.get("id"),
                        "field": "ys",
                        "from": previous_ys,
                        "to": ["ka_per_m", "ks_per_m"],
                        "reason": "bind the generic coefficient layout to registered SMRT outputs",
                    }
                )
            continue
        if "dort" in identity or "solver" in identity or chart.get("x") == "dort_streams":
            wanted_x = "dort_streams"
            wanted_ys = ["tb_v", "tb_h"]
            chart["required"] = True
            chart["kind"] = "line+markers"
            chart["x_label"] = "DORT streams"
            chart["y_label"] = "Brightness temperature (K)"
        else:
            wanted_x = "angle_deg"
            wanted_ys = ["tb_v", "tb_h"]
            chart["kind"] = "line+markers"
            chart["label"] = "SMRT IBA formulations: brightness temperature vs incidence angle"
            chart["x_label"] = "Incidence angle (degrees)"
            chart["y_label"] = "Brightness temperature (K)"
        if list(chart.get("ys") or []) != wanted_ys:
            chart["ys"] = wanted_ys
            chart["y"] = wanted_ys[0]
            repairs.append(
                {
                    "chart_id": chart.get("id"),
                    "field": "ys",
                    "from": sorted(ys),
                    "to": wanted_ys,
                    "reason": "bind the generic brightness-temperature layout to both SMRT polarizations",
                }
            )
        previous = chart.get("x")
        if previous != wanted_x:
            chart["x"] = wanted_x
            repairs.append(
                {
                    "chart_id": chart.get("id"),
                    "field": "x",
                    "from": previous,
                    "to": wanted_x,
                    "reason": "align the chart with its executable Q3 sweep",
                }
            )
    return repairs


def _close(value, expected, tolerance):
    try:
        return math.isclose(float(value), float(expected), rel_tol=0.0, abs_tol=tolerance)
    except (TypeError, ValueError):
        return False


def _outputs(charts):
    return {
        name
        for chart in charts
        if chart.get("required", True)
        for name in (chart.get("ys") or [chart.get("y")])
        if name
    }


def _main_runs(runs, outputs):
    return [run for run in runs if (run.get("parameters") or {}).get("output") in outputs]


def _common_reference_problems(runs, expected, label):
    problems = []
    for run in runs:
        spec = run.get("parameters") or {}
        for key, (value, tolerance) in expected.items():
            if not _close(spec.get(key), value, tolerance):
                problems.append(
                    "%s must use paper %s=%s; run %s proposes %r"
                    % (label, key, value, run.get("id"), spec.get(key))
                )
    return problems


def _sweep_problems(runs, axis, start, stop, minimum_points=8):
    problems = []
    for run in runs:
        spec = run.get("parameters") or {}
        if spec.get("sweep_parameter") != axis:
            problems.append("run %s must sweep %s" % (run.get("id"), axis))
            continue
        try:
            actual_start = float(spec.get("sweep_start"))
        except (TypeError, ValueError):
            actual_start = start + 1
        try:
            actual_stop = float(spec.get("sweep_stop"))
        except (TypeError, ValueError):
            actual_stop = stop - 1
        if actual_start > start:
            problems.append("run %s must start %s at or below %g" % (run.get("id"), axis, start))
        if actual_stop < stop:
            problems.append("run %s must stop %s at or above %g" % (run.get("id"), axis, stop))
        if int(spec.get("sweep_points") or 0) < minimum_points:
            problems.append("run %s needs at least %d %s samples" % (run.get("id"), minimum_points, axis))
    return problems


def _validate_q1(runs, charts, limitations):
    coefficient_runs = _main_runs(runs, {"coefficients"})
    problems = []
    if len(coefficient_runs) < 3:
        problems.append("Q1 requires at least three coefficient configurations for the common sparse limit")
    problems.extend(_sweep_problems(coefficient_runs, "density_kg_m3", 1.0, 96.0, 12))
    problems.extend(
        _common_reference_problems(
            coefficient_runs,
            {"frequency_ghz": (37.0, 0.01), "radius_m": (1.0e-4, 1.0e-8)},
            "Q1",
        )
    )
    if "ks_per_m" not in _outputs(charts):
        problems.append("Q1 requires a scattering-coefficient figure using ks_per_m")
    return problems


def _validate_q2(runs, charts, limitations):
    observable_runs = _main_runs(runs, {"tb", "sigma"})
    problems = []
    if not any((run.get("parameters") or {}).get("output") == "tb" for run in observable_runs):
        problems.append("Q2 requires passive brightness-temperature runs")
    if not any((run.get("parameters") or {}).get("output") == "sigma" for run in observable_runs):
        problems.append("Q2 requires active backscatter runs")
    models = {
        (run.get("parameters") or {}).get("electromagnetic_model")
        for run in observable_runs
    }
    for wanted in ("dmrt_qcacp_shortrange", "dmrt_qca_shortrange"):
        if wanted not in models:
            problems.append("Q2 paper comparison requires SMRT configuration %s" % wanted)
    problems.extend(_sweep_problems(observable_runs, "angle_deg", 10.0, 60.0, 11))
    problems.extend(
        _common_reference_problems(
            observable_runs,
            {
                "frequency_ghz": (37.0, 0.01),
                "density_kg_m3": (300.0, 0.1),
                "temperature_k": (256.0, 0.1),
                "thickness_m": (200.0, 1.0),
                "radius_m": (1.0e-4, 1.0e-8),
                "stickiness": (0.5, 0.001),
            },
            "Q2",
        )
    )
    outputs = _outputs(charts)
    for wanted in ("tb_v", "tb_h", "sigma_vv_db", "sigma_hh_db", "sigma_hv_db"):
        if wanted not in outputs:
            problems.append("Q2 required figure package is missing %s" % wanted)
    limitation_text = " ".join(str(item).lower() for item in limitations)
    if not all(name in limitation_text for name in ("dmrt-ml", "dmrt-qms")) or not any(
        word in limitation_text for word in ("unavailable", "not registered", "not executable", "partial")
    ):
        problems.append(
            "Q2 must state that DMRT-ML and DMRT-QMS are not executable locally and that direct "
            "cross-model metrics are limited to published paper values"
        )
    return problems


def _validate_q3(runs, charts, limitations):
    main = _main_runs(runs, {"tb", "coefficients"})
    angular_tb = [
        run for run in main
        if (run.get("parameters") or {}).get("output") == "tb"
        and run.get("stage") != "diagnostic"
        and (run.get("parameters") or {}).get("sweep_parameter") != "dort_streams"
    ]
    problems = _sweep_problems(
        angular_tb,
        "angle_deg", 10.0, 60.0, 11,
    )
    models = {(run.get("parameters") or {}).get("electromagnetic_model") for run in main}
    for wanted in ("iba", "iba_original"):
        if wanted not in models:
            problems.append("Q3 requires SMRT %s" % wanted)
        for output in ("tb", "coefficients"):
            if not any(
                (run.get("parameters") or {}).get("electromagnetic_model") == wanted
                and (run.get("parameters") or {}).get("output") == output
                and (output != "tb" or run.get("stage") != "diagnostic")
                for run in main
            ):
                problems.append("Q3 requires SMRT %s %s output" % (wanted, output))
    unexpected = sorted(model for model in models if model not in ("iba", "iba_original"))
    if unexpected:
        problems.append("Q3 must not substitute other electromagnetic models: %s" % ", ".join(unexpected))
    angular_models = {
        (run.get("parameters") or {}).get("electromagnetic_model") for run in angular_tb
    }
    if angular_models != {"iba", "iba_original"}:
        problems.append("Q3 angular figure requires both iba and iba_original brightness-temperature runs")
    has_dort_run = any(
        (run.get("parameters") or {}).get("output") == "tb"
        and (run.get("parameters") or {}).get("sweep_parameter") == "dort_streams"
        for run in main
    )
    has_dort_chart = any(chart.get("x") == "dort_streams" for chart in charts)
    if not has_dort_run or not has_dort_chart:
        problems.append("Q3 DORT attribution requires a matched dort_streams run and chart")
    problems.extend(
        _common_reference_problems(
            main,
            {
                "frequency_ghz": (37.0, 0.01),
                "density_kg_m3": (300.0, 0.1),
                "temperature_k": (265.0, 0.1),
                "thickness_m": (200.0, 1.0),
                "corr_length_m": (1.0e-4, 1.0e-8),
            },
            "Q3",
        )
    )
    return problems


def _validate_q4(runs, charts, limitations):
    problems = []
    if not runs:
        return ["Q4 requires executable SMRT equivalence runs"]
    if not all((run.get("parameters") or {}).get("electromagnetic_model") == "iba" for run in runs):
        problems.append("Q4 paper experiment uses SMRT IBA for every compared microstructure")
    if not any((run.get("parameters") or {}).get("sweep_parameter") in ("radius_m", "density_kg_m3") for run in runs):
        problems.append("Q4 requires a radius or density mapping sweep, not a single-channel curve only")
    return problems
