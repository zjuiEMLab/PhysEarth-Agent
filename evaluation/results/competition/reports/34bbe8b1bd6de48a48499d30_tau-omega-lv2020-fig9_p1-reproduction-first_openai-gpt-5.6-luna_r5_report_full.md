# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated tau–omega figure shows two ordered, smoothly decreasing brightness-temperature curves: both \(TB_H\) and \(TB_V\) decline as soil moisture increases from 0.01 to 0.60 m³/m³, with \(TB_V\) remaining above \(TB_H\) throughout the sweep. This is qualitatively consistent with the negative soil-moisture/brightness-temperature association visible in the source figure, but it is not a full reproduction: the source is a two-panel joint-density plot from CMEM, whereas the generated figure is a deterministic two-curve tau–omega diagnostic [cmem-sampling-density#fig-fig09].

The supported reproduction outcome is therefore **partial**. The tau–omega component was successfully run, but CMEM was unavailable and no numerical comparison, digitization, bias, RMSE, or correlation was supplied.

## Supporting results

The formal baseline run used 1.41 GHz, 40° incidence, and soil moisture 0.25 m³/m³. It produced:

- \(TB_H = 224.8044\) K
- \(TB_V = 246.4358\) K

The 25-point sweep produced the following recorded endpoint results:

| Quantity | At 0.01 m³/m³ | At 0.60 m³/m³ | Recorded pattern |
|---|---:|---:|---|
| \(TB_H\) | 264.3791 K | 212.2743 K | Monotonically decreasing |
| \(TB_V\) | 280.1328 K | 231.4606 K | Monotonically decreasing |

The generated figure has soil moisture on the x-axis and brightness temperature in kelvin on the y-axis, with two model series. Its render check passed, establishing that the plotted arrays were finite, sufficiently sampled, and legible. That check does not establish agreement with the source image.

## Source-image conclusion

The source figure contains two panels, H and V polarization, showing joint density between brightness temperature and soil moisture. Both panels show an overall negative association: warmer brightness temperatures are concentrated toward lower soil moisture, while cooler values occur toward higher soil moisture. The V-polarization distribution is generally warmer than the H-polarization distribution. The source uses density-colored scatter distributions rather than the generated chart’s continuous model curves [figure:cmem-sampling-density#fig09].

## Generated-array conclusion

The actual model arrays show a strictly decreasing response in both polarizations over the approved sweep. The V-polarized brightness temperature is higher than the H-polarized brightness temperature at the recorded endpoints and at the baseline state. The numerical comparison is limited to these model outputs; no measured reference series or digitized source values were used [model:tau_omega@1.0.0].

## Comparison and qualification

| Aspect | Source figure | Generated figure | Assessment |
|---|---|---|---|
| Soil-moisture relationship | Overall negative association | Monotonic decrease in both polarizations | Same qualitative direction |
| Polarization ordering | V distribution generally warmer than H | \(TB_V > TB_H\) in the recorded model results | Qualitatively consistent |
| Representation | Joint-density scatter distributions | Two deterministic model curves | Not the same plotted quantity |
| Numerical agreement | Not digitized | Model values recorded above | Not scoreable |
| Original model | CMEM | tau–omega | Partial reproduction only |

The qualitative correspondence is therefore limited to the direction of the soil-moisture response and the warmer V-polarization ordering. Differences in distribution shape, density structure, and numerical values cannot be interpreted as model disagreement because CMEM was unavailable and the generated experiment used assumed parameters.

## Guessed/assumed parameters

The following ledger entries were not paper-explicit and are retained as model assumptions or user-specified settings:

- `soil_moisture`: 0.01–0.60 m³/m³ sweep; `model_assumption`
- `angle_deg`: 40.0°; `model_assumption`
- `bulk_density_g_cm3`: 1.3; `model_assumption`
- `soil_temperature_k`: 293.0 K; `model_assumption`
- `canopy_temperature_k`: 293.0 K; `model_assumption`
- `vegetation_optical_depth`: 0.3; `model_assumption`
- `single_scattering_albedo`: 0.05; `model_assumption`
- `roughness_h`: 0.3; `model_assumption`
- `cross_q`: 0.0; `model_assumption`
- `sweep_parameter`: `soil_moisture` for the sweep and `none` for the baseline; `model_assumption`
- `sweep_start`: 0.01; `model_assumption`
- `sweep_stop`: 0.6; `model_assumption`
- `sweep_points`: 25; `user_specified`
- `sweep_parameter`: `none` where omitted in the baseline; `backend_default`

The frequency, 1.41 GHz, was the paper-explicit mapping to the paper’s L-band context [cmem-sampling-density#03]. The tau–omega modelling context and supported component were taken from the opened paper sections [cmem-sampling-density#03] [cmem-sampling-density#06].

## Limitations

This report does not claim full reproduction of the paper’s Fig. 9. CMEM was unavailable, the source density field was not digitized, and no statistical comparison was performed. Consequently, bias, RMSE, correlation, percent error, and numerical source-to-model agreement are **not scoreable**. The final calibrated outcome is **partial**.

<parameter_provenance>
[{"field":"frequency_ghz","value":1.41,"source_kind":"paper","source_ref":"cmem-sampling-density#03","source_span":"L-band brightness-temperature modelling context","reason":"The registered frequency input is mapped to the opened paper's L-band context.","sensitivity_checked":false},{"field":"soil_moisture","value":"0.01–0.60 sweep","source_kind":"assumption","source_ref":"approved run definition","source_span":"","reason":"The soil-moisture input is swept over the registered physical range for the supported diagnostic.","sensitivity_checked":true},{"field":"angle_deg","value":40.0,"source_kind":"assumption","source_ref":"approved plan; paper-to-model mapping","source_span":"","reason":"A fixed legal geometry is retained as a model assumption.","sensitivity_checked":false},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"approved plan; paper-to-model mapping","source_span":"","reason":"A fixed legal soil density is retained as a model assumption.","sensitivity_checked":false},{"field":"soil_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"approved plan; paper-to-model mapping","source_span":"","reason":"A fixed legal soil temperature is retained as a model assumption.","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"approved plan; paper-to-model mapping","source_span":"","reason":"A fixed legal canopy temperature is retained as a model assumption.","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.3,"source_kind":"assumption","source_ref":"approved plan; paper-to-model mapping","source_span":"","reason":"A fixed legal vegetation optical depth is retained as a model assumption.","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.05,"source_kind":"assumption","source_ref":"approved plan; paper-to-model mapping","source_span":"","reason":"A fixed legal single-scattering albedo is retained as a model assumption.","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"assumption","source_ref":"approved plan; paper-to-model mapping","source_span":"","reason":"A fixed legal roughness parameter is retained as a model assumption.","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"assumption","source_ref":"approved plan; paper-to-model mapping","source_span":"","reason":"The legal default-like value is retained explicitly as a model assumption.","sensitivity_checked":false},{"field":"sweep_parameter","value":"soil_moisture for sweep; none for baseline","source_kind":"assumption","source_ref":"approved run definitions","source_span":"","reason":"The sweep selector is set by the preserved experiment design.","sensitivity_checked":true},{"field":"sweep_start","value":0.01,"source_kind":"assumption","source_ref":"approved sweep definition","source_span":"","reason":"The start value is retained from the preserved sweep.","sensitivity_checked":true},{"field":"sweep_stop","value":0.6,"source_kind":"assumption","source_ref":"approved sweep definition","source_span":"","reason":"The stop value is retained from the preserved sweep.","sensitivity_checked":true},{"field":"sweep_points","value":25,"source_kind":"user","source_ref":"approved research plan","source_span":"","reason":"The number of sweep points is retained from the preserved run.","sensitivity_checked":true},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"tau_omega registered input default","source_span":"","reason":"The baseline omits the sweep selector and uses the backend default.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
