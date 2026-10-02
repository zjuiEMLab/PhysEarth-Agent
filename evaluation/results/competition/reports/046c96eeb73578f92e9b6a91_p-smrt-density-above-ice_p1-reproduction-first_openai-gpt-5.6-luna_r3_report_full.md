# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated diagnostic shows two passive brightness-temperature curves over **916–917 kg m⁻³**. Vertical polarization remains above horizontal polarization, and both curves decrease slightly across the interval. This is a legal-boundary diagnostic; it does not evaluate the requested density of **2000 kg m⁻³**.

The original reproduction is therefore **partial**. The approved SMRT run completed successfully, but 2000 kg m⁻³ was not executable within the registered model’s declared density range. [model:smrt@1.5.1]

## Supporting results

The model returned:

| Snow density (kg m⁻³) | TBₕ (K) | TBᵥ (K) |
|---:|---:|---:|
| 916.0 | 156.3343 | 199.3226 |
| 917.0 | 156.2760 | 199.2696 |

Across the diagnostic interval, TBₕ decreased by **0.0584 K**, while TBᵥ decreased by **0.0530 K**. TBᵥ was higher than TBₕ at both evaluated densities. These values are model outputs, not measurements. [model:smrt@1.5.1]

The selected figure was rendered with snow density on the x-axis and brightness temperature in kelvin on the y-axis. The recorded render check passed. This establishes that the generated curves were available and legible; it does not establish numerical agreement with a source figure.

## Comparison and interpretation

The figure and the returned arrays support the same qualitative interpretation:

- two polarization series are present;
- TBᵥ is ordered above TBₕ;
- both series slope slightly downward over 916–917 kg m⁻³.

No numerical comparison with a source curve was recorded. Bias, RMSE, correlation, and percent error are therefore **not scoreable**.

## Assumed parameters

The original user-specified conditions were:

- frequency: **37 GHz**;
- snow thickness: **1 m**;
- requested density: **2000 kg m⁻³**;
- output: **brightness temperature**.

The executed legal-boundary diagnostic used **916–917 kg m⁻³** with two sweep points. The following values were retained as assumptions or backend defaults rather than paper-explicit values:

- electromagnetic model: `iba`;
- microstructure model: `exponential`;
- incidence angle: **55°**;
- snow temperature: **265 K**;
- DORT streams: **32**;
- correlation length: **0.00015 m**;
- particle radius: **0.0002 m**;
- stickiness: **0.2**;
- sweep parameter: `density_kg_m3`;
- sweep start: **916.0 kg m⁻³**;
- sweep stop: **917.0 kg m⁻³**;
- sweep points: **2**.

These choices describe the executed diagnostic and should not be interpreted as values extracted from the paper.

## Limitations

The executed run does not identify the model response at 2000 kg m⁻³. The two-point boundary diagnostic shows only the local behavior at the upper legal boundary. The outcome is consequently **partial**, not a reproduction at the requested density.

<parameter_provenance>
[{"field":"frequency_ghz","value":37,"source_kind":"user","source_ref":"user question","reason":"User-specified frequency retained in the approved run.","sensitivity_checked":false},{"field":"thickness_m","value":1,"source_kind":"user","source_ref":"user question","reason":"User-specified snow thickness retained in the approved run.","sensitivity_checked":false},{"field":"density_kg_m3","value":2000,"source_kind":"user","source_ref":"user question","reason":"Original requested density; not evaluated because it was outside the registered model range.","sensitivity_checked":false},{"field":"density_kg_m3","value":917,"source_kind":"assumption","source_ref":"approved legal-boundary validation run","reason":"Upper legal-boundary value used by the executed diagnostic.","sensitivity_checked":false},{"field":"output","value":"tb","source_kind":"user","source_ref":"user question","reason":"User requested passive brightness temperature.","sensitivity_checked":false},{"field":"electromagnetic_model","value":"iba","source_kind":"model_default","source_ref":"registered SMRT default","reason":"Backend default retained in the approved run.","sensitivity_checked":false},{"field":"microstructure_model","value":"exponential","source_kind":"model_default","source_ref":"registered SMRT default","reason":"Backend default retained in the approved run.","sensitivity_checked":false},{"field":"angle_deg","value":55,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Backend default retained in the approved run.","sensitivity_checked":false},{"field":"temperature_k","value":265,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Backend default retained in the approved run.","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Backend default retained in the approved run.","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Registered model default retained in the approved run.","sensitivity_checked":false},{"field":"radius_m","value":0.0002,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Registered model default retained in the approved run.","sensitivity_checked":false},{"field":"stickiness","value":0.2,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Registered model default retained in the approved run.","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"assumption","source_ref":"approved diagnostic run","reason":"Density was varied to test the legal boundary.","sensitivity_checked":false},{"field":"sweep_start","value":916.0,"source_kind":"assumption","source_ref":"approved diagnostic run","reason":"Lower endpoint of the executed legal-boundary sweep.","sensitivity_checked":false},{"field":"sweep_stop","value":917.0,"source_kind":"assumption","source_ref":"approved diagnostic run","reason":"Upper endpoint of the executed legal-boundary sweep.","sensitivity_checked":false},{"field":"sweep_points","value":2,"source_kind":"assumption","source_ref":"approved diagnostic run","reason":"Number of points in the executed sweep.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
