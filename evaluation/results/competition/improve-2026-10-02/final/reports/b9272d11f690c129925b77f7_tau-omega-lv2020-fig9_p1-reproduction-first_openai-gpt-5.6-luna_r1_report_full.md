# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure shows two ordered, monotonically decreasing brightness-temperature curves as soil moisture increases. The vertical-polarization curve remains above the horizontal-polarization curve across the plotted range; the curves do not cross or converge. This is a successful execution of the approved tau–omega local analogue, but it is **not a reproduction of CMEM**. CMEM remains unavailable, so the paper’s CMEM comparison and sampling-density result are not identifiable. [model:tau_omega@1.0.0] [cmem-sampling-density#02] [cmem-sampling-density#fig-fig09]

## Supporting results

### Conclusion supported by the generated image

Figure 1 has two series, soil moisture on the x-axis in model units, and brightness temperature in K on the y-axis. The legend distinguishes horizontal and vertical polarization. Both curves decrease with soil moisture, with vertical polarization consistently higher than horizontal polarization. The figure does not establish numerical agreement with the source figure or with CMEM. [figure:cmem-sampling-density#fig09]

### Conclusion supported by the result arrays

The executed result is handle `res_9ff3a690a33d`, produced by `tau_omega@1.0.0`. It contains 21 points over soil moisture from 0.01 to 0.6. The recorded endpoints are:

- `tb_h`: 264.3791 K at soil moisture 0.01 and 212.2743 K at 0.6.
- `tb_v`: 280.1328 K at soil moisture 0.01 and 231.4606 K at 0.6.

Both outputs are recorded as monotonically decreasing. [model:tau_omega@1.0.0]

## Comparison and outcome

| Aspect | Generated figure | Source/model comparison |
|---|---|---|
| Curve ordering | `tb_v` remains above `tb_h`. | Supported by the executed arrays. |
| Soil-moisture response | Both curves decrease. | Supported by the executed arrays. |
| CMEM comparison | Not shown. | Not scoreable because CMEM was unavailable. |
| Numerical agreement | Not supplied by the figure or run. | RMSE, bias, correlation, and other validation statistics: N/A. |

The render check confirms that the plotted arrays are finite, sufficiently dense, and legible; it does not establish agreement with the source figure. The result is therefore **partial**: the tau–omega analogue was run and rendered, while CMEM and the paper’s CMEM-based conclusion were not reproduced. [skill:research-reporting]

## Assumed parameters

The recorded configuration used `frequency_ghz=backend default`, `angle_deg=backend default`, and `soil_moisture=sweep over the declared tau-omega range`, with `paper_value=None` for each. Parameter resolution supplied `bulk_density_g_cm3=1.3`, `soil_temperature_k=293.0`, `canopy_temperature_k=293.0`, `vegetation_optical_depth=0.3`, `single_scattering_albedo=0.05`, `roughness_h=0.3`, and `cross_q=0.0`; these are backend defaults, not paper evidence. The sweep used `sweep_parameter=soil_moisture`, `sweep_start=0.01`, `sweep_stop=0.6`, and `sweep_points=21`; these are model assumptions. [model:tau_omega@1.0.0]

## Limitations

This single-layer tau–omega calculation is a local analogue, not CMEM. The requested CMEM comparison, any paper-specific convergence or sampling threshold, and any quantitative validation statistic are not identifiable from the recorded state. The endpoint warning for the horizontal-polarization series should be treated as a sampling-resolution diagnostic rather than as evidence of physical agreement or disagreement. [cmem-sampling-density#05] [cmem-sampling-density#06]

<parameter_provenance>
[{"field":"frequency_ghz","value":"backend default","source_kind":"model_default","source_ref":"registered model parameter resolution; paper_value=None","reason":"The submitted experiment differs from the paper condition and retained the backend default.","sensitivity_checked":false},{"field":"angle_deg","value":"backend default","source_kind":"model_default","source_ref":"registered model parameter resolution; paper_value=None","reason":"The submitted experiment differs from the paper condition and retained the backend default.","sensitivity_checked":false},{"field":"soil_moisture","value":"sweep over the declared tau-omega range","source_kind":"model_default","source_ref":"registered model parameter resolution; paper_value=None","reason":"The submitted experiment differs from the paper condition and retained the backend sweep range.","sensitivity_checked":true},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"soil_temperature_k","value":293.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.3,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.05,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"soil_moisture","source_kind":"assumption","source_ref":"approved submitted run","reason":"Retained as the independent variable without attached paper or user evidence.","sensitivity_checked":true},{"field":"sweep_start","value":0.01,"source_kind":"assumption","source_ref":"approved submitted run","reason":"Retained as the sweep lower bound without attached paper or user evidence.","sensitivity_checked":true},{"field":"sweep_stop","value":0.6,"source_kind":"assumption","source_ref":"approved submitted run","reason":"Retained as the sweep upper bound without attached paper or user evidence.","sensitivity_checked":true},{"field":"sweep_points","value":21,"source_kind":"assumption","source_ref":"approved submitted run","reason":"Retained as the sweep resolution without attached paper or user evidence.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| tau_omega | frequency_ghz | paper-explicit value if available; otherwise backend default | backend_default | cmem-sampling-density#02 |
| tau_omega | angle_deg | paper-explicit value if available; otherwise backend default | backend_default | cmem-sampling-density#fig09 |
| tau_omega | soil_moisture | sweep over the declared tau-omega range, unless the paper explicitly supplies a narrower interval | backend_default | cmem-sampling-density#05 |
| tau_omega | bulk_density_g_cm3 | 1.3 | backend_default | - |
| tau_omega | soil_temperature_k | 293.0 | backend_default | - |
| tau_omega | canopy_temperature_k | 293.0 | backend_default | - |
| tau_omega | vegetation_optical_depth | 0.3 | backend_default | - |
| tau_omega | single_scattering_albedo | 0.05 | backend_default | - |
| tau_omega | roughness_h | 0.3 | backend_default | - |
| tau_omega | cross_q | 0.0 | backend_default | - |
| tau_omega | sweep_parameter | soil_moisture | model_assumption | - |
| tau_omega | sweep_start | 0.01 | model_assumption | - |
| tau_omega | sweep_stop | 0.6 | model_assumption | - |
| tau_omega | sweep_points | 21 | model_assumption | - |
