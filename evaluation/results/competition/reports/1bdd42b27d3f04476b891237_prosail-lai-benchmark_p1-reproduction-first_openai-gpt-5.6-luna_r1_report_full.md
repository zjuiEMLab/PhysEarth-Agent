# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows a clear LAI response: NDVI and NIR reflectance increase as LAI rises from 0.5 to 6.0, while red and SWIR reflectance decrease. The curves approach a flatter, canopy-saturated regime at higher LAI; green reflectance decreases overall but has a small high-LAI reversal. [model:prosail@2.0.5]

The generated figure therefore supports the qualitative conclusion that increasing LAI strengthens the vegetation signal and produces convergence toward a more stable optical response. This is a supported PROSAIL sensitivity result, not an exact reproduction of the unavailable PROSPECT-5 + 4SAIL spherical-LAD/SDR configuration. [prosail-docs#00]

## Supporting results

### Conclusion supported by the generated image

The image contains five modeled series on common axes:

- x-axis: leaf area index, m² m⁻²
- y-axis: reflectance / NDVI, dimensionless
- series: green, red, NIR, SWIR reflectance, and NDVI

The visible ordering and shape show:

- NDVI increasing with LAI.
- NIR increasing with LAI.
- Red and SWIR decreasing with LAI.
- Green decreasing overall, with a small endpoint reversal.
- Greater flattening of the curves toward high LAI.

The automatic render check passed, establishing that the plotted arrays were finite, sufficiently populated, and legible. It did not test agreement with a source figure.

### Conclusion supported by the result arrays

At LAI 0.5, the recorded values were:

- NDVI: 0.3755
- Green reflectance: 0.1715
- Red reflectance: 0.1803
- NIR reflectance: 0.3970
- SWIR reflectance: 0.4252

At LAI 6.0, they were:

- NDVI: 0.9326
- Green reflectance: 0.0530
- Red reflectance: 0.0167
- NIR reflectance: 0.4777
- SWIR reflectance: 0.2115

The baseline run at LAI 3.0 returned NDVI 0.9006, green reflectance 0.0583, red reflectance 0.0233, NIR reflectance 0.4465, and SWIR reflectance 0.2344. [model:prosail@2.0.5]

## Image–array comparison

| Aspect | Generated image | Recorded arrays | Assessment |
|---|---|---|---|
| LAI range | 0.5–6.0 | 12 points over 0.5–6.0 | Agreement |
| NDVI | Increasing, flattening at high LAI | 0.3755 to 0.9326 | Agreement |
| NIR | Increasing | 0.3970 to 0.4777 | Agreement |
| Red and SWIR | Decreasing | Red 0.1803 to 0.0167; SWIR 0.4252 to 0.2115 | Agreement |
| Green | Decreasing overall with endpoint reversal | 0.1715 to 0.0530, non-monotonic | Agreement |
| Numerical comparison with source figure | Not available from the rendered image alone | No digitized source data or error metrics | Not scoreable |

The image and arrays support the same qualitative pattern. No numerical agreement statistic with the paper figure was supplied, so bias, RMSE, correlation, and percent error are not scoreable. The result is consequently **partial**: the supported optical sensitivity experiment succeeded, while the unavailable paper-specific model configuration was not reproduced.

## Assumed parameters

The following values were not paper-derived. They are retained exactly from the authoritative ledger.

### Backend defaults

- `leaf_structure = 1.5`
- `chlorophyll_ug_cm2 = 40.0`
- `carotenoid_ug_cm2 = 8.0`
- `anthocyanin_ug_cm2 = 0.0`
- `brown_pigment = 0.0`
- `equivalent_water_thickness_cm = 0.01`
- `dry_matter_g_cm2 = 0.009`
- `average_leaf_angle_deg = 50.0`
- `hot_spot = 0.01`
- `solar_zenith_deg = 30.0`
- `view_zenith_deg = 10.0`
- `relative_azimuth_deg = 0.0`
- `soil_brightness = 1.0`
- `soil_moisture_fraction = 1.0`
- `sweep_parameter = none` for the baseline

These are registered backend defaults, not paper evidence. [model:prosail@2.0.5]

### Model assumption

- `leaf_area_index = 3.0` for the baseline and `0.5–6.0` for the sensitivity sweep.

The baseline is the registered default, while the sweep is a supported exploratory sensitivity and not paper data. [model:prosail@2.0.5]

### User-specified sweep settings

- `sweep_start = 0.5`
- `sweep_stop = 6.0`
- `sweep_points = 12`

## Limitations

The available registered capability did not provide the paper’s PROSPECT-5 plus 4SAIL spherical leaf-angle-distribution and SDR configuration. Exact paper-configuration reproduction is therefore not identifiable. The reported results are from PROSAIL 2.0.5 using the recorded defaults and the approved LAI sweep. [prosail-docs#00]

<parameter_provenance>
[{"field":"leaf_structure","value":1.5,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"chlorophyll_ug_cm2","value":40.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"carotenoid_ug_cm2","value":8.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"anthocyanin_ug_cm2","value":0.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"brown_pigment","value":0.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"equivalent_water_thickness_cm","value":0.01,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"dry_matter_g_cm2","value":0.009,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"leaf_area_index","value":"3.0 baseline; 0.5-6.0 sweep","source_kind":"assumption","source_ref":"approved research plan and retained model configuration","source_span":"","reason":"The registered default defines the baseline; the retained sweep is supported exploratory sensitivity, not paper data.","sensitivity_checked":true},{"field":"average_leaf_angle_deg","value":50.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"hot_spot","value":0.01,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"solar_zenith_deg","value":30.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"view_zenith_deg","value":10.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"relative_azimuth_deg","value":0.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"soil_brightness","value":1.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"soil_moisture_fraction","value":1.0,"source_kind":"model_default","source_ref":"registered prosail backend default","source_span":"","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none baseline; leaf_area_index sweep","source_kind":"model_default","source_ref":"registered backend default and approved LAI sweep configuration","source_span":"","reason":"The backend default is none for the baseline; the retained sweep selects LAI.","sensitivity_checked":true},{"field":"sweep_start","value":0.5,"source_kind":"user","source_ref":"approved research plan","source_span":"","reason":"Retained as the supported LAI sensitivity lower bound.","sensitivity_checked":true},{"field":"sweep_stop","value":6.0,"source_kind":"user","source_ref":"approved research plan","source_span":"","reason":"Retained as the supported LAI sensitivity upper bound.","sensitivity_checked":true},{"field":"sweep_points","value":12,"source_kind":"user","source_ref":"approved research plan","source_span":"","reason":"Retained as the approved LAI sampling density.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
