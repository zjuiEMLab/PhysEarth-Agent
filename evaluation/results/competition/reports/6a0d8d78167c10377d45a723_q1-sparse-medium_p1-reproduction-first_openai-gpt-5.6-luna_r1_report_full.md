# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 shows six scattering-coefficient curves increasing with snow density from 1 to 100 kg m⁻³. The curves remain ordered and visibly separated at higher density: sticky-hard-sphere configurations are highest, non-sticky hard-sphere configurations are lowest, and independent-sphere cases lie between them. This is the same qualitative pattern as the inspected source figure, so the approved target is a **qualitative reproduction** [figure:smrt-v1#fig03] [model:smrt@1.5.1].

The reproduction is not a numerical curve match: the submitted experiment begins at 1 kg m⁻³ rather than the source origin at 0 kg m⁻³, uses 20 display points, and retains several backend defaults rather than paper-specified conditions.

## Supporting results

### Conclusion supported by the source and generated images

Both images support the following qualitative conclusions:

- six model combinations are compared;
- the x-axis is density and the y-axis is scattering coefficient \(k_s\);
- all curves increase with density;
- the curves separate progressively toward higher density;
- sticky, non-sticky, and independent-sphere groupings have distinct orderings [smrt-v1#fig03] [figure:smrt-v1#fig03].

The generated figure is therefore consistent with the source figure at the level of curve count, axes, units, grouping, trend, and qualitative ordering. The source image was not digitized, so it does not support a pointwise numerical error assessment.

### Conclusion supported by the recorded result arrays

All six runs passed model quality control. The recorded endpoint values at 100 kg m⁻³ were:

| Configuration | \(k_s\) at 100 kg m⁻³ (m⁻¹) |
|---|---:|
| DMRT QCA-CP + non-sticky hard spheres | 0.0072548 |
| IBA + non-sticky hard spheres | 0.0064180 |
| Rayleigh + independent spheres | 0.0139806 |
| IBA + independent spheres | 0.0134276 |
| IBA + sticky hard spheres | 0.0165438 |
| DMRT QCA-CP + sticky hard spheres | 0.0188528 |

Each curve was monotonic increasing over the recorded sweep. The plotted quantity was `ks_per_m`, with units of m⁻¹ [model:smrt@1.5.1].

## Comparison and qualifications

| Aspect | Source/generated image conclusion | Recorded-array conclusion |
|---|---|---|
| Trend | All curves increase with density | Confirmed for all six runs |
| Ordering | Sticky-hard-sphere curves appear highest and non-sticky hard-sphere curves lowest | Confirmed at the upper endpoint |
| Separation | Curves visibly diverge toward higher density | Confirmed by distinct endpoint values |
| Numerical agreement with source | Not scoreable; source curves were not digitized | Not scoreable |
| Rendering | Figure contains six legible series | Render check passed; this establishes legibility only, not source agreement |

The qualitative correspondence is successful, but exact numerical agreement is not identifiable from the available evidence. Differences may reflect the altered lower density bound, display sampling, registered-model version, and backend-default parameters rather than a contradiction of the source result.

## Guessed/assumed parameters

The following values were not paper-explicit: `output` was paper-inferred; `frequency_ghz`, `temperature_k`, `stickiness`, `thickness_m`, `angle_deg`, `corr_length_m`, and `dort_streams` were backend defaults; `sweep_parameter` and `sweep_points` were model assumptions. `density_kg_m3` and the three model-family selections were user-specified for this submitted experiment. The lower sweep bound of 1 kg m⁻³ was a paper-inferred legal approximation to the source axis origin. These choices limit direct numerical comparison with the paper.

## Limitations

The result addresses the approved qualitative Figure 3 reproduction only. No source-curve digitization, pointwise comparison, validation dataset, bias, RMSE, correlation, or parameter-sensitivity experiment was recorded. The render check confirms that the generated arrays were finite, sufficiently sampled, and legible; it does not establish that the generated curves numerically match the source.

The final conclusion is that the experiment successfully reproduces the **qualitative density dependence and ordering** of the six scattering-coefficient curves, while numerical agreement with the source remains not scoreable.

<parameter_provenance>
[{"field":"radius_m","value":0.0001,"provenance":"paper_explicit","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"sphere radius of 100 micrometres","reason":"Direct conversion of the paper caption value.","sensitivity_checked":false},{"field":"density_kg_m3","value":"1–100 kg m-3, 20 points","provenance":"user_specified","source_kind":"user","source_ref":"submitted experiment and approved run state","source_span":null,"reason":"The submitted experiment differs from the paper condition; the paper value remains comparison context.","sensitivity_checked":false},{"field":"output","value":"coefficients","provenance":"paper_inferred","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"scattering coefficient","reason":"Coefficient output exposes ks_per_m directly.","sensitivity_checked":false},{"field":"electromagnetic_model","value":["rayleigh","dmrt_qcacp_shortrange","iba"],"provenance":"user_specified","source_kind":"user","source_ref":"approved run state","source_span":null,"reason":"The submitted experiment differs from the paper condition; the paper value remains comparison context.","sensitivity_checked":false},{"field":"microstructure_model","value":["independent_sphere","non_sticky_hard_spheres","sticky_hard_spheres"],"provenance":"user_specified","source_kind":"user","source_ref":"approved run state","source_span":null,"reason":"The submitted experiment differs from the paper condition; the paper value remains comparison context.","sensitivity_checked":false},{"field":"frequency_ghz","value":37.0,"provenance":"backend_default","source_kind":"model_default","source_ref":"registered SMRT model default","source_span":null,"reason":"Backend default retained as an implementation choice, not paper evidence.","sensitivity_checked":false},{"field":"temperature_k","value":265.0,"provenance":"backend_default","source_kind":"model_default","source_ref":"registered SMRT model default","source_span":null,"reason":"Backend default retained as an implementation choice, not paper evidence.","sensitivity_checked":false},{"field":"stickiness","value":0.2,"provenance":"backend_default","source_kind":"model_default","source_ref":"registered SMRT model default","source_span":null,"reason":"Required for sticky-hard-sphere runs and explicitly treated as a backend default.","sensitivity_checked":false},{"field":"thickness_m","value":1.0,"provenance":"backend_default","source_kind":"model_default","source_ref":"registered SMRT model default","source_span":null,"reason":"Backend default retained; not interpreted as a paper condition.","sensitivity_checked":false},{"field":"angle_deg","value":55.0,"provenance":"backend_default","source_kind":"model_default","source_ref":"registered SMRT model default","source_span":null,"reason":"Backend default retained because the input is part of the registered declaration but is not a plotted source condition.","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"provenance":"backend_default","source_kind":"model_default","source_ref":"registered SMRT model default","source_span":null,"reason":"Backend default retained and not treated as paper evidence.","sensitivity_checked":false},{"field":"dort_streams","value":32,"provenance":"backend_default","source_kind":"model_default","source_ref":"registered SMRT model default","source_span":null,"reason":"Backend default retained and not treated as paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","provenance":"model_assumption","source_kind":"assumption","source_ref":"smrt-v1#fig03 and approved research plan","source_span":"density axis","reason":"Exact registered sweep input corresponding to the source x-axis.","sensitivity_checked":false},{"field":"sweep_start","value":1.0,"provenance":"paper_inferred","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"source axis starts at 0","reason":"Legal approximation to the source origin.","sensitivity_checked":false},{"field":"sweep_stop","value":100.0,"provenance":"paper_explicit","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"upper axis extent of 100 kg m-3","reason":"Matches the source upper axis extent.","sensitivity_checked":false},{"field":"sweep_points","value":20,"provenance":"model_assumption","source_ref":"approved research plan","source_kind":"assumption","source_span":null,"reason":"Display sampling choice, not paper evidence.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>reproduced</reproduction_outcome>
