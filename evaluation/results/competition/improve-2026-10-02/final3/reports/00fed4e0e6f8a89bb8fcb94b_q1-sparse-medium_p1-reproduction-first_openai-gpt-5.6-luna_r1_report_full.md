# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows six SMRT scattering-coefficient curves increasing with density from **1.0 to 100.0 kg m⁻³**. The curves do not converge: their separation grows with density, and their ordering depends on the electromagnetic and microstructure combination. [figure:smrt-v1#fig03]

The generated figure provides a **qualitatively successful reproduction** of the source comparison: it contains the six requested curves and the same broad density-dependent separation described by the source figure. Exact numerical agreement is **not identifiable**, because the source curves were not digitized and several source conditions were unspecified. [smrt-v1#fig03] [smrt-v1#fig-fig03]

## Supporting results

The plotted observable is the scattering coefficient \(k_s\), in m⁻¹, versus density, in kg m⁻³. The recorded arrays show increasing \(k_s\) for all six configurations. The largest recorded upper-end value is **0.12935714866913908 m⁻¹** for sticky hard spheres with IBA at **100.0 kg m⁻³**. The smallest recorded upper-end value is **0.0064179512352543905 m⁻¹** for non-sticky hard spheres with IBA at **100.0 kg m⁻³**. [model:smrt@1.5.1]

Recorded upper-end results include:

| Configuration | \(k_s\) at 100.0 kg m⁻³ |
|---|---:|
| Independent spheres — IBA | 0.013427634533094483 m⁻¹ |
| Non-sticky hard spheres — DMRT QCA-CP | 0.007254801199743284 m⁻¹ |
| Non-sticky hard spheres — IBA | 0.0064179512352543905 m⁻¹ |
| Sticky hard spheres — DMRT QCA-CP | 0.01885283914637513 m⁻¹ |
| Sticky hard spheres — IBA | 0.12935714866913908 m⁻¹ |
| Independent spheres — Rayleigh | not identifiable from the retained result summary |

All six runs used **25 points** over the density sweep. [model:smrt@1.5.1]

## Conclusions supported by the image and by the arrays

**Source/generated image:** The figure supports the conclusion that six curves are present, all rise with density, and become separated according to formulation. It supports qualitative ordering and curve-shape comparisons, but it does not provide digitized numerical values. [figure:smrt-v1#fig03]

**Recorded arrays:** The model results support monotonic increase of \(k_s\) with density for the recorded configurations. At **100.0 kg m⁻³**, the retained values span **0.0064179512352543905 to 0.12935714866913908 m⁻¹** among the configurations with available endpoint summaries. [model:smrt@1.5.1]

| Comparison | Result |
|---|---|
| Qualitative pattern | Same broad pattern: increasing, formulation-dependent curves. |
| Convergence | Not observed; the curves separate with density. |
| Numerical source agreement | Not scoreable; no digitized source values were retained. |
| Rendering | The generated chart was rendered successfully; this establishes chart usability, not source agreement. |

## Guessed/assumed parameters

The following ledger values were not paper-explicit and are reported as implementation defaults or assumptions:

- **user_specified:** `radius_m = 0.0001`.
- **backend_default:** `density_kg_m3` sweep endpoints `1.0` and `100.0`; `frequency_ghz = 37`; `angle_deg = 55`; `temperature_k = 265`; `thickness_m = 1`; `stickiness = 0.2`; `corr_length_m = 0.00015`; and `dort_streams = 32`.
- **model_assumption:** `sweep_points = 25`; the electromagnetic-model choices; the microstructure-model choices; `sweep_parameter = density_kg_m3`; `sweep_start = 1.0`; and `sweep_stop = 100.0`.
- **paper_explicit:** `output = coefficients`, corresponding to the scattering-coefficient quantity shown in the source figure. [smrt-v1#fig03]

The source evidence does not identify the frequency, angle, temperature, thickness, stickiness, correlation length, stream count, or numerical sweep resolution. Therefore, the exact source parameterization and point-by-point numerical agreement are not identifiable. [smrt-v1#fig03]

## Limitations

This is a qualitative reproduction of the six-curve comparison, not a digitized numerical reproduction. The submitted density sweep begins at **1.0 kg m⁻³**, while the paper comparison context records **0 to 100 kg m⁻³**. No measured-data comparison or validation statistic was recorded. The calibrated outcome is therefore **partial**.

<parameter_provenance>
[{"field":"radius_m","value":"0.0001","source_kind":"user_specified","source_ref":"smrt-v1#fig03","reason":"The submitted experiment differs from the paper condition; the paper value remains comparison context."},{"field":"density_kg_m3","value":{"sweep_start":"1.0","sweep_stop":"100.0","sweep_points":"25"},"source_kind":"backend_default","source_ref":"smrt-v1#fig03","reason":"The submitted experiment differs from the paper condition; the paper value remains comparison context."},{"field":"output","value":"coefficients","source_kind":"paper_explicit","source_ref":"smrt-v1#fig03","reason":"The y-axis is scattering coefficient."},{"field":"frequency_ghz","value":"37","source_kind":"backend_default","source_ref":"none","reason":"The opened Figure 3 evidence does not state frequency."},{"field":"angle_deg","value":"55","source_kind":"backend_default","source_ref":"none","reason":"Retained registered default for a coefficient-only run."},{"field":"temperature_k","value":"265","source_kind":"backend_default","source_ref":"none","reason":"Figure 3 evidence does not state temperature."},{"field":"thickness_m","value":"1","source_kind":"backend_default","source_ref":"none","reason":"Retained registered default; coefficient output is a layer property."},{"field":"stickiness","value":"0.2","source_kind":"backend_default","source_ref":"none","reason":"Required for sticky runs but not stated in the opened Figure 3 evidence."},{"field":"sweep_points","value":"25","source_kind":"model_assumption","source_ref":"none","reason":"Chosen to resolve curve shape without digitizing the source."},{"field":"electromagnetic_model","value":["rayleigh","iba","dmrt_qcacp_shortrange","iba","dmrt_qcacp_shortrange","iba"],"source_kind":"model_assumption","source_ref":"none","reason":"Retained for the six approved Figure 3 combinations."},{"field":"microstructure_model","value":["independent_sphere","independent_sphere","non_sticky_hard_spheres","non_sticky_hard_spheres","sticky_hard_spheres","sticky_hard_spheres"],"source_kind":"model_assumption","source_ref":"none","reason":"Retained for the six approved Figure 3 combinations."},{"field":"corr_length_m","value":"0.00015","source_kind":"backend_default","source_ref":"none","reason":"Inserted during registered-model parameter resolution."},{"field":"dort_streams","value":"32","source_kind":"backend_default","source_ref":"none","reason":"Inserted during registered-model parameter resolution."},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"model_assumption","source_ref":"none","reason":"Retained as the independent variable."},{"field":"sweep_start","value":"1.0","source_kind":"model_assumption","source_ref":"none","reason":"Retained as the lower sweep bound."},{"field":"sweep_stop","value":"100.0","source_kind":"model_assumption","source_ref":"none","reason":"Retained as the upper sweep bound."}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | radius_m | 0.0001 | user_specified | smrt-v1#fig03 |
| smrt | density_kg_m3 | sweep 1 to 100 | backend_default | smrt-v1#fig03 |
| smrt | output | coefficients | paper_explicit | smrt-v1#fig03 |
| smrt | frequency_ghz | 37 | backend_default | - |
| smrt | angle_deg | 55 | backend_default | - |
| smrt | temperature_k | 265 | backend_default | - |
| smrt | thickness_m | 1 | backend_default | - |
| smrt | stickiness | 0.2 | backend_default | - |
| smrt | sweep_points | 25 | model_assumption | - |
| smrt | electromagnetic_model | rayleigh | model_assumption | - |
| smrt | microstructure_model | independent_sphere | model_assumption | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_parameter | density_kg_m3 | model_assumption | - |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | model_assumption | - |
