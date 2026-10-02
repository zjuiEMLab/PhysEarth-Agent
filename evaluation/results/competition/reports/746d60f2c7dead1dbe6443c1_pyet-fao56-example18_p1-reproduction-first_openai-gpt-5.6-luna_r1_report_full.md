# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure shows a two-point ET₀ result that increases slightly with mean air temperature: **4.0102 mm d⁻¹ at 16.8 °C** and **4.0217 mm d⁻¹ at 17.0 °C** [model:pyet@1.5.0]. It does not establish convergence or divergence between multiple formulations because only one Penman series was generated.

The Penman benchmark run completed successfully. The requested six-formulation comparison is **not identifiable** from the recorded execution because those additional formulations and a single paper reference curve were unavailable.

## Supporting results

### Conclusion supported by the generated image

The generated figure contains one series, with:

- x-axis: mean air temperature (°C)
- y-axis: reference ET₀ (mm d⁻¹)
- two plotted points
- a small upward ordering from the lower to the higher temperature

No source-paper figure was available for a curve-by-curve visual comparison. Therefore, qualitative correspondence with a source image is **not scoreable**. The passed render check establishes only that the generated chart was legible.

### Conclusion supported by the result arrays

The recorded result contains:

- ET₀ minimum: **4.0102 mm d⁻¹**
- ET₀ maximum: **4.0217 mm d⁻¹**
- plotted range: **16.8–17.0 °C**
- number of points: **2**

No bias, RMSE, correlation, threshold, or percentage difference was computed. Those statistics are **N/A**.

### Comparison

| Evidence | Supported conclusion | Qualification |
|---|---|---|
| Generated image | One Penman series rises slightly across the two plotted temperatures | It does not compare formulations or prove numerical agreement with the source |
| Result arrays | ET₀ increases from 4.0102 to 4.0217 mm d⁻¹ | These are model outputs, not measurements |
| Source comparison | Not scoreable | No source figure or single reference curve was available |

## Guessed/assumed parameters

The authoritative ledger identifies the following non-paper-explicit choices:

- **Derived from paper inputs:** `air_temperature_c = 16.9`, `day_of_year = 187`, `air_pressure_kpa = 100.1`, and `net_radiation_mj_m2_day = 13.6`.
- **Model defaults:** `solar_radiation_mj_m2_day = 20.0`, `relative_humidity_pct = 60.0`, `sweep_parameter = none`, and `sweep_points = 10`.
- **Model assumptions:** `sweep_start = 16.8` and `sweep_stop = 17.0`.

There is a recorded-state inconsistency: the authoritative ledger describes a fixed benchmark run with `sweep_parameter = none`, whereas the formal run record reports a two-point `air_temperature_c` sweep from 16.8 to 17.0 °C. The numerical results above follow the formal run record.

## Limitations

The result is a **partial reproduction**. The Penman computation was successful, but the six-formulation comparison was not executed, no single paper reference curve was available, and no source-figure comparison could be made. The two-point result supports only the observed local increase in the registered Penman calculation [pyet-docs#02].

<parameter_provenance>
[{"field":"method","value":"penman","source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 Penman benchmark formulation","reason":"Use registered Penman formulation.","sensitivity_checked":false},{"field":"air_temperature_c","value":16.9,"source_kind":"derived","source_ref":"pyet-docs#02","source_span":"mean temperature derived from Example 18 extremes","reason":"(21.5+12.3)/2.","sensitivity_checked":false},{"field":"tmax_c","value":21.5,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 maximum temperature","reason":"Direct mapping.","sensitivity_checked":false},{"field":"tmin_c","value":12.3,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 minimum temperature","reason":"Direct mapping.","sensitivity_checked":false},{"field":"latitude_deg","value":50.8,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 latitude","reason":"Direct mapping.","sensitivity_checked":false},{"field":"day_of_year","value":187,"source_kind":"derived","source_ref":"pyet-docs#02","source_span":"6 July converted to non-leap-year day count","reason":"Non-leap-year day count.","sensitivity_checked":false},{"field":"wind_speed_m_s","value":2.078,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 wind speed","reason":"Direct mapping.","sensitivity_checked":false},{"field":"relative_humidity_max_pct","value":84.0,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 maximum relative humidity","reason":"Direct mapping.","sensitivity_checked":false},{"field":"relative_humidity_min_pct","value":63.0,"source_kind":"paper","source_span":"Example 18 minimum relative humidity","reason":"Direct mapping.","sensitivity_checked":false},{"field":"air_pressure_kpa","value":100.1,"source_kind":"derived","source_ref":"pyet-docs#02","source_span":"pressure mapping for Example 18","reason":"Adapter requires pressure rather than elevation.","sensitivity_checked":false},{"field":"net_radiation_mj_m2_day","value":13.6,"source_kind":"derived","source_ref":"pyet-docs#02","source_span":"documented Example 18 radiation inputs","reason":"Inferred mapping from documented Example 18 radiation inputs.","sensitivity_checked":false},{"field":"solar_radiation_mj_m2_day","value":20.0,"source_kind":"model_default","source_ref":"registered pyet default; no paper evidence","reason":"Unused by Penman but resolved by backend.","sensitivity_checked":false},{"field":"relative_humidity_pct","value":60.0,"source_kind":"model_default","source_ref":"registered pyet default; no paper evidence","reason":"Extrema are supplied; mean RH is unused.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"registered pyet default; authoritative ledger","reason":"Fixed benchmark run according to the ledger; formal run record instead reports an air-temperature sweep.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"registered pyet default; authoritative ledger","reason":"No sweep is requested according to the ledger.","sensitivity_checked":false},{"field":"sweep_start","value":16.8,"source_kind":"assumption","source_ref":"approved run record; no paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence.","sensitivity_checked":false},{"field":"sweep_stop","value":17.0,"source_kind":"assumption","source_ref":"approved run record; no paper or user evidence","reason":"The submitted run retained this value without attached paper/user evidence.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
