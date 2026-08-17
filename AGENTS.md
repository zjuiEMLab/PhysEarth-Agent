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
- `backend/physearth/` — the importable package, grouped by concern:
  `agent/` the loop, `tools/` what the agent may call, `research/` planning and review,
  `harness/` the guarantees (validation, approval, audit, budget, untrusted, results,
  switches, gates), `corpus/` what may be read (knowledge, live, reference, model
  guidelines), `registry/` how a model is loaded and refused, `ingest/` fetching and
  parsing sources. What is left at the top level is genuinely cross-cutting: `config.py`,
  `session.py`, `paths.py`, `plotting.py`, `api.py`.
- `backend/physearth/api.py` — the declared surface between the two. The frontend imports this
  and nothing else from the package.
- `frontend/views/evaluation.py` — renders the committed evidence under `evaluation/` for
  the Evaluation tab. It is a view, not agent code; it was `physearth.evals` and was the
  package's only dependency on the `evaluation/` tree. Not to be confused with
  `backend/physearth/evaluation.py`, the session-scoped upload-and-test workbench.
- `assets/` — shared, not frontend. `fonts/` is read by `frontend/theme.py` *and* by
  `backend/physearth/plotting.py`, which registers the same faces with matplotlib so a rendered
  figure carries the interface's type. `evaluation/` holds the architecture diagram
  `backend/physearth/evals.py` reads.
- `models/` — the registered models, as content rather than code: `bundled/` (the six
  that ship), `examples/`, a copyable `TEMPLATE/`, and `CONTRACT.md`. Outside the package
  on purpose, so an operator's own model registers by the same mechanism the bundled six
  use. The loader stays in `backend/physearth/models/`.
- `knowledge/` — bundled CC-BY literature, method notes, reference data. Not part of the
  distribution: the package finds it through `backend/physearth/paths.py`, which walks up
  for a directory holding both `knowledge/` and `evaluation/`, or takes `PHYSEARTH_ROOT`.
  Never reach for it with `Path(__file__).parent.parent` again — that is what made these
  constants fail silently, as an empty corpus rather than an error.
- `prompts/` — what the agent is told, one file per block, levelled L0–L2. Plain text, no
  build step. `prompts/README.md` explains the stack and where L3–L5 live.
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

## Fixing a demo means fixing the mechanism

A demo is a test of the system, not a thing to be satisfied. So when a demo fails, do not
write what it needs into a script, a model card, a literature card or a task file. Ask
what general fact the system was missing, record that fact where it belongs, and let the
demo pass as a consequence.

The difference is concrete. Figure 4 of the SMRT paper compares against DMRT-ML and
DMRT-QMS; figure 5 uses SMRT IBA. The wrong fix is to list those names on the paper's card
as models to look out for, or to add the outputs one SMRT figure happens to plot: that
makes the corpus assert a conclusion, and the next figure or the next paper is wrong
again. The right fix is to record what each figure *is* -- its title, axes, legend, labels,
extracted from the figure itself -- and let the registry decide which of those names it can
answer. One is a note about a demo; the other is a fact about a figure, and everything
downstream can use it.

Practical tests before adding data or a branch:

- Would this still be true for a paper nobody has run yet, or a model nobody has
  registered? If not, it is demo knowledge in disguise.
- Is it a *description* of something (what a figure shows, what a card declares) or a
  *verdict* about it (which models are unsupported, which values are expected)? Prefer the
  description; let the verdict be computed.
- Could it be extracted rather than typed? `scripts/extract_figure_metadata.py` reads
  axes and legends out of the figures; that is preferable to a human writing them in,
  because it stays true when the corpus changes.
- Does a name resolve through a declaration, or through a list of special cases? Model
  identity comes from the registry and the cards, never from a hardcoded alias table --
  the last one of those, `model_names`, was removed for exactly this reason.

Failing to find a general fix is worth saying out loud. A demo that needs a special case
is telling you the model of the problem is wrong, and that is more useful than a green
demo.

## Evidence and evaluation

`evaluation/results/` is committed evidence behind `REPORT.md`, not build output. Do not
regenerate or delete records to make something pass. Tier 0 and the registration runner are deterministic
in what they *assert*: `9/9 tasks, 38 checks` and `20/20 checks`. Those are the gate.
They do **not** reproduce their committed JSON byte-for-byte — re-running them shifts
values by 1e-16 to 1e-11 through BLAS and library round-off, which is why a verification
run leaves `results/tier0.json` and `results/model_registration.json` modified. Revert
them; do not commit the drift.

Changing prompt text or tool contracts invalidates comparisons against existing records.
Say so in the commit message. `tests/test_prompt_layers.py` pins all 48 combinations of
the ablation switches, the online layer and the session state by digest, so an accidental
change fails loudly; a deliberate one is regenerated with
`PHYSEARTH_UPDATE_PROMPT_FIXTURES=1`.

## Configuration

All runtime configuration is environment variables with defaults in `backend/physearth/config.py`;
`.env.example` documents them. `PHYSEARTH_ONLINE=0` closes the live-literature layer
entirely and nothing else changes. Budgets default to `0`, meaning unlimited.

Never commit `.env`. Never put a real token in a test fixture.

## Reorganisation in progress

The reorganisation to a backend/frontend split (Option C) is complete, in six commits,
each green: the four oversized modules split into packages, the frontend lifted out, the
package moved under `backend/`, the prompt text levelled into `prompts/`, and the models
lifted into `models/`.

The wheel ships `physearth/` only — no models and no corpus, and since the evaluation
view moved to the frontend, no dependency on the `evaluation/` tree either. `knowledge/`,
`models/`, `prompts/`, `evaluation/`, `assets/` and `frontend/` stay in the repository, so
an installed distribution needs `PHYSEARTH_ROOT` pointing at a
checkout. Verify a packaging change by building and importing from a clean venv with a
neutral working directory — from the repository root, `.` is on `sys.path` and hides the
difference.

Three invariants are enforced by `tests/test_boundaries.py`:

- nothing under `backend/` may import `gradio`;
- nothing under `frontend/` may import anything from the package except `physearth.api`;
- `app.py` exists at the root and delegates to `frontend.studio`.

`backend/physearth/api.py` declares the boundary rather than narrowing it: the interface
uses 62 names across 14 modules, and reducing that is separate work from moving the files.
What it buys now is that the coupling is in one place and cannot grow by accident.

Two names that look alike and are not:

- `models/` (top level) is **content** — the cards and adapters, read and copied by users.
- `backend/physearth/registry/` is the **mechanism** — what counts as a model, how a card
  is validated, and how a bad one is refused. It was called `physearth/models/` until the
  collision with the top-level directory became actively confusing.

The remaining `sys.path.insert` calls in `evaluation/` exist because `evaluation/runners/`
is not a package; the runners import each other as top-level modules. Making it one is the
last piece of tidying and would change how each runner is invoked directly.
