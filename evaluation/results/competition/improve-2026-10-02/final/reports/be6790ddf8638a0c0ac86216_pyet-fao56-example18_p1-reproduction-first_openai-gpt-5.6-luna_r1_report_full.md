# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 shows one increasing daily reference-evapotranspiration curve as mean air temperature increases from **12.9 to 20.9 °C**. There are no multiple curves, crossings, convergence, or divergence to compare. The computed ET0 increases from **3.376128180636503 mm d⁻¹** to **4.0210230122334085 mm d⁻¹** across the nine-point sweep. [model:pyet@1.5.0]

The result is **partial**: the pyet output and generated chart are available, but a quantitative comparison with the source result is not identifiable from the recorded state. [skill:research-reporting]

### Source/generated-image conclusion

Figure 1 contains one series, with mean air temperature in °C on the x-axis and reference evapotranspiration in mm d⁻¹ on the y-axis. The plotted curve rises monotonically across the displayed range. The render check confirms that the plotted series is legible; it does not establish agreement with a source figure. [model:pyet@1.5.0]

### Result-backed conclusion

The formal result handle is `res_3b8be5670188`. It contains nine `et0_mm_day` values indexed by `air_temperature_c`. The series is monotonic increasing, with a minimum of **3.376128180636503 mm d⁻¹**, a maximum of **4.0210230122334085 mm d⁻¹**, and a mean of **3.7054 mm d⁻¹**. [model:pyet@1.5.0]

No correlation, RMSE, bias, threshold, or independent validation statistic was supplied; these quantities are **N/A**.

### Comparison

| Aspect | Figure-based reading | Result-backed reading | Qualification |
|---|---|---|---|
| Series count | One curve | One `et0_mm_day` series | Agreement |
| Temperature range | 12.9–20.9 °C | 12.9–20.9 °C over 9 points | Agreement |
| Trend | Increasing | Monotonic increasing | Same qualitative pattern |
| Source comparison | Not identifiable from the recorded state | No source-comparison statistic recorded | Quantitative reproduction is not scoreable |

## Assumed parameters

All non-explicit inputs remain classified as guessed or assumed. The parameter-source table is provided in the required machine-readable appendix below. The run used the `penman` method, backend-default meteorological values, and an assumed air-temperature sweep from **12.9 to 20.9 °C** with **9** points. [model:pyet@1.5.0]

## Limitations

The result describes this registered pyet configuration only. It does not establish a paper-value reproduction, a six-formulation comparison, or agreement with an independent observation. The requested source-based numerical comparison is not identifiable from the recorded evidence. [skill:research-reporting]

<parameter_provenance>[{"field":"air_temperature_c","value":"20.0","source_kind":"model_default","source_ref":"none; registered pyet parameter resolution","reason":"Exact resolved physical value retained by the approved run.","sensitivity_checked":false},{"field":"method","value":"penman","source_kind":"assumption","source_ref":"none; approved run configuration","reason":"The submitted run retained this method without attached paper or user evidence.","sensitivity_checked":false},{"field":"latitude_deg","value":"40.0","source_kind":"model_default","source_ref":"none; registered pyet parameter resolution","reason":"Inserted by the registered model as a backend default.","sensitivity_checked":false},{"field":"day_of_year","value":"182","source_kind":"model_default","source_ref":"none; registered pyet parameter resolution","reason":"Inserted by the registered model as a backend default.","sensitivity_checked":false},{"field":"net_radiation_mj_m2_day","value":"12.0","source_kind":"model_default","source_ref":"none; registered pyet parameter resolution","reason":"Inserted by the registered model as a backend default.","sensitivity_checked":false},{"field":"solar_radiation_mj_m2_day","value":"20.0","source_kind":"model_default","source_ref":"none; registered pyet parameter resolution","reason":"Inserted by the registered model as a backend default.","sensitivity_checked":false},{"field":"wind_speed_m_s","value":"2.0","source_kind":"model_default","source_ref":"none; registered pyet parameter resolution","reason":"Inserted by the registered model as a backend default.","sensitivity_checked":false},{"field":"relative_humidity_pct","value":"60.0","source_kind":"model_default","source_ref":"none; registered pyet parameter resolution","reason":"Inserted by the registered model as a backend default.","sensitivity_checked":false},{"field":"air_pressure_kpa","value":"101.3","source_kind":"model_default","source_ref":"none; registered pyet parameter resolution","reason":"Inserted by the registered model as a backend default.","sensitivity_checked":false},{"field":"sweep_parameter","value":"air_temperature_c","source_kind":"assumption","source_ref":"none; approved temperature-response sweep","reason":"The submitted run retained this sweep axis without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_start","value":"12.9","source_kind":"assumption","source_ref":"none; approved temperature-response sweep","reason":"The submitted run retained this lower sweep endpoint without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_stop","value":"20.9","source_kind":"assumption","source_ref":"none; approved temperature-response sweep","reason":"The submitted run retained this upper sweep endpoint without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_points","value":"9","source_kind":"assumption","source_ref":"none; approved temperature-response sweep","reason":"The submitted run retained this sweep density without attached paper or user evidence.","sensitivity_checked":false}]</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| pyet | air_temperature_c | 20.0 | backend_default | - |
| pyet | method | penman | model_assumption | - |
| pyet | latitude_deg | 40.0 | backend_default | - |
| pyet | day_of_year | 182 | backend_default | - |
| pyet | net_radiation_mj_m2_day | 12.0 | backend_default | - |
| pyet | solar_radiation_mj_m2_day | 20.0 | backend_default | - |
| pyet | wind_speed_m_s | 2.0 | backend_default | - |
| pyet | relative_humidity_pct | 60.0 | backend_default | - |
| pyet | air_pressure_kpa | 101.3 | backend_default | - |
| pyet | sweep_parameter | air_temperature_c | model_assumption | - |
| pyet | sweep_start | 12.9 | model_assumption | - |
| pyet | sweep_stop | 20.9 | model_assumption | - |
| pyet | sweep_points | 9 | model_assumption | - |
