# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show two ordered, separated polarization curves in each plot. Both brightness temperature and emissivity decrease as soil moisture increases from 0.05 to 0.60 m³ m⁻³; vertical polarization remains above horizontal polarization throughout. The figures show no curve crossing or convergence over the plotted range.

Thus, the approved local `tau_omega` analogue reproduces the qualitative soil-moisture response, but the exact CMEM tau-omega emission-chain comparison is not identifiable from the available execution. The calibrated outcome is **partial**, not an exact quantitative reproduction. [model:tau_omega@1.0.0] [cmem-sampling-density#03]

## Supporting results

### Conclusion supported by the generated figures

- **Figure 1:** Soil moisture (m³ m⁻³) versus brightness temperature (K), with two polarization series.
- **Figure 2:** Soil moisture (m³ m⁻³) versus emissivity (1), with two polarization series.
- In both figures, the curves have the same qualitative ordering: vertical polarization is above horizontal polarization.
- The curves remain visibly separated and decrease across the full plotted range.
- Both generated charts passed the automated legibility check. This establishes that the plotted arrays are usable; it does not establish agreement with the paper figure.

### Conclusion supported by the executed arrays

The 12-point sweep confirms monotonic decreases in both polarizations:

- \(T_b^H\): 248.1286 to 212.2743 K.
- \(T_b^V\): 268.9662 to 231.4606 K.
- \(e_H\): 0.7073 to 0.4458.
- \(e_V\): 0.8593 to 0.5857. [model:tau_omega@1.0.0]

At the baseline soil moisture of 0.25 m³ m⁻³, the model produced \(T_b^H=224.8044\) K, \(T_b^V=246.4358\) K, \(e_H=0.5372\), and \(e_V=0.6950\). [model:tau_omega@1.0.0]

## Comparison and qualification

| Aspect | Generated-figure conclusion | Array-supported conclusion | Assessment |
|---|---|---|---|
| Trend | Both polarization curves decrease with soil moisture. | All four output series decrease monotonically. | Same qualitative pattern. |
| Ordering | Vertical polarization remains above horizontal polarization. | The recorded endpoints and intermediate values preserve that ordering. | Consistent. |
| Curve crossing | No visible crossing. | No crossing is present in the recorded sweep summaries. | Consistent. |
| Quantitative paper agreement | Not scoreable from the generated figures alone. | No RMSE, bias, correlation, or other comparison statistic was supplied. | N/A. |
| Exact method reproduction | Not established. | The available run used registered `tau_omega`, not the unavailable CMEM tau-omega chain. | Partial outcome. |

The low-moisture interval from 0.05 to 0.10 produced the automated endpoint warning for the horizontal-polarization curves. This is a feature of the local result requiring interpretation, not evidence of failed execution. The numerical comparison with the paper is not scoreable because the exact CMEM chain was unavailable and no digitized reference series was supplied. [skill:research-reporting]

## Guessed/assumed parameters

The following values were not paper-explicit in the approved ledger:

- Incidence angle: 40.0°.
- Bulk density: 1.3 g cm⁻³.
- Soil temperature: 293.0 K.
- Canopy temperature: 293.0 K.
- Single-scattering albedo: 0.05.
- Roughness parameter \(h\): 0.3.
- Cross-polarization parameter \(Q\): 0.0.
- Vegetation optical depth: 0.3, retained from the backend default.

The paper-explicit value was the 1.41 GHz L-band frequency. The soil-moisture range, sweep bounds, and 12-point resolution were user-specified. [cmem-sampling-density#03] [model:tau_omega@1.0.0]

## Limitations and final conclusion

The figures and arrays support an inverse local relationship between soil moisture and both brightness temperature and emissivity for this registered `tau_omega` configuration. They do not establish quantitative agreement with the paper’s CMEM implementation, and the requested exact CMEM comparison remains unavailable. The reproduction outcome is therefore **partial**. [model:tau_omega@1.0.0] [cmem-sampling-density#03]

<parameter_provenance>
[{"field":"frequency_ghz","value":1.41,"source_kind":"paper","source_ref":"cmem-sampling-density#03","source_span":"L-band context","reason":"Use the paper's L-band context.","sensitivity_checked":false},{"field":"angle_deg","value":40.0,"source_kind":"assumption","source_ref":"approved parameter ledger: no paper-specific value","reason":"Fixed valid geometry for the local analogue.","sensitivity_checked":false},{"field":"soil_moisture","value":"0.05 to 0.60","source_kind":"user","source_ref":"approved research plan","reason":"Registered valid sweep range.","sensitivity_checked":true},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"approved parameter ledger: no paper-specific value","reason":"Held fixed because no paper-specific value was available in the opened evidence.","sensitivity_checked":false},{"field":"soil_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"approved parameter ledger: frozen-soil conditions outside registered validity","reason":"Used an unfrozen reference temperature.","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"approved parameter ledger","reason":"Held equal to soil temperature.","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.3,"source_kind":"model_default","source_ref":"registered tau_omega backend default","reason":"No paper-specific value was supplied for this local analogue.","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.05,"source_kind":"assumption","source_ref":"approved parameter ledger","reason":"Held fixed with nonzero vegetation optical depth.","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"assumption","source_ref":"approved parameter ledger: no paper-specific value","reason":"No paper-specific value was supplied for this local analogue.","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"assumption","source_ref":"approved parameter ledger","reason":"Held fixed for the local analogue.","sensitivity_checked":false},{"field":"sweep_parameter","value":"soil_moisture","source_kind":"user","source_ref":"approved research plan","reason":"Soil moisture is the sole swept input.","sensitivity_checked":false},{"field":"sweep_start","value":0.05,"source_kind":"user","source_ref":"approved research plan","reason":"Registered valid lower endpoint.","sensitivity_checked":false},{"field":"sweep_stop","value":0.6,"source_kind":"user","source_ref":"approved research plan","reason":"Registered valid upper endpoint.","sensitivity_checked":false},{"field":"sweep_points","value":12,"source_kind":"user","source_ref":"approved research plan","reason":"Requested number of sweep points.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"approved baseline run specification","reason":"Baseline run is fixed-parameter.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
