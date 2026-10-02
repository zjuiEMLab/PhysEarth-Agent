# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show the expected qualitative LAI response: as LAI increases from 0.0 to 6.0, red and SWIR reflectance decrease, NIR reflectance increases, and NDVI increases toward a high-LAI plateau. The benchmark chart contains four reflectance series; the LAI chart contains five series, adding NDVI. [model:prosail@2.0.5]

This is a **partial reproduction**. The local PROSAIL implementation produced the supported benchmark and LAI-sensitivity results, but the unavailable PROSAIL Fortran reference (PROSPECT-5 + 4SAIL) could not be quantitatively reproduced or directly compared. [prosail-docs#00] [prosail-docs#01]

## Supporting results

The `benchmark_local` run used LAI 3.0 and returned:

- green reflectance: 0.05833922334208669
- red reflectance: 0.02334383898010929
- NIR reflectance: 0.4459157497955028
- SWIR reflectance: 0.197881517088087
- NDVI: 0.9005077806038324

The `lai_sensitivity` run covered LAI 0.0–6.0 with 13 recorded points. NDVI increased from 0.09155225398882812 to 0.9324975592492014; red reflectance decreased from 0.32100000977516174 to 0.016658403940625444; NIR reflectance increased from 0.385699987411499 to 0.476906088108601; and SWIR reflectance decreased from 0.5095000267028809 to 0.1763350123995467. [model:prosail@2.0.5]

Green reflectance was non-monotonic overall, declining strongly at low LAI and showing a small endpoint increase between the final two recorded points. [model:prosail@2.0.5]

## Source/generated-image conclusion

Figure 1 is titled “Supported benchmark outputs,” with LAI on the x-axis and reflectance on the y-axis; it contains four reflectance series. Figure 2 is titled “Reflectance and NDVI versus LAI,” with LAI on the x-axis and dimensionless output on the y-axis; it contains five series. Both generated figures rendered successfully and passed the automatic legibility check.

A direct visual comparison with the unavailable Fortran reference figure is not identifiable from the recorded state. Thus, the shared qualitative pattern is supported by the generated arrays, but equivalence to the reference implementation is not established.

## Comparison

| Aspect | Generated figures and arrays | Reference comparison |
|---|---|---|
| Series | Four reflectance outputs in Figure 1; five outputs including NDVI in Figure 2 | Fortran reference unavailable |
| LAI ordering | Red and SWIR decrease; NIR and NDVI increase | Not scoreable against the unavailable reference |
| Convergence | NDVI and spectral responses approach high-LAI plateaus | Not scoreable quantitatively |
| Differences | Green reflectance is non-monotonic and has a small high-LAI endpoint reversal | Cannot determine whether this differs from the reference |
| Numerical agreement statistics | N/A | No comparison data or explicit check supplied |

## Assumed parameters

The paper-inferred values were LAI 3.0, chlorophyll 40.0 µg cm⁻², equivalent water thickness 0.015 cm, and solar zenith 30.0°. The registered model supplied the backend-default parameters listed in the provenance appendix. The LAI sweep bounds 0.0 and 6.0 were model assumptions, not paper-explicit values. [prosail-docs#01] [model:prosail@2.0.5]

## Limitations

The result is limited to the registered local PROSAIL v2.0.5 implementation. The Fortran PROSAIL reference was unavailable and is not treated as equivalent. The paper-inferred and backend-default inputs limit quantitative reproduction claims. The requested direct numerical comparison with the Fortran reference is therefore not identifiable.

<parameter_provenance>
[{"field":"benchmark_local.leaf_area_index","value":3.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented benchmark configuration","reason":"Use the benchmark canopy-density setting described in the opened documentation.","sensitivity_checked":false},{"field":"benchmark_local.chlorophyll_ug_cm2","value":40.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented benchmark configuration","reason":"Use the documented green-leaf pigment setting.","sensitivity_checked":false},{"field":"benchmark_local.equivalent_water_thickness_cm","value":0.015,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented benchmark configuration","reason":"Use the documented leaf-water setting.","sensitivity_checked":false},{"field":"benchmark_local.solar_zenith_deg","value":30.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented benchmark configuration","reason":"Use the documented illumination geometry.","sensitivity_checked":false},{"field":"benchmark_local.leaf_structure","value":1.5,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.carotenoid_ug_cm2","value":8.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.anthocyanin_ug_cm2","value":0.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.brown_pigment","value":0.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.dry_matter_g_cm2","value":0.009,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.average_leaf_angle_deg","value":50.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.hot_spot","value":0.01,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.view_zenith_deg","value":10.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.relative_azimuth_deg","value":0.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.soil_brightness","value":1.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.soil_moisture_fraction","value":1.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; not paper evidence.","sensitivity_checked":false},{"field":"benchmark_local.sweep_parameter","value":"none","source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default; benchmark has no sweep.","sensitivity_checked":false},{"field":"benchmark_local.sweep_points","value":10,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.leaf_area_index","value":3.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented benchmark configuration","reason":"Retained fixed reference value in the approved run specification.","sensitivity_checked":false},{"field":"lai_sensitivity.chlorophyll_ug_cm2","value":40.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented benchmark configuration","reason":"Retained fixed reference value in the approved run specification.","sensitivity_checked":false},{"field":"lai_sensitivity.equivalent_water_thickness_cm","value":0.015,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented benchmark configuration","reason":"Retained fixed reference value in the approved run specification.","sensitivity_checked":false},{"field":"lai_sensitivity.solar_zenith_deg","value":30.0,"source_kind":"paper","source_ref":"prosail-docs#01","source_span":"documented benchmark configuration","reason":"Retained fixed reference value in the approved run specification.","sensitivity_checked":false},{"field":"lai_sensitivity.leaf_structure","value":1.5,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.carotenoid_ug_cm2","value":8.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.anthocyanin_ug_cm2","value":0.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.brown_pigment","value":0.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.dry_matter_g_cm2","value":0.009,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.average_leaf_angle_deg","value":50.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.hot_spot","value":0.01,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.view_zenith_deg","value":10.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.relative_azimuth_deg","value":0.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.soil_brightness","value":1.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.soil_moisture_fraction","value":1.0,"source_kind":"model_default","source_ref":"prosail@1.0","reason":"Registered model default.","sensitivity_checked":false},{"field":"lai_sensitivity.sweep_parameter","value":"leaf_area_index","source_kind":"derived","source_ref":"approved run lai_sensitivity","reason":"The approved sensitivity run varies leaf_area_index.","sensitivity_checked":false},{"field":"lai_sensitivity.sweep_points","value":13,"source_kind":"derived","source_ref":"result handle res_06fd1588a84a","reason":"Recorded executed result contains 13 points.","sensitivity_checked":false},{"field":"lai_sensitivity.sweep_start","value":0.0,"source_kind":"assumption","source_ref":"approved run lai_sensitivity","reason":"Submitted sweep lower bound without paper or user evidence.","sensitivity_checked":false},{"field":"lai_sensitivity.sweep_stop","value":6.0,"source_kind":"assumption","source_ref":"approved run lai_sensitivity","reason":"Submitted sweep upper bound without paper or user evidence.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| prosail | leaf_area_index | 3.0 | paper_inferred | prosail-docs#01 |
| prosail | chlorophyll_ug_cm2 | 40.0 | paper_inferred | prosail-docs#01 |
| prosail | equivalent_water_thickness_cm | 0.015 | paper_inferred | prosail-docs#01 |
| prosail | solar_zenith_deg | 30.0 | paper_inferred | prosail-docs#01 |
| prosail | leaf_structure | 1.5 | backend_default | - |
| prosail | carotenoid_ug_cm2 | 8.0 | backend_default | - |
| prosail | anthocyanin_ug_cm2 | 0.0 | backend_default | - |
| prosail | brown_pigment | 0.0 | backend_default | - |
| prosail | dry_matter_g_cm2 | 0.009 | backend_default | - |
| prosail | average_leaf_angle_deg | 50.0 | backend_default | - |
| prosail | hot_spot | 0.01 | backend_default | - |
| prosail | view_zenith_deg | 10.0 | backend_default | - |
| prosail | relative_azimuth_deg | 0.0 | backend_default | - |
| prosail | soil_brightness | 1.0 | backend_default | - |
| prosail | soil_moisture_fraction | 1.0 | backend_default | - |
| prosail | sweep_parameter | none | backend_default | - |
| prosail | sweep_points | 10 | backend_default | - |
| prosail | sweep_start | 0.0 | model_assumption | - |
| prosail | sweep_stop | 6.0 | model_assumption | - |
