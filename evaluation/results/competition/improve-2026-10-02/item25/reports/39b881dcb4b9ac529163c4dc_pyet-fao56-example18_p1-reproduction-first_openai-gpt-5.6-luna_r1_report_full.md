# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows seven increasing reference-evapotranspiration curves as air temperature rises. Hargreaves is highest across the broad temperature sweep, Priestley–Taylor is generally lowest, and the curves remain ordered without a reported crossing. The generated figure therefore supports a clear divergence in magnitude among formulations rather than convergence. [model:pyet@1.5.0]

This is a **partial reproduction**: the supported PyET formulation cases were executed successfully, but FAO-56 was unavailable and was not run. The chart was rendered successfully and passed the automatic legibility check; that check establishes usability of the plotted arrays, not agreement with a source figure.

## Conclusion supported by the generated image

Figure 1 has seven series, with air temperature (°C) on the x-axis and reference evapotranspiration, ET0 (mm day⁻¹), on the y-axis. The curves rise smoothly over the displayed temperature range. The broad-sweep curves preserve the same qualitative ordering: Hargreaves is highest, PM and Penman occupy intermediate positions, and Priestley–Taylor is lower at the warm end. [model:pyet@1.5.0]

No digitized values or source-figure agreement statistic is available from the image itself. Quantitative agreement with the source figure is therefore **not scoreable** from the recorded state.

## Conclusion supported by the executed results

The broad sweeps used nine points from 0 to 40 °C. The computed ranges were:

- Penman: 1.8948–4.4426 mm day⁻¹
- PM: 1.8104–5.4955 mm day⁻¹
- Priestley–Taylor: 2.0028–4.4697 mm day⁻¹
- Hargreaves: 2.1606–7.2913 mm day⁻¹

All four sweeps were monotonically increasing. At 20 °C, the outputs were 3.3971 mm day⁻¹ for the Penman baseline, 3.7896 mm day⁻¹ for PM, 3.5041 mm day⁻¹ for Priestley–Taylor, and 4.6766 mm day⁻¹ for Hargreaves. [model:pyet@1.5.0]

For the common 19–21 °C baseline interval, the recorded chart comparison supplied a Priestley–Taylor-minus-PM bias of −0.2856 mm day⁻¹ and a Hargreaves-minus-PM bias of 0.8873 mm day⁻¹. These are comparisons among model outputs, not validation statistics against observations. [model:pyet@1.5.0]

## Comparison and qualifications

| Aspect | Figure-based reading | Result-backed reading | Assessment |
|---|---|---|---|
| Temperature response | All curves rise | All four broad sweeps are monotonically increasing | Agreement |
| Formulation ordering | Hargreaves is highest; Priestley–Taylor is lower | Same ordering at the recorded sweep endpoints and at 20 °C | Qualitative agreement |
| Separation | Curves diverge in magnitude toward warmer temperatures | The endpoint ranges show increasing differences among formulations | Agreement, conditional on fixed inputs |
| Source-figure reproduction | Not quantitatively identifiable from the recorded state | No source-figure digitization or comparison statistic was recorded | Not scoreable |
| Complete method coverage | Seven generated series are shown | FAO-56 was unavailable and unrun | Partial reproduction |

The differences among formulations reflect the approved fixed meteorological assumptions and the registered PyET implementation. They should not be interpreted as a comparison against measured evapotranspiration.

## Guessed/assumed parameters

The following values were not paper-explicit and are retained with their authoritative provenance classes.

| Parameter | Value | Provenance | Reason |
|---|---:|---|---|
| air_temperature_c | 20 | model_assumption | Common fixed baseline for the supported sensitivity experiment |
| net_radiation_mj_m2_day | 10 | model_assumption | Held fixed across formulations |
| wind_speed_m_s | 2 | model_assumption | Held fixed across wind-dependent formulations |
| relative_humidity_pct | 60 | model_assumption | Held fixed where required |
| latitude_deg | 45 | model_assumption | Held fixed for radiation/temperature formulations |
| day_of_year | 180 | model_assumption | Held fixed |
| tmin_c | 15 | model_assumption | Hargreaves input assumption |
| tmax_c | 25 | model_assumption | Hargreaves input assumption |
| method | penman | model_assumption | Retained by the submitted run without attached paper or user evidence |
| solar_radiation_mj_m2_day | 20.0 | backend_default | Inserted during registered-model parameter resolution |
| air_pressure_kpa | 101.3 | backend_default | Inserted during registered-model parameter resolution |
| sweep_parameter | none | backend_default | Inserted during registered-model parameter resolution |
| sweep_points | 10 | backend_default | Inserted during registered-model parameter resolution |
| sweep_start | 19.0 | model_assumption | Retained by the submitted run without attached paper or user evidence |
| sweep_stop | 21.0 | model_assumption | Retained by the submitted run without attached paper or user evidence |

The paper documentation was used for the supported PyET context, but none of the listed values above is classified as paper-derived in the authoritative ledger. [pyet-docs#00] [pyet-docs#01] [pyet-docs#02]

## Limitations

The results are model outputs, not measurements. The temperature sweeps vary air temperature while holding the other listed inputs fixed, so they show controlled formulation sensitivity rather than a complete meteorological scenario. FAO-56 was unavailable, and quantitative reproduction of the source figure is not identifiable from the recorded state. The calibrated conclusion is therefore that the supported PyET formulations reproduce the reported qualitative pattern of increasing ET0 with temperature and differing formulation magnitudes, but complete reproduction is not established. [model:pyet@1.5.0]

<parameter_provenance>
[{"field":"air_temperature_c","value":20,"source_kind":"assumption","source_ref":"pyet-docs#02","reason":"Common fixed baseline for the supported sensitivity experiment.","sensitivity_checked":true},{"field":"net_radiation_mj_m2_day","value":10,"source_kind":"assumption","source_ref":"pyet-docs#02","reason":"Held fixed across formulations.","sensitivity_checked":false},{"field":"wind_speed_m_s","value":2,"source_kind":"assumption","source_ref":"pyet-docs#02","reason":"Held fixed across wind-dependent formulations.","sensitivity_checked":false},{"field":"relative_humidity_pct","value":60,"source_kind":"assumption","source_ref":"pyet-docs#02","reason":"Held fixed where required.","sensitivity_checked":false},{"field":"latitude_deg","value":45,"source_kind":"assumption","source_ref":"pyet-docs#02","reason":"Held fixed for radiation and temperature formulations.","sensitivity_checked":false},{"field":"day_of_year","value":180,"source_kind":"assumption","source_ref":"pyet-docs#02","reason":"Held fixed.","sensitivity_checked":false},{"field":"tmin_c","value":15,"source_kind":"assumption","source_ref":"pyet-docs#02","reason":"Hargreaves input assumption.","sensitivity_checked":false},{"field":"tmax_c","value":25,"source_kind":"assumption","source_ref":"pyet-docs#02","reason":"Hargreaves input assumption.","sensitivity_checked":false},{"field":"method","value":"penman","source_kind":"assumption","source_ref":"none","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"solar_radiation_mj_m2_day","value":20.0,"source_kind":"model_default","source_ref":"none","reason":"The registered model inserted this value during parameter resolution.","sensitivity_checked":false},{"field":"air_pressure_kpa","value":101.3,"source_kind":"model_default","source_ref":"none","reason":"The registered model inserted this value during parameter resolution.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"none","reason":"The registered model inserted this value during parameter resolution.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"none","reason":"The registered model inserted this value during parameter resolution.","sensitivity_checked":false},{"field":"sweep_start","value":19.0,"source_kind":"assumption","source_ref":"none","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_stop","value":21.0,"source_kind":"assumption","source_ref":"none","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
