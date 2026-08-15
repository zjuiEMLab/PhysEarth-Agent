# AGENTS.md

Working notes for anyone — human or coding agent — changing this repository. Only what is
specific to this project and not obvious from the code.

## Commands

```bash
uv sync --extra dev                  # the only supported way to build the environment
.venv/bin/python -m pytest tests -q  # full suite, ~45 s, no network, no LLM
.venv/bin/python app.py              # the Studio on PHYSEARTH_PORT (default 7860)
.venv/bin/python -m ruff check .     # line-length 100, rules E,F,I,W,UP,B
```

Evaluation, in increasing cost:

```bash
.venv/bin/python evaluation/runners/tier0.py               # deterministic, free, ~20 s
.venv/bin/python evaluation/runners/model_registration.py  # deterministic, no LLM
.venv/bin/python evaluation/runners/agent_tasks.py --dry-run
.venv/bin/python evaluation/runners/report.py              # rebuild REPORT.md from cache
```

`uv sync` matters: the venv drifts silently otherwise, and a missing `pymupdf` makes the
figure-inspection tests fail in a way that looks like a code defect but is not.

## Layout

- `app.py` — Gradio entry point. **The only file in the repository that may import
  `gradio`.** The ModelScope deployspec in the README front-matter pins this filename;
  it cannot be renamed, only reduced to a shim.
- `physearth/` — the importable package. Agent loop, tools, harness, research planning.
- `physearth/ui/` — every pixel of the interface as plain strings. Imports no Gradio, so
  it is testable without a browser.
- `physearth/models/bundled/` — six model cards and adapters. Being moved to a top-level
  user-owned `models/`; see the reorganisation note below.
- `knowledge/` — bundled CC-BY literature, method notes, reference data. Resolved from the
  package by relative path, so it must travel with any move of `physearth/`.
- `evaluation/` — task set, ablation configs, runners, and committed result records.
- `docs/` — design notes and research task documents. Not runnable.

## Invariants that are not style preferences

These are the product, not conventions. Breaking one silently is worse than a crash.

- **Numeric arrays never enter the model's context.** A run returns a handle and a bounded
  preview; the full result stays in the session store.
- **Charts come from a declarative specification** naming result handles, never from code
  the agent wrote. A measured series is never drawn like a simulated one.
- **A human approves a run before a physical model executes.** The agent has no way to
  approve on its own behalf.
- **Parameters are validated against declared physical ranges before the run**, results
  against declared bounds after it. Both come from the model card, so they apply unchanged
  to any registered model.
- **Every claim carries a marker** that resolves to a section actually opened, a model
  actually run, or a dataset actually queried. Abstract-only evidence (`[abs:doi]`) may
  never carry a value in kelvin, decibels or volumetric soil moisture.
- **Text from outside the system arrives inside a labelled boundary** and is evidence,
  never instruction.

## Evidence and evaluation

`evaluation/results/` is committed evidence behind `REPORT.md`, not build output. Do not
regenerate or delete records to make something pass. Tier 0 and the registration runner are
deterministic and must reproduce their committed JSON byte-for-byte; if they drift, that is
a real defect.

Changing prompt text or tool contracts invalidates comparisons against existing records.
Say so in the commit message.

## Configuration

All runtime configuration is environment variables with defaults in `physearth/config.py`;
`.env.example` documents them. `PHYSEARTH_ONLINE=0` closes the live-literature layer
entirely and nothing else changes. Budgets default to `0`, meaning unlimited.

Never commit `.env`. Never put a real token in a test fixture.

## Reorganisation in progress

The repository is moving to a backend/frontend split (Option C): `frontend/` for the
Gradio app and views, `backend/physearth/` for the package, with `prompts/`, `models/` and
`evaluation/` as top-level user-facing content. Phases land one commit at a time, each
green. Two invariants arrive with the frontend split and are enforced by tests:

- nothing under `backend/` may import `gradio`;
- nothing under `frontend/` may import `research`, `tools` or `agent` directly — it goes
  through `backend/physearth/api.py`.
