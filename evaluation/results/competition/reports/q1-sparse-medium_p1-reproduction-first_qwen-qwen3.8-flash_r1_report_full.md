# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 renders all six curve families of [figure:smrt-v1#fig03] over density on the paper's own axis, plus one robustness curve. Read as a figure, it reproduces two of the three things Fig. 3 is there to show: the curves all leave the low-density end on top of one another, and within each microstructure pair the IBA curve sits slightly below its DMRT QCA-CP counterpart, the gap widening with density. It does **not** reproduce the third, and the one that carries the paper's argument: the terminal ordering of the three groups. In the source image the sticky-hard-sphere pair is the top band, the independent-sphere pair the middle, the non-sticky pair the bottom, flattened toward the right end — the braces in the right margin state that ordering explicitly. In our reproduction the sticky-hard-sphere pair is the *lowest* band, and the independent-sphere pair the highest. So the qualitative pattern of convergence-then-separation is reproduced, the separation *sequence* is inverted.

That inversion is attributable to the one physical parameter Fig. 3 never states. The paper gives radius (100 µm) and density range, but no stickiness for this figure; we assumed τ = 0.5. The recorded robustness run answers the question "is the ordering sensitive to that assumption?" affirmatively and with a definite sign: lowering τ from 0.5 to 0.2 moves the SHS + DMRT QCA-CP curve from lying below the independent-sphere reference to lying above it (mean bias −0.0011 m⁻¹ → +0.0018 m⁻¹ [model:smrt@1.5.1]). Since τ is the only free knob on that pair, a stickiness nearer the hard-sphere limit would push SHS up toward the paper's position. The ordering mismatch is therefore reported as a diagnostic on an unspecified parameter, not as a contradiction of a paper-explicit condition.

For the density quantities the original question asked for: the band of common first-order behaviour is visible in our figure over roughly the first fifth of the axis, and the paper states the sparse-medium approximation holds only for 10–20 kg m⁻³ [smrt-v1#08]. A numeric divergence threshold is **not identifiable** from either image — no digitization was performed, and the 40-point grid between 1 and 100 kg m⁻³ is spaced ≈2.5 kg m⁻³ apart (derived from the recorded sweep limits), which is coarser than the distinction being sought.

## Supporting results

**What the source figure supports** [figure:smrt-v1#fig03]. One panel, no sub-panels. x = Density (kg m⁻³), ticks 0–100 in 20s; y = Scattering coefficient (m⁻¹), ticks 0.000–0.025 in 0.005 steps. Six legend entries; colour encodes microstructure (blue IND, orange HS, green SHS), line style encodes theory (solid = Rayleigh for IND and DMRT QCA-CP for HS/SHS, dashed = IBA). Three margin braces label the terminal order SHS / IND / HS. All curves monotonic, concave upward, coincident near the origin, with a low-density crossover before SHS overtakes. The image supplies count, axes, units, grouping, ordering and shape; it supplies no digitized values and proves no numerical agreement.

**What the computed arrays support.** All seven approved runs completed and passed the model's quality control; each returned 40 points of κs against density [model:smrt@1.5.1]. The renderer's pairwise statistics, all taken against the IND + Rayleigh series over the full overlap 1–100 kg m⁻³:

| Series | bias (m⁻¹) | MAE | RMSE | r |
|---|---|---|---|---|
| IND + IBA | −0.0002 | 0.0002 | 0.0003 | 0.9999 |
| HS + DMRT QCA-CP | −0.0025 | 0.0025 | 0.0032 | 0.9789 |
| HS + IBA | −0.0028 | 0.0028 | 0.0037 | 0.9685 |
| SHS + DMRT QCA-CP (τ=0.5) | −0.0011 | 0.0011 | 0.0015 | 0.9967 |
| SHS + IBA (τ=0.5) | −0.0016 | 0.0016 | 0.0021 | 0.9929 |
| SHS + DMRT QCA-CP (τ=0.2) | +0.0018 | 0.0018 | 0.0024 | 0.9984 |

These are cross-run comparisons *inside* the local SMRT build. There is no paper array to score against, so model-versus-paper RMSE and correlation are N/A / not scoreable; the `r` values above are inflated by shared monotonicity across a common x-axis and should not be read as agreement.

**Comparison of the two readings.**

| Aspect | Source figure | Computed arrays | Verdict |
|---|---|---|---|
| Six curves, IND/HS/SHS × two theories | present | present (7 series incl. robustness) | agree |
| Collapse at the sparse end | visible | all biases | r ≈ 0.97–0.9999 with small absolute bias | agree |
| IBA below DMRT within each pair | visible | IND pair −0.0002; HS pair −0.0028 vs −0.0025; SHS pair −0.0016 vs −0.0011 | agree in direction at high density; in the IND and SHS pairs the dashed curve is the lower mean |
| Terminal order SHS > IND > HS | yes, brace-annotated | order inverted; SHS lowest at τ = 0.5 | disagree, qualified by unstated τ |
| HS flattening at the right edge | visible | HS has the most negative bias in both theories | same qualitative pattern |
| Divergence density | not digitizable | not resolvable on a ~2.5 kg m⁻³ grid | not identifiable |

The layout review flagged a crowded legend and long series labels and the figure was redrawn wider; it passed with no scientific issues [skill:research-reporting]. That establishes the chart is usable and legible, not that it agrees with the paper.

## Guessed / assumed parameters

No value in this row-group comes from Fig. 3 itself; each is a choice we made or the backend made.

- `sweep_parameter` = density_kg_m³ — **paper_inferred** (paper_value "0 to 100 kg m⁻³"; the swept quantity is the declared independent variable)
- `sweep_start` = 1 — **model_assumption** (paper_value 0; density 0 is outside the declared range, so the sweep begins at the smallest executable value; the figure origin is therefore *not* sampled)
- `sweep_points` = 40 — **model_assumption** (paper_value None; resolution choice, affects no physics)
- `stickiness` = 0.5 — **user_specified** (paper_value not stated for Fig. 3; this is the parameter the ordering disagreement turns on, with τ = 0.2 carried as the robustness curve)
- `temperature_k` = 265 — **backend_default** (not stated; identical across runs so it cannot bias the theory comparison)
- `thickness_m` = 1 — **backend_default** (single homogeneous layer; κs is a layer property, thickness does not enter it)
- `angle_deg` = 55 — **backend_default** (not applicable; Fig. 3 implies no sensor geometry)
- `dort_streams` = 32 — **backend_default** (inert: `output = coefficients` performs no radiative-transfer solve)
- `corr_length_m` = 0.00015 — **backend_default** (no ACF microstructure is plotted in Fig. 3)
- `density_kg_m3` = 300.0 — **backend_default** (inserted during parameter resolution, overridden by the sweep; not paper evidence)

Paper-explicit conditions held fixed: `output = coefficients` matched to Scattering coefficient (m⁻¹) [figure:smrt-v1#fig03]; `radius_m` = 0.0001 (100 µm) [figure:smrt-v1#fig03]; `frequency_ghz` = 37 [smrt-v1#07]; `sweep_stop` = 100 [figure:smrt-v1#fig03]. Theory and microstructure assignments per curve are **user_specified** against the legend and the microstructure definitions [smrt-v1#05], and `microstructure_model = non_sticky_hard_spheres` is the local adapter's translation of the none-sticky limit.

## Limitations

- SMRT 1.5.1 local versus the paper's SMRT v1.0 [model:smrt@1.5.1]; a version difference cannot be excluded as a contributor to the SHS placement.
- Reproduction is at `output = coefficients`: κs is compared directly, with no radiative-transfer solve, so the figure carries no information about solvers, polarization or emission — a different question from Figs. 4–6 of the paper [smrt-v1#08].
- The sparse limit itself is untested at the origin because the sweep starts at 1 kg m⁻³, and divergence onset is unresolvable to better than ≈2.5 kg m⁻³.
- No numeric agreement with the paper is claimed or scoreable: no digitization of the source asset was performed, and reading a source figure is not model data.
- All seven series share one radius, one frequency and one temperature; only the density axis varies. Conclusions about the size dependence of these orderings are outside this experiment [smrt-v1#05].

**Outcome (from recorded state):** rendered = true; required curves present = 6 of 6 (plus 1 robustness run); figure quality review = passed after redraw; unavailable/unrun comparisons = none; target `fig03` = covered by `chart_fig03_repro`; scientific verdict = qualitative convergence and theory-pair pattern reproduced, terminal microstructure ordering not reproduced, classified as a diagnostic on the unstated stickiness rather than a failure of a paper-explicit condition.
