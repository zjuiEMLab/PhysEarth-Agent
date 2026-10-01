# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 shows two brightness-temperature curves over the recorded snow-density range of 100–917 kg m⁻³. The vertical-polarization curve remains above the horizontal-polarization curve; both rise, reach a maximum before the densest endpoint, and then decline. The curves therefore show the same qualitative pattern, not convergence or crossing. [model:smrt@1.5.1]

The planned chart rendered and passed manual visual review. The physical-model run also completed successfully and passed quality control. The qualitative reproduction is therefore successful, but numerical agreement with the paper is not scoreable because no digitized reference values or comparison statistics were supplied.

## Supporting results

### Conclusion supported by the generated image

Figure 1 contains two series, with snow density on the x-axis in kg m⁻³ and brightness temperature on the y-axis in K. The legend separates the two polarizations, and the image shows:

- two visible polarization curves;
- vertical polarization ordered above horizontal polarization;
- increasing brightness temperature through most of the range;
- a downturn near the high-density endpoint;
- no visible crossing or convergence claim.

The visual review confirms the same qualitative curve pattern. It does not provide digitized values or establish numerical agreement with a paper figure.

### Conclusion supported by the result arrays

The recorded SMRT result contains 10 points for each polarization. The reported series summaries show:

- `tb_v`: 45.1447–203.3109 K, with endpoint value 199.2696 K;
- `tb_h`: 40.8272–164.9864 K, with endpoint value 156.2760 K;
- both series marked non-monotonic.

These arrays support the rise–maximum–decline pattern and the ordering of vertical above horizontal polarization. No bias, RMSE, MAE, correlation, or other model-to-measurement statistic was supplied; numerical validation is therefore **not scoreable**. [model:smrt@1.5.1]

### Image–array comparison

| Aspect | Generated image | Result arrays | Assessment |
|---|---|---|---|
| Number of curves | Two | Two polarization outputs | Agreement |
| Axis quantities | Density and brightness temperature | Density sweep and `tb_h`/`tb_v` | Agreement |
| Units | kg m⁻³ and K | K for brightness temperature | Agreement |
| Polarization ordering | V above H | V values exceed H values in the recorded summary and preview | Agreement |
| Curve shape | Rise, maximum, then decline | Both series are non-monotonic | Agreement |
| Numerical paper agreement | Not digitized | No reference array or metric | Not scoreable |

The chart is qualitatively usable and corresponds to the recorded model outputs. It should not be described as an exact reproduction or as numerically validated against the paper.

## Guessed/assumed parameters

The authoritative ledger identifies the following values as backend defaults or assumptions rather than paper-explicit inputs:

- `electromagnetic_model = iba` — `backend_default`
- `microstructure_model = exponential` — `backend_default`
- `angle_deg = 55` — `backend_default`
- `temperature_k = 265` — `backend_default`
- `corr_length_m = 0.00015` — `backend_default`
- `radius_m = 0.0002` — `backend_default`
- `stickiness = 0.2` — `backend_default`
- `dort_streams = 32` — `backend_default`
- `sweep_parameter = none` — `backend_default`
- `sweep_points = 10` — `backend_default`
- `density_kg_m3 = 917` — `model_assumption`
- `sweep_start = 100.0` — `model_assumption`
- `sweep_stop = 917.0` — `model_assumption`

The ledger also records `output = tb`, `frequency_ghz = 37`, and `thickness_m = 1` as `user_specified`. The formal run record identifies the plotted axis as a density sweep, while the authoritative ledger lists `sweep_parameter = none`; this provenance inconsistency prevents treating the ledger as a complete paper-specific recipe. The recorded run itself nevertheless produced and rendered the density-axis figure.

## Limitations

The result demonstrates successful execution and qualitative curve correspondence, not numerical paper reproduction. The paper-specific parameter values were not available for the full configuration, and no digitized reference curve was provided. The final reproduction status is therefore **partial**: the requested model figure was generated and qualitatively reviewed, but numerical paper agreement remains unidentifiable.

<parameter_provenance>
[{"field":"electromagnetic_model","value":"iba","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Backend default retained in the authoritative ledger.","sensitivity_checked":false},{"field":"microstructure_model","value":"exponential","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Backend default retained in the authoritative ledger.","sensitivity_checked":false},{"field":"output","value":"tb","source_kind":"user","source_ref":"The registered input was mapped to the opened paper evidence and retained from the submitted plan.","reason":"User-specified output retained in the approved run.","sensitivity_checked":false},{"field":"frequency_ghz","value":"37","source_kind":"user","source_ref":"The registered input was mapped to the opened paper evidence and retained from the submitted plan.","reason":"User-specified frequency retained in the approved run.","sensitivity_checked":false},{"field":"angle_deg","value":"55","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Backend default retained in the authoritative ledger.","sensitivity_checked":false},{"field":"thickness_m","value":"1","source_kind":"user","source_ref":"The registered input was mapped to the opened paper evidence and retained from the submitted plan.","reason":"User-specified thickness retained in the approved run.","sensitivity_checked":false},{"field":"density_kg_m3","value":"917","source_kind":"assumption","source_ref":"The registered input was retained as a model assumption without paper evidence.","reason":"Model-assumption value recorded in the authoritative ledger.","sensitivity_checked":false},{"field":"temperature_k","value":"265","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Backend default retained in the authoritative ledger.","sensitivity_checked":false},{"field":"corr_length_m","value":"0.00015","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Backend default retained in the authoritative ledger.","sensitivity_checked":false},{"field":"radius_m","value":"0.0002","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Backend default retained in the authoritative ledger.","sensitivity_checked":false},{"field":"stickiness","value":"0.2","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Backend default retained in the authoritative ledger.","sensitivity_checked":false},{"field":"dort_streams","value":"32","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Backend default retained in the authoritative ledger.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Ledger value retained exactly; the formal figure record separately identifies a density axis.","sensitivity_checked":false},{"field":"sweep_points","value":"10","source_kind":"model_default","source_ref":"The registered backend supplied this default; it is not paper evidence.","reason":"Ledger value retained exactly.","sensitivity_checked":false},{"field":"sweep_start","value":"100.0","source_kind":"assumption","source_ref":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","reason":"Model-assumption sweep bound retained exactly from the ledger.","sensitivity_checked":false},{"field":"sweep_stop","value":"917.0","source_kind":"assumption","source_ref":"The submitted run retained this value without attached paper/user evidence; confirm it during plan review.","reason":"Model-assumption sweep bound retained exactly from the ledger.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
