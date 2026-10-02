# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 shows six brightness-temperature curves—horizontal and vertical polarization for Rayleigh, DMRT-QCA-CP, and IBA—plotted from 1.0 to 100.0 GHz. The formulations have the same broad spectral pattern but diverge across the frequency range: DMRT-QCA-CP is generally highest, IBA is intermediate, and Rayleigh is generally lowest. The result is therefore a **partial qualitative reproduction** of the source comparison, not an exact quantitative reproduction. [figure:smrt-v1#fig03] [model:smrt@1.5.1]

All three approved runs completed successfully, and the six-series chart was rendered with a passed automatic legibility check. The check establishes that the generated chart is usable; it does not by itself establish agreement with the source figure. [model:smrt@1.5.1]

## Conclusion supported by the source and generated images

The source and generated images both present the three formulations as a six-curve comparison of `tb_h` and `tb_v` against frequency. The curves share a broadly similar frequency-dependent shape while separating according to the electromagnetic and microstructure formulation. [smrt-v1#fig-fig03] [figure:smrt-v1#fig03]

The generated image contains six series, uses `frequency_ghz` on the x-axis, and reports brightness temperature in K on the y-axis. [model:smrt@1.5.1] The image comparison supports qualitative correspondence only; the source image was not digitized, so direct source-to-model numerical agreement is not scoreable. [figure:smrt-v1#fig03]

## Supporting results

The three result handles were:

- `res_e34268b98137`: Rayleigh, 20 points over `frequency_ghz`.
- `res_8fc08e6cdb64`: DMRT-QCA-CP, 20 points over `frequency_ghz`.
- `res_be0ec31a2c6a`: IBA, 20 points over `frequency_ghz`.

All runs used `tb_h` and `tb_v` as outputs. [model:smrt@1.5.1]

The computed extrema were:

| Configuration | `tb_h` maximum | `tb_v` maximum |
|---|---:|---:|
| Rayleigh | 154.713 K | 162.805 K |
| DMRT-QCA-CP | 196.955 K | 217.453 K |
| IBA | 180.157 K | 199.667 K |

The recorded chart calculation supplied the following pairwise comparisons against Rayleigh over the common 1.0–100.0 GHz range:

| Comparison | Quantity | Bias | MAE | RMSE | r |
|---|---|---:|---:|---:|---:|
| DMRT-QCA-CP − Rayleigh | `tb_h` | 25.7342 K | 25.7342 K | 32.0072 K | 0.9942 |
| IBA − Rayleigh | `tb_h` | 18.8746 K | 18.8746 K | 22.6255 K | 0.9978 |
| DMRT-QCA-CP − Rayleigh | `tb_v` | 34.1703 K | 34.1703 K | 42.2251 K | 0.9908 |
| IBA − Rayleigh | `tb_v` | 27.4046 K | 27.4046 K | 32.3759 K | 0.9970 |

These are comparisons among model arrays, not comparisons with measurements or digitized source-figure values. [model:smrt@1.5.1]

## Figure-versus-results comparison

| Aspect | Image-supported conclusion | Result-supported conclusion | Qualification |
|---|---|---|---|
| Series and axes | Six curves compare `tb_h` and `tb_v` versus frequency. [figure:smrt-v1#fig03] | Six series were generated over 20 frequency points. [model:smrt@1.5.1] | Agreement. |
| Overall shape | The curves show a common broad spectral pattern. [figure:smrt-v1#fig03] | All three formulations show similar broad frequency dependence. [model:smrt@1.5.1] | Qualitative agreement. |
| Ordering | The formulations are visibly separated and ordered. [figure:smrt-v1#fig03] | DMRT-QCA-CP has the largest recorded maxima, IBA is intermediate, and Rayleigh is lowest at the recorded maxima. [model:smrt@1.5.1] | Agreement for the generated comparison. |
| Quantitative source agreement | The source image does not provide digitized values here. [figure:smrt-v1#fig03] | Model-to-model statistics are available, but source-to-model statistics are not. [model:smrt@1.5.1] | Direct quantitative reproduction is not scoreable. |

## Guessed/assumed parameters

The following ledger values were not paper-explicit. `model_assumption` values are reported as assumptions, and `backend_default` values are reported as model defaults; none is relabeled as paper-derived.

The three runs used the exact submitted values `angle_deg = 55.0`, `thickness_m = 1.0`, `density_kg_m3 = 300.0`, `temperature_k = 265.0`, `corr_length_m = 0.00015`, `radius_m = 0.0002`, `stickiness = 0.2`, and `dort_streams = 32`. The sweep used `sweep_parameter = frequency_ghz`, `sweep_start = 1.0`, `sweep_stop = 100.0`, and `sweep_points = 20`. These values came from the approved run state as backend defaults or model assumptions, not from paper evidence.

The model-assumed values were `microstructure_model = independent_sphere` and `output = tb` for the Rayleigh run; the corresponding approved DMRT-QCA-CP and IBA microstructure selections were `sticky_hard_spheres` and `exponential`, respectively. The electromagnetic formulation was user-specified as `rayleigh`, `dmrt_qcacp_shortrange`, and `iba`. [model:smrt@1.5.1]

## Limitations and final conclusion

The generated figure qualitatively reproduces the intended comparison of three SMRT formulations over the 1.0–100.0 GHz range, including six brightness-temperature curves and their broad divergence and ordering. The numerical differences reported above are valid only as comparisons among the three executed model arrays. Because the paper figure was not digitized and several configuration values were defaults or assumptions, exact quantitative reproduction of the source figure is not identifiable. [figure:smrt-v1#fig03] [model:smrt@1.5.1]

<parameter_provenance>
[{"field":"fig03-rayleigh.electromagnetic_model","value":"rayleigh","source_kind":"user","source_ref":"approved reproduction configuration; paper comparison context smrt-v1#08","reason":"User-specified Rayleigh formulation","sensitivity_checked":false},{"field":"fig03-rayleigh.microstructure_model","value":"independent_sphere","source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Retained model assumption","sensitivity_checked":false},{"field":"fig03-rayleigh.output","value":"tb","source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Retained model assumption for brightness-temperature output","sensitivity_checked":false},{"field":"fig03-rayleigh.frequency_ghz","value":37.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default retained while frequency_ghz was swept","sensitivity_checked":false},{"field":"fig03-rayleigh.angle_deg","value":55.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-rayleigh.thickness_m","value":1.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-rayleigh.density_kg_m3","value":300.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-rayleigh.temperature_k","value":265.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-rayleigh.corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-rayleigh.radius_m","value":0.0002,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-rayleigh.stickiness","value":0.2,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-rayleigh.dort_streams","value":32,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-rayleigh.sweep_parameter","value":"frequency_ghz","source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Selected sweep axis","sensitivity_checked":false},{"field":"fig03-rayleigh.sweep_start","value":1.0,"source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Approved sweep lower bound","sensitivity_checked":false},{"field":"fig03-rayleigh.sweep_stop","value":100.0,"source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Approved sweep upper bound","sensitivity_checked":false},{"field":"fig03-rayleigh.sweep_points","value":20,"source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Approved sweep resolution","sensitivity_checked":false},{"field":"fig03-dmrt.electromagnetic_model","value":"dmrt_qcacp_shortrange","source_kind":"user","source_ref":"approved reproduction configuration; paper comparison context smrt-v1#08","reason":"User-specified DMRT-QCA-CP formulation","sensitivity_checked":false},{"field":"fig03-dmrt.microstructure_model","value":"sticky_hard_spheres","source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Retained model assumption","sensitivity_checked":false},{"field":"fig03-dmrt.output","value":"tb","source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Retained model assumption for brightness-temperature output","sensitivity_checked":false},{"field":"fig03-dmrt.frequency_ghz","value":37.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default retained while frequency_ghz was swept","sensitivity_checked":false},{"field":"fig03-dmrt.angle_deg","value":55.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-dmrt.thickness_m","value":1.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-dmrt.density_kg_m3","value":300.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-dmrt.temperature_k","value":265.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-dmrt.corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-dmrt.radius_m","value":0.0002,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-dmrt.stickiness","value":0.2,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-dmrt.dort_streams","value":32,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-dmrt.sweep_parameter","value":"frequency_ghz","source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Selected sweep axis","sensitivity_checked":false},{"field":"fig03-dmrt.sweep_start","value":1.0,"source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Approved sweep lower bound","sensitivity_checked":false},{"field":"fig03-dmrt.sweep_stop","value":100.0,"source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Approved sweep upper bound","sensitivity_checked":false},{"field":"fig03-dmrt.sweep_points","value":20,"source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Approved sweep resolution","sensitivity_checked":false},{"field":"fig03-iba.electromagnetic_model","value":"iba","source_kind":"user","source_ref":"approved reproduction configuration; paper comparison context smrt-v1#08","reason":"User-specified IBA formulation","sensitivity_checked":false},{"field":"fig03-iba.microstructure_model","value":"exponential","source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Retained model assumption","sensitivity_checked":false},{"field":"fig03-iba.output","value":"tb","source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Retained model assumption for brightness-temperature output","sensitivity_checked":false},{"field":"fig03-iba.frequency_ghz","value":37.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default retained while frequency_ghz was swept","sensitivity_checked":false},{"field":"fig03-iba.angle_deg","value":55.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-iba.thickness_m","value":1.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-iba.density_kg_m3","value":300.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-iba.temperature_k","value":265.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-iba.corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-iba.radius_m","value":0.0002,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-iba.stickiness","value":0.2,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-iba.dort_streams","value":32,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend default","sensitivity_checked":false},{"field":"fig03-iba.sweep_parameter","value":"frequency_ghz","source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Selected sweep axis","sensitivity_checked":false},{"field":"fig03-iba.sweep_start","value":1.0,"source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Approved sweep lower bound","sensitivity_checked":false},{"field":"fig03-iba.sweep_stop","value":100.0,"source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Approved sweep upper bound","sensitivity_checked":false},{"field":"fig03-iba.sweep_points","value":20,"source_kind":"assumption","source_ref":"approved run ledger: no attached paper or user evidence","reason":"Approved sweep resolution","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | electromagnetic_model | rayleigh | user_specified | smrt-v1#08 |
| smrt | microstructure_model | independent_sphere | model_assumption | - |
| smrt | output | tb | model_assumption | - |
| smrt | frequency_ghz | 37.0 | backend_default | - |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | thickness_m | 1.0 | backend_default | - |
| smrt | density_kg_m3 | 300.0 | backend_default | - |
| smrt | temperature_k | 265.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | radius_m | 0.0002 | backend_default | - |
| smrt | stickiness | 0.2 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_parameter | frequency_ghz | model_assumption | - |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | model_assumption | - |
| smrt | sweep_points | 20 | model_assumption | - |
