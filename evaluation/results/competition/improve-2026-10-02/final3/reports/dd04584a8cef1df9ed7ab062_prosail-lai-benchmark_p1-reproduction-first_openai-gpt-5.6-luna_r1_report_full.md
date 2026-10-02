# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show a clear LAI response in the supported PROSAIL implementation. As LAI increases, NDVI and NIR reflectance rise toward a plateau, while red, green, and SWIR reflectances generally decline toward plateaus. The strongest change occurs between LAI = 0.0 and 0.5, followed by progressively weaker sensitivity at larger LAI. [model:prosail@2.0.5]

The figures are usable, but the PROSPECT-5 + 4SAIL Fortran reference is unavailable, so quantitative equivalence to that reference is not identifiable. The calibrated outcome is **partial**.

## Supporting results

Figure 1 contains four dimensionless reflectance-proxy series versus dimensionless LAI: green, red, NIR, and SWIR. Figure 2 contains one dimensionless NDVI series versus dimensionless LAI. Both generated charts passed the automated render check for finite, dense, legible plotted arrays; this check does not establish agreement with the unavailable reference figure.

The baseline result at LAI = 3.0 produced:

- green reflectance: 0.05833952322187055
- red reflectance: 0.023343884754454473
- NIR reflectance: 0.44648578316204524
- SWIR reflectance: 0.23441951953774764
- NDVI: 0.9006283070289071

The LAI sweep used 17 plotted points over LAI = 0.0–8.0. NDVI increased from 0.09155225398882812 to 0.933331031087096, and NIR reflectance increased from 0.385699987411499 to 0.485853373251835. Red reflectance decreased from 0.32100000977516174 to 0.016754163108499146, and SWIR reflectance decreased from 0.5095000267028809 to 0.21205186295868386. [model:prosail@2.0.5]

## Image and result comparison

| Aspect | Generated-image conclusion | Result-backed conclusion | Qualification |
|---|---|---|---|
| LAI response | NIR and NDVI rise; red, green, and SWIR decline and flatten. | The recorded arrays show those same qualitative trends. | Agreement is established for the supported implementation. |
| Low-LAI behaviour | The curves show an abrupt transition near LAI = 0.0–0.5. | The render review flagged that adjacent interval for the affected curves. | Endpoint behaviour should not be interpreted as reference-code validation. |
| Reference reproduction | No source/reference comparison is available for the PROSPECT-5 + 4SAIL Fortran implementation. | The supported model ran successfully. | Exact quantitative reproduction is not identifiable; validation statistics are N/A. |

## Guessed/assumed parameters

The authoritative ledger classifies the listed backend defaults as `backend_default` and the sweep bounds as `model_assumption`. None are paper-explicit. The parameter-source table is provided in the required machine-readable appendix below.

## Limitations

The experiment used the registered PROSAIL implementation, version 2.0.5, rather than the unavailable PROSPECT-5 + 4SAIL Fortran reference. No measured reflectance dataset was used, and no RMSE, bias, correlation, or other validation statistic was supplied. The result therefore supports the qualitative LAI sensitivity of the registered implementation, not numerical equivalence to the unavailable reference.

<parameter_provenance>
[{"field":"leaf_structure","value":"1.5","source_kind":"model_default","source_ref":"prosail-docs#00","reason":"Use the exact registered input; the ledger classifies it as a backend default, not paper evidence.","sensitivity_checked":false},{"field":"chlorophyll_ug_cm2","value":"40.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"carotenoid_ug_cm2","value":"8.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"anthocyanin_ug_cm2","value":"0.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"brown_pigment","value":"0.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"equivalent_water_thickness_cm","value":"0.01","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"dry_matter_g_cm2","value":"0.009","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"leaf_area_index","value":"3.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Baseline value inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":true},{"field":"average_leaf_angle_deg","value":"50.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"hot_spot","value":"0.01","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"solar_zenith_deg","value":"30.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"view_zenith_deg","value":"10.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"relative_azimuth_deg","value":"0.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"soil_brightness","value":"1.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"soil_moisture_fraction","value":"1.0","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default; no paper evidence was recorded.","sensitivity_checked":false},{"field":"sweep_parameter","value":"none","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default in the authoritative ledger.","sensitivity_checked":false},{"field":"sweep_points","value":"10","source_kind":"model_default","source_ref":"recorded run state: registered-model parameter resolution","reason":"Inserted as a backend default in the authoritative ledger.","sensitivity_checked":false},{"field":"sweep_start","value":"0.0","source_kind":"assumption","source_ref":"recorded approved run state; no paper or user evidence","reason":"Retained as the submitted sweep lower bound without attached paper or user evidence.","sensitivity_checked":true},{"field":"sweep_stop","value":"8.0","source_kind":"assumption","source_ref":"recorded approved run state; no paper or user evidence","reason":"Retained as the submitted sweep upper bound without attached paper or user evidence.","sensitivity_checked":true}]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>

**Parameter sources** (from the approved plan's parameter ledger)

| Model | Input | Value | Source | Evidence |
| --- | --- | --- | --- | --- |
| prosail | leaf_structure | 1.5 | backend_default | prosail-docs#00 |
| prosail | chlorophyll_ug_cm2 | 40.0 | backend_default | - |
| prosail | carotenoid_ug_cm2 | 8.0 | backend_default | - |
| prosail | anthocyanin_ug_cm2 | 0.0 | backend_default | - |
| prosail | brown_pigment | 0.0 | backend_default | - |
| prosail | equivalent_water_thickness_cm | 0.01 | backend_default | - |
| prosail | dry_matter_g_cm2 | 0.009 | backend_default | - |
| prosail | leaf_area_index | 3.0 | backend_default | - |
| prosail | average_leaf_angle_deg | 50.0 | backend_default | - |
| prosail | hot_spot | 0.01 | backend_default | - |
| prosail | solar_zenith_deg | 30.0 | backend_default | - |
| prosail | view_zenith_deg | 10.0 | backend_default | - |
| prosail | relative_azimuth_deg | 0.0 | backend_default | - |
| prosail | soil_brightness | 1.0 | backend_default | - |
| prosail | soil_moisture_fraction | 1.0 | backend_default | - |
| prosail | sweep_parameter | none | backend_default | - |
| prosail | sweep_points | 10 | backend_default | - |
| prosail | sweep_start | 0.0 | model_assumption | - |
| prosail | sweep_stop | 8.0 | model_assumption | - |
