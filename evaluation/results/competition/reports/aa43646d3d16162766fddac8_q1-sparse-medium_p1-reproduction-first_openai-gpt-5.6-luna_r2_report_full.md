# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 provides a **qualitatively successful reproduction** of the inspected source figure. It contains six scattering-coefficient curves that increase with snow density and separate according to the electromagnetic and microstructure formulations [smrt-v1#fig-fig03].

The six approved SMRT runs completed successfully, and all six \(k_s\) curves increased monotonically over the recorded density sweep from 1 to 100 kg m⁻³ [model:smrt@1.5.1]. Exact numerical agreement with the source is not scoreable because the source curves were not digitized.

## Supporting results

The generated figure contains six 60-point curves with:

- x-axis: density, kg m⁻³;
- y-axis: scattering coefficient, m⁻¹;
- configurations spanning Rayleigh, IBA, and DMRT QCA-CP formulations with independent, non-sticky hard-sphere, and sticky hard-sphere microstructures.

Recorded \(k_s\) values at 100 kg m⁻³ were:

| Configuration | \(k_s\) (m⁻¹) |
|---|---:|
| Independent spheres — Rayleigh | 0.0140 |
| Independent spheres — IBA | 0.0134 |
| Non-sticky hard spheres — DMRT QCA-CP | 0.0073 |
| Non-sticky hard spheres — IBA | 0.0064 |
| Sticky hard spheres — DMRT QCA-CP | 0.0189 |
| Sticky hard spheres — IBA | 0.0165 |

Thus, the curves agree in trend but diverge in magnitude as density increases. The largest recorded endpoint is for sticky hard spheres with DMRT QCA-CP; the smallest is for non-sticky hard spheres with IBA [model:smrt@1.5.1].

## Source-image and result-array conclusions

The inspected source/generated images support the following qualitative conclusions:

- six curves are present;
- density is the independent variable;
- scattering increases toward higher density;
- the model families are visibly separated;
- the curves do not collapse onto a single result [smrt-v1#fig-fig03].

The result arrays independently support:

- monotonic increase of \(k_s\) for all six runs;
- endpoint values ranging from 0.0064 to 0.0189 m⁻¹;
- different magnitudes for different theory–microstructure combinations [model:smrt@1.5.1].

These conclusions agree qualitatively. Point-by-point numerical agreement with the source is **not scoreable**, because no digitized source-data artifact was recorded.

## Assumed parameters

The following ledger values were not paper-explicit and were retained as assumptions or registered backend defaults:

- `sweep_start = 1.0`: `model_assumption`; used as a near-zero-density approximation.
- `sweep_points = 60`: `model_assumption`; no paper value was supplied.
- `stickiness = 0.2`: `backend_default`.
- `frequency_ghz = 37.0`: `backend_default`.
- `temperature_k = 265.0`: `backend_default`.
- `angle_deg = 55.0`: `backend_default`.
- `thickness_m = 1.0`: `backend_default`.
- `dort_streams = 32`: `backend_default`.
- `electromagnetic_model`: `model_assumption` for the submitted configurations.
- `microstructure_model`: `model_assumption` for the submitted configurations.
- `output = coefficients`: `model_assumption`.
- `density_kg_m3 = 300.0`: `backend_default`; this was the resolved fixed input while the plotted density values came from the sweep.
- `corr_length_m = 0.00015`: `backend_default`.

The paper-explicit mappings were:

- `radius_m = 0.0001 m`;
- `sweep_parameter = density_kg_m3`;
- `sweep_stop = 100.0 kg m⁻³` [smrt-v1#08] [smrt-v1#fig-fig03].

## Limitations

The result is a **qualitative reproduction**, not a numerical validation. Bias, RMSE, correlation, percentage error, and point-by-point source agreement are not available. Differences may reflect the assumed sweep resolution, backend defaults, selected theory–microstructure mappings, or the registered SMRT implementation [model:smrt@1.5.1].

<parameter_provenance>
[{"field":"radius_m","value":0.0001,"provenance":"paper_explicit","paper_value":"100 micrometres","evidence":"smrt-v1#08","reason":"The registered input was mapped to the opened paper evidence."},{"field":"sweep_parameter","value":"density_kg_m3","provenance":"paper_explicit","paper_value":"0–100 kg m-3 plotted; density tends to zero","evidence":"smrt-v1#fig03","reason":"The registered input was mapped to the opened paper evidence."},{"field":"sweep_start","value":1.0,"provenance":"model_assumption","paper_value":"near-zero limit","evidence":null,"reason":"The registered input was retained as a model assumption without paper evidence."},{"field":"sweep_stop","value":100.0,"provenance":"paper_explicit","paper_value":"100 kg m-3","evidence":"smrt-v1#fig03","reason":"The registered input was mapped to the opened paper evidence."},{"field":"sweep_points","value":60,"provenance":"model_assumption","paper_value":null,"evidence":null,"reason":"The registered input was retained as a model assumption without paper evidence."},{"field":"stickiness","value":0.2,"provenance":"backend_default","paper_value":null,"evidence":null,"reason":"The registered backend supplied this default; it is not paper evidence."},{"field":"frequency_ghz","value":37.0,"provenance":"backend_default","paper_value":null,"evidence":null,"reason":"The registered backend supplied this default; it is not paper evidence."},{"field":"temperature_k","value":265.0,"provenance":"backend_default","paper_value":null,"evidence":null,"reason":"The registered backend supplied this default; it is not paper evidence."},{"field":"angle_deg","value":55.0,"provenance":"backend_default","paper_value":null,"evidence":null,"reason":"The registered backend supplied this default; it is not paper evidence."},{"field":"thickness_m","value":1.0,"provenance":"backend_default","paper_value":null,"evidence":null,"reason":"The registered backend supplied this default; it is not paper evidence."},{"field":"dort_streams","value":32,"provenance":"backend_default","paper_value":null,"evidence":null,"reason":"The registered backend supplied this default; it is not paper evidence."},{"field":"electromagnetic_model","value":["rayleigh","iba","dmrt_qcacp_shortrange"],"provenance":"model_assumption","paper_value":null,"evidence":null,"reason":"The submitted runs retained these values without attached paper or user evidence."},{"field":"microstructure_model","value":["independent_sphere","non_sticky_hard_spheres","sticky_hard_spheres"],"provenance":"model_assumption","paper_value":null,"evidence":null,"reason":"The submitted runs retained these values without attached paper or user evidence."},{"field":"output","value":"coefficients","provenance":"model_assumption","paper_value":null,"evidence":null,"reason":"The submitted run retained coefficient output for the scattering-coefficient target."},{"field":"density_kg_m3","value":300.0,"provenance":"backend_default","paper_value":null,"evidence":null,"reason":"The registered model inserted this value during parameter resolution; it is not paper evidence."},{"field":"corr_length_m","value":0.00015,"provenance":"backend_default","paper_value":null,"evidence":null,"reason":"The registered model inserted this value during parameter resolution; it is not paper evidence."}]
</parameter_provenance>
<reproduction_outcome>reproduced</reproduction_outcome>
