# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure shows a clear LAI response: NDVI and NIR reflectance increase toward a high-LAI plateau, while red and SWIR reflectance generally decrease and then converge. The curves therefore show convergence or saturation at higher LAI rather than continued linear separation. The generated figure contains all five planned PROSAIL outputs over LAI 0–8. [model:prosail@2.0.5]

A qualitative comparison with the paper’s source image is **not scoreable from the recorded state**, because no inspected source-image comparison or digitized reference data was recorded. The supported reproduction is therefore **partial**, not a claim of numerical or visual agreement with the paper. The unavailable comparisons remain PROSPECT-5 plus 4SAIL spherical LAD and SDR. [prosail-docs#00]

## Conclusion supported by the generated figure

Figure 1 has five unitless series plotted against leaf area index from 0 to 8:

- Green, red, NIR, and SWIR reflectance
- NDVI

The plotted image shows the same internally coherent pattern described by the generated arrays: strong change at low LAI, followed by progressively smaller changes and apparent saturation at higher LAI. The figure rendered successfully and passed the legibility check, which establishes that the generated curves are usable; it does not establish agreement with the paper source figure. [skill:research-reporting]

## Conclusion supported by the result arrays

The baseline at LAI 3 produced:

- Green reflectance: **0.0583**
- Red reflectance: **0.0233**
- NIR reflectance: **0.4465**
- SWIR reflectance: **0.2344**
- NDVI: **0.9006**

Across the LAI sweep:

- NDVI increased from **0.0916** at LAI 0 to **0.9333** at LAI 8.
- NIR reflectance increased from **0.3857** to **0.4859**.
- Green reflectance decreased from **0.2587** to **0.0535**, with a small high-LAI rebound.
- Red reflectance decreased from **0.3210** to **0.0168**, with a small high-LAI rebound.
- SWIR reflectance decreased from **0.5095** to **0.2121**, after reaching a minimum near the upper part of the sweep. [model:prosail@2.0.5]

## Comparison and qualification

| Aspect | Generated figure | Source-figure comparison |
|---|---|---|
| Curves and grouping | Five PROSAIL output series are present | Not scoreable from the recorded state |
| Axes and units | LAI on the x-axis; reflectance and NDVI are unitless | No independent source-image check recorded |
| Pattern | Low-LAI change followed by high-LAI convergence/saturation | Cannot determine whether the paper shows the same pattern |
| Numerical agreement | Recorded model values are available | Not scoreable; no digitized source values or comparison metric |
| Reproduction status | Supported LAI sensitivity result | Partial reproduction overall |

No RMSE, bias, correlation, or percentage agreement was calculated. The figure’s endpoint changes between LAI 0 and 0.5 should be interpreted as part of the modeled response, not as evidence of source-figure agreement.

## Assumed and guessed parameters

The following values were not paper-explicit. They were retained from the approved physical-model run as registered defaults or modeling assumptions:

- `leaf_structure = 1.5` — registered default.
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

The LAI baseline and sweep settings were user-specified in the approved plan:

- Baseline `leaf_area_index = 3.0`
- `sweep_parameter = leaf_area_index`
- `sweep_start = 0.0`
- `sweep_stop = 8.0`
- `sweep_points = 17`

## Limitations

This report covers the registered PROSAIL computation only. It does not reproduce the unavailable PROSPECT-5 plus 4SAIL spherical-LAD or SDR comparison. The paper’s parameter values were not available as explicit inputs in the recorded ledger, so the assumed optical, geometric, and soil-background parameters limit physical comparability. The outcome is consequently **partial**.

<parameter_provenance>
[
  {"field":"leaf_structure","value":1.5,"source_kind":"model_default","source_ref":"registered PROSAIL declaration","reason":"Use the registered default.","sensitivity_checked":false},
  {"field":"chlorophyll_ug_cm2","value":40.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"carotenoid_ug_cm2","value":8.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"anthocyanin_ug_cm2","value":0.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"brown_pigment","value":0.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"equivalent_water_thickness_cm","value":0.01,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"dry_matter_g_cm2","value":0.009,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"leaf_area_index","value":3.0,"source_kind":"user","source_ref":"approved research plan v001","reason":"Retain the existing benchmark and sweep baseline.","sensitivity_checked":true},
  {"field":"average_leaf_angle_deg","value":50.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"hot_spot","value":0.01,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"solar_zenith_deg","value":30.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"view_zenith_deg","value":10.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"relative_azimuth_deg","value":0.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"soil_brightness","value":1.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"soil_moisture_fraction","value":1.0,"source_kind":"assumption","source_ref":"existing physical run","reason":"Fixed assumed value retained from the existing physical run.","sensitivity_checked":false},
  {"field":"sweep_parameter","value":"leaf_area_index","source_kind":"user","source_ref":"approved research plan v001","reason":"Retain the existing LAI sweep.","sensitivity_checked":true},
  {"field":"sweep_start","value":0.0,"source_kind":"user","source_ref":"approved research plan v001","reason":"Retain the existing sweep range.","sensitivity_checked":true},
  {"field":"sweep_stop","value":8.0,"source_kind":"user","source_ref":"approved research plan v001","reason":"Retain the existing sweep range.","sensitivity_checked":true},
  {"field":"sweep_points","value":17,"source_kind":"user","source_ref":"approved research plan v001","reason":"Retain the existing sweep resolution.","sensitivity_checked":true}
]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
