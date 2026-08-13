# Evaluation structure

The public evaluation uses two names that are easier for first-time reviewers to
understand:

1. **Model registration tests** — deterministic registry, adapter, demo, and replay checks.
2. **Paper reproduction results** — the planned SMRT reproduction workflow.

The directories below are internal implementation paths. They are kept stable so
task runners and historical records remain addressable.

| Internal directory | Public meaning | Current status |
| --- | --- | --- |
| `t0_registry_integrity` | Model registration tests | Completed |
| `t1_model_onboarding` | Future new-model onboarding fixture | Design only |
| `t2_paper_reconstruction` | SMRT paper reproduction | Not executed |
| `t3_independent_reproduction` | Compatibility alias for the paper oracle | Not a separate evaluation |

Independent research remains outside the competition scope.
