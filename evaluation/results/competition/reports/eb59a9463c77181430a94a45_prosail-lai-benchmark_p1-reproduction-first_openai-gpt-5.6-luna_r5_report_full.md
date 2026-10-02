# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show the expected LAI response: NDVI and NIR reflectance increase with leaf area index, while green, red, and SWIR reflectance decline sharply from LAI 0 to 0.5 and then approach stable high-LAI behavior. The modeled LAI range was 0–8 with 17 points. The qualitative result is therefore supported, but exact reproduction of the unavailable PROSAIL Fortran reference is not identifiable. [model:prosail@2.0.5]

At the approved baseline of LAI 3, the model produced NDVI 0.9006, green reflectance 0.0583, red reflectance 0.0233, NIR reflectance 0.4465, and SWIR reflectance 0.2344. [model:prosail@2.0.5]

## Supporting results

### Conclusion supported by the generated figures

- Figure 1 contains four reflectance curves over LAI.
- Figure 2 contains one NDVI curve over LAI.
- Both figures use LAI from 0 to 8 on the x-axis.
- The curves show strong low-LAI change followed by high-LAI flattening.
- Render checks passed for both figures, establishing that the plotted arrays were finite, sufficiently sampled, and legible. This does not establish numerical agreement with the unavailable Fortran reference.

### Conclusion supported by the result arrays

Across the LAI sweep:

- NDVI increased from **0.0916** at LAI 0 to **0.9333** at LAI 8.
- NIR reflectance increased from **0.3857** to **0.4859**.
- Green reflectance decreased from **0.2587** to **0.0535**, with a minimum of **0.0529**.
- Red reflectance decreased from **0.3210** to **0.0168**, with a minimum of **0.0166**.
- SWIR reflectance decreased from **0.5095** to **0.2121**, with a minimum of **0.2114**. [model:prosail@2.0.5]

| Aspect | Generated figures | Result arrays | Assessment |
|---|---|---|---|
| LAI range | 0–8 | 17 points over 0–8 | Agreement |
| NDVI behavior | Increasing and flattening | 0.0916 to 0.9333 | Agreement |
| NIR behavior | Increasing and flattening | 0.3857 to 0.4859 | Agreement |
| Green, red, SWIR behavior | Sharp initial decline, then flattening | Same qualitative behavior | Agreement |
| Exact comparison with PROSAIL Fortran | Not available | Not scoreable | Partial reproduction |

No RMSE, bias, correlation, or numerical validation score was supplied; these comparisons are therefore **not scoreable**. The paper’s PROSAIL documentation provided the reproduction context, but the required PROSPECT-5 + 4SAIL spherical-LAD Fortran reference was unavailable. [prosail-docs#00]

## Guessed/assumed parameters

The following values are copied from the authoritative ledger. They are **model_assumption** values, not paper-explicit values:

- `leaf_structure = 1.5`
- `chlorophyll_ug_cm2 = 40.0`
- `carotenoid_ug_cm2 = 8.0`
- `anthocyanin_ug_cm2 = 0.0`
- `brown_pigment = 0.0`
- `equivalent_water_thickness_cm = 0.01`
- `dry_matter_g_cm2 = 0.009`
- `leaf_area_index = 3.0` as the retained baseline field
- `average_leaf_angle_deg = 50.0`
- `hot_spot = 0.01`
- `solar_zenith_deg = 30.0`
- `view_zenith_deg = 10.0`
- `relative_azimuth_deg = 0.0`
- `soil_brightness = 1.0`
- `soil_moisture_fraction = 1.0`

The baseline also used `sweep_parameter = none` and `sweep_points = 10` as **backend_default** values. The LAI sweep used `sweep_start = 0.0`, `sweep_stop = 8.0`, and `sweep_points = 17` as **user_specified** values.

## Limitations

The outcome is **partial**. Both approved model runs succeeded and both generated figures rendered, but the unavailable PROSAIL Fortran reference prevents an exact numerical reproduction. The sensitivity result is conditional on the assumed leaf, canopy, geometry, and soil-background parameters above. The figures support qualitative curve behavior, not a claim of numerical agreement with the source reference.

<parameter_provenance>
[{"field":"baseline.leaf_structure","value":1.5,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.chlorophyll_ug_cm2","value":40.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.carotenoid_ug_cm2","value":8.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.anthocyanin_ug_cm2","value":0.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.brown_pigment","value":0.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.equivalent_water_thickness_cm","value":0.01,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.dry_matter_g_cm2","value":0.009,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.leaf_area_index","value":3.0,"source_kind":"assumption","source_ref":"approved baseline configuration","reason":"retained baseline LAI field; the sweep controls LAI in the sensitivity run","sensitivity_checked":true},{"field":"baseline.average_leaf_angle_deg","value":50.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.hot_spot","value":0.01,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.solar_zenith_deg","value":30.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.view_zenith_deg","value":10.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.relative_azimuth_deg","value":0.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.soil_brightness","value":1.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.soil_moisture_fraction","value":1.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"baseline.sweep_parameter","value":"none","source_kind":"model_default","source_ref":"registered PROSAIL default for a non-sweep run","reason":"backend_default in authoritative ledger","sensitivity_checked":false},{"field":"baseline.sweep_points","value":10,"source_kind":"model_default","source_ref":"registered PROSAIL default for a non-sweep run","reason":"backend_default in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.leaf_structure","value":1.5,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.chlorophyll_ug_cm2","value":40.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.carotenoid_ug_cm2","value":8.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.anthocyanin_ug_cm2","value":0.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.brown_pigment","value":0.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.equivalent_water_thickness_cm","value":0.01,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.dry_matter_g_cm2","value":0.009,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.leaf_area_index","value":3.0,"source_kind":"assumption","source_ref":"approved LAI sweep run state","reason":"retained nominal LAI field while LAI was swept from 0.0 to 8.0","sensitivity_checked":true},{"field":"lai_sweep.average_leaf_angle_deg","value":50.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.hot_spot","value":0.01,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.solar_zenith_deg","value":30.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.view_zenith_deg","value":10.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.relative_azimuth_deg","value":0.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.soil_brightness","value":1.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.soil_moisture_fraction","value":1.0,"source_kind":"assumption","source_ref":"approved run state; registered PROSAIL default retained in plan","reason":"model_assumption in authoritative ledger","sensitivity_checked":false},{"field":"lai_sweep.sweep_parameter","value":"leaf_area_index","source_kind":"user","source_ref":"user-approved LAI sensitivity experiment","reason":"approved sweep axis","sensitivity_checked":true},{"field":"lai_sweep.sweep_start","value":0.0,"source_kind":"user","source_ref":"user-approved exploratory sweep boundary","reason":"user_specified in authoritative ledger","sensitivity_checked":true},{"field":"lai_sweep.sweep_stop","value":8.0,"source_kind":"user","source_ref":"user-approved exploratory sweep boundary","reason":"user_specified in authoritative ledger","sensitivity_checked":true},{"field":"lai_sweep.sweep_points","value":17,"source_kind":"user","source_ref":"user-approved sweep sampling","reason":"user_specified in authoritative ledger","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
