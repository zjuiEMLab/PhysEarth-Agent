# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show a clear, non-crossing ordering: V-polarized brightness temperature and emissivity remain above the corresponding H-polarized curves across the full soil-moisture range of 0.05–0.50 m³ m⁻³. All four modeled quantities decrease monotonically as soil moisture increases. [model:tau_omega@1.0.0]

This is a **partial reproduction** of the Fig. 9 target [figure:cmem-sampling-density#fig09]. The approved tau-omega analogue was executed successfully, but the paper’s CMEM comparison could not be reproduced quantitatively because CMEM was unavailable. The paper’s L-band modeling context is documented in [cmem-sampling-density#03] and [cmem-sampling-density#06].

## Supporting results

The baseline run used 1.41 GHz, 40° incidence, and soil moisture of 0.25 m³ m⁻³. It produced:

- H brightness temperature: **224.8044 K**
- V brightness temperature: **246.4358 K**
- H emissivity: **0.5372**
- V emissivity: **0.6950**

The 10-point soil-moisture sweep produced the following endpoint changes:

- H brightness temperature: **248.1286 to 214.7619 K**
- V brightness temperature: **268.9662 to 234.5853 K**
- H emissivity: **0.7073 to 0.4639**
- V emissivity: **0.8593 to 0.6085**

These are tau-omega model outputs, not measurements or values digitized from the paper. [model:tau_omega@1.0.0]

Two formal figures were generated:

1. **Tau-omega H/V brightness temperature versus soil moisture**  
   x-axis: volumetric soil moisture (m³ m⁻³); y-axis: brightness temperature (K); two series.

2. **Tau-omega H/V emissivity versus soil moisture**  
   x-axis: volumetric soil moisture (m³ m⁻³); y-axis: emissivity (1); two series.

Both figures rendered successfully and passed the automatic render checks. Those checks establish array legibility only; they do not establish quantitative agreement with the source figure.

## Source and generated-figure comparison

The source target is Fig. 9 [figure:cmem-sampling-density#fig09]. The generated figures contain the approved H/V groupings and show the monotonic soil-moisture response described above. The comparison is limited because the executed model was tau-omega rather than CMEM. No digitized source values, bias, RMSE, correlation, or other agreement statistic was supplied; quantitative agreement is therefore **not scoreable**.

The appropriate conclusion is that the experiment reproduces a qualitative soil-moisture sensitivity pattern within the registered tau-omega model, not that it quantitatively reproduces the CMEM result.

## Assumed parameters

The following entries were not paper-explicit in the approved ledger:

- **Model assumptions:** incidence angle 40.0°, baseline soil moisture 0.25 m³ m⁻³, sweep start 0.05 m³ m⁻³, and sweep stop 0.50 m³ m⁻³.
- **Backend defaults:** 10 sweep points, bulk density 1.3 g cm⁻³, soil temperature 293.0 K, canopy temperature 293.0 K, vegetation optical depth 0.3, single-scattering albedo 0.05, roughness parameter 0.3, and cross-polarization parameter 0.0.
- **User-specified settings:** frequency 1.41 GHz and soil moisture as the swept parameter.

## Limitations

The executed model was tau-omega v1.0.0, not CMEM. Consequently, differences in formulation, parameterization, and unspecified paper conditions prevent a quantitative CMEM reproduction. The result is **partial**, with the qualitative tau-omega response successfully generated and the requested CMEM comparison remaining unavailable. [model:tau_omega@1.0.0]

<parameter_provenance>
[{"field":"frequency_ghz","value":1.41,"source_kind":"user","source_ref":"cmem-sampling-density#03; approved parameter ledger","source_span":"L-band context","reason":"User-approved frequency for the submitted tau-omega analogue; the experiment differs from the paper condition.","sensitivity_checked":false},{"field":"angle_deg","value":40.0,"source_kind":"assumption","source_ref":"approved parameter ledger; no paper evidence","reason":"Hold geometry fixed for the sensitivity experiment.","sensitivity_checked":false},{"field":"soil_moisture","value":0.25,"source_kind":"assumption","source_ref":"approved parameter ledger; no paper evidence","reason":"Baseline value for smoke validation.","sensitivity_checked":false},{"field":"sweep_parameter","value":"soil_moisture","source_kind":"user","source_ref":"approved parameter ledger; user-approved experiment","reason":"Sweep the declared soil-moisture input.","sensitivity_checked":false},{"field":"sweep_start","value":0.05,"source_kind":"assumption","source_ref":"approved parameter ledger; no paper evidence","reason":"Legal lower endpoint for the planned exploration.","sensitivity_checked":false},{"field":"sweep_stop","value":0.5,"source_kind":"assumption","source_ref":"approved parameter ledger; no paper evidence","reason":"Legal upper endpoint for the planned exploration.","sensitivity_checked":false},{"field":"sweep_points","value":10,"source_kind":"model_default","source_ref":"registered tau_omega default; approved parameter ledger","reason":"Retain the declared default point count.","sensitivity_checked":false},{"field":"bulk_density_g_cm3","value":1.3,"source_kind":"model_default","source_ref":"registered tau_omega default; approved parameter ledger","reason":"Hold fixed.","sensitivity_checked":false},{"field":"soil_temperature_k","value":293.0,"source_kind":"model_default","source_ref":"registered tau_omega default; approved parameter ledger","reason":"Hold fixed.","sensitivity_checked":false},{"field":"canopy_temperature_k","value":293.0,"source_ref":"registered tau_omega default; approved parameter ledger","reason":"Hold fixed.","sensitivity_checked":false},{"field":"vegetation_optical_depth","value":0.3,"source_kind":"model_default","source_ref":"registered tau_omega default; approved parameter ledger","reason":"Retain the declared vegetated-surface default.","sensitivity_checked":false},{"field":"single_scattering_albedo","value":0.05,"source_kind":"model_default","source_ref":"registered tau_omega default; approved parameter ledger","reason":"Legal with nonzero vegetation optical depth; hold fixed.","sensitivity_checked":false},{"field":"roughness_h","value":0.3,"source_kind":"model_default","source_ref":"registered tau_omega default; approved parameter ledger","reason":"Hold fixed.","sensitivity_checked":false},{"field":"cross_q","value":0.0,"source_kind":"model_default","source_ref":"registered tau_omega default; approved parameter ledger","reason":"Hold fixed.","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
