# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated six-series chart shows increasing scattering coefficient \(k_s\) with density for all formulations. The curves are relatively close at low density and separate progressively toward higher density. The independent-sphere formulations remain closer together, while the hard-sphere and sticky-hard-sphere formulations show stronger divergence. This is a **partial, qualitative reproduction** of the source Figure 3 pattern. [figure:smrt-v1#fig03] [smrt-v1#fig-fig03] [model:smrt@1.5.1]

The generated figure uses density from **1.0 to 100.0 kg m⁻³** on the x-axis and scattering coefficient from the model output in **m⁻¹** on the y-axis. It contains six series and 25 points per series. [model:smrt@1.5.1]

## Source and generated figure

The source comparison concerns six combinations of electromagnetic theory and snow microstructure representation. [smrt-v1#fig-fig03] The generated chart contains:

- independent spheres with Rayleigh;
- independent spheres with IBA;
- non-sticky hard spheres with DMRT QCA-CP;
- non-sticky hard spheres with IBA;
- sticky hard spheres with DMRT QCA-CP;
- sticky hard spheres with IBA.

The source and generated figures support the same qualitative interpretation: convergence or close agreement at lower density followed by increasing separation at higher density. Exact numerical agreement with the source is **not scoreable**, because the recorded workflow did not digitize source-figure values. [figure:smrt-v1#fig03] [research-reporting#00]

## Supporting results

All six planned SMRT runs completed successfully, with 25 density points each and no recorded quality-control problems. The computed \(k_s\) series increased monotonically across the full density range. [model:smrt@1.5.1]

The recorded model-to-model comparison used the independent-sphere Rayleigh series as the reference. RMSE values for the other five series were supplied by the chart calculation as **0.0002, 0.0033, 0.0037, 0.0024, and 0.0013 m⁻¹**, respectively. These quantify differences among model runs, not agreement with the published figure. [model:smrt@1.5.1]

## Assumed parameters

The electromagnetic-theory and microstructure selections were `user_specified`. The remaining provenance is:

- `model_assumption`: output=`coefficients`; frequency=`37.0` GHz; density sweep=`density_kg_m3`; sweep start=`1.0` kg m⁻³; sweep stop=`100.0` kg m⁻³; sweep points=`25`; temperature=`265.0` K; radius=`0.0001` m.
- `backend_default`: angle=`55.0` degrees; thickness=`1.0` m; correlation length=`0.00015` m; stickiness=`0.2`; discrete-ordinates streams=`32`.

These values are configuration provenance, not paper-explicit evidence. [model:smrt@1.5.1]

## Limitations

The runs used SMRT **1.5.1** and the configuration above. Because several inputs were model assumptions or backend defaults, the result does not establish parameter-identical reproduction of the source experiment. It supports qualitative comparison of curve shape, convergence, divergence, and ordering only. [smrt-v1#08] [smrt-v1#09] [research-reporting#00]

## Final conclusion

The generated figure reproduces the source figure’s main qualitative pattern: \(k_s\) increases with density, the six formulations are closer together at low density, and their predictions diverge at higher density. Quantitative agreement with the source is **not identifiable** from the recorded results because no source-curve digitization or direct numerical source comparison was performed. [figure:smrt-v1#fig03] [model:smrt@1.5.1]

<outcome_provenance>
{"figure_id":"Figure 1","source_target":"smrt-v1#fig03","outcome":"partial_qualitative_reproduction","x":{"field":"density_kg_m3","range":[1.0,100.0],"points":25,"unit":"kg m^-3"},"y":{"field":"ks_per_m","unit":"m^-1"},"series_count":6,"model":"smrt@1.5.1","render_check":true,"source_numeric_comparison":"not_scoreable","unavailable_comparisons":[]}
</outcome_provenance>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | electromagnetic_model | series-specific: rayleigh, iba, or dmrt_qcacp_shortrange | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | series-specific: independent_sphere, non_sticky_hard_spheres, or sticky_hard_spheres | user_specified | smrt-v1#fig03 |
| smrt | output | coefficients | model_assumption | - |
| smrt | frequency_ghz | 37.0 | model_assumption | - |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | thickness_m | 1.0 | backend_default | - |
| smrt | density_kg_m3 | 1.0 | model_assumption | - |
| smrt | temperature_k | 265.0 | model_assumption | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | radius_m | 0.0001 | model_assumption | - |
| smrt | stickiness | 0.2 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_parameter | density_kg_m3 | model_assumption | - |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | model_assumption | - |
| smrt | sweep_points | 25 | model_assumption | - |
