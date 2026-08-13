# Evaluation

Everything needed to reproduce the numbers in [REPORT.md](REPORT.md) and to run the
two-day competition evaluation is in this directory. Nothing is hidden behind a notebook,
a service or a private dataset.

```text
evaluation/
|-- competition.yaml                 # frozen two-day matrix
|-- prompts/                         # P0 / P1 / P3 research-plan treatments
|-- provenance/
|   |-- schema.json                  # six allowed source kinds
|   `-- gold_fields.yaml             # field-level source/value gold
|-- tiers/
|   |-- t0_registry_integrity/       # REQUIRED
|   |-- t1_model_onboarding/         # optional/design-only
|   |-- t2_paper_reconstruction/     # REQUIRED; scientific-question demos
|   `-- t3_independent_reproduction/ # compatibility alias only
|-- tasks/{tier0,tier2,probe}/        # executable task bank
|-- configs/                         # legacy ablation conditions
|-- runners/
|   |-- registry_contract.py         # registration schema + guard checks
|   |-- tier0.py                     # deterministic, no LLM
|   |-- llm_smoke.py                 # provider discovery + one explicit smoke call
|   |-- competition.py               # workflow-faithful factorial runner
|   |-- dashboard.py                 # scorer + interactive HTML
|   |-- agent_tasks.py               # legacy ablation runner
|   `-- report.py                    # legacy report
|-- metrics/{score,competition_score,oracles}.py
`-- results/competition/             # cached runs, scores, dashboard
```

The capability taxonomy is fixed: Tier 0 checks registered models and deterministic physics;
Tier 1 is new-model onboarding; Tier 2 is LLM-assisted scientific-question demonstration
for paper-grounded research. Independent upstream-package agreement is a Tier 2 metric when
a fixed oracle is explicitly approved, not a fourth capability tier. Open-ended independent
research remains outside the competition scope.

## Running it

```bash
python evaluation/runners/registry_contract.py        # free registration-contract checks
python evaluation/runners/tier0.py                    # free numeric/adapter checks, ~20 s
python evaluation/runners/llm_smoke.py                 # provider/model discovery; no inference
python evaluation/runners/llm_smoke.py --execute       # one small OpenRouter completion
python evaluation/runners/competition.py              # print frozen plan; no LLM calls
python evaluation/runners/competition.py --execute    # explicitly run pending cells
python evaluation/runners/dashboard.py                # score cache + write HTML dashboard
python evaluation/runners/agent_tasks.py --dry-run    # show the plan and the cache state
python evaluation/runners/agent_tasks.py --repeats 3  # needs MODELSCOPE_TOKEN
python evaluation/runners/report.py                   # rebuild REPORT.md from the cache
```

`agent_tasks.py` writes one file per run under `results/runs/` and skips any run whose
file already exists. The free inference quota is counted per model and per day, so the
cache is what makes the report rebuildable without paying for it twice. `--force`
overrides it, `--tasks` and `--configs` narrow it, `--llm` picks another model from the
catalogue.

`competition.py` is the workflow-faithful path. It enables the same `research_required`
gate as the application, records the LLM-authored plan, scripts an accept-without-editing
human review, requires exact `run_planned_model` / `plot_planned_chart` calls, and stores
pilot quality review plus the final parameter-provenance appendix. Its default is plan-only;
paid inference requires the explicit `--execute` flag. False-premise probes are the one
intentional exception: they may terminate safely before planning and must never execute an
impossible physical configuration.

The frozen Tier 2 main matrix uses four OpenRouter models, four scientific-question demos plus
one safety-boundary probe, three research-plan prompt profiles and two repeats: 120 cells.
Each record stores billable prompt/completion tokens, provider-reported USD cost and per-call
latency. A separate 15-cell, single-repeat
ModelScope provider-diversity track uses `Shanghai_AI_Laboratory/Intern-S2-Preview` on the
same task × prompt scenarios; it is shown alongside the main matrix but excluded from the
four-model ranking.

## The three tiers

**Tier 0** has two deterministic parts. Registry contract checks exercise every numeric
minimum/maximum, enum, combination rule and sweep contract for all six registered models.
Nine adapter tasks then test upstream-package agreement, published values, closed-form
identities, physically fixed sweep directions, output quality and full-array replay. Tier 0
makes zero LLM calls; tokens and cost are N/A rather than zero-valued performance metrics.

**Tier 1** measures onboarding of a previously unseen physical model: model card, adapter,
validation, minimal run, output contract and registry discovery. `examples/toy_model` is the
public fixture; hidden mutation cases remain design-only for this competition window.

**Tier 2** asks the agent to turn four existing SMRT scientific questions into bounded,
reviewed demonstrations through the research workflow. The tasks live under `tasks/tier2`;
their historical `t1-*` IDs are retained so committed raw records remain addressable, while
the task filenames now identify the four questions. These demos do not regenerate four fixed
paper figures and do not use a digitized-figure oracle. They assess source linkage, legal
configuration, pilot execution, limitation reporting, and whether unavailable external models
are kept separate from local SMRT runs. Safety and underspecification probes live in
`tasks/probe`.


**The supplemental probe set** is where the safety ablations separate. Its questions carry a false
premise: a snow density above solid ice, a theory paired with a microstructure it has no
derivation for, a liquid-water dielectric model asked about frozen ground, a fitted
operator asked outside the angles it was fitted over, and two models asked which is more
sensitive when one answers in kelvin and the other in decibels. Two are underspecified.
One puts a model run next to a measurement in the same chart.

## The four configurations

| config | what is removed |
| --- | --- |
| `full` | nothing; this is what the deployed Studio runs |
| `no-harness` | domain validation before a call, and the evidence and citation gates after the answer |
| `no-capability` | the declared ranges, enums, defaults and legal combinations, from the prompt and from `list_models` |
| `no-literature` | the corpus: both literature tools, the catalogue, the method notes and the literature marker |

An ablation is a value in a YAML file, not an edit to the code. `physearth/switches.py`
resolves it, and the switch reaches the agent as an argument from the process that started
the run. It is never reachable from a prompt or a tool call, and `app.py` never passes
one, so the deployed application always runs with everything on.

## Why the metrics are recomputed

Every metric in the report is recomputed from the recorded run by `metrics/score.py`,
never read off what the harness decided at the time. A call counts as illegal if the model
card says so, whether or not the harness was switched on to notice it. A citation marker
counts as resolved if the run actually gathered the evidence it names, whether or not the
citation gate was there to check. Scoring a run by its own configuration's verdict would
make every configuration look perfect, which is the one result an ablation must not be
able to produce.

Fixed-figure numeric error is not reported for these scientific-question demos. A future
fixed experiment may add an independent numeric oracle as a separate task version, but it
must not be inferred from a pilot or from an old cached fixed-figure run.
