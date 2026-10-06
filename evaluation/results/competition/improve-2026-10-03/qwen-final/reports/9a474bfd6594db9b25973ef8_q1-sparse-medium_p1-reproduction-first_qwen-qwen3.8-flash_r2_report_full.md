# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure (Figure 1, six series, x = Density in kg m⁻³, y = Scattering coefficient in m⁻¹) shows the pattern the source figure was drawn to demonstrate: **all six microstructure/electromagnetic-theory curves converge at the bottom of the density axis and fan out as density rises, and they separate into three persistent pairs in which the Rayleigh or DMRT QCA-CP curve sits above its IBA partner.** [model:smrt@1.5.1] Against the inspected source image the axes, units, six-item legend, the IND/HS/SHS grouping, the within-pair solid-above-dashed ordering, the straight line of the independent-spheres-Rayleigh curve and the steep concave-up shape of the sticky-hard-sphere pair are all the same qualitative pattern [figure:smrt-v1#fig03]. One feature does not carry over: in the source image the sticky-hard-sphere pair climbs to the top of the plotted range and sits **above** the independent-sphere pair, whereas in the generated figure it ends **between** the non-sticky and independent groups. That rank reversal involves the only Fig. 3 input the paper never states — the stickiness — so it is reported below as a diagnostic of the assumed parameter, not as a contradicted paper condition.

For the quantity the question asks about, density: the opened paper evidence gives the validity range of the sparse-medium approximation as **10–20 kg m⁻³**, which it calls unrealistic for snow modelling [smrt-v1#08]. The recorded runs cover **1 to 100 kg m⁻³ in 50 points**, so the paper's range lies inside the sweep; the arrays show mutual agreement of about 1% at 1 kg m⁻³, a spread of about 7.7% near 9 kg m⁻³ and about 17% near 19 kg m⁻³ — i.e. divergence already beginning at the upper edge of the 10–20 kg m⁻³ band the paper names, growing to a factor of about 2.2 between highest and lowest curve at 100 kg m⁻³. The 300 kg m⁻³ figure quoted in the same section belongs to the Fig. 4 angle comparison, not to this one [smrt-v1#08].

## What the image supports

Source image [figure:smrt-v1#fig03]: single panel; x-axis Density (kg m⁻³) with ticks 0–100; y-axis Scattering coefficient (m⁻¹) with ticks 0.000–0.025; six legend entries pairing three microstructures with two theories; curves read as IND ≈ linear and mid-range, SHS steepest and highest, HS lowest. Generated figure [model:smrt@1.5.1]: same six named series, same units, same low-density convergence, same within-pair ordering, same linearity of IND-Rayleigh, same concave-up SHS shape, but SHS ranked second rather than first. No curve value was digitized from the source image, so no point-by-point agreement with it is claimed or scoreable.

## What the run arrays support

At 100 kg m⁻³: IND-Rayleigh 0.01398 m⁻¹, IND-IBA 0.01343, SHS-DMRT QCA-CP 0.01068, SHS-IBA 0.00943, HS-DMRT QCA-CP 0.00726, HS-IBA 0.00642; at 1 kg m⁻³ all six lie in 0.0001384–0.0001398 m⁻¹. [model:smrt@1.5.1] The chart's own statistics against IND-Rayleigh over the 50-point overlap (1–100 kg m⁻³) are: IND-IBA r = 0.9999, rmse 0.0003; SHS-DMRT r = 0.9967, rmse 0.0015, bias −0.0011; SHS-IBA r = 0.993, rmse 0.0021; HS-DMRT r = 0.9791, rmse 0.0032, bias −0.0025; HS-IBA r = 0.9687, rmse 0.0037, bias −0.0028 m⁻¹. Supporting physics from the same arrays: `single_scattering_albedo` is constant at 0.1460 for IND-Rayleigh while it falls to 0.126 (IND-IBA) and 0.064 (HS-DMRT) with density, and `effective_permittivity` stays at 1.0 for Rayleigh but rises to 1.1497 (IBA) and 1.1523 (DMRT QCA-CP) — the mixing formula is active only in the dense-media theories. Against measured data: not applicable; nothing here was compared to observations.

## Comparison of the two conclusions

| Aspect | Image-based | Array-based | Verdict |
|---|---|---|---|
| Six curves, axes, units, legend, pairing | Present in both | Present in both | Agree |
| Convergence at low density, fan-out at high | Visible | Quantified above | Agree |
| Within-pair ordering (solid above IBA dashed) | Visible | 0.01398 > 0.01343 etc. | Agree |
| IND-Rayleigh linearity | Visible | ks ∝ density, albedo constant | Agree |
| SHS rank and top-of-axis magnitude | Highest, near top of 0.000–0.025 range | 0.01068 m⁻¹, ranked third | **Disagree** |
| x-axis start | 0 kg m⁻³ | 1 kg m⁻³ | Rendering/scope difference; 0 is not a valid input |

The disagreement is confined to the two SHS curves and traces to stickiness = 0.5, a value the paper states for a different figure's configuration and not for Fig. 3 [smrt-v1#08]; Section 8 also shows the SHS short-range results are strongly stickiness-dependent [smrt-v1#08], so the missing input is precisely the one that controls the disagreeing quantity. The render check passed, which establishes only that the plotted arrays are finite, dense and legible; it is not evidence that the figure matches the source, and the correspondence above rests on the curves compared against the source image. Reproduction outcome: **qualitative reproduction successful for the sparse-medium convergence, divergence and within-pair ordering; SHS group magnitude and rank unresolved pending the stickiness the paper does not give.**

## Guessed/assumed parameters

Paper-explicit inputs are only the observable (Scattering coefficient (m⁻¹)), radius_m = 0.0001 and frequency_ghz = 37. Everything else was supplied by the user or the system and is listed here: **user_specified** stickiness = 0.5 for the sticky-hard-sphere curves (0.2 elsewhere, ignored by IND and HS), taken from the Sect. 8 comparison configuration rather than from Fig. 3; **model_assumption** thickness_m = 1 standing in for the semi-infinite medium, and the choice of electromagnetic_model = rayleigh, microstructure_model = independent_sphere, sweep_parameter = density_kg_m3, sweep_start = 1.0, sweep_stop = 100.0, sweep_points = 50; **backend_default** density sweep resolved as 1 to 100 kg m⁻³ against the paper's 0 to 100 kg m⁻³, temperature_k = 265 (not stated for Fig. 3; only the Fig. 4 configuration states 256 K), and angle_deg = 55.0, corr_length_m = 0.00015, dort_streams = 32, which have no effect on a coefficients-mode run. Because stickiness is assumed, the SHS rank in this report should be read as conditional on it.

## Limitations

- SMRT v1.5.1 was run; the published figure comes from version-1.0 code, and version-level numerical differences are not separated from the stickiness effect [skill:model-comparison].
- Comparisons are between formulations of one model at one configuration (37 GHz, 100 µm, coefficients mode); they are not predictions of brightness temperature or backscatter, and no measurement constrains them.
- Source-figure values were not digitized, so agreement is assessed on shape, count, grouping, ordering and visible separation only.
- Densities below roughly 50 kg m⁻³ are outside realistic snow ranges; the low end of the sweep exists to reproduce the published axis.
- The DMRT QCA-CP short-range approximation has stated validity limits in radius and stickiness [smrt-v1#08]; this report follows the research-reporting procedure for provenance and outcome calibration [skill:research-reporting].

```outcome
target: smrt-v1#fig03
status: qualitative_reproduction_successful_with_unresolved_component
runs: ind_rayleigh, ind_iba, hs_dmrtqcacp, hs_iba, shs_dmrtqcacp, shs_iba (6/6 succeeded)
chart: fig03_ks_vs_density | series=6 | points=50 | render_check=passed_legibility_only
paper_explicit_inputs: output=Scattering coefficient (m^-1); radius_m=0.0001; frequency_ghz=37
assumed_inputs: stickiness=0.5 [user_specified]; thickness_m=1, sweep_start=1.0, sweep_stop=100.0, sweep_points=50, sweep_parameter=density_kg_m3, electromagnetic_model=rayleigh, microstructure_model=independent_sphere [model_assumption]; temperature_k=265, angle_deg=55.0, corr_length_m=0.00015, dort_streams=32, density sweep 1-100 [backend_default]
density_answer: paper=10-20 kg m^-3 [smrt-v1#08]; recorded_sweep=1-100 kg m^-3 (50 pts)
agreement_metrics: r=0.9687-0.9999; rmse=0.0003-0.0037 m^-1 vs IND-Rayleigh
numeric_agreement_with_source: not_scoreable (no digitization)
discrepancy: SHS rank and magnitude; cause=candidate assumed stickiness; status=unresolved
measurement_comparison: none

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | output | coefficients | paper_explicit | smrt-v1#fig03 |
| smrt | radius_m | 0.0001 | paper_explicit | smrt-v1#08 |
| smrt | density_kg_m3 | sweep 1 to 100 kg m^-3, 50 points | backend_default | smrt-v1#fig03 |
| smrt | frequency_ghz | 37 | paper_explicit | smrt-v1#07 |
| smrt | stickiness | 0.5 | user_specified | smrt-v1#08 |
| smrt | temperature_k | 265 | backend_default | smrt-v1#07 |
| smrt | thickness_m | 1 | model_assumption | smrt-v1#07 |
| smrt | electromagnetic_model | rayleigh | model_assumption | - |
| smrt | microstructure_model | independent_sphere | model_assumption | - |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_parameter | density_kg_m3 | model_assumption | - |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | model_assumption | - |
| smrt | sweep_points | 50 | model_assumption | - |
