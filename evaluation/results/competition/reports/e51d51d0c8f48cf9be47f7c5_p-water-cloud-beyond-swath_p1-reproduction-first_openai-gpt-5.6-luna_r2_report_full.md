# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

## Research result and conclusion

The generated figures show two local sensitivity relationships, not a reproduction of the paper’s calibrated WCM result. Figure 1 shows an ordered, monotonic increase in soil and total backscatter with soil moisture. Figure 2 shows increasing vegetation backscatter and decreasing transmissivity as vegetation water increases, with a fixed soil-backscatter curve. Both figures contain three backscatter series with the recorded axes and units.

A source-image comparison is not available in the recorded state, so qualitative correspondence with the paper figure is **not scoreable**. The reproduction outcome is therefore **partial**: the local diagnostic was executed successfully, but the unavailable paper WCM comparison cannot be reproduced.

## Conclusion supported by the generated figures

- **Figure 1:** Three curves are plotted against soil moisture, with soil and total backscatter increasing and the vegetation contribution remaining visually constant.
- **Figure 2:** Three curves are plotted against vegetation water, with the soil contribution remaining constant while the vegetation and total-backscatter curves change.
- The figures establish curve count, axes, units, grouping, ordering, and qualitative shape. They do not establish numerical agreement with the source paper.

## Conclusion supported by result arrays

The baseline result was:

- Total backscatter: **−13.4748 dB**
- Soil contribution: **−14.5000 dB**
- Vegetation contribution: **−17.2917 dB**
- Two-way transmissivity: **0.7404** [model:water_cloud@1.0.0]

For the soil-moisture sweep from **0.01 to 0.60 m³ m⁻³**, total backscatter increased from **−16.2594 to −5.0386 dB**, while the vegetation contribution remained **−17.2917 dB**. [model:water_cloud@1.0.0]

For the vegetation-water sweep from **0 to 8.0 kg m⁻²**, total backscatter changed from **−14.5000 to −2.7879 dB**; vegetation backscatter changed from **−60.0000 to −2.8144 dB**, and two-way transmissivity declined from **1.0000 to 0.0903**. [model:water_cloud@1.0.0]

## Comparison of the two conclusions

| Aspect | Generated figures | Result arrays | Assessment |
|---|---|---|---|
| Soil-moisture response | Increasing soil and total curves; constant vegetation curve | Total: −16.2594 to −5.0386 dB; vegetation fixed at −17.2917 dB | Agreement |
| Vegetation-water response | Changing vegetation and total curves; fixed soil curve | Total: −14.5000 to −2.7879 dB; soil fixed at −14.5000 dB | Agreement |
| Comparison with paper source image | No inspected source-image comparison recorded | No paper-WCM result available | Not scoreable |
| Numerical agreement statistics | Not supplied | Bias, RMSE, correlation, and percent error: **N/A** | Not scoreable |

The figures are usable representations of the executed local model arrays, but their successful rendering does not demonstrate agreement with the paper. The unavailable paper WCM and the local `water_cloud` implementation are not treated as equivalent.

## Guessed/assumed parameters

The following ledger entries were not paper-explicit:

- `angle_deg = 37.0`: **model_assumption**; local diagnostic assumption.
- `soil_moisture = 0.25`: **model_assumption**; local baseline.
- `vegetation_water_kg_m2 = 1.0`: **model_assumption**; local baseline.
- `coefficient_a = 0.09`: **backend_default**; registered backend default.
- `coefficient_b = 0.12`: **backend_default**; registered backend default.
- `coefficient_c = -22.0`: **backend_default**; registered backend default.
- `coefficient_d = 30.0`: **backend_default**; registered backend default.
- `sweep_parameter = none`: **backend_default** for the baseline; overridden in the sweep runs.
- `sweep_points = 10`: **backend_default** for the baseline; the two sweep runs used their existing configured 20 points.
- `sweep_start = 0.01` and `sweep_stop = 0.6`: **model_assumption** for the soil-moisture sweep.
- `sweep_start = 0.0` and `sweep_stop = 8.0`: **model_assumption** for the vegetation-water sweep.

## Limitations

The requested paper WCM comparison was unavailable and unrun. No source-image qualitative comparison, digitized reference data, or numerical validation statistics were recorded. The result supports only the local `water_cloud` sensitivity diagnostics. [backscatter-forward-operator#05]

<parameter_provenance>
[
  {
    "field": "angle_deg",
    "value": 37.0,
    "source_kind": "assumption",
    "source_ref": "Local diagnostic assumption; not an exact paper setting",
    "reason": "Controlled baseline incidence angle",
    "sensitivity_checked": false
  },
  {
    "field": "soil_moisture",
    "value": 0.25,
    "source_kind": "assumption",
    "source_ref": "Local baseline; swept separately and not treated as paper-reproduced",
    "reason": "Baseline soil moisture",
    "sensitivity_checked": true
  },
  {
    "field": "vegetation_water_kg_m2",
    "value": 1.0,
    "source_kind": "assumption",
    "source_ref": "Local baseline; swept separately and not treated as paper-reproduced",
    "reason": "Baseline vegetation water content",
    "sensitivity_checked": true
  },
  {
    "field": "coefficient_a",
    "value": 0.09,
    "source_kind": "model_default",
    "source_ref": "Registered backend default held fixed",
    "reason": "Vegetation scattering coefficient",
    "sensitivity_checked": false
  },
  {
    "field": "coefficient_b",
    "value": 0.12,
    "source_kind": "model_default",
    "source_ref": "Registered backend default held fixed",
    "reason": "Vegetation attenuation coefficient",
    "sensitivity_checked": false
  },
  {
    "field": "coefficient_c",
    "value": -22.0,
    "source_kind": "model_default",
    "source_ref": "Registered backend default held fixed",
    "reason": "Soil backscatter intercept",
    "sensitivity_checked": false
  },
  {
    "field": "coefficient_d",
    "value": 30.0,
    "source_kind": "model_default",
    "source_ref": "Registered backend default held fixed",
    "reason": "Soil-moisture backscatter coefficient",
    "sensitivity_checked": false
  },
  {
    "field": "sweep_parameter",
    "value": {
      "baseline": "none",
      "soil-moisture-sweep": "soil_moisture",
      "vegetation-water-sweep": "vegetation_water_kg_m2"
    },
    "source_kind": "model_default",
    "source_ref": "Baseline default; sweep runs override this with their declared sweep parameter",
    "reason": "Approved baseline and sensitivity runs",
    "sensitivity_checked": true
  },
  {
    "field": "sweep_points",
    "value": {
      "baseline": 10,
      "soil-moisture-sweep": 20,
      "vegetation-water-sweep": 20
    },
    "source_kind": "model_default",
    "source_ref": "Backend default mapping; explicit sweep runs retain their existing configured point count",
    "reason": "Approved run configurations",
    "sensitivity_checked": false
  },
  {
    "field": "sweep_start",
    "value": {
      "soil-moisture-sweep": 0.01,
      "vegetation-water-sweep": 0.0
    },
    "source_kind": "assumption",
    "source_ref": "Preserved existing local sensitivity-sweep ranges",
    "reason": "Approved sweep lower bounds",
    "sensitivity_checked": true
  },
  {
    "field": "sweep_stop",
    "value": {
      "soil-moisture-sweep": 0.6,
      "vegetation-water-sweep": 8.0
    },
    "source_kind": "assumption",
    "source_ref": "Preserved existing local sensitivity-sweep ranges",
    "reason": "Approved sweep upper bounds",
    "sensitivity_checked": true
  }
]
</parameter_provenance>
<reproduction_outcome>partial</reproduction_outcome>
