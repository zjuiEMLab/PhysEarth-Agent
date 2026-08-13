# Scientific Questions and SMRT Reproduction Steps for Section 3

**Reference paper:** Picard et al. (2018), *Simulation of the microwave emission of multi-layered snowpacks using the Dense Media Radiative transfer theory: the SMRT model*, Geoscientific Model Development, 11, 2763–2788.

**Objective:** Reproduce and verify the numerical experiments in Section 3 using SMRT, while separating differences caused by electromagnetic theory, microstructure representation, radiative-transfer solvers, and numerical implementation.

---

## 0. Review of the Existing Steps

### Overall assessment

The four scientific questions and their main experimental directions are scientifically reasonable. They follow the same progression as the paper:

```text
low-density limit
    -> cross-model comparison with DMRT
    -> cross-solver / cross-formulation comparison with MEMLS
    -> equivalence and transferability of microstructure representations
```

However, the original steps are primarily a **reproduction checklist**. They are not yet a complete, safe, user-facing research workflow. Before an Agent runs a registered physical model, it must also:

1. resolve ambiguities in the source paper;
2. translate a natural-language question into measurable quantities and a controlled experiment;
3. verify that the selected model actually declares the required capability;
4. ask the user to approve or revise the plan when choices affect the scientific interpretation;
5. run a baseline and numerical sanity checks before the main sweep;
6. record all inputs, software versions, intermediate outputs, warnings, and failed runs;
7. separate model failure, unsupported comparison, and scientific negative results;
8. connect every quantitative claim to a stored result and plot;
9. report applicability limits instead of presenting one successful run as a general conclusion.

### Issues that must be fixed before claiming a faithful reproduction

#### 1. Resolve source-paper inconsistencies explicitly

The Picard et al. paper has an apparent temperature inconsistency for the Figure 4 experiment: the paragraph in the main text states 256 K, while the Figure 4 caption states 265 K. The existing task uses 265 K. This is a reasonable default because it follows the figure caption and the implementation currently uses 265 K, but it must be recorded as a source ambiguity rather than silently treated as an exact fact.

The Agent should either:

- ask the user which interpretation to use;
- run both 256 K and 265 K as an ambiguity sensitivity test; or
- use the caption value as the default and state the alternative in the run manifest.

The same rule applies to every unclear radius, density, substrate, dielectric model, angle grid, stream count, and unit in a reference paper.

#### 2. Verify the semi-infinite-medium approximation

The paper describes a semi-infinite medium, while the task proposes a 200 m homogeneous layer. A 200 m layer is an implementation proxy, not automatically an exact equivalent. The Agent should perform a thickness convergence check, for example by comparing 20 m, 50 m, 100 m, and 200 m, and report the smallest thickness for which the target output changes below a declared tolerance.

#### 3. Do not claim unavailable cross-model reproduction

The local registry currently declares SMRT configurations such as `rayleigh`, `iba`, `iba_original`, `dmrt_qca_shortrange`, and `dmrt_qcacp_shortrange`. DMRT-ML, DMRT-QMS, and MEMLS are reference models in the paper, but they are not automatically available merely because the paper names them. Until independent adapters or reference outputs are registered, Q2 and Q3 are only partial reproductions.

The Agent must distinguish:

- **reproduced**: the registered local model and the required comparison model both ran;
- **partial**: the local side ran, but the external reference side is unavailable;
- **blocked**: a required capability or input cannot be obtained;
- **failed**: the declared model was available but the run failed;
- **negative result**: all required runs completed and the scientific hypothesis was not supported.

It must never substitute one SMRT configuration for DMRT-ML, DMRT-QMS, or MEMLS and present that as an independent-model comparison.

#### 4. Make every “difference attribution” a controlled experiment

It is not enough to observe that two final brightness-temperature curves differ. Attribution requires a controlled comparison:

```text
same inputs, different electromagnetic formulation
same electromagnetic coefficients, different radiative-transfer solver
same theory, different microstructure
same model, different numerical resolution
```

If one of these interventions cannot be run, the conclusion must be written as “consistent with” rather than “caused by”.

#### 5. Add numerical and statistical acceptance criteria

Every sweep needs a declared comparison metric and tolerance before the result is interpreted. Examples include:

- relative deviation from the Rayleigh reference: 1%, 5%, and 10%;
- brightness-temperature bias, RMSD, and maximum absolute error;
- backscatter error in dB;
- root-finding residual and bracket status for Q4;
- DORT stream or layer-thickness convergence;
- number of failed, warning, non-finite, and nonphysical points.

The choice of tolerance is part of the research plan and must not be chosen after seeing the desired curve.

---

## Standard Problem-Solving Workflow for the Agent

This section defines the standard workflow to be used whenever a user enters a research question and expects a physical-model result, plot, and explanation. It is designed for the registered local-model architecture in this repository and for long-running research projects that may be paused and resumed.

The workflow is inspired by Microsoft ResearchStudio's idea-development loop—**read the field, find the bottleneck, choose a method, generate a proposal, check prior art, audit and revise, then render a reviewable artifact**—and by reproducible computational-research guidance. The workflow is adapted here for physical-model experiments: literature grounding and user approval happen before execution, while model capability checks, numerical diagnostics, provenance, and claim-to-result links are mandatory during and after execution.

### The core loop

```text
Research question
    ↓
0. Intake and scope check
    ↓
1. Evidence and model-capability check
    ↓
2. Formalize the question and hypotheses
    ↓
3. Generate a step-by-step research plan
    ↓
4. User review and plan revision
    ↓
5. Environment, data, and provenance lock
    ↓
6. Synthetic-data / smoke-test demonstration
    ↓
7. Baseline and validation run
    ↓
8. Main experiment or parameter sweep
    ↓
9. Diagnostics, uncertainty, and robustness checks
    ↓
10. Plot generation and evidence-linked interpretation
    ↓
11. User review, revise, and rerun if necessary
    ↓
12. Final research package and resumable state
    ↺ return to steps 2–11 when the question or evidence changes
```

This is a **workflow**, not a single linear pipeline. A pipeline describes what the computer executes. A research workflow also includes hypothesis formation, decisions, interpretation, user feedback, dead ends, and changes of scope.

### Stage 0: Intake and scope check

The Agent first decides what kind of request it received:

- a request for explanation only;
- a single model prediction;
- a parameter sensitivity or sweep;
- a comparison with another model or observation;
- a reproduction of a paper result;
- an open-ended research project.

For an executable research question, the Agent extracts or asks for:

- the scientific quantity of interest;
- the independent variable or intervention;
- the expected output: curve, map, table, scalar, or comparison;
- the target physical model or acceptable model family;
- fixed conditions and uncertain conditions;
- the reference paper, dataset, or observation if one exists;
- the desired accuracy, compute budget, and output language.

If a missing item can change the interpretation, the Agent asks the user before running. If it is scientifically harmless, it may choose a declared default and record it.

**Gate 0:** The request is either executable, requires user clarification, or is explicitly marked as unsupported. No model run occurs before this gate passes.

### Stage 1: Evidence and registered-model capability check

The Agent gathers the minimum evidence needed to choose a defensible method:

1. read the relevant reference paper or local knowledge section;
2. identify equations, parameter definitions, units, and reported validity ranges;
3. identify the reference result or figure to reproduce;
4. list registered local models with `list_models`;
5. match the requested observable and sweep to the model card's declared parameters and outputs;
6. check whether comparison models, observational data, or external software are actually available;
7. identify contradictions between the paper, task file, model card, and user request.

The model registry is the authority for what the Agent can execute. The language model must not invent a model capability from a name in a paper.

**Output:** an evidence bundle containing sources, citations, model-card identifiers, capability gaps, and unresolved ambiguities.

**Gate 1:** Every planned run has a registered implementation or is marked as an explicit external dependency. Unsupported comparisons are blocked or downgraded to partial reproduction.

### Stage 2: Formalize the scientific question

The Agent rewrites the natural-language question into a compact experiment specification:

| Field | Required content |
|---|---|
| Question | One falsifiable or measurable question |
| Hypothesis | Expected relationship, convergence, difference, or failure |
| Quantity of interest | Exact model output and units |
| Intervention | Parameter or model choice being changed |
| Controls | Conditions held constant |
| Comparison | Baseline, reference model, observation, or null expectation |
| Acceptance metric | Bias, RMSD, relative error, threshold, residual, or convergence criterion |
| Validity limits | Conditions under which the claim is allowed |
| Stop condition | When to stop, ask the user, or mark the run blocked |

For example, “Does density affect scattering?” is not yet executable. A formal version is: “At 37 GHz and radius 100 µm, how does the scattering coefficient (k_s) vary from 1 to 96 kg m−3 under Rayleigh, IBA, and DMRT QCA-CP, and at what density does each result first deviate from the Rayleigh low-density reference by 5%?”

The Agent should separate:

- **exploration hypotheses**: useful expectations that may change;
- **confirmatory criteria**: thresholds and comparisons fixed before the main run;
- **post-hoc observations**: patterns noticed after execution, which must not be presented as pre-registered predictions.

**Gate 2:** A human can tell what will be varied, what will be measured, and what would count as agreement or disagreement.

### Stage 3: Generate the research plan

The Agent writes a plan before running the main experiment. The plan must contain:

1. a plain-language explanation of the question;
2. the formal question and hypothesis;
3. source-paper parameters and any deviations;
4. model selection and why the selected model is capable;
5. fixed parameters, swept parameters, and ranges;
6. baseline, smoke test, and main experiment;
7. expected plots and tables;
8. numerical checks and acceptance criteria;
9. uncertainty, sensitivity, and robustness tests;
10. expected failure modes and fallback options;
11. artifact locations and provenance fields;
12. explicit questions requiring user approval.

The first plan should be small enough to run a cheap pilot. The plan may contain a coarse sweep followed by a refined sweep, rather than immediately using the maximum range and resolution.

### Stage 4: User review and revision

The Agent pauses at scientifically meaningful decision points. It should ask the user to review:

- interpretation of ambiguous paper parameters;
- model choice when more than one registered model is plausible;
- the calibration observable and comparison metric;
- sweep ranges and resolution;
- whether a pseudo-data demonstration should be used;
- whether a failed external dependency should stop the project or allow a partial run;
- whether newly observed behavior should become a revised question.

The Agent should present the plan as a concise decision table, not ask the user to inspect hidden prompts. Every revision gets a version number and a reason.

**Gate 3:** No irreversible or expensive main run begins until required choices are approved or explicitly defaulted.

#### UI operating rule for plan approval

The user-facing review card follows this sequence:

```text
Review plan
  -> Approve plan (method only; no physical run)
  -> Generate pseudo-data preview (layout demonstration only)
  -> Confirm the figure package
  -> Approve formal execution
  -> Run the registered model and render figures from real outputs
```

Approving the plan does **not** approve the pseudo-data or the final figure. Pseudo-data
exist only to make axes, labels, ranges, and series layout reviewable before a model run.
They must be visibly labelled and are discarded when the figure package is confirmed or
when the plan is revised.

If the user does not agree with the pseudo-data or figure, the user should choose **Revise
plan in chat** and state the scientific change in plain language, for example:

- `Remove the optional chart and keep the required brightness-temperature chart.`
- `Change the density sweep to 10-500 kg/m3 with 12 points.`
- `Plot tb_v and tb_h against incidence angle; keep frequency fixed at 37 GHz.`

The Agent converts that request into `research_plan(action="revise_plan", changes=...)`.
The backend validates the revised runs and chart axes, increments the plan version, records
the reason in the review log, clears stale pseudo-data, and returns to **Review plan**.
The user must approve the new plan before a new preview is generated. If only the visual
layout needs another draw and the scientific plan is unchanged, the user may ask for a
preview regeneration instead; that action must not be treated as plan approval.

### Stage 5: Lock environment, inputs, and provenance

Before execution, create a run manifest containing:

- research project and plan version;
- model name and version from the registry;
- adapter and source revision;
- Python and package versions;
- operating system and relevant hardware;
- input files and checksums;
- exact resolved parameters and units;
- random seed, if randomness exists;
- timestamp and execution status;
- source-paper DOI and figure or section being reproduced.

The Agent must never rely on an informal statement such as “the default settings were used.” Defaults should be resolved into explicit values in the manifest.

### Stage 6: Synthetic-data and smoke-test demonstration

Before using expensive or uncertain real inputs, the Agent runs a small demonstration:

- use a tiny parameter grid;
- verify that the adapter accepts the planned parameters;
- check output schema, units, array lengths, finite values, and expected monotonicity where known;
- generate a preliminary plot;
- if the task is an inversion or equivalence problem, create controlled pseudo-data with a known answer;
- test that the numerical solver can recover the known answer within tolerance.

Pseudo-data are for verifying the workflow and implementation. They must never be mixed with real or paper-reproduction results without a clear label.

**Gate 4:** The model can run, outputs are structurally valid, and the planned analysis can consume them.

### Stage 7: Baseline and validation run

Every research run starts with a baseline before the full sweep:

- reproduce the paper's central or easiest configuration;
- compare the result with the paper's reported value, curve, or qualitative trend;
- run physical sanity checks;
- record differences rather than silently tuning parameters to force agreement.

Typical sanity checks for SMRT include:

- units and dimensions;
- non-negative or physically allowed coefficients;
- finite values and no unexpected NaNs;
- sensible low-density limit;
- layer-thickness convergence for a semi-infinite proxy;
- DORT stream convergence;
- consistency between passive and active output shapes;
- stable behavior when the sweep is repeated.

If the baseline fails, the Agent stops the main sweep and diagnoses the failure. It does not generate a polished conclusion from an unvalidated baseline.

### Stage 8: Main experiment

The Agent executes the approved plan using the registered model adapter. Each run should save:

- resolved input specification;
- raw model output;
- normalized tabular output;
- warnings and exceptions;
- derived metrics;
- plot data;
- execution metadata.

For parameter sweeps, the Agent should preserve the complete grid, including failed points. Missing points must not silently disappear from a plot.

For model comparisons, the Agent must align:

- units;
- angle conventions;
- frequency units;
- polarization labels;
- active/passive mode;
- boundary and substrate assumptions;
- native grids and interpolation method.

### Stage 9: Diagnostics, uncertainty, and robustness

The Agent performs checks appropriate to the question:

- numerical convergence: thickness, streams, resolution, solver tolerance;
- sensitivity: one-factor-at-a-time or local perturbations around important parameters;
- uncertainty: input ranges, measurement uncertainty, or model-form uncertainty when available;
- reproducibility: rerun the same manifest and compare outputs;
- robustness: test alternative but defensible parameterizations;
- failure analysis: identify nonphysical values, warnings, missing brackets, and solver failures.

For Q4, root existence, bracket coverage, residual, and uniqueness are not optional diagnostics; they are part of the scientific result.

### Stage 10: Generate plots and evidence-linked interpretation

The Agent generates plots from stored normalized data, never from manually copied values. Every plot should contain:

- title or caption describing the question;
- axis names and units;
- legend with model and configuration names;
- visible parameter conditions;
- uncertainty or failure markers where relevant;
- a link or identifier for the raw/derived data behind the plot.

The explanation is generated in three layers:

1. **What was run:** model, inputs, sweep, and comparison;
2. **What the results show:** observed trend, numerical metrics, and deviations;
3. **What can be concluded:** supported claim, applicability range, limitations, and unresolved issues.

Every sentence containing a number or scientific claim should point to a result artifact, metric table, plot, or source citation. The Agent must distinguish “the model produced” from “the physical world does”.

### Stage 11: User review and iterative revision

The Agent presents the plot and a short result summary, then asks whether the user wants to:

- change the question;
- refine the parameter range;
- add another model or observation;
- inspect an anomaly;
- run a robustness test;
- accept the current answer as a preliminary result.

If the plan changes, the Agent creates a new plan version and preserves the previous run. It never overwrites a prior result without recording the relationship between versions.

### Stage 12: Final research package and resumable state

The final output for one question should be a small research package, not only a prose answer:

```text
research_project/
├── question.md              # formal question, hypothesis, scope
├── plan.v001.yaml           # approved plan and decisions
├── evidence/                # papers, model cards, source excerpts
├── runs/
│   └── run-0001/
│       ├── manifest.json
│       ├── inputs.json
│       ├── raw/
│       ├── derived/
│       ├── plots/
│       ├── diagnostics.json
│       └── status.json
├── claims.json              # claim -> metric/plot/source links
├── result_summary.md        # explanation and conclusions
├── limitations.md
└── review_log.md            # user decisions and revisions
```

The next conversation should be able to load `status.json`, the latest approved plan, the last diagnostics, and the unresolved questions without replaying the entire chat history. This is how the Agent supports research lasting weeks or months.

## Minimum execution contract for a registered local model

Before the Agent calls `run_model`, the model card and the plan must jointly answer:

| Contract item | Required check |
|---|---|
| Identity | Name, version, source, adapter |
| Inputs | Parameter names, units, ranges, defaults |
| Outputs | Quantity names, units, shape, active/passive mode |
| Validity | Declared assumptions and unsupported cases |
| Reproducibility | Seed, software version, deterministic status |
| Diagnostics | Warnings, failed points, convergence information |
| Provenance | Plan version, source paper, input checksum |
| Evidence | Raw output and plot-data paths |

If a model card does not declare an output required by the question, the Agent should not infer it from an internal implementation detail. The correct behavior is to ask for a new adapter, choose another registered model, or mark the question blocked.

## How this workflow maps to the four SMRT questions

| SMRT question | Baseline gate | Main experiment | Critical diagnostics | Main conclusion boundary |
|---|---|---|---|---|
| Q1 sparse medium | Low-density Rayleigh point and coefficient schema | Density sweep across microstructures and theories | Linear-limit fit, deviation thresholds, units | Only claim a density range supported by the selected tolerance |
| Q2 DMRT comparison | Paper Figure 4 central configuration | Passive/active angular comparison and radius-stickiness sweep | Common inputs, external reference availability, solver failures | Do not call a partial local comparison a cross-model reproduction |
| Q3 MEMLS comparison | Exponential ACF and coefficient extraction | MEMLS vs `iba_original` vs default `iba` | Coefficient-level comparison and DORT convergence | Similar coefficients plus different outputs suggests, but does not by itself prove, solver causality |
| Q4 microstructure equivalence | Pseudo-data root-recovery test | Parameter mapping across densities and conditions | Brackets, residuals, uniqueness, transferability | Local calibration agreement is not general equivalence |

## References used to design this workflow

- Microsoft ResearchStudio repository: [ResearchStudio](https://github.com/microsoft/ResearchStudio). Its Idea workflow explicitly composes literature search, bottleneck identification, method/idea generation, prior-art checking, auditing, revision, and artifact rendering.
- Zhao et al. (2026), [ResearchStudio-Idea: An Evidence-Grounded Research-Ideation Skill Suite from ML Conference Outcomes](https://arxiv.org/abs/2607.04439). The paper describes an evidence-grounded loop of reconstructing context, identifying bottlenecks, generating a proposal, checking prior work, auditing, and revising.
- Stoudt, Vásquez, and Martinez (2021), [Principles for data analysis workflows](https://doi.org/10.1371/journal.pcbi.1008770). It distinguishes a nonlinear research workflow from a computer pipeline and proposes Explore, Refine, and Produce phases, with documentation and reproducibility throughout.
- Sandve et al. (2013), [Ten Simple Rules for Reproducible Computational Research](https://doi.org/10.1371/journal.pcbi.1003285). The rules emphasize tracking how every result was produced, versioning programs, recording intermediate results and seeds, storing raw data behind plots, connecting claims to results, and making scripts and runs accessible.
- Wilkinson et al. (2016), [The FAIR Guiding Principles for scientific data management and stewardship](https://doi.org/10.1038/sdata.2016.18). The FAIR principles motivate making research artifacts findable, accessible, interoperable, and reusable.

The references are used as design guidance, not as a claim that there is one universally mandatory research procedure. The workflow above is the project-specific operational standard for turning a natural-language physical-science question into a traceable local-model run and an evidence-linked result.

---

## 1. The Sparse Medium Approximation （Section 3.1.1）

### Scientific question

Under what snow-density range do 1) Rayleigh theory, 2) DMRT-QCA-CP sticky and 3) DMRT-QCA-CP non-sticky hard sphere converge to the same first-order scattering behavior, and at what density do particle correlation and dense-medium effects cause their predictions to diverge?

### Key steps using SMRT

1. **Construct the sparse-density experiment**
   - Use a frequency of 37 GHz. 
   - Fix the ice-sphere radius at \(100\,\mu\text{m}\). 
   - Vary snow density from approximately 1 to 96 kg m\(^{-3}\), preferably in 5 kg m\(^{-3}\) increments. 
   - Define independent spheres, nearly non-sticky hard spheres, and sticky hard spheres. 

2. **Calculate the electromagnetic scattering coefficients**
   - Run Rayleigh theory with independent spheres.
   - Run IBA with independent spheres.
   - Run IBA with non-sticky and sticky hard-sphere microstructures.
   - Run DMRT QCA-CP with the same hard-sphere microstructures.
   - Extract the scattering coefficient \(k_s\) without introducing radiative-transfer effects.

3. **Verify the common sparse-medium limit**
   - Plot \(k_s\) against density for every configuration.
   - Fit linear regressions over progressively larger low-density ranges.
   - Compare the fitted slopes and verify that the intercepts approach zero.
   - Confirm whether all theories converge to the Rayleigh first-order limit.

4. **Identify the breakdown density**
   - Use the Rayleigh linear solution as the sparse-medium reference.
   - Calculate the relative deviation of each IBA and DMRT result from this reference.
   - Report the densities at which the deviation first exceeds 1%, 5%, and 10%.
   - Examine how stickiness changes the onset and direction of the deviation.

5. **Attribute the observed divergence**
   - Compare IBA and DMRT using identical microstructure parameters to isolate theory differences.
   - Compare different microstructures under the same electromagnetic theory to isolate correlation effects.
   - Determine whether the divergence is predominantly caused by dense-medium corrections, the structure factor, or their interaction.

### Expected outputs

- Scattering coefficient versus density.
- Low-density linear-fit slopes and intercepts.
- Relative deviation from the Rayleigh limit.
- Estimated validity range of the sparse-medium approximation.
- Separate assessment of electromagnetic-theory and microstructure effects.

---

## 2. Comparison of SMRT to DMRT-Based Models

### Scientific question

**Can SMRT reproduce the passive brightness temperatures and active backscatter predicted by DMRT-ML and DMRT-QMS under identical snow and observation conditions, and can the remaining discrepancies be attributed to the electromagnetic formulation, the short-range approximation, or the radiative-transfer solver?**

### Key steps using SMRT

1. **Reconstruct the common reference configuration**
   - Create a homogeneous snow layer approximately 200 m thick to represent a semi-infinite medium.
   - Use a density of 300 kg m\(^{-3}\), temperature of 256 K, sphere radius of \(100\,\mu\text{m}\), and stickiness \(\tau=0.5\), matching Section 3.1.2 of the paper.
   - Use 37 GHz and incidence angles from approximately \(10^\circ\) to \(60^\circ\).
   - Match the substrate, atmosphere, dielectric model, and interface assumptions used in the reference models.

2. **Run the baseline passive and active comparisons**
   - Compare SMRT `dmrt_qcacp_shortrange` with DMRT-ML.
   - Compare SMRT `dmrt_qca_shortrange` with DMRT-QMS.
   - Calculate passive \(T_{b,V}\) and \(T_{b,H}\).
   - Calculate active \(\sigma^0_{VV}\), \(\sigma^0_{HH}\), and \(\sigma^0_{HV}\), where supported.

3. **Quantify agreement**
   - Preserve each model's native angle grid before interpolation.
   - Calculate polarization-specific bias, RMSD, and maximum absolute difference.
   - Identify the angle at which the maximum discrepancy occurs.
   - Check whether discrepancies increase toward large incidence angles or for cross-polarization.

4. **Map the validity of the short-range approximation**
   - At fixed \(\tau=0.5\), vary sphere radius over the range used in the paper.
   - At fixed radius, vary \(\tau\) from strongly sticky to nearly non-sticky conditions.
   - Compare short-range QCA, DMRT-QMS, and IBA for passive and active cases.
   - Identify parameter combinations that cause nonphysical results, warnings, or solver failure.

5. **Diagnose the source of discrepancies**
   - Save \(k_s\), \(k_a\), effective permittivity, single-scattering albedo, and phase-function information.
   - Compare electromagnetic coefficients before comparing top-of-snow observables.
   - Test DORT convergence with respect to the number of streams.
   - Where possible, prescribe common electromagnetic coefficients to separate the electromagnetic model from the radiative-transfer solver.

### Expected outputs

- Angular curves of \(T_{b,V}\), \(T_{b,H}\), and radar backscatter.
- Error statistics relative to DMRT-ML and DMRT-QMS.
- Radius-stickiness validity map for the short-range approximation.
- Records of numerical warnings and nonphysical cases.
- Attribution of discrepancies to electromagnetic or radiative-transfer components.

---

## 3. Comparison of SMRT to MEMLS-IBA

### Scientific question

**When SMRT and MEMLS use the same exponential microstructure and snowpack properties, how closely do they reproduce the same electromagnetic coefficients and brightness temperatures, and how much of their difference is caused by the IBA absorption formulation versus the DORT and six-flux radiative-transfer solvers?**

### Key steps using SMRT

1. **Create an equivalent exponential-microstructure snowpack**
   - Use a homogeneous snow layer approximately 200 m thick.
   - Set density to 300 kg m\(^{-3}\), temperature to 265 K, and frequency to 37 GHz.
   - Use an exponential correlation length of \(100\,\mu\text{m}\).
   - Evaluate incidence angles from approximately \(10^\circ\) to \(60^\circ\).
   - Match dielectric, boundary, and atmospheric assumptions between SMRT and MEMLS.

2. **Run the required model configurations**
   - Run MEMLS with its IBA exponential-correlation option.
   - Run SMRT using `iba_original` with DORT.
   - Run SMRT using the current/default `iba` implementation with DORT.
   - Use `iba_original` as the closest electromagnetic comparison with the original MEMLS-IBA formulation.

3. **Compare electromagnetic coefficients first**
   - Extract \(k_s\), \(k_a\), extinction coefficient, effective permittivity, and single-scattering albedo.
   - Compare the SMRT and MEMLS coefficients before running the full brightness-temperature comparison.
   - Determine whether differences originate in scattering, absorption, or both.

4. **Compare brightness temperatures**
   - Calculate \(T_{b,V}\) and \(T_{b,H}\) as functions of incidence angle.
   - Calculate bias, RMSD, and maximum absolute difference for each polarization.
   - Compare `iba_original` and default `iba` to quantify the effect of changes in the absorption formulation.
   - Examine whether the difference is angle- or polarization-dependent.

5. **Separate electromagnetic and solver contributions**
   - Test DORT convergence using increasing numbers of streams.
   - Where possible, run DORT with externally supplied MEMLS electromagnetic coefficients.
   - Interpret similar coefficients but different brightness temperatures as a solver-level difference.
   - Interpret differences between `iba_original` and default `iba` primarily as an absorption-formulation effect.

### Expected outputs

- Comparison of electromagnetic coefficients.
- Angular \(T_b\) curves for MEMLS, SMRT `iba_original`, and SMRT default `iba`.
- Polarization-specific error metrics.
- DORT stream-convergence assessment.
- Quantified contributions from absorption and radiative-transfer formulations.

---

## 4. On the Equivalence of Microstructure Models

### Scientific question

**Can sticky hard spheres, scaled non-sticky spheres, and exponential autocorrelation functions be parameterized to produce equivalent microwave brightness temperatures for snow with the same density and specific surface area, and is that equivalence unique and transferable across densities, frequencies, incidence angles, and polarizations?**

### Key steps using SMRT

1. **Define the operational equivalence experiment**

   - Use SMRT IBA with DORT.
   - Create a homogeneous 200 m snow layer at 265 K.
   - Use a reference sphere radius of \(100\,\mu\text{m}\).
   - Test densities of approximately 200, 250, 300, 350, and 400 kg m\(^{-3}\).
   - Initially define equivalence as matching \(T_{b,V}\) at 37 GHz and \(55^\circ\).

2. **Map scaled non-sticky spheres to equivalent stickiness**
   - Generate reference brightness temperatures using nearly non-sticky hard spheres with systematically scaled radii.
   - Return the radius to \(100\,\mu\text{m}\).
   - Numerically solve for the sticky-hard-sphere parameter \(\tau\) that reproduces each reference brightness temperature.
   - Use a sufficiently broad search interval and check that the root is bracketed.

3. **Map sticky hard spheres to the exponential microstructure**
   - Generate target brightness temperatures using sticky hard spheres over a prescribed range of \(\tau\).
   - Solve for the exponential correlation-length scaling factor \(\phi_{\exp}\).
   - Use the paper's relation

     \[
     l_{\exp}
     =
     \phi_{\exp}\frac{4}{3}
     \left(1-\frac{\rho}{917}\right)a .
     \]

   - Record the solution residual and whether multiple roots exist.

4. **Evaluate uniqueness and density dependence**
   - Repeat both mappings for every tested density.
   - Record all successful roots, missing brackets, and multiple-solution cases.
   - Determine whether a single mapping applies across densities.
   - Assess whether matching density and specific surface area is sufficient to determine microwave-equivalent microstructure.

5. **Test transferability beyond the calibration channel**
   - Re-evaluate matched parameter pairs at additional frequencies and incidence angles.
   - Test H polarization and, where supported, active VV and HH backscatter.
   - Compare \(k_s\), \(k_a\), single-scattering albedo, and phase-function moments.
   - Reject general equivalence when two models agree only at the channel used for calibration.

### Expected outputs

- Equivalent stickiness versus scaled sphere radius.
- Equivalent exponential correlation length versus stickiness.
- Density-dependent equivalence curves.
- Root residuals and uniqueness diagnostics.
- Cross-frequency, angular, polarization, and active/passive transferability tests.

---

## Suggested Agent Execution Order

1. Reproduce the sparse-medium electromagnetic-coefficient experiment.
2. Validate SMRT against DMRT-ML and DMRT-QMS.
3. Validate SMRT IBA against MEMLS-IBA.
4. Reproduce the microstructure-equivalence inversion.
5. Perform cross-configuration tests to distinguish exact reproduction from general physical equivalence.
