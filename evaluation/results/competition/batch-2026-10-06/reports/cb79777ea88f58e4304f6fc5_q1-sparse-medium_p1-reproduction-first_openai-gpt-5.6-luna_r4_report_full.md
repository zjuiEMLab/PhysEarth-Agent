# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The paper’s reported sparse-medium density range is **10–20 kg m⁻³** [smrt-v1#08]. Separately, the recorded results show a density sweep of **1.0–100.0 kg m⁻³** [model:smrt@1.5.1]. Within that sweep, the six scattering-coefficient curves converge at low density and separate progressively as density increases. The generated Figure 1 therefore provides a qualitative successful reproduction of the source Figure 3.

A pointwise numerical agreement with the source figure is not identifiable because the source image was not digitized.

## Supporting results

### Conclusion from the source and generated images

The source figure specifies six combinations:

1. independent spheres with Rayleigh;
2. independent spheres with IBA;
3. non-sticky hard spheres with DMRT QCA-CP;
4. non-sticky hard spheres with IBA;
5. sticky hard spheres with DMRT QCA-CP;
6. sticky hard spheres with IBA.

The generated chart contains these six combinations and uses density on the horizontal axis and `ks_per_m` on the vertical axis, reproducing the source figure’s qualitative comparison [smrt-v1#fig03] [model:smrt@1.5.1].

The source and generated images support the same qualitative pattern:

- convergence at low density;
- increasing separation at higher density;
- different behavior associated with both electromagnetic theory and microstructure;
- strongest interpretive relevance within the paper’s stated sparse-medium range of **10–20 kg m⁻³** [smrt-v1#08].

### Conclusion from the recorded model results

The six approved SMRT runs each contain **40 points** over `density_kg_m3`, with the recorded sweep extending from **1.0 kg m⁻³** to **100.0 kg m⁻³** [model:smrt@1.5.1].

The arrays show that:

- the six `ks_per_m` curves are closely grouped at the low-density end;
- all six curves increase with density;
- the curves are increasingly separated toward the upper end of the sweep;
- sticky hard spheres produce the largest scattering coefficients at the high-density end;
- non-sticky hard spheres produce the smallest scattering coefficients at the high-density end;
- within the sticky and non-sticky groups, the DMRT QCA-CP and IBA curves remain distinct.

These statements describe the recorded model arrays, not digitized values from the source image [model:smrt@1.5.1].

### Comparison

| Comparison | Assessment |
|---|---|
| Number and identity of curves | Agree |
| Density and scattering-coefficient axes | Agree |
| Low-density convergence | Same qualitative pattern |
| Higher-density divergence | Same qualitative pattern |
| Paper’s sparse-medium range | **10–20 kg m⁻³** |
| Recorded model sweep | **1.0–100.0 kg m⁻³** |
| Pointwise source-versus-model error | Not scoreable |
| Bias, RMSE, correlation, or percent error | N/A |

The main qualification is that the model sweep extends beyond the paper’s stated sparse-medium range. Consequently, the high-density separation is a recorded behavior of the configured SMRT runs, not evidence that the sparse-medium approximation remains valid through **100.0 kg m⁻³** [smrt-v1#08] [model:smrt@1.5.1].

## Assumed parameters

### Paper-explicit parameters

- `radius_m = 0.0001`; paper value: 100 micrometres; provenance: `paper`.
- `output = coefficients`; plotted observable: scattering coefficient represented by `ks_per_m`; provenance: `paper` [smrt-v1#fig03].

### User-specified formulation choices

- `electromagnetic_model = rayleigh`; provenance: `user`.
- `microstructure_model = independent_sphere`; provenance: `user`.
- `electromagnetic_model = iba`; provenance: `user`.
- `electromagnetic_model = dmrt_qcacp_shortrange`; provenance: `user`.
- `microstructure_model = non_sticky_hard_spheres`; provenance: `user`.
- `microstructure_model = sticky_hard_spheres`; provenance: `user`.

These choices identify the six combinations compared in the approved experiment [smrt-v1#fig03] [model:smrt@1.5.1].

### Guessed/assumed parameters

The following values were not identified as Figure 3 values in the opened evidence and were inherited from the recorded model configuration:

- `density_kg_m3 = sweep 1–100`; provenance: `model_default`.
- `stickiness = 0.2`; provenance: `model_default`.
- `frequency_ghz = 37`; provenance: `model_default`.
- `angle_deg = 55`; provenance: `model_default`.
- `temperature_k = 265`; provenance: `model_default`.
- `thickness_m = 1`; provenance: `model_default`.
- `dort_streams = 32`; provenance: `model_default`.
- `corr_length_m = 0.00015`; provenance: `model_default`.
- `sweep_parameter = density_kg_m3`; provenance: `assumption`.
- `sweep_start = 1.0`; provenance: `assumption`.
- `sweep_stop = 100.0`; provenance: `assumption`.
- `sweep_points = 40`; provenance: `assumption` [model:smrt@1.5.1].

## Limitations

The source Figure 3 was inspected as an image, but its curve values were not digitized. Therefore, numerical source-versus-generated agreement is not scoreable.

The recorded experiment uses **1.0–100.0 kg m⁻³**, whereas the paper states that the sparse-medium approximation is valid only over approximately **10–20 kg m⁻³** [smrt-v1#08]. The portion above that interval should be treated as an extended model sweep rather than as a demonstrated sparse-medium-validity range.

The result is also conditional on the assumed backend parameters listed above. In particular, the opened Figure 3 evidence does not identify the numerical values for frequency, angle, temperature, thickness, correlation length, DORT streams, or sticky-sphere stickiness.

## Final conclusion

The paper reports **10–20 kg m⁻³** as the sparse-medium density range [smrt-v1#08]. The recorded experiment shows the six `ks_per_m` curves over **1.0–100.0 kg m⁻³** [model:smrt@1.5.1]. Within that experiment, the curves converge at low density and diverge with increasing density in the same qualitative manner as the source figure. The reproduction is therefore **qualitatively successful**, but pointwise numerical agreement with the source image remains not identifiable.

<parameter_provenance>
[{"field":"radius_m","value":"0.0001","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"sphere radius 100 micrometres","reason":"Figure 3 fixes the sphere radius.","sensitivity_checked":false},{"field":"density_kg_m3","value":"1.0–100.0","source_kind":"model_default","source_ref":"smrt-v1#fig03","source_span":"density axis shown from 0 to 100 kg m-3","reason":"The recorded executable sweep uses the model-supported interval 1.0–100.0 kg m-3 rather than the displayed paper lower bound.","sensitivity_checked":false},{"field":"output","value":"coefficients","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"layer scattering coefficient","reason":"The plotted observable is represented by ks_per_m.","sensitivity_checked":false},{"field":"electromagnetic_model","value":"rayleigh","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"independent spheres (Rayleigh)","reason":"Required first plotted combination.","sensitivity_checked":false},{"field":"microstructure_model","value":"independent_sphere","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"independent spheres","reason":"Required independent-sphere microstructure combination.","sensitivity_checked":false},{"field":"electromagnetic_model","value":"iba","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"independent spheres (IBA)","reason":"Required second plotted combination.","sensitivity_checked":false},{"field":"electromagnetic_model","value":"dmrt_qcacp_shortrange","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"DMRT QCA-CP","reason":"Required DMRT QCA-CP combinations.","sensitivity_checked":false},{"field":"microstructure_model","value":"non_sticky_hard_spheres","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"non-sticky hard spheres","reason":"Required non-sticky hard-sphere combinations.","sensitivity_checked":false},{"field":"microstructure_model","value":"sticky_hard_spheres","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"sticky hard spheres","reason":"Required sticky hard-sphere combinations.","sensitivity_checked":false},{"field":"stickiness","value":"0.2","source_kind":"model_default","source_ref":"none","source_span":"not identified for Figure 3","reason":"Registered default inherited because the opened evidence does not specify the numerical Figure 3 stickiness.","sensitivity_checked":false},{"field":"frequency_ghz","value":"37","source_kind":"model_default","source_ref":"none","source_span":"not specified for Figure 3","reason":"Registered default inherited.","sensitivity_checked":false},{"field":"angle_deg","value":"55","source_kind":"model_default","source_ref":"none","source_span":"not specified for Figure 3","reason":"Registered default inherited.","sensitivity_checked":false},{"field":"temperature_k","value":"265","source_kind":"model_default","source_ref":"none","source_span":"not specified for Figure 3","reason":"Registered default inherited.","sensitivity_checked":false},{"field":"thickness_m","value":"1","source_kind":"model_default","source_ref":"none","source_span":"not specified for Figure 3","reason":"Registered default inherited.","sensitivity_checked":false},{"field":"dort_streams","value":"32","source_kind":"model_default","source_ref":"none","source_span":"not specified for Figure 3","reason":"Registered default inherited.","sensitivity_checked":false},{"field":"corr_length_m","value":"0.00015","source_kind":"model_default","source_ref":"none","source_span":"not specified for Figure 3","reason":"Registered model value inserted during parameter resolution.","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"assumption","source_ref":"none","source_span":"density sweep","reason":"Density was selected as the independent variable for the reproduction chart.","sensitivity_checked":false},{"field":"sweep_start","value":"1.0","source_kind":"assumption","source_ref":"none","source_span":"40 points over density_kg_m3","reason":"Executable lower bound of the recorded sweep.","sensitivity_checked":false},{"field":"sweep_stop","value":"100.0","source_kind":"assumption","source_ref":"none","source_span":"40 points over density_kg_m3","reason":"Recorded upper bound of the sweep.","sensitivity_checked":false},{"field":"sweep_points","value":"40","source_kind":"assumption","source_ref":"none","source_span":"40 points over density_kg_m3","reason":"Recorded point count for each approved run.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | radius_m | 0.0001 | paper_explicit | smrt-v1#fig03 |
| smrt | density_kg_m3 | sweep 1–100 | backend_default | smrt-v1#fig03 |
| smrt | output | coefficients | paper_explicit | smrt-v1#fig03 |
| smrt | electromagnetic_model | rayleigh | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | independent_sphere | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | dmrt_qcacp_shortrange | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | non_sticky_hard_spheres | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | iba | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | sticky_hard_spheres | user_specified | smrt-v1#fig03 |
| smrt | stickiness | 0.2 | backend_default | - |
| smrt | frequency_ghz | 37 | backend_default | - |
| smrt | angle_deg | 55 | backend_default | - |
| smrt | temperature_k | 265 | backend_default | - |
| smrt | thickness_m | 1 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | sweep_parameter | density_kg_m3 | model_assumption | - |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | model_assumption | - |
| smrt | sweep_points | 40 | model_assumption | - |
