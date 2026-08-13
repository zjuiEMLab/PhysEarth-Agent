# T0 — Registry integrity

Deterministic, no-LLM checks for manifest discovery, schema validation, every declared
range/enum/combination/sweep guard, output shape, physical identities and reference values.
The executable task suite is in `evaluation/tasks/tier0`.

Run `evaluation/runners/registry_contract.py` first for exhaustive registration coverage.
Then run `evaluation/runners/tier0.py` for adapter/upstream agreement, physical identities
and full-array replay. Both result schemas explicitly report zero LLM calls and N/A
token/cost fields.

Competition status: **required**.
