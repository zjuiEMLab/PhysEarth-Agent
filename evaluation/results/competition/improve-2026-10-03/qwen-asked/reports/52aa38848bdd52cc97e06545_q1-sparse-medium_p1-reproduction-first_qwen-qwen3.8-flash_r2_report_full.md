# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

# Reproduction of SMRT Figure 3 (Picard et al., 2018, Sect. 3.1.1)

## Research result and conclusion

Generated Figure 1 answers the question. Its six curves — Rayleigh and IBA on independent spheres, DMRT QCA-CP and IBA on non-sticky hard spheres, DMRT QCA-CP and IBA on sticky hard spheres, each `output = coefficients` at 37 GHz with `radius_m = 0.0001` — all rise monotonically from the same sparse end and then fan out. They converge into one trend only at the sparse limit and diverge progressively, the divergence being governed **mainly by the microstructure family, not by the electromagnetic theory**: at 100 kg m⁻³ the six span 0.0064 to 0.014 m⁻¹, a factor of 2.2 (my arithmetic on the two recorded endpoints), while within any one family the two theories differ by only 0.0006 to 0.0013 m⁻¹ [model:smrt@1.5.1]. No single divergence density is identifiable: the fan-out opens continuously, and on the 40-point grid (spacing ≈2.5 kg m⁻³) the reading from the generated figure is that the six are indistinguishable at the low end, group visibly into three family pairs by about 40 kg m⁻³, and are fully ordered with no further crossing above about 60 kg m⁻³ — approximate readings, not thresholds.

For the density value itself, the two sources give different numbers and must be kept apart. **Reported paper evidence:** the sparse-medium approximation "is valid only for very low densities in the range 10–20 kgm-3 which is unrealistic for the goal of snow modeling" [smrt-v1#08] — so the paper's own bound on the convergence band is 10–20 kg m⁻³, and the same section reports 300 kg m⁻³ as the density of the neighbouring dense-medium comparison of Fig. 4, well outside Fig. 3's plotted axis and outside the sweep run here (`sweep 1 to 100 kg m-3, 40 points`) [smrt-v1#08]. **Recorded results:** the six curves are numerically identical at the sparse end, each with a first value 0.0001 m⁻¹ at 1 kg m⁻³, and separate monotonically thereafter [model:smrt@1.5.1]. The computed convergence band is therefore consistent with the paper's 10–20 kg m⁻³, and the paper's single quantitative statement about it — that validity ends there — reproduces.

**Outcome: partial, with the qualitative reproduction successful.** Figure 1 shows the scientific pattern of Fig. 3 — six origin-starting curves, one bundle in the sparse limit, a fan-out organised by microstructure, and the solid curve of each family pair above the dashed IBA curve, all visible in the source image [figure:smrt-v1#fig03]. One ordering differs: at τ = 0.5 the computed top family is independent spheres, whereas the source image's right-margin braces stack sticky-hard-sphere, independent-sphere, hard-sphere from the top down [figure:smrt-v1#fig03]. Because the paper gives no stickiness for Fig. 3 and ks falls steeply with it, I record this as a diagnostic of an unspecified parameter rather than a contradiction of a required one. Agreement statistics against the published curves: **N/A** — the source image was inspected but not digitized, so no RMSE, correlation or bias exists to report.

## Supporting results

**What the images support.** Source Fig. 3: one panel, six continuous lines, no markers, no gridlines; axes *Density (kg m⁻³)* with ticks 0–100 and *Scattering coefficient (m⁻¹)* with ticks 0.000–0.025; colour = microstructure, line style = theory with dashed always IBA; braces on the right stack SHS, IND, HS; one bundle over roughly the first fifth of the axis, then three colour pairs [figure:smrt-v1#fig03]. No value, crossing point or threshold can be read from it. Generated Figure 1 carries six series on the same axes and units; Figure 2 shows two falling ks-versus-τ curves; Figure 3 shows one near-flat ks-versus-temperature curve.

**What the computed arrays support.** r1–r6 (`res_f988adfd6f0f`, `res_cda51790ff9a`, `res_c8698ef0194d`, `res_dcea32607288`, `res_3ef84c5a74b9`, `res_82b14da2af74`), 40 points over 1–100 kg m⁻³: ks increasing in all six, endpoint values 0.014 (Rayleigh/IND), 0.0134 (IBA/IND), 0.0107 (DMRT/SHS), 0.0094 (IBA/SHS), 0.0073 (DMRT/HS), 0.0064 (IBA/HS) m⁻¹ [model:smrt@1.5.1]. Within every family the non-IBA theory is the higher one. All six curve means exceed half their maximum — flattening with density — most for HS (0.0046 versus 0.00365 m⁻¹, my arithmetic) and hardly at all for Rayleigh/IND (0.0071 versus 0.0070 m⁻¹), so the source image's "green steepening" reads, in the arrays, as *less flattening* rather than upward curvature. r7, r8 (`res_64f6103dd65a`, `res_80a98762ebe6`): at 60 kg m⁻³ ks falls monotonically over τ 0.2→5.0 from 0.0096 to 0.0054 m⁻¹ (IBA) and 0.0104 to 0.0058 m⁻¹ (DMRT QCA-CP) — about −44 % (my arithmetic) — with ka unchanged [model:smrt@1.5.1]. This is both the source of the ordering difference and its likely remedy: a lower τ lifts SHS toward the position the figure shows. r9 (`res_5a26b33ae461`): over 210→273 K ks moves 0.0065→0.0067 m⁻¹ (+3 %, my arithmetic) while ka rises 0.025→0.0625 m⁻¹, a factor of 2.5 (my arithmetic; this corrects an earlier draft of mine that called that increase a doubling) [model:smrt@1.5.1].

| Question | Image reading | Array reading | Agreement |
| --- | --- | --- | --- |
| One shared trend at low density? | Yes, one bundle over the first fifth of the axis | All six first values 0.0001 m⁻¹ at 1 kg m⁻³ | Same qualitative pattern; no threshold value is readable or computable beyond the ≈2.5 kg m⁻³ grid |
| Family or theory governs the spread? | Colour separates far more than line style | 0.0064–0.014 versus 0.0006–0.0013 m⁻¹ | Agreement, and it matches the paper's own statement [smrt-v1#08] |
| Highest family at 100 kg m⁻³? | SHS | IND (0.014, 0.0134 m⁻¹) | **Disagreement**; rests on `stickiness = 0.5`, which the ledger records as `model_assumption` with `paper_value = None`, and r7/r8 give its direction |
| Within-pair ordering | Solid above dashed | Non-IBA above IBA in all three families | Agreement |
| Curvature | Green steepening, orange flattening | All six flatten; IND flattens least | Partial; aspect ratio of a 0–100 axis compresses near-linear curves [skill:research-reporting] |

## Assumed parameters

Two inputs are `paper_explicit` (`radius_m = 0.0001`, `frequency_ghz = 37`) and two `user_specified` (`electromagnetic_model = rayleigh | dmrt_qcacp_shortrange | iba`, `microstructure_model = independent_sphere | non_sticky_hard_spheres | sticky_hard_spheres`), with the independent variable also user-specified (`density_kg_m3 = sweep 1 to 100 kg m-3, 40 points`). Every ledger row carries `paper_value = None`.

**Guessed/assumed parameters.** `paper_inferred`: `output = coefficients`. `model_assumption`: `stickiness = 0.5`, `sweep_parameter = density_kg_m3`, `sweep_start = 1.0`, `sweep_stop = 100.0`, `sweep_points = 40`. `backend_default`: `temperature_k = 265`, `thickness_m = 1.0`, `angle_deg = 55.0`, `corr_length_m = 0.00015`, `dort_streams = 32`. τ = 0.5 is the value the paper uses in the neighbouring Sect. 3.1.2 comparison [smrt-v1#08], but it is not evidence for Fig. 3 and stays `model_assumption`; it is the one assumed input that materially moves the answer. The default `temperature_k = 265` also differs from the 256 K the same paper reports for Fig. 4 [smrt-v1#08]; r9 bounds that difference at about 3 % in ks. Angle, correlation length, stream count and thickness are inert or near-inert for ks at `output = coefficients`.

## Limitations

SMRT is a single homogeneous layer, so this is a first-order answer [smrt-v1#07]. Fig. 3 compares electromagnetic theories, which cannot validate any of them; the paper's own resolution is to drop IBA and extend DMRTQCA to dense media [smrt-v1#08]. The dense end is unverified: at 100 kg m⁻³, hard-sphere volume fraction reaches 0.091, above the 0.05–0.07 at which the paper reports sparse-medium error "quickly exceeds 3 %", and the 10–20 kg m⁻³ validity bound means no theory here is claimed accurate over most of the plotted axis [smrt-v1#08]. The `rayleigh` runs hold `effective_permittivity = 1.0` across the sweep while every other run rises to ≈1.15, so that pairing is a bare-particle limit; and in the `sticky_hard_spheres` runs changing τ leaves `single_scattering_albedo` unchanged to four decimals, indicating τ does not enter the single-particle amplitude in this implementation. `temperature_k = 265` is inside the declared −40…0 °C range but above the 253…273 K window in which the paper's temperature check holds. Each of the six density sweeps was executed once, so no grid-refinement or replicate estimate exists. The automatic render check passed for all three charts, which establishes only that the plotted arrays are finite and legible; it is not a comparison with the source figure, and the comparison above was made against the inspected source image separately. What remains unverified: the absolute published ks values, the SHS-versus-IND ordering, the paper's actual stickiness, and the early termination of the source figure's dashed green curve.

```outcome
target fig03            partial — qualitative reproduction successful; quantitative comparability not established
reference_model         SMRT v1.0 configurations (rayleigh | dmrt_qcacp_shortrange | iba) [smrt-v1#08]
model_executed          smrt v1.5.1 (registered), 9 runs r1–r9, all successful
inputs_verified         r1–r6 density sweeps; r7–r8 stickiness; r9 temperature
inputs_assumed          stickiness 0.5 (model_assumption, paper_value None); output=coefficients (paper_inferred);
                        temperature 265, thickness 1.0, angle 55.0, corr_length 0.00015, dort_streams 32 (backend_default);
                        sweep grid 1.0–100.0, 40 points (model_assumption)
evidence                smrt-v1#fig03, smrt-v1#07, smrt-v1#08; res_f988adfd6f0f, res_cda51790ff9a, res_c8698ef0194d,
                        res_dcea32607288, res_3ef84c5a74b9, res_82b14da2af74, res_64f6103dd65a, res_80a98762ebe6,
                        res_5a26b33ae461; fig03 source asset
agreement_statistics    N/A — source figure not digitized; no RMSE, correlation or bias computed
unavailable             none
```

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | output | coefficients | paper_inferred | smrt-v1#fig03 |
| smrt | electromagnetic_model | rayleigh / dmrt_qcacp_shortrange / iba | user_specified | smrt-v1#08 |
| smrt | microstructure_model | independent_sphere / non_sticky_hard_spheres / sticky_hard_spheres | user_specified | smrt-v1#08 |
| smrt | radius_m | 0.0001 | paper_explicit | smrt-v1#08 |
| smrt | density_kg_m3 | sweep 1 to 100 kg m-3, 40 points | user_specified | smrt-v1#fig03 |
| smrt | frequency_ghz | 37 | paper_explicit | smrt-v1#07 |
| smrt | stickiness | 0.5 | model_assumption | smrt-v1#08 |
| smrt | temperature_k | 265 | backend_default | smrt-v1#08 |
| smrt | thickness_m | 1.0 | backend_default | smrt-v1#07 |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_parameter | density_kg_m3 | model_assumption | - |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | model_assumption | - |
| smrt | sweep_points | 40 | model_assumption | - |
