# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show a strong low-LAI transition followed by convergence toward a stable canopy response. Across LAI 0–10, NIR reflectance increases, while red, green, and SWIR reflectances decrease rapidly and then flatten. NDVI rises rapidly at low LAI, approaches approximately 0.93 at high LAI, and changes only slightly after about LAI 7.5–8. [model:prosail@2.0.5]

The supported PROSAIL reproduction is therefore **partial**: both approved runs completed and both figures were rendered successfully, but the unavailable PROSAIL Fortran reference prevents an implementation-level numerical comparison. [model:prosail@2.0.5]

## Supporting results

Figure 1 contains four reflectance series plotted against leaf area index, with reflectance as the y-axis quantity. Figure 2 contains one NDVI series plotted against leaf area index. The x-axis is labelled in m² m⁻², while the reflectance and NDVI outputs are dimensionless. [model:prosail@2.0.5]

The benchmark run at LAI 3.0 returned:

- green reflectance: 0.05833952322187055
- red reflectance: 0.023343884754454473
- NIR reflectance: 0.44648578316204524
- SWIR reflectance: 0.23441951953774764
- NDVI: 0.9006283070289071 [model:prosail@2.0.5]

The LAI sweep used 21 points from 0.0 to 10.0. NDVI ranged from 0.09155225398882812 at LAI 0.0 to a maximum of 0.9333310310870961 near LAI 8.0, ending at 0.9330573096685556 at LAI 10.0. NIR reflectance increased from 0.385699987411499 at LAI 0.0 to 0.4903348033723853 at LAI 10.0. [model:prosail@2.0.5]

## Source/generated-figure conclusion

The generated curves show four reflectance responses and one NDVI response, with rapid low-LAI changes and weaker changes at larger LAI. The reflectance curves become more closely spaced as LAI increases, while NDVI approaches a high-LAI plateau. The recorded state does not include a digitized source-figure comparison or a numerical agreement statistic, so numerical agreement with the source is **not scoreable**.

## Result-backed conclusion

The executed arrays support increasing NIR reflectance and increasing-but-nearly-saturated NDVI across the requested LAI range. Green, red, and SWIR reflectances show their largest changes between LAI 0.0 and 0.5 and then approach lower, slowly varying values. The automatic render check established that the plotted arrays were finite and legible; it did not establish agreement with the source figure. [model:prosail@2.0.5]

| Aspect | Generated-figure reading | Executed-result reading | Qualification |
|---|---|---|---|
| Reflectance response | Rapid low-LAI change followed by convergence-like flattening | Green, red, and SWIR decline rapidly; NIR increases across the full sweep | Same qualitative pattern is supported by the arrays |
| NDVI response | Rapid increase followed by high-LAI convergence | NDVI increases from 0.09155225398882812 to approximately 0.933, with a small maximum near LAI 8.0 | High-LAI behavior is nearly saturated but not strictly monotonic |
| Quantitative comparison with source | Not available from the recorded figure state | No RMSE, bias, correlation, or other comparison statistic was supplied | N/A; not scoreable |
| Reference implementation | Not available | Registered `prosail@2.0.5` ran successfully | Partial reproduction only |

## Guessed/assumed parameters

The ledger records the following values as `backend_default`: leaf structure 1.5; chlorophyll 40.0 µg cm⁻²; carotenoids 8.0 µg cm⁻²; anthocyanins 0.0; brown pigment 0.0; equivalent water thickness 0.01 cm; dry matter 0.009 g cm⁻²; average leaf angle 50.0°; hot-spot parameter 0.01; solar zenith 30.0°; view zenith 10.0°; relative azimuth 0.0°; soil brightness 1.0; soil-moisture fraction 1.0; sweep parameter `none`; and sweep points 10. The benchmark LAI value was 3.0 in the recorded run state and is retained as `backend_default`.

The sweep bounds, `sweep_start = 0.0` and `sweep_stop = 10.0`, are recorded as `model_assumption`, not as paper-explicit values. The sweep used 21 points in the executed run. [model:prosail@2.0.5]

## Limitations

The unavailable PROSAIL Fortran reference means that implementation-level numerical reproduction is not identifiable. No source-figure digitization, RMSE, bias, correlation, or validation statistic was recorded. The result characterizes the registered `prosail@2.0.5` implementation under the listed defaults and assumptions, rather than establishing observational accuracy or exact agreement with the paper reference. [model:prosail@2.0.5]

The original question is answered qualitatively: increasing LAI drives the simulated canopy toward a convergent spectral response, with NDVI saturating near 0.93 and NIR reflectance continuing to increase modestly over LAI 0–10. [model:prosail@2.0.5]

<parameter_provenance>
[{"field":"leaf_area_index","value":3.0,"source_kind":"model_default","source_ref":"approved run state; registered prosail@2.0.5 parameter resolution","reason":"Benchmark-specific value recorded in the executed run; ledger class is backend_default.","sensitivity_checked":true},{"field":"leaf_structure","value":1.5,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"chlorophyll_ug_cm2","value":40.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"carotenoid_ug_cm2","value":8.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"anthocyanin_ug_cm2","value":0.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"brown_pigment","value":0.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"equivalent_water_thickness_cm","value":0.01,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"dry_matter_g_cm2","value":0.009,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"average_leaf_angle_deg","value":50.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"hot_spot","value":0.01,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"solar_zenith_deg","value":30.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"view_zenith_deg","value":10.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"relative_azimuth_deg","value":0.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"soil_brightness","value":1.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"soil_moisture_fraction","value":1.0,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The registered model inserted this value; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"The benchmark execution was a single-point run.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"registered prosail@2.0.5 parameter resolution","reason":"Value retained in the registered run specification; it was not used to generate the benchmark point.","sensitivity_checked":false},{"field":"sweep_start","value":0.0,"source_kind":"assumption","source_ref":"approved research plan; no paper or user value attached","reason":"Retained as the lower bound for the LAI sweep without attached paper/user evidence.","sensitivity_checked":true},{"field":"sweep_stop","value":10.0,"source_kind":"assumption","source_ref":"approved research plan; no paper or user value attached","reason":"Retained as the upper bound for the LAI sweep without attached paper/user evidence.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| prosail | leaf_area_index | benchmark-specific value from prosail-docs#01 where explicit; otherwise backend default | backend_default | prosail-docs#01 |
| prosail | leaf_structure | 1.5 | backend_default | - |
| prosail | chlorophyll_ug_cm2 | 40.0 | backend_default | - |
| prosail | carotenoid_ug_cm2 | 8.0 | backend_default | - |
| prosail | anthocyanin_ug_cm2 | 0.0 | backend_default | - |
| prosail | brown_pigment | 0.0 | backend_default | - |
| prosail | equivalent_water_thickness_cm | 0.01 | backend_default | - |
| prosail | dry_matter_g_cm2 | 0.009 | backend_default | - |
| prosail | average_leaf_angle_deg | 50.0 | backend_default | - |
| prosail | hot_spot | 0.01 | backend_default | - |
| prosail | solar_zenith_deg | 30.0 | backend_default | - |
| prosail | view_zenith_deg | 10.0 | backend_default | - |
| prosail | relative_azimuth_deg | 0.0 | backend_default | - |
| prosail | soil_brightness | 1.0 | backend_default | - |
| prosail | soil_moisture_fraction | 1.0 | backend_default | - |
| prosail | sweep_parameter | none | backend_default | - |
| prosail | sweep_points | 10 | backend_default | - |
| prosail | sweep_start | 0.0 | model_assumption | - |
| prosail | sweep_stop | 10.0 | model_assumption | - |
