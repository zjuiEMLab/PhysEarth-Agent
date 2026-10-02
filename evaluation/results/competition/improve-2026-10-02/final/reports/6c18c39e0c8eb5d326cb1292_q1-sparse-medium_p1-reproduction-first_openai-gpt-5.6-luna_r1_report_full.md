# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 reproduces the source comparison qualitatively: all six scattering-coefficient curves increase with density, while the formulation and microstructure choices produce distinct curve groupings. The independent-sphere curves remain close; non-sticky hard spheres give the lowest values at high density, and sticky hard spheres give the highest. [smrt-v1#fig03] [model:smrt@1.5.1]

The reproduction is therefore **qualitatively successful**. Quantitative agreement with the published curves is **not scoreable**, because the source image was not digitized and no source-value error calculation was recorded.

### Supporting results

The generated chart contains six 40-point series for scattering coefficient \(k_s\), with density swept from **1.0 to 100.0 kg m⁻³**:

- Rayleigh, independent spheres
- IBA, independent spheres
- DMRT-QCA-CP, non-sticky hard spheres
- IBA, non-sticky hard spheres
- DMRT-QCA-CP, sticky hard spheres
- IBA, sticky hard spheres

The plotted axes are density in kg m⁻³ and scattering coefficient in m⁻¹. All six model runs completed successfully and passed the recorded model checks. [model:smrt@1.5.1]

At **100.0 kg m⁻³**, the recorded scattering coefficients were:

| Formulation and microstructure | \(k_s\) (m⁻¹) |
|---|---:|
| Rayleigh, independent spheres | 0.0140 |
| IBA, independent spheres | 0.0134 |
| DMRT-QCA-CP, non-sticky hard spheres | 0.0073 |
| IBA, non-sticky hard spheres | 0.0064 |
| DMRT-QCA-CP, sticky hard spheres | 0.0189 |
| IBA, sticky hard spheres | 0.0165 |

These are computed SMRT outputs, not measurements. [model:smrt@1.5.1]

The recorded chart comparison calculated inter-run RMSE values against the Rayleigh independent-sphere series of **0.0003, 0.0032, 0.0037, 0.0024, and 0.0013 m⁻¹** for the other five curves. These values compare model runs with one another; they do not measure agreement with the paper. [model:smrt@1.5.1]

### Source-figure and generated-result comparison

| Feature | Source/generated image | Executed results | Assessment |
|---|---|---|---|
| Number of curves | Six comparison curves | Six curves were generated | Agreement |
| Axes | Density versus scattering coefficient | Density in kg m⁻³ versus \(k_s\) in m⁻¹ | Agreement |
| Density dependence | Increasing scattering with density | All six arrays increase across the sweep | Agreement |
| Curve grouping | Formulation- and microstructure-dependent separation | Sticky, non-sticky, and independent-sphere groups separate | Same qualitative pattern |
| Numerical correspondence | Source values were not digitized | Only inter-run statistics were available | Not scoreable |

The source figure supports the qualitative curve comparison, but it does not provide digitized values through the recorded workflow. [smrt-v1#fig03] The model configuration and scattering-coefficient calculation follow the recorded SMRT reproduction context. [smrt-v1#08]

### Assumed parameters

The following values were recorded as `model_assumption`:

- `electromagnetic_model = rayleigh`
- `microstructure_model = independent_sphere`
- `output = coefficients`
- `frequency_ghz = 37.0`
- `temperature_k = 265.0`
- `radius_m = 0.0001`
- `sweep_parameter = density_kg_m3`
- `sweep_start = 1.0`
- `sweep_stop = 100.0`
- `sweep_points = 40`

The following values were recorded as `backend_default`:

- `density_kg_m3 = None`
- `angle_deg = 55.0`
- `thickness_m = 1.0`
- `corr_length_m = 0.00015`
- `stickiness = 0.2`
- `dort_streams = 32`

The executed result handles nevertheless record a density sweep from **1.0 to 100.0 kg m⁻³** with **40 points**. The ledger entry `density_kg_m3 = None` is preserved as recorded and is not interpreted as paper evidence.

### Limitations

The source curves were not digitized, so exact numerical reproduction, source-to-model RMSE, bias, correlation, and percentage error are **not identifiable**. The runs also used several model assumptions and backend defaults rather than exclusively paper-explicit inputs. The result should therefore be interpreted as a qualitative reproduction of the six curve families and their density-dependent ordering, not as a numerical validation against published data.

**Final conclusion:** the recorded SMRT results reproduce the source figure’s qualitative increase with density and its formulation/microstructure-dependent ordering. Exact numerical agreement with the source remains not scoreable. [model:smrt@1.5.1] [skill:research-reporting]

<parameter_provenance>
[{"field":"density_kg_m3","value":null,"source_kind":"backend_default","source_ref":"Authoritative parameter ledger","reason":"The registered backend supplied this default; it is not paper evidence.","sensitivity_checked":false},{"field":"electromagnetic_model","value":"rayleigh","source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"microstructure_model","value":"independent_sphere","source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"output","value":"coefficients","source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"frequency_ghz","value":37.0,"source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"angle_deg","value":55.0,"source_kind":"backend_default","source_ref":"Authoritative parameter ledger","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},{"field":"thickness_m","value":1.0,"source_kind":"backend_default","source_ref":"Authoritative parameter ledger","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},{"field":"temperature_k","value":265.0,"source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"backend_default","source_ref":"Authoritative parameter ledger","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},{"field":"radius_m","value":0.0001,"source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"stickiness","value":0.2,"source_kind":"backend_default","source_ref":"Authoritative parameter ledger","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"backend_default","source_ref":"Authoritative parameter ledger","reason":"The registered model inserted this value during parameter resolution; it is not paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_start","value":1.0,"source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_stop","value":100.0,"source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_points","value":40,"source_kind":"model_assumption","source_ref":"Authoritative parameter ledger","reason":"The submitted run retained this value without attached paper or user evidence.","sensitivity_checked":false}]
</parameter_provenance>

<outcome>qualitative_reproduction_successful_quantitative_not_scoreable</outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| smrt | density_kg_m3 |  | backend_default | - |
| smrt | electromagnetic_model | rayleigh | model_assumption | - |
| smrt | microstructure_model | independent_sphere | model_assumption | - |
| smrt | output | coefficients | model_assumption | - |
| smrt | frequency_ghz | 37.0 | model_assumption | - |
| smrt | angle_deg | 55.0 | backend_default | - |
| smrt | thickness_m | 1.0 | backend_default | - |
| smrt | temperature_k | 265.0 | model_assumption | - |
| smrt | corr_length_m | 0.00015 | backend_default | - |
| smrt | radius_m | 0.0001 | model_assumption | - |
| smrt | stickiness | 0.2 | backend_default | - |
| smrt | dort_streams | 32 | backend_default | - |
| smrt | sweep_parameter | density_kg_m3 | model_assumption | - |
| smrt | sweep_start | 1.0 | model_assumption | - |
| smrt | sweep_stop | 100.0 | model_assumption | - |
| smrt | sweep_points | 40 | model_assumption | - |
