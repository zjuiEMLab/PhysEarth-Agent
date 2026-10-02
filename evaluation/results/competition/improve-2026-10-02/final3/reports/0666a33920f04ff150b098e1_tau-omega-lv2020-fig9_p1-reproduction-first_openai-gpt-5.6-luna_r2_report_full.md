# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows two tau–omega brightness-temperature curves as soil moisture increases. Both curves decrease monotonically, and the V-polarized curve remains above the H-polarized curve throughout the plotted interval. The curves do not cross. [model:tau_omega@1.0.0]

This is a **partial reproduction**. The generated figure supports the same qualitative sensitivity pattern represented by the paper target, but the unavailable CMEM implementation prevents quantitative or implementation-level reproduction. The requested CMEM comparison is therefore not identifiable. [cmem-sampling-density#fig-fig09] [research-reporting#00]

## Source and generated-image conclusion

The generated chart contains two series:

- x-axis: soil moisture, cm³ cm⁻³;
- y-axis: brightness temperature, K;
- curves: H-polarized and V-polarized brightness temperature.

The image shows decreasing curves, with V above H and no visible crossing. The source target is the paper’s Fig. 9 sensitivity result. [cmem-sampling-density#fig-fig09]

No digitized source values or compatible CMEM output are available. Consequently, the image supports a qualitative pattern comparison only; it does not establish numerical agreement. [research-reporting#00]

## Supporting results

The executed tau–omega result contains 20 points over the soil-moisture sweep. The recorded endpoint outputs are:

- H-polarized brightness temperature: 232.4935881419776 K at the low endpoint and 214.76189727575073 K at the high endpoint.
- V-polarized brightness temperature: 254.65700162755877 K at the low endpoint and 234.58530609436016 K at the high endpoint.

Both output arrays are recorded as monotonically decreasing. [model:tau_omega@1.0.0]

The selected chart was rendered, and its automatic render check passed. That check establishes that the plotted arrays were usable and legible; it does not establish agreement with the paper figure. [research-reporting#00]

No bias, RMSE, correlation, ratio, or percent-error result was supplied. These quantities are **not scoreable** for the CMEM comparison. [research-reporting#00]

## Comparison

| Aspect | Generated image | Recorded result | Assessment |
|---|---|---|---|
| Curve count | Two brightness-temperature curves are shown. | The result contains `tb_h` and `tb_v`. [model:tau_omega@1.0.0] | Agrees. |
| Ordering | V is above H. | V exceeds H at the recorded endpoints and remains the higher series. [model:tau_omega@1.0.0] | Same qualitative ordering. |
| Shape | Both curves decrease with soil moisture. | Both arrays are monotonically decreasing. [model:tau_omega@1.0.0] | Same qualitative pattern. |
| Quantitative reproduction | Source values are not digitized here. | No CMEM comparison statistic was calculated. [research-reporting#00] | Not identifiable. |

The principal qualification is model non-equivalence: the executed model is tau–omega, while the unavailable reference is CMEM. The fixed parameters and sweep settings were also not paper-explicit in the authoritative ledger. [research-planning#00]

## Guessed/assumed parameters

The authoritative ledger classifies frequency and incidence angle as `paper_inferred` but records both values as `None`. Soil moisture is classified as `backend_default`. The remaining fixed physical inputs are also `backend_default`, while the sweep definition is `model_assumption`. These classifications are preserved in the appendix below.

## Limitations

The run establishes the behavior of the supported tau–omega configuration only. It does not establish CMEM parameter fidelity, a numerical match to the source, or validation against measurements. The frequency and incidence-angle values are not identifiable from the authoritative ledger, and no compatible CMEM result is available. [research-reporting#00]

## Final conclusion

The approved run produces decreasing H- and V-polarized brightness temperatures with increasing soil moisture, with V consistently higher than H. This reproduces the target sensitivity qualitatively, but the CMEM result itself remains not identifiable; the calibrated outcome is therefore **partial**, not quantitative reproduction. [model:tau_omega@1.0.0] [cmem-sampling-density#fig-fig09]

<parameter_provenance>
[{"field":"frequency_ghz","value":null,"source_kind":"paper","source_ref":"cmem-sampling-density#03","source_span":"Reference context only; no explicit value recorded","reason":"The authoritative ledger records no executable value.","sensitivity_checked":false},{"field":"angle_deg","value":null,"source_kind":"paper","source_ref":"cmem-sampling-density#06","source_span":"Reference context only; no explicit value recorded","reason":"The authoritative ledger records no executable value.","sensitivity_checked":false},{"field":"soil_moisture","value":"paper-relevant interval approximately 0.15–0.50 cm3 cm-3","source_kind":"model_default","source_ref":"cmem-sampling-density#fig09","source_span":"Paper-relevant interval used as comparison context","reason":"The submitted experiment differs from the paper condition; the paper value remains comparison context.","sensitivity_checked":true},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"model_default","source_ref":"registered model parameter resolution","source_span":"","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"soil_temperature_k","value":293.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","source_span":"","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","source_span":"","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.3,"source_kind":"model_default","source_ref":"registered model parameter resolution","source_span":"","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.05,"source_kind":"model_default","source_ref":"registered model parameter resolution","source_span":"","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"model_default","source_ref":"registered model parameter resolution","source_span":"","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","source_span":"","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"soil_moisture","source_kind":"assumption","source_ref":"approved research plan","source_span":"","reason":"The submitted run retained this parameter as the sensitivity axis without attached paper or user evidence.","sensitivity_checked":true},{"field":"sweep_start","value":0.15,"source_kind":"assumption","source_ref":"approved research plan","source_span":"","reason":"The submitted run retained this sweep lower bound without attached paper or user evidence.","sensitivity_checked":true},{"field":"sweep_stop","value":0.5,"source_kind":"assumption","source_ref":"approved research plan","source_span":"","reason":"The submitted run retained this sweep upper bound without attached paper or user evidence.","sensitivity_checked":true},{"field":"sweep_points","value":20,"source_kind":"assumption","source_ref":"approved research plan","source_span":"","reason":"The submitted run retained this sweep resolution without attached paper or user evidence.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| tau_omega | frequency_ghz |  | paper_inferred | cmem-sampling-density#03 |
| tau_omega | angle_deg |  | paper_inferred | cmem-sampling-density#06 |
| tau_omega | soil_moisture | paper-relevant interval approximately 0.15–0.50 cm3 cm-3 | backend_default | cmem-sampling-density#fig09 |
| tau_omega | bulk_density_g_cm3 | 1.3 | backend_default | - |
| tau_omega | soil_temperature_k | 293.0 | backend_default | - |
| tau_omega | canopy_temperature_k | 293.0 | backend_default | - |
| tau_omega | vegetation_optical_depth | 0.3 | backend_default | - |
| tau_omega | single_scattering_albedo | 0.05 | backend_default | - |
| tau_omega | roughness_h | 0.3 | backend_default | - |
| tau_omega | cross_q | 0.0 | backend_default | - |
| tau_omega | sweep_parameter | soil_moisture | model_assumption | - |
| tau_omega | sweep_start | 0.15 | model_assumption | - |
| tau_omega | sweep_stop | 0.5 | model_assumption | - |
| tau_omega | sweep_points | 20 | model_assumption | - |
