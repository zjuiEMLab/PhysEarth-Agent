# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure shows one finite, legible ET₀ curve that is constant across day-of-year 180–194. Thus, under the fixed approved inputs, the diagnostic shows neither divergence nor changing ordering: the single series remains flat. The baseline result is **4.7729 mm d⁻¹** [model:pyet@1.5.0].

This is a partial reproduction rather than an exact FAO-56 benchmark reproduction. The registered Penman run completed successfully, but the approved FAO-56 benchmark implementation and the six-formulation comparison were unavailable. The source figure was not inspected, so correspondence with a paper image is not identifiable.

## Supporting results

### Generated-figure conclusion

Figure 1 contains one series with:

- x-axis: day of year;
- y-axis: reference evapotranspiration, mm d⁻¹;
- 15 plotted points;
- a constant visible line;
- successful render-legibility check.

The figure supports the qualitative conclusion that the approved diagnostic is flat. It does not independently establish numerical agreement with the paper.

### Result-array conclusion

The baseline run returned **4.7729 mm d⁻¹**. The day-of-year sweep returned the same value at every evaluated point from 180 through 194 [model:pyet@1.5.0]. No bias, RMSE, correlation, or other validation statistic was supplied; numerical agreement with the unavailable FAO-56 implementation is therefore **not scoreable**.

The opened documentation describes Example 18 and its benchmark tests [pyet-docs#02]. However, the approved evaluation recorded the exact FAO-56 benchmark implementation as unavailable, so the executed Penman result cannot be treated as an exact reproduction.

| Aspect | Generated figure | Result arrays | Assessment |
|---|---|---|---|
| Series count | One | One | Agreement |
| Trend over the diagnostic range | Constant | 4.7729 mm d⁻¹ at all points | Agreement |
| Numerical comparison with FAO-56 | Not supplied by the image | Not scoreable | Unresolved |
| Comparison with a source image | No inspected source image | Not applicable | Not identifiable |

## Assumed and backend-supplied parameters

The following values are not independent evidence from the paper and are reported according to the authoritative ledger:

- **Backend defaults:** `solar_radiation_mj_m2_day=20.0`, `relative_humidity_pct=60.0`, and baseline `sweep_points=10`.
- **Model assumptions:** `sweep_start=180.0` and `sweep_stop=194.0`.
- **User-specified diagnostic:** `sweep_parameter=day_of_year`.
- The ledger classifies the remaining listed inputs as paper-explicit; they were used as the approved run configuration. The documentation identifies the relevant Penman and Example 18 material [pyet-docs#00] [pyet-docs#02].

## Limitations

The result is limited to the registered pyet Penman implementation and the approved parameterization. The unavailable FAO-56 benchmark implementation and unavailable six-formulation comparison prevent a complete reproduction. The flat date diagnostic is a property of the fixed-input approved run; it should not be generalized to all evapotranspiration calculations. No source-image comparison or validation statistic was performed.

## Final conclusion

The approved experiment produced a constant ET₀ of **4.7729 mm d⁻¹** across day-of-year 180–194, so the generated figure supports convergence to a flat single-series result. The broader paper reproduction remains **partial**, because the exact reference implementation and comparison set were unavailable.

<parameter_provenance>
[{"field":"method","value":"penman","source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 Penman configuration","reason":"Use registered Penman configuration.","sensitivity_checked":false},{"field":"air_temperature_c","value":20.1,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 air-temperature input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"tmax_c","value":26.6,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 maximum-temperature input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"tmin_c","value":13.6,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 minimum-temperature input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"latitude_deg","value":50.8,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 latitude input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"day_of_year","value":187,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"6 July Example 18 date","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":true},{"field":"net_radiation_mj_m2_day","value":14.5,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 net-radiation input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"wind_speed_m_s","value":2.0,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 wind-speed input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"relative_humidity_max_pct","value":84.0,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 maximum relative humidity","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"relative_humidity_min_pct","value":43.0,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 minimum relative humidity","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"air_pressure_kpa","value":101.3,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 air-pressure input","reason":"The registered input was mapped to the opened paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"day_of_year","source_kind":"user","source_ref":"user-approved diagnostic","reason":"Hold Example 18 conditions fixed and vary date.","sensitivity_checked":true},{"field":"solar_radiation_mj_m2_day","value":20.0,"source_kind":"model_default","source_ref":"registered pyet default","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},{"field":"relative_humidity_pct","value":60.0,"source_kind":"model_default","source_ref":"registered pyet default","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"registered pyet default","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_start","value":180.0,"source_kind":"assumption","source_ref":"approved run specification","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":true},{"field":"sweep_stop","value":194.0,"source_kind":"assumption","source_ref":"approved run specification","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
