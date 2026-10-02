# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows a clear LAI-dependent spectral response in the generated PROSAIL output. As LAI increases from 0 to 6, NDVI and NIR reflectance increase, while red, green, and SWIR reflectance decrease overall. The curves remain ordered as distinct model outputs rather than converging to a common value. [model:prosail@2.0.5]

The supported reproduction is therefore **qualitatively successful for the generated PROSAIL LAI-sensitivity result**, but it is **partial as a paper reproduction**: the unavailable PROSAIL Fortran reference implementation (PROSPECT-5 + 4SAIL) was not run, so direct numerical equivalence cannot be assessed. [prosail-docs#01] [skill:research-reporting]

## Conclusion supported by the generated image

The generated figure contains five series on a common LAI axis: green, red, NIR, and SWIR reflectance, plus NDVI. It shows:

- increasing NDVI with increasing LAI;
- increasing NIR reflectance;
- decreasing red and SWIR reflectance;
- an overall decrease in green reflectance;
- the largest visible changes near the low-LAI endpoint, especially from LAI 0 to 0.5.

The figure is usable and legible, but that establishes only that the generated arrays were rendered successfully. It does not establish numerical agreement with the source figure.

## Conclusion supported by the result arrays

The recorded model result contains 13 LAI points from 0 to 6 in increments of 0.5. NDVI increases from 0.0916 to 0.9326, and NIR reflectance increases from 0.3857 to 0.4777. Red reflectance decreases from 0.3210 to 0.0167, while green and SWIR reflectance decrease overall to 0.0530 and 0.2115, respectively. [model:prosail@2.0.5]

The array summary reports NDVI and NIR as increasing and red as decreasing. Green is reported as non-monotonic because of its endpoint behaviour, although its overall endpoint change is downward. [model:prosail@2.0.5]

## Image–array comparison

| Aspect | Generated image | Recorded arrays | Assessment |
|---|---|---|---|
| Number of curves | Five | Five output series | Agreement |
| Axis and grouping | LAI against reflectance/NDVI | 13 LAI-indexed points | Agreement |
| NDVI pattern | Increasing | 0.0916 to 0.9326; increasing | Agreement |
| NIR pattern | Increasing | 0.3857 to 0.4777; increasing | Agreement |
| Red pattern | Decreasing | 0.3210 to 0.0167; decreasing | Agreement |
| Green pattern | Overall decrease with endpoint change | Non-monotonic flag; lower final value | Agreement with qualification |
| Source-figure numerical agreement | Not established by the rendered figure | No digitized source values or comparison metric recorded | Not scoreable |

The generated image and arrays support the same qualitative pattern. No bias, RMSE, correlation, or other numerical comparison with the source figure was supplied, so such agreement is not scoreable.

## Assumed parameters

The benchmark LAI value of 3.0 is **paper-inferred**, not paper-explicit: the recorded evidence identifies the documentation benchmark, but does not provide an explicit paper value in the ledger. The LAI sweep definition and bounds are **model assumptions** retained in the approved run. [prosail-docs#01]

The following parameters are **backend defaults**, not paper evidence: leaf structure 1.5; chlorophyll 40.0 µg cm⁻²; carotenoid 8.0 µg cm⁻²; anthocyanin 0.0; brown pigment 0.0; equivalent water thickness 0.01 cm; dry matter 0.009 g cm⁻²; average leaf angle 50.0°; hot spot 0.01; solar zenith 30.0°; view zenith 10.0°; relative azimuth 0.0°; soil brightness 1.0; and soil moisture fraction 1.0. [model:prosail@2.0.5]

The sweep parameter was LAI, with assumed bounds of 0.0–6.0 and 13 points. These choices were not supported by paper evidence in the recorded ledger.

## Limitations

The PROSAIL Fortran reference implementation was unavailable, as was a direct SDR bidirectional-reflectance comparison. Consequently, the report supports the generated-model result and its qualitative LAI response, but not exact reproduction of the unavailable reference implementation. No source-figure digitization or numerical validation statistic was recorded. [prosail-docs#01] [skill:research-reporting]

<parameter_provenance>
[{"field":"leaf_area_index","value":3.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":null,"reason":"Paper-inferred benchmark input; exact registered value used in the supported benchmark run","sensitivity_checked":true,"provenance":"paper_inferred"},{"field":"leaf_structure","value":1.5,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"chlorophyll_ug_cm2","value":40.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"carotenoid_ug_cm2","value":8.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"anthocyanin_ug_cm2","value":0.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"brown_pigment","value":0.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"equivalent_water_thickness_cm","value":0.01,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"dry_matter_g_cm2","value":0.009,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"average_leaf_angle_deg","value":50.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"hot_spot","value":0.01,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"solar_zenith_deg","value":30.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"view_zenith_deg","value":10.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"relative_azimuth_deg","value":0.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"soil_brightness","value":1.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"soil_moisture_fraction","value":1.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","source_span":null,"reason":"Inserted by the registered model; not paper evidence","sensitivity_checked":false,"provenance":"backend_default"},{"field":"sweep_parameter","value":"leaf_area_index","source_kind":"assumption","source_ref":"approved run configuration","source_span":null,"reason":"Retained as the submitted sweep variable without paper or user evidence","sensitivity_checked":true,"provenance":"model_assumption"},{"field":"sweep_start","value":0.0,"source_kind":"assumption","source_ref":"approved run configuration","source_span":null,"reason":"Retained as the submitted sweep lower bound without paper or user evidence","sensitivity_checked":false,"provenance":"model_assumption"},{"field":"sweep_stop","value":6.0,"source_kind":"assumption","source_ref":"approved run configuration","source_span":null,"reason":"Retained as the submitted sweep upper bound without paper or user evidence","sensitivity_checked":false,"provenance":"model_assumption"},{"field":"sweep_points","value":13,"source_kind":"assumption","source_ref":"approved run configuration","source_span":null,"reason":"Retained as the submitted number of sweep points without paper or user evidence","sensitivity_checked":false,"provenance":"model_assumption"}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
