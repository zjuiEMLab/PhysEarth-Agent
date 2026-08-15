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

- `app.py` — a shim. The ModelScope deployspec in the README front-matter pins this
  filename, so it stays at the root; everything it does lives in `frontend/studio.py`.
- `frontend/` — everything the visitor sees. `studio.py` is the Gradio wiring, `views/`
  is every pixel of the interface as plain strings, `static/` holds `ui.css` and `ui.js`,
  `theme.py` assembles the stylesheet. `views/` imports no Gradio, so it is testable
  without a browser.
- `backend/physearth/` — the importable package. Agent loop, tools, harness, research planning.
- `backend/physearth/api.py` — the declared surface between the two. The frontend imports this
  and nothing else from the package.
- `assets/` — shared, not frontend. `fonts/` is read by `frontend/theme.py` *and* by
  `backend/physearth/plotting.py`, which registers the same faces with matplotlib so a rendered
  figure carries the interface's type. `evaluation/` holds the architecture diagram
  `backend/physearth/evals.py` reads.
- `backend/physearth/models/bundled/` — six model cards and adapters. Being moved to a top-level
  user-owned `models/`; see the reorganisation note below.
- `knowledge/` — bundled CC-BY literature, method notes, reference data. Not part of the
  distribution: the package finds it through `backend/physearth/paths.py`, which walks up
  for a directory holding both `knowledge/` and `evaluation/`, or takes `PHYSEARTH_ROOT`.
  Never reach for it with `Path(__file__).parent.parent` again — that is what made these
  constants fail silently, as an empty corpus rather than an error.
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

All runtime configuration is environment variables with defaults in `backend/physearth/config.py`;
`.env.example` documents them. `PHYSEARTH_ONLINE=0` closes the live-literature layer
entirely and nothing else changes. Budgets default to `0`, meaning unlimited.

Never commit `.env`. Never put a real token in a test fixture.

## Reorganisation in progress

The repository is moving to a backend/frontend split (Option C). Phases land one commit at
a time, each green. Done: the four oversized modules split into packages, the frontend
lifted out, and the package moved under `backend/`. Still to come: prompts become levelled
files under `prompts/`, and `models/` and `evaluation/` are consolidated as top-level
user-facing content.

The wheel ships `physearth/` only. `knowledge/`, `evaluation/`, `assets/` and `frontend/`
stay in the repository, so an installed distribution needs `PHYSEARTH_ROOT` pointing at a
checkout. Verify a packaging change by building and importing from a clean venv with a
neutral working directory — from the repository root, `.` is on `sys.path` and hides the
difference.

Three invariants are enforced by `tests/test_boundaries.py`:

- nothing under `backend/` may import `gradio`;
- nothing under `frontend/` may import anything from the package except `physearth.api`;
- `app.py` exists at the root and delegates to `frontend.studio`.

`physearth/api.py` declares the boundary rather than narrowing it: the interface uses 62
names across 14 modules, and reducing that is separate work from moving the files. What it
buys now is that the coupling is in one place and cannot grow by accident.
