# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated six-series chart shows the same qualitative pattern as source Figure 3: the curves are close at low density, separate as density increases, and are ordered at high density with sticky hard spheres highest, independent spheres intermediate, and non-sticky hard spheres lowest. The qualitative reproduction is therefore **successful**. The chart contains all six required series and passed the recorded visual review. [figure:smrt-v1#fig03]

The computation used a density sweep from **1 to 100 kg m⁻³ with 40 points**. The source comparison is represented over a 0–100 kg m⁻³ axis, whereas the registered model run began at 1 kg m⁻³. [smrt-v1#08] [model:smrt@1.5.1]

## Supporting results

### Conclusion supported by the source image

The source image shows one scattering-coefficient panel with density on the x-axis, scattering coefficient on the y-axis, and six theory–microstructure combinations. It supports qualitative conclusions about curve count, grouping, ordering, convergence, and separation. It was not digitized, so it does not support a point-by-point numerical agreement claim. [figure:smrt-v1#fig03]

### Conclusion supported by the generated results

All six planned SMRT runs completed successfully and passed quality control. Each computed `ks_per_m` series increased monotonically over the density sweep. The endpoint values at 100 kg m⁻³ were:

| Theory and microstructure | `ks_per_m` (m⁻¹) |
|---|---:|
| DMRT QCA-CP, sticky hard spheres | 0.0188528 |
| IBA, sticky hard spheres | 0.0165438 |
| Rayleigh, independent spheres | 0.0139806 |
| IBA, independent spheres | 0.0134276 |
| DMRT QCA-CP, non-sticky hard spheres | 0.0072548 |
| IBA, non-sticky hard spheres | 0.0064180 |

These computed results support the increasing trend and the high-density ordering visible in the generated figure. [model:smrt@1.5.1]

### Comparison of source and generated conclusions

| Feature | Source image | Generated results | Assessment |
|---|---|---|---|
| Number of curves | Six | Six | Same qualitative structure |
| Low-density behavior | Curves are close | Curves begin close | Same qualitative pattern |
| Density response | Scattering increases with density | All six series increase monotonically | Agreement |
| High-density ordering | Sticky hard spheres highest; non-sticky hard spheres lowest | Same ordering at 100 kg m⁻³ | Agreement |
| Numerical agreement | No digitized values available | Computed values available | Not scoreable point by point |
| Parameter identity | Some run conditions are unspecified | Several conditions were assumed or defaulted | Qualification |

The visual review supports qualitative correspondence. It does not establish exact numerical agreement.

## Guessed/assumed parameters

The following values retain the recorded provenance classes.

| Input | Value | Provenance |
|---|---:|---|
| `radius_m` | 0.0001 m | `paper_explicit`; paper value 0.0001; evidence `smrt-v1#fig03` |
| `density_kg_m3` | Sweep 1–100 kg m⁻³, 40 points | `backend_default`; paper value [0, 100]; evidence `smrt-v1#fig03` |
| `output` | `coefficients` | `user_specified`; paper value `ks`; evidence `smrt-v1#fig03` |
| `stickiness` | 0.2 | `model_assumption`; paper value null; no evidence |
| `frequency_ghz` | 37 | `model_assumption`; paper value null; no evidence |
| `temperature_k` | 265 | `model_assumption`; paper value null; no evidence |
| `thickness_m` | 1 | `model_assumption`; paper value null; no evidence |
| `angle_deg` | 55 | `model_assumption`; paper value null; no evidence |
| `dort_streams` | 32 | `backend_default`; paper value null; no evidence |
| `electromagnetic_model` | `rayleigh` | `model_assumption`; paper value null; no evidence |
| `microstructure_model` | `independent_sphere` | `model_assumption`; paper value null; no evidence |
| `corr_length_m` | 0.00015 m | `backend_default`; paper value null; no evidence |
| `sweep_parameter` | `density_kg_m3` | `model_assumption`; paper value null; no evidence |
| `sweep_start` | 1.0 | `model_assumption`; paper value null; no evidence |
| `sweep_stop` | 100.0 | `model_assumption`; paper value null; no evidence |
| `sweep_points` | 40 | `model_assumption`; paper value null; no evidence |

The six runs used the approved combinations of electromagnetic theory and microstructure. The model capability and output are supported by the registered SMRT declaration. [model:smrt@1.5.1] [guideline:smrt@1.0]

## Limitations

This is a qualitative reproduction rather than a digitized numerical reconstruction. No source-curve data were available for calculating bias, RMSE, correlation, percentage error, or another numerical validation statistic; these comparisons are therefore **not scoreable**.

The frequency, temperature, layer thickness, incidence angle, stickiness, DORT-stream count, correlation-length default, and several run-selection details were not established as paper-explicit in the recorded evidence. Differences from the source image could therefore result from these assumptions, backend defaults, rendering, or implementation details. [smrt-v1#08]

## Provenance and outcome appendix

```yaml
figure:
  id: 1
  title: "Figure 1. Figure 3 qualitative reproduction"
  x: "Density (kg m^-3)"
  y: "Scattering coefficient (m^-1)"
  series: 6
  render_review: true
  review_status: passed

target:
  source: "smrt-v1#fig03"
  quantity: "ks_per_m versus density_kg_m3"
  status: successful_qualitative_reproduction
  source_curve_digitized: false
  numerical_agreement: not_scoreable

runs:
  - id: rayleigh_ind
    status: success
    points: 40
    sweep: "density_kg_m3 1.0–100.0"
    endpoint_ks_per_m: 0.013980647568598967
  - id: iba_ind
    status: success
    points: 40
    sweep: "density_kg_m3 1.0–100.0"
    endpoint_ks_per_m: 0.013427634533094483
  - id: dmrt_hs
    status: success
    points: 40
    sweep: "density_kg_m3 1.0–100.0"
    endpoint_ks_per_m: 0.007254801199743284
  - id: iba_hs
    status: success
    points: 40
    sweep: "density_kg_m3 1.0–100.0"
    endpoint_ks_per_m: 0.0064179512352543905
  - id: dmrt_shs
    status: success
    points: 40
    sweep: "density_kg_m3 1.0–100.0"
    endpoint_ks_per_m: 0.01885283914637513
  - id: iba_shs
    status: success
    points: 40
    sweep: "density_kg_m3 1.0–100.0"
    endpoint_ks_per_m: 0.01654376886623223

unavailable_or_unrun_comparisons: none
```
