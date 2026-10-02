# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 gives a **qualitatively successful reproduction** of the inspected source Figure 3. It contains the same comparison among Rayleigh, DMRT QCA-CP, and IBA, with V- and H-polarized brightness temperatures plotted against frequency. The curves share the same broad rise, maximum, and decline, while separating in magnitude. In the generated results, DMRT QCA-CP is generally highest, IBA is intermediate, and Rayleigh is lowest. [smrt-v1#08] [figure:smrt-v1#fig03] [model:smrt@1.5.1]

This is not a claim of exact numerical agreement with the paper: the source curves were not digitized, and several model inputs were assumptions or registered defaults.

## Supporting results

The computed Figure 1 contains six series over a 1–100 GHz frequency sweep:

- Rayleigh V and H polarization
- DMRT QCA-CP V and H polarization
- IBA V and H polarization

The generated curves all show a similar frequency-dependent shape. Their recorded maxima were:

| Formulation | V maximum | H maximum |
|---|---:|---:|
| Rayleigh | 162.805 K | 154.713 K |
| DMRT QCA-CP | 217.453 K | 196.955 K |
| IBA | 199.667 K | 180.157 K |

The recorded model-to-model comparisons gave the following RMSE values relative to Rayleigh:

| Comparison | V RMSE | H RMSE |
|---|---:|---:|
| DMRT QCA-CP vs Rayleigh | 42.225 K | 32.008 K |
| IBA vs Rayleigh | 32.376 K | 22.626 K |

These are differences between newly computed model runs, not errors against digitized paper data or observations. [model:smrt@1.5.1]

The separate coefficient diagnostics also completed. At 100 GHz, the recorded scattering coefficients were 17.903 m⁻¹ for Rayleigh, 15.078 m⁻¹ for DMRT QCA-CP, and 24.226 m⁻¹ for IBA. The corresponding absorption coefficients were 1.789, 2.706, and 2.501 m⁻¹. These diagnostics were not included in the selected final chart. [model:smrt@1.5.1]

## Image-supported conclusion

The source and generated images support the following qualitative findings:

- The same three electromagnetic formulations are compared.
- Each formulation has V- and H-polarized curves.
- Frequency is the horizontal axis and brightness temperature in kelvin is the vertical axis.
- The curves have a shared broad frequency pattern but differ in magnitude.
- The generated figure preserves the intended grouping and ordering of the model comparison.

The image does not provide digitized curve values, so numerical agreement with the paper is **not scoreable** from the image alone. [figure:smrt-v1#fig03]

## Array-supported conclusion

The result arrays support the numerical maxima and RMSE values reported above. They also show that the formulation differences are substantial in brightness temperature, especially near the broad maxima. The array-based ordering generally agrees with the qualitative ordering visible in the generated figure.

The image-based conclusion and array-based conclusion therefore agree on curve count, frequency behavior, separation, and general ordering. They differ only in evidentiary scope: the image supports qualitative correspondence, while the arrays support numerical comparisons among the computed runs. No numerical paper-validation statistic was available.

## Assumed parameters

The following ledger entries were not paper-explicit:

### Model assumptions

- `microstructure_model = independent_sphere` for Rayleigh; selected to preserve the legal existing Rayleigh run.
- `microstructure_model = sticky_hard_spheres` for DMRT QCA-CP; selected to preserve the legal existing DMRT run.
- `microstructure_model = exponential` for IBA; selected to preserve the legal existing IBA run.
- `sweep_start = 1.0` GHz.
- `sweep_stop = 100.0` GHz.
- `sweep_points = 20`.

### Backend defaults

- `frequency_ghz = 37`
- `angle_deg = 55`
- `thickness_m = 1`
- `density_kg_m3 = 300`
- `temperature_k = 265`
- `radius_m = 0.0002`
- `stickiness = 0.2`
- `corr_length_m = 0.00015`
- `dort_streams = 32`

The frequency sweep itself was paper-explicit: `sweep_parameter = frequency_ghz`. The electromagnetic formulations and brightness-temperature output were user-specified for this submitted experiment, with the paper values retained as comparison context. [smrt-v1#08] [guideline:smrt@1.0]

## Limitations

The reproduction is **qualitatively successful but numerically unvalidated against the paper**. The source figure was not digitized, so no paper-to-model residual, bias, or numerical agreement score can be reported. The submitted experiment also differs from the paper condition through the selected legal microstructure representations and retained backend defaults.

The final selected figure was rendered successfully with six series and passed the recorded legibility check. That check establishes chart usability only; it does not establish agreement with the source figure.

## Provenance appendix

```json
{
  "outcome": "qualitatively_successful_partial_numeric_validation",
  "formal_figure": {
    "id": "Figure 1",
    "title": "Figure 1. Supported Figure 3 brightness-temperature comparison",
    "x": "Frequency (GHz)",
    "y": "Brightness temperature (K)",
    "series": 6,
    "render_check": true
  },
  "parameter_provenance": [
    {"field": "electromagnetic_model", "value": "rayleigh", "provenance": "user_specified", "paper_value": "Rayleigh", "evidence": "smrt-v1#08"},
    {"field": "electromagnetic_model", "value": "dmrt_qcacp_shortrange", "provenance": "user_specified", "paper_value": "DMRT QCA-CP", "evidence": "smrt-v1#08"},
    {"field": "electromagnetic_model", "value": "iba", "provenance": "user_specified", "paper_value": "IBA", "evidence": "smrt-v1#08"},
    {"field": "microstructure_model", "value": "independent_sphere", "provenance": "model_assumption", "paper_value": null, "evidence": "smrt-v1#08"},
    {"field": "microstructure_model", "value": "sticky_hard_spheres", "provenance": "model_assumption", "paper_value": null, "evidence": "smrt-v1#08"},
    {"field": "microstructure_model", "value": "exponential", "provenance": "model_assumption", "paper_value": null, "evidence": "smrt-v1#08"},
    {"field": "sweep_parameter", "value": "frequency_ghz", "provenance": "paper_explicit", "paper_value": "frequency", "evidence": "smrt-v1#fig-fig03"},
    {"field": "output", "value": "tb", "provenance": "user_specified", "paper_value": "tb_h and tb_v", "evidence": "smrt-v1#08"},
    {"field": "frequency_ghz", "value": 37, "provenance": "backend_default", "paper_value": 37, "evidence": null},
    {"field": "angle_deg", "value": 55, "provenance": "backend_default", "paper_value": 55, "evidence": null},
    {"field": "thickness_m", "value": 1, "provenance": "backend_default", "paper_value": 1, "evidence": null},
    {"field": "density_kg_m3", "value": 300, "provenance": "backend_default", "paper_value": 300, "evidence": null},
    {"field": "temperature_k", "value": 265, "provenance": "backend_default", "paper_value": 265, "evidence": null},
    {"field": "radius_m", "value": 0.0002, "provenance": "backend_default", "paper_value": 0.0002, "evidence": null},
    {"field": "stickiness", "value": 0.2, "provenance": "backend_default", "paper_value": 0.2, "evidence": null},
    {"field": "corr_length_m", "value": 0.00015, "provenance": "backend_default", "paper_value": 0.00015, "evidence": null},
    {"field": "dort_streams", "value": 32, "provenance": "backend_default", "paper_value": null, "evidence": null},
    {"field": "sweep_start", "value": 1.0, "provenance": "model_assumption", "paper_value": null, "evidence": null},
    {"field": "sweep_stop", "value": 100.0, "provenance": "model_assumption", "paper_value": null, "evidence": null},
    {"field": "sweep_points", "value": 20, "provenance": "model_assumption", "paper_value": null, "evidence": null}
  ]
}
```
