# Next week: to-do

Aligned with `origin/main` at `878f6a9` (2 Oct 2026). Source of truth for status is
`docs/evaluation/TRUST-PROTOCOL.md` in the repository; this file only lists what is left.

## Already done upstream (drop from the list)

- A/B/C protocol frozen and written up; every eval has a runner and a recomputed score.
- Registration runners restored (`tier0.py`, `registry_contract.py`, `model_registration.py`):
  6/6 models, 197 contract checks, 10/10 Tier 0 tasks (42 checks), 21/21 registration checks.
- Capability gate (A6) over every task: 21 tasks, 16 can, 4 partial, 1 cannot. Replaces the
  hand-written can/cannot table in the old to-do.
- Final evidence: `evaluation/results/competition/final-db4b2e1/` (26 records, `scores.json`),
  main LLM `openai/gpt-5.6-luna`, judge `openai/gpt-6-luna`, candidate cost USD 2.64.
- Plugins merged into `integrations/geoai/`; approval is an operator setting (`--approval`),
  and `geoai_verify_report` exists.
- Spend caps on by default; no-harness SMRT calls now counted in A5.

## 1. Evidence gaps (P0)

1. **PROSAIL, pyET, pywatershed are Failed because no plan cites a corpus source.** Add their
   CC-BY sources to the corpus (pywatershed: HESS 30, 5195, 2026; Zenodo 17180693; FAO-56
   Example 18; the PROSAIL tutorial) with `ingest_paper` / `scripts/build_corpus.py`, then re-run
   those three grid cells. The B3 oracles already exist, so the numeric score follows.
2. **Water cloud: gate says `cannot`, grid cell ran and scored Partial (figure 0/8).** Decide
   which is right. If the gate is right, the cell should be a correct refusal, not a figure.
3. **SMRT r2 Partial: three parameter sources unlabelled.** Fix the provenance mechanism, not
   the task or the card (see AGENTS.md "Fixing a demo means fixing the mechanism").
4. **A4: only 3 of 10 harness-on probe runs ended with an answer naming the card's limit.**
   The rest stopped on `no_progress` or answered without the limit. Mechanism fix at the final
   answer gate, then re-run the probes.
5. **Rescore A5 for the no-harness records** after `878f6a9` (Q1 r1 executed stickiness 0.0,
   card minimum 0.05); refresh `scores.json` and the status table. Rescore only; do not re-run.
6. **Comparators (B7): coding agents not run.** Claude Code and Codex on Q1, raw and then with the
   plugin, same scorer and judge, under the spend caps. Check the robustness list in
   `competition.yaml` is complete (only DeepSeek V4.1 Flash and Qwen3.8 Flash are in the table).
7. **Tier 1 figures (Fig. 4a/4b, 5, 6)** are `partial` in the gate (DMRT-ML, DMRT-QMS, MEMLS
   not registered). Either run them as partial reproductions with the scope stated, or leave them
   out of the claim. Q2 to Q4 still have no task files.

## 2. Repository (P0 before the reorganisation)

- Land the merged tree: branch `merge-origin-main` in worktree `../PhysEarth-Agent-merge`
  (rebased on `878f6a9`; one commit on top of upstream plus the decision trail). Your main checkout
  is still in a half-applied pull; it needs clearing.
- Decide on branch `smrt-repeat-distance-fix` (Teubner-Strey and Gaussian random field currently
  fail inside SMRT). It changes the SMRT card text, so it regenerates the prompt digests and
  invalidates earlier comparisons for tasks that list SMRT parameters.
- Three tests fail on plain `origin/main` here: `test_dsh_integration` (Python lookup) and two
  Tier 0 replays (`pywatershed` version is `None`). Check `uv sync --extra dev` first.
- Backups of the old working tree: `refs/backup/wip-autostash`, `refs/backup/wip-stash1`.
- Delete remote branch `claude/relaxed-pascal-twywbo`, then `git fetch --prune`.
- Reorganisation: see the plan; waiting on four decisions.

## 3. Deck and demo (P1)

- Slide numbers are stale. The deck still shows the qwen-plus pilot (figure 3/3, report 6, 6, 5
  of 10, 4 to 5 min). Replace with `final-db4b2e1`: SMRT Success r1 and r3, Partial r2; per-model
  grid; A: 197, 42 and 21 checks; A5 0 illegal calls executed in 26 records; cost USD 2.64.
  Report rubric is now v3 (8 dimensions, pass 8 of 16, factuality at least 1).
- Remove `docs/slides/TRUST-PROTOCOL.md` from the deck folder once the deck links the upstream one.
- Record the demo video to `docs/slides/deck/media/demo.mp4`; keep or replace the plugin animation.
- Rehearse with the timer (`T`); trim the results gallery before the demo if long.

## 4. Decisions needed from you

- Coding-agent comparison now (item 1.6) or Later?
- User-experience metric (C3): pick two or three measures, or leave it Later.
- Reorganisation questions: `models/` under `content/`, `src/` + `apps/` naming, root files,
  and when to start.
