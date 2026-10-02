# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show a clear local vegetation-water sensitivity: as vegetation water content increases from **0 to 8 kg m⁻²**, total backscatter increases monotonically, while two-way transmissivity decreases monotonically. The soil-backscatter curve remains constant because soil parameters were held fixed [model:water_cloud@1.0.0].

This is a **partial reproduction**, not a reproduction of the paper’s Water Cloud Model result. The registered local model produced usable figures, but the paper’s reference Water Cloud Model was unavailable, so numerical equivalence to the source Figure 11 is not identifiable [backscatter-forward-operator#12] [figure:backscatter-forward-operator#fig11].

## Conclusion supported by the generated figures

Figure 1 contains three backscatter series over vegetation water content from 0 to 8 kg m⁻²:

- Total backscatter
- Soil backscatter
- Vegetation backscatter

Figure 2 contains the corresponding two-way transmissivity diagnostic. Both figures rendered successfully and were legible; this establishes chart usability, not agreement with the source figure [model:water_cloud@1.0.0].

## Conclusion supported by result arrays

The recorded arrays show:

- Total backscatter: **−14.5 to −2.7879 dB**, monotonically increasing.
- Soil backscatter: **−14.5 dB throughout the sweep**.
- Vegetation backscatter: **−60.0 to −2.8144 dB**, monotonically increasing.
- Two-way transmissivity: **1.0000 to 0.0903**, monotonically decreasing.
- Baseline at 1.0 kg m⁻²: total backscatter **−13.4748 dB** and transmissivity **0.7404** [model:water_cloud@1.0.0].

## Image and array comparison

| Aspect | Generated figures | Source comparison |
|---|---|---|
| Curves and grouping | Three backscatter components and one transmissivity diagnostic are shown | Not scoreable against the paper model |
| Axes and units | Vegetation water content in kg m⁻²; backscatter in dB; transmissivity dimensionless | The source Figure 11 is the paper target [figure:backscatter-forward-operator#fig11] |
| Ordering and shape | Backscatter increases with vegetation water; transmissivity decreases | Qualitative reproduction is not claimed because the required reference model is unavailable |
| Numerical agreement | Recorded model values are available | Bias, RMSE, correlation, and percent error: **N/A** |
| Qualification | The soil series is constant by construction; the vegetation curve has an abrupt change between 0 and 0.5 kg m⁻² | These are local-model diagnostics, not evidence of paper-model agreement |

## Assumed parameters

The following values were guessed, assumed, or supplied by the registered model rather than transferred from a paper calibration:

- `angle_deg = 37.0`: model assumption; fixed local condition.
- `soil_moisture = 0.25`: model assumption; fixed local condition.
- `vegetation_water_kg_m2 = 0 to 8`: user-specified independent sweep variable.
- `coefficient_a = 0.09`: backend default; not paper calibration.
- `coefficient_b = 0.12`: backend default; not paper calibration.
- `coefficient_c = -22.0`: backend default; not paper calibration.
- `coefficient_d = 30.0`: backend default; not paper calibration.
- `sweep_parameter = none`: backend default for the baseline run.
- `sweep_points = 10`: backend default retained in the baseline specification.
- `sweep_start = 0.0`: model assumption; no paper or user evidence was attached.
- `sweep_stop = 8.0`: model assumption; no paper or user evidence was attached.

## Limitations

The result is limited to the registered `water_cloud@1.0.0` implementation and its fixed local parameters. The unavailable paper Water Cloud Model prevents a formal model-to-model reproduction. The figures therefore support a local sensitivity conclusion, not a claim that the paper’s Figure 11 was numerically reproduced. This reporting follows the recorded-result and provenance requirements [skill:research-reporting].

<parameter_provenance>
[{"field":"angle_deg","value":37.0,"source_kind":"assumption","source_ref":"Fixed local condition; not a transferred paper value","reason":"Model-assumption incidence angle used in the approved local run","sensitivity_checked":false},{"field":"soil_moisture","value":0.25,"source_kind":"assumption","source_ref":"Fixed local condition; not a transferred paper calibration","reason":"Model-assumption soil moisture used in the approved local run","sensitivity_checked":false},{"field":"vegetation_water_kg_m2","value":"0 to 8","source_kind":"user","source_ref":"Independent sweep variable","reason":"User-specified sensitivity range","sensitivity_checked":true},{"field":"coefficient_a","value":0.09,"source_kind":"model_default","source_ref":"Registered local default, not paper calibration","reason":"Backend default vegetation scattering coefficient","sensitivity_checked":false},{"field":"coefficient_b","value":0.12,"source_kind":"model_default","source_ref":"Registered local default, not paper calibration","reason":"Backend default vegetation attenuation coefficient","sensitivity_checked":false},{"field":"coefficient_c","value":-22.0,"source_kind":"model_default","source_ref":"Registered local default, not paper calibration","reason":"Backend default soil backscatter intercept","sensitivity_checked":false},{"field":"coefficient_d","value":30.0,"source_kind":"model_default","source_ref":"Registered local default, not paper calibration","reason":"Backend default soil-moisture backscatter sensitivity","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"The registered model inserted this value during parameter resolution; it is not paper evidence","reason":"Baseline run used no sweep parameter","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"The registered model inserted this value during parameter resolution; it is not paper evidence","reason":"Baseline specification retained the registered default","sensitivity_checked":false},{"field":"sweep_start","value":0.0,"source_kind":"assumption","source_ref":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review","reason":"Lower endpoint of the approved local sweep","sensitivity_checked":false},{"field":"sweep_stop","value":8.0,"source_kind":"assumption","source_ref":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review","reason":"Upper endpoint of the approved local sweep","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
