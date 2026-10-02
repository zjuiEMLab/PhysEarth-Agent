# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show clear, ordered sensitivity patterns in the local `tau_omega` proxy: brightness temperature decreases monotonically with soil moisture and increases monotonically with vegetation optical depth for both H and V polarization. [model:tau_omega@1.0.0]

This is a **partial, non-comparable reproduction**, not a reproduction of the paper’s CMEM tau-omega chain. The source figure was not available for an evidence-based visual comparison, so qualitative agreement with the paper cannot be scored. The unavailable comparison is the CMEM/tau-omega emission chain.

## Supporting results

### Conclusion supported by the generated figures

- **Figure 1** uses soil moisture on the x-axis and brightness temperature in K on the y-axis, with two polarization curves.
- **Figure 2** uses vegetation optical depth on the x-axis and brightness temperature in K on the y-axis, again with H and V curves.
- Both figures rendered successfully with legible two-series curves.
- Figure 2 was redrawn to accommodate its labels; this is a rendering adjustment, not evidence of physical disagreement.

The source image was not inspected, so source-supported axes, curve ordering, and pattern comparisons are **not available**.

### Conclusion supported by the result arrays

For the soil-moisture sweep from **0.05 to 0.55 m³ m⁻³**:

- H-polarized TB decreased from **248.13 K to 213.45 K**.
- V-polarized TB decreased from **268.97 K to 232.95 K**.

For the vegetation-optical-depth sweep from **0.0 to 1.5**:

- H-polarized TB increased from **157.39 K to 276.89 K**.
- V-polarized TB increased from **203.62 K to 278.10 K**.

At the baseline configuration, the model produced **224.80 K** for H polarization and **246.44 K** for V polarization. [model:tau_omega@1.0.0]

## Comparison of image-supported and array-supported conclusions

| Aspect | Generated figures | Source comparison |
|---|---|---|
| Curves rendered | Two curves in each figure | Not available |
| Units and axes | As specified in the recorded figure state | Not independently checked against a source image |
| Soil-moisture ordering | Decreasing TB | Not scoreable against source |
| Vegetation optical-depth ordering | Increasing TB | Not scoreable against source |
| Numerical agreement | Not assessed | N/A |
| RMSE, bias, correlation | Not supplied | N/A |

The array results support the reported monotonic trends. Because no source figure was available for comparison and the local model is not the paper’s CMEM implementation, reproduction agreement is not identifiable.

## Assumed parameters

All parameters below were classified as assumptions or backend defaults, not paper-explicit values. The paper section was used as context for the local proxy experiment, not as evidence that these values were specified by the paper. [cmem-sampling-density#03]

- `frequency_ghz = 1.41`: model assumption; local proxy configuration.
- `angle_deg = 40.0`: model assumption; fixed local proxy condition.
- `soil_moisture = 0.25`: model assumption; baseline value while the soil-moisture sweep varied this input.
- `bulk_density_g_cm3 = 1.3`: model assumption; fixed local proxy condition.
- `soil_temperature_k = 293.0`: model assumption; fixed local condition and validity limitation.
- `canopy_temperature_k = 293.0`: model assumption; fixed local proxy condition.
- `vegetation_optical_depth = 0.3`: model assumption; baseline value while the vegetation sweep varied this input.
- `single_scattering_albedo = 0.05`: model assumption; fixed local proxy condition.
- `roughness_h = 0.3`: model assumption; fixed local proxy condition.
- `cross_q = 0.0`: model assumption; fixed local proxy condition.
- `sweep_parameter = none`: backend default for the baseline.
- `sweep_points = 10`: backend default metadata for the baseline.
- `soil-moisture sweep_start = 0.05`: model assumption; retained run value without paper evidence.
- `soil-moisture sweep_stop = 0.55`: model assumption; retained run value without paper evidence.
- `soil-moisture sweep_points = 11`: approved sensitivity-run setting.
- `vegetation-optical-depth sweep_start = 0.0`: approved sensitivity-run setting.
- `vegetation-optical-depth sweep_stop = 1.5`: approved sensitivity-run setting.
- `vegetation-optical-depth sweep_points = 11`: approved sensitivity-run setting.

## Limitations

The results describe the registered local `tau_omega` model only. They are not measurements and were not compared numerically with the paper. The unavailable CMEM tau-omega chain prevents a model-equivalent reproduction. No RMSE, bias, correlation, threshold, or parameter-identification result was supplied.

<parameter_provenance>
[{"field":"frequency_ghz","value":1.41,"source_kind":"assumption","source_ref":"cmem-sampling-density#03; local proxy configuration only","reason":"Assumed L-band frequency for the local proxy","sensitivity_checked":false},{"field":"angle_deg","value":40.0,"source_kind":"assumption","source_ref":"cmem-sampling-density#03; fixed local proxy condition","reason":"Held fixed across approved runs","sensitivity_checked":false},{"field":"soil_moisture","value":0.25,"source_kind":"assumption","source_ref":"cmem-sampling-density#03; soil-moisture sweep baseline","reason":"Baseline value while soil moisture was swept","sensitivity_checked":true},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"cmem-sampling-density#03; fixed local proxy condition","reason":"Held fixed across approved runs","sensitivity_checked":false},{"field":"soil_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"cmem-sampling-density#03; validity limitation","reason":"Fixed effective soil temperature","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.0,"source_ref":"cmem-sampling-density#03; fixed local proxy condition","source_kind":"assumption","reason":"Fixed effective canopy temperature","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.3,"source_kind":"assumption","source_ref":"cmem-sampling-density#03; vegetation-optical-depth sweep baseline","reason":"Baseline value while vegetation optical depth was swept","sensitivity_checked":true},{"field":"single_scattering_albedo","value":0.05,"source_kind":"assumption","source_ref":"cmem-sampling-density#03; fixed local proxy condition","reason":"Held fixed across approved runs","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"assumption","source_ref":"cmem-sampling-density#03; fixed local proxy condition","reason":"Held fixed across approved runs","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"assumption","source_ref":"cmem-sampling-density#03; fixed local proxy condition","reason":"Held fixed across approved runs","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"cmem-sampling-density#03; baseline does not sweep","reason":"Backend-resolved baseline setting","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"cmem-sampling-density#03; backend-resolved metadata","reason":"Default baseline metadata","sensitivity_checked":false},{"field":"soil_moisture_sweep_start","value":0.05,"source_kind":"assumption","source_ref":"approved run soil_moisture_sweep; no paper evidence attached","reason":"Lower endpoint of the approved soil-moisture sweep","sensitivity_checked":true},{"field":"soil_moisture_sweep_stop","value":0.55,"source_kind":"assumption","source_ref":"approved run soil_moisture_sweep; no paper evidence attached","reason":"Upper endpoint of the approved soil-moisture sweep","sensitivity_checked":true},{"field":"soil_moisture_sweep_points","value":11,"source_kind":"assumption","source_ref":"approved run soil_moisture_sweep","reason":"Approved chart sampling","sensitivity_checked":true},{"field":"vegetation_optical_depth_sweep_start","value":0.0,"source_kind":"assumption","source_ref":"approved run vod_sweep","reason":"Lower endpoint of the approved vegetation-optical-depth sweep","sensitivity_checked":true},{"field":"vegetation_optical_depth_sweep_stop","value":1.5,"source_kind":"assumption","source_ref":"approved run vod_sweep","reason":"Upper endpoint of the approved vegetation-optical-depth sweep","sensitivity_checked":true},{"field":"vegetation_optical_depth_sweep_points","value":11,"source_kind":"assumption","source_ref":"approved run vod_sweep","reason":"Approved chart sampling","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
