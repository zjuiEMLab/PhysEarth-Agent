# Evaluation

Everything needed to reproduce the evaluation evidence is in this directory, and the
records themselves are committed under `results/`. Nothing is hidden behind a notebook, a
service or a private dataset. What each evaluation measures, and its current status, is in
[`docs/evaluation/TRUST-PROTOCOL.md`](../docs/evaluation/TRUST-PROTOCOL.md).

```
competition.yaml  the frozen evaluation: tasks, configurations, LLMs, repeats, judge
tasks/tier0/      deterministic model checks, no language model involved
tasks/tier1/      further figures of the SMRT paper
tasks/tier2/      one reproduction task per registered model
tasks/probe/      false-premise and underspecified questions
tiers/            capability tiers: what each dimension claims, and from which tasks
demos/            UI-only overlays that reference tier2 task IDs
configs/          full (the deployed Studio) and no-harness (the direct-LLM baseline)
prompts/          the declared prompt profiles a run is tagged with
fixtures/         reference fixtures and reference images, one per reproduction task
standards/        the figure and report judge standards, human-editable
runners/          the scripts below
metrics/          scoring: score.py, competition_score.py, figure3.py, judge.py, ...
results/          committed records: the deterministic runners' JSON and competition/
```

## Running it

In increasing cost; run from the repository root with the project environment:

```bash
python evaluation/runners/registry_contract.py   # model card contract, no LLM, <1 s
python evaluation/runners/tier0.py               # adapter truth, no LLM, ~20 s
python evaluation/runners/model_registration.py  # registration and guards, no LLM
python evaluation/runners/capability_gate.py     # can/cannot per task, no LLM
python evaluation/runners/competition.py         # the frozen matrix: plan only
python evaluation/runners/score_runs.py DIR      # rescore a record directory, no LLM
```

`competition.py` calls an LLM only with `--execute`, and runs a paid batch only with
`--approve-batch` after the plan it prints has been approved. `--grid` runs one
reproduction task per registered model instead of the matrix; `--tasks`, `--configs`,
`--llm` and `--repeats` narrow or extend a batch; `--max-spend-usd` stops it before the next
cell once its candidate cost reaches the limit. Each cell is cached under
`results/competition/runs/` and never overwritten, so a later run adds repeats rather than
replacing them. `score_runs.py` recomputes every score from the records and writes
`scores.json` beside them. `build_references.py` rebuilds the upstream oracles under
`results/competition/oracles/`; `rejudge_q1_records.py` re-applies the judge to stored Q1
records. `agent_tasks.py` is the older per-config ablation runner (`--dry-run` shows its
plan).

The registry contract, Tier 0 and the registration runner are deterministic in what they
assert. Tier 0 and the registration runner do not reproduce their JSON byte for byte:
library round-off shifts values by 1e-16 to 1e-11, so a verification run leaves
`results/tier0.json` and `results/model_registration.json` modified with drift that should
not be committed.

## `tasks/` and `tiers/` are two different things

They are easy to confuse, and the numbers deliberately do not line up.

**`tasks/<suite>/`** is storage. A suite is a folder of task definitions, loaded by
`common.load_tasks("tier2")`. The suite name is part of how a task is found.

**`tiers/t*/`** is a claim. Each manifest declares what a capability dimension asserts,
which runners produce the evidence for it, and which tasks it draws on — and it draws
across suites. `t2_paper_reconstruction` claims `t1-smrt-fig4-passive`, which lives in
`tasks/tier1/`, together with probes from `tasks/probe/`.

So a tier is not a suite with a different name, and merging the two would collapse a
scoring dimension into a directory listing. `t3_independent_reproduction` is the one
exception: its manifest declares itself a `compatibility_alias` for t2, kept so existing
links resolve.

`tasks/tier2/` is the single source of truth for the reproduction tasks, one per registered model.
The files under `demos/` contain only beginner-facing titles, summaries and button labels;
the UI joins them to the canonical task by `task_id`. Figure pilots in `tier1`, deterministic
checks in `tier0`, and adversarial probes remain separate because they have different scoring
purposes. Historical task IDs are retained as `legacy_id` aliases for audit records, but they
are not separate task definitions.

## The two configurations

| config | what it is |
| --- | --- |
| `full` | everything on; this is what the deployed Studio runs |
| `no-harness` | the direct-LLM baseline: raw publisher PDF pages, a raw upstream-SMRT recipe tool and `plot`; no structured corpus, model cards, planning, validation or evidence gates |

A configuration is a value in a YAML file, not an edit to the code. The switches reach
the agent as an argument from the process that started the run; they are never reachable
from a prompt or a tool call, and `apps/studio/studio.py` never passes them, so the deployed
application always runs with everything on.

## Why the metrics are recomputed

Every metric is recomputed from the recorded run by `metrics/score.py`,
never read off what the harness decided at the time. A call counts as illegal if the model
card says so, whether or not the harness was switched on to notice it. A citation marker
counts as resolved if the run actually gathered the evidence it names, whether or not the
citation gate was there to check. Scoring a run by its own configuration's verdict would
make every configuration look perfect, which is the one result an ablation must not be
able to produce.

The numeric comparison against a reference configuration needs the same care and gets it differently. It
does not compare the agent's curve with the fully specified reference configuration,
because that would measure the fields the paper never states: for Figure 6 the paper fixes
the theory, the microstructure and the correlation length but not the snow depth, and over
a vacuum background depth moves brightness temperature by more than a hundred kelvin. The
target is instead the agent's own configuration with the graded fields corrected, so the
number reports the cost of the mistakes the task is actually about.
