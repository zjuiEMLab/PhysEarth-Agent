# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

**The density quantity asked for.** The opened paper evidence gives two numbers. The sparse-medium regime Fig. 3 illustrates is described as "valid only for very low densities in the range 10–20 kg m⁻³, which is unrealistic for the goal of snow modeling" [smrt-v1#08]; the paper's separate reference comparison configuration uses a "density of 300 kg m⁻³" with stickiness of τ = 0.5 at a sphere radius of 0.1 mm [smrt-v1#08]. Fig. 3 itself states no density value in its caption; its abscissa is the density axis in kg m⁻³ [smrt-v1#fig-fig03]. The recorded runs swept density over **2–96 kg m⁻³** in 20 points [model:smrt@1.5.1].

**What the generated figure shows.** Figure 1 (chart `chart_fig03`, 6 series, x = density_kg_m3 in kg m⁻³, y = ks_per_m in m⁻¹) reproduces the source figure's central pattern for four of its six curves and contradicts it for two. Reading the generated curves against the opened source figure [smrt-v1#fig-fig03]: both show six curves that converge onto one common near-linear trend as density falls toward the low end of the axis, and both present that convergence as a property of the low-density limit rather than of any one formulation [smrt-v1#08]. Both show the same within-pair separation, with the solid theoretical curve above the dashed IBA curve of the same microstructure, and both place the independent-spheres and non-sticky-hard-spheres pairs at comparable intermediate and low levels. They disagree on the sticky-hard-spheres pair: in the source figure it rises most steeply and ends as the highest group, whereas in the recomputation it falls between the independent-spheres and non-sticky-hard-spheres groups and is sublinear rather than superlinear. Because frequency and radius — the only two conditions recorded as paper values — were held at their reported values and are shared by all six runs, and because the IND and HS curves land on the source figure under exactly that shared configuration, this disagreement is diagnosed as the effect of one unspecified input (stickiness) rather than of the electromagnetic formulations. The reproduction is therefore a successful qualitative reproduction of the convergence, the pairing structure and the IND/HS curves, and an unsuccessful reproduction of the SHS group's position and curvature.

## Conclusion supported by the images

The **source figure** supports: six curves grouped in three microstructure pairs, each pair drawn as a theory curve and its IBA counterpart; a density abscissa in kg m⁻³ and a scattering-coefficient ordinate in m⁻¹ [smrt-v1#fig-fig03]; the labels IND, HS and SHS corresponding to independent spheres, hard spheres and sticky hard spheres [smrt-v1#05]; strong low-density convergence; SHS the steepest and highest group at the top of the axis; IND intermediate and nearly linear; HS the shallowest and lowest; solid curves above dashed within every pair. The **generated figure** supports the same six-curve count, the same axis variables and units, the same pairing structure, the same solid-over-dashed separation inside all three pairs, the same low-density merging of all six curves, and the same intermediate IND / low HS placement. It shows the SHS pair in a different order and with opposite curvature. Neither image supplies digitized curve values, so no agreement in level or slope between the two figures can be established from the images alone, and the automatic render check on `chart_fig03` only establishes that the plotted arrays are finite and legible — it is not a comparison with the source figure.

## Conclusion supported by the recorded results

Values below are `ks_per_m` in m⁻¹ at the two ends of the swept density axis, from the six completed runs (`res_3fb7b59afe33`, `res_d714c929a47e`, `res_e830fecb432b`, `res_d5343af46fef`, `res_b7ba590a340e`, `res_92368edf8bd6`) [model:smrt@1.5.1]:

| Curve | 2 kg m⁻³ | 96 kg m⁻³ | Growth over sweep | Gap to its IBA counterpart |
|---|---|---|---|---|
| Independent spheres, Rayleigh | 0.000280 | 0.013421 | 48× | +3.9% |
| Independent spheres, IBA | 0.000279 | 0.012913 | 46× | — |
| Non-sticky hard spheres, DMRT QCA-CP | 0.000276 | 0.007150 | 26× | +12.5% |
| Non-sticky hard spheres, IBA | 0.000275 | 0.006353 | 23× | — |
| Sticky hard spheres, DMRT QCA-CP (τ = 0.5) | 0.000278 | 0.010385 | 37× | +12.8% |
| Sticky hard spheres, IBA (τ = 0.5) | 0.000277 | 0.009208 | 33× | — |

Derived from these arrays: at the lowest swept density the six values lie within 1.8% of one another, so the convergence is numerical and not merely visual; at 96 kg m⁻³ the IND group exceeds the HS group by a factor of 1.9; the SHS pair sits at 77% of IND Rayleigh and above the HS pair. Within the 10–20 kg m⁻³ sparse-medium window the paper names [smrt-v1#08], microstructure changes κs by more than the choice of theory does, which is the hierarchy the paper asserts between microstructure and formulation deviations [smrt-v1#08].

## Comparison of the two conclusions

| Aspect | Source image | Generated image | Recorded arrays | Verdict |
|---|---|---|---|---|
| Six curves, three pairs, axes and units | present | present | 20 points per run, `ks_per_m` | agreement |
| Low-density convergence | visible | visible | spread ≤1.8% at 2 kg m⁻³ | agreement; matches [smrt-v1#08] |
| Solid above dashed within pairs | visible all three | visible all three | +3.9%, +12.5%, +12.8% at 96 kg m⁻³ | agreement |
| IND level and near-linear slope | intermediate | intermediate | 0.0134 m⁻¹, 48× | same qualitative pattern |
| HS level and shallow slope | lowest | lowest | 0.0072 / 0.0064 m⁻¹ | same qualitative pattern |
| SHS ordering | highest group | between IND and HS | 0.0104 / 0.0092 m⁻¹ | **disagreement** |
| SHS curvature | superlinear | sublinear | 37× and 33× vs IND's 48× | **disagreement** |
| Numeric agreement with the figure | — | — | no digitization performed | not scoreable |

The two disagreements are confined to the one input the paper does not give for Fig. 3: stickiness, recorded in the ledger as `user` with `paper_value = not stated for Fig. 3`, its context taken from the paper's *other* configuration where τ = 0.5 applies [smrt-v1#08]. τ enters only through the SHS structure factor [smrt-v1#05], so an assumed τ of 0.5 can shift and reshape the SHS pair while leaving IND and HS untouched — which is the pattern observed. Qualification: SMRT v1.5.1 is the registered implementation and not the paper's v1.0 release, so a residual version difference is included in whatever mismatch survives after the τ explanation.

For the six runs compared with each other: observable, frequency, incidence angle, medium, radius and all held-fixed defaults are identical, so their differences are attributable to the formulation and microstructure choice — the object of study — except where a formulation requires a parameter the paper leaves unspecified [skill:model-comparison]. One internal diagnostic must not be read as evidence: the IBA runs report an `effective_permittivity` that rises with density to about 1.14 while the Rayleigh runs report 1.0 throughout the sweep, and `ka_per_m` at 96 kg m⁻³ is 0.0785 for Rayleigh against 0.0890 for IBA. That is the two formulations' different treatment of the effective permittivity — IBA computing it with the Polder–van Santen mixing formula [smrt-v1#04], the PVS-based absorption coefficient being the recommended SMRT default [guideline:smrt@1.0] — not independent support for the plotted scattering coefficient.

## Assumed parameters

Parameters were guessed or assumed for this reproduction. Only two entries carry the plan ledger's `paper` class, frequency_ghz = 37 [smrt-v1#07] and radius_m = 0.0001 [smrt-v1#fig-fig03]. `derived`: the observable (output = coefficients, taken from the figure ordinate) and sweep_parameter = density_kg_m3. `assumption`: sweep_start = 2, sweep_stop = 96, sweep_points = 20, and temperature_k = 265, for which the paper states no value for Fig. 3 and which is held identical across the six runs so that it shifts curves together rather than reordering them. `model_default`, inserted by the registered model during parameter resolution and not paper evidence: angle_deg = 55.0, thickness_m = 1.0, density_kg_m3 = 300.0 (overridden by the sweep), corr_length_m = 0.00015 and dort_streams = 32. `user`: the three microstructures, the three electromagnetic theories, and stickiness = 0.5 for the SHS runs.

## Limitations

- The swept window 2–96 kg m⁻³ approaches but does not reach the origin, and does not extend to the 300 kg m⁻³ regime of the paper's reference configuration [smrt-v1#08], so nothing here speaks to dense snow.
- The stickiness Fig. 3 used is not identifiable from the opened evidence, and no τ sensitivity sweep was run under the approved plan; the explanation offered for the SHS disagreement is consistent rather than demonstrated.
- The comparison with the source figure is qualitative by eye; no curve values were digitized from the source image, so no numeric agreement with the figure is scoreable and none is claimed.
- The registered model is SMRT v1.5.1, not the paper's v1.0; a residual implementation-version difference is included in any surviving mismatch.
- κs is returned as a medium property, as the figure's ordinate requires [smrt-v1#fig-fig03]; no radiative-transfer solve was performed, so this report says nothing about brightness temperature or backscatter for these configurations, and the semi-infinite-medium condition is represented by the per-unit-length coefficient rather than by a layered solve.

<parameter_provenance>
[{"field":"output","value":"coefficients","source_kind":"derived","source_ref":"smrt-v1#fig-fig03","source_span":"Scattering coefficient (m^-1)","reason":"the figure ordinate is the scattering coefficient, a medium property, so the coefficients output was requested and no radiative-transfer solve was performed","sensitivity_checked":false}, {"field":"frequency_ghz","value":"37","source_kind":"paper","source_ref":"smrt-v1#07","source_span":"37 GHz","reason":"the paper's default sensor configuration for the validation comparisons unless otherwise stated","sensitivity_checked":false}, {"field":"radius_m","value":"0.0001","source_kind":"paper","source_ref":"smrt-v1#fig-fig03","source_span":"The sphere radius is 100 micrometres.","reason":"radius fixed by the caption of the reproduced figure","sensitivity_checked":false}, {"field":"microstructure_model","value":"independent_sphere","source_kind":"user","source_ref":"smrt-v1#05","source_span":"IND","reason":"microstructure named in the figure legend and requested by the question; the paper value stays comparison context","sensitivity_checked":false}, {"field":"microstructure_model","value":"non_sticky_hard_spheres","source_kind":"user","source_ref":"smrt-v1#05","source_span":"HS","reason":"microstructure named in the figure legend and requested by the question; the paper value stays comparison context","sensitivity_checked":false}, {"field":"microstructure_model","value":"sticky_hard_spheres","source_kind":"user","source_ref":"smrt-v1#05","source_span":"SHS","reason":"microstructure named in the figure legend and requested by the question; the paper value stays comparison context","sensitivity_checked":false}, {"field":"stickiness","value":"0.5","source_kind":"user","source_ref":"smrt-v1#08","source_span":"not stated for Fig. 3","reason":"required by the SHS microstructure but not given for Fig. 3; 0.5 taken from the paper's other comparison configuration, and the most likely cause of the SHS disagreement","sensitivity_checked":false}, {"field":"electromagnetic_model","value":"iba","source_kind":"user","source_ref":"smrt-v1#04","source_span":"IBA","reason":"theory named in the figure legend and requested by the question","sensitivity_checked":false}, {"field":"electromagnetic_model","value":"dmrt_qcacp_shortrange","source_kind":"user","source_ref":"smrt-v1#08","source_span":"DMRT QCA-CP","reason":"theory named in the figure legend and requested by the question","sensitivity_checked":false}, {"field":"electromagnetic_model","value":"rayleigh","source_kind":"user","source_ref":"smrt-v1#08","source_span":"Rayleigh","reason":"theory named in the figure legend and requested by the question","sensitivity_checked":false}, {"field":"sweep_parameter","value":"density_kg_m3","source_kind":"derived","source_ref":"smrt-v1#fig-fig03","source_span":"Density (kg m^3)","reason":"the swept quantity is the figure abscissa","sensitivity_checked":false}, {"field":"sweep_start","value":"2","source_kind":"assumption","source_ref":"smrt-v1#fig-fig03","source_span":"about 0 to 100 kg m^-3, curves spanning roughly 2 to 96","reason":"chosen to match where the plotted curves begin and to approach the low-density limit; kept above the declared minimum","sensitivity_checked":false}, {"field":"sweep_stop","value":"96","source_kind":"assumption","source_ref":"smrt-v1#fig-fig03","source_span":"about 0 to 100 kg m^-3, curves spanning roughly 2 to 96","reason":"upper end of the curves as drawn, below the 100 kg m-3 axis limit","sensitivity_checked":false}, {"field":"sweep_points","value":"20","source_kind":"assumption","source_ref":"smrt-v1#fig-fig03","source_span":"not stated","reason":"sampling chosen to resolve the curvature and the near-origin convergence of six curves","sensitivity_checked":false}, {"field":"temperature_k","value":"265","source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"not stated for Fig. 3","reason":"no temperature given for this figure; held identical across all six runs so it shifts curves together rather than reordering them","sensitivity_checked":false}, {"field":"angle_deg","value":"55.0","source_kind":"model_default","source_ref":"smrt@1.5.1","source_span":"backend default","reason":"inserted by the registered model during parameter resolution; not paper evidence, and irrelevant to ks for an isotropic medium","sensitivity_checked":false}, {"field":"thickness_m","value":"1.0","source_kind":"model_default","source_ref":"smrt@1.5.1","source_span":"backend default","reason":"inserted by the registered model; inert for the coefficients output, which is per unit length","sensitivity_checked":false}, {"field":"density_kg_m3","value":"300.0","source_kind":"model_default","source_ref":"smrt@1.5.1","source_span":"backend default","reason":"registered default, overridden by the sweep on this parameter","sensitivity_checked":false}, {"field":"corr_length_m","value":"0.00015","source_kind":"model_default","source_ref":"smrt@1.5.1","source_span":"backend default","reason":"used by ACF-based microstructures; the sphere-based microstructures run here are set by radius and stickiness","sensitivity_checked":false}, {"field":"dort_streams","value":"32","source_kind":"model_default","source_ref":"smrt@1.5.1","source_span":"backend default","reason":"stream count for the radiative-transfer solve, which the coefficients output does not use","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | output | coefficients | paper_inferred | smrt-v1#fig03 |
| smrt | frequency_ghz | 37 | paper_explicit | smrt-v1#07 |
| smrt | radius_m | 0.0001 | paper_explicit | smrt-v1#fig03 |
| smrt | microstructure_model | independent_sphere | user_specified | smrt-v1#05 |
| smrt | microstructure_model | non_sticky_hard_spheres | user_specified | smrt-v1#05 |
| smrt | microstructure_model | sticky_hard_spheres | user_specified | smrt-v1#05 |
| smrt | stickiness | 0.5 | user_specified | smrt-v1#08 |
| smrt | electromagnetic_model | iba | user_specified | smrt-v1#04 |
| smrt | electromagnetic_model | dmrt_qcacp_shortrange | user_specified | smrt-v1#08 |
| smrt | electromagnetic_model | rayleigh | user_specified | smrt-v1#08 |
| smrt | sweep_parameter | density_kg_m3 | paper_inferred | smrt-v1#fig03 |
| smrt | sweep_start | 2 | model_assumption | smrt-v1#fig03 |
| smrt | sweep_stop | 96 | model_assumption | smrt-v1#fig03 |
| smrt | sweep_points | 20 | model_assumption | smrt-v1#fig03 |
| smrt | temperature_k | 265 | model_assumption | smrt-v1#08 |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | thickness_m | 1.0 | backend_default | - |
| smrt | density_kg_m3 | 300.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
