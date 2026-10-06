# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure shows all seven curves sharing one value at the left end of the sweep and fanning out monotonically to the right, so the convergence at low density and the progressive divergence with density that Fig. 3 depicts are both reproduced [figure:smrt-v1#fig03]. The curve ordering, however, is not: in the reproduced chart the two independent-sphere curves sit at the top of the fan at 100 kg m⁻³, above both sticky-hard-sphere curves, which are in turn above the two hard-sphere curves — whereas the source figure presents the ordering SHS > IND > HS [figure:smrt-v1#fig03]. The pairing the caption itself calls out as tight, independent spheres under IBA against independent spheres under Rayleigh, is reproduced, and the structure-driven spread (non-sticky hardest, sticky intermediate) is reproduced. Every required curve is present and the figure rendered legibly, so this is a **qualitative partial reproduction**: pattern, origin and IND-pair agreement hold; the IND-vs-SHS ordering does not, under this configuration.

On density itself, the quantity the question asks about: the opened paper evidence states that the sparse-medium approximation is valid only at 10–20 kg m⁻³, which the paper calls unrealistic for snow modelling, and fixes 300 kg m⁻³ as the density of the separate Fig. 4 configuration [smrt-v1#08]. The recorded runs sweep 1.0 to 100.0 kg m⁻³, whose upper limit 100.0 kg m⁻³ is Fig. 3's last x-axis tick, and hold 300.0 kg m⁻³ only as the unswept backend default [model:smrt@1.5.1]. So no result here lies inside the 10–20 kg m⁻³ range in which the paper says the independent-sphere approximation is valid, and none reaches 300 kg m⁻³.

## Supporting results

**What the inspected source figure supports.** X axis density in kg m⁻³ with ticks to 100; y axis a logarithmic scattering coefficient in m⁻¹ labelled from 1e-4 up to 1e0; six legend entries crossing IND/HS/SHS with Rayleigh/IBA; all curves converging at the left, rising and separating into a fan at the right, with the SHS group placed above IND and IND above HS; the caption noting that the IBA and Rayleigh curves for IND are very close [figure:smrt-v1#fig03]. The bitmap carries no values and was not digitized, so it supplies count, axes, units, legend, grouping, ordering, shape and visible separation but no numerical target.

**What the result arrays support.** At the swept endpoints, ks rises from 1.398e-4 to 1.398e-2 m⁻¹ for IND + rayleigh, 1.394e-4 to 1.343e-2 for IND + iba, 1.395e-4 to 1.068e-2 for SHS + dmrt (τ 0.5), 1.390e-4 to 9.43e-3 for SHS + iba, 1.389e-4 to 7.25e-3 for HS + dmrt and 1.384e-4 to 6.42e-3 for HS + iba [model:smrt@1.5.1]. The renderer's pair statistics against IND + rayleigh over the shared interval are RMSE 0.0003 (r = 0.9999) for the IND + iba curve, RMSE 0.0015 and 0.0022 for the two SHS curves and 0.0033 and 0.0037 for the two HS curves — that is, the closest pair in the fan is the IND pair, as the source states. Single-scattering albedo at the top of the sweep falls from 0.1460 (IND, constant across the sweep) to 0.0985 (SHS + dmrt) and 0.0691 (HS + dmrt), so the structural change is a genuine change in scattering efficiency rather than in absorption: ka is set by the electromagnetic theory alone (0.0817 rayleigh, 0.0932 iba, 0.0977 dmrt at 100 kg m⁻³) and is identical across the three microstructures within a theory [model:smrt@1.5.1]. The 10 GHz diagnostic falls to 7.46e-5 m⁻¹ at 100 kg m⁻³, 187.4× below its 37 GHz counterpart, i.e. the ν⁴ law of the independent-sphere Rayleigh limit recovered on the computed arrays [model:smrt@1.5.1].

**The two readings compared.**

| Feature | Generated figure (image) | Result arrays | Status |
| --- | --- | --- | --- |
| Common origin at low density | curves meet at the left | six curves within 1.0% of one another at 1.0 kg m⁻³ | reproduced |
| Monotonic rise with density | rising fan | every curve monotonic increasing | reproduced |
| IND IBA ≈ IND Rayleigh | "very close" | RMSE 0.0003, r = 0.9999 | reproduced |
| Structure separates the curves | distinct groups | albedo 0.1460 → 0.0985 → 0.0691 at 100 kg m⁻³ | reproduced |
| Ordering SHS > IND > HS | caption's claim | IND > SHS > HS at 100 kg m⁻³ | **disagreement** |
| Absolute magnitude | axis labelled to 1e0 m⁻¹ | maximum 1.398e-2 m⁻¹ | not scoreable; no digitized values |

The disagreement is qualified by two assumptions rather than resolved by a test. Frequency is not stated for this figure, so the whole fan sits on an assumed 37.0 GHz slice, and the 10 GHz arm shows how far that slice can be moved vertically — by nearly 200× — without changing its shape. Range is the other: with radius fixed at 0.0001 and density the only free structural parameter, the sweep reaches 1.398e-2 m⁻¹ while the source axis is labelled to 1e0 m⁻¹, so the published panel may extend past 100.0 kg m⁻³ or use a different radius, which the extracted image cannot show [figure:smrt-v1#fig03]. Within the computed range the IND curves grow linearly while the SHS curves grow sublinearly, so the IND–SHS gap widens with density instead of closing; both explanations are untested here.

## Assumed parameters

Values below are quoted exactly as recorded; the full parameter-source table is appended to this report. **paper_inferred:** sweep_start = 1.0, against the figure's origin at 0 kg m⁻³, since ks vanishes identically at zero density. **model_assumption:** frequency_ghz = 37.0 for the six main curves and 10.0 for the diagnostic, neither stated for Fig. 3; temperature_k = 265.0, where the paper uses 256 K only for Figs. 4–5 [smrt-v1#08]; electromagnetic_model = rayleigh and microstructure_model = independent_sphere retained as the reference corner of the design; sweep_points = 21. **user_specified:** stickiness = 0.5, named in the conversation — the paper gives τ=0 and 0.5 for Fig. 3 and 0.5 for Fig. 4, so 0.5 is used only on the sticky-hard-sphere arms and this run is a submitted experiment that differs from the paper's own τ-conditioned comparison. **backend_default:** angle_deg = 55.0, thickness_m = 1.0, density_kg_m3 = 300.0, corr_length_m = 0.00015, dort_streams = 32; all five are inert for a coefficients output, which carries no radiative-transfer solution, except density_kg_m3 and corr_length_m, both overridden by the sweep [model:smrt@1.5.1]. Paper-explicit inputs are radius_m = 0.0001, sweep_stop = 100.0, output = coefficients and the swept variable density_kg_m3. No parameter is unrecorded, and at least one — frequency_ghz = 37.0 — is assumed, so this is not a run with nothing guessed.

## Limitations

The ordering inversion is a qualitative claim of the figure that the reproduced curves contradict, and it is reported as such rather than smoothed over; the paper's own statement that the sparse-medium approximation holds only at 10–20 kg m⁻³ means the IND curves at the top of the fan are outside the regime in which that theory is claimed valid [smrt-v1#08]. The entire sweep sits below the declared density floor of the registered model, so these curves diagnose model architecture rather than predict real snow, and each is a single homogeneous layer of one grain size [model:smrt@1.5.1]. Version differences are unquantified: SMRT v1.5.1 derives the sticky and hard-sphere structure factor from density and radius internally, which is a different microstructure mapping from the paper's reference implementation, and no cross-run against that implementation is available here [smrt-v1#05]. Absolute agreement with Fig. 3 is not scoreable because the source bitmap was not digitized. The automatic render check passed (7 series, 21 points each, redrawn in a wider publication layout) and establishes only that the plotted arrays are finite and legible; it is not evidence that the figure matches the source. Of the two charts originally chosen, only fig03_ks_vs_density was in the confirmed package, so the 10 GHz arm appears as the seventh series of that chart rather than in a chart of its own; the declared comparisons list is empty, and the remaining open arms are IBA versus Rayleigh at fixed structure across the two frequencies, and the τ=0 versus τ=0.5 contrast.

Outcome: qualitative partial reproduction — all required curves generated and legible; convergence, monotonic divergence and the tight IND Rayleigh/IBA pairing reproduced; SHS > IND > HS ordering not reproduced under frequency_ghz = 37.0, radius_m = 0.0001, sweep 1.0–100.0 kg m⁻³. Target fig03 status: planned, partial correspondence. Render check: passed (legibility only).

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | radius_m | 0.0001 | paper_explicit | smrt-v1#fig03 |
| smrt | sweep_parameter | density_kg_m3 | paper_explicit | smrt-v1#fig03 |
| smrt | sweep_start | 1.0 | paper_inferred | smrt-v1#fig03 |
| smrt | sweep_stop | 100.0 | paper_explicit | smrt-v1#fig03 |
| smrt | output | coefficients | paper_explicit | smrt-v1#fig03 |
| smrt | frequency_ghz | 37.0 | model_assumption | - |
| smrt | temperature_k | 265.0 | model_assumption | - |
| smrt | stickiness | 0.5 | user_specified | smrt-v1#08 |
| smrt | electromagnetic_model | rayleigh | model_assumption | - |
| smrt | microstructure_model | independent_sphere | model_assumption | - |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | thickness_m | 1.0 | backend_default | - |
| smrt | density_kg_m3 | 300.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_points | 21 | model_assumption | - |
