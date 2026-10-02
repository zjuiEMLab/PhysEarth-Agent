# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows two distinct brightness-temperature curves over the legal snow-density range of 50–917 kg m⁻³. V polarization remains above H polarization, and both curves rise through most of the range before turning downward near the highest densities; they do not converge. The run therefore provides a legal-density diagnostic, not an exact reproduction of the paper condition at 2000 kg m⁻³. [model:smrt@1.5.1]

The requested 2000 kg m⁻³ condition is not identifiable from this run because it lies beyond the executed range. The calibrated outcome is therefore **partial**.

## Conclusion supported by the generated figure

The generated figure contains two series with density on the x-axis in kg m⁻³ and brightness temperature on the y-axis in K. It shows:

- two separated polarization curves;
- V-polarized brightness temperature above H-polarized brightness temperature across the plotted range;
- increasing brightness temperature through intermediate densities;
- a downturn near the upper-density boundary.

No source-paper figure comparison was recorded for this run, so the figure supports these generated-curve conclusions only. The passed render check establishes that the plotted arrays were finite, sufficiently populated, and legible; it does not establish agreement with the source figure.

## Conclusion supported by the result arrays

The executed sweep used 10 density points from 50.0 to 917.0 kg m⁻³. V-polarized brightness temperature ranged from 21.7003 to a maximum of 203.3855 K; H-polarized brightness temperature ranged from 20.1491 to a maximum of 164.9813 K. At the final density, 917.0 kg m⁻³, the values were 199.2696 K for V polarization and 156.2760 K for H polarization. [model:smrt@1.5.1]

The recorded arrays describe both series as non-monotonic. No bias, RMSE, correlation, or other numerical comparison with paper data was supplied; such metrics are **not scoreable**.

## Comparison of image-supported and array-supported conclusions

| Aspect | Generated image | Result arrays |
|---|---|---|
| Curves | Two separated curves | Two polarization series |
| Ordering | V visibly above H | V maximum and endpoint both exceed H |
| Shape | Rise followed by upper-range downturn | Both series recorded as non-monotonic |
| Convergence | No visible convergence | No convergence statistic was calculated |
| Paper agreement | Not assessed | Not scoreable |
| Exact target | Not shown | 2000 kg m⁻³ was not run |

The image and arrays support the same qualitative pattern: separated H/V curves with an upper-range downturn. This is a diagnostic result only; it does not establish qualitative or numerical reproduction of a source-paper figure.

## Assumed/guessed parameters

The following values were not paper-explicit in the authoritative ledger and are therefore treated as guessed, assumed, or backend-supplied:

- `electromagnetic_model = iba` — provenance class `model_assumption`
- `microstructure_model = exponential` — provenance class `model_assumption`
- `output = tb` — provenance class `model_assumption`
- `angle_deg = 55.0` — provenance class `model_assumption`
- `temperature_k = 265.0` — provenance class `model_assumption`
- `corr_length_m = 0.00015` — provenance class `model_assumption`
- `radius_m = 0.0002` — provenance class `backend_default`
- `stickiness = 0.2` — provenance class `backend_default`
- `dort_streams = 32` — provenance class `model_assumption`
- `sweep_parameter = density_kg_m3` — provenance class `model_assumption`
- `sweep_start = 50.0` — provenance class `model_assumption`
- `sweep_stop = 917.0` — provenance class `model_assumption`
- `sweep_points = 10` — provenance class `model_assumption`

The ledger identifies `frequency_ghz = 37.0` and `thickness_m = 1.0` as `paper_inferred`, not paper-explicit. It identifies `density_kg_m3 = 917.0` as `user_specified`; the paper comparison value was 2000 kg m⁻³, but that condition was not executed.

## Limitations

The legal-density diagnostic cannot answer the original question at 2000 kg m⁻³. The model run used the registered SMRT configuration and produced no measured-data comparison. The source figure was not available as a recorded comparison artifact for this report, so no claim of visual correspondence or reproduction success is made. The result remains **partial**.

<parameter_provenance>
[{"field":"electromagnetic_model","value":"iba","source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"microstructure_model","value":"exponential","source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"output","value":"tb","source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"frequency_ghz","value":37.0,"source_kind":"paper","provenance_class":"paper_inferred","source_ref":"user question","source_span":"paper condition mapped to frequency_ghz = 37","reason":"Paper condition mapped to the registered model input.","sensitivity_checked":false},{"field":"angle_deg","value":55.0,"source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"thickness_m","value":1.0,"source_kind":"paper","provenance_class":"paper_inferred","source_ref":"user question","source_span":"paper condition mapped to thickness_m = 1","reason":"Paper condition mapped to the registered model input.","sensitivity_checked":false},{"field":"density_kg_m3","value":917.0,"source_kind":"user","provenance_class":"user_specified","source_ref":"user question","reason":"The submitted experiment differs from the paper condition; the paper value remains comparison context.","sensitivity_checked":false},{"field":"temperature_k","value":265.0,"source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"radius_m","value":0.0002,"source_kind":"model_default","provenance_class":"backend_default","source_ref":"registered model parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"stickiness","value":0.2,"source_kind":"model_default","provenance_class":"backend_default","source_ref":"registered model parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"sweep_start","value":50.0,"source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"sweep_stop","value":917.0,"source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"assumption","provenance_class":"model_assumption","source_ref":"approved run ledger; no attached paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
