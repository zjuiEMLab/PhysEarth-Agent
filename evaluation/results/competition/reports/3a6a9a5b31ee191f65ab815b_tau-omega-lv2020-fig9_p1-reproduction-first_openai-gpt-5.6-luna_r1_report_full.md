# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure shows H- and V-polarized brightness temperatures decreasing as soil moisture increases from **0.05 to 0.50 m³ m⁻³**, with V remaining above H throughout. This is the same qualitative pattern visible in the inspected source figure: two separated, declining polarization curves. [figure:cmem-sampling-density#fig09]

The result is therefore a **qualitative partial reproduction**. The approved τ–ω experiment reproduces the H/V ordering and soil-moisture trend, but it is not a direct numerical reproduction of the paper’s CMEM result because CMEM was unavailable. [cmem-sampling-density#03] [cmem-sampling-density#06] [model:tau_omega@1.0.0]

## Supporting results

### Source/generated image

The source and generated figures support the following qualitative conclusions:

- The x-axis is volumetric soil moisture in m³ m⁻³.
- The y-axis is brightness temperature in K.
- Two polarization series are shown.
- V lies above H.
- Both series decline with increasing soil moisture.
- The curves remain visibly separated across the plotted interval.

These image-based observations establish qualitative pattern and ordering, not digitized numerical agreement. [figure:cmem-sampling-density#fig09]

### Recorded model arrays

The τ–ω model produced the following endpoint values:

- H polarization: **248.13 K** at 0.05 m³ m⁻³ and **214.76 K** at 0.50 m³ m⁻³.
- V polarization: **268.97 K** at 0.05 m³ m⁻³ and **234.59 K** at 0.50 m³ m⁻³.
- Baseline at 0.25 m³ m⁻³: **224.80 K (H)** and **246.44 K (V)**. [model:tau_omega@1.0.0]

| Comparison | Result |
|---|---|
| H/V ordering in the image | V above H |
| H/V ordering in the arrays | Confirmed at every sweep point |
| Soil-moisture trend in the image | Both curves decline |
| Soil-moisture trend in the arrays | Monotonically decreasing for both polarizations |
| Numerical agreement with the source | Not scoreable; no digitized source values or comparison metric were supplied |

The generated chart was rendered and passed the recorded legibility check. That check confirms usability of the plotted arrays only; it does not establish numerical agreement with the source figure.

## Assumed parameters

The following ledger entries were model assumptions rather than paper-explicit values:

- `angle_deg = 40.0`
- `soil_moisture = 0.05–0.50 m³ m⁻³`
- `bulk_density_g_cm3 = 1.3`
- `soil_temperature_k = 293.0`
- `canopy_temperature_k = 293.0`
- `vegetation_optical_depth = 0.3`
- `single_scattering_albedo = 0.05`
- `roughness_h = 0.3`
- `cross_q = 0.0`
- `sweep_start = 0.05`
- `sweep_stop = 0.5`

The frequency, **1.41 GHz**, was user-specified for the submitted experiment. It was not treated as proof that the complete paper configuration had been reproduced. The baseline used `sweep_parameter = none`; the sensitivity run varied soil moisture using 10 points. [cmem-sampling-density#03] [model:tau_omega@1.0.0]

## Limitations

The comparison is partial because CMEM was unavailable. The registered τ–ω model was used instead, with fixed assumed geometry, soil, canopy, and roughness parameters. Consequently, the result supports the qualitative H/V response but does not validate the paper’s CMEM-specific numerical result. [cmem-sampling-density#03] [cmem-sampling-density#06] [model:tau_omega@1.0.0]

No bias, RMSE, correlation, or other numerical comparison statistic was calculated. Numerical agreement with the source is therefore **not identifiable** from the recorded evidence.

## Final conclusion

Across **0.05–0.50 m³ m⁻³**, the generated figure shows V brightness temperature above H brightness temperature, with both decreasing as soil moisture increases. The supported τ–ω run reproduces that qualitative pattern, while the paper-level CMEM comparison remains partial and numerically unassessed.

<parameter_provenance>
[
  {"field":"frequency_ghz","value":1.41,"source_kind":"user","source_ref":"approved research plan; cmem-sampling-density#03 comparison context","reason":"The submitted experiment used 1.41 GHz; this was not treated as a complete paper-configuration match.","sensitivity_checked":false},
  {"field":"angle_deg","value":40.0,"source_kind":"assumption","source_ref":"approved research plan","reason":"Hold geometry fixed for the supported sensitivity run.","sensitivity_checked":false},
  {"field":"soil_moisture","value":[0.05,0.5],"source_kind":"assumption","source_ref":"approved research plan","reason":"Expose the registered model response over a legal soil-moisture interval.","sensitivity_checked":false},
  {"field":"bulk_density_g_cm3","value":1.3,"source_kind":"assumption","source_ref":"approved research plan","reason":"Keep substrate density fixed during the sensitivity.","sensitivity_checked":false},
  {"field":"soil_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"approved research plan","reason":"Use an unfrozen effective soil temperature.","sensitivity_checked":false},
  {"field":"canopy_temperature_k","value":293.0,"source_kind":"assumption","source_ref":"approved research plan","reason":"Hold canopy temperature fixed.","sensitivity_checked":false},
  {"field":"vegetation_optical_depth","value":0.3,"source_kind":"assumption","source_ref":"approved research plan","reason":"Hold canopy attenuation fixed.","sensitivity_checked":false},
  {"field":"single_scattering_albedo","value":0.05,"source_kind":"assumption","source_ref":"approved research plan","reason":"Hold canopy scattering fixed.","sensitivity_checked":false},
  {"field":"roughness_h","value":0.3,"source_kind":"assumption","source_ref":"approved research plan","reason":"Hold roughness fixed.","sensitivity_checked":false},
  {"field":"cross_q","value":0.0,"source_kind":"assumption","source_ref":"approved research plan","reason":"Use zero cross-polarization mixing.","sensitivity_checked":false},
  {"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"approved baseline run specification","reason":"No sweep is used in the baseline.","sensitivity_checked":false},
  {"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"approved run specification","reason":"Use the registered sweep resolution.","sensitivity_checked":false},
  {"field":"sweep_start","value":0.05,"source_kind":"assumption","source_ref":"approved research plan","reason":"Start the soil-moisture sweep at the declared legal value.","sensitivity_checked":false},
  {"field":"sweep_stop","value":0.5,"source_kind":"assumption","source_ref":"approved research plan","reason":"End the soil-moisture sweep at the declared legal value.","sensitivity_checked":false}
]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
