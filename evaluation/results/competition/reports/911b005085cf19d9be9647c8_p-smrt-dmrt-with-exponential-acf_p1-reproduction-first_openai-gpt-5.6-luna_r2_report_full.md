# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figure shows two smooth, monotonically increasing brightness-temperature curves across 1–60 GHz, with vertical polarization above horizontal polarization throughout. It does not demonstrate convergence between electromagnetic formulations: only one formulation was actually executed, and the run used `iba` rather than the requested `dmrt_qcacp_shortrange`. [model:smrt@1.5.1]

The requested configuration was therefore **not reproduced exactly**. The outcome is **partial**: the chart was generated successfully, but the executed electromagnetic model contradicts the requested model identity.

## Supporting results

### Conclusion supported by the generated image

Figure 1 contains two series, with frequency in GHz on the x-axis and brightness temperature in K on the y-axis. The curves have the same broad increasing shape and remain visibly ordered, with `tb_v` above `tb_h`. The figure supports a qualitative frequency-response conclusion only; it does not establish numerical agreement with the source paper.

No inspected source-paper figure is recorded for direct visual comparison. Consequently, correspondence to a source image is **not identifiable**.

### Conclusion supported by the result arrays

The executed run used SMRT `iba`, exponential microstructure, 300 kg m⁻³ density, 55° incidence, 1 m thickness, 265 K temperature, 0.00015 m correlation length, and 32 DORT streams. It returned 10 frequency points from 1 to 60 GHz. [model:smrt@1.5.1]

`tb_h` increased from 0.4236 K to 179.1072 K, while `tb_v` increased from 0.4478 K to 198.9389 K. Both series were monotonic in the returned arrays. [model:smrt@1.5.1]

### Comparison

| Aspect | Generated figure | Actual result arrays | Qualification |
|---|---|---|---|
| Number of curves | Two | Two | Agrees |
| Units and axes | Frequency (GHz), brightness temperature (K) | 10-point frequency sweep with `tb_h` and `tb_v` | Agrees |
| Ordering | `tb_v` visibly above `tb_h` | `tb_v` is higher at the reported endpoints and across the returned series | Agrees |
| Convergence between formulations | Not shown | Not testable | Only one formulation was executed |
| Requested electromagnetic model | Not established by the image | Returned run used `iba` | Does not reproduce the requested DMRT-QCA-CP configuration |
| Numerical agreement with source | Not shown | No comparison statistic supplied | Not scoreable |

The render check passed, establishing that the plotted arrays were finite, sufficiently populated, and legible. It was not a comparison with the source figure and does not establish reproduction quality.

## Assumed parameters

The requested paper-linked configuration specified DMRT QCA-CP short-range electromagnetic theory and exponential microstructure. The SMRT paper describes the relevant electromagnetic and microstructure formulation choices. [smrt-v1#05]

The following values were assumptions or defaults rather than paper-explicit values: incidence angle, snow thickness, snow temperature, correlation length, DORT stream count, sweep bounds, radius, stickiness, sweep parameter, and sweep-point handling. Radius and stickiness were retained as backend metadata and were not used to make an exact exponential-autocorrelation claim.

## Limitations

The executed specification differed from the authoritative requested configuration in at least two material ways: it reported `iba` instead of `dmrt_qcacp_shortrange`, and it executed a frequency sweep despite the ledger listing `sweep_parameter = none`. The recorded result therefore supports the behavior of the returned run, not the requested DMRT-QCA-CP experiment.

No bias, RMSE, correlation, threshold, or other validation statistic was supplied. Numerical agreement with the paper is therefore not scoreable. The final conclusion is **partial reproduction**, not exact reproduction.

<parameter_provenance>
[{"field":"electromagnetic_model","value":"iba","source_kind":"unknown","source_ref":"recorded executed-run specification; conflicts with authoritative ledger value dmrt_qcacp_shortrange","reason":"Actual returned run used iba, so the requested user-specified theory was not executed","sensitivity_checked":false},{"field":"microstructure_model","value":"exponential","source_kind":"user","source_ref":"user-approved configuration; smrt-v1#05","source_span":"exponential microstructure representation","reason":"Preserved in the executed run","sensitivity_checked":false},{"field":"output","value":"tb","source_kind":"user","source_ref":"user-approved configuration","reason":"Requested brightness-temperature output","sensitivity_checked":false},{"field":"frequency_ghz","value":37.0,"source_kind":"user","source_ref":"user-approved configuration","reason":"Baseline frequency in the returned run specification","sensitivity_checked":false},{"field":"angle_deg","value":55.0,"source_kind":"assumption","source_ref":"recorded run metadata; no paper or user value","reason":"Model assumption","sensitivity_checked":false},{"field":"thickness_m","value":1.0,"source_kind":"assumption","source_ref":"recorded run metadata; no paper or user value","reason":"Model assumption","sensitivity_checked":false},{"field":"density_kg_m3","value":300.0,"source_kind":"user","source_ref":"user-approved configuration","reason":"Requested snow density","sensitivity_checked":false},{"field":"temperature_k","value":265.0,"source_kind":"assumption","source_ref":"recorded run metadata; no paper or user value","reason":"Model assumption","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"assumption","source_ref":"recorded run metadata; no paper or user value","reason":"Model assumption","sensitivity_checked":false},{"field":"radius_m","value":0.0002,"source_kind":"model_default","source_ref":"SMRT backend default retained in recorded run metadata","reason":"Not used for the exponential-microstructure interpretation","sensitivity_checked":false},{"field":"stickiness","value":0.2,"source_kind":"model_default","source_ref":"SMRT backend default retained in recorded run metadata","reason":"Not applicable to the exponential target","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"assumption","source_ref":"recorded run metadata; no paper or user value","reason":"Model assumption","sensitivity_checked":false},{"field":"sweep_parameter","value":"frequency_ghz","source_kind":"unknown","source_ref":"recorded executed-run specification; conflicts with authoritative ledger value none","reason":"The returned run performed a frequency sweep","sensitivity_checked":false},{"field":"sweep_start","value":1.0,"source_kind":"assumption","source_ref":"recorded executed-run specification","reason":"Retained sweep lower bound without attached paper or user evidence","sensitivity_checked":false},{"field":"sweep_stop","value":60.0,"source_kind":"assumption","source_ref":"recorded executed-run specification","reason":"Retained sweep upper bound without attached paper or user evidence","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"recorded backend/run metadata","reason":"Returned point count","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
