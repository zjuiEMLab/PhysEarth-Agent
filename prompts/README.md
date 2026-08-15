# prompts/

What the agent is told, before it is told anything about your question.

Every file here is plain text. Edit one and the change takes effect on the next turn —
there is no build step and no Python to open. What you must not do casually is edit one
and then compare against the numbers in `evaluation/REPORT.md`: those runs were produced
against the wording as it stands, and changing it invalidates the comparison. The suite
will tell you, loudly, in `tests/test_prompt_layers.py`.

## The levels

The prompt is a stack. Lower levels change almost never; higher ones change per turn.

| Level | What it is | Where it lives | Changes |
|---|---|---|---|
| **L0** identity | who the agent is, and how it writes | `00-role.md`, `01-style.md` | almost never |
| **L1** policy | citation rules, evidence tiers, the untrusted-text boundary, the online layer | `10-citations.md`, `11-abstract-only.md`, `12-online.md`, `13-citations-no-corpus.md` | with a scientific decision |
| **L2** workflow | explore → plan → approve → run → report, and the triggers that open a method note | `20-workflow.md`, `21-research.md`, `22-triggers.md`, `23-workflow-no-corpus.md` | with a UX decision |
| **L3** context | the registered models, the reference datasets, the corpus catalogue, the run status | generated per turn in `backend/physearth/prompt.py` | every turn |
| **L4** methods | the three method notes the agent opens before acting | `knowledge/skills/` | per method |
| **L5** profiles | per-experiment instructions for the robustness study | `evaluation/prompts/*.yaml` | per experiment |

**L3 is not a file** and cannot be: it is different on every call. It is the only part of
the prompt still written in Python, and that is deliberate — `models_section` renders what
the registry actually holds, so a newly registered model appears in the prompt without
anyone editing it.

**L4 and L5 are not in this directory**, and the table says where they are rather than
moving them here, because both would be misfiled:

- The method notes in `knowledge/skills/` are *evidence*, not prompt text. The agent opens
  them with a tool and cites them with `[skill:slug]`, and the marker resolves only for a
  note it actually read. Only a listing of them reaches the prompt. They belong with the
  corpus, beside the papers that work the same way.
- The profiles in `evaluation/prompts/` are experiment configuration. `competition.yaml`
  names them, and the evaluation runners load them directly. Moving them here would split
  one experiment's configuration across two trees.

## Which blocks are in play

Not every block is sent every turn. The ablation switches decide, in `prompt.build`:

- **literature off** — the corpus catalogue, the method-note listing and `20-workflow.md`
  drop out; `23-workflow-no-corpus.md` and `13-citations-no-corpus.md` take their place,
  and `read_literature` is rewritten out of the research workflow.
- **capability off** — the registered-model table still appears, but without the declared
  parameter ranges and legal combinations.
- **online layer available** — `12-online.md` is appended, and `11-abstract-only.md` is
  spliced into the citation rules, because `[abs:doi]` only exists when a search can
  return one.

Forty-eight combinations of those switches, the online layer and the session state are
pinned by digest in `tests/fixtures/prompts/digests.json`.

## Changing something here

1. Edit the file.
2. Run `.venv/bin/python -m pytest tests/test_prompt_layers.py` and expect it to fail —
   that is the test doing its job.
3. Read the failure. It names every case whose prompt moved.
4. If the change is what you meant, regenerate:
   `PHYSEARTH_UPDATE_PROMPT_FIXTURES=1 .venv/bin/python -m pytest tests/test_prompt_layers.py`
5. Say in the commit message that the prompt changed, so the next person reading
   `REPORT.md` knows the records above that commit and below it are not comparable.
