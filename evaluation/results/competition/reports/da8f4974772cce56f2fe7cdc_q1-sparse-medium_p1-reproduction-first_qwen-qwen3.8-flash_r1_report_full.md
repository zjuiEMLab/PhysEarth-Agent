# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure (Figure 1, four curves, render check passed) answers the question the plan set out to test. All four κs curves leave the low-density end together and then split into three ordered bands — sticky hard spheres (SHS) highest, independent spheres (IND) in the middle, non-sticky hard spheres (HS) lowest — while the two independent-sphere formulations, Rayleigh and IBA, run almost on top of each other. So the paper's claim holds in this build: the departure from the shared sparse-medium limit is governed mainly by the microstructure representation, and the choice of electromagnetic theory moves the curve much less [smrt-v1#08].

Calibrated outcome: **partial, with the qualitative reproduction successful.** The pattern, the band ordering and the near-coincidence of the theory pair are reproduced against the source figure [smrt-v1#fig-fig03]. Two of the source figure's six curves — HS with DMRT QCA-CP and SHS with DMRT QCA-CP — are not available in this SMRT build, so the paper's cross-theory check at the origin is demonstrated over Rayleigh and IBA only, and the paper-explicit pairing of every microstructure with two theories is not closed. One level also differs: the computed SHS curve ends below the SHS pair of the source figure at the top of the density axis, which traces to assumed parameters rather than to a changed ordering. The automatic render check only establishes that the plotted arrays are finite and legible; it is not evidence of agreement with the source image.

## Supporting results

**What the images support.** Source figure [smrt-v1#fig-fig03]: a single panel; x-axis "Density (kg m⁻³)" with ticks 0, 20, 40, 60, 80, 100; y-axis "Scattering coefficient (m⁻¹)" with ticks 0.000 to 0.025; six legend entries (independent spheres with Rayleigh and with IBA; non-sticky hard spheres with DMRT QCA-CP and with IBA; sticky hard spheres with DMRT QCA-CP and with IBA); three brace annotations labelling the groups SHS, IND and HS. Reading the image: all curves rise monotonically from the origin, the SHS pair is steepest and reaches the top of the axis, the IND pair is intermediate and roughly straight, the HS pair is lowest and visibly bends toward a plateau, and each solid–dashed pair nearly coincides. Generated figure: same two axes and units, four series of 20 points spanning 2–96 kg m⁻³, showing a shared starting point, the SHS > IND > HS banding, a near-coincident IND pair, and an HS curve that flattens at the right-hand end. No values were digitized from either image, so no number below comes from a picture.

**What the recorded arrays support.** Four successful [model:smrt@1.5.1] runs in `coefficients` mode at 100 µm sphere radius, 37 GHz, 20 densities from 2 to 96 kg m⁻³, all quality-controlled with no solver recoveries: `res_066bdde83185` (IND/Rayleigh), `res_fe61a18c7a99` (IND/IBA), `res_caba79da0095` (HS/IBA), `res_91bd8b177434` (SHS/IBA).

- *Shared limit.* At 2 kg m⁻³ the four κs arrays are 0.0002806 (SHS/IBA), 0.0002796 (IND/Rayleigh), 0.0002788 (IND/IBA) and 0.0002746 m⁻¹ (HS/IBA): highest over lowest is 1.02, i.e. within about 2 % across all four formulations.
- *Divergence.* At 96 kg m⁻³ they give 0.015864, 0.013421, 0.012913 and 0.006353 m⁻¹ in the same order. The between-microstructure gap (SHS minus HS = 0.0095 m⁻¹) is roughly nineteen times the between-theory gap inside IND (0.00051 m⁻¹, about 3.8 % of the IND value). These are arithmetic on the recorded endpoints, not tool statistics.
- *Absorption, computed but not plotted.* κa is identical at 0.0890 m⁻¹ for all three IBA microstructures at 96 kg m⁻³ and lower for Rayleigh at 0.0785 m⁻¹; the Rayleigh run also returns an effective permittivity fixed at 1.0, whereas the IBA runs rise from 1.0028 to 1.1433. Single-scattering albedo falls from 0.143 to 0.067 for HS/IBA and stays near 0.15 for SHS/IBA. These are result-backed only; no visual claim is made about them.
- *Model-versus-paper agreement statistics* (bias, RMSE, correlation): **N/A** — the source figure was not digitized, and no measured dataset in this environment covers a sparse-medium κs profile.

**Comparison of the two readings.**

| Question | Image-based reading | Array-based reading | Agreement and qualification |
| --- | --- | --- | --- |
| Shared limit at low density | Curves leave the origin together | Four κs arrays within ~2 % at 2 kg m⁻³ | Agree; supports the paper's sparse-medium validation claim [smrt-v1#08] |
| What dominates the spread | Three braced groups, theory pairs nearly coincident | Between-microstructure gap ~19× the between-theory gap | Agree; band ordering reproduced exactly |
| Curvature | HS bends toward a plateau | HS/IBA lowest and flattest at the top end (0.0064 m⁻¹) | Agree qualitatively |
| Absolute level of SHS | SHS pair approaches the top of a 0.025 m⁻¹ axis | SHS/IBA reaches 0.0159 m⁻¹ | Visible difference; consequence of assumed `stickiness` and `frequency_ghz`, neither sensitivity-tested |
| Curve count and pairing | Six curves, two theories per microstructure | Four curves; DMRT QCA-CP unavailable with both hard-sphere cases | Not reproduced — required curves missing from this build, hence partial |

## Assumed parameters

Provenance classes copied exactly from the authoritative ledger.

| Input | Value used | Provenance | Paper value / evidence | Reason |
| --- | --- | --- | --- | --- |
| `radius_m` | 0.0001 | paper_explicit | 100 µm [smrt-v1#fig-fig03] | Caption value converted to the declared SI unit |
| `sweep_parameter` | density_kg_m3 | paper_explicit | 0–100 kg m⁻³ [smrt-v1#fig-fig03] | The swept quantity is the figure's x-axis |
| `output` | coefficients | paper_explicit | y-axis quantity [smrt-v1#fig-fig03] | Coefficients mode returns κs directly |
| `microstructure_model` | independent_sphere | user_specified | legend entry [smrt-v1#fig-fig03] | The submitted experiment differs from the paper condition; the paper value remains comparison context |
| `microstructure_model` | non_sticky_hard_spheres | user_specified | legend entry [smrt-v1#fig-fig03] | As above |
| `microstructure_model` | sticky_hard_spheres | user_specified | legend entry [smrt-v1#fig-fig03] | As above |
| `electromagnetic_model` | rayleigh | user_specified | legend entry [smrt-v1#fig-fig03] | Legal only with a sphere-based microstructure, per the declaration and instruction [model:smrt@1.5.1] [guideline:smrt@1.0] |
| `electromagnetic_model` | iba | user_specified | legend entry [smrt-v1#05] | IBA is also the declared default of the registered model [model:smrt@1.5.1] |

### Guessed / assumed parameters

"Guessed" means selected without direct paper or user evidence, not invalid.

| Input | Value used | Provenance | Paper value | Effect on the result |
| --- | --- | --- | --- | --- |
| `sweep_start` | 2 kg m⁻³ | paper_inferred | curves start just above 0 [smrt-v1#fig-fig03] | The origin itself is not reached; the shared limit is approached, not measured at zero |
| `sweep_stop` | 96 kg m⁻³ | paper_inferred | curves end just below the 100 tick | Reaches the top of the plotted range without extrapolating |
| `frequency_ghz` | 37 | model_assumption | not stated for Fig. 3 | κs and κa are frequency-dependent, so absolute levels carry this choice; recorded as an assumption, not a paper value |
| `stickiness` | 0.2 | model_assumption | not stated | The main free parameter; a value below unity increases clustering and raises κs. Most likely cause of the SHS level difference, and it was not varied |
| `angle_deg` | 55 | backend_default | None | Inserted by the registered model during parameter resolution; does not enter a `coefficients` output |
| `thickness_m` | 1 | backend_default | None | Inserted default; not paper evidence, and not used by `coefficients` |
| `density_kg_m3` | 300 | backend_default | None | Fixed value, overridden by the sweep |
| `temperature_k` | 265 | backend_default | None | Inserted default; not paper evidence |
| `corr_length_m` | 0.00015 | backend_default | None | Inactive for the sphere-based microstructures actually run |
| `dort_streams` | 32 | backend_default | None | Inert: coefficients runs return no solver diagnostics |
| `sweep_points` | 20 | backend_default | None | Chart resolution only |
| `radius_m` | 0.0002 | backend_default | None | Declared model default, superseded by the paper-explicit 0.0001 in all four runs |

## Limitations

- Densities below about 50 kg m⁻³ are outside natural snow; the model's own declaration treats that range as a statement about the theories and not about a snowpack [model:smrt@1.5.1]. The paper puts the validity of the sparse-medium approximation at 10–20 kg m⁻³ [smrt-v1#08].
- Each run is a single homogeneous layer of monodisperse spheres; real snow is stratified and polydisperse, so this is a first-order implementation check, as the paper itself frames Fig. 3 [smrt-v1#08].
- Two of six source curves are unavailable, so "several electromagnetic theories share the limit" is demonstrated over Rayleigh and IBA only.
- Frequency and stickiness were chosen, not read from the paper, and neither was varied; the SHS amplitude is therefore qualitatively reproduced and not quantitatively reproduced. A run at a different frequency with a higher stickiness would be needed to test that, and none was performed.
- κa, effective permittivity and single-scattering albedo were computed but not plotted; the offered κa chart was never rendered, so those quantities are result-backed only.

```json
{"outcome": "partial_qualitative_success", "figure_rendered": true, "render_check": true, "render_check_scope": "legibility only, not comparison with source", "digitized_from_figure": false, "targets_covered": ["fig03-ind-rayleigh", "fig03-ind-iba", "fig03-hs-iba", "fig03-shs-iba"], "targets_unavailable": ["fig03-hs-dmrtqcp", "fig03-shs-dmrtqcp"], "model_vs_paper_metrics": "N/A", "guessed_parameters": ["sweep_start", "sweep_stop", "frequency_ghz", "stickiness", "angle_deg", "thickness_m", "density_kg_m3", "temperature_k", "corr_length_m", "dort_streams", "sweep_points", "radius_m_default"]}
```
