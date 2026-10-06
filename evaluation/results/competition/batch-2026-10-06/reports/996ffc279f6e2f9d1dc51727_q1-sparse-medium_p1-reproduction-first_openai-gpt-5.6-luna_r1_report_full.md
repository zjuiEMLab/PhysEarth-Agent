# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The paper identifies **10–20 kg m⁻³** as the valid range for the sparse-medium approximation. [smrt-v1#08] The generated figure covers **1–100 kg m⁻³** with 40 points and shows the six scattering-coefficient curves converging at low density, then separating progressively as density increases. The requested density comparison is therefore: **paper-reported range: 10–20 kg m⁻³; recorded model sweep: 1–100 kg m⁻³**. [model:smrt@1.5.1]

The reproduction is **qualitatively successful**. The generated curves contain the same six theory–microstructure combinations and the same qualitative pattern as the inspected source figure: approximately common low-density behavior followed by increasing divergence at higher density. [figure:smrt-v1#fig03]

## Supporting results

### Conclusion from the source and generated images

The source and generated figures show:

- six curves;
- density on the x-axis, displayed from 0 to 100 kg m⁻³ in the source;
- scattering coefficient \(k_s\) on the y-axis, in m⁻¹;
- close convergence at low density;
- increasing separation toward the upper end of the density range.

The source figure uses a sphere radius of 100 micrometres and compares Rayleigh, IBA, and DMRT QCA-CP formulations with independent-sphere, non-sticky-hard-sphere, and sticky-hard-sphere microstructures. [smrt-v1#fig03]

### Conclusion from the recorded results

The six SMRT v1.5.1 runs each contain 40 points over **density_kg_m3 = 1–100**. The recorded \(k_s\) series increase with density and show the expected low-density convergence followed by greater separation at higher density. [model:smrt@1.5.1]

The runs compare:

1. Rayleigh with independent spheres;
2. IBA with independent spheres;
3. DMRT QCA-CP with non-sticky hard spheres;
4. IBA with non-sticky hard spheres;
5. DMRT QCA-CP with sticky hard spheres;
6. IBA with sticky hard spheres.

The chart was rendered with all six series, and the automatic render check passed. That check establishes that the generated chart is usable and legible; it does not independently establish agreement with the source figure.

## Comparison

| Feature | Source/generated image | Recorded results | Assessment |
|---|---|---|---|
| Density range | Source displays 0–100 kg m⁻³ | Model legally sweeps 1–100 kg m⁻³ | Comparable, with the zero-density endpoint replaced by the model’s legal lower bound |
| Low-density behavior | Curves converge and are approximately linear | Six computed series are closely grouped at low density | Same qualitative pattern |
| Higher-density behavior | Curves separate with increasing density | Computed series increasingly diverge across the upper sweep | Same qualitative pattern |
| Exact numerical agreement | Not recoverable from the image alone | Computed arrays are available | Not scoreable point-for-point from the recorded evidence |

The main qualification is that several source-figure execution parameters were not explicitly stated. The recorded reproduction therefore supports the curve ordering and density-dependent behavior, but not exact numerical identity with the published curves.

## Assumed parameters

### Guessed/assumed parameters

The following ledger values were not treated as paper-explicit:

- `sweep_start = 1` — `assumption`
- `frequency_ghz = 37` — `derived`
- `temperature_k = 265` — `assumption`
- `stickiness = 0.2` — `assumption`
- `electromagnetic_model = rayleigh` — `assumption`
- `microstructure_model = independent_sphere` — `assumption`
- `angle_deg = 55.0` — `model_default`
- `thickness_m = 1.0` — `model_default`
- `density_kg_m3 = 300.0` — `model_default`
- `corr_length_m = 0.00015` — `model_default`
- `dort_streams = 32` — `model_default`
- `sweep_points = 40` — `assumption`

The source figure displays a density start of 0 kg m⁻³, but the registered model uses **sweep_start = 1** because zero is outside the legal model range. The density stop was **sweep_stop = 100**. The source-explicit sphere radius was **radius_m = 0.0001**, and the output was **output = coefficients**. [smrt-v1#fig03] [model:smrt@1.5.1]

## Limitations

The reproduction uses SMRT v1.5.1, while the source paper describes SMRT v1.0. [smrt-v1#00] The model represents a homogeneous snow layer and does not establish behavior for stratified or three-dimensional snowpacks. [smrt-v1#02] Absolute coefficient values may also depend on the assumed temperature, stickiness, angle, thickness, correlation length, numerical stream count, and the unspecified implementation details of the source figure.

## Final conclusion

The paper-supported density range is **10–20 kg m⁻³**. [smrt-v1#08] The recorded reproduction sweeps **1–100 kg m⁻³** and shows convergence at low density with increasing divergence among the six \(k_s\) curves at higher density. [model:smrt@1.5.1] The result is therefore a **qualitatively successful reproduction**, but exact point-by-point numerical agreement is **not scoreable** from the available source-figure information.

<parameter_provenance>
[{"field":"radius_m","value":"0.0001","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"sphere radius of 100 micrometres","reason":"Directly stated in the Figure 3 caption","sensitivity_checked":false},{"field":"output","value":"coefficients","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"scattering coefficient","reason":"The source plots the layer scattering coefficient","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"density is the independent axis","reason":"Density is the source figure independent variable","sensitivity_checked":false},{"field":"sweep_start","value":"1","source_kind":"assumption","source_ref":"smrt-v1#fig03","source_span":"source display begins at 0 kg m-3","reason":"The registered model does not accept zero and uses its legal lower bound","sensitivity_checked":false},{"field":"sweep_stop","value":"100","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"upper density tick at 100 kg m-3","reason":"Matches the source figure upper density limit","sensitivity_checked":false},{"field":"frequency_ghz","value":"37","source_kind":"derived","source_ref":"smrt-v1#07","source_span":"comparisons use 37 GHz unless otherwise stated","reason":"Figure 3 is part of the stated comparisons","sensitivity_checked":false},{"field":"temperature_k","value":"265","source_kind":"assumption","source_ref":"smrt-v1#fig03","source_span":"temperature not identified in the figure caption","reason":"Retained the recorded model value without treating it as paper-given","sensitivity_checked":false},{"field":"stickiness","value":"0.2","source_kind":"assumption","source_ref":"smrt-v1#fig03","source_span":"sticky hard spheres identified without a stickiness value","reason":"Used the recorded value for the sticky-hard-sphere runs","sensitivity_checked":false},{"field":"electromagnetic_model","value":"rayleigh","source_kind":"assumption","source_ref":"smrt-v1#fig03","source_span":"Rayleigh configuration in the planned comparison","reason":"Retained the recorded configuration without attached paper evidence for this field","sensitivity_checked":false},{"field":"microstructure_model","value":"independent_sphere","source_kind":"assumption","source_ref":"smrt-v1#fig03","source_span":"independent-sphere configuration in the planned comparison","reason":"Retained the recorded configuration without attached paper evidence for this field","sensitivity_checked":false},{"field":"angle_deg","value":"55.0","source_kind":"model_default","source_ref":"model:smrt@1.5.1","source_span":"registered backend value","reason":"Inserted by the registered model during parameter resolution","sensitivity_checked":false},{"field":"thickness_m","value":"1.0","source_kind":"model_default","source_ref":"model:smrt@1.5.1","source_span":"registered backend value","reason":"Inserted by the registered model during parameter resolution","sensitivity_checked":false},{"field":"density_kg_m3","value":"300.0","source_kind":"model_default","source_ref":"model:smrt@1.5.1","source_span":"registered backend value","reason":"Base density retained while density was swept","sensitivity_checked":false},{"field":"corr_length_m","value":"0.00015","source_kind":"model_default","source_ref":"model:smrt@1.5.1","source_span":"registered backend value","reason":"Inserted by the registered model during parameter resolution","sensitivity_checked":false},{"field":"dort_streams","value":"32","source_kind":"model_default","source_ref":"model:smrt@1.5.1","source_span":"registered backend value","reason":"Inserted by the registered model during parameter resolution","sensitivity_checked":false},{"field":"sweep_points","value":"40","source_kind":"assumption","source_ref":"model:smrt@1.5.1","source_span":"40 points over density_kg_m3","reason":"Recorded sweep resolution used for the generated chart","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | radius_m | 0.0001 | paper_explicit | smrt-v1#fig03 |
| smrt | output | coefficients | paper_explicit | smrt-v1#fig03 |
| smrt | sweep_parameter | density_kg_m3 | paper_explicit | smrt-v1#fig03 |
| smrt | sweep_start | 1 | model_assumption | smrt-v1#fig03 |
| smrt | sweep_stop | 100 | paper_explicit | smrt-v1#fig03 |
| smrt | frequency_ghz | 37 | paper_inferred | smrt-v1#07 |
| smrt | temperature_k | 265 | model_assumption | smrt-v1#fig03 |
| smrt | stickiness | 0.2 | model_assumption | smrt-v1#fig03 |
| smrt | electromagnetic_model | rayleigh | model_assumption | - |
| smrt | microstructure_model | independent_sphere | model_assumption | - |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | thickness_m | 1.0 | backend_default | - |
| smrt | density_kg_m3 | 300.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_points | 40 | model_assumption | - |
