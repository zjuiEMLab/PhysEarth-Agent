# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

Executing the approved runs now.

All 7 approved runs succeeded. Rendering the selected charts.

Both approved charts: one is in the confirmed package, one is not. Running the render check and re-opening the Fig. 3 evidence I need for the provenance spans.

Both approved runs are done and the main chart passed its render check. The frequency diagnostic was executed but is not in the confirmed chart package, so I will draw it from its existing handle.

All seven approved runs succeeded; the confirmed chart `fig03_ks_vs_density` (6 series × 25 points) rendered and passed its render check (crowded-legend redraw only). The frequency diagnostic ran but is not in the confirmed chart package, so I drew it from its existing handle for the level check below.

## Answer

**The paper's claim reproduces in shape and in ranking, but not in absolute level.** All six SMRT formulations start from one and the same linear origin, and microstructure (not electromagnetic theory) dominates the departures — exactly as [smrt-v1#08] states [skill:research-planning].

**Shared origin.** At 1 kg m⁻³ all six `ks` curves fall in 0.0004605–0.0004662 m⁻¹, a spread of 1.2 %; at 9.25 kg m⁻³ the spread is 0.00399–0.00431 m⁻¹ (≈8 %) [model:smrt@1.5.1]. The origin slope is ≈4.6 × 10⁻⁴ m⁻¹ per kg m⁻³ for every combination, matching "at the origin (for f2→0) the linear trend is the same for several microstructures ... and different theories" [smrt-v1#08].

**Departure from that line at 100 kg m⁻³** (endpoint ratio `ks(100) / [100·ks(1)]`, derived from the run arrays): independent spheres + Rayleigh 1.00 (strictly linear), IND + IBA 0.96, SHS + DMRT QCA-CP 0.77, SHS + IBA 0.68, HS + DMRT QCA-CP 0.52, HS + IBA 0.47. At the fixed IBA theory the three microstructures span a factor 2.1 (0.0447 / 0.0314 / 0.0214 m⁻¹), whereas at the fixed sticky-hard-sphere microstructure the two theories differ by only 13 % (0.0356 vs 0.0314 m⁻¹). The microstructure signal therefore outweighs the theory signal over the whole plotted range, as the figure asserts [model:smrt@1.5.1]. Correlation of each curve against IND + Rayleigh is 0.9999 (IND IBA), 0.9966, 0.9928, 0.9784, 0.9679 — same shape, different level, with bias growing with density (−0.0007 to −0.0095 m⁻¹).

**Mechanism, result-backed.** `ka` and effective permittivity are identical within a given electromagnetic theory across microstructures (IBA: `ka` 0.0015→0.1700 m⁻¹, ε 1.0014→1.1497; DMRT QCA-CP: `ka` 0.0015→0.1783 m⁻¹, ε 1.0014→1.1523), while `ks` differs strongly. So the divergence is entirely in the scattering term / structure factor, not in absorption or in the dielectric mixing. Correspondingly the single-scattering albedo stays constant at 0.2382 for IND + Rayleigh but falls with density for the dense-medium pairs (0.2366→0.1195 HS QCA-CP; 0.2357→0.1118 HS IBA; 0.2374→0.1666 SHS QCA-CP; 0.2365→0.1559 SHS IBA).

**Frequency diagnostic.** At 96 kg m⁻³ with SHS + IBA, `ks` rises from 4.9 × 10⁻⁵ m⁻¹ at 10 GHz to 0.485 m⁻¹ at 100 GHz: exponent ≈4 in frequency (50→100 GHz ratio 15.8), while `ka` scales as f² (ratio 4.00). Derived from that curve, the 50 GHz level used for Fig. 3 reproduction is roughly 3× the level a 37 GHz run would give (interpolating 0.00398 m⁻¹ at 30 GHz and 0.01257 m⁻¹ at 40 GHz to ≈0.0095 m⁻¹ at 37 GHz) [model:smrt@1.5.1].

## Assumed / chosen parameters
`frequency_ghz` = 50 GHz and `sweep_start` = 1 kg m⁻³ are session assumptions, not paper values: [smrt-v1#07] says comparisons are made at 37 GHz in a semi-infinite medium unless stated otherwise, and [smrt-v1#08] only fixes 100 µm spheres and notes the sparse approximation holds at 10–20 kg m⁻³. `sweep_points` = 25 and the microstructure/theory pairing are resolution and legend-matching choices. `angle_deg`, `thickness_m`, `dort_streams`, `temperature_k`, `corr_length_m` and the fixed `density_kg_m3` = 300 are declared defaults that are inert for a per-unit-length coefficient extraction, or overridden by the sweep.

## Limitations
- The `ks` **level** is not identifiable against Fig. 3: frequency was assumed, and `ks` ∝ f⁴ here, so any absolute comparison with the source figure [smrt-v1#fig-fig03] would attribute an assumed-frequency offset to the physics.
- No digitized paper values exist; the figure was inspected for axis identity and trend only, never read as data, so agreement is qualitative/structural, not point-by-point.
- The 1–100 kg m⁻³ window is mostly *outside* the sparse-medium regime the paper flags as physical (10–20 kg m⁻³), so the upper part tests formulation divergence, not the approximation's validity.
- All comparisons are between formulations **within one registered model** (SMRT 1.5.1, same microstructure inputs, same output); differences are attributable to the selected scattering/microstructure formulations, not to different codes or solvers. `dmrt_qcacp_shortrange` was used at stickiness 0.5, inside its moderate-stickiness requirement [smrt-v1#08], and DORT/solver settings do not enter a coefficient run.

<parameter_provenance>
[{"field":"radius_m","value":"1.0e-4","source_kind":"paper","source_ref":"smrt-v1#08","source_span":"The results for 100 µm radius spheres","reason":"Fig. 3 scatterer size stated in the section text","sensitivity_checked":false},{"field":"output","value":"coefficients","source_kind":"paper","source_ref":"smrt-v1#08","source_span":"the influence of microstructure on deviations from the sparse medium assumption for the scattering coefficient","reason":"Fig. 3 plots ks directly, so the solver stage is bypassed","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"user","source_ref":"user question / approved plan mapping (abscissa of Fig. 3)","reason":"density is Fig. 3's x-axis; declared user_specified in the plan","sensitivity_checked":true},{"field":"sweep_start","value":"1.0","source_kind":"assumption","source_ref":"agent choice; paper states the sparse regime only as 10-20 kg m-3 (smrt-v1#08)","reason":"start the axis close to the origin so the linear trend can be read","sensitivity_checked":false},{"field":"sweep_stop","value":"100.0","source_kind":"paper","source_ref":"smrt-v1#fig-fig03","source_span":"Fig. 3 abscissa: density (kg m-3); ordinate: scattering coefficient (m-1)","reason":"upper axis limit read from the opened figure axis, not quoted numerically in the section text","sensitivity_checked":false},{"field":"sweep_points","value":"25","source_kind":"assumption","source_ref":"agent choice (plan mapping: resolution needed to see the curvature)","reason":"enough points to resolve origin slope and high-density divergence","sensitivity_checked":false},{"field":"frequency_ghz","value":"50.0","source_kind":"assumption","source_ref":"agent choice; smrt-v1#07 says comparisons use 37 GHz unless otherwise stated","reason":"Fig. 3 frequency not stated in the opened section; 50 GHz assumed, so level is not comparable to the figure","sensitivity_checked":true},{"field":"stickiness","value":"0.5 (SHS runs); 0.2 in IND/HS specs, inactive there","source_kind":"user","source_ref":"approved plan mapping (stickiness of the sticky hard sphere curves)","reason":"0.5 keeps dmrt_qcacp_shortrange inside its moderate-stickiness validity; unused by independent/non-sticky spheres","sensitivity_checked":false},{"field":"electromagnetic_model","value":"rayleigh | iba | dmrt_qcacp_shortrange","source_kind":"user","source_ref":"approved plan mapping to the six Fig. 3 legend curves (IND/HS/SHS, solid vs dashed)","reason":"selected to reproduce each plotted curve; legal pairing enforced by the registration (rayleigh only with independent_sphere)","sensitivity_checked":true},{"field":"microstructure_model","value":"independent_sphere | non_sticky_hard_spheres | sticky_hard_spheres","source_kind":"assumption","source_ref":"agent choice matching Fig. 3 legend families (IND, HS, SHS)","reason":"three microstructure families plotted in Fig. 3","sensitivity_checked":true},{"field":"angle_deg","value":"55.0","source_kind":"model_default","source_ref":"registered default in smrt@1.5.1 declaration","reason":"incidence angle does not enter a ks/ka coefficient extraction","sensitivity_checked":false},{"field":"thickness_m","value":"1.0","source_kind":"model_default","source_ref":"registered default; paper uses a semi-infinite medium (smrt-v1#07)","reason":"coefficients are per unit length, so layer thickness is inert here","sensitivity_checked":false},{"field":"density_kg_m3","value":"300.0 (spec default, overridden by the sweep 1-100)","source_kind":"model_default","source_ref":"registered default in smrt@1.5.1 declaration","reason":"fixed value retained in the spec but replaced at every point by sweep_parameter","sensitivity_checked":false},{"field":"temperature_k","value":"265.0","source_kind":"model_default","source_ref":"registered default in smrt@1.5.1 declaration","reason":"affects emission only through the ice permittivity; not part of Fig. 3's coefficient comparison","sensitivity_checked":false},{"field":"corr_length_m","value":"1.5e-4","source_kind":"model_default","source_ref":"registered default in smrt@1.5.1 declaration","reason":"the three sphere microstructures used are defined by radius and stickiness","sensitivity_checked":false},{"field":"dort_streams","value":"32","source_kind":"model_default","source_ref":"registered default; smrt-v1#08 also reports 32 streams for DORT","reason":"radiative-transfer solver setting, not used for a coefficients-only run","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | radius_m | 0.0001 | paper_explicit | smrt-v1#fig03 |
| smrt | output | coefficients | paper_explicit | smrt-v1#fig03 |
| smrt | sweep_parameter | density_kg_m3 | user_specified | smrt-v1#fig03 |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | paper_explicit | smrt-v1#fig03 |
| smrt | sweep_points | 25 | model_assumption | - |
| smrt | frequency_ghz | 50 | model_assumption | - |
| smrt | stickiness | 0.5 | user_specified | smrt-v1#08 |
| smrt | electromagnetic_model | rayleigh | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | iba | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | dmrt_qcacp_shortrange | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | iba | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | dmrt_qcacp_shortrange | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | iba | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | independent_sphere | model_assumption | - |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | thickness_m | 1.0 | backend_default | - |
| smrt | density_kg_m3 | 300.0 | backend_default | - |
| smrt | temperature_k | 265.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
