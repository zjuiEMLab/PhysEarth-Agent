# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure shows two finite, ordered brightness-temperature curves: V polarization remains above H polarization, and both increase slightly across the plotted 1–2 GHz range. The result is a **partial surrogate**, not a reproduction of the requested frozen-soil case: the executed model used 273.15 K rather than the requested 260 K. [model:tau_omega@1.0.0]

The requested frozen-soil brightness temperature is therefore **not identifiable** with the registered tau–omega model under the approved configuration. The chart is usable, but no source-image comparison or numerical agreement statistic was recorded.

## Supporting results

### Conclusion supported by the generated image

Figure 1 contains two series with frequency in GHz on the x-axis and brightness temperature in K on the y-axis. The V-polarized curve is visibly above the H-polarized curve throughout, and both curves have a small positive slope. The figure contains the expected two plotted outputs. [model:tau_omega@1.0.0]

### Conclusion supported by the result arrays

The executed run used eight frequency points from 1 to 2 GHz:

- H polarization: **143.791–144.188 K**
- V polarization: **186.519–186.972 K**

Both series were monotonic increasing in the recorded output. [model:tau_omega@1.0.0]

No bias, RMSE, correlation, or other validation statistic was supplied; numerical agreement with the paper is therefore **not scoreable**.

### Image–array comparison

| Aspect | Generated image | Result arrays | Assessment |
|---|---|---|---|
| Number of curves | Two | `tb_h` and `tb_v` | Agreement |
| Ordering | V above H | V exceeds H at all recorded points | Agreement |
| Trend | Both increase slightly | Both are monotonic increasing | Agreement |
| Numerical agreement with source | Not assessed | No reference values or metric supplied | Not scoreable |
| Frozen-soil validity | Not established by the image | Run used 273.15 K, not 260 K | Partial surrogate only |

The passed render check establishes that the generated curves were finite, sufficiently sampled, and legible; it does not establish agreement with a source figure. [skill:research-reporting]

## Guessed/assumed parameters

The following values were not paper-explicit and are reported as assumptions, defaults, or user-specified inputs according to the parameter ledger:

- `soil_temperature_k = 273.15`: `model_assumption`; nearest legal boundary used only for the partial surrogate.
- `soil_moisture = 0.25`: `user_specified`.
- `frequency_ghz = 1.41`: `model_assumption`; the paper provides the L-band context, while 1.41 GHz is an implementation choice. [cmem-sampling-density#03]
- `angle_deg = 40`: `model_assumption`; the paper context gives approximately 41°, while the approved run used 40°. [cmem-sampling-density#03]
- `bulk_density_g_cm3 = 1.3`: `backend_default`.
- `canopy_temperature_k = 273.15`: `model_assumption`.
- `vegetation_optical_depth = 0`: `model_assumption`.
- `single_scattering_albedo = 0`: `model_assumption`, required for the zero-vegetation configuration.
- `roughness_h = 0.3`: `backend_default`.
- `cross_q = 0`: `backend_default`.
- The executed run actually used a frequency sweep with `sweep_parameter = frequency_ghz`, `sweep_points = 8`, `sweep_start = 1.0`, and `sweep_stop = 2.0`. These values are taken from the formal run record; they differ from the supplied ledger entries that list an inactive sweep and 10 points. [model:tau_omega@1.0.0]

## Limitations

The registered model does not provide the requested frozen-soil calculation at 260 K; the approved run used the nearest legal temperature, 273.15 K. Consequently, the output cannot be presented as a frozen-soil result. The bare-soil interpretation, canopy temperature, roughness, polarization mixing, and frequency-sweep settings were not all paper-explicit. No source-image comparison, digitized reference data, or validation metric was recorded. The direct conclusion is therefore: **the approved run demonstrates the surrogate’s polarization ordering and slight frequency increase, but it does not reproduce or identify the requested frozen-soil brightness temperature**.

<parameter_provenance>
[{"field":"soil_temperature_k","value":273.15,"source_kind":"assumption","source_ref":"Approved partial surrogate; requested frozen-soil temperature 260 K is outside the legal model range","reason":"Only for an explicitly labeled partial surrogate, not the requested frozen-soil result","sensitivity_checked":false},{"field":"soil_moisture","value":0.25,"source_kind":"user","source_ref":"User-approved research plan","reason":"The registered input is fixed directly by the user request","sensitivity_checked":false},{"field":"frequency_ghz","value":1.41,"source_kind":"assumption","source_ref":"cmem-sampling-density#03","source_span":"L-band observations and modelling context","reason":"The paper establishes the L-band context, while 1.41 GHz is an implementation choice for the surrogate","sensitivity_checked":false},{"field":"angle_deg","value":40.0,"source_kind":"assumption","source_ref":"cmem-sampling-density#03","source_span":"approximately 41 degree observation context","reason":"The paper context gives approximately 41 degrees, while the surrogate uses 40 degrees","sensitivity_checked":false},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"model_default","source_ref":"Registered tau_omega backend default","reason":"The registered backend supplied this default; it is not paper evidence","sensitivity_checked":false},{"field":"canopy_temperature_k","value":273.15,"source_kind":"assumption","source_ref":"Approved partial surrogate configuration","reason":"The surrogate uses the legal boundary temperature because the exact frozen-soil case is unavailable","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.0,"source_kind":"assumption","source_ref":"Approved partial surrogate configuration","reason":"The surrogate interprets the request as bare soil; this is not specified by the paper","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.0,"source_kind":"assumption","source_ref":"Registered tau_omega legal combination for zero vegetation optical depth","reason":"Zero albedo is used when vegetation optical depth is zero","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"model_default","source_ref":"Registered tau_omega backend default","reason":"The registered backend supplied this default; it is not paper evidence","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"model_default","source_ref":"Registered tau_omega backend default","reason":"The registered backend supplied this default","sensitivity_checked":false},{"field":"sweep_parameter","value":"frequency_ghz","source_kind":"model_default","source_ref":"Executed run record; discrepancy with supplied ledger noted","reason":"The formal run swept frequency despite the ledger listing an inactive sweep","sensitivity_checked":false},{"field":"sweep_points","value":8,"source_kind":"model_default","source_ref":"Executed run record; discrepancy with supplied ledger noted","reason":"The formal run returned eight points","sensitivity_checked":false},{"field":"sweep_start","value":1.0,"source_kind":"assumption","source_ref":"Executed run record","reason":"The submitted run retained this value without attached paper or user evidence","sensitivity_checked":false},{"field":"sweep_stop","value":2.0,"source_kind":"assumption","source_ref":"Executed run record","reason":"The submitted run retained this value without attached paper or user evidence","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
