# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

Figure 1 shows two finite, legible brightness-temperature curves with the same ordering throughout the density sweep: V-polarized brightness temperature remains above H-polarized brightness temperature, and both decrease slightly as density increases. The generated figure therefore supports a same-pattern, weakly decreasing response over the executed range, not a divergence or crossing. [model:smrt@1.5.1]

The requested density value of **2000 kg m⁻³** is not identifiable from the executed result: it lies outside the registered model range, and no run at that value was performed. The executed run instead covered **916–917 kg m⁻³** with eight points. [model:smrt@1.5.1]

## Supporting results

### Conclusion supported by the generated image

The generated image contains two series, with density on the x-axis in kg m⁻³ and brightness temperature on the y-axis in K. It shows:

- V polarization above H polarization throughout;
- both curves decreasing over the plotted interval;
- no visible crossing or divergence;
- a very small change over the narrow density range.

The render check establishes that the generated arrays were finite, sufficiently sampled, and legible. It does not establish agreement with the source paper.

### Conclusion supported by the result arrays

The recorded run used SMRT v1.5.1 with 37 GHz, 55° incidence, 1 m snow thickness, and a density sweep from 916 to 917 kg m⁻³. [model:smrt@1.5.1]

- H-polarized brightness temperature: **156.3343 K → 156.2760 K**.
- V-polarized brightness temperature: **199.3226 K → 199.2696 K**.
- Both series were recorded as monotonically decreasing in the run summary. [model:smrt@1.5.1]

No bias, RMSE, correlation, or other numerical comparison with a source-paper curve was supplied; such statistics are **not scoreable**.

## Image–array comparison

| Aspect | Generated image | Recorded arrays | Assessment |
|---|---|---|---|
| Series count | Two curves | H and V series | Agreement |
| Ordering | V above H | V values exceed H values | Agreement |
| Trend | Both decrease | Both decrease | Agreement |
| Numerical scale | Axes show K | Values are in K | Agreement |
| Source-paper agreement | Not established by the render check | No digitized source values or comparison metric | Not scoreable |

The result is therefore a qualitative reproduction of the generated diagnostic pattern only. A source-image comparison and complete paper reproduction are not established by the recorded evidence.

## Assumed/guessed parameters

The following values were not supported as paper-explicit values in the ledger:

- `electromagnetic_model = iba` — backend default.
- `microstructure_model = exponential` — backend default.
- `output = tb` — model assumption.
- `angle_deg = 55.0` — backend default.
- `temperature_k = 265.0` — backend default.
- `corr_length_m = 0.00015` — backend default.
- `radius_m = 0.0002` — backend default.
- `stickiness = 0.2` — backend default.
- `dort_streams = 32` — backend default.
- `sweep_parameter = density_kg_m3` — model assumption.
- `sweep_start = 916.0` and `sweep_stop = 917.0` — model assumptions in the ledger, although these values were used by the recorded execution.
- `sweep_points = 2` — listed in the authoritative ledger, but the recorded execution used **8** points. The execution record therefore conflicts with this ledger entry.

The ledger also identifies `frequency_ghz = 37` and `thickness_m = 1` as user-specified. The ledger’s `density_kg_m3 = 2000` entry was not executable under the registered model range and was not used by the recorded run. [model:smrt@1.5.1]

## Limitations

The executed result cannot answer the response at 2000 kg m⁻³ because that density is outside the declared model range and was not simulated. The available chart is a diagnostic density sweep, not a validated reproduction against digitized paper data. Consequently, the calibrated outcome is **partial**.

<parameter_provenance>
[{"field":"frequency_ghz","value":37.0,"source_kind":"user","source_ref":"user-locked frequency","reason":"User-specified frequency in the authoritative parameter ledger.","sensitivity_checked":false},{"field":"thickness_m","value":1.0,"source_kind":"user","source_ref":"user-locked thickness","reason":"User-specified thickness in the authoritative parameter ledger.","sensitivity_checked":false},{"field":"density_kg_m3","value":{"executed_sweep_start":916.0,"executed_sweep_stop":917.0,"executed_sweep_points":8,"ledger_value":2000},"source_kind":"user","source_ref":"user-locked value; execution record legal_partial_run","reason":"The ledger specifies 2000 kg m-3, but the recorded execution used the legal 916–917 kg m-3 sweep; 2000 kg m-3 was not run.","sensitivity_checked":false},{"field":"electromagnetic_model","value":"iba","source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"microstructure_model","value":"exponential","source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"output","value":"tb","source_kind":"assumption","source_ref":"approved run specification","reason":"The executed run retained brightness temperature as the observable without attached paper or user evidence.","sensitivity_checked":false},{"field":"angle_deg","value":55.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"temperature_k","value":265.0,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"corr_length_m","value":0.00015,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"radius_m","value":0.0002,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"stickiness","value":0.2,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"dort_streams","value":32,"source_kind":"model_default","source_ref":"registered model parameter resolution","reason":"Inserted by the registered model; not paper evidence.","sensitivity_checked":false},{"field":"sweep_parameter","value":"density_kg_m3","source_kind":"assumption","source_ref":"approved diagnostic chart design","reason":"Density was used as the plotted sweep axis.","sensitivity_checked":false},{"field":"sweep_start","value":916.0,"source_kind":"assumption","source_ref":"execution record legal_partial_run","reason":"The recorded run began the density sweep at 916 kg m-3.","sensitivity_checked":false},{"field":"sweep_stop","value":917.0,"source_kind":"assumption","source_ref":"execution record legal_partial_run","reason":"The recorded run ended the density sweep at 917 kg m-3.","sensitivity_checked":false},{"field":"sweep_points","value":8,"source_kind":"assumption","source_ref":"execution record legal_partial_run","reason":"The recorded run produced eight density points; this conflicts with the authoritative ledger value of 2.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
