# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show two monotonic, downward-sloping tau-omega brightness-temperature curves as soil moisture increases: the V-polarized curve remains above the H-polarized curve throughout the sweep. This is the same qualitative soil-moisture sensitivity pattern represented by the source Figure 9, but it is not a quantitative reproduction of CMEM because CMEM was unavailable. [cmem-sampling-density#fig-fig09] [model:tau_omega@1.0.0]

The reproduction outcome is therefore **partial**. Both approved figures were rendered successfully, with one series each, but direct CMEM comparison and associated agreement statistics are not identifiable.

## Supporting results

The generated figures are:

- **Figure 1:** Tau-omega H-polarized brightness temperature; soil moisture versus brightness temperature (K).
- **Figure 2:** Tau-omega V-polarized brightness temperature; soil moisture versus brightness temperature (K).

The executed tau-omega run used 51 soil-moisture points from **0.01 to 0.6**. H-polarized brightness temperature decreased from **247.7603316371689 K** to **148.6866773514669 K**. V-polarized brightness temperature decreased from **277.7138183794178 K** to **185.1768689420164 K**. [model:tau_omega@1.0.0]

The result arrays show monotonic decrease for both polarizations, with V polarization higher than H polarization at both ends and throughout the recorded sweep. No RMSE, bias, correlation, or other model-to-CMEM statistic was supplied; quantitative agreement is **not scoreable**.

## Source/generated-image conclusion

The source figure presents a soil-moisture sensitivity experiment in a CMEM comparison context. [cmem-sampling-density#02] [cmem-sampling-density#03] [cmem-sampling-density#06] [cmem-sampling-density#fig-fig09]

The generated images contain the expected two polarization-specific tau-omega outputs as separate figures. Their axes, units, series counts, ordering, and decreasing shape are clear. The generated figures should therefore be regarded as a qualitative tau-omega reproduction of the sensitivity pattern, not as evidence that tau-omega numerically reproduces CMEM.

## Comparison

| Aspect | Source/generated-image reading | Actual result-array reading | Assessment |
|---|---|---|---|
| Soil-moisture response | The source presents brightness-temperature sensitivity to soil moisture. [cmem-sampling-density#fig-fig09] | Both tau-omega outputs decrease monotonically over **0.01 to 0.6** soil moisture. [model:tau_omega@1.0.0] | Same qualitative pattern. |
| Polarization ordering | The generated figures provide separate H and V curves. | V remains above H throughout the returned array. [model:tau_omega@1.0.0] | Ordering is supported for tau-omega only. |
| Numerical agreement with CMEM | The source comparison context is CMEM-based. [cmem-sampling-density#06] | CMEM was unavailable and was not run. | Not identifiable; no validation statistic is available. |
| Rendering | Both selected figures were rendered and passed the automatic legibility check. | Each contains 51 plotted points. | The charts are usable; this does not establish source-figure agreement. |

## Assumed parameters

The authoritative ledger classifies frequency, incidence angle, soil temperature, and vegetation optical depth as **user_specified**, the soil-moisture base value as **backend_default**, and bulk density, canopy temperature, single-scattering albedo, roughness, cross-polarization, and all sweep-construction fields as **model_assumption**.

The recorded configuration values were frequency **1.4 GHz**, incidence angle **40.0 degrees**, soil-moisture base value **0.25** with a sweep from **0.01** to **0.6** using **51** points, soil temperature **293.15 K**, vegetation optical depth **0.0**, bulk density **1.3 g cm⁻³**, canopy temperature **293.15 K**, single-scattering albedo **0.0**, roughness **0.5**, cross-polarization **0.0**, and the sweep parameter **soil_moisture**. [model:tau_omega@1.0.0]

## Limitations

The submitted tau-omega configuration differs from the paper comparison condition, and the ledger contains no paper-explicit numerical value for the mapped frequency, angle, soil moisture, soil temperature, or vegetation condition. CMEM was unavailable, so the requested model-to-CMEM comparison is not identifiable. The result supports the direction and polarization ordering of the generated tau-omega sensitivity curves, but not quantitative reproduction of the paper’s CMEM result.

<parameter_provenance>
[{"field":"frequency_ghz","value":1.4,"source_kind":"user","source_ref":"cmem-sampling-density#06; submitted experiment differs from paper condition","reason":"User-specified run configuration","sensitivity_checked":false},{"field":"angle_deg","value":40.0,"source_kind":"user","source_ref":"cmem-sampling-density#fig09; submitted experiment differs from paper condition","reason":"User-specified run configuration","sensitivity_checked":false},{"field":"soil_moisture","value":{"base":0.25,"sweep_start":0.01,"sweep_stop":0.6,"sweep_points":51},"source_kind":"model_default","source_ref":"cmem-sampling-density#fig09; submitted experiment differs from paper condition","reason":"Backend-default base value with the approved soil-moisture sweep","sensitivity_checked":false},{"field":"soil_temperature_k","value":293.15,"source_kind":"user","source_ref":"cmem-sampling-density#03; submitted experiment differs from paper condition","reason":"User-specified run configuration","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.0,"source_kind":"user","source_ref":"cmem-sampling-density#06; submitted experiment differs from paper condition","reason":"User-specified vegetation condition","sensitivity_checked":false},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"no paper or user evidence recorded","reason":"Retained model assumption","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.15,"source_kind":"assumption","source_ref":"no paper or user evidence recorded","reason":"Retained model assumption","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.0,"source_kind":"assumption","source_ref":"no paper or user evidence recorded","reason":"Retained model assumption","sensitivity_checked":false},{"field":"roughness_h","value":0.5,"source_kind":"assumption","source_ref":"no paper or user evidence recorded","reason":"Retained model assumption","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"assumption","source_ref":"no paper or user evidence recorded","reason":"Retained model assumption","sensitivity_checked":false},{"field":"sweep_parameter","value":"soil_moisture","source_kind":"assumption","source_ref":"no paper or user evidence recorded","reason":"Approved sweep design","sensitivity_checked":false},{"field":"sweep_start","value":0.01,"source_kind":"assumption","source_ref":"no paper or user evidence recorded","reason":"Approved sweep lower bound","sensitivity_checked":false},{"field":"sweep_stop","value":0.6,"source_kind":"assumption","source_ref":"no paper or user evidence recorded","reason":"Approved sweep upper bound","sensitivity_checked":false},{"field":"sweep_points","value":51,"source_kind":"assumption","source_ref":"no paper or user evidence recorded","reason":"Approved sweep resolution","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| tau_omega | frequency_ghz | Figure 9 frequency | user_specified | cmem-sampling-density#06 |
| tau_omega | angle_deg | Figure 9 incidence angle | user_specified | cmem-sampling-density#fig09 |
| tau_omega | soil_moisture | Figure 9 soil-moisture range | backend_default | cmem-sampling-density#fig09 |
| tau_omega | soil_temperature_k | Figure 9 soil temperature | user_specified | cmem-sampling-density#03 |
| tau_omega | vegetation_optical_depth | Figure 9 vegetation condition | user_specified | cmem-sampling-density#06 |
| tau_omega | bulk_density_g_cm3 | 1.3 | model_assumption | - |
| tau_omega | canopy_temperature_k | 293.15 | model_assumption | - |
| tau_omega | single_scattering_albedo | 0.0 | model_assumption | - |
| tau_omega | roughness_h | 0.5 | model_assumption | - |
| tau_omega | cross_q | 0.0 | model_assumption | - |
| tau_omega | sweep_parameter | soil_moisture | model_assumption | - |
| tau_omega | sweep_start | 0.01 | model_assumption | - |
| tau_omega | sweep_stop | 0.6 | model_assumption | - |
| tau_omega | sweep_points | 51 | model_assumption | - |
