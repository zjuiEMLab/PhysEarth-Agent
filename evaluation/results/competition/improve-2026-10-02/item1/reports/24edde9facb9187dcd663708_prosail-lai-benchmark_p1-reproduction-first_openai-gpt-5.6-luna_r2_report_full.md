# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated LAI figure shows a clear vegetation-saturation pattern: as LAI increases from 0.5 to 6.0, red and SWIR reflectance decline, NIR reflectance and NDVI rise, and the curves flatten toward higher LAI. The figure contains five supported-model series and is legible. Because no inspected source image with comparable plotted curves is recorded, qualitative agreement with the paper figure is **not identifiable**.

The reproduction is therefore **partial**: the registered PROSAIL run successfully reproduces supported-model benchmark and LAI-sensitivity outputs, but it does not reproduce the unavailable PROSAIL-5/4SAIL configuration with spherical leaf-angle distribution. [model:prosail@2.0.5] [prosail-docs#00]

## Conclusion supported by the generated figure

The generated image supports the following qualitative ordering and shape:

- Green, red, and SWIR reflectance generally decrease with LAI.
- NIR reflectance increases with LAI.
- NDVI increases strongly and then approaches a plateau.
- The largest transition occurs near the low-LAI endpoint, especially between LAI 0.5 and 1.0.

The render check confirms that the plotted arrays were finite, sufficiently sampled, and legible; it does not establish agreement with the paper image.

## Conclusion supported by the recorded result arrays

The benchmark at LAI 3.0 produced green reflectance 0.0583, red reflectance 0.0233, NIR reflectance 0.4465, SWIR reflectance 0.2344, and NDVI 0.9006. The LAI sweep produced:

| Quantity | LAI 0.5 | LAI 6.0 | Recorded pattern |
|---|---:|---:|---|
| Green reflectance | 0.1715 | 0.0530 | Overall decrease; slight endpoint upturn at LAI 6.0 |
| Red reflectance | 0.1803 | 0.0167 | Decrease |
| NIR reflectance | 0.3970 | 0.4777 | Increase |
| SWIR reflectance | 0.4252 | 0.2115 | Decrease |
| NDVI | 0.3755 | 0.9326 | Increase |

These values are model outputs, not measurements. [model:prosail@2.0.5]

## Comparison and limitations

| Comparison | Finding |
|---|---|
| Generated image versus recorded arrays | Agreement: the image displays the same five series and qualitative trends reported by the arrays. |
| Generated image versus source-paper figure | Not scoreable: no inspected source image or digitized reference curves are recorded. |
| Supported model versus requested paper configuration | Partial: the registered PROSAIL implementation ran successfully, but PROSAIL-5 with 4SAIL and spherical LAD was unavailable. |
| Numerical agreement metrics | N/A; no source digitization, bias, RMSE, correlation, or other comparison statistic was supplied. |

The paper-explicit benchmark inputs were mapped directly where supported. Pigment and geometry values not specified by the paper configuration were assumed or retained as registered defaults; these choices limit exact reproducibility. [prosail-docs#00]

## Assumed parameters

The following are not paper-explicit: anthocyanin and brown-pigment values were model assumptions. Average leaf angle, hotspot, solar and viewing geometry, relative azimuth, soil brightness, soil moisture fraction, sweep parameter, and sweep points were backend defaults. The sweep bounds, 0.5–6.0, were retained as model assumptions in the authoritative ledger and are not treated as paper evidence.

<parameter_provenance>
[
  {"field":"leaf_structure","value":1.5,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct benchmark input mapping","reason":"Direct benchmark input mapping.","sensitivity_checked":false},
  {"field":"chlorophyll_ug_cm2","value":40,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct benchmark input mapping","reason":"Direct benchmark input mapping.","sensitivity_checked":false},
  {"field":"carotenoid_ug_cm2","value":8,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct benchmark input mapping","reason":"Direct benchmark input mapping.","sensitivity_checked":false},
  {"field":"equivalent_water_thickness_cm","value":0.01,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct benchmark input mapping","reason":"Direct benchmark input mapping.","sensitivity_checked":false},
  {"field":"dry_matter_g_cm2","value":0.009,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct benchmark input mapping","reason":"Direct benchmark input mapping.","sensitivity_checked":false},
  {"field":"leaf_area_index","value":3,"source_kind":"paper","source_ref":"prosail-docs#00","source_span":"Direct benchmark input mapping","reason":"Direct benchmark input mapping for the benchmark run.","sensitivity_checked":false},
  {"field":"anthocyanin_ug_cm2","value":0,"source_kind":"assumption","source_ref":"none; held at registered default/green-leaf assumption","reason":"No paper value was supplied for this supported configuration.","sensitivity_checked":false},
  {"field":"brown_pigment","value":0,"source_kind":"assumption","source_ref":"none; held at registered default/green-leaf assumption","reason":"No paper value was supplied for this supported configuration.","sensitivity_checked":false},
  {"field":"average_leaf_angle_deg","value":50,"source_kind":"model_default","source_ref":"Registered default retained","reason":"The paper's spherical LAD was unavailable in the registered model.","sensitivity_checked":false},
  {"field":"hot_spot","value":0.01,"source_kind":"model_default","source_ref":"Registered default retained","reason":"No supported paper-specific hotspot value was available.","sensitivity_checked":false},
  {"field":"solar_zenith_deg","value":30,"source_kind":"model_default","source_ref":"Registered default retained","reason":"No supported paper-specific solar geometry value was available.","sensitivity_checked":false},
  {"field":"view_zenith_deg","value":10,"source_kind":"model_default","source_ref":"Registered default retained","reason":"No supported paper-specific viewing geometry value was available.","sensitivity_checked":false},
  {"field":"relative_azimuth_deg","value":0,"source_kind":"model_default","source_ref":"Registered default retained","reason":"No supported paper-specific relative azimuth was available.","sensitivity_checked":false},
  {"field":"soil_brightness","value":1,"source_kind":"model_default","source_ref":"Registered default retained","reason":"No supported paper-specific soil-background value was available.","sensitivity_checked":false},
  {"field":"soil_moisture_fraction","value":1,"source_kind":"model_default","source_ref":"Registered default retained","reason":"No supported paper-specific soil-wetness value was available.","sensitivity_checked":false},
  {"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"The registered model inserted this value during parameter resolution","reason":"Benchmark run used no sweep; the LAI run separately used leaf_area_index.","sensitivity_checked":false},
  {"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"The registered model inserted this value during parameter resolution","reason":"Backend-resolved default retained for the fixed benchmark specification.","sensitivity_checked":false},
  {"field":"sweep_start","value":0.5,"source_kind":"assumption","source_ref":"none; submitted run retained this value without attached paper/user evidence","reason":"Lower bound of the approved LAI sweep; not treated as paper-derived.","sensitivity_checked":false},
  {"field":"sweep_stop","value":6.0,"source_kind":"assumption","source_ref":"none; submitted run retained this value without attached paper/user evidence","reason":"Upper bound of the approved LAI sweep; not treated as paper-derived.","sensitivity_checked":false}
]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
