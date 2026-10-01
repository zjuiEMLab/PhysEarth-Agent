# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows two distinct, ordered brightness-temperature curves that decline monotonically as volumetric soil moisture increases from 0.05 to 0.45 m³ m⁻³. The V-polarized curve remains above the H-polarized curve across the plotted range; the curves do not visibly converge. The generated figure therefore supports the same qualitative soil-moisture sensitivity pattern as the intended passive-microwave comparison, but it is a tau-omega analogue rather than a CMEM reproduction.

The result is a **partial reproduction**: the local analogue was successfully rendered and visually reviewed, while CMEM was unavailable for direct reproduction.

## Supporting results

### Conclusion supported by the generated image

- Figure 1 has one common soil-moisture x-axis and brightness temperature in kelvin on the y-axis.
- It contains two polarization series.
- Both curves slope downward with increasing soil moisture.
- The V series is visibly above the H series throughout.
- Manual chart review passed, confirming that the plotted series, axes, units, and grouping were usable.

The image supports these qualitative statements only; it does not provide digitized values or a numerical agreement score.

### Conclusion supported by the recorded result arrays

The formal 21-point sweep produced monotonically decreasing values in both polarizations [model:tau_omega@1.0.0]:

- H polarization: 248.1286 K at 0.05 m³ m⁻³ to 216.2340 K at 0.45 m³ m⁻³.
- V polarization: 268.9662 K at 0.05 m³ m⁻³ to 236.3995 K at 0.45 m³ m⁻³.
- At the approved baseline of 0.25 m³ m⁻³: \(T_b^H=224.8044\) K and \(T_b^V=246.4358\) K [model:tau_omega@1.0.0].

No bias, RMSE, correlation, or other numerical comparison with CMEM was supplied; such statistics are **not scoreable**.

### Image–array comparison

| Aspect | Generated image | Recorded arrays | Assessment |
|---|---|---|---|
| Number of curves | Two | Two | Agreement |
| Units | Brightness temperature, K | Brightness temperature, K | Agreement |
| Ordering | V above H | V exceeds H at the reported sweep endpoints and baseline | Agreement |
| Soil-moisture response | Both curves decline | Both are monotonic decreasing | Agreement |
| Numerical agreement with CMEM | Not available from image | Not computable | Not scoreable |
| Reproduction status | Usable, reviewed chart | Successful tau-omega run | Qualitative local analogue only |

## Guessed/assumed parameters

The following values were not paper-explicit and are reported as assumptions or defaults rather than paper-derived parameters:

- `frequency_ghz = 1.41`: **model_assumption**, based on the registered tau-omega L-band analogue; the paper value was not specified for this mapping [cmem-sampling-density#03].
- `angle_deg = 40.0`: **model_assumption**, using the registered tau-omega default; not paper-explicit [cmem-sampling-density#03].
- `soil_moisture = 0.05–0.45`: **model_assumption**, swept as the supported independent variable for the local analogue [cmem-sampling-density#06].
- `soil_temperature_k = 293.0`: **backend_default**.
- `canopy_temperature_k = 293.0`: **backend_default**.
- `bulk_density_g_cm3 = 1.3`: **backend_default**.
- `vegetation_optical_depth = 0.3`: **backend_default**.
- `single_scattering_albedo = 0.05`: **backend_default**.
- `roughness_h = 0.3`: **backend_default**.
- `cross_q = 0.0`: **backend_default**.
- `sweep_parameter = soil_moisture`: **user_specified**.
- `sweep_start = 0.05`: **user_specified**.
- `sweep_stop = 0.45`: **user_specified**.
- `sweep_points = 21`: **user_specified**.

## Limitations

The experiment used tau-omega v1.0.0, not CMEM. Consequently, the figure demonstrates a supported local analogue and its qualitative soil-moisture response, but it cannot establish numerical agreement with the paper’s CMEM result. The paper-explicit value of every mapped model parameter was not available in the recorded state, and no measurement dataset or digitized paper curve was used for validation.

<parameter_provenance>
[{"field":"frequency_ghz","value":1.41,"source_kind":"assumption","source_ref":"cmem-sampling-density#03","source_span":"","reason":"provenance=model_assumption; Use the registered tau-omega L-band default as the supported analogue.","sensitivity_checked":false},{"field":"angle_deg","value":40.0,"source_kind":"assumption","source_ref":"cmem-sampling-density#03","source_span":"","reason":"provenance=model_assumption; Use the registered tau-omega default.","sensitivity_checked":false},{"field":"soil_moisture","value":"0.05 to 0.45","source_kind":"assumption","source_ref":"cmem-sampling-density#06","source_span":"","reason":"provenance=model_assumption; Sweep the supported independent variable for the local analogue.","sensitivity_checked":true},{"field":"soil_temperature_k","value":293.0,"source_kind":"model_default","source_ref":"backend default; no paper-specific value recorded","source_span":"","reason":"provenance=backend_default; Held fixed as a backend default.","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.0,"source_kind":"model_default","source_ref":"backend default; no paper-specific value recorded","source_span":"","reason":"provenance=backend_default; Held fixed as a backend default.","sensitivity_checked":false},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"model_default","source_ref":"backend default; no paper-specific value recorded","source_span":"","reason":"provenance=backend_default; Held fixed as a backend default.","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.3,"source_kind":"model_default","source_ref":"backend default; no paper-specific value recorded","source_span":"","reason":"provenance=backend_default; Held fixed as a backend default.","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.05,"source_kind":"model_default","source_ref":"backend default; no paper-specific value recorded","source_span":"","reason":"provenance=backend_default; Held fixed as a backend default.","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"model_default","source_ref":"backend default; no paper-specific value recorded","source_span":"","reason":"provenance=backend_default; Held fixed as a backend default.","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"model_default","source_ref":"backend default; no paper-specific value recorded","source_span":"","reason":"provenance=backend_default; Held fixed as a backend default.","sensitivity_checked":false},{"field":"sweep_parameter","value":"soil_moisture","source_kind":"user","source_ref":"user-approved research plan","source_span":"","reason":"provenance=user_specified; Select soil moisture as the sweep axis.","sensitivity_checked":true},{"field":"sweep_start","value":0.05,"source_kind":"user","source_ref":"user-approved research plan","source_span":"","reason":"provenance=user_specified; Preserve the requested sweep range.","sensitivity_checked":true},{"field":"sweep_stop","value":0.45,"source_kind":"user","source_ref":"user-approved research plan","source_span":"","reason":"provenance=user_specified; Preserve the requested sweep range.","sensitivity_checked":true},{"field":"sweep_points","value":21,"source_kind":"user","source_ref":"user-approved research plan","source_span":"","reason":"provenance=user_specified; Preserve the requested sweep density.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
