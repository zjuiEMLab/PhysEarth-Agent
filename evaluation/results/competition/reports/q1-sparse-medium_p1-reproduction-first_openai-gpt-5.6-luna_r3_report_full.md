# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show three formulation curves over 1–37 GHz. Absorption coefficient and single-scattering albedo increase with frequency, while the formulations become more separated toward the high-frequency end. The comparison is therefore qualitatively reproduced, but source-to-model numerical agreement is not scoreable because no digitized source-curve data were used.

The approved experiment compared IBA, Rayleigh, and DMRT QCA-CP coefficient diagnostics with the same controlled frequency sweep. All four approved runs completed successfully, with the IBA run reused from an identical successful result. The three selected figures were rendered successfully and were legible [model:smrt@1.5.1].

## Source-figure conclusion

The source figure presents the intended comparison of snow-microwave coefficient diagnostics across formulations [smrt-v1#08] [figure:smrt-v1#fig03]. Its visible evidence supports the qualitative comparison of curve count, frequency dependence, grouping, ordering, and separation. It does not provide digitized values for numerical residual calculations.

The generated figures show the same broad type of comparison: three formulation curves plotted against frequency. Thus, the result is a **qualitatively successful reproduction** of the comparison structure, with a **partial quantitative outcome**.

## Generated-result conclusion

The recorded model outputs show the following values at 37 GHz:

- Absorption coefficient: IBA **0.3428 m⁻¹**, Rayleigh **0.2452 m⁻¹**, and DMRT QCA-CP **0.3709 m⁻¹** [model:smrt@1.5.1].
- Single-scattering albedo: IBA **0.6599**, Rayleigh **0.5777**, and DMRT QCA-CP **0.4324** [model:smrt@1.5.1].
- Effective permittivity: IBA approximately **1.5239**, Rayleigh **1.0**, and DMRT QCA-CP approximately **1.5419** [model:smrt@1.5.1].

The recorded chart calculations supplied absorption RMSE values relative to the IBA curve of **0.0477 m⁻¹** for Rayleigh and **0.0137 m⁻¹** for DMRT QCA-CP. These are comparisons among model outputs, not errors against the paper figure.

## Comparison

| Aspect | Source figure | Generated results | Interpretation |
|---|---|---|---|
| Formulations | Three formulation diagnostics | Three formulation curves | Qualitatively consistent |
| Frequency behaviour | Frequency-dependent comparison | Absorption and albedo increase with frequency | Consistent broad pattern |
| High-frequency separation | Visible curve separation | Increasing model separation toward 37 GHz | Consistent qualitative result |
| Numerical agreement | No digitized values | Model values and inter-model metrics available | Source-to-model score is not available |
| Permittivity | Qualitative formulation comparison | Rayleigh is constant; DMRT QCA-CP has a small endpoint change | Requires qualification |

The generated curves support the qualitative conclusion from the source image, while the recorded arrays provide the numerical model comparison. Exact source-to-model agreement cannot be claimed.

## Assumed and guessed parameters

The authoritative ledger identifies the following values as assumptions or defaults rather than paper-explicit conditions:

- `corr_length_m = 0.00015`: backend default.
- `sweep_parameter = frequency_ghz`: model assumption.
- `sweep_start = 1.0`: model assumption.
- `sweep_stop = 37.0`: model assumption.
- `sweep_points = 10`: model assumption.
- `microstructure_model = exponential`: model assumption.
- `output = coefficients`: model assumption.
- `frequency_ghz = 37.0`: model assumption retained while the sweep was active.
- `angle_deg = 55.0`: model assumption.
- `thickness_m = 1.0`: model assumption.
- `density_kg_m3 = 300.0`: model assumption.
- `temperature_k = 265.0`: model assumption.
- `radius_m = 0.0002`: backend default.
- `stickiness = 0.2`: backend default.
- `dort_streams = 32`: model assumption.

The electromagnetic-model selection was user-specified for the approved comparison. The paper comparison context included Rayleigh, DMRT QCA-CP, and IBA, but the ledger does not treat those paper values as provenance for the submitted baseline [smrt-v1#08].

## Limitations and final conclusion

The experiment did not include new measurements, source-curve digitization, or additional model runs. Consequently, source-to-model bias, MAE, RMSE, correlation, and percent error are not scoreable. The recorded render checks establish that the generated figures were usable and legible; they do not establish agreement with the source image.

The original research question is answered as follows: the approved model formulations show broadly similar low-frequency behaviour and increasing divergence toward higher frequency, with formulation-dependent ordering in absorption, effective permittivity, and single-scattering albedo. The reproduction is **qualitatively successful but quantitatively partial** [model:smrt@1.5.1].

<parameter_provenance>
[
  {"field":"corr_length_m","value":"0.00015","source_kind":"model_default","source_ref":"Backend default; not paper evidence","reason":"Backend default retained in the approved runs","sensitivity_checked":false},
  {"field":"sweep_parameter","value":"frequency_ghz","source_kind":"assumption","source_ref":"Model assumption for the diagnostic frequency sweep","reason":"Frequency was the approved diagnostic axis","sensitivity_checked":false},
  {"field":"sweep_start","value":"1.0","source_kind":"assumption","source_ref":"Model assumption, not paper evidence","reason":"Lower bound of the approved sweep","sensitivity_checked":false},
  {"field":"sweep_stop","value":"37.0","source_kind":"assumption","source_ref":"Model assumption, not paper evidence","reason":"Upper bound of the approved sweep","sensitivity_checked":false},
  {"field":"sweep_points","value":"10","source_kind":"assumption","source_ref":"Model assumption, not paper evidence","reason":"Approved frequency sampling density","sensitivity_checked":false},
  {"field":"electromagnetic_model","value":"iba; rayleigh; dmrt_qcacp_shortrange","source_kind":"user","source_ref":"Approved comparison runs; paper comparison context in smrt-v1#08","source_span":"comparison of Rayleigh, DMRT QCA-CP, and IBA","reason":"The approved experiment compared all three formulations","sensitivity_checked":false},
  {"field":"microstructure_model","value":"exponential; independent_sphere; sticky_hard_spheres","source_kind":"assumption","source_ref":"Approved model configurations; no paper-explicit provenance in the ledger","reason":"Legal microstructure paired with each formulation","sensitivity_checked":false},
  {"field":"output","value":"coefficients","source_kind":"assumption","source_ref":"Approved coefficient-diagnostic target","reason":"Coefficient outputs were selected for the reproduction","sensitivity_checked":false},
  {"field":"frequency_ghz","value":"37.0","source_kind":"assumption","source_ref":"Approved run configuration","reason":"Fixed parameter field retained during the frequency sweep","sensitivity_checked":false},
  {"field":"angle_deg","value":"55.0","source_kind":"assumption","source_ref":"Approved run configuration","reason":"Retained incidence angle","sensitivity_checked":false},
  {"field":"thickness_m","value":"1.0","source_kind":"assumption","source_ref":"Approved run configuration","reason":"Retained snow-layer thickness","sensitivity_checked":false},
  {"field":"density_kg_m3","value":"300.0","source_kind":"assumption","source_ref":"Approved run configuration","reason":"Fixed snow density","sensitivity_checked":false},
  {"field":"temperature_k","value":"265.0","source_kind":"assumption","source_ref":"Approved run configuration","reason":"Fixed snow temperature","sensitivity_checked":false},
  {"field":"radius_m","value":"0.0002","source_kind":"model_default","source_ref":"Registered model parameter resolution","reason":"Backend default particle radius","sensitivity_checked":false},
  {"field":"stickiness","value":"0.2","source_kind":"model_default","source_ref":"Registered model parameter resolution","reason":"Backend default stickiness","sensitivity_checked":false},
  {"field":"dort_streams","value":"32","source_kind":"assumption","source_ref":"Approved run configuration","reason":"Numerical stream count retained in the controlled comparison","sensitivity_checked":false}
]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
