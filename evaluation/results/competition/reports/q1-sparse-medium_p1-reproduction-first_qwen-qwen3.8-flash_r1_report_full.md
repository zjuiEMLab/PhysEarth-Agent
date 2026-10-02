# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

# Reproduction report — SMRT Fig. 3: sparse-medium scattering coefficient

## Research result and conclusion

The generated figure reproduces the published one qualitatively. Six κ_s(ρ) curves from SMRT v1.5.1 at 100 µm radius and 37 GHz leave the common origin, fan out from roughly 20 kg m⁻³, and keep the order the paper's right-margin braces show — sticky hard spheres highest, independent spheres intermediate, non-sticky hard spheres lowest — with the IBA member of each colour pair falling below its Rayleigh or DMRT QCA-CP partner [figure:smrt-v1#fig03] [model:smrt@1.5.1]. Outcome: **reproduced; quantitatively partially comparable.**

The original question asked for the density band of sparse-medium convergence and the density at which the representations separate. From the arrays: convergence extends to about **20 kg m⁻³**, where the per-unit-density slopes of the three families agree to within roughly ±18 % (1.83 × 10⁻⁴ for IND/Rayleigh, 1.51 × 10⁻⁴ for SHS/DMRT QCA-CP, 1.52 × 10⁻⁴ for HS/DMRT QCA-CP, each m⁻¹ per kg m⁻³, derived by me near ρ ≈ 19). Beyond that the separation grows monotonically, and at 100 kg m⁻³ the six series span about a factor of 10, from 0.0189 m⁻¹ down to 0.00177 m⁻¹. There is no threshold density: the departure is smooth and centred just above 20 kg m⁻³, which matches the paper's statement that the sparse-medium approximation holds only at about 10–20 kg m⁻³ [smrt-v1#08].

A sensitivity run adds the caveat that matters most: the assumed SHS stickiness is irrelevant in the convergence band and decisive above it. At τ = 0.2 versus τ = 0.5, κ_s at ~19 kg m⁻³ changes by 0.4 %, but at ~54 kg m⁻³ it changes by 31 % (0.00926 versus 0.00638 m⁻¹) [model:smrt@1.5.1]. So the green pair's position at the top of the range is not secured by the paper, while the convergence band is.

## Supporting results

Seven runs of 40 density points each (1–100 kg m⁻³), all quality checks passed with no problems reported. κ_s values at 100 kg m⁻³:

| Series | κ_s (m⁻¹) | Handle |
| --- | --- | --- |
| SHS + DMRT QCA-CP (τ = 0.2) | 0.0189 | `res_8a496668664b` |
| IND + Rayleigh | 0.0134 | `res_9ef4816f0b2e` |
| HS + DMRT QCA-CP | 0.0116 | `res_02953e8c0d0a` |
| HS + IBA | 0.00357 | `res_eeb7391d8985` |
| IND + IBA | 0.00177 (saturating) | `res_2070142ba1cc` |
| SHS + DMRT QCA-CP (τ = 0.5, diagnostic) | 0.00638 at ~54 kg m⁻³ | `res_21823996c64d` |

Every series increases monotonically with density, and the effective permittivity rises only 1.0014 → 1.1523 across the range, so the media remain dielectrically sparse even where scattering is no longer sparse. Two papers-side statements are corroborated: microstructure deviates from sparse-medium behaviour more strongly than the choice of electromagnetic theory [smrt-v1#08], and each formulation shares a cubic low-density limit that all curves must obey [smrt-v1#05].

## Parameter provenance

| Input | Value used | Provenance | Evidence or reason |
| --- | --- | --- | --- |
| `radius_m` | 0.0001 | paper_explicit | Caption states 100 µm; overrides the 2 × 10⁻⁴ default [smrt-v1#fig03] |
| `sweep_parameter` | `density_kg_m3` | paper_explicit | Density on the x axis; everything else held fixed [smrt-v1#fig03] |
| `sweep_stop` | 100 | paper_explicit | Matches the plotted range [smrt-v1#fig03] |
| `frequency_ghz` | 37 | paper_explicit | Section-wide default for the validation figures [smrt-v1#07] |
| `output` | `coefficients` | paper_inferred | Fig. 3 plots scattering coefficient in m⁻¹, a medium property; this returns κ_s without solving radiative transfer [smrt-v1#fig03] |
| `electromagnetic_model` | Rayleigh / IBA for IND; DMRT QCA-CP / IBA for HS and SHS | user_specified | Taken one-to-one from the legend; the submitted experiment differs from the paper condition, the paper value stays as comparison context |
| `microstructure_model` | `independent_sphere`, `non_sticky_hard_spheres`, `sticky_hard_spheres` | user_specified | Same legend mapping, same qualification |

### Guessed/assumed parameters

| Input | Value used | Provenance | Paper value | Effect |
| --- | --- | --- | --- | --- |
| `sweep_start` | 1 | paper_inferred | 0 | Declared model minimum is 1.0 kg m⁻³, so the origin is approached but not reached; softens only the very first points |
| `sweep_points` | 40 | model_assumption | not stated | A trend needs enough points to show shape; changes no physics |
| `stickiness` | 0.2 | model_assumption | not reported | Bounded by the τ = 0.5 run: 0.4 % at ~19, 31 % at ~54 kg m⁻³ |
| `temperature_k` | 265 | backend_default | not reported | Enters weakly through the ice permittivity |
| `thickness_m` | 1 | backend_default | semi-infinite | Recorded for completeness; cannot affect κ_s |
| `angle_deg` | 55 | backend_default | not applicable | Unused by the coefficients output |
| `corr_length_m` | 0.00015 | backend_default | not applicable | All six series are sphere-based representations |
| `dort_streams` | 32 | backend_default | not applicable | Kept out of the comparison deliberately |
| `density_kg_m3` | 300.0 | backend_default | none | Inserted by the registered model during parameter resolution; replaced point-by-point by the sweep, so it carries no evidence and no result |

The frequency is paper-explicit from §.7 rather than printed on the figure, and the SHS stickiness is the only assumption that could imitate the paper's physics, since lower τ means more clustering and higher κ_s [smrt-v1#05].

## What the images support

Source figure, read from the attached asset: single panel, x = Density (kg m⁻³) from 0 to 100 with ticks every 20, y = Scattering coefficient (m⁻¹) from 0.000 to 0.025 with ticks every 0.005, six legend series in three colour pairs with line style carrying the theory, braces ordered SHS, IND, HS, SHS convex and topmost, HS concave and lowest, IND near-linear, no crossings after the origin [figure:smrt-v1#fig03]. Nothing was digitised; the convergence region is compressed into the left few percent of the panel, so onset is readable only to about ±10 kg m⁻³.

Generated figure: same observables and units, seven plotted series — the extra one is the τ = 0.5 diagnostic, not part of the published comparison — and a tighter y window (0–0.019 m⁻¹), so the fan-out fills the panel instead of the upper third. It was checked against the source image by reading both; the automatic render check confirmed only that the plotted arrays are finite, dense and legible, and is not evidence of agreement with the paper.

## What the result arrays support

The orderings, the monotonic shapes and the onset of separation are computed from the run arrays named above: agreement of slopes to ±18 % near 19 kg m⁻³, and the high-density spread of 0.0189 / 0.0134 / 0.0116 m⁻¹ across the three bundles. These are model outputs, not measurements, and no measured κ_s of artificial sparse media exists in this environment.

## Figure versus results

| Question | Figure-based reading | Result-backed reading | Agreement and qualification |
| --- | --- | --- | --- |
| Do all six coincide at low density? | Within about one line width up to ~10–20 kg m⁻³ | Slope spread ±18 % near 19 kg m⁻³ | Agreement. The image cannot resolve the residual offsets that the arrays show |
| Bundle order at high density | SHS > IND > HS by brace order | 0.0189 > 0.0134 > 0.0116 m⁻¹ at 100 kg m⁻³ | Agreement on the Rayleigh/DMRT member of each pair |
| IBA below the other theory in each pair | Yes, most visibly for SHS | IND + IBA 0.00177 and HS + IBA 0.00357 against 0.0134 and 0.0116 | Same direction, and the computed gaps are larger than the figure's line spacing suggests — a y-range and aspect-ratio effect, not a physics difference |
| Curvature of each bundle | SHS convex, HS concave, IND near-linear | HS flattens toward ~100; IND + IBA saturates at 0.0018 | Agreement for SHS and HS. IND + IBA saturation is not distinguishable from the source image at this compression |
| Where does separation begin | ~20 kg m⁻³, readable to ±10 kg m⁻³ | Smooth departure centred just above 20 kg m⁻³ | Agreement within the image's resolution. No single threshold density is identifiable from either |
| Quantitative residuals against the paper curves | Not available | Not available | N/A — the source figure was inspected, not digitised, so no point-by-point comparison, RMSE, bias or correlation exists and none is claimed |

Differences that remain are attributable to the rendering window (y range and aspect ratio), to the assumed stickiness, and to `sweep_start = 1` rather than 0; none of them contradicts a condition the paper states explicitly.

## Limitations

SMRT treats the medium as one homogeneous layer of uniform spheres; a real snowpack is stratified and polydisperse, so this is a first-order answer. The upper density reached, 100 kg m⁻³, is well above natural snow and sits at the sparse-medium limit where, as the paper itself notes, a result is a statement about the theory rather than about a snowpack — which is exactly what Fig. 3 is for, and it is why the high-density values should not be read as snow. Agreement with the published figure is qualitative: shape, ordering, onset and direction of the within-pair splitting. Absolute values, the SHS curve's height at the top of the range, and any numeric tolerance remain unverified because the source curves were not digitised and the stickiness was assumed.

```outcome
target: smrt-v1#fig03
model: smrt@1.5.1
runs: 7 (6 reproduction series + 1 stickiness diagnostic), 40 points each, all QC passed
figure: 1 rendered, render_check=true (legibility only)
comparison_with_source: qualitative, by inspection of both images; no digitisation
outcome: reproduced_qualitatively; quantitatively partial
paper_explicit_conditions: radius=100 um, sweep=density 1-100 kg m-3, frequency=37 GHz -> honoured
contradicted_paper_explicit_conditions: none
assumed_inputs: stickiness=0.2 (model_assumption), sweep_points=40 (model_assumption),
  sweep_start=1 (paper_inferred), output=coefficients (paper_inferred),
  temperature/thickness/angle/corr_length/dort_streams (backend_default),
  density_kg_m3=300.0 (backend_default, replaced by sweep)
unavailable_or_unrun_comparisons: none
agreement_statistics: N/A (no digitised reference curve)
```
