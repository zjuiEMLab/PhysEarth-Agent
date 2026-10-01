# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show a clear, monotonic vegetation-water sensitivity: as vegetation water increases from **0 to 8 kg m⁻²**, total and vegetation backscatter increase, while two-way transmissivity decreases. The soil-backscatter curve remains ordered as a constant baseline. Both figures rendered and passed manual review, so the supported qualitative pattern is reproduced.

This is a **partial reproduction** of the paper result. The figures demonstrate the registered model’s scalar vegetation-water response, but they do not reproduce the unavailable calibrated KGE/J formulation or polarization-specific VV/VH time series.

## Conclusion supported by the generated images

Figure 1 contains three backscatter series over vegetation water, in dB. It shows:

- Increasing total backscatter.
- Increasing vegetation backscatter.
- A constant soil-backscatter component.
- A visible endpoint change in the vegetation series between 0 and 0.5 kg m⁻², noted during chart review.

Figure 2 contains one transmissivity series. It shows decreasing two-way transmissivity with increasing vegetation water. Both figures have the expected axes, units, series count, and rendered grouping, and both passed review.

The image-based conclusion is therefore: **the same qualitative vegetation-water sensitivity pattern is present in the generated figures, but visual review does not establish numerical agreement with the paper.**

## Supporting results from the model arrays

The baseline run produced:

- Total backscatter: **−13.4748 dB**
- Soil backscatter: **−14.5000 dB**
- Vegetation backscatter: **−17.2917 dB**
- Two-way transmissivity: **0.7404**

The sweep produced the following endpoint results:

| Quantity | At 0 kg m⁻² | At 8 kg m⁻² | Recorded pattern |
|---|---:|---:|---|
| Total backscatter | −14.5000 dB | −2.7879 dB | Increasing |
| Vegetation backscatter | −60.0000 dB | −2.8144 dB | Increasing |
| Soil backscatter | −14.5000 dB | −14.5000 dB | Constant |
| Two-way transmissivity | 1.0000 | 0.0903 | Decreasing |

These values are outputs of the registered Water Cloud model, not measurements or values digitized from the paper [model:water_cloud@1.0.0]. No bias, RMSE, correlation, or other numerical agreement statistic was supplied; numerical agreement with the paper is therefore **not scoreable**.

## Image-versus-array comparison

| Aspect | Generated-image conclusion | Array-supported conclusion | Assessment |
|---|---|---|---|
| Backscatter ordering | Soil is a constant baseline; total and vegetation curves rise | Soil remains −14.5 dB; total and vegetation increase | Agreement |
| Transmissivity | Curve decreases with vegetation water | 1.0000 to 0.0903 | Agreement |
| Endpoint behaviour | Vegetation curve has an abrupt low-end change | The change occurs between 0 and 0.5 kg m⁻² | Agreement |
| Numerical agreement with paper | Not established by the image | No paper-to-model error statistic supplied | Not scoreable |
| Full paper reproduction | Not shown by these figures | Required calibrated and polarization-specific outputs were unavailable | Partial only |

The source paper describes the Water Cloud backscatter formulation and its calibration context [backscatter-forward-operator#04] [backscatter-forward-operator#05] [backscatter-forward-operator#12]. The generated figures support the scalar sensitivity result, but not the unavailable calibrated or polarization-specific comparison.

## Guessed/assumed parameters

The following values are not paper-explicit:

- `angle_deg = 37`: provenance **model_assumption**; the exact paper time-varying configuration was unavailable.
- `soil_moisture = 0.25`: provenance **model_assumption**; held fixed to isolate vegetation-water response.
- `vegetation_water_kg_m2 = 1` for the baseline and **0–8** for the sweep: provenance **user_specified**; used to isolate the supported sensitivity.
- `coefficient_a = 0.09`: provenance **backend_default**; paper calibration unavailable.
- `coefficient_b = 0.12`: provenance **backend_default**; paper calibration unavailable.
- `coefficient_c = −22`: provenance **backend_default**; paper calibration unavailable.
- `coefficient_d = 30`: provenance **backend_default**; paper calibration unavailable.
- `sweep_parameter = none` for the baseline: provenance **backend_default**.
- `sweep_points = 10` for the baseline: provenance **backend_default**.
- `sweep_start = 0.0`: provenance **model_assumption**; retained for the submitted sweep without attached paper or user evidence.
- `sweep_stop = 8.0`: provenance **model_assumption**; retained for the submitted sweep without attached paper or user evidence.

## Limitations and final conclusion

The registered model successfully generated and reviewed both planned figures. They show the requested qualitative comparison: vegetation water increases modeled backscatter and decreases modeled transmissivity, while the soil component remains fixed. The result is **partial**, because the paper’s calibrated KGE/J model and VV/VH time series were unavailable; consequently, full numerical or polarization-specific reproduction is not identifiable from this execution.

<parameter_provenance>
[{"field":"angle_deg","value":37,"source_kind":"assumption","source_ref":"Exact paper time-varying configuration unavailable","reason":"Fixed incidence angle used in the approved run","sensitivity_checked":false},{"field":"soil_moisture","value":0.25,"source_kind":"assumption","source_ref":"Held fixed to isolate vegetation-water response","reason":"Fixed soil moisture used in the approved run","sensitivity_checked":false},{"field":"vegetation_water_kg_m2","value":"baseline 1; sweep 0-8","source_kind":"user","source_ref":"Supported vegetation-water sensitivity selected in the approved plan","reason":"Baseline and sweep variable","sensitivity_checked":true},{"field":"coefficient_a","value":0.09,"source_kind":"model_default","source_ref":"Paper calibration unavailable; registered model default","reason":"Default vegetation scattering coefficient","sensitivity_checked":false},{"field":"coefficient_b","value":0.12,"source_kind":"model_default","source_ref":"Paper calibration unavailable; registered model default","reason":"Default vegetation attenuation coefficient","sensitivity_checked":false},{"field":"coefficient_c","value":-22,"source_kind":"model_default","source_ref":"Paper calibration unavailable; registered model default","reason":"Default soil-backscatter intercept","sensitivity_checked":false},{"field":"coefficient_d","value":30,"source_kind":"model_default","source_ref":"Paper calibration unavailable; registered model default","reason":"Default soil-moisture sensitivity coefficient","sensitivity_checked":false},{"field":"sweep_parameter","value":"none for baseline; vegetation_water_kg_m2 for sweep","source_kind":"model_default","source_ref":"Registered model parameter resolution and approved sweep specification","reason":"Baseline is unswept; second run sweeps vegetation water","sensitivity_checked":true},{"field":"sweep_points","value":"10 for baseline; 17 for vegetation-water sweep","source_kind":"model_default","source_ref":"Registered run specifications","reason":"Point counts used by the approved runs","sensitivity_checked":true},{"field":"sweep_start","value":0.0,"source_kind":"assumption","source_ref":"Submitted sweep retained this value without attached paper or user evidence","reason":"Lower bound of the approved vegetation-water sweep","sensitivity_checked":true},{"field":"sweep_stop","value":8.0,"source_kind":"assumption","source_ref":"Submitted sweep retained this value without attached paper or user evidence","reason":"Upper bound of the approved vegetation-water sweep","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
