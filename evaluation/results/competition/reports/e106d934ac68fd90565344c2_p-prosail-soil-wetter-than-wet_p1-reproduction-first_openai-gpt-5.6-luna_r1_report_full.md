# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated Figure 1 shows a clear, ordered separation of the two brightness-temperature curves: both H- and V-polarized brightness temperatures increase monotonically with snow density from 100 to 500 kg m⁻³, with V remaining above H throughout. It shows a density response, not numerical convergence between models or comparison with measurements.

The recorded state contains no inspected source-image comparison, so qualitative agreement with the paper figure is **not identifiable**. The computed SMRT result itself is successful for the approved configuration, but the broader reproduction outcome remains **partial** because the paper-level target was not fully identifiable with the registered outputs and assumptions [model:smrt@1.5.1].

## Conclusion supported by the generated image

Figure 1 contains two curves on axes of snow density (kg m⁻³) and brightness temperature (K). The curves are visibly separated and ordered, with V polarization above H polarization across the plotted range. No visual claim about agreement with the source figure is made because a source-image comparison was not recorded.

## Conclusion supported by the result arrays

The arrays confirm the plotted pattern:

- H polarization increased from **40.83 K** at 100 kg m⁻³ to **152.48 K** at 500 kg m⁻³.
- V polarization increased from **45.14 K** to **177.65 K** over the same range.
- Both series were monotonic over the nine-point sweep [model:smrt@1.5.1].

The baseline at 300 kg m⁻³ was **112.44 K (H)** and **127.23 K (V)** [model:smrt@1.5.1].

## Image–array comparison

| Aspect | Generated image | Recorded arrays | Assessment |
|---|---|---|---|
| Number of curves | Two | Two | Agreement |
| Axes and units | Density in kg m⁻³; brightness temperature in K | Same | Agreement |
| Ordering | V above H | V above H at every point | Agreement |
| Shape | Both curves rise with density | Both are monotonic increasing | Agreement |
| Source-figure correspondence | Not inspected in the recorded state | Not applicable | Not scoreable |
| Numerical agreement with source | Not supplied | No digitized source values | Not scoreable |

The successful render check establishes that Figure 1 is legible and contains the intended arrays; it does not establish agreement with the paper source image. No bias, RMSE, correlation, or other validation statistic was supplied.

## Guessed/assumed parameters

The following values are not paper-explicit in the recorded ledger and are therefore treated as assumptions or backend defaults rather than paper-derived values:

- IBA electromagnetic model.
- Exponential microstructure.
- Baseline density of 300 kg m⁻³.
- Correlation length of 0.00015 m.
- Frequency of 37 GHz.
- Incidence angle of 55°.
- Layer thickness of 1 m.
- Temperature of 265 K.
- DORT stream count of 32.
- Backend-default particle radius of 0.0002 m.
- Backend-default stickiness of 0.2.
- Brightness-temperature output selection.

The density sweep from 100 to 500 kg m⁻³ with nine points was user-specified. The paper evidence used for the model context was SMRT v1 [smrt-v1#08].

## Limitations

The source figure was not available for a recorded visual comparison, and the source curves were not digitized. Consequently, the result supports the generated-figure and model-array conclusions only; source-figure numerical agreement is not scoreable. The report does not claim exact reproduction.

<parameter_provenance>
[{"field":"electromagnetic_model","value":"iba","source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"provenance=model_assumption; preserve the submitted IBA theory choice as an explicitly labeled model assumption","sensitivity_checked":false},{"field":"microstructure_model","value":"exponential","source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"provenance=model_assumption; preserve the submitted exponential microstructure choice as an explicitly labeled model assumption","sensitivity_checked":false},{"field":"density_kg_m3","value":300,"source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"provenance=model_assumption; preserve the submitted baseline density","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"provenance=model_assumption; preserve the submitted correlation length","sensitivity_checked":false},{"field":"frequency_ghz","value":37,"source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"provenance=model_assumption; preserve the submitted frequency","sensitivity_checked":false},{"field":"angle_deg","value":55,"source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"provenance=model_assumption; preserve the submitted incidence angle","sensitivity_checked":false},{"field":"thickness_m","value":1,"source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"provenance=model_assumption; preserve the submitted layer thickness","sensitivity_checked":false},{"field":"temperature_k","value":265,"source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"provenance=model_assumption; preserve the submitted temperature","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"assumption","source_ref":"smrt-v1#08","source_span":"","reason":"provenance=model_assumption; preserve the submitted numerical setting","sensitivity_checked":false},{"field":"radius_m","value":0.0002,"source_kind":"model_default","source_ref":"none","source_span":"","reason":"provenance=backend_default; resolved backend default, not paper evidence","sensitivity_checked":false},{"field":"stickiness","value":0.2,"source_kind":"model_default","source_ref":"none","source_span":"","reason":"provenance=backend_default; resolved backend default, not paper evidence","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"user","source_ref":"user-approved research plan","source_span":"","reason":"provenance=user_specified; submitted density sweep","sensitivity_checked":true},{"field":"sweep_start","value":100,"source_kind":"user","source_ref":"user-approved research plan","source_span":"","reason":"provenance=user_specified; submitted sweep range","sensitivity_checked":true},{"field":"sweep_stop","value":500,"source_kind":"user","source_ref":"user-approved research plan","source_span":"","reason":"provenance=user_specified; submitted sweep range","sensitivity_checked":true},{"field":"sweep_points","value":9,"source_kind":"user","source_ref":"user-approved research plan","source_span":"","reason":"provenance=user_specified; submitted sweep resolution","sensitivity_checked":true},{"field":"output","value":"tb","source_kind":"assumption","source_ref":"none","source_span":"","reason":"provenance=model_assumption; retained brightness-temperature output without attached paper or user evidence","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
