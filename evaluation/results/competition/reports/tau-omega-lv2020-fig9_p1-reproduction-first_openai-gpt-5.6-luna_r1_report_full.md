# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 shows two ordered, smoothly decreasing brightness-temperature curves over soil moisture from 0.05 to 0.50 m³ m⁻³. The V-polarized curve remains above the H-polarized curve throughout. The result supports a monotonic decrease in simulated L-band brightness temperature with increasing soil moisture under the approved tau–omega assumptions. [model:tau_omega@1.0.0]

This is a **partial qualitative reproduction**, not a reproduction of the unavailable CMEM–TerrSysMP coupled experiment. The generated figure was rendered successfully and passed the automated legibility check, but that check does not establish numerical agreement with the source figure.

## Source-image conclusion

The source target was Figure 9 of the CMEM sampling-density study. [figure:cmem-sampling-density#fig09] The available evidence identifies the paper’s CMEM-based sampling and brightness-temperature context, but the recorded state does not provide digitized source-curve values or a numerical comparison. [cmem-sampling-density#07]

Accordingly, source-to-generated numerical agreement is **not scoreable**. The reproduction outcome remains partial because the coupled reference environment was unavailable.

## Result-handle conclusion

The baseline run produced:

- \(T_{b,H}=224.804\) K
- \(T_{b,V}=246.436\) K
- \(e_H=0.5372\)
- \(e_V=0.6950\)

Across the soil-moisture sweep:

- H polarization decreased from **248.129 K** at 0.05 m³ m⁻³ to **214.762 K** at 0.50 m³ m⁻³.
- V polarization decreased from **268.966 K** to **234.585 K** over the same range.
- Both responses were monotonic decreasing. [model:tau_omega@1.0.0]

## Comparison

| Aspect | Generated result | Source/reproduction status |
|---|---|---|
| Curves | Two polarization curves | Required CMEM–TerrSysMP comparison unavailable |
| Axis quantities | Soil moisture and brightness temperature | Consistent with the approved analogue |
| Units | m³ m⁻³ and K | Recorded in Figure 1 |
| Ordering | V above H throughout | No digitized source values available |
| Numerical agreement | Not calculated | N/A; no source data artifact |
| Outcome | Successful model execution | Partial reproduction |

## Assumed parameters

The following ledger entries were assumptions rather than paper-explicit values: frequency 1.41 GHz, incidence angle 40°, baseline soil moisture 0.25 m³ m⁻³, bulk density 1.3 g cm⁻³, soil and canopy temperatures of 293 K, vegetation optical depth 0.3, single-scattering albedo 0.05, roughness \(h=0.3\), cross-polarization parameter \(Q=0\), and sweep bounds of 0.05–0.50 m³ m⁻³. The registered-model defaults were used for `sweep_parameter` and `sweep_points` where applicable. [model:tau_omega@1.0.0]

## Limitations

The result is not a measurement and was not validated against a reference dataset. The unavailable CMEM coupled to TerrSysMP virtual-reality experiment prevents a full reproduction. No bias, RMSE, correlation, or source-curve digitization was supplied, so numerical similarity is not identifiable. The automated render check establishes only that the generated curves are finite, dense enough, and legible.

<parameter_provenance>
[{"field":"frequency_ghz","value":1.41,"source_kind":"assumption","source_ref":"Approved tau-omega partial analogue; paper evidence cmem-sampling-density#07","reason":"The tau-omega model returns tb_h and tb_v; no output-selection parameter is declared, and this frequency was retained as a model assumption.","sensitivity_checked":false},{"field":"angle_deg","value":40.0,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption value.","sensitivity_checked":false},{"field":"soil_moisture","value":0.25,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Baseline value retained while soil moisture was swept in the sensitivity run.","sensitivity_checked":true},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption value.","sensitivity_checked":false},{"field":"soil_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption value.","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption value.","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.3,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption value.","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.05,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption value.","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption value.","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption value.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"Registered tau-omega model parameter resolution","reason":"Backend inserted the default for the baseline run; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"Registered tau-omega model parameter resolution","reason":"Backend inserted the default value; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_start","value":0.05,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption lower bound for the sensitivity sweep.","sensitivity_checked":true},{"field":"sweep_stop","value":0.5,"source_kind":"assumption","source_ref":"No paper or user value attached in the approved run ledger","reason":"Submitted run retained this model-assumption upper bound for the sensitivity sweep.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
