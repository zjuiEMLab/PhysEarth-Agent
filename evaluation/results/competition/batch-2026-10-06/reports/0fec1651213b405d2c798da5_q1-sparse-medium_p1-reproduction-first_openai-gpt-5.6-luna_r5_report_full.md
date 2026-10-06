# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The paper’s reported sparse-medium validity range is **10–20 kg m⁻³**. [smrt-v1#08] The recorded results show a density sweep of **1.0–100.0 kg m⁻³**, with **25 points** for each of six configurations. [model:smrt@1.5.1] The generated figure therefore shows convergence at low density and increasing divergence toward higher density, but it does not identify a new validity threshold.

The generated figure is a **partial qualitative reproduction** of Figure 3. The six scattering-coefficient curves have the same qualitative pattern as the source: they are closely grouped at low density and separate as density increases. Sticky hard spheres produce the highest curves, independent spheres are intermediate, and non-sticky hard spheres are lowest. [figure:smrt-v1#fig03] [model:smrt@1.5.1]

## Supporting results

### Source/generated-image conclusion

- Axes: density from **1.0–100.0 kg m⁻³** and scattering coefficient \(k_s\) in **m⁻¹**.
- Series: six curves.
- Pattern: low-density convergence followed by increasing separation.
- Ordering at the high-density end: sticky hard spheres highest, independent spheres intermediate, and non-sticky hard spheres lowest.
- The source figure and generated figure show the same qualitative curve families and ordering. Exact numerical agreement is not scoreable because the source curve values were not digitized. [figure:smrt-v1#fig03]

### Result-backed conclusion

All six planned SMRT runs completed successfully with 25 points and passed the recorded renderability checks. The computed \(k_s\) values increased monotonically with density for every configuration. At **100.0 kg m⁻³**, the recorded endpoint ordering was:

1. DMRT QCA-CP with sticky hard spheres: **0.0189 m⁻¹**
2. IBA with sticky hard spheres: **0.0165 m⁻¹**
3. Rayleigh with independent spheres: **0.0140 m⁻¹**
4. IBA with independent spheres: **0.0134 m⁻¹**
5. DMRT QCA-CP with non-sticky hard spheres: **0.0073 m⁻¹**
6. IBA with non-sticky hard spheres: **0.0064 m⁻¹** [model:smrt@1.5.1]

The recorded model density default was **300.0 kg m⁻³**, but the formal runs used the density sweep **1.0–100.0 kg m⁻³**. Thus, **300.0 kg m⁻³ is not a plotted sweep value**. [model:smrt@1.5.1]

### Figure-to-result comparison

| Aspect | Figure-based reading | Result-backed reading | Assessment |
|---|---|---|---|
| Low-density behavior | Curves converge | All six curves are closely grouped at low density | Same qualitative pattern |
| High-density behavior | Curves diverge | The six \(k_s\) values separate progressively | Same qualitative pattern |
| Ordering | Sticky highest; non-sticky lowest | Same endpoint ordering at 100.0 kg m⁻³ | Agrees |
| Numerical agreement with source | Not digitized | No source-value comparison available | Not scoreable |
| Render status | Six curves are displayed | All six runs completed; render check passed | The check establishes usability, not agreement with the source |

## Guessed/assumed parameters

The following ledger values were not paper-explicit:

- `stickiness = 0.2`
- `angle_deg = 55.0`
- `thickness_m = 1.0`
- `temperature_k = 265.0`
- `sweep_parameter = density_kg_m3`
- `sweep_start = 1.0`
- `sweep_stop = 100.0`
- `sweep_points = 25`

Backend-provided values were:

- `density_kg_m3 = 300.0`
- `corr_length_m = 0.00015`
- `dort_streams = 32`

Paper-explicit configuration values retained in the runs were:

- `radius_m = 0.0001`
- `frequency_ghz = 37`
- `output = coefficients`

The six user-specified theory–microstructure combinations were Rayleigh/independent sphere, IBA/independent sphere, DMRT QCA-CP/non-sticky hard spheres, IBA/non-sticky hard spheres, DMRT QCA-CP/sticky hard spheres, and IBA/sticky hard spheres. [smrt-v1#fig03]

## Limitations

This is a qualitative reproduction rather than an exact numerical reproduction. The source does not provide all execution values used here, including `angle_deg = 55.0`, `thickness_m = 1.0`, `temperature_k = 265.0`, and `stickiness = 0.2`. The model version used was SMRT **1.5.1**, while the paper describes the earlier SMRT implementation. [smrt-v1#02] [model:smrt@1.5.1]

The recorded experiment supports the paper’s **10–20 kg m⁻³** sparse-medium range as a source-reported value, but it does not independently establish that range as a new threshold. [smrt-v1#08]

### Machine-readable outcome

```json
{
  "figure": "Figure 1",
  "source_target": "Figure 3",
  "outcome": "partial_qualitative_reproduction",
  "x": "density_kg_m3",
  "x_range_kg_m3": [1.0, 100.0],
  "x_points": 25,
  "y": "ks_per_m",
  "series": 6,
  "model": "smrt@1.5.1",
  "render_check": true,
  "source_reported_density_range_kg_m3": [10, 20],
  "source_numeric_curve_comparison": "not_scoreable",
  "runs": [
    "rayleigh_ind",
    "iba_ind",
    "dmrt_hs",
    "iba_hs",
    "dmrt_shs",
    "iba_shs"
  ]
}
```

<parameter_provenance>
[{"field":"electromagnetic_model","value":"rayleigh","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"Rayleigh","reason":"Submitted reproduction combination; paper value remains comparison context","sensitivity_checked":false},{"field":"electromagnetic_model","value":"dmrt_qcacp_shortrange","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"DMRT QCA-CP","reason":"Submitted reproduction combination; paper value remains comparison context","sensitivity_checked":false},{"field":"electromagnetic_model","value":"iba","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"IBA","reason":"Submitted reproduction combination; paper value remains comparison context","sensitivity_checked":false},{"field":"microstructure_model","value":"independent_sphere","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"independent spheres","reason":"Submitted reproduction combination; paper value remains comparison context","sensitivity_checked":false},{"field":"microstructure_model","value":"non_sticky_hard_spheres","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"non-sticky hard spheres","reason":"Submitted reproduction combination; paper value remains comparison context","sensitivity_checked":false},{"field":"microstructure_model","value":"sticky_hard_spheres","source_kind":"user","source_ref":"smrt-v1#fig03","source_span":"sticky hard spheres","reason":"Submitted reproduction combination; paper value remains comparison context","sensitivity_checked":false},{"field":"radius_m","value":"0.0001","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"sphere radius is 100 micrometres","reason":"Caption-stated sphere radius","sensitivity_checked":false},{"field":"frequency_ghz","value":"37","source_kind":"paper","source_ref":"smrt-v1#07","source_span":"single configuration at 37 GHz","reason":"Paper-wide comparison condition","sensitivity_checked":false},{"field":"stickiness","value":"0.2","source_kind":"assumption","source_ref":"none","source_span":"not stated for Figure 3","reason":"Required implementation input; registered default retained","sensitivity_checked":false},{"field":"output","value":"coefficients","source_kind":"paper","source_ref":"smrt-v1#fig03","source_span":"scattering coefficient","reason":"Figure target is ks_per_m","sensitivity_checked":false},{"field":"angle_deg","value":"55.0","source_kind":"assumption","source_ref":"none","source_span":"not specified","reason":"Retained submitted run value without paper evidence","sensitivity_checked":false},{"field":"thickness_m","value":"1.0","source_kind":"assumption","source_ref":"none","source_span":"not specified","reason":"Retained submitted run value without paper evidence","sensitivity_checked":false},{"field":"density_kg_m3","value":"300.0","source_kind":"model_default","source_ref":"none","source_span":"not specified","reason":"Inserted during registered-model parameter resolution","sensitivity_checked":false},{"field":"temperature_k","value":"265.0","source_kind":"assumption","source_ref":"none","source_span":"not specified","reason":"Retained submitted run value without paper evidence","sensitivity_checked":false},{"field":"corr_length_m","value":"0.00015","source_kind":"model_default","source_ref":"none","source_span":"not specified","reason":"Inserted as registered-model default","sensitivity_checked":false},{"field":"dort_streams","value":"32","source_kind":"model_default","source_ref":"none","source_span":"not specified","reason":"Inserted as registered-model default","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"assumption","source_ref":"none","source_span":"not specified","reason":"Selected to reproduce the density-dependent figure","sensitivity_checked":false},{"field":"sweep_start","value":"1.0","source_kind":"assumption","source_ref":"none","source_span":"not specified","reason":"Retained submitted sweep range","sensitivity_checked":false},{"field":"sweep_stop","value":"100.0","source_kind":"assumption","source_ref":"none","source_span":"not specified","reason":"Retained submitted sweep range","sensitivity_checked":false},{"field":"sweep_points","value":"25","source_kind":"assumption","source_ref":"none","source_span":"not specified","reason":"Retained submitted sweep resolution","sensitivity_checked":false}]
</parameter_provenance>
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
| smrt | frequency_ghz | 37 | paper_explicit | smrt-v1#07 |
| smrt | stickiness | 0.2 | model_assumption | - |
| smrt | output | coefficients | paper_explicit | smrt-v1#fig03 |
| smrt | angle_deg | 55.0 | model_assumption | - |
| smrt | thickness_m | 1.0 | model_assumption | - |
| smrt | density_kg_m3 | 300.0 | backend_default | - |
| smrt | temperature_k | 265.0 | model_assumption | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_parameter | density_kg_m3 | model_assumption | - |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | model_assumption | - |
| smrt | sweep_points | 25 | model_assumption | - |
