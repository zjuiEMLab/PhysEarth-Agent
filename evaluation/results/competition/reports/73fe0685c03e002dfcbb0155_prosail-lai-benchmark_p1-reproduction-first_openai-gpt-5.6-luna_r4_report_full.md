# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show a clear LAI response: NDVI and NIR reflectance increase with LAI, while red, green, and SWIR reflectance decrease rapidly at low LAI and then level off. The figures therefore support qualitative canopy-convergence behavior at high LAI, but they do not establish equivalence to the unavailable PROSPECT-5 + 4SAIL spherical-leaf-angle reference.

The approved PROSAIL benchmark and 0–8 LAI sweep both completed successfully. The result is a **partial qualitative reproduction** of the registered PROSAIL behavior, not a full reproduction of the unavailable reference implementation. [model:prosail@2.0.5] [prosail-docs#00]

## Supporting results

### Conclusion supported by the generated figures

- Figure 1 contains four reflectance curves versus LAI.
- Green, red, and SWIR reflectance decline sharply from LAI 0 to low positive LAI and then approach relatively stable values.
- NIR reflectance increases with LAI.
- Figure 2 shows NDVI increasing with LAI and approaching a high-LAI plateau.
- Both selected figures rendered successfully and passed the legibility render check. This confirms that the plotted arrays are usable; it does not constitute a comparison with the unavailable reference figure.

### Conclusion supported by the result arrays

At the benchmark LAI of 3.0, the model returned:

| Observable | Value |
|---|---:|
| Green reflectance | 0.0583 |
| Red reflectance | 0.0233 |
| NIR reflectance | 0.4465 |
| SWIR reflectance | 0.2344 |
| NDVI | 0.9006 |

Across the recorded LAI sweep from 0 to 8:

| Observable | LAI 0 | LAI 8 | Recorded behavior |
|---|---:|---:|---|
| Green reflectance | 0.2587 | 0.0535 | Non-monotonic; minimum near high LAI before a slight rise |
| Red reflectance | 0.3210 | 0.0168 | Non-monotonic; approaches a low plateau |
| NIR reflectance | 0.3857 | 0.4859 | Increasing |
| SWIR reflectance | 0.5095 | 0.2121 | Non-monotonic; approaches a low plateau |
| NDVI | 0.0916 | 0.9333 | Increasing toward saturation |

No bias, RMSE, correlation, digitized curve comparison, or other numerical agreement statistic was supplied; these comparisons are therefore **not scoreable**.

## Comparison and qualification

| Aspect | Generated figures and arrays | Reference comparison |
|---|---|---|
| Curves available | Four reflectances and NDVI versus LAI | PROSPECT-5 + 4SAIL SDR spherical-angle reference unavailable |
| Qualitative pattern | Low-LAI transition, increasing NIR and NDVI, high-LAI flattening | Cannot be numerically or visually scored against the unavailable reference |
| Numerical values | Available from the two completed PROSAIL runs | No reference values available for error statistics |
| Outcome | Supported registered-model behavior | Partial reproduction only |

The agreement between the two generated representations is strong: the plotted shapes correspond to the recorded arrays. The qualification is that the local registered model is not the unavailable paper reference implementation, so the result cannot be called an exact reproduction.

## Assumed and user-specified parameters

The paper-explicit parameters were taken from the documented benchmark configuration. [prosail-docs#00]

The following were not paper evidence for the unavailable reference:

- `anthocyanin_ug_cm2 = 0.0`: model assumption.
- `brown_pigment = 0.0`: model assumption.
- `sweep_parameter = leaf_area_index`: user-specified.
- `sweep_start = 0.0`: user-specified.
- `sweep_stop = 8.0`: user-specified.
- `sweep_points = 17`: user-specified.

The LAI value of 3.0 is paper-explicit for the benchmark and was held as the baseline while LAI was swept in the sensitivity run. The registered sweep specification also retained the baseline `leaf_area_index = 3.0` in the run specification.

## Limitations

The unavailable PROSPECT-5 + 4SAIL SDR implementation with spherical leaf-angle distribution prevents a full reference-code reproduction. No digitized source curves or independent measurements were available, so numerical agreement with the paper reference is not identifiable. The low-LAI endpoint changes should also be interpreted as endpoint behavior of the registered model rather than as a validated physical threshold.

<parameter_provenance>
[{"field":"leaf_structure","value":1.5,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"chlorophyll_ug_cm2","value":40.0,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"carotenoid_ug_cm2","value":8.0,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"equivalent_water_thickness_cm","value":0.01,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"dry_matter_g_cm2","value":0.009,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"leaf_area_index","value":3.0,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input; held at 3 for baseline and swept in sensitivity run","reason":"Baseline value in the approved run specification","sensitivity_checked":false},{"field":"average_leaf_angle_deg","value":50.0,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"solar_zenith_deg","value":30.0,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"view_zenith_deg","value":10.0,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"relative_azimuth_deg","value":0.0,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"soil_brightness","value":1.0,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"soil_moisture_fraction","value":1.0,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct documented benchmark input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"hot_spot","value":0.01,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Paper condition mapped to the registered model input","reason":"Used in both approved physical-model runs","sensitivity_checked":false},{"field":"anthocyanin_ug_cm2","value":0.0,"source_kind":"assumption","source_ref":"Explicit registered input; unavailable reference does not supply this mapping","source_span":"","reason":"Model assumption used in both approved physical-model runs","sensitivity_checked":false},{"field":"brown_pigment","value":0.0,"source_kind":"assumption","source_ref":"Explicit registered input; unavailable reference does not supply this mapping","source_span":"","reason":"Model assumption used in both approved physical-model runs","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"Approved benchmark run specification","source_span":"","reason":"Benchmark run is a single-point run","sensitivity_checked":false},{"field":"sweep_parameter","value":"leaf_area_index","source_kind":"user","source_ref":"User-confirmed approved research plan","source_span":"","reason":"Identifies the LAI sensitivity sweep","sensitivity_checked":false},{"field":"sweep_start","value":0.0,"source_kind":"user","source_ref":"User-confirmed approved research plan","source_span":"","reason":"Exact approved sweep boundary","sensitivity_checked":false},{"field":"sweep_stop","value":8.0,"source_kind":"user","source_ref":"User-confirmed approved research plan","source_span":"","reason":"Exact approved sweep boundary","sensitivity_checked":false},{"field":"sweep_points","value":17,"source_kind":"user","source_ref":"User-confirmed approved research plan","source_span":"","reason":"Exact approved sweep sampling","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
