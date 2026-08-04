# Evaluation

Everything needed to reproduce the numbers in [REPORT.md](REPORT.md) is in this
directory. Nothing is hidden behind a notebook, a service or a private dataset.

```
tasks/tier0/   deterministic model checks, no language model involved
tasks/tier1/   figures of the SMRT paper, reproduced through the agent
tasks/probe/   questions built to separate the ablations
configs/       the four ablation configurations
runners/       tier0.py, agent_tasks.py, report.py
metrics/       identities.py, score.py
results/       tier0.json and one JSON record per agent run
```

## Running it

```bash
python evaluation/runners/tier0.py                    # free, deterministic, ~20 s
python evaluation/runners/agent_tasks.py --dry-run    # show the plan and the cache state
python evaluation/runners/agent_tasks.py --repeats 3  # needs MODELSCOPE_TOKEN
python evaluation/runners/report.py                   # rebuild REPORT.md from the cache
```

`agent_tasks.py` writes one file per run under `results/runs/` and skips any run whose
file already exists. The free inference quota is counted per model and per day, so the
cache is what makes the report rebuildable without paying for it twice. `--force`
overrides it, `--tasks` and `--configs` narrow it, `--llm` picks another model from the
catalogue.

## The three tiers

**Tier 0** asks whether the bundled model still computes what it computed before. The
three SMRT tasks drive the upstream `smrt` package directly with the recipe from its own
documentation and require the adapter to agree to nine decimal places, so a change in the
adapter that alters the physics fails here rather than showing up as a puzzling number
somewhere downstream. The other two tasks check closed-form identities that hold whatever
is underneath: with no canopy, tau-omega must collapse to the soil temperature times the
emissivity it reports, and with no vegetation water the water cloud model must equal its
soil law exactly. Sweep directions are asserted only where physics fixes them; the
direction of the density sweep is deliberately left unasserted because at a fixed
correlation length it is not monotonic, and pinning it would be pinning an artefact.

**Tier 1** takes four figures from the SMRT paper (Picard, Sandells and Löwe, GMD 11,
2763, 2018), which is in the bundled corpus, and asks the agent to reproduce them from a
natural-language question. The paper states its configurations more completely than any
other source in the corpus, which is what makes it the first real test of whether the
agent can configure a physical model rather than talk about one. Only the fields the
paper actually fixes are graded.

**The probe set** is where the ablations separate. Five of its questions carry a false
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

The numeric column in the Tier 1 table needs the same care and gets it differently. It
does not compare the agent's curve with the fully specified reference configuration,
because that would measure the fields the paper never states: for Figure 6 the paper fixes
the theory, the microstructure and the correlation length but not the snow depth, and over
a vacuum background depth moves brightness temperature by more than a hundred kelvin. The
target is instead the agent's own configuration with the graded fields corrected, so the
number reports the cost of the mistakes the task is actually about.
