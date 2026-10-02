# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated six-curve reproduction shows the same qualitative behavior as the source Figure 3: the scattering-coefficient curves converge at low snow density and diverge progressively as density increases. At the upper end of the sweep, the sticky-hard-sphere formulations are highest and the non-sticky-hard-sphere formulations are lowest. The result is therefore a **qualitative reproduction**, while exact point-by-point numerical agreement is not identifiable from the available source figure. [figure:smrt-v1#fig03] [smrt-v1#fig-fig03]

The curves were generated with SMRT v1.5.1 for density **1.0–100.0 kg m\(^{-3}\)** using **25 points**. The plotted quantity is the scattering coefficient \(k_s\), in **m\(^{-1}\)**. [model:smrt@1.5.1]

## Source and generated figure

The figure contains six series:

- independent spheres with Rayleigh;
- independent spheres with IBA;
- non-sticky hard spheres with DMRT-QCA-CP;
- non-sticky hard spheres with IBA;
- sticky hard spheres with DMRT-QCA-CP;
- sticky hard spheres with IBA.

The axes are density in kg m\(^{-3}\) and scattering coefficient in m\(^{-1}\). The visible pattern is near-convergence at low density followed by increasing separation toward 100.0 kg m\(^{-3}\). [figure:smrt-v1#fig03]

## Computed results

The actual model arrays support the following endpoint results:

| Configuration | \(k_s\) at 1.0 kg m\(^{-3}\) | \(k_s\) at 100.0 kg m\(^{-3}\) |
|---|---:|---:|
| Independent spheres + Rayleigh | 0.00013980647568598967 m\(^{-1}\) | 0.013980647568598967 m\(^{-1}\) |
| Independent spheres + IBA | 0.00013942584889482432 m\(^{-1}\) | 0.013427634533094483 m\(^{-1}\) |
| Non-sticky hard spheres + DMRT-QCA-CP | 0.00013888028002194273 m\(^{-1}\) | 0.007254801199743284 m\(^{-1}\) |
| Non-sticky hard spheres + IBA | 0.00013837141449503308 m\(^{-1}\) | 0.0064179512352543905 m\(^{-1}\) |
| Sticky hard spheres + DMRT-QCA-CP | 0.00014040204052898344 m\(^{-1}\) | 0.01885283914637513 m\(^{-1}\) |
| Sticky hard spheres + IBA | 0.00013987542281689467 m\(^{-1}\) | 0.01654376886623223 m\(^{-1}\) |

Thus, the curves are tightly grouped near **0.00014 m\(^{-1}\)** at 1.0 kg m\(^{-3}\), but span **0.0064179512352543905–0.01885283914637513 m\(^{-1}\)** at 100.0 kg m\(^{-3}\). [model:smrt@1.5.1]

The recorded comparisons among generated curves supplied these statistics relative to independent-sphere Rayleigh:

- independent-sphere IBA: RMSE **0.0002 m\(^{-1}\)**; \(r=0.9999\);
- non-sticky-hard-sphere DMRT-QCA-CP: RMSE **0.0033 m\(^{-1}\)**; \(r=0.9784\);
- sticky-hard-sphere DMRT-QCA-CP: RMSE **0.0024 m\(^{-1}\)**; \(r=0.9984\). [model:smrt@1.5.1]

These are model-to-model comparisons, not errors against digitized values from the paper.

## Figure-to-result comparison

| Feature | Figure-based conclusion | Result-based conclusion | Assessment |
|---|---|---|---|
| Low-density behavior | Six curves nearly converge | All six values are close to 0.00014 m\(^{-1}\) at 1.0 kg m\(^{-3}\) | Same qualitative pattern |
| Increasing density | Curves separate progressively | Endpoint spread increases to 0.01243588791112074 m\(^{-1}\) between the lowest and highest curves | Consistent |
| High-density ordering | Sticky-hard-sphere curves are highest; non-sticky-hard-sphere curves are lowest | Sticky-hard-sphere DMRT-QCA-CP is highest and non-sticky-hard-sphere IBA is lowest at 100.0 kg m\(^{-3}\) | Consistent |
| Exact numerical agreement | Not readable as source data | No digitized source series are available | Not scoreable |

The generated results support the same scientific pattern as the source figure. The numerical values should not be treated as an exact reproduction because frequency was inferred and several other inputs were inserted as defaults or assumptions.

## Assumed parameters

The following values retain their recorded provenance:

- **paper_explicit:** `radius_m = 0.0001`
- **paper_inferred:** `frequency_ghz = 37`
- **backend_default:** `density_kg_m3 = sweep 1–100, 25 points`; `angle_deg = 55.0`; `thickness_m = 1.0`; `temperature_k = 265.0`; `corr_length_m = 0.00015`; `dort_streams = 32`
- **model_assumption:** `stickiness = 0.2`; `output = coefficients`; `sweep_parameter = density_kg_m3`; `sweep_start = 1.0`; `sweep_stop = 100.0`; `sweep_points = 25`
- **user_specified:** the six electromagnetic-theory and microstructure combinations

The paper evidence identifies the relevant Figure 3 combinations and the sphere radius, but it does not provide every execution parameter needed for exact numerical replication. [smrt-v1#07] [smrt-v1#08]

## Limitations

The reproduction contains all six requested curves and establishes qualitative convergence and divergence over **1.0–100.0 kg m\(^{-3}\)**. Exact source-to-model differences are **not scoreable** because the source curve values were not digitized and the paper does not fully specify the submitted configuration.

**Final outcome: partial reproduction—qualitatively successful, quantitatively unverified.**

<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | electromagnetic_model | rayleigh | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | dmrt_qcacp_shortrange | user_specified | smrt-v1#fig03 |
| smrt | electromagnetic_model | iba | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | independent_sphere | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | non_sticky_hard_spheres | user_specified | smrt-v1#fig03 |
| smrt | microstructure_model | sticky_hard_spheres | user_specified | smrt-v1#fig03 |
| smrt | radius_m | 0.0001 | paper_explicit | smrt-v1#fig03 |
| smrt | frequency_ghz | 37 | paper_inferred | smrt-v1#07 |
| smrt | density_kg_m3 | sweep 1–100, 25 points | backend_default | smrt-v1#fig03 |
| smrt | stickiness | 0.2 | model_assumption | smrt-v1#08 |
| smrt | output | coefficients | model_assumption | - |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | thickness_m | 1.0 | backend_default | - |
| smrt | temperature_k | 265.0 | backend_default | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_parameter | density_kg_m3 | model_assumption | - |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | model_assumption | - |
| smrt | sweep_points | 25 | model_assumption | - |
