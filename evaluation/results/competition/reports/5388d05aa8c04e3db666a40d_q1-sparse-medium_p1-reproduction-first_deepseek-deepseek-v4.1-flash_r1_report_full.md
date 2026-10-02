# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The planned sparse-medium validation behaviour is reproduced only in part [skill:research-reporting]. The generated figure shows six scattering-coefficient curves (three microstructures × three electromagnetic theories) that all spring from a shared low-density origin and then fan apart as density rises, with the hard-sphere curves at the bottom — matching the source figure's central claim of a common sparse-medium limit [smrt-v1#08]. What it does **not** reproduce is the source figure's high-density ordering: the source figure orders the curves SHS above IND above HS, whereas the new runs give **IND > SHS > HS**. The independent-sphere curves sit highest, and the sticky-hard-sphere curves fall below them. Because the requested ordering test (`SHS > IND > HS`) is only partly met, I score this a partial reproduction — not a failure, since every required curve is present and no paper-explicit condition is contradicted.

## Conclusion from the source and generated figure

The inspected source figure [figure:smrt-v1#fig03] is a single panel: x-axis Density (kg m⁻³) from 0 to 100, y-axis Scattering coefficient (m⁻¹) from 0 to 0.025, six curves, with the caption fixing the sphere radius at 100 µm. The extraction returned the axes, ticks and the six-series legend but no digitized curve values, so ordering is read qualitatively only. The paper states the scientific content of this panel directly: at the origin (f₂→0) "the linear trend is the same for several microstructures … and different theories (Rayleigh, DMRT QCA-CP, IBA)", and it is the microstructure, more than the electromagnetic theory, that controls departure from the sparse-medium assumption [smrt-v1#08]. The figure is the paper's first technical validation, and the sparse-medium approximation is valid only for very low densities in the range 10–20 kg m⁻³ [smrt-v1#08].

The generated figure carries the same six curves on the same axes and units, converging at the origin and separating with density. On that reading the qualitative pattern of the panel — one shared origin, divergence set by microstructure — is reproduced.

## Conclusion from the actual result arrays

Six formal runs (r1–r6, each executed once) returned coefficient arrays over density 1–100 kg m⁻³ [model:smrt@1.5.1]. The render step reported 20 points per series and computed pairwise agreement of each curve against the IND-Rayleigh reference, all in the same unit (m⁻¹):

| Curve vs IND-Rayleigh | bias (m⁻¹) | rmse (m⁻¹) | r |
|---|---|---|---|
| IND (IBA) | −2×10⁻⁴ | 3×10⁻⁴ | 0.9999 |
| SHS (DMRT QCA-CP) | −1.1×10⁻³ | 1.5×10⁻³ | 0.9965 |
| SHS (IBA) | −1.6×10⁻³ | 2.2×10⁻³ | 0.9926 |
| HS (DMRT QCA-CP) | −2.5×10⁻³ | 3.3×10⁻³ | 0.978 |
| HS (IBA) | −2.8×10⁻³ | 3.7×10⁻³ | 0.9672 |

Every bias is negative and every curve follows the same monotone rise (r ≥ 0.97 throughout), so the structured result is: shared low-density origin, divergence growing with density. The magnitudes of the biases give the ordering directly — IND-Rayleigh highest, SHS intermediate, HS lowest, i.e. **IND > SHS > HS**.

## Comparison of the two conclusions

| Aspect | Source-figure conclusion | Result-array conclusion | Agreement |
|---|---|---|---|
| Curve count / axes / units | 6 curves, Density vs scattering coefficient | 6 curves, same axes/units | Agree |
| Sparse-medium origin | Shared linear trend at f₂→0 | Common start, small low-density biases | Agree |
| Microstructure controls divergence | HS lowest, separation grows with density | HS biases most negative, separation grows | Agree |
| High-density ordering | SHS > IND > HS | IND > SHS > HS | **Disagree on SHS vs IND** |

The disagreement is confined to the SHS arm. The diagnostic most likely responsible is the stickiness value: 0.5 was a guess (see below), and lower stickiness means more clustering and more scattering [smrt-v1#08, smrt-v1#09]. A guessed stickiness that is too high would under-scatter the SHS curves and push them below IND, the offset seen here. Since the source figure annotates no stickiness, this is a diagnostic difference, not a contradicted paper condition — but it means the SHS>IND ordering arm is not established by these runs. The render check passed, which confirms only that the plotted arrays are finite and legible; it is not a comparison with the source figure, and the qualitative correspondence above rests on the curves I compared with the inspected figure, not on that check.

## Assumed and guessed parameters

The parameter ledger marks the following as not paper-explicit:

- `radius_m = 0.0001` — **user_specified** (100 µm, consistent with the figure caption, but classified as user-specified).
- `density_kg_m3` sweep 1–100 — **backend_default** for the range.
- `electromagnetic_model` (dmrt_qcacp_shortrange / iba / rayleigh) and `microstructure_model` (independent_sphere / non_sticky_hard_spheres / sticky_hard_spheres) — **user_specified**.
- `stickiness = 0.5` — **user_specified**; the guessed value most implicated in the SHS ordering mismatch.
- `frequency_ghz = 37.0` and `temperature_k = 265.0` — **model_assumption**, not stated by the figure; neither enters the coefficient comparison.
- `output = coefficients` — **paper_inferred**.
- `angle_deg = 55.0`, `thickness_m = 1.0`, `corr_length_m = 0.00015`, `dort_streams = 32` — **backend_default**, inserted by the model, not paper evidence; none affects a coefficient-only output.
- `sweep_parameter = density_kg_m3`, `sweep_start = 1.0`, `sweep_stop = 100.0`, `sweep_points = 20` — **model_assumption**, retained without attached paper/user evidence.

No paper-explicit value was overridden, and no parameter above is claimed as paper_explicit.

## Limitations

The ordering claim rests on a qualitative comparison with a source figure whose curve values were **not digitized**; the agreement statistics describe the model curves among themselves, not agreement with the figure. The figure annotates neither frequency, temperature nor stickiness, so those remain assumptions, and the SHS-versus-IND question is left open until stickiness is swept rather than fixed. The lower sweep bound (1 kg m⁻³) approaches but does not reach the f₂→0 origin.

```yaml
reproduction_outcome: partial
target: fig03 (smrt-v1 figure 3)
runs_executed: 6/6 (r1-r6, once each)
render_check_passed: true   # legibility only, not source comparison
curve_discrepancy: "SHS vs IND high-density ordering (source SHS>IND>HS; obtained IND>SHS>HS)"
likely_cause: "guessed stickiness=0.5 (not stated in figure)"
```

**Direct answer to the original question.** The requested validation — a common low-density origin and the ordering SHS > IND > HS — is reproduced for the shared origin and for HS being lowest, but **not** for SHS sitting above IND; the obtained ordering is IND > SHS > HS, most plausibly because stickiness was fixed at an assumed 0.5 rather than determined from the paper, which does not state it.
