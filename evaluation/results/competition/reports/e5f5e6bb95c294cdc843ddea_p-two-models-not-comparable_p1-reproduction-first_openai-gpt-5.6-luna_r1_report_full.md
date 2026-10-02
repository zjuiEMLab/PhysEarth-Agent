# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show opposite monotonic responses to increasing soil moisture: tau–omega brightness temperature decreases, while Water Cloud total backscatter increases. The passive and active curves are ordered within their respective observables, but they are not directly comparable because they use different physical quantities and units. [model:tau_omega@1.0.0] [model:water_cloud@1.0.0]

The approved local reproduction is therefore **partial**. All required runs and generated figures completed, but no numerical agreement statistic or digitized source-figure comparison was recorded.

## Supporting results

### Conclusion supported by the generated figures

- **Figure 1:** two brightness-temperature curves are plotted against soil moisture, with axes in m³ m⁻³ and K.
- **Figure 2:** three backscatter curves are plotted against soil moisture, with axes in m³ m⁻³ and dB.
- The tau–omega curves decrease across the plotted range.
- The Water Cloud total and soil backscatter curves increase; the vegetation component is visually constant because vegetation parameters were fixed.

Both figures passed the recorded render check, which establishes that the plotted arrays were finite, sufficiently populated, and legible. It does not establish agreement with a source figure.

### Conclusion supported by the result arrays

For the 0.05–0.50 m³ m⁻³ sweep:

- Tau–omega horizontal brightness temperature decreased from **248.13 K to 214.76 K**; vertical brightness temperature decreased from **268.97 K to 234.59 K**. [model:tau_omega@1.0.0]
- Water Cloud total backscatter increased from **−16.01 dB to −7.84 dB**. Soil backscatter increased from **−20.50 dB to −7.00 dB**, while vegetation backscatter remained **−17.32 dB**. [model:water_cloud@1.0.0]
- At the baseline soil moisture of 0.25 m³ m⁻³, tau–omega produced horizontal brightness temperature **224.80 K** and horizontal emissivity **0.5372**. Water Cloud produced total backscatter **−13.52 dB**. [model:tau_omega@1.0.0] [model:water_cloud@1.0.0]

No bias, RMSE, correlation, threshold, or validation statistic was supplied; these quantities are **not scoreable**.

## Image and array comparison

| Aspect | Generated figures | Result arrays | Assessment |
|---|---|---|---|
| Number and grouping | Two passive-polarization curves; three active-backscatter curves | Same planned series were plotted | Agreement |
| Axes and units | Soil moisture versus K or dB | Matching model output units | Agreement |
| Trend | Passive decrease; active increase | Monotonic decrease/increase recorded | Agreement |
| Numerical agreement with a source | Not established | No digitized source values or comparison metric | Not identifiable |
| Cross-observable comparison | K and dB are separate quantities | No direct difference is valid | Not comparable |

The opened paper supplied the L-band context, but the recorded execution used several local assumptions rather than a fully paper-specified parameter set. [cmem-sampling-density#00]

## Guessed/assumed parameters

The following values were not paper-explicit in the authoritative ledger:

- `angle_deg = 40`: model assumption.
- `bulk_density_g_cm3 = 1.3`: model assumption.
- `soil_temperature_k = 293`: model assumption.
- `canopy_temperature_k = 293`: model assumption.
- `vegetation_optical_depth = 0.3`: model assumption.
- `single_scattering_albedo = 0.05`: model assumption.
- `roughness_h = 0.3`: model assumption.
- `cross_q = 0`: model assumption.
- Water Cloud `vegetation_water_kg_m2 = 1.0`: model assumption.
- Water Cloud `coefficient_a = 0.09`, `coefficient_b = 0.12`, `coefficient_c = -22`, and `coefficient_d = 30`: backend defaults.
- Sweep start and stop values, 0.05 and 0.50 m³ m⁻³: recorded as model assumptions in the ledger.
- Sweep resolution: 12 points, user-specified.
- Frequency `1.41 GHz`: paper-explicit L-band mapping from the opened paper context. [cmem-sampling-density#00]

## Limitations

The report does not claim exact reproduction of a published numerical curve. The generated figures establish the approved local-model trends only. The passive and active outputs should not be ranked against one another as if they measured the same quantity. The result is **partial**, not failed: all runs and required figures were produced, but source-curve digitization and numerical agreement checks were not recorded.

<parameter_provenance>
[{"field":"tau_omega.frequency_ghz","value":1.41,"source_kind":"paper","source_ref":"cmem-sampling-density#00","source_span":"L-band microwave-emission context","reason":"Use the paper's L-band context as the frequency mapping.","sensitivity_checked":false},{"field":"tau_omega.angle_deg","value":40,"source_kind":"assumption","source_ref":"approved plan v001; fixed representative geometry","reason":"Fixed representative geometry for the local sweep.","sensitivity_checked":false},{"field":"tau_omega.soil_moisture","value":"0.05 to 0.50","source_kind":"user","source_ref":"user-confirmed local exploration range","reason":"User-confirmed local exploration range.","sensitivity_checked":true},{"field":"tau_omega.bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"approved plan v001; fixed representative soil state","reason":"Fixed representative soil state.","sensitivity_checked":false},{"field":"tau_omega.soil_temperature_k","value":293,"source_kind":"assumption","source_ref":"approved plan v001; fixed unfrozen effective temperature","reason":"Fixed unfrozen effective temperature within model validity.","sensitivity_checked":false},{"field":"tau_omega.canopy_temperature_k","value":293,"source_kind":"assumption","source_ref":"approved plan v001; fixed representative effective canopy temperature","reason":"Fixed representative effective canopy temperature.","sensitivity_checked":false},{"field":"tau_omega.vegetation_optical_depth","value":0.3,"source_kind":"assumption","source_ref":"approved plan v001; fixed nonzero canopy state","reason":"Fixed nonzero canopy state.","sensitivity_checked":false},{"field":"tau_omega.single_scattering_albedo","value":0.05,"source_kind":"assumption","source_ref":"approved plan v001; fixed canopy scattering state","reason":"Fixed canopy scattering state.","sensitivity_checked":false},{"field":"tau_omega.roughness_h","value":0.3,"source_kind":"assumption","source_ref":"approved plan v001; fixed representative roughness","reason":"Fixed representative roughness.","sensitivity_checked":false},{"field":"tau_omega.cross_q","value":0,"source_kind":"assumption","source_ref":"approved plan v001; fixed zero mixing parameter","reason":"Fixed zero mixing parameter.","sensitivity_checked":false},{"field":"water_cloud.angle_deg","value":40,"source_kind":"assumption","source_ref":"approved plan v001; fixed representative geometry","reason":"Fixed representative geometry.","sensitivity_checked":false},{"field":"water_cloud.soil_moisture","value":"0.05 to 0.50","source_kind":"user","source_ref":"user-confirmed local exploration range","reason":"User-confirmed local exploration range.","sensitivity_checked":true},{"field":"water_cloud.vegetation_water_kg_m2","value":1.0,"source_kind":"assumption","source_ref":"approved plan v001; fixed representative canopy water state","reason":"Fixed representative canopy water state.","sensitivity_checked":false},{"field":"water_cloud.coefficient_a","value":0.09,"source_kind":"model_default","source_ref":"registered backend default","reason":"Retained registered backend default.","sensitivity_checked":false},{"field":"water_cloud.coefficient_b","value":0.12,"source_kind":"model_default","source_ref":"registered backend default","reason":"Retained registered backend default.","sensitivity_checked":false},{"field":"water_cloud.coefficient_c","value":-22,"source_kind":"model_default","source_ref":"registered backend default","reason":"Retained registered backend default.","sensitivity_checked":false},{"field":"water_cloud.coefficient_d","value":30,"source_kind":"model_default","source_ref":"registered backend default","reason":"Retained registered backend default.","sensitivity_checked":false},{"field":"tau_omega.sweep_parameter","value":"soil_moisture","source_kind":"user","source_ref":"user requested soil-moisture sweep","reason":"User requested soil-moisture sweep.","sensitivity_checked":true},{"field":"water_cloud.sweep_parameter","value":"soil_moisture","source_kind":"user","source_ref":"user requested soil-moisture sweep","reason":"User requested soil-moisture sweep.","sensitivity_checked":true},{"field":"tau_omega.sweep_points","value":12,"source_kind":"user","source_ref":"approved plan v001; preserved sweep resolution","reason":"Preserve existing sweep resolution.","sensitivity_checked":false},{"field":"water_cloud.sweep_points","value":12,"source_kind":"user","source_ref":"approved plan v001; preserved sweep resolution","reason":"Preserve existing sweep resolution.","sensitivity_checked":false},{"field":"tau_omega.sweep_start","value":0.05,"source_kind":"assumption","source_ref":"submitted run retained this value without attached paper/user evidence","reason":"Retained approved run value.","sensitivity_checked":true},{"field":"tau_omega.sweep_stop","value":0.5,"source_kind":"assumption","source_ref":"submitted run retained this value without attached paper/user evidence","reason":"Retained approved run value.","sensitivity_checked":true},{"field":"water_cloud.sweep_start","value":0.05,"source_kind":"assumption","source_ref":"submitted run retained this value without attached paper/user evidence","reason":"Retained approved run value.","sensitivity_checked":true},{"field":"water_cloud.sweep_stop","value":0.5,"source_kind":"assumption","source_ref":"submitted run retained this value without attached paper/user evidence","reason":"Retained approved run value.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
