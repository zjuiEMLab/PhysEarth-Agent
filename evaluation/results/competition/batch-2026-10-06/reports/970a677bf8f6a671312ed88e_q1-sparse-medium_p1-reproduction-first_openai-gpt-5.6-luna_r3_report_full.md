# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The paper reports that the sparse-medium approximation is valid only for **10–20 kg m⁻³**. [smrt-v1#08] The recorded experiment evaluates density from **1–100 kg m⁻³**. [model:smrt@1.5.1]

The generated figure shows six scattering-coefficient curves converging at low density and separating progressively as density increases. The non-sticky hard-sphere curves are lowest, the independent-sphere curves are intermediate, and the sticky-hard-sphere curves are highest. The exact density at which separation becomes visibly distinct is **not identifiable as a single threshold** from the recorded results. [smrt-v1#fig-fig03] [model:smrt@1.5.1]

## Supporting results

### Source-figure conclusion

The opened source figure contains the six theory–microstructure combinations reproduced in the experiment: Rayleigh, DMRT QCA-CP, and IBA applied to independent spheres, non-sticky hard spheres, and sticky hard spheres. [smrt-v1#fig03] [smrt-v1#fig-fig03]

Its relevant qualitative conclusion is that the curves share a low-density convergence pattern but diverge as density increases. The paper’s stated **10–20 kg m⁻³** range is a sparse-medium validity range, not a reported numerical threshold for curve separation. [smrt-v1#08]

### Generated-result conclusion

The six approved SMRT runs each contain **40 points** over `density_kg_m3 = 1–100`, with `ks_per_m` as the plotted output. The recorded arrays show increasing scattering coefficient with density for all six configurations. [model:smrt@1.5.1]

The generated figure therefore supports:

- convergence at low density;
- increasing separation with density;
- lower values for non-sticky hard spheres;
- higher values for sticky hard spheres;
- intermediate values for the independent-sphere cases.

The recorded results do not supply a uniquely calculated onset density for visible separation, and the source curves were not digitized. Numerical source-to-model bias, RMSE, and percent error are therefore **not scoreable**.

| Quantity | Result |
|---|---|
| Paper-reported sparse-medium range | **10–20 kg m⁻³** [smrt-v1#08] |
| Recorded model density range | **1–100 kg m⁻³** [model:smrt@1.5.1] |
| Exact separation threshold | **Not identifiable** |
| Numerical point-by-point source comparison | **Not scoreable** |
| Qualitative reproduction | Same convergence-to-divergence pattern and ordering |

The source-based and array-based conclusions agree qualitatively. The main qualification is that the paper’s 10–20 kg m⁻³ range describes sparse-medium validity, whereas the generated figure shows the full modeled progression through 100 kg m⁻³.

## Assumed parameters

The following provenance labels use the plan ledger’s normalized classes: `derived`, `assumption`, and `model_default`.

The following ledger values were not paper-explicit for Figure 3:

- `sweep_parameter = density_kg_m3` — **derived**; the source axis spans 0–100 kg m⁻³.
- `sweep_start = 1` — **assumption**; the legal model range excludes zero.
- `sweep_points = 40` — **assumption**; the paper does not state the point count.
- `stickiness = 0.2` — **assumption**; no Figure 3 value was specified.
- `temperature_k = 265` — **assumption**.
- `angle_deg = 55` — **assumption**.
- `thickness_m = 1.0` — **assumption**.
- `microstructure_model = independent_sphere` — **assumption** in the retained configuration.
- `output = coefficients` — **assumption**.
- `density_kg_m3 = 300.0` — **model_default**.
- `corr_length_m = 0.00015` — **model_default**.
- `dort_streams = 32` — **model_default**.

The following values were paper-explicit or user-specified in the plan ledger:

- `radius_m = 0.0001` — **paper**; the source figure specifies a 100-micrometre sphere radius.
- `sweep_stop = 100` — **paper**.
- `frequency_ghz = 37` — **paper**.
- `electromagnetic_model = rayleigh`, `dmrt_qcacp_shortrange`, and `iba` — **user** alternatives corresponding to Rayleigh, DMRT QCA-CP, and IBA.

[smrt-v1#fig03] [smrt-v1#08] [model:smrt@1.5.1]

## Limitations

- The paper’s **10–20 kg m⁻³** statement is not a computed separation threshold.
- Zero density appears on the source axis but was not modeled; the legal recorded sweep begins at **1 kg m⁻³**.
- The source figure was not digitized, so numerical agreement with the source cannot be quantified.
- Several configuration values were assumptions or model defaults, especially stickiness, temperature, angle, thickness, correlation length, stream count, and output configuration.
- The result is limited to the registered SMRT configuration and its homogeneous snow-model formulation. [smrt-v1#02] [smrt-v1#03]

## Final conclusion

The paper identifies **10–20 kg m⁻³** as the sparse-medium validity range, while the recorded experiment spans **1–100 kg m⁻³**. Within that modeled range, the generated figure reproduces the source’s qualitative pattern: low-density convergence followed by density-dependent divergence and microstructure-dependent ordering. A unique density threshold for visible separation is not available from the recorded results. [smrt-v1#08] [smrt-v1#fig-fig03] [model:smrt@1.5.1]

<parameter_provenance>
[{"field":"electromagnetic_model","value":"rayleigh","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"Rayleigh theory series","reason":"One of the three requested electromagnetic theories","sensitivity_checked":false},{"field":"electromagnetic_model","value":"dmrt_qcacp_shortrange","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"DMRT QCA-CP theory series","reason":"One of the three requested electromagnetic theories","sensitivity_checked":false},{"field":"electromagnetic_model","value":"iba","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"IBA theory series","reason":"One of the three requested electromagnetic theories","sensitivity_checked":false},{"field":"radius_m","value":"0.0001","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"sphere radius 100 micrometres","reason":"Matches the source-figure sphere radius","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"derived","source_ref":"smrt-v1#fig03","source_span":"figure density axis 0–100 kg m^-3","reason":"Uses the source figure’s horizontal quantity","sensitivity_checked":false},{"field":"sweep_start","value":"1","source_kind":"assumption","source_ref":"smrt-v1#fig03","source_span":"source axis begins at 0 kg m^-3","reason":"Uses the legal registered lower bound because zero is unavailable","sensitivity_checked":false},{"field":"sweep_stop","value":"100","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"source axis ends at 100 kg m^-3","reason":"Matches the source-figure upper density limit","sensitivity_checked":false},{"field":"sweep_points","value":"40","source_kind":"assumption","source_ref":"none","source_span":"not stated in the paper","reason":"Provides the recorded density resolution","sensitivity_checked":false},{"field":"frequency_ghz","value":"37","source_kind":"paper","source_ref":"smrt-v1#08","source_span":"comparisons use 37 GHz","reason":"Matches the paper comparison frequency","sensitivity_checked":false},{"field":"stickiness","value":"0.2","source_kind":"assumption","source_ref":"none","source_span":"not stated for Figure 3","reason":"Retains the registered value for sticky-hard-sphere runs","sensitivity_checked":false},{"field":"temperature_k","value":"265","source_kind":"assumption","source_ref":"none","source_span":"not stated for Figure 3","reason":"Retains the registered value","sensitivity_checked":false},{"field":"angle_deg","value":"55","source_kind":"assumption","source_ref":"none","source_span":"not relevant to coefficient output and not stated","reason":"Retains the registered value","sensitivity_checked":false},{"field":"thickness_m","value":"1.0","source_kind":"assumption","source_ref":"none","source_span":"not relevant to coefficient output and not stated","reason":"Retains the registered value","sensitivity_checked":false},{"field":"microstructure_model","value":"independent_sphere","source_kind":"assumption","source_ref":"none","source_span":"not attached to paper or user evidence","reason":"Retains the recorded independent-sphere configuration","sensitivity_checked":false},{"field":"output","value":"coefficients","source_kind":"assumption","source_ref":"none","source_span":"not attached to paper or user evidence","reason":"Provides the scattering coefficient output","sensitivity_checked":false},{"field":"density_kg_m3","value":"300.0","source_kind":"model_default","source_ref":"none","source_span":"inserted during parameter resolution","reason":"Recorded backend default outside the swept density axis","sensitivity_checked":false},{"field":"corr_length_m","value":"0.00015","source_kind":"model_default","source_ref":"none","source_span":"inserted during parameter resolution","reason":"Recorded backend default","sensitivity_checked":false},{"field":"dort_streams","value":"32","source_kind":"model_default","source_ref":"none","source_span":"inserted during parameter resolution","reason":"Recorded backend default","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>reproduced</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | electromagnetic_model | rayleigh | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | dmrt_qcacp_shortrange | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | iba | user_specified | smrt-v1#fig03 |
| smrt | radius_m | 0.0001 | paper_explicit | smrt-v1#fig03 |
| smrt | sweep_parameter | density_kg_m3 | paper_inferred | smrt-v1#fig03 |
| smrt | sweep_start | 1 | model_assumption | smrt-v1#fig03 |
| smrt | sweep_stop | 100 | paper_explicit | smrt-v1#fig03 |
| smrt | sweep_points | 40 | model_assumption | - |
| smrt | frequency_ghz | 37 | paper_explicit | smrt-v1#08 |
| smrt | stickiness | 0.2 | model_assumption | - |
| smrt | temperature_k | 265 | model_assumption | - |
| smrt | angle_deg | 55 | model_assumption | - |
| smrt | thickness_m | 1.0 | model_assumption | - |
| smrt | microstructure_model | independent_sphere | model_assumption | - |
| smrt | output | coefficients | model_assumption | - |
| smrt | density_kg_m3 | 300.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
