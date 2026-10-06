# Research plan schema (design draft, not wired in)

`research_plan.schema.json` is a JSON Schema (2020-12) for a reviewable experiment plan: what a
plan must declare before any model may run, domain-agnostic, with provenance per parameter
(`paper`, `inferred`, `assumed`), a baseline run, sensitivity runs for assumed parameters,
figures, success and stop criteria, and approval state. Sixteen rules that JSON Schema cannot
express (for example "every assumed parameter has a sensitivity run" or "runs drawn on one figure
share a sweep") are listed in its `x-validator-rules`.

**Status.** The live plan is documented in [../research-plan.md](../research-plan.md). This draft was written on 14 August 2026 as "new, intentionally dead" (see
`docs/reorganisation/audit-before-execution.html`). Nothing loads it. The plan the agent actually
produces today (`src/physearth/research/`) uses `charts`, `runs` and `reproduction_targets`, not
this schema's `figures` and `comparison`, so the two have drifted. It is kept as the intended
direction for a stricter plan contract, not as a description of the running system.

If it is wired in, it belongs in the library as package data with a small cached loader, and the
live plan format has to be reconciled with it first.
