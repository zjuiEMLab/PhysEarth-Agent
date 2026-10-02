# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated LAI figure shows a clear canopy-response pattern: NDVI and NIR reflectance increase with LAI, while green, red, and SWIR reflectances decrease rapidly at low LAI and then level off. The response is therefore convergent or saturating at high LAI rather than continuously diverging. The plotted range is LAI **0–8 m² m⁻²** across 17 points. [model:prosail@2.0.5]

The registered-model experiment supports this qualitative conclusion, but it is only a partial reproduction of the documented benchmark because the PROSPECT-5 + 4SAIL Jussieu Fortran reference was unavailable. [prosail-docs#00]

## Conclusion supported by the generated image

Figure 1 contains five curves on shared LAI axes: green, red, NIR, and SWIR reflectance plus NDVI. The visible grouping shows:

- NDVI rising toward a high-LAI plateau.
- NIR reflectance increasing with LAI.
- Green, red, and SWIR reflectance decreasing strongly at low LAI.
- Small reversals or flattening at high LAI, indicating saturation-like behavior rather than strict monotonicity for every reflectance band.

The generated chart was legible after rendering. This establishes chart usability, not agreement with the unavailable Jussieu reference figure.

## Conclusion supported by result arrays

The actual PROSAIL result arrays give:

| Quantity | LAI = 0 | LAI = 8 |
|---|---:|---:|
| Green reflectance | 0.2587 | 0.0535 |
| Red reflectance | 0.3210 | 0.0168 |
| NIR reflectance | 0.3857 | 0.4859 |
| SWIR reflectance | 0.5095 | 0.2121 |
| NDVI | 0.0916 | 0.9333 |

At the baseline LAI of 3, the model produced green reflectance **0.0583**, red reflectance **0.0233**, NIR reflectance **0.4465**, SWIR reflectance **0.2344**, and NDVI **0.9006**. [model:prosail@2.0.5]

The arrays show that NIR reflectance and NDVI are increasing over the sweep. Green, red, and SWIR reflectances are not strictly monotonic: each decreases to a minimum and then changes slightly at high LAI. [model:prosail@2.0.5]

## Image–array comparison

| Aspect | Generated image | Result arrays | Assessment |
|---|---|---|---|
| LAI response | Curves rise or fall and then flatten | Same qualitative behavior, with numerical endpoint values | Agreement |
| High-LAI behavior | Visible saturation-like grouping | Small high-LAI reversals in several reflectances | Agreement with qualification |
| Low-LAI behavior | Strong separation near LAI 0 | Large changes between LAI 0 and 0.5 | Agreement |
| Reference-model agreement | Not established from the unavailable Jussieu implementation | No reference-array comparison supplied | Not scoreable |
| Numerical validation statistics | Not shown | No bias, RMSE, correlation, or percent error calculated | N/A |

The figure and arrays support the same qualitative pattern. Exact numerical agreement with the original reference implementation is not identifiable, and no quantitative validation statistic was supplied.

## Assumed parameters

All entries below use the authoritative ledger’s provenance classes. `backend_default` is represented as the permitted XML value `model_default`.

The baseline used the registered defaults, including LAI = 3.0. The sensitivity run used the approved LAI sweep from 0 to 8 with 17 points; the ledger separately records the retained submitted-run sweep fields.

<parameter_provenance>
[
  {"field":"leaf_structure","value":1.5,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"chlorophyll_ug_cm2","value":40.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"carotenoid_ug_cm2","value":8.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"equivalent_water_thickness_cm","value":0.01,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"dry_matter_g_cm2","value":0.009,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"leaf_area_index","value":3.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The baseline uses the registered default; the sensitivity run maps LAI to the declared sweep input.","sensitivity_checked":false},
  {"field":"average_leaf_angle_deg","value":50.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"hot_spot","value":0.01,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"solar_zenith_deg","value":30.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"view_zenith_deg","value":10.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"relative_azimuth_deg","value":0.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"anthocyanin_ug_cm2","value":0.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"brown_pigment","value":0.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"soil_brightness","value":1.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"soil_moisture_fraction","value":1.0,"source_kind":"model_default","source_ref":"prosail-docs#00","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},
  {"field":"sweep_parameter","value":"none","source_kind":"assumption","source_ref":"none","reason":"The submitted run retained this value without attached paper or user evidence; it was confirmed during plan review.","sensitivity_checked":false},
  {"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"none","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},
  {"field":"sweep_start","value":0.0,"source_kind":"assumption","source_ref":"none","reason":"The submitted run retained this value without attached paper or user evidence; it was confirmed during plan review.","sensitivity_checked":false},
  {"field":"sweep_stop","value":8.0,"source_kind":"assumption","source_ref":"none","reason":"The submitted run retained this value without attached paper or user evidence; it was confirmed during plan review.","sensitivity_checked":false},
  {"field":"approved_lai_sweep","value":"leaf_area_index from 0.0 to 8.0, 17 points","source_kind":"user","source_ref":"approved research plan","reason":"This was the approved sensitivity-run configuration.","sensitivity_checked":false}
]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
