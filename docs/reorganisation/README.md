# Repository reorganisation — the decision trail

Five documents, in the order they were written. They are kept because the reasoning
behind the current layout is not recoverable from the tree: the repository shows what was
decided, not what was rejected or why.

Until September 2026 these lived only in chat transcripts and published artifacts. That
turned out to be a real cost — reconstructing the Option D definition and its scoring
took an hour of digging through session logs. Hence this folder.

| Document | Written | What it is | Status |
|---|---|---|---|
| [audit-before-execution.html](audit-before-execution.html) | 14 Aug 2026 | An audit of what the running app actually touches, what was committed by accident, and what should never have shipped. Tiered by risk against a submission deadline. | **Historical.** Tier 1 and 2 were executed; `output_no_cascades/` is gone. |
| [structure-proposals.html](structure-proposals.html) | 15 Aug 2026 | Four candidate layouts — A consolidate in place, B flat audience-first, C backend/frontend split, D four-package monorepo — scored against the stated requirements. | **Historical.** Option C was chosen. |
| [option-c-vs-d.html](option-c-vs-d.html) | 15 Aug 2026 | Answers "is C wasted work if D is the target?" Contains the effort breakdown (C 6d · C-then-D 12d · straight-to-D 15d) and the **six conditions** that justify a multi-package split. | **Live reference.** The six conditions are still the test applied to any future split. |
| [option-c-plan.html](option-c-plan.html) | 15 Aug 2026 | The phased migration actually carried out: six phases, each green, ending at the present layout. | **Executed.** Complete as of Aug 2026. |
| [option-d-migration-plan.html](option-d-migration-plan.html) | 17 Sep 2026 | Option D planned in full and costed at 6.5 days, with the six conditions re-scored against the repository as it then stood. | **Proposal.** Not executed. |

## What was decided, in one paragraph

Option C — `frontend/` plus `backend/physearth/`, with `prompts/`, `models/` and
`evaluation/` lifted to the top level as content a user reads and edits. Root `app.py`
stays a shim because the ModelScope deployspec pins the filename. Option D was deferred,
not rejected on taste: it scored three "not met", three "partial" and zero "met" against
its six conditions in August, and the same three "partial" a month later.

The recurring conclusion across both D assessments is worth stating once here, because it
is the thing most likely to be re-litigated: **every partial condition points at the same
two seams — models versus agent, and data versus code.** Nothing has ever argued for
splitting `physearth-eval` into its own distribution. If a split happens, the honest shape
is two or three packages, not four.

## Reading these files

They are self-contained HTML — open one in a browser, no build step. They follow the same
convention as `docs/evaluation/`.

## Update, 3 October 2026: the minimal top-level layout

Option C's split was kept and its folders were regrouped by role, taking the repository from
15 visible top-level folders to 8: `src/physearth` (was `backend/physearth`), `apps/studio`
(was `frontend`), `catalog/` (was `knowledge/` and `models/`), `onboarding/` (was the corpus
scripts and the literature template), `integrations/` (was `plugins/`, `claude/`, `codex/` and
the old `integrations/`), plus `evaluation/`, `tests/` and `docs/` unchanged. The prompts, the
typefaces and the model templates moved inside the library as package data, so a built wheel
carries them. It is still one distribution, so none of the six Option D conditions is triggered.
The documents above describe the layout of their day and keep their old paths on purpose.

