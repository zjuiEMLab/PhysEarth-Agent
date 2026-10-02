# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show the expected qualitative ordering over 0.05–0.50 m³ m⁻³: passive brightness temperature decreases with soil moisture, while active backscatter increases. The two polarization curves remain ordered throughout the passive sweep, and the active soil and total-backscatter curves rise while vegetation backscatter remains constant. [model:tau_omega@1.0.0] [model:water_cloud@1.0.0]

This is a **partial qualitative reproduction**, not an exact reproduction of the cited studies. CMEM and the paper’s calibrated Water Cloud Model were unavailable or unrun, so the generated figures are local `tau_omega` and `water_cloud` proxy results.

## Supporting results

### Conclusion supported by the generated figures

- **Figure 1** uses soil moisture on the x-axis and brightness temperature in K on the y-axis, with two curves: \(T_b^H\) and \(T_b^V\).
- Both passive curves slope downward as soil moisture increases.
- The V-polarized curve remains above the H-polarized curve across the plotted range.
- **Figure 2** uses soil moisture on the x-axis and backscatter in dB on the y-axis, with soil, total, and vegetation contributions.
- Soil and total backscatter increase with soil moisture.
- The vegetation-backscatter curve is horizontal because vegetation parameters were fixed.

The figures rendered successfully and passed the automated legibility check. That check establishes that the plotted arrays are usable; it does not establish agreement with a source figure.

### Conclusion supported by the recorded result arrays

The passive sweep produced:

- \(T_b^H\): 248.1286 K at 0.05 m³ m⁻³, decreasing to 214.7619 K at 0.50 m³ m⁻³.
- \(T_b^V\): 268.9662 K at 0.05 m³ m⁻³, decreasing to 234.5853 K at 0.50 m³ m⁻³.

The active sweep produced:

- Total backscatter: \(-15.9764\) dB at 0.05 m³ m⁻³, increasing to \(-7.7886\) dB at 0.50 m³ m⁻³.
- Soil backscatter: \(-20.5000\) to \(-7.0000\) dB over the same range.
- Vegetation backscatter: constant at \(-17.2917\) dB.

All four approved model runs completed successfully with quality control passed. [model:tau_omega@1.0.0] [model:water_cloud@1.0.0]

### Comparison and qualification

| Aspect | Generated-figure conclusion | Result-array conclusion | Assessment |
|---|---|---|---|
| Passive response | Both curves decrease | Both arrays decrease monotonically | Agreement |
| Passive ordering | V remains above H | V exceeds H at the reported sweep endpoints and intermediate values | Agreement |
| Active response | Soil and total curves rise | Both arrays increase monotonically | Agreement |
| Vegetation contribution | Horizontal curve | Constant at \(-17.2917\) dB | Agreement |
| Source-figure comparison | No source-image inspection is recorded for these local figures | Numerical proxy results only | Not scoreable |
| Exact paper reproduction | Not established visually or numerically | CMEM and the calibrated paper Water Cloud Model were unavailable or unrun | Partial outcome |

The qualitative conclusions are supported by both the plotted curves and the recorded arrays. Numerical agreement with the papers is not identifiable because the approved local models are not the unavailable reference implementations. [paper:cmem-sampling-density#03] [paper:backscatter-forward-operator#05]

## Assumed parameters

The L-band frequency, passive and active incidence angles, material properties, temperatures, vegetation properties, roughness, and active-model coefficients were model assumptions rather than paper-explicit values. The soil-moisture range was the user-specified primary sweep. Baseline and sweep controls were resolved using the registered model defaults and approved run settings. [model:tau_omega@1.0.0] [model:water_cloud@1.0.0]

## Limitations

The figures do not reproduce CMEM or the paper-calibrated Water Cloud Model. No measured reference dataset was used in these runs, and no source-image digitization or numerical source-curve comparison was performed. Therefore, bias, RMSE, correlation, and percentage-error statistics are N/A. The outcome is limited to a qualitative local-model sensitivity result.

<parameter_provenance>
[
  {"field":"tau_baseline.frequency_ghz","value":1.41,"source_kind":"assumption","source_ref":"cmem-sampling-density#03","reason":"Use the registered tau_omega L-band operating point for the local proxy.","sensitivity_checked":false},
  {"field":"tau_baseline.angle_deg","value":40,"source_kind":"assumption","source_ref":"cmem-sampling-density#03","reason":"Fixed geometry for the local sensitivity experiment.","sensitivity_checked":false},
  {"field":"tau_baseline.soil_moisture","value":0.25,"source_kind":"user","source_ref":"approved research plan v001","reason":"Baseline control value; the primary sweep varies this parameter.","sensitivity_checked":true},
  {"field":"tau_baseline.bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed substrate property.","sensitivity_checked":false},
  {"field":"tau_baseline.soil_temperature_k","value":293,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed thermal condition.","sensitivity_checked":false},
  {"field":"tau_baseline.canopy_temperature_k","value":293,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed thermal condition.","sensitivity_checked":false},
  {"field":"tau_baseline.vegetation_optical_depth","value":0.3,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed vegetation attenuation.","sensitivity_checked":false},
  {"field":"tau_baseline.single_scattering_albedo","value":0.05,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed canopy scattering condition.","sensitivity_checked":false},
  {"field":"tau_baseline.roughness_h","value":0.3,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed roughness condition.","sensitivity_checked":false},
  {"field":"tau_baseline.cross_q","value":0,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed polarisation-mixing condition.","sensitivity_checked":false},
  {"field":"tau_baseline.sweep_parameter","value":"none","source_kind":"model_default","source_ref":"registered tau_omega parameter resolution","reason":"Baseline holds the control fixed.","sensitivity_checked":false},
  {"field":"tau_baseline.sweep_points","value":10,"source_kind":"model_default","source_ref":"registered tau_omega parameter resolution","reason":"Registered default; inactive because sweep_parameter is none.","sensitivity_checked":false},

  {"field":"tau_sweep.frequency_ghz","value":1.41,"source_kind":"assumption","source_ref":"cmem-sampling-density#03","reason":"Use the registered tau_omega L-band operating point for the local proxy.","sensitivity_checked":false},
  {"field":"tau_sweep.angle_deg","value":40,"source_kind":"assumption","source_ref":"cmem-sampling-density#03","reason":"Fixed geometry for the local sensitivity experiment.","sensitivity_checked":false},
  {"field":"tau_sweep.soil_moisture","value":"0.05-0.50","source_kind":"user","source_ref":"approved research plan v001","reason":"Primary sweep variable.","sensitivity_checked":true},
  {"field":"tau_sweep.bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed substrate property.","sensitivity_checked":false},
  {"field":"tau_sweep.soil_temperature_k","value":293,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed thermal condition.","sensitivity_checked":false},
  {"field":"tau_sweep.canopy_temperature_k","value":293,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed thermal condition.","sensitivity_checked":false},
  {"field":"tau_sweep.vegetation_optical_depth","value":0.3,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed vegetation attenuation.","sensitivity_checked":false},
  {"field":"tau_sweep.single_scattering_albedo","value":0.05,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed canopy scattering condition.","sensitivity_checked":false},
  {"field":"tau_sweep.roughness_h","value":0.3,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed roughness condition.","sensitivity_checked":false},
  {"field":"tau_sweep.cross_q","value":0,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed polarisation-mixing condition.","sensitivity_checked":false},
  {"field":"tau_sweep.sweep_parameter","value":"soil_moisture","source_kind":"model_default","source_ref":"registered tau_omega parameter resolution","reason":"Main run sweeps soil moisture.","sensitivity_checked":true},
  {"field":"tau_sweep.sweep_start","value":0.05,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Submitted sweep lower bound without paper-derived evidence.","sensitivity_checked":true},
  {"field":"tau_sweep.sweep_stop","value":0.5,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Submitted sweep upper bound without paper-derived evidence.","sensitivity_checked":true},
  {"field":"tau_sweep.sweep_points","value":20,"source_kind":"unknown","source_ref":"recorded formal run state; provenance not assigned in the ledger","reason":"Actual executed sweep resolution.","sensitivity_checked":false},

  {"field":"wc_baseline.angle_deg","value":37,"source_kind":"assumption","source_ref":"backscatter-forward-operator#05","reason":"Fixed geometry for the local active sensitivity experiment.","sensitivity_checked":false},
  {"field":"wc_baseline.soil_moisture","value":0.25,"source_kind":"user","source_ref":"approved research plan v001","reason":"Baseline control value; the primary sweep varies this parameter.","sensitivity_checked":true},
  {"field":"wc_baseline.vegetation_water_kg_m2","value":1.0,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed canopy water condition.","sensitivity_checked":false},
  {"field":"wc_baseline.coefficient_a","value":0.09,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed local-model scattering coefficient.","sensitivity_checked":false},
  {"field":"wc_baseline.coefficient_b","value":0.12,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed local-model attenuation coefficient.","sensitivity_checked":false},
  {"field":"wc_baseline.coefficient_c","value":-22,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed local-model soil intercept.","sensitivity_checked":false},
  {"field":"wc_baseline.coefficient_d","value":30,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed local-model soil-moisture coefficient.","sensitivity_checked":false},
  {"field":"wc_baseline.sweep_parameter","value":"none","source_kind":"model_default","source_ref":"registered water_cloud parameter resolution","reason":"Baseline holds the control fixed.","sensitivity_checked":false},
  {"field":"wc_baseline.sweep_points","value":10,"source_kind":"model_default","source_ref":"registered water_cloud parameter resolution","reason":"Registered default; inactive because sweep_parameter is none.","sensitivity_checked":false},

  {"field":"wc_sweep.angle_deg","value":37,"source_kind":"assumption","source_ref":"backscatter-forward-operator#05","reason":"Fixed geometry for the local active sensitivity experiment.","sensitivity_checked":false},
  {"field":"wc_sweep.soil_moisture","value":"0.05-0.50","source_kind":"user","source_ref":"backscatter-forward-operator#05","reason":"Primary sweep variable.","sensitivity_checked":true},
  {"field":"wc_sweep.vegetation_water_kg_m2","value":1.0,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed canopy water condition.","sensitivity_checked":false},
  {"field":"wc_sweep.coefficient_a","value":0.09,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed local-model scattering coefficient.","sensitivity_checked":false},
  {"field":"wc_sweep.coefficient_b","value":0.12,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed local-model attenuation coefficient.","sensitivity_checked":false},
  {"field":"wc_sweep.coefficient_c","value":-22,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed local-model soil intercept.","sensitivity_checked":false},
  {"field":"wc_sweep.coefficient_d","value":30,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Fixed local-model soil-moisture coefficient.","sensitivity_checked":false},
  {"field":"wc_sweep.sweep_parameter","value":"soil_moisture","source_kind":"model_default","source_ref":"registered water_cloud parameter resolution","reason":"Main run sweeps soil moisture.","sensitivity_checked":true},
  {"field":"wc_sweep.sweep_start","value":0.05,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Submitted sweep lower bound without paper-derived evidence.","sensitivity_checked":true},
  {"field":"wc_sweep.sweep_stop","value":0.5,"source_kind":"assumption","source_ref":"approved research plan v001","reason":"Submitted sweep upper bound without paper-derived evidence.","sensitivity_checked":true},
  {"field":"wc_sweep.sweep_points","value":20,"source_kind":"unknown","source_ref":"recorded formal run state; provenance not assigned in the ledger","reason":"Actual executed sweep resolution.","sensitivity_checked":false}
]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
