# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 shows two ordered, clearly separated brightness-temperature curves that both decrease monotonically as volumetric soil moisture increases from **0.05 to 0.50 m³ m⁻³**. The V-polarized curve remains above the H-polarized curve throughout the sweep. [model:tau_omega@1.0.0]

This is a **partial qualitative reproduction**, not a reproduction of the paper’s CMEM result. The registered `tau_omega` model produced the requested L-band soil-moisture response, but CMEM was unavailable; therefore, the paper’s exact model comparison and any CMEM sampling-density conclusion are not identifiable from this run. [cmem-sampling-density#03] [cmem-sampling-density#06] [cmem-sampling-density#fig-fig09]

## Supporting results

### Conclusion supported by the generated image

Figure 1 contains two series on the stated axes:

- x-axis: volumetric soil moisture, m³ m⁻³
- y-axis: brightness temperature, K
- curves: H and V polarization

The curves have the same qualitative ordering across the plotted range: both decline with increasing soil moisture, and the V curve stays above the H curve. The figure was rendered successfully and passed the automated legibility check; that check does not establish agreement with the source figure.

### Conclusion supported by the result arrays

The actual model arrays show:

- H polarization: **248.13 K** at 0.05 m³ m⁻³ to **214.76 K** at 0.50 m³ m⁻³.
- V polarization: **268.97 K** at 0.05 m³ m⁻³ to **234.59 K** at 0.50 m³ m⁻³.
- Both series are recorded as monotonically decreasing.
- Baseline at 0.25 m³ m⁻³: **224.80 K** for H and **246.44 K** for V. [model:tau_omega@1.0.0]

No bias, RMSE, correlation, digitized source values, or CMEM comparison statistic was computed; numerical agreement with the paper is therefore **not scoreable**.

### Comparison

| Aspect | Generated figure and arrays | Source-paper reproduction |
|---|---|---|
| Curves | Two polarization brightness-temperature curves | Paper target is associated with CMEM |
| Qualitative pattern | Both curves decrease with soil moisture; V remains above H | Exact source-model correspondence is not established |
| Numerical comparison | Recorded tau-omega values available | CMEM values unavailable |
| Outcome | Supported partial analogue | Partial, not full reproduction |

The generated result is internally consistent with its approved tau-omega configuration. It should not be interpreted as a recovered CMEM curve or as a CMEM sampling-density result.

## Guessed/assumed parameters

The following values were not paper-explicit and must be treated as assumed or model-default inputs:

- `frequency_ghz = 1.41`: model assumption; used as a supported L-band analogue, not as a recovered CMEM figure setting. [cmem-sampling-density#03]
- `angle_deg = 40.0`: model assumption used to isolate soil-moisture response.
- `vegetation_optical_depth = 0.3`: backend default, held fixed.
- `single_scattering_albedo = 0.05`: backend default, held fixed.
- `roughness_h = 0.3`: backend default, held fixed.
- `bulk_density_g_cm3 = 1.3`: model assumption without attached paper or user evidence.
- `soil_temperature_k = 293.0`: model assumption without attached paper or user evidence.
- `canopy_temperature_k = 293.0`: model assumption without attached paper or user evidence.
- `cross_q = 0.0`: model assumption without attached paper or user evidence.
- `sweep_start = 0.05` and `sweep_stop = 0.50`: recorded plan values used for the supported forward-response test.
- `sweep_parameter` and `sweep_points`: backend/model-resolved controls; they are not paper evidence.

The soil-moisture sweep itself was user-specified as a supported forward-model sensitivity test. It was not a CMEM sampling-density metric.

## Limitations

The paper target used CMEM, whereas the available registered model was tau-omega. The local model is therefore not an alias for CMEM, and the result cannot establish numerical agreement with the source figure. The source figure was treated as paper evidence, not digitized reference data; no source-curve values were extracted. [cmem-sampling-density#fig-fig09]

The final conclusion is consequently: **the approved tau-omega run demonstrates a monotonic, polarization-ordered brightness-temperature response over 0.05–0.50 m³ m⁻³, but the paper reproduction remains partial because CMEM is unavailable.**

<parameter_provenance>
[{"field":"frequency_ghz","value":1.41,"source_kind":"assumption","source_ref":"cmem-sampling-density#03","reason":"Used as a supported L-band analogue, not claimed as a recovered CMEM figure setting.","sensitivity_checked":false},{"field":"soil_moisture","value":"sweep 0.05 to 0.50","source_kind":"user","source_ref":"user-approved research plan","reason":"Tests the supported forward response; it is not a CMEM sampling-density metric.","sensitivity_checked":true},{"field":"angle_deg","value":40.0,"source_kind":"assumption","source_ref":"approved run configuration","reason":"Fixed to isolate soil-moisture response.","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.3,"source_kind":"model_default","source_ref":"registered tau_omega default","reason":"Held fixed; no CMEM vegetation-parameter equivalence is claimed.","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.05,"source_kind":"model_default","source_ref":"registered tau_omega default","reason":"Held fixed.","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"model_default","source_ref":"registered tau_omega default","reason":"Held fixed.","sensitivity_checked":false},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"soil_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"registered model parameter resolution for the baseline run","reason":"The registered model inserted this value for the baseline; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"registered model parameter resolution for the baseline run","reason":"The registered model inserted this value for the baseline; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_start","value":0.05,"source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_stop","value":0.5,"source_kind":"assumption","source_ref":"approved run configuration","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"soil_moisture_sweep_parameter","value":"soil_moisture","source_kind":"user","source_ref":"approved soil_moisture_sweep run","reason":"The formal sweep varied soil moisture over the approved range.","sensitivity_checked":true},{"field":"soil_moisture_sweep_points","value":12,"source_kind":"user","source_ref":"approved soil_moisture_sweep run","reason":"The formal sweep used twelve approved points.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
