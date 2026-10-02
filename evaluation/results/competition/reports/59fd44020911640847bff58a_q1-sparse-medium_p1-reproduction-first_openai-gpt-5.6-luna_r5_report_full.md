# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated six-curve figure shows a common qualitative pattern: scattering coefficient \(k_s\) increases with density from the legal execution range of **1–100 kg m⁻³**, while the curves increasingly diverge as density rises. The ordering depends on the electromagnetic formulation and microstructure; sticky-hard-sphere cases lie highest at the upper end, while non-sticky-hard-sphere cases lie lowest [figure:smrt-v1#fig03] [model:smrt@1.5.1].

This is therefore a **successful qualitative reproduction** of the source figure’s density-dependent scattering behavior, but not an exact quantitative reproduction. The origin was narrowed from the paper’s plotted 0 kg m⁻³ to 1 kg m⁻³ because 0 is outside the registered model range, and several required parameters were inherited defaults or assumptions [smrt-v1#08] [guideline:smrt@1.0].

## Conclusion supported by the source image

The inspected source figure and generated figure show the same broad scientific pattern:

- six theory/microstructure combinations;
- scattering coefficient on the vertical axis;
- density on the horizontal axis;
- convergence toward the sparse-density limit;
- increasing separation among formulations at higher density;
- formulation-dependent ordering of the curves [figure:smrt-v1#fig03].

The source image supports these qualitative comparisons only. It was not digitized, so it does not support a numerical curve-by-curve error assessment.

## Conclusion supported by the computed arrays

All six model runs completed successfully and produced 50-point, quality-controlled arrays over density 1–100 kg m⁻³ [model:smrt@1.5.1].

At 100 kg m⁻³, the computed \(k_s\) values were:

| Configuration | \(k_s\) (m⁻¹) |
|---|---:|
| Rayleigh + independent spheres | 0.01398 |
| IBA + independent spheres | 0.01343 |
| DMRT-QCA-CP + non-sticky hard spheres | 0.00725 |
| IBA + non-sticky hard spheres | 0.00642 |
| DMRT-QCA-CP + sticky hard spheres | 0.01885 |
| IBA + sticky hard spheres | 0.01654 |

The arrays show monotonic increases for all six configurations. Numerical comparison against the paper’s plotted curves is **not scoreable**, because no digitized source data were supplied [model:smrt@1.5.1].

## Comparison of source-image and generated-figure conclusions

| Aspect | Source image | Generated figure and arrays | Assessment |
|---|---|---|---|
| Number of curves | Six | Six | Agreement |
| Axes and quantity | Density versus scattering coefficient | Density versus \(k_s\) | Agreement |
| Density behavior | Increasing with density | Increasing over 1–100 kg m⁻³ | Same qualitative pattern |
| Sparse-density behavior | Curves approach one another | Curves begin near one another | Same qualitative pattern |
| High-density behavior | Curves separate and reorder by formulation | Curves separate, with sticky-hard-sphere cases highest and non-sticky cases lowest at the endpoint | Qualitative correspondence |
| Numeric agreement | Not digitized | Not scoreable | No quantitative claim |

The automatic render check passed and confirmed that the six plotted arrays were finite, sufficiently sampled, and legible. That check establishes figure usability only; it does not establish agreement with the source image.

## Assumed parameters

The following values were not paper-explicit and are treated as guessed or assumed parameters:

- `sweep_start = 1` kg m⁻³: nearest legal approximation to the paper origin.
- `stickiness = 0.2`: registered backend default; no paper value was available.
- `frequency_ghz = 37`: registered backend default.
- `temperature_k = 265`: registered backend default.
- `electromagnetic_model = rayleigh`: model assumption for the retained run.
- `microstructure_model = independent_sphere`: model assumption for the retained run.
- `output = coefficients`: model assumption selecting \(k_s\).
- `angle_deg = 55.0`: registered backend default.
- `thickness_m = 1.0`: registered backend default.
- `density_kg_m3 = 300.0`: registered backend default retained in the resolved specification while density was swept.
- `corr_length_m = 0.00015`: registered backend default.
- `dort_streams = 32`: registered backend default.
- `sweep_points = 50`: model assumption for the plotted sweep.

The paper-explicit or paper-mapped values were `radius_m = 0.0001` m, `sweep_parameter = density_kg_m3`, and `sweep_stop = 100` kg m⁻³ [figure:smrt-v1#fig03].

## Limitations

This reproduction evaluates qualitative curve behavior rather than observational accuracy. It does not provide digitized paper values, a numerical source-figure error metric, or a measurement comparison. The use of backend defaults for frequency, temperature, stickiness, and other parameters prevents an exact quantitative reproduction claim.

The direct answer is: **the generated figure reproduces the source figure’s qualitative density trend and model-dependent divergence over approximately 1–100 kg m⁻³, but numerical agreement is not identifiable from the available evidence.**

<parameter_provenance>
[{"field":"radius_m","value":0.0001,"source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"100 micrometres","reason":"Use the caption value exactly.","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"plotted 0–100 kg m-3","reason":"Use density as the plotted independent variable; execution starts at 1 kg m-3 because density 0 is outside the registered model range.","sensitivity_checked":false},{"field":"sweep_start","value":1,"source_kind":"assumption","source_ref":"smrt-v1#fig03; registered model legal range","reason":"Nearest legal approximation to the paper origin; not paper-exact.","sensitivity_checked":false},{"field":"sweep_stop","value":100,"source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"plotted upper limit 100 kg m-3","reason":"Matches the plotted upper limit.","sensitivity_checked":false},{"field":"stickiness","value":0.2,"source_kind":"model_default","source_ref":"smrt-v1#08; registered SMRT default","reason":"Inherited registered default solely to make sticky-hard-sphere runs executable; no paper value was available.","sensitivity_checked":false},{"field":"frequency_ghz","value":37,"source_kind":"model_default","source_ref":"smrt-v1#fig03; registered SMRT default","reason":"Inherited registered default; coefficient dependence makes this an implementation assumption.","sensitivity_checked":false},{"field":"temperature_k","value":265,"source_kind":"model_default","source_ref":"smrt-v1#fig03; registered SMRT default","reason":"Inherited registered default.","sensitivity_checked":false},{"field":"electromagnetic_model","value":"rayleigh","source_kind":"assumption","source_ref":"approved run specification; no paper evidence attached","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"microstructure_model","value":"independent_sphere","source_kind":"assumption","source_ref":"approved run specification; no paper evidence attached","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"output","value":"coefficients","source_kind":"assumption","source_ref":"approved run specification; no paper evidence attached","reason":"The submitted run retained this value to produce the scattering coefficient output.","sensitivity_checked":false},{"field":"angle_deg","value":55.0,"source_kind":"model_default","source_ref":"registered SMRT default; no paper evidence attached","reason":"Inserted by the registered model during parameter resolution.","sensitivity_checked":false},{"field":"thickness_m","value":1.0,"source_kind":"model_default","source_ref":"registered SMRT default; no paper evidence attached","reason":"Inserted by the registered model during parameter resolution.","sensitivity_checked":false},{"field":"density_kg_m3","value":300.0,"source_kind":"model_default","source_ref":"registered SMRT default; no paper evidence attached","reason":"Inserted as the baseline density in the resolved specification while density was swept.","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered SMRT default; no paper evidence attached","reason":"Inserted by the registered model during parameter resolution.","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"model_default","source_ref":"registered SMRT default; no paper evidence attached","reason":"Inserted by the registered model during parameter resolution.","sensitivity_checked":false},{"field":"sweep_points","value":50,"source_kind":"assumption","source_ref":"approved run specification; no paper evidence attached","reason":"Retained to generate the approved 50-point density sweep.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>reproduced</reproduction_outcome>
