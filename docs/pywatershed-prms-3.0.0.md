# Task: add pywatershed/PRMS 3.0.0

## Goal

Add a real, pure-Python hydrologic model without changing PhysEarth-Agent's model contract.
The first milestone is a reproducible run of the official five-year Sagehen test domain in
the Sierra Nevada. A later milestone can replace the prepared test inputs with data acquired
and transformed from authoritative sources for a user-defined basin and period.

## Fixed provenance

- Model: [DOI-USGS/pywatershed](https://github.com/DOI-USGS/pywatershed)
- Release: `3.0.0` (13 July 2026)
- Git commit: `41707c16f1fac09e2e4d4ecb9e3bf6bf1948885e`
- Runtime: Python `>=3.12,<3.14`; use Python 3.12 initially
- Licence: CC0-1.0
- Initial domain: the release's `sagehen_5yr` / `sagehen_no_cascades` fixture
- Reference period: 1 October 1980 through 30 September 1985 at a 24-hour time step

Record the release URL, commit, environment lock, input checksums, control period, spatial
units, parameter files, and output checksums in every run manifest.

## Concise implementation sequence

1. **Declare the experiment.** Start with: “How do snow accumulation, snowmelt, and runoff
   evolve over the five-year Sagehen reference simulation?” Define the period, HRUs, output
   variables, units, and validation criteria before running.
2. **Resolve the environment.** Create an isolated Python 3.12 environment, install exactly
   `pywatershed==3.0.0`, record resolved dependencies and hardware, and run an import/version
   smoke test. Prefer the release's platform-specific frozen environment when exact
   dependency reproduction is required.
3. **Acquire immutable inputs.** Fetch the Sagehen fixture at the pinned 3.0.0 commit, verify
   checksums, and inventory the control, discretization, process-parameter, and time-varying
   forcing files. Never silently substitute missing data.
4. **Validate the model contract.** Check calendar and daily time axis; HRU identifiers and
   dimensions; precipitation and temperature units; missing values; parameter/forcing spatial
   alignment; and that every process input has one unambiguous producer.
5. **Build the PhysEarth adapter.** Follow the existing `model_card.yaml` plus `adapter.py`
   structure. Expose the process chain used by the no-cascades Sagehen configuration:
   `PRMSSolarGeometry`, `PRMSAtmosphere`, `PRMSCanopy`, `PRMSSnow`,
   `PRMSRunoffNoDprst`, `PRMSSoilzoneNoDprst`, and `PRMSGroundwaterNoDprst`. Keep large arrays
   in the result store and return bounded previews/handles.
6. **Run the reference case.** Execute the complete five-year daily simulation with mass
   budgets enabled. Preserve stdout, warnings, timing, configuration, derived files, and raw
   NetCDF outputs as run artifacts.
7. **Validate scientifically and numerically.** Require finite outputs, declared units and
   ranges, monotonic time, exact HRU alignment, acceptable water-budget closure, and agreement
   with the release's Sagehen reference outputs at the upstream project's documented process
   tolerances.
8. **Analyze and report.** Plot precipitation, SWE, snowmelt, surface runoff, soil-zone flow,
   and groundwater flow through time; report seasonal and water-year summaries; distinguish
   simulated quantities from observations; cite the model, data, transformations, and run.
9. **Test failure paths.** Cover unavailable Python versions, incomplete downloads, checksum
   mismatch, unit/calendar mismatch, missing parameters, resource limits, interrupted runs,
   budget failure, and output-contract failure.
10. **Only then generalize data preparation.** Add basin delineation, forcing download,
    temporal aggregation, spatial downscaling, unit conversion, gap handling, and PRMS-format
    export as explicit provenance-bearing transformations. A ratio such as snowmelt/runoff is
    a diagnostic, not source-water attribution, unless the experiment implements a defensible
    attribution method.

## Definition of done

- A clean machine can reproduce the pinned Sagehen run from recorded artifacts.
- PhysEarth-Agent refuses malformed or scientifically incompatible inputs before execution.
- Mass balance and upstream numerical comparisons pass with recorded tolerances.
- Every plotted or reported value resolves to an input, transformation, model run, and model
  version.
