# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

# Reproduction report — SMRT paper Figure 3

## Research result and conclusion

The generated figure (Figure 1, "Scattering coefficient vs density, six theory/microstructure combinations") shows the local `smrt@1.5.1` reproducing the *qualitative pattern* of the SMRT paper's figure 3 [figure:smrt-v1#fig03]: all six theory/microstructure combinations give a scattering coefficient that rises monotonically with bulk density across 1–100 kg m⁻³, and the curves group in the same family ordering. Manual visual review passed the redrawn figure. Because the paper documents **SMRT v1.0** and only the local **v1.5.1** is registered, this is a **partial** reproduction — a qualitative correspondence, not a pointwise numerical match [model:smrt@1.5.1].

## Conclusion supported by the source image

The source figure was opened and inspected as an image [figure:smrt-v1#fig03]. It plots scattering coefficient (m⁻¹) against density (kg m⁻³) for sparse-medium theory/microstructure pairings. The check covers axes, units, legend, series count and grouping: six pairings distinguished by electromagnetic theory and microstructure. The image supports count, axes, units, legend, grouping, ordering and shape; it does not supply digitized values and does not prove numerical agreement.

## Conclusion supported by the actual result handles

Six coefficient runs (r1–r6) returned `ks_per_m` over 1–100 kg m⁻³ at 11 points, all passing quality control [model:smrt@1.5.1]. The arrays show:
- Every series rises monotonically in density.
- At 100 kg m⁻³ the ordering is: DMRT QCA-CP + sticky hard spheres (≈0.019 m⁻¹) highest, then IBA + sticky hard spheres and Rayleigh + independent spheres, then IBA + independent spheres, with the two non-sticky-hard-sphere curves lowest (≈0.006–0.007 m⁻¹).
- The renderer's built-in agreement metrics against the Rayleigh + independent-sphere curve: DMRT+non-sticky (bias −0.0025, r 0.977), IBA+non-sticky (bias −0.0029, r 0.965), DMRT+sticky (bias +0.0019, r 0.998), IBA+sticky (bias +0.0010, r 0.9996), IBA+independent (bias −0.0002, r 0.9999), all in m⁻¹ over the shared 1–100 range.

## Comparison of the two conclusions

| Aspect | Image-based | Result-based | Agreement |
|---|---|---|---|
| Series count | 6 pairings | 6 runs | agree |
| Axes/units | density (kg m⁻³) vs ks (m⁻¹) | `density_kg_m3` vs `ks_per_m` (m⁻¹) | agree |
| Shape | monotonic rise | monotonic rise in all series | agree |
| Ordering | by theory/microstructure family | non-sticky lowest, sticky highest | agree, qualitatively |
| Pointwise values | not available | model values only | not scoreable |

**Agreement:** structure, axes, monotonic shape and family ordering correspond. **Qualification:** the paper values are v1.0 implementation results; the local runs are v1.5.1, so no claim of exact numerical agreement is made, and no curve digitization was performed, so pointwise comparison is **not scoreable**. The unavailable comparison is SMRT v1.0.

## Assumed parameters

The following were not fixed by the paper figure and are assumptions or backend defaults: `sweep_points` = 11 (sampling assumption); `stickiness` = 0.2 (caption states no value; default retained, flagged for review); `frequency_ghz` = 37 (representative, held fixed across series); `temperature_k` = 265, `thickness_m` = 1.0, `angle_deg` = 55.0, `density_kg_m3` = 300.0, `corr_length_m` = 0.00015, `dort_streams` = 32 (all backend defaults). `sweep_start` = 1 is the paper range [0,100] clamped to the declared model minimum of 1.0 kg m⁻³.

## Limitations

- Local SMRT is v1.5.1, not the paper's v1.0; differences may reflect implementation evolution, not physics.
- Values below ~50 kg m⁻³ are the sparse-medium limit and describe the theories, not real snow [model:smrt@1.5.1].
- No curve digitization: exact pointwise reproduction is not assessable.
- A robustness pass (dort_streams convergence, stickiness sensitivity, v1.0 cross-check) would be needed to promote this from partial to reproduced.

<parameter_provenance>
[{"field":"radius_m","value":0.0001,"source_kind":"paper","source_ref":"figure:smrt-v1#fig03","source_span":"sphere radius at 100 micrometres for all sparse-medium curves","reason":"Figure caption fixes the sphere radius","sensitivity_checked":false},
{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"paper","source_ref":"figure:smrt-v1#fig03","source_span":"independent variable is density","reason":"Figure x-axis is density","sensitivity_checked":false},
{"field":"sweep_start","value":1,"source_kind":"paper","source_ref":"figure:smrt-v1#fig03","source_span":"axis starts at 0, clamped to model minimum 1.0","reason":"Lower bound of plotted density range","sensitivity_checked":false},
{"field":"sweep_stop","value":100,"source_kind":"paper","source_ref":"figure:smrt-v1#fig03","source_span":"axis ends at 100 kg m^-3","reason":"Upper bound of plotted density range","sensitivity_checked":false},
{"field":"sweep_points","value":11,"source_kind":"model_default","source_ref":"model_assumption; chosen to resolve the curved portion of the figure","source_span":"","reason":"Sampling assumption, not paper evidence","sensitivity_checked":false},
{"field":"output","value":"coefficients","source_kind":"paper","source_ref":"smrt-v1#08","source_span":"ks_per_m produced by coefficients output mode","reason":"Paper quantity ks maps to coefficients output","sensitivity_checked":false},
{"field":"electromagnetic_model","value":"rayleigh","source_kind":"user","source_ref":"approved plan pairings; paper value IND/Rayleigh remains comparison context","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"microstructure_model","value":"independent_sphere","source_kind":"user","source_ref":"approved plan pairings; paper value IND","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"electromagnetic_model","value":"iba","source_kind":"user","source_ref":"approved plan pairings; paper value IND/IBA","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"microstructure_model","value":"independent_sphere","source_kind":"user","source_ref":"approved plan pairings; paper value IND","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"electromagnetic_model","value":"dmrt_qcacp_shortrange","source_kind":"user","source_ref":"approved plan pairings; paper value HS/DMRT","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"microstructure_model","value":"non_sticky_hard_spheres","source_kind":"user","source_ref":"approved plan pairings; paper value HS","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"electromagnetic_model","value":"iba","source_kind":"user","source_ref":"approved plan pairings; paper value HS/IBA","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"microstructure_model","value":"non_sticky_hard_spheres","source_kind":"user","source_ref":"approved plan pairings; paper value HS","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"electromagnetic_model","value":"dmrt_qcacp_shortrange","source_kind":"user","source_ref":"approved plan pairings; paper value SHS/DMRT","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"microstructure_model","value":"sticky_hard_spheres","source_kind":"user","source_ref":"approved plan pairings; paper value SHS","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"electromagnetic_model","value":"iba","source_kind":"user","source_ref":"approved plan pairings; paper value SHS/IBA","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"microstructure_model","value":"sticky_hard_spheres","source_kind":"user","source_ref":"approved plan pairings; paper value SHS","source_span":"","reason":"Submitted experiment differs from paper condition","sensitivity_checked":false},
{"field":"stickiness","value":0.2,"source_kind":"assumption","source_ref":"figure:smrt-v1#fig03 caption states no stickiness value","source_span":"","reason":"Default retained as assumption, flagged for review","sensitivity_checked":false},
{"field":"frequency_ghz","value":37,"source_kind":"assumption","source_ref":"figure:smrt-v1#fig03 states no frequency","source_span":"","reason":"Representative microwave frequency held fixed across all series","sensitivity_checked":false},
{"field":"temperature_k","value":265,"source_kind":"backend_default","source_ref":"none","source_span":"","reason":"Registered backend default; ks is intensive in temperature","sensitivity_checked":false},
{"field":"thickness_m","value":1.0,"source_kind":"backend_default","source_ref":"none","source_span":"","reason":"Registered backend default; coefficients output is a layer property","sensitivity_checked":false},
{"field":"angle_deg","value":55.0,"source_kind":"backend_default","source_ref":"none","source_span":"","reason":"Registered backend default; coefficients output does not use geometry","sensitivity_checked":false},
{"field":"density_kg_m3","value":300.0,"source_kind":"backend_default","source_ref":"none","source_span":"","reason":"Registered model default inserted during parameter resolution","sensitivity_checked":false},
{"field":"corr_length_m","value":0.00015,"source_kind":"backend_default","source_ref":"none","source_span":"","reason":"Registered model default; not used by sphere-based microstructures","sensitivity_checked":false},
{"field":"dort_streams","value":32,"source_kind":"backend_default","source_ref":"none","source_span":"","reason":"Registered model default; coefficients output does not require DORT","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
