# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated LAI chart shows that PROSAIL reflectance is strongly LAI-sensitive at low LAI and approaches a high-LAI plateau. NIR reflectance and NDVI increase with LAI, while green, red, and SWIR reflectance generally decrease before stabilizing. The approved runs therefore reproduce the expected qualitative LAI-sensitivity pattern for the registered PROSAIL implementation.

The reproduction outcome is **partial**: the documented benchmark configuration was successfully run, but the PROSAIL Fortran reference was unavailable for direct numerical comparison. [model:prosail@2.0.5]

## Supporting results

At the benchmark configuration, LAI = 3, the computed outputs were:

- Green reflectance: 0.0583
- Red reflectance: 0.0233
- NIR reflectance: 0.4465
- SWIR reflectance: 0.2344
- NDVI: 0.9006

Across the LAI sweep from 0 to 8:

- NDVI increased from 0.0916 to 0.9333.
- NIR reflectance increased from 0.3857 to 0.4859.
- Green reflectance decreased from 0.2587 to 0.0535 overall.
- Red reflectance decreased from 0.3210 to 0.0168 overall.
- SWIR reflectance decreased from 0.5095 to 0.2121 overall.

The arrays also show small reflectance increases at the highest LAI values for green, red, and SWIR, indicating approach to a plateau rather than strictly monotonic decrease. [model:prosail@2.0.5]

## Generated-chart conclusion

The generated chart contains four reflectance series plotted against leaf area index, with unitless reflectance on the vertical axis. It shows strong separation at low LAI and reduced changes at high LAI. The chart rendered successfully and was legible.

This conclusion concerns the generated model chart only. It does not establish numerical agreement with the unavailable PROSAIL Fortran reference.

## Result-array conclusion

The recorded model arrays support the numerical endpoint values and trends reported above. No correlation, RMSE, bias, or other comparison statistic was calculated. Numerical agreement with the unavailable Fortran reference is therefore **not scoreable**. [model:prosail@2.0.5]

## Comparison

| Aspect | Generated result | Reference comparison |
|---|---|---|
| Number of plotted curves | Four reflectance bands | No Fortran result available |
| LAI range | 0–8 for the sensitivity sweep | No reference range available for numerical checking |
| Qualitative behavior | Strong low-LAI response and high-LAI stabilization | Cannot be quantitatively assessed |
| Numerical error statistics | Not calculated | Not scoreable |
| Reproduction outcome | Successful execution of the registered model | Partial |

The benchmark parameters correspond to the documented PROSAIL configuration. [prosail-docs#01] The missing Fortran reference prevents a direct implementation-to-implementation comparison.

## Assumed parameters

The following ledger entries were not paper-explicit:

- `sweep_parameter = none`: registered-model default.
- `sweep_points = 10`: registered-model default.
- `sweep_start = 0.0`: model assumption retained for the LAI sweep.
- `sweep_stop = 8.0`: model assumption retained for the LAI sweep.

The remaining physical parameters were treated as paper-explicit mappings from the opened PROSAIL documentation. [prosail-docs#01]

## Limitations

The PROSAIL Fortran reference was unavailable, so the report cannot establish exact numerical reproduction or compute reference-based error statistics. The generated chart demonstrates the behavior of the registered PROSAIL implementation and supports the reported qualitative pattern, but it is not a numerical validation against the original Fortran output.

<parameter_provenance>
[{"field":"leaf_structure","value":1.5,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"chlorophyll_ug_cm2","value":40.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"carotenoid_ug_cm2","value":8.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"equivalent_water_thickness_cm","value":0.01,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"dry_matter_g_cm2","value":0.009,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"leaf_area_index","value":3.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented benchmark LAI","reason":"The benchmark LAI was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"average_leaf_angle_deg","value":50.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"hot_spot","value":0.01,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"solar_zenith_deg","value":30.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"view_zenith_deg","value":10.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"relative_azimuth_deg","value":0.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"anthocyanin_ug_cm2","value":0.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"brown_pigment","value":0.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"soil_brightness","value":1.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"soil_moisture_fraction","value":1.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented PROSAIL benchmark input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_start","value":0.0,"source_kind":"assumption","source_ref":"approved LAI sweep run","reason":"The submitted run retained this lower bound without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_stop","value":8.0,"source_kind":"assumption","source_ref":"approved LAI sweep run","reason":"The submitted run retained this upper bound without attached paper or user evidence.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
