# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 (`chart_fig03`, seven plotted series, x = density in kg m⁻³, y = scattering coefficient ks in m⁻¹) shows the six Figure 3 combinations as one bundle at the left edge, opening into a fan to the right in a fixed order: non-sticky hard spheres (HS) lowest, independent spheres (IND) in the middle, sticky hard spheres (SHS) highest, and DMRT QCA‑CP above IBA inside each microstructure pair [model:smrt@1.5.1]. Convergence at low density and divergence by microstructure rather than by electromagnetic theory are the two patterns the paper states for this figure [smrt-v1#08], and the generated curves show the same qualitative pattern.

For the quantity the question asks — the density at which the six agree, and the density at which they separate — the opened paper evidence gives the validity band of the sparse‑medium approximation as **10–20 kg m⁻³**, described as valid "only for very low densities" and unrealistic for snow modelling [smrt-v1#08]. The recorded arrays place full six‑curve convergence **below about 10 kg m⁻³**, not inside that band: spread between the highest and lowest curve is 1.2 % at 1 kg m⁻³, 14.5 % at 11.2 kg m⁻³, 24 % at 18.1 kg m⁻³, 69.5 % at 45.4 kg m⁻³ and 194 % at 100 kg m⁻³ [model:smrt@1.5.1]. So the paper's 10–20 kg m⁻³ band is where agreement is *already failing* by 15–24 %, and there is no sharp threshold on the computed grid (30 points over 1–100 kg m⁻³, ≈3.4 kg m⁻³ steps): separation is gradual, and the exact onset density is not identifiable more finely than this grid without a denser sweep, which was not part of the approved plan.

## What the generated figure supports

Image‑level reading of `chart_fig03` — curve count and identity (IND + Rayleigh, IND + IBA, HS + DMRT QCA‑CP, HS + IBA, SHS + DMRT QCA‑CP, SHS + IBA, plus one diagnostic series), visible merging of all series at the left edge, visible fanning beginning in the 10–20 kg m⁻³ region, visible ordering HS < IND < SHS and DMRT > IBA, and a straight line for IND + Rayleigh against downward curvature for HS and upward curvature for SHS [model:smrt@1.5.1]. The automatic render check confirmed only that the plotted arrays are finite, dense enough and legible; it is not a comparison with the source figure [model:smrt@1.5.1]. The source figure's own image was not digitized in this session, so nothing here rests on reading values off it: the correspondence claim below is against the figure caption and Section 3.1.1, which state the shared linear trend at f²→0, the microstructure‑dominated deviation, and the 10–20 kg m⁻³ limit, and give no tabulated ks values [smrt-v1#fig-fig03][smrt-v1#08].

## What the computed arrays support

ks in units of 10⁻⁶ m⁻¹, except the first column (10⁻⁷), from the seven approved runs (handles `res_69539de364b8`, `res_022d0ef7d84d`, `res_a994d35f9c70`, `res_c0ffff1ecdb0`, `res_9d5d10596b95`, `res_3ee270873ac6`, `res_6f5b1ea3f0c9`) [model:smrt@1.5.1]:

| density kg m⁻³ | IND+Ray | IND+IBA | HS+DMRT | HS+IBA | SHS+DMRT | SHS+IBA |
|---|---|---|---|---|---|---|
| 1.0 | 1.398 | 1.398 | 1.389 | 1.387 | 1.404 | 1.402 |
| 11.2 | 1.572 | 1.566 | 1.459 | 1.438 | 1.647 | 1.623 |
| 18.1 | 2.526 | 2.511 | 2.241 | 2.190 | 2.720 | 2.657 |
| 45.4 | 6.344 | 6.246 | 4.705 | 4.441 | 7.528 | 7.105 |
| 100.0 | 13.98 | 13.46 | 7.255 | 6.416 | 18.85 | 16.67 |

- **Microstructure dominates theory**, the paper's own ordering, quantified at 45.4 kg m⁻³: with IBA held fixed the three microstructures span a factor 1.60 (7.105 vs 4.441 ×10⁻⁶ m⁻¹), while switching theory at fixed microstructure moves ks by only 1.6 % (IND), 5.9 % (HS) and 6.0 % (SHS) [model:smrt@1.5.1][smrt-v1#08].
- IND + Rayleigh is exactly linear in density: ks(100)/ks(1) = 13.98×10⁻⁶ / 1.398×10⁻⁷ = 100.0, which is what makes it a usable sparse‑medium reference line [model:smrt@1.5.1].
- Curve‑shape statistics against that reference, taken from the chart's own comparison record: r = 0.9999 (IND+IBA), 0.9996 (SHS+IBA), 0.9984 (SHS+DMRT at stickiness 0.2), 0.9966 (SHS+DMRT diagnostic), 0.9786 (HS+DMRT), 0.9678 (HS+IBA). The bias, mae and rmse in that record are returned as 0.0 only because ks here is of order 10⁻⁶ m⁻¹, so they are uninformative and only the r row is used [model:smrt@1.5.1].
- Stickiness sensitivity (SHS + DMRT QCA‑CP, τ = 0.5 versus τ = 0.2): 1.3949×10⁻⁷ vs 1.404×10⁻⁷ m⁻¹ at 1 kg m⁻³ (−0.6 %), 5.6738×10⁻⁶ vs 7.528×10⁻⁶ at 45.4 kg m⁻³ (−24.6 %), and 1.0684×10⁻⁵ vs 1.885×10⁻⁵ m⁻¹ at 100 kg m⁻³ (−43 %). The τ = 0.5 value at 100 kg m⁻³ lies *below* the sparse line (13.98×10⁻⁶) whereas τ = 0.2 lies above it, so the sign of the SHS deviation from linearity is set by the assumed stickiness, while convergence near the origin is not [model:smrt@1.5.1].
- Absorption at 100 kg m⁻³: ka = 0.0817 m⁻¹ (Rayleigh), 0.0932 m⁻¹ (the three IBA curves), 0.0977 m⁻¹ (both DMRT curves), with effective permittivity 1.1523 for DMRT and 1.1497 for IBA [model:smrt@1.5.1]. These are companion outputs of the same coefficient solve, not independent evidence for ks, and the Rayleigh pair does not treat the effective permittivity on the same dense‑media footing, so they are reported for context only [skill:model-comparison].

## The two readings compared

| Aspect | Generated figure | Computed arrays | Status |
|---|---|---|---|
| Convergence at low density | all series merge at the left edge | 1.2 % spread at 1 kg m⁻³ | agree |
| Where agreement stops | separation opens in the 10–20 kg m⁻³ zone | 14.5 % at 11.2, 24 % at 18.1 kg m⁻³ | agree, with the qualification that the paper's band is where the spread is already 15–24 %, and the onset is grid‑limited to ≈3.4 kg m⁻³ [smrt-v1#08] |
| Ordering HS < IND < SHS; DMRT > IBA | visible | factor 1.60 across microstructures vs ≤6 % across theories at 45.4 kg m⁻³ | agree |
| Curve shape | straight IND line; HS bends down, SHS bends up | IND+Ray exactly proportional to density (ratio 100.0) | agree |
| Absolute ks magnitude | — | 1.39×10⁻⁷ to 1.89×10⁻⁵ m⁻¹ over the sweep | **not scoreable**: no tabulated reference values and no digitized figure; the frequency (frequency_ghz = 37) is an assumption, so magnitude is a diagnostic, not a claimed reproduction |
| The limit f²→0 | Figure 3 starts at zero on the density axis [smrt-v1#fig-fig03] | lowest legal point is 1 kg m⁻³ (sweep_start = 1) | approached, not evaluated |
| SHS branch direction at high density | above the bundle | above at stickiness 0.2, below at 0.5 | qualified by the assumed stickiness |

Outcome: the qualitative reproduction — same curves, same convergence, same fan, same ordering, same microstructure‑first attribution — is successful. Numerical agreement with Figure 3 is not claimed and is not scoreable from the evidence opened here.

## Guessed/assumed parameters

The automatically appended parameter‑source table records the full ledger; grouped here as required: `sweep_stop = 100` is paper_inferred (top of the printed density axis [smrt-v1#fig-fig03]). `sweep_start = 1`, `sweep_points = 30`, `stickiness = 0.2` and `frequency_ghz = 37` are model_assumption — the paper states no frequency, temperature, stickiness or sampling density for this figure [smrt-v1#fig-fig03], the origin is unrunnable because the declared minimum density is 1 kg m⁻³ [model:smrt@1.5.1], and these two assumptions are the ones that can move the result (see the stickiness sensitivity above). `temperature_k = 265`, `angle_deg = 55.0`, `thickness_m = 1.0`, `density_kg_m3 = 300.0`, `corr_length_m = 0.00015` and `dort_streams = 32` are backend_default; `density_kg_m3 = 300.0` and `angle_deg = 55.0` are comparison context only (the paper's 300 kg m⁻³ belongs to its Figure 4 comparison, not to Figure 3 [smrt-v1#08]), `corr_length_m = 0.00015` is inert for the sphere‑based microstructures, and `thickness_m = 1.0` with `dort_streams = 32` are inert because `output = coefficients` returns ka and ks without solving the radiative transfer equation, which is also why no brightness temperature or backscatter exists in these runs [guideline:smrt@1.0]. `output = coefficients` and `sweep_parameter = density_kg_m3` are paper_explicit; `radius_m = 0.0001` and the three microstructure and three electromagnetic choices are recorded as user_specified run inputs, chosen to match the paper's IND/HS/SHS and Rayleigh/DMRT QCA‑CP/IBA labels [smrt-v1#05][smrt-v1#fig-fig03].

## Limitations

The result is a reproduction of trend, ordering and onset, not of magnitude; absolute ks scales with the assumed 37 GHz, so magnitudes cannot be compared to Figure 3. The whole sweep lies at the sparse end of a range the paper itself calls unrealistic for snow — it is a deliberate mathematical limit case, and dense‑media treatment is required for real snow [smrt-v1#08]. The SHS position in the fan above ≈20 kg m⁻³ depends first‑order on the assumed stickiness and so is qualified rather than established. The 1–100 kg m⁻³ axis was sampled at ≈3.4 kg m⁻³ steps, so a sharper "density at which they separate" is not identifiable from these runs. The comparison of the two runs' ks against ka, or of one curve against its own transform, is not counted as extra support [skill:model-comparison]. All six curves plus the diagnostic were supported by the registered model and the capability checkpoint recorded nothing unavailable and nothing non‑comparable, so no partial‑scope decision was needed.

```
reproduction_outcome
  question: density band of agreement and separation of the six Figure 3 ks curves
  objective: recompute the six ks(density) curves and read the agreement/separation band from arrays
  plan: v001, phase approved; capability_check: ready; supported: smrt@1.5.1; unavailable: none; not_comparable: 0
  targets: fig03 -> planned, 7 approved runs (6 curves + 1 stickiness diagnostic), all success, quality control passed
  charts: chart_fig03 confirmed and rendered (7 series, 210 points); render check passed = legibility only, not a source-figure comparison
          chart_stickiness approved in plan but not in the confirmed package; its run is plotted as the 7th labelled series
  paper_answer: sparse-medium approximation valid only for 10-20 kg m-3 [smrt-v1#08]
  computed_answer: six-curve spread 1.2 % at 1 kg m-3, 14.5 % at 11.2, 24 % at 18.1, 69.5 % at 45.4, 194 % at 100 kg m-3
  attribution_from_arrays: microstructure factor 1.60 vs theory <=6.0 % at 45.4 kg m-3
  scoreable_numbers: r = 0.9678-0.9999 vs IND+Rayleigh (chart comparison record); bias/mae/rmse returned 0.0, uninformative at ks ~ 1e-6 m-1
  magnitude_vs_figure3: N/A / not scoreable (no tabulated values, figure not digitized, frequency_ghz = 37 assumed)
  origin_limit: not evaluated (density minimum 1 kg m-3, sweep_start = 1)
  outcome: qualitative reproduction successful; numerical reproduction not claimed
```

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | output | coefficients | paper_explicit | smrt-v1#fig03 |
| smrt | radius_m | 0.0001 | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | independent_sphere | user_specified | smrt-v1#05 |
| smrt | microstructure_model | non_sticky_hard_spheres | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | sticky_hard_spheres | user_specified | smrt-v1#05 |
| smrt | electromagnetic_model | rayleigh | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | iba | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | dmrt_qcacp_shortrange | user_specified | smrt-v1#05 |
| smrt | sweep_parameter | density_kg_m3 | paper_explicit | smrt-v1#fig03 |
| smrt | sweep_start | 1 | model_assumption | smrt-v1#fig03 |
| smrt | sweep_stop | 100 | paper_inferred | smrt-v1#fig03 |
| smrt | sweep_points | 30 | model_assumption | smrt-v1#fig03 |
| smrt | stickiness | 0.2 | model_assumption | smrt-v1#fig03 |
| smrt | frequency_ghz | 37 | model_assumption | smrt-v1#fig03 |
| smrt | temperature_k | 265 | backend_default | smrt-v1#fig03 |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | thickness_m | 1.0 | backend_default | - |
| smrt | density_kg_m3 | 300.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
