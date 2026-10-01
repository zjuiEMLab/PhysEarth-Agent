# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 provides a successful **qualitative reproduction** of the target comparison. It contains the same six scattering-coefficient curves, common density axis, units, and qualitative grouping shown in the inspected source figure: all curves increase with density, while the model configurations diverge in their predicted \(k_s\) values. [figure:smrt-v1#fig03] [smrt-v1#08]

The source/generated image supports qualitative correspondence, not digitized numerical agreement. All six approved runs completed successfully, the chart rendered with six 40-point series, and visual review passed after publication-layout redrawing. [model:smrt@1.5.1]

## Supporting results

### Conclusion supported by the source and generated images

The generated figure shows:

- six series;
- density on the x-axis in kg m⁻³;
- scattering coefficient \(k_s\) on the y-axis in m⁻¹;
- increasing curves across the plotted density range;
- divergence between electromagnetic and microstructure configurations at higher density;
- sticky-hard-sphere and non-sticky-hard-sphere configurations occupying distinct groups.

The image was not digitized, so it cannot establish point-by-point numerical agreement with the paper figure. [figure:smrt-v1#fig03]

### Conclusion supported by the result handles and arrays

The six model arrays each contain 40 density points from 1 to 100 kg m⁻³. All six \(k_s\) series are monotonic increasing. At the upper sweep endpoint of 100 kg m⁻³, the recorded \(k_s\) values range from 0.00642 to 0.0189 m⁻¹:

- Rayleigh + independent spheres: 0.0140 m⁻¹
- IBA + independent spheres: 0.0134 m⁻¹
- DMRT-QCA-CP + non-sticky hard spheres: 0.00725 m⁻¹
- IBA + non-sticky hard spheres: 0.00642 m⁻¹
- DMRT-QCA-CP + sticky hard spheres: 0.0189 m⁻¹
- IBA + sticky hard spheres: 0.0165 m⁻¹

These values are model outputs, not measurements or digitized paper values. [model:smrt@1.5.1]

### Image-to-array comparison

| Aspect | Source/generated image | Recorded arrays | Assessment |
|---|---|---|---|
| Number of curves | Six | Six | Agreement |
| Axis and units | Density in kg m⁻³; \(k_s\) in m⁻¹ | Same | Agreement |
| Trend | Curves increase with density | All six are monotonic increasing | Agreement |
| Configuration separation | Visible divergence and ordering | Endpoint range 0.00642–0.0189 m⁻¹ | Agreement |
| Quantitative curve agreement | Not digitized | Model values available only for the new runs | Not scoreable |
| Validation statistics | None supplied | No measurement comparison performed | N/A |

The visual review establishes the same qualitative pattern. It does not establish exact numerical agreement, because the paper image was not converted into reference data.

## Assumed parameters

The following values are guessed, assumed, inferred, or supplied by model defaults rather than being paper-explicit. The paper-inferred, model-assumption, and backend-default provenance classes are retained exactly as recorded.

- `density_kg_m3 = [1, 100]`: **backend_default**; the paper comparison context was [0, 100], but the submitted experiment used 1–100 kg m⁻³.
- `frequency_ghz = 37`: **paper_inferred**, based on the inherited comparison configuration. [smrt-v1#07]
- `stickiness = 0.2`: **model_assumption**; required implementation choice for sticky-hard-sphere runs, not a paper value. [smrt-v1#08]
- `temperature_k = 265`, `thickness_m = 1`, `angle_deg = 55`, and `dort_streams = 32`: **backend_default**.
- `electromagnetic_model`, `microstructure_model`, and `output`: **model_assumption** for the submitted configurations.
- `corr_length_m = 0.00015`: **backend_default** and not paper evidence.
- `sweep_parameter = density_kg_m3`, `sweep_start = 1.0`, `sweep_stop = 100.0`, and `sweep_points = 40`: **model_assumption** for the submitted sweep.
- `radius_m = 0.0001`: **paper_explicit**, obtained by converting 100 micrometres. [smrt-v1#fig03]

## Limitations

This was a qualitative reproduction of the source figure, not a quantitative digitized reproduction. No measured dataset or digitized paper curve was used, so bias, RMSE, correlation, and percent-error statistics are not available. The density range differs from the paper comparison context, and several fixed parameters were defaults or implementation assumptions. The conclusions therefore apply to the approved SMRT v1.5.1 configurations and should not be interpreted as observational validation. [model:smrt@1.5.1]

The calibrated outcome is **reproduced** in the qualitative, visually reviewed sense: the required curves were rendered, all runs passed, and the reviewed figure showed the same qualitative comparison pattern. [figure:smrt-v1#fig03]

<parameter_provenance>
[
  {"field":"radius_m","value":0.0001,"source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"100 micrometres","reason":"Direct conversion from 100 micrometres.","sensitivity_checked":false},
  {"field":"density_kg_m3","value":[1,100],"source_kind":"model_default","source_ref":"approved run state","source_span":"","reason":"Submitted sweep differs from the paper comparison context [0,100].","sensitivity_checked":false},
  {"field":"frequency_ghz","value":37,"source_kind":"derived","source_ref":"smrt-v1#07","source_span":"inherited paper comparison configuration","reason":"Paper-inferred frequency used for the approved comparison.","sensitivity_checked":false},
  {"field":"stickiness","value":0.2,"source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"Required implementation choice for sticky-hard-sphere runs; not claimed as a paper value.","sensitivity_checked":false},
  {"field":"temperature_k","value":265,"source_kind":"model_default","source_ref":"registered SMRT default","source_span":"","reason":"Registered default.","sensitivity_checked":false},
  {"field":"thickness_m","value":1,"source_kind":"model_default","source_ref":"registered SMRT default","source_span":"","reason":"Registered default.","sensitivity_checked":false},
  {"field":"angle_deg","value":55,"source_kind":"model_default","source_ref":"registered SMRT default","source_span":"","reason":"Registered default.","sensitivity_checked":false},
  {"field":"dort_streams","value":32,"source_kind":"model_default","source_ref":"registered SMRT default","source_span":"","reason":"Registered default.","sensitivity_checked":false},
  {"field":"electromagnetic_model","value":["rayleigh","iba","dmrt_qcacp_shortrange","iba","dmrt_qcacp_shortrange","iba"],"source_kind":"assumption","source_ref":"approved run state","source_span":"","reason":"Approved model configurations; not independently paper-explicit in the ledger.","sensitivity_checked":false},
  {"field":"microstructure_model","value":["independent_sphere","independent_sphere","non_sticky_hard_spheres","non_sticky_hard_spheres","sticky_hard_spheres","sticky_hard_spheres"],"source_kind":"assumption","source_ref":"approved run state","source_span":"","reason":"Approved microstructure configurations; not independently paper-explicit in the ledger.","sensitivity_checked":false},
  {"field":"output","value":"coefficients","source_kind":"assumption","source_ref":"approved run state","source_span":"","reason":"Selected to produce ks_per_m for the target chart.","sensitivity_checked":false},
  {"field":"corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered SMRT default","source_span":"","reason":"Inserted during parameter resolution; not paper evidence.","sensitivity_checked":false},
  {"field":"sweep_parameter","value":"density_kg_m3","source_kind":"assumption","source_ref":"approved run state","source_span":"","reason":"Approved chart uses density as the sweep axis.","sensitivity_checked":false},
  {"field":"sweep_start","value":1.0,"source_kind":"assumption","source_ref":"approved run state","source_span":"","reason":"Approved sweep lower bound.","sensitivity_checked":false},
  {"field":"sweep_stop","value":100.0,"source_kind":"assumption","source_ref":"approved run state","source_span":"","reason":"Approved sweep upper bound.","sensitivity_checked":false},
  {"field":"sweep_points","value":40,"source_kind":"assumption","source_ref":"approved run state","source_span":"","reason":"Approved number of points per run.","sensitivity_checked":false}
]
</parameter_provenance>
<reproduction_outcome>reproduced</reproduction_outcome>
