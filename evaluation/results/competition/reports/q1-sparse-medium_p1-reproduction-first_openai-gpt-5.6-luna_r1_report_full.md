# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 shows six scattering-coefficient curves that increase with snow density from 1 to \(100\ \mathrm{kg\,m^{-3}}\). The curves separate according to electromagnetic formulation and microstructure: sticky-hard-sphere cases are highest at the upper end, while non-sticky-hard-sphere cases are lowest. Compared with the inspected source Figure 3, this is the same qualitative pattern, so the reproduction is qualitatively successful. [figure:smrt-v1#fig03] [model:smrt@1.5.1]

The comparison is qualitative rather than a digitized numerical validation. No required curves were missing, all seven approved model runs completed successfully, and the generated figure rendered six series over the requested range.

## Conclusion supported by the source image

The source image and generated figure both present scattering coefficient \(k_s\) as a function of density, with increasing curves and separation among the model/microstructure combinations. The source image supports the curve count, axes, units, grouping, ordering, and qualitative shape; it does not provide digitized values. [figure:smrt-v1#fig03]

## Conclusion supported by model results

The recorded arrays show monotonic increases in \(k_s\) for every plotted series. At \(100\ \mathrm{kg\,m^{-3}}\), the computed values were:

| Configuration | \(k_s\) (\(\mathrm{m^{-1}}\)) |
|---|---:|
| Rayleigh + independent spheres | 0.013981 |
| IBA + independent spheres | 0.013428 |
| DMRT QCA-CP + non-sticky hard spheres | 0.007255 |
| IBA + non-sticky hard spheres | 0.006418 |
| DMRT QCA-CP + sticky hard spheres | 0.018853 |
| IBA + sticky hard spheres | 0.016544 |

These are model outputs, not observations. [model:smrt@1.5.1]

## Comparison of image and result conclusions

| Aspect | Source/generated image conclusion | Array-supported conclusion | Assessment |
|---|---|---|---|
| Trend | Curves rise with density | Every series is monotonically increasing | Agreement |
| Curve grouping | Microstructure and formulation produce separated curves | Sticky-hard-sphere values are highest at the upper endpoint; non-sticky values are lowest | Agreement |
| Numerical agreement | Not available from the image alone | Endpoint values are available from model arrays | Source-to-model numerical agreement is not scoreable |
| Figure usability | Six curves, common axes and units are visible | Six 60-point series were plotted | The render check confirms legibility only, not source-figure agreement |

## Assumed and guessed parameters

The following retained the authoritative provenance classes: `model_assumption` values were not supported by paper or user evidence; `backend_default` values came from registered model defaults; and `user_specified` values were chosen for the submitted experiment. The paper explicitly identifies the coefficient observable and the radius mapping, but the ledger records no paper value for either.

The formal chart used density \(1\)–\(100\ \mathrm{kg\,m^{-3}}\), six model/microstructure combinations, and 60 points per sweep. The baseline run additionally used the recorded single-point configuration with IBA and independent spheres. [model:smrt@1.5.1]

## Limitations

The source figure was not digitized, so numerical bias, RMSE, correlation, and percent-error comparisons are not available. The submitted density range differs from the paper condition, and several physical settings were retained as model defaults or assumptions rather than taken from the paper. The render check established that the generated arrays were finite, dense, and legible; it was not evidence that the generated figure numerically matches the source.

<parameter_provenance>
[
  {"field":"radius_m","value":0.0001,"source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"Direct figure-caption mapping","reason":"Direct figure-caption mapping.","sensitivity_checked":false},
  {"field":"density_kg_m3","value":[1,100],"source_kind":"user","source_ref":"user-approved research plan","reason":"The submitted experiment differs from the paper condition; the paper value remains comparison context.","sensitivity_checked":false},
  {"field":"output","value":"coefficients","source_kind":"paper","source_ref":"smrt-v1#08","source_span":"Coefficient output returns ks_per_m","reason":"Coefficient output returns ks_per_m.","sensitivity_checked":false},
  {"field":"frequency_ghz","value":37,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Registered default retained.","sensitivity_checked":false},
  {"field":"temperature_k","value":265,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Registered default retained.","sensitivity_checked":false},
  {"field":"thickness_m","value":1,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Registered default retained.","sensitivity_checked":false},
  {"field":"angle_deg","value":55,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Registered default retained.","sensitivity_checked":false},
  {"field":"dort_streams","value":32,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Registered default retained.","sensitivity_checked":false},
  {"field":"stickiness","value":0.2,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Registered default retained; not paper evidence.","sensitivity_checked":false},
  {"field":"electromagnetic_model","value":"iba","source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence; it was to be confirmed during plan review.","sensitivity_checked":false},
  {"field":"microstructure_model","value":"independent_sphere","source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence; it was to be confirmed during plan review.","sensitivity_checked":false},
  {"field":"corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},
  {"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"registered SMRT default","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},
  {"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},
  {"field":"sweep_start","value":1.0,"source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence; it was to be confirmed during plan review.","sensitivity_checked":false},
  {"field":"sweep_stop","value":100.0,"source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence; it was to be confirmed during plan review.","sensitivity_checked":false}
]
</parameter_provenance>
<reproduction_outcome>reproduced</reproduction_outcome>
