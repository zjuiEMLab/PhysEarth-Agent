# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows a legal-boundary diagnostic, not an executable result at the requested density of **2000 kg m⁻³**. The generated curves remain ordered with **V-polarized brightness temperature above H-polarized brightness temperature** across the plotted density range, while both curves rise and then decline near the upper boundary. The requested 2000 kg m⁻³ value lies outside the registered model range, so the original configuration is only partially identifiable. [model:smrt@1.5.1]

The formal run successfully evaluated **1–917 kg m⁻³** at 37 GHz, using 10 density points. The chart rendered and passed the automatic legibility check. No source-paper figure or source-image comparison was recorded; therefore, no claim of visual reproduction against a paper figure is made.

## Supporting results

### Conclusion supported by the generated image

The generated figure contains two curves on axes of snow density (kg m⁻³) and brightness temperature (K). It shows:

- two polarization series, H and V;
- V above H throughout the plotted range;
- increasing brightness temperature through intermediate densities;
- a turnover and decline toward 917 kg m⁻³;
- no plotted point at 2000 kg m⁻³.

The figure establishes these qualitative patterns, but it does not independently provide digitized values or demonstrate agreement with a source figure.

### Conclusion supported by the result arrays

The recorded arrays give the following ranges:

- **V polarization:** 0.3807–203.4450 K;
- **H polarization:** 0.3793–164.6854 K.

Both series were recorded as non-monotonic over the full density sweep. At the legal upper endpoint, 917 kg m⁻³, the outputs were **199.2696 K** for V and **156.2760 K** for H. [model:smrt@1.5.1]

## Comparison and qualification

| Aspect | Generated figure | Recorded arrays |
|---|---|---|
| Series | H and V curves | H and V outputs |
| Ordering | V visibly above H | V exceeds H at the recorded points |
| Shape | Rise followed by turnover and decline | Both series recorded as non-monotonic |
| Requested density | Not plotted at 2000 kg m⁻³ | Not executable; legal endpoint was 917 kg m⁻³ |
| Numerical agreement with a source | Not assessed | Not scoreable; no source data comparison was supplied |

The image-level and array-level conclusions agree qualitatively. The result remains a boundary validation rather than a reproduction of the requested 2000 kg m⁻³ configuration. The passed render check establishes that the plotted arrays were usable and legible; it does not establish source-figure agreement.

## Assumed/guessed parameters

The following parameters were not supported by paper evidence and were retained as defaults or run assumptions:

- `electromagnetic_model = iba` — backend default.
- `microstructure_model = exponential` — backend default.
- `angle_deg = 55` — backend default.
- `temperature_k = 265` — backend default.
- `corr_length_m = 0.00015` — backend default.
- `dort_streams = 32` — backend default.
- `radius_m = 0.0002` — backend default inserted during parameter resolution.
- `stickiness = 0.2` — backend default inserted during parameter resolution.
- `sweep_parameter = density_kg_m3` — model assumption.
- `sweep_start = 1.0` — model assumption.
- `sweep_stop = 917.0` — model assumption.
- `sweep_points = 10` — model assumption.

The requested `density_kg_m3 = 2000` remains a user-specified context value, but it was not used in the executable run because it exceeded the registered SMRT range. [model:smrt@1.5.1]

## Limitations

The evaluation did not run a model at 2000 kg m⁻³, did not compare against measured data, and did not compute bias, RMSE, correlation, or other validation statistics. These quantities are therefore **not scoreable**. The conclusion is limited to the registered legal density range and the selected default model configuration.

<parameter_provenance>
[{"field":"frequency_ghz","value":"37","source_kind":"user","source_ref":"User-fixed sensor frequency","reason":"User-fixed sensor frequency.","sensitivity_checked":false},{"field":"thickness_m","value":"1","source_kind":"user","source_ref":"User-fixed layer thickness","reason":"User-fixed layer thickness.","sensitivity_checked":false},{"field":"density_kg_m3","value":"917.0; requested context value 2000","source_kind":"user","source_ref":"The requested value is retained as context but cannot be used in an executable registered-model run.","reason":"The approved executable run used the legal upper boundary of 917 kg m-3 rather than the unsupported requested value.","sensitivity_checked":false},{"field":"output","value":"tb","source_kind":"user","source_ref":"User requested passive brightness temperature","reason":"User requested passive brightness temperature.","sensitivity_checked":false},{"field":"electromagnetic_model","value":"iba","source_kind":"backend_default","source_ref":"Backend default retained for the legal-boundary diagnostic","reason":"Backend default retained.","sensitivity_checked":false},{"field":"microstructure_model","value":"exponential","source_kind":"backend_default","source_ref":"Backend default retained for the legal-boundary diagnostic","reason":"Backend default retained.","sensitivity_checked":false},{"field":"angle_deg","value":"55","source_kind":"backend_default","source_ref":"Backend default retained for the legal-boundary diagnostic","reason":"Backend default retained.","sensitivity_checked":false},{"field":"temperature_k","value":"265","source_kind":"backend_default","source_ref":"Backend default retained for the legal-boundary diagnostic","reason":"Backend default retained.","sensitivity_checked":false},{"field":"corr_length_m","value":"0.00015","source_kind":"backend_default","source_ref":"Backend default retained for the legal-boundary diagnostic","reason":"Backend default retained.","sensitivity_checked":false},{"field":"dort_streams","value":"32","source_kind":"backend_default","source_ref":"Registered numerical-resolution default","reason":"Registered numerical-resolution default.","sensitivity_checked":false},{"field":"radius_m","value":"0.0002","source_kind":"backend_default","source_ref":"The registered model inserted this value during parameter resolution; it is not paper evidence.","reason":"Backend-inserted default.","sensitivity_checked":false},{"field":"stickiness","value":"0.2","source_kind":"backend_default","source_ref":"The registered model inserted this value during parameter resolution; it is not paper evidence.","reason":"Backend-inserted default.","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"assumption","source_ref":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","reason":"Density sweep used for the legal-boundary diagnostic.","sensitivity_checked":false},{"field":"sweep_start","value":"1.0","source_kind":"assumption","source_ref":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","reason":"Lower endpoint used for the legal-boundary diagnostic.","sensitivity_checked":false},{"field":"sweep_stop","value":"917.0","source_kind":"assumption","source_ref":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","reason":"Upper legal endpoint used for the diagnostic.","sensitivity_checked":false},{"field":"sweep_points","value":"10","source_kind":"assumption","source_ref":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","reason":"Number of points in the approved diagnostic sweep.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
