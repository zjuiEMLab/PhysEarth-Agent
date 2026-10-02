# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows two brightness-temperature curves, H and V polarization, plotted against soil moisture. Both curves decrease as soil moisture increases from **0.05 to 0.45**, and the V-polarized curve remains above the H-polarized curve throughout. No crossing or convergence is visible. [cmem-sampling-density#fig-fig09]

The executed result reproduces this qualitative ordering and monotonic pattern with `tau_omega@1.0.0`. It is a **partial reproduction**: CMEM was unavailable, so the result is a local tau-omega benchmark under the Figure 9 reference context, not a quantitative CMEM reproduction. [model:tau_omega@1.0.0]

## Supporting results

### Source and generated image

The generated chart contains two series, `tb_h` and `tb_v`.

- x-axis: Soil moisture (volumetric fraction)
- y-axis: Brightness temperature (K)
- curves: two polarization outputs
- visible pattern: both curves decrease; V remains above H

This is the qualitative pattern observed when comparing the generated chart with the source Figure 9. The image does not provide digitized values or a quantitative agreement statistic. [cmem-sampling-density#fig-fig09]

### Recorded model results

The baseline run used `soil_moisture = 0.2` and produced:

- `tb_h = 164.5542 K`
- `tb_v = 211.4816 K`

The sensitivity run used the recorded soil-moisture interval **0.05–0.45** with 9 points:

- `tb_h`: **207.2398 K** at 0.05 to **139.0709 K** at 0.45
- `tb_v`: **251.7769 K** at 0.05 to **182.1709 K** at 0.45

Both outputs were monotonic decreasing, and V polarization was higher than H polarization at all recorded points. [model:tau_omega@1.0.0]

## Comparison

| Aspect | Image-based conclusion | Result-based conclusion | Assessment |
|---|---|---|---|
| Number of curves | Two | `tb_h` and `tb_v` | Agreement |
| Soil-moisture response | Both curves decrease | Both outputs decrease monotonically over **0.05–0.45** | Same qualitative pattern |
| Polarization ordering | V is above H | V is above H at every recorded point | Agreement |
| Quantitative CMEM agreement | Not identifiable from the image | Not calculated; RMSE, bias, and correlation are N/A | Not scoreable |
| Model formulation | Figure 9 reference context | `tau_omega@1.0.0` | Limits the result to a partial reproduction |

The recorded render check confirms that the generated arrays were finite, sufficiently sampled, and legible. It does not establish agreement with the source image. The principal qualification is that the executed model was tau-omega, while CMEM was unavailable. [model:tau_omega@1.0.0]

## Assumed parameters

The paper-to-model mappings for frequency and observation geometry were `paper_inferred`, not paper-explicit values. Soil moisture, vegetation settings, and sweep bounds were `model_assumption`. Bulk density, temperatures, roughness, cross-polarization, sweep parameter, and sweep-point settings were `backend_default` values in the authoritative ledger. None of these values is relabeled as paper-explicit.

The recorded baseline configuration was:

- `frequency_ghz = 1.4`
- `angle_deg = 40`
- `soil_moisture = 0.2`
- `vegetation_optical_depth = 0.0`
- `single_scattering_albedo = 0.0`

The sensitivity configuration used the recorded interval `sweep_start = 0.05` and `sweep_stop = 0.45`. [model:tau_omega@1.0.0]

## Limitations

A CMEM result, CMEM parameter equivalence, and a numerical validation statistic are not identifiable from the recorded state. The conclusion is therefore limited to the qualitative behavior of the executed tau-omega configuration. [cmem-sampling-density#03] [cmem-sampling-density#06]

<parameter_provenance>
[{"field":"frequency_ghz","value":"1.4","source_kind":"paper","source_ref":"cmem-sampling-density#03","source_span":"paper L-band reference context","reason":"Used for the local tau-omega run; not treated as equivalent to a CMEM parameter","sensitivity_checked":false},{"field":"angle_deg","value":"40","source_kind":"paper","source_ref":"cmem-sampling-density#06","source_span":"paper observation geometry","reason":"Used as a tagged reference condition for the local benchmark","sensitivity_checked":false},{"field":"soil_moisture","value":"0.2","source_kind":"assumption","source_ref":"Approved local tau-omega baseline","reason":"Concrete executable baseline; not claimed as a paper-explicit CMEM value","sensitivity_checked":true},{"field":"vegetation_optical_depth","value":"0.0","source_kind":"assumption","source_ref":"cmem-sampling-density#03","source_span":"bare-surface baseline","reason":"Set vegetation attenuation to zero","sensitivity_checked":false},{"field":"single_scattering_albedo","value":"0.0","source_kind":"assumption","source_ref":"Approved local tau-omega configuration","reason":"Legal companion setting for zero vegetation optical depth","sensitivity_checked":false},{"field":"bulk_density_g_cm3","value":"1.3","source_kind":"model_default","source_ref":"tau_omega@1.0.0","reason":"Registered backend default","sensitivity_checked":false},{"field":"soil_temperature_k","value":"293.0","source_kind":"model_default","source_ref":"tau_omega@1.0.0","reason":"Registered backend default","sensitivity_checked":false},{"field":"canopy_temperature_k","value":"293.0","source_kind":"model_default","source_ref":"tau_omega@1.0.0","reason":"Registered backend default","sensitivity_checked":false},{"field":"roughness_h","value":"0.3","source_kind":"model_default","source_ref":"tau_omega@1.0.0","reason":"Registered backend default","sensitivity_checked":false},{"field":"cross_q","value":"0.0","source_kind":"model_default","source_ref":"tau_omega@1.0.0","reason":"Registered backend default","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"tau_omega@1.0.0","reason":"Recorded baseline default; the approved sensitivity run varied soil_moisture","sensitivity_checked":true},{"field":"sweep_points","value":"10","source_kind":"model_default","source_ref":"tau_omega@1.0.0","reason":"Recorded baseline default; the sensitivity run used 9 points","sensitivity_checked":false},{"field":"sweep_start","value":"0.05","source_kind":"assumption","source_ref":"Approved sensitivity run","reason":"Recorded lower bound of the local soil-moisture sweep","sensitivity_checked":false},{"field":"sweep_stop","value":"0.45","source_kind":"assumption","source_ref":"Approved sensitivity run","reason":"Recorded upper bound of the local soil-moisture sweep","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| tau_omega | frequency_ghz | 1.4 | paper_inferred | cmem-sampling-density#03 |
| tau_omega | angle_deg | 40 | paper_inferred | cmem-sampling-density#06 |
| tau_omega | soil_moisture | 0.2 | model_assumption | - |
| tau_omega | vegetation_optical_depth | 0.0 | model_assumption | cmem-sampling-density#03 |
| tau_omega | single_scattering_albedo | 0.0 | model_assumption | - |
| tau_omega | bulk_density_g_cm3 | 1.3 | backend_default | - |
| tau_omega | soil_temperature_k | 293.0 | backend_default | - |
| tau_omega | canopy_temperature_k | 293.0 | backend_default | - |
| tau_omega | roughness_h | 0.3 | backend_default | - |
| tau_omega | cross_q | 0.0 | backend_default | - |
| tau_omega | sweep_parameter | none | backend_default | - |
| tau_omega | sweep_points | 10 | backend_default | - |
| tau_omega | sweep_start | 0.05 | model_assumption | - |
| tau_omega | sweep_stop | 0.45 | model_assumption | - |
