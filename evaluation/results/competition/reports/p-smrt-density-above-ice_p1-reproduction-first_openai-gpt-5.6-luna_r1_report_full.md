# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated chart shows two brightness-temperature curves with the same qualitative pattern: both increase rapidly at low frequency and approach a high-frequency plateau. The H-polarized curve remains below the V-polarized curve. This is a spectral-shape result, not evidence of numerical solver convergence.

The requested **2000 kg m⁻³ density was not simulated**. The approved diagnostic used **917 kg m⁻³**, the legal upper boundary of the registered SMRT model. Consequently, the result is a **partial reproduction** and cannot identify the brightness temperature at 2000 kg m⁻³. [model:smrt@1.5.1]

## Supporting results

### Conclusion from the generated chart

The reviewed chart contains two series, H and V brightness temperature, with frequency in GHz on the horizontal axis and brightness temperature in K on the vertical axis. Visually, both curves rise sharply and then flatten. The displayed ordering is H below V.

This visual interpretation supports the same qualitative pattern as the recorded arrays, but it does not establish numerical agreement with a paper result or prove convergence with respect to the radiative-transfer solver.

### Conclusion from the recorded result

The formal run completed successfully and passed quality control. It used 10 frequency samples from 1 to 250 GHz. The recorded endpoint values were:

- At 1 GHz: H = 1.0745 K; V = 1.3702 K.
- At 250 GHz: H = 206.7223 K; V = 263.5836 K.

The recorded series were flagged as not strictly monotonic because of small high-frequency variations after the main rise. [model:smrt@1.5.1]

No measured comparison, bias, RMSE, correlation, or other validation statistic was recorded. Numerical agreement is therefore **not scoreable**.

| Question | Chart interpretation | Recorded-result interpretation | Assessment |
|---|---|---|---|
| Are there two polarization curves? | Yes | Yes: H and V outputs | Agreement |
| Is V above H? | Yes | Yes at the recorded endpoints and across the displayed sweep | Same qualitative ordering |
| Do the curves flatten at high frequency? | Yes | Yes, with small residual high-frequency variation | Same qualitative pattern |
| Is solver convergence demonstrated? | No | No convergence sweep was run | Not established |
| Was 2000 kg m⁻³ reproduced? | Not identifiable from the chart | No; the run used 917 kg m⁻³ | Partial outcome |

## Guessed/assumed parameters

The following values were not paper-explicit and are therefore treated as guessed or assumed:

- **Model assumptions:** `density_kg_m3=917`, `electromagnetic_model=iba`, `microstructure_model=exponential`, `sweep_parameter=frequency_ghz`, `sweep_start=1.0`, `sweep_stop=250.0`, and `sweep_points=10`.
- **Backend defaults:** `angle_deg=55`, `temperature_k=265`, `corr_length_m=0.00015`, `dort_streams=32`, `radius_m=0.0002`, and `stickiness=0.2`.
- **User-specified values:** `frequency_ghz=37`, `thickness_m=1`, and `output=tb`. The approved diagnostic also swept frequency, so the recorded result contains values at multiple frequencies.

The SMRT paper section supplied model context, but it did not make the diagnostic’s assumed parameter choices paper-explicit. [smrt-v1#02]

## Limitations

This run does not provide a result for 2000 kg m⁻³ and should not be extrapolated to that density. The first frequency interval is broad, from 1 to 28.67 GHz, so the low-frequency transition is only coarsely sampled. The run also did not test solver-stream convergence or compare against measurements.

The direct conclusion is therefore: **the legal-boundary diagnostic shows ordered H/V brightness-temperature curves with rapid increase and high-frequency flattening, but the requested 2000 kg m⁻³ result remains unidentifiable.**

<parameter_provenance>
[{"field":"frequency_ghz","value":37,"source_kind":"user","source_ref":"user question","reason":"The requested frequency is fixed by the user; the paper section establishes SMRT context but does not specify this numerical case.","sensitivity_checked":false},{"field":"thickness_m","value":1,"source_kind":"user","source_ref":"user question","reason":"The requested thickness is fixed by the user and passed to the legal-boundary diagnostic.","sensitivity_checked":false},{"field":"density_kg_m3","value":917,"source_kind":"assumption","source_ref":"smrt-v1#02; registered legal upper boundary","reason":"The requested 2000 kg/m3 is outside the registered model range; the diagnostic uses the declared upper boundary and is not a reproduction of the requested density.","sensitivity_checked":false},{"field":"electromagnetic_model","value":"iba","source_kind":"assumption","source_ref":"smrt-v1#02; approved run state","reason":"Preserved from the existing run and explicitly labeled as an assumption.","sensitivity_checked":false},{"field":"microstructure_model","value":"exponential","source_kind":"assumption","source_ref":"smrt-v1#02; approved run state","reason":"Preserved from the existing run and explicitly labeled as an assumption.","sensitivity_checked":false},{"field":"output","value":"tb","source_kind":"user","source_ref":"user question","reason":"The requested observable is passive brightness temperature.","sensitivity_checked":false},{"field":"angle_deg","value":55,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Backend default; not paper evidence or a user-specified condition.","sensitivity_checked":false},{"field":"temperature_k","value":265,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Backend default; not paper evidence or a user-specified condition.","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Backend default; not paper evidence or a user-specified condition.","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Backend default; no convergence test was recorded.","sensitivity_checked":false},{"field":"radius_m","value":0.0002,"source_kind":"model_default","source_ref":"registered SMRT parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"stickiness","value":0.2,"source_kind":"model_default","source_ref":"registered SMRT default","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"frequency_ghz","source_kind":"assumption","source_ref":"approved run state","reason":"The submitted diagnostic retained a frequency sweep without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_start","value":1.0,"source_kind":"assumption","source_ref":"approved run state","reason":"Retained diagnostic sweep lower bound without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_stop","value":250.0,"source_kind":"assumption","source_ref":"approved run state","reason":"Retained diagnostic sweep upper bound without attached paper or user evidence.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"assumption","source_ref":"approved run state","reason":"Retained diagnostic sample count without attached paper or user evidence.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
