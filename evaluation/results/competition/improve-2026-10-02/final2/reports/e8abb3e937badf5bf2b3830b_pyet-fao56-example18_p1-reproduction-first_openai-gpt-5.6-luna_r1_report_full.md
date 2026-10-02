# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated six-series figure shows that all formulations increase ET₀ as air temperature rises from **12.9 to 20.9 °C**. The curves remain distinct rather than converging: Priestley–Taylor is generally highest, while Oudin is lowest at the cool end; the other formulations occupy intermediate positions. The figure contains six series with air temperature in °C on the x-axis and ET₀ in mm d⁻¹ on the y-axis.

The chart was rendered successfully and its automatic render check passed, establishing that the plotted arrays are finite and legible. It does not establish agreement with a source figure. The recorded evidence contains the Example 18 numerical benchmark but no source figure for this temperature-sensitivity chart, so qualitative figure reproduction against a published image is **not scoreable**. The numerical Penman–Monteith benchmark remains reproduced to the published precision. [model:pyet@1.5.0] [pyet-docs#02]

### Source/generated-image conclusion

The generated image contains six labeled ET₀ curves over the same temperature range. All curves slope upward, but they have different slopes and offsets. The image therefore supports divergence in formulation response rather than convergence to a common ET₀ value. Exact numerical values are taken from the executed arrays below, not digitized from the image.

### Executed-result conclusion

All six approved runs completed successfully with nine points each and passed quality control. The recorded endpoint ranges were:

| Formulation | ET₀ range (mm d⁻¹) |
|---|---:|
| Penman | 3.6990–4.1461 |
| Penman–Monteith | 3.6948–4.0459 |
| Priestley–Taylor | 4.0234–4.7459 |
| Makkink | 3.4494–4.0688 |
| Hargreaves | 3.5619–4.5247 |
| Oudin | 2.9770–4.3407 |

At the Example 18 temperature of **16.9 °C**, Penman–Monteith produced **3.8715 mm d⁻¹**. The published Example 18 value is approximately **3.9 mm d⁻¹**, so the benchmark agrees at the published one-decimal precision. [model:pyet@1.5.0] [pyet-docs#02]

The chart tool calculated the following comparisons against Penman–Monteith over the shared nine-point range:

- Penman: bias **−0.0569 mm d⁻¹**; RMSE **0.0649 mm d⁻¹**
- Priestley–Taylor: bias **0.4658 mm d⁻¹**; RMSE **0.4742 mm d⁻¹**
- Makkink: bias **−0.1611 mm d⁻¹**; RMSE **0.1704 mm d⁻¹**
- Hargreaves: bias **0.1143 mm d⁻¹**; RMSE **0.2019 mm d⁻¹**
- Oudin: bias **−0.2706 mm d⁻¹**; RMSE **0.4009 mm d⁻¹**

These are computed-model comparisons, not measurements. [model:pyet@1.5.0]

### Comparison and qualification

| Aspect | Generated image | Executed results | Assessment |
|---|---|---|---|
| Number of curves | Six | Six nine-point runs | Agreement |
| Temperature response | All curves rise | All six arrays are monotonic increasing | Agreement |
| Separation | Curves remain visibly separated | Different endpoint ranges and computed pairwise statistics | Agreement |
| Source-figure reproduction | No source figure for this sensitivity chart was recorded | No source-image numerical comparison available | Not scoreable |
| Example 18 benchmark | Chart is a sensitivity figure, not a single-point benchmark | Penman–Monteith = 3.8715 mm d⁻¹ | Numerically consistent with published ~3.9 mm d⁻¹ |

The calibrated outcome is **partial**: the approved runs and chart were successfully produced, and the Penman–Monteith Example 18 value was reproduced at the documentation’s precision. The six-method temperature chart is a new sensitivity analysis, not a quantitatively verifiable reproduction of a published source figure.

### Guessed/assumed parameters

The authoritative ledger identifies the following non-paper-explicit inputs or choices:

- Wind speed used in the main runs: **2.078 m s⁻¹**, user-specified from the paper’s 10 m condition; the Oudin executed specification used **2.0 m s⁻¹**.
- Atmospheric pressure: **100.1 kPa**, paper-inferred from the 100 m elevation condition.
- Method selection, sweep variable, sweep limits, and point count: model assumptions.
- Mean relative humidity: **60.0%**, backend default.
- Temperature sweep: **12.9–20.9 °C**, nine points.

These choices limit interpretation: the chart compares formulations under the approved configuration and should not be treated as an observational validation.

<parameter_provenance>
[{"field":"air_temperature_c","value":{"baseline":16.9,"sweep_start":12.9,"sweep_stop":20.9,"sweep_points":9},"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 mean temperature from tmax 21.5 and tmin 12.3","reason":"Baseline is paper-derived; sweep values are the approved sensitivity configuration.","sensitivity_checked":true},{"field":"tmax_c","value":21.5,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 input","reason":"Maximum air temperature.","sensitivity_checked":false},{"field":"tmin_c","value":12.3,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 input","reason":"Minimum air temperature.","sensitivity_checked":false},{"field":"latitude_deg","value":50.8,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"50°48′ N converted to decimal degrees","reason":"Benchmark latitude.","sensitivity_checked":false},{"field":"day_of_year","value":187,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"6 July","reason":"Benchmark calendar date represented as day of year.","sensitivity_checked":false},{"field":"solar_radiation_mj_m2_day","value":22.07,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"worked-example radiation value","reason":"Incoming solar radiation.","sensitivity_checked":false},{"field":"net_radiation_mj_m2_day","value":13.28,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"worked-example net-radiation value","reason":"Net radiation.","sensitivity_checked":false},{"field":"relative_humidity_max_pct","value":84.0,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 input","reason":"Maximum relative humidity.","sensitivity_checked":false},{"field":"relative_humidity_min_pct","value":63.0,"source_kind":"paper","source_ref":"pyet-docs#02","source_span":"Example 18 input","reason":"Minimum relative humidity.","sensitivity_checked":false},{"field":"wind_speed_m_s","value":{"penman":2.078,"pm":2.078,"priestley_taylor":2.078,"makkink":2.078,"hargreaves":2.078,"oudin":2.0},"source_kind":"user","source_ref":"pyet-docs#02 plus approved executed run specifications","source_span":"paper condition: 10 km h−1 at 10 m","reason":"User-specified conversion for the first five runs; exact Oudin executed value retained.","sensitivity_checked":false},{"field":"air_pressure_kpa","value":100.1,"source_kind":"derived","source_ref":"pyet-docs#02","source_span":"100 m elevation pressure relation","reason":"Paper-inferred atmospheric pressure used by the benchmark implementation.","sensitivity_checked":false},{"field":"method","value":["penman","pm","priestley_taylor","makkink","hargreaves","oudin"],"source_kind":"assumption","source_ref":"approved research plan","reason":"One approved pyet formulation per run.","sensitivity_checked":false},{"field":"relative_humidity_pct","value":60.0,"source_kind":"model_default","source_ref":"executed pyet run specification","reason":"Backend-inserted value; not paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"air_temperature_c","source_kind":"assumption","source_ref":"approved research plan","reason":"Controlled sensitivity variable.","sensitivity_checked":true},{"field":"sweep_start","value":12.9,"source_kind":"assumption","source_ref":"approved research plan","reason":"Approved lower sweep bound.","sensitivity_checked":true},{"field":"sweep_stop","value":20.9,"source_kind":"assumption","source_ref":"approved research plan","reason":"Approved upper sweep bound.","sensitivity_checked":true},{"field":"sweep_points","value":9,"source_kind":"assumption","source_ref":"approved executed run specifications","reason":"Number of evenly spaced points in every run.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| pyet | air_temperature_c | 16.9 | paper_explicit | pyet-docs#02 |
| pyet | tmax_c | 21.5 | paper_explicit | pyet-docs#02 |
| pyet | tmin_c | 12.3 | paper_explicit | pyet-docs#02 |
| pyet | latitude_deg | 50.8 | paper_explicit | pyet-docs#02 |
| pyet | day_of_year | 187 | paper_explicit | pyet-docs#02 |
| pyet | solar_radiation_mj_m2_day | 22.07 | paper_explicit | pyet-docs#02 |
| pyet | net_radiation_mj_m2_day | 13.28 | paper_explicit | pyet-docs#02 |
| pyet | relative_humidity_max_pct | 84.0 | paper_explicit | pyet-docs#02 |
| pyet | relative_humidity_min_pct | 63.0 | paper_explicit | pyet-docs#02 |
| pyet | wind_speed_m_s | 2.078 | user_specified | pyet-docs#02 |
| pyet | air_pressure_kpa | 100.1 | paper_inferred | pyet-docs#02 |
| pyet | method | penman | model_assumption | - |
| pyet | relative_humidity_pct | 60.0 | backend_default | - |
| pyet | sweep_parameter | air_temperature_c | model_assumption | - |
| pyet | sweep_start | 12.9 | model_assumption | - |
| pyet | sweep_stop | 20.9 | model_assumption | - |
| pyet | sweep_points | 9 | model_assumption | - |
