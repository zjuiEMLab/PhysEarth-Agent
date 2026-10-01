# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 shows the same qualitative pattern as the source comparison: the six scattering-coefficient curves converge at low density and diverge progressively toward higher density. All curves increase with density, while the microstructure choices produce the clearest separation. The qualitative reproduction is therefore successful. [figure:smrt-v1#fig03] [model:smrt@1.5.1]

The curves are not identical numerically. Independent-sphere formulations remain relatively close, non-sticky hard-sphere results lie lower at high density, and sticky-hard-sphere results lie higher. The figure supports this ordering and separation, but it does not provide digitized paper values or establish exact numerical agreement.

## Supporting results

### Conclusion supported by the generated image

Figure 1 contains six series with density from **1 to 100 kg m⁻³** on the x-axis and scattering coefficient from **m⁻¹** on the y-axis. The reviewed image confirms:

- six required curves are present;
- all curves increase with density;
- curves are close at low density;
- separation becomes visible at higher density;
- sticky and non-sticky hard-sphere groups depart from the independent-sphere group.

The figure review passed, so the qualitative convergence/divergence and ordering pattern is reproduced. [figure:smrt-v1#fig03]

### Conclusion supported by result handles and arrays

The recorded model outputs confirm that every curve is monotonically increasing in \(k_s\). At density 100 kg m⁻³, the recorded values were:

| Configuration | \(k_s\) (m⁻¹) |
|---|---:|
| Rayleigh + independent spheres | 0.01398 |
| IBA + independent spheres | 0.01343 |
| DMRT QCA-CP + non-sticky hard spheres | 0.00725 |
| IBA + non-sticky hard spheres | 0.00642 |
| DMRT QCA-CP + sticky hard spheres | 0.01885 |
| IBA + sticky hard spheres | 0.01654 |

[model:smrt@1.5.1]

The recorded chart calculations supplied these pairwise comparisons against Rayleigh plus independent spheres: IBA plus independent spheres had RMSE **0.0002 m⁻¹** and \(r=0.9999\); IBA plus non-sticky hard spheres had RMSE **0.0037 m⁻¹** and \(r=0.9689\); DMRT QCA-CP plus non-sticky hard spheres had RMSE **0.0032 m⁻¹** and \(r=0.9792\); DMRT QCA-CP plus sticky hard spheres had RMSE **0.0024 m⁻¹** and \(r=0.9985\); and IBA plus sticky hard spheres had RMSE **0.0013 m⁻¹** and \(r=0.9996\). [model:smrt@1.5.1]

### Image–array comparison

| Aspect | Generated image | Result arrays | Assessment |
|---|---|---|---|
| Number of curves | Six | Six approved sweep runs | Agreement |
| Axes and units | Density in kg m⁻³; \(k_s\) in m⁻¹ | Same recorded axis and output | Agreement |
| Low-density behavior | Curves converge | Similar low-density values | Agreement |
| High-density behavior | Curves separate and reorder by formulation | Recorded endpoint values show the same separation | Agreement |
| Exact paper values | Not digitized | Not scoreable against paper values | Qualification |

The visual review establishes qualitative correspondence; the numerical statistics compare the model curves with one another, not directly with digitized paper data.

## Assumed parameters

The following values were not paper-explicit in the recorded ledger and are therefore treated as guessed, assumed, or backend-supplied:

- **Angle:** 55°, model assumption.
- **Layer thickness:** 1.0 m, model assumption.
- **Temperature:** 265 K, model assumption.
- **Stickiness:** 0.2 for sticky-hard-sphere runs, model assumption; 1000 for the non-sticky-hard-sphere representation in the executed runs.
- **DORT streams:** 32, model assumption.
- **Correlation length:** 0.00015 m, backend default.
- **Sweep start and stop:** 1 and 100 kg m⁻³, model assumptions in the ledger.
- **Baseline sweep parameter:** none, and baseline sweep points: 10, backend defaults. The six formal comparison runs instead used density as the sweep parameter with 60 points.
- **Electromagnetic theory and microstructure choices:** user-specified experiment configurations. The paper’s Rayleigh, IBA, and DMRT QCA-CP formulations and its independent-, non-sticky-hard-sphere, and sticky-hard-sphere representations remain comparison context rather than being treated as a single paper-explicit parameter value.

## Limitations

The result is a successful qualitative reproduction, not an exact numerical reproduction. The source figure was visually inspected but not digitized, so direct paper-to-model numerical error is not scoreable. The experiment also retained several assumed or backend-default parameters, and the formal runs used the registered SMRT implementation and its legal parameterization. [smrt-v1#05] [figure:smrt-v1#fig03]

<parameter_provenance>
[{"field":"electromagnetic_model","value":{"baseline":"iba","rayleigh_ind":"rayleigh","iba_ind":"iba","dmrt_hs":"dmrt_qcacp_shortrange","iba_hs":"iba","dmrt_shs":"dmrt_qcacp_shortrange","iba_shs":"iba"},"source_kind":"user","source_ref":"smrt-v1#fig03; submitted experiment differs from paper condition","reason":"User-specified theory configurations across the existing six comparison runs","sensitivity_checked":false},{"field":"microstructure_model","value":{"baseline":"independent_sphere","rayleigh_ind":"independent_sphere","iba_ind":"independent_sphere","dmrt_hs":"non_sticky_hard_spheres","iba_hs":"non_sticky_hard_spheres","dmrt_shs":"sticky_hard_spheres","iba_shs":"sticky_hard_spheres"},"source_kind":"user","source_ref":"smrt-v1#05; submitted experiment differs from paper condition","reason":"User-specified microstructure configurations across the existing six comparison runs","sensitivity_checked":false},{"field":"output","value":"coefficients","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"y-axis is scattering coefficient","reason":"Paper condition mapped to the registered model input","sensitivity_checked":false},{"field":"frequency_ghz","value":37.0,"source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"common 37 GHz comparison context","reason":"Paper condition mapped to the registered model input","sensitivity_checked":false},{"field":"angle_deg","value":55.0,"source_kind":"assumption","source_ref":"approved run specification; no attached paper or user evidence","reason":"Retained model assumption","sensitivity_checked":false},{"field":"thickness_m","value":1.0,"source_kind":"assumption","source_ref":"approved run specification; no attached paper or user evidence","reason":"Retained model assumption","sensitivity_checked":false},{"field":"density_kg_m3","value":{"baseline":1.0,"formal_sweeps":{"start":1.0,"stop":100.0,"points":60}},"source_kind":"user","source_ref":"approved run specification and recorded formal sweep","source_span":"density sweep from 1 to 100 kg m-3","reason":"Controlled density variable in the approved experiment","sensitivity_checked":false},{"field":"temperature_k","value":265.0,"source_kind":"assumption","source_ref":"approved run specification; no attached paper or user evidence","reason":"Retained model assumption","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Backend-inserted default; not paper evidence","sensitivity_checked":false},{"field":"radius_m","value":0.0001,"source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"figure caption specifies the sphere radius","reason":"Paper-inferred model mapping","sensitivity_checked":false},{"field":"stickiness","value":{"baseline":0.2,"dmrt_shs":0.2,"iba_shs":0.2,"dmrt_hs":1000.0,"iba_hs":1000.0},"source_kind":"assumption","source_ref":"approved run specification and registered non-sticky-limit representation","reason":"Model-assumed sticky and non-sticky parameterization","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"assumption","source_ref":"approved run specification; no attached paper or user evidence","reason":"Retained numerical-resolution assumption","sensitivity_checked":false},{"field":"sweep_parameter","value":{"baseline":"none","formal_sweeps":"density_kg_m3"},"source_kind":"model_default","source_ref":"registered model resolution and approved run specification","reason":"Baseline retained the backend default; formal runs used the approved density sweep","sensitivity_checked":false},{"field":"sweep_points","value":{"baseline":10,"formal_sweeps":60},"source_kind":"model_default","source_ref":"registered model resolution and approved run specification","reason":"Baseline and formal sweep resolutions recorded in the run state","sensitivity_checked":false},{"field":"sweep_start","value":{"baseline":null,"formal_sweeps":1.0},"source_kind":"assumption","source_ref":"approved run specification; no attached paper or user evidence","reason":"Retained formal sweep lower bound","sensitivity_checked":false},{"field":"sweep_stop","value":{"baseline":null,"formal_sweeps":100.0},"source_kind":"assumption","source_ref":"approved run specification; no attached paper or user evidence","reason":"Retained formal sweep upper bound","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>reproduced</reproduction_outcome>
