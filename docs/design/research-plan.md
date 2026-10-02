# The research plan: current design

How a question becomes a reviewed, approved, executed and reported experiment today. Code:
`src/physearth/research/` (the stages), `src/physearth/tools/planning.py` and `tools/specs.py`
(what the agent can call), `apps/studio/views/review.py` (what the human sees). The draft
contract that may replace the plan's shape in the next round is
[research-plan-schema/](research-plan-schema/README.md); the comparison is at the end.

## Principle

The agent proposes; the harness validates; a human approves. The agent has no way to approve on
its own behalf, and no physical model runs before the plan reaches the `approved` phase. A plan
is data the agent authors, not code: runs name registered models and declared parameters, charts
are specifications over run results, and neither contains anything executable.

## Lifecycle

```
analysis -> plan_review -> plan_approved -> pseudo_preview -> chart_selected -> approved -> completed
              ^   |            (human)         (layout only)    (human picks)   (human)      (report)
              |   +-- revise_plan (agent or human), plan_version increments, review_log kept
```

| Phase | Entered by | What is true |
|---|---|---|
| `plan_review` | `research_plan(action="propose")` passes validation | The plan exists and is shown; nothing has run. |
| `plan_approved` | the human approves the plan | The parameters, runs and model choices are frozen unless revised. |
| `pseudo_preview` | preview | Axes, labels, units and series names drawn with no data, so the intended figure is confirmed before any sweep runs. |
| `chart_selected` | the human chooses or confirms the required charts | The figure package is fixed. |
| `approved` | the human approves execution | `run_planned_model` and `plot_planned_chart` may now execute. |
| `completed` | `research_plan(action="complete")` | Runs and charts are recorded; the report is written from the recorded state. |

The two user-facing review controls (primary and "satisfied with figures") are dispatched to the
right gate by `review.review_action`, so one click is never an invisible second approval.

## What the agent can call

| Tool | Actions | Purpose |
|---|---|---|
| `read_research_guideline` | `planning`, `reporting` | Read the method note before proposing or reporting. |
| `research_capability_check` | `check`, `confirm_partial`, `reject` | Can the registered models answer this? One session-wide checkpoint across every reproduction target. A partial scope must be confirmed by the user, and the confirmation records exactly what was accepted. |
| `research_plan` | `propose`, `status`, `revise_plan`, `preview`, `choose_chart`, `complete` | Submit and control the plan. |
| `run_planned_model` | by `run_id` | Execute one approved run with the exact validated parameters stored in the plan. |
| `plot_planned_chart` | `render`, `review` | Render one approved chart from every compatible successful run; `review` records the figure-quality check. |

## The plan

Created by `propose.propose`, stored at `session["research"]` as a project:
`{plan, phase, plan_version, selected_charts, pseudo, review_log, ...}`.

| Group | Fields |
|---|---|
| Intent | `question`, `objective`, `hypothesis`, `steps` |
| Evidence | `literature_evidence`, `reference_sections`, `reference_paper_sections`, `paper_conditions`, `condition_provenance` |
| Scope | `reproduction_targets` (id, label, reference_models, requested_outputs, evidence_refs, run_ids, chart_ids, status, availability_reason), `selected_models`, `capability_review`, `capability_gaps` |
| Parameters | `parameters`, `parameter_mapping` (model, paper_concept, paper_value, model_input, mapped_value, units, provenance_class, confidence, evidence_ref, rationale), `parameter_resolution` |
| Execution | `outputs`, `runs` (id, label, model, parameters, stage), `baseline_run_id` |
| Figures | `charts` (id, label, kind, x, y, ys, required, purpose, x_label, y_label), `quantities`, `controls`, `metrics`, `diagnostics` |
| Judgement | `success_criteria`, `stop_conditions`, `assumptions`, `limitations` |
| Bookkeeping | `plan_version`, `automatic_repairs`, `validation_warnings`, `revision_summary`, `approval_state` |

**Provenance vocabulary** (`research/common.py`): `paper_explicit` (high confidence),
`paper_inferred` (medium), `user_specified` (high), `backend_default` (medium, supplied by the model
card, not by evidence), `model_assumption` (low, needs review). Abstract-only evidence may not
carry a number; every claim later resolves to a section opened, a model run or a dataset queried.

**Item identity.** `runs`, `charts` and `reproduction_targets` are keyed by `id`, and
`parameter_mapping` by `(model, model_input)`. A list that contains a partial item is a patch:
matching identities update field by field (`None` deletes a key), new identities append, and
`remove: true` drops one. A list of complete items replaces the list. This lets a repair name only
what it fixes without silently losing the other runs.

## Validation on `propose`

`propose` refuses, listing every failing check at once, and the refusal carries repair hints.

| Error code | Meaning |
|---|---|
| `run_validation` | A run names no registered model, or a parameter is out of the card's declared range or combination. |
| `steps_missing` | The plan lists no steps. |
| `research_plan_validation` (`registered_model_validation`) | Reproduction metadata does not resolve against the registry. |
| `plan_quality` | A required protocol field is missing. |
| `reproduction_evidence_incomplete` | A paper-grounded plan lacks opened evidence, targets, or a parameter mapping. |
| `output_independent_sweep` | A requested output does not depend on the swept parameter. |
| `chart_axis_mismatch` | A chart's axes are not outputs or sweep parameters of the runs that feed it. |
| `question_coverage` | The runs and charts do not cover what the question asked. |

Some mismatches are repaired automatically (parameter names and units, chart axes, a missing
baseline id) and listed in `automatic_repairs` so the reviewer sees what changed.

## Revision

`revise.revise` applies changes by request, `revise_after_figure_quality` after a figure fails
review, and `revise_after_run_failures` after a run fails. Each bumps `plan_version`, writes a
`revision_summary` and appends to `review_log`. A revision after approval returns the plan to
`plan_review`.

## Protocol document

`common.protocol_document` derives a session-scoped `phys-earth/research-protocol` YAML from the
current plan for the reviewer and the run record. It is generated, never read from the corpus,
never persisted as a file, and never used as hidden instruction text.

## Against the draft schema

| Concern | Live plan | Draft (`research-plan-schema`) |
|---|---|---|
| Figures | `charts` | `figures` |
| Sources | `literature_evidence`, `reference_sections` | `sources` with `opened` and a quotable `quote` |
| Provenance classes | five (`paper_explicit` ... `backend_default`) | three (`paper`, `inferred`, `assumed`) |
| Reproduction scope | `reproduction_targets`, `capability_review` | `comparison` |
| Sensitivity of assumptions | not a plan field | `sensitivity_run_id` required per assumed parameter |
| Tolerances and reference values | in the scorer, outside the plan | `tolerance`, `reference_value.read_error` fixed at submission |
| Execution order | implicit | `execution.order`, `depends_on` |
| Identity and audit | `plan_version`, `review_log` | `plan_id`, `schema_version`, `created_at`, `authored_by`, `approval` |
| Cross-field rules | enforced in code (`propose`, `charts`, `coverage`, `evidence`) | 16 prose rules in `x-validator-rules` |

## Next round: adopting the draft

Only after the Studio page is confirmed working, and not before, because the live plan shape is
what the interface, the scorer and every recorded run depend on. Proposed order:

1. Map the live fields onto the draft and write the translation both ways, without changing
   behaviour. The five-class provenance collapses to three with `backend_default` becoming
   `assumed` plus a `source` tag, which scoring (B4) must read identically.
2. Validate every recorded plan under `evaluation/results/` against the schema and list the
   failures. Those failures are the real gap, not the table above.
3. Decide which of the sixteen `x-validator-rules` are already enforced in code and which are
   new (sensitivity runs and pre-registered tolerances are new).
4. Ship the schema as package data with a cached loader, validate on `propose`, and keep the
   code checks for what JSON Schema cannot express.

Changing the plan's shape changes prompt text and tool contracts, so it invalidates comparisons
against existing evaluation records; the commit must say so.
