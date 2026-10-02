# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure shows six scattering-coefficient curves over density 1–100 kg m⁻³. All curves increase with density, while their separation depends on the electromagnetic and microstructure formulation. The generated curves reproduce the source figure’s qualitative structure and density-dependent pattern, so the qualitative reproduction is successful. Quantitative agreement with the source is not scoreable because the source curves were not digitized. [smrt-v1#08] [figure:smrt-v1#fig03] [model:smrt@1.5.1]

The calibrated outcome is therefore **partial**: all required model curves were generated and rendered, but numerical source-figure validation remains unavailable.

## Supporting results

### Conclusion supported by the source image

The source image contains six coefficient curves plotted against density, with density as the independent variable and scattering coefficient in m⁻¹ as the ordinate. The figure supports comparison of curve count, grouping, visible separation, ordering, and qualitative shape, but it does not provide digitized values for numerical validation. [figure:smrt-v1#fig03]

### Conclusion supported by the generated arrays

All six approved runs completed successfully and passed model quality control. Each generated \(k_s\) series increased monotonically over the density sweep. At 100 kg m⁻³, the modeled scattering coefficients ranged from 0.00642 to 0.01885 m⁻¹ across the six configurations. [model:smrt@1.5.1]

The smallest upper-bound value was produced by IBA with non-sticky hard spheres; the largest was produced by DMRT with sticky hard spheres. These are differences between model formulations, not model–measurement residuals. [model:smrt@1.5.1]

### Comparison

| Aspect | Source image | Generated figure and arrays | Assessment |
|---|---|---|---|
| Curves | Six density-dependent coefficient curves | Six \(k_s\) curves | Same qualitative target |
| x-axis | Density, approximately 0–100 kg m⁻³ | Density, 1–100 kg m⁻³ | Comparable; lower bound shifted to the nearest legal model value |
| y-axis | Scattering coefficient | Scattering coefficient, m⁻¹ | Same quantity |
| Trend | Density-dependent separated curves | All six curves increase monotonically | Same qualitative pattern |
| Numerical agreement | Not digitized | Model values available | Not scoreable |
| Rendering | Source figure inspected | Generated chart rendered and found legible | Usable figure; this does not establish source agreement |

The main qualification is parameter provenance: the electromagnetic and microstructure configurations were user-specified, while several other values were backend defaults or model assumptions rather than paper-explicit conditions. The source figure therefore supports a qualitative reproduction claim, not a deterministic numerical match. [smrt-v1#08] [figure:smrt-v1#fig03]

## Assumed parameters

The following values were not all paper-explicit. The density lower bound was inferred from the plotted zero and changed to 1 kg m⁻³ because that was the nearest legal model value. Stickiness, frequency, angle, thickness, temperature, correlation length, DORT streams, and baseline density were backend defaults. The 60-point sampling was a model assumption. The six electromagnetic/microstructure combinations were user-specified for the submitted experiment. [model:smrt@1.5.1]

## Limitations

The source figure was not digitized, so bias, RMSE, correlation, percent error, and pointwise numerical agreement with the paper are **not scoreable**. The passed render check establishes that the generated arrays were finite, sufficiently sampled, and legible; it does not establish visual or numerical agreement with the source. [smrt-v1#08] [figure:smrt-v1#fig03]

<parameter_provenance>
[{"field":"radius_m","value":0.0001,"source_kind":"paper","source_ref":"smrt-v1#08","source_span":"100 micrometre spheres","reason":"Sphere radius used in the approved runs.","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"derived","source_ref":"smrt-v1#fig03","source_span":"Density is the plotted independent variable","reason":"Density was inferred as the independent variable of the source figure.","sensitivity_checked":false},{"field":"sweep_start","value":1,"source_kind":"derived","source_ref":"smrt-v1#fig03","source_span":"plotted range begins at approximately zero","reason":"Nearest legal model value to the plotted zero.","sensitivity_checked":false},{"field":"sweep_stop","value":100,"source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"end of plotted range at 100","reason":"Upper end of the approved density sweep.","sensitivity_checked":false},{"field":"output","value":"coefficients","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"scattering coefficient","reason":"The approved output was ks_per_m.","sensitivity_checked":false},{"field":"stickiness","value":0.2,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Required to execute the sticky-hard-sphere configurations; no paper value was supplied.","sensitivity_checked":false},{"field":"electromagnetic_model","value":{"r1":"rayleigh","r2":"iba","r3":"dmrt_qcacp_shortrange","r4":"iba","r5":"dmrt_qcacp_shortrange","r6":"iba"},"source_kind":"user","source_ref":"approved research plan","reason":"The six submitted electromagnetic configurations were user-specified for the reproduction experiment.","sensitivity_checked":false},{"field":"microstructure_model","value":{"r1":"independent_sphere","r2":"independent_sphere","r3":"non_sticky_hard_spheres","r4":"non_sticky_hard_spheres","r5":"sticky_hard_spheres","r6":"sticky_hard_spheres"},"source_kind":"user","source_ref":"approved research plan","reason":"The six submitted microstructure configurations were user-specified for the reproduction experiment.","sensitivity_checked":false},{"field":"frequency_ghz","value":37.0,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Inserted during parameter resolution; not paper evidence.","sensitivity_checked":false},{"field":"angle_deg","value":55.0,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Inserted during parameter resolution; not paper evidence.","sensitivity_checked":false},{"field":"thickness_m","value":1.0,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Inserted during parameter resolution; not paper evidence.","sensitivity_checked":false},{"field":"density_kg_m3","value":300.0,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Baseline density retained during the density sweep; not paper evidence.","sensitivity_checked":false},{"field":"temperature_k","value":265.0,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Inserted during parameter resolution; not paper evidence.","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Retained during the approved sphere-based runs; not paper evidence.","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Numerical-stream default retained in the approved runs.","sensitivity_checked":false},{"field":"sweep_points","value":60,"source_kind":"assumption","source_ref":"approved research plan","reason":"The submitted run retained 60 points without attached paper or user evidence.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
