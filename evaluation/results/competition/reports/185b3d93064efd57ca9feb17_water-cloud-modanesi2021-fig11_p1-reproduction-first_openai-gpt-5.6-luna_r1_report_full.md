# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show monotonic component behavior, not convergence between model formulations or reproduction of the paper’s VV/VH Sentinel-1 time series. Total backscatter increases with both vegetation water content and soil moisture in the supported local Water Cloud runs. The figures therefore support a **partial reproduction only**: they demonstrate the registered model’s component sensitivities, but do not reproduce Figure 11’s calibrated VV/VH time series or KGE/J-based evaluation.

## Supporting results

Figure 1 contains three curves versus vegetation water content from 0–8 kg m⁻². Total backscatter increases from −14.5 to −2.7879 dB, while two-way transmissivity decreases from 1.0 to 0.09035. The soil component remains constant at −14.5 dB. [model:water_cloud@1.0.0]

Figure 2 contains three curves versus soil moisture from 0.05–0.55 m³ m⁻³. Total backscatter increases from −15.9764 to −6.4332 dB, and the soil component increases from −20.5 to −5.5 dB. The vegetation component remains constant at −17.2917 dB, and transmissivity remains 0.74044. [model:water_cloud@1.0.0]

The source paper’s Figure 11 concerns VV and VH Sentinel-1 time series and a calibrated Water Cloud Model evaluation [backscatter-forward-operator#11] [backscatter-forward-operator#12]. The generated figures use scalar supported components rather than those required time series, so numerical agreement, curve-by-curve correspondence, bias, RMSE, correlation, KGE, and J are **not scoreable**.

| Aspect | Source/generated-image conclusion | Result-array conclusion |
|---|---|---|
| Curves | Three supported backscatter components are plotted in each generated figure. | The recorded runs contain soil, vegetation, and total backscatter outputs. |
| Ordering and trend | The generated curves show increasing total backscatter with both sweep variables; transmissivity decreases with vegetation water content. | The recorded arrays confirm those monotonic endpoint changes. |
| Paper comparison | No claim of visual reproduction of Figure 11 is supported. | VV/VH time-series comparison and calibrated KGE/J assessment are unavailable. |
| Quantitative agreement | Not scoreable. | No source-aligned numerical comparison was supplied. |

The chart render checks passed, establishing that the generated arrays were finite, sufficiently sampled, and legible. This does not establish agreement with the source figure.

## Assumed parameters

The following values were assumptions or registered backend defaults, not paper-derived parameters:

- `angle_deg = 37`: model assumption; no paper evidence.
- `soil_moisture = 0.25`: model assumption; no paper evidence.
- `vegetation_water_kg_m2 = 1`: model assumption; no paper evidence.
- `coefficient_a = 0.09`, `coefficient_b = 0.12`, `coefficient_c = -22`, and `coefficient_d = 30`: backend defaults.
- `sweep_parameter = none`: model assumption in the baseline specification.
- `sweep_points = 10`: backend default in the baseline specification.
- `sweep_start = 0.0` and `sweep_stop = 8.0`: model assumptions associated with the vegetation-water sweep.

The principal limitations are the absence of the paper’s calibrated KGE/J procedure, the missing VV/VH Sentinel-1 time-series output, and the use of assumed rather than paper-explicit local input values. The requested full Figure 11 reproduction is therefore not identifiable from the recorded supported runs.

## Conclusion

The generated figures support a clear local-model conclusion: backscatter increases with vegetation water content and soil moisture under the approved conditions, while vegetation water reduces transmissivity. They do not support a full reproduction or quantitative validation of the paper’s Figure 11. The calibrated outcome is **partial**. [skill:research-reporting]

<parameter_provenance>
[
  {"field":"angle_deg","value":37,"source_kind":"assumption","source_ref":"none; registered input retained without paper evidence","reason":"The registered input was retained as a model assumption without paper evidence.","provenance_class":"model_assumption","sensitivity_checked":false},
  {"field":"soil_moisture","value":0.25,"source_kind":"assumption","source_ref":"none; registered input retained without paper evidence","reason":"The registered input was retained as a model assumption without paper evidence.","provenance_class":"model_assumption","sensitivity_checked":false},
  {"field":"vegetation_water_kg_m2","value":1,"source_kind":"assumption","source_ref":"none; registered input retained without paper evidence","reason":"The registered input was retained as a model assumption without paper evidence.","provenance_class":"model_assumption","sensitivity_checked":false},
  {"field":"coefficient_a","value":0.09,"source_kind":"model_default","source_ref":"registered backend default","reason":"The registered backend supplied this default; it is not paper evidence.","provenance_class":"backend_default","sensitivity_checked":false},
  {"field":"coefficient_b","value":0.12,"source_kind":"model_default","source_ref":"registered backend default","reason":"The registered backend supplied this default; it is not paper evidence.","provenance_class":"backend_default","sensitivity_checked":false},
  {"field":"coefficient_c","value":-22,"source_kind":"model_default","source_ref":"registered backend default","reason":"The registered backend supplied this default; it is not paper evidence.","provenance_class":"backend_default","sensitivity_checked":false},
  {"field":"coefficient_d","value":30,"source_kind":"model_default","source_ref":"registered backend default","reason":"The registered backend supplied this default; it is not paper evidence.","provenance_class":"backend_default","sensitivity_checked":false},
  {"field":"sweep_parameter","value":"none","source_kind":"assumption","source_ref":"none; submitted baseline run specification","reason":"The submitted run retained this value without attached paper or user evidence.","provenance_class":"model_assumption","sensitivity_checked":false},
  {"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"registered backend parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","provenance_class":"backend_default","sensitivity_checked":false},
  {"field":"sweep_start","value":0.0,"source_kind":"assumption","source_ref":"none; submitted vegetation-water sweep specification","reason":"The submitted run retained this value without attached paper or user evidence.","provenance_class":"model_assumption","sensitivity_checked":false},
  {"field":"sweep_stop","value":8.0,"source_kind":"assumption","source_ref":"none; submitted vegetation-water sweep specification","reason":"The submitted run retained this value without attached paper or user evidence.","provenance_class":"model_assumption","sensitivity_checked":false}
]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
