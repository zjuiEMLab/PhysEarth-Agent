# Archived tests

These tests exercise evaluation runners and result files that were removed from the tree
in commit `35eee2c` ("update evaluation dashboard"):

- `evaluation/runners/registration_demo.py`, `dashboard.py`, `llm_smoke.py`,
  `llm_robustness.py`, `reproduction_eval.py`;
- `evaluation/results/registration_demo.json`, `llm_robustness.json`.

`tier0.py`, `model_registration.py` and `registry_contract.py` were restored with their
result files, and their tests moved to `tests/test_tier0_evaluation.py`.

They are not collected (`tests/conftest.py`). Each test is kept unchanged apart from the
repository-root path, so it can be moved back into `tests/` when its runner is restored
with `git checkout 35eee2c~1 -- <runner>` and its result file regenerated. A test whose
runner is retired for good should be deleted with it rather than left here.
