# PhysEarth-Agent — competition slide plan (handoff)

Prepared 2026-10-01 for the Open Source GeoAI Practice challenge (ModelScope; IEEE AP-GARSS 2026,
organizers = judges: UCAS, Tsinghua, AIR-CAS, ModelScope). Talk: **12 minutes, English.**
Main LLM and baseline: **Qwen**; robustness: latest **DeepSeek, GLM, GPT-5.5**.

Tags: **[Done]** works and is evidenced today · **[1 wk]** to finish within one week ·
**[Later]** roadmap only. Never present a [1 wk] item as done.

Current deck (v1 audit version, 20 slides, to be rebuilt as below):
https://claude.ai/artifact/B7qigZGqvdKa5RFHnoEaJP — its source is in `deck-source/`.
Drop the audit and reviewer-question slides; keep the agent-loop slide (`loop.html`).

---

## Outline v5 (12 min)

### 1. GeoAI agents meet physical models (1 min)
- Today's GeoAI **agents** are data- and tool-driven:
  - perception agents (RS-Agent, ThinkGeo) call trained networks, e.g. SAR to flood extent;
  - code agents (GeoAgent, EE Genie) write code.
- Code agents are brittle: on UnivEARTH, accuracy is 40% and the code fails to run in over 44%
  of cases.
- PhysEarth-Agent is an agent for **physics-based models**: radiative transfer, hydrology and
  land surface models, which encode processes rather than learn them from data.
- The question is not whether an agent can call a model, but whether its run can be trusted.
- Physical models fail silently: snow denser than ice still yields a plausible curve. [Done, `problem.html`]

### 2. Goal and contribution (1.5 min) — rebuild the user's comparison slide with three columns
- Columns: perception agents / code agents / **physical-model agent (PhysEarth)**.
- Goal: (1) reproduce published model experiments; (2) run trustworthy new ones.
- Coverage:

  | Family | Registered now | Not in this version |
  |---|---|---|
  | Radiative transfer | SMRT, tau-omega, water cloud, PROSAIL | MEMLS, DMRT-QMS, HUT |
  | Hydrology | pywatershed (PRMS, Sagehen Creek) | — |
  | Land surface / water balance | pyET (reference ET, 6 formulations) | full LSMs (Noah-MP, CLM) |

  Do not call pyET a land surface model.
- What PhysEarth adds:
  - an evaluation protocol (configuration and provenance);
  - plug-in registration of your own model and papers;
  - checks enforced in code;
  - host plugins.
- Open source, deploys as a ModelScope Studio app.
- On the user's comparison image, add "Evaluation protocol" and "Provenance ledger" to *What
  PhysEarth adds*, and add step 0, "Register model & paper".

### 3. Problem-solving philosophies (45 s) — placed before the evidence on purpose
1. **Declare, don't code**: a model's capability lives in its card (ranges, legal combinations,
   output bounds), not in code the LLM writes.
2. **Plan before compute**: the whole experiment is approved by a human before anything runs;
   unstated values are labelled, not hidden.
3. **Verify in code, not by self-scoring**: gates before the run, after the run and at the
   answer, plus an external rubric.
4. **Persist evidence, not functions**: sections read, result handles and provenance carry
   across turns.

Contrast with EE Genie:
- decomposition into sub-tasks ↔ plan before compute;
- minimal Python per turn ↔ declare, don't code;
- the LLM verifies by printing values ↔ verify in code;
- persisting functions ↔ persisting evidence.

One-liner: *EE Genie makes the LLM a better programmer; PhysEarth makes the LLM a checked
operator of trusted models.*

### 4. Logic flow, steps 0–4 (2 min) — keep the agent-loop slide
0. **Register your model and paper.** [Done]
   - Model: card + adapter, `PHYSEARTH_MODEL_PATH`, `python -m physearth.registry.check`,
     `register_github_model_repo`.
   - Paper: `ingest_paper` (DOI or file, licence-gated).
   - Testing each registration with visible progress. [Later]
1. **Read and plan.** The agent opens sections and the figure's title, axes and legend, then
   writes a research plan with each parameter's source labelled. [Done; figures extracted
   only for the SMRT paper]
2. **Check, approve, run.** Range and combination validation, human approval, output QC,
   results stored as handles. [Done]
3. **Report and score.** Chart from a spec beside the paper's figure, citation gate, declared
   outcome (reproduced / partial / not identifiable / failed), rubric scores. [Done in part]
4. **Evaluation-driven improvement loop.** Failure → fix the general mechanism (never the
   task, card or prompt) → regression test → human approval → re-score. [Done as practice]

Do not call step 4 "recursive self-improvement"; it is human-gated.

### 5. Evaluation protocol (1 min)

| Score | Status |
|---|---|
| Execution rate | [Done] |
| Reproduction: visual judge | [Done] |
| Reproduction: numeric error against the authors' code | [1 wk] |
| Provenance: label scheme and scorer | [Done] |
| Provenance: cross-check against system-recorded `defaulted_parameters` | [1 wk] |
| Safety: illegal calls attempted / executed, false-premise handling | [Done] |
| Report judge | [Done] |
| Time and cost | [Done] |

Contrast: ThinkGeo and Earth-Bench score tool choice and final answer; ours adds
**configuration fidelity** and **parameter provenance**.

### 6. Results: success / partial / failed (2.5 min)
- **Main experiment** [1 wk]: Q1 (SMRT Fig. 3), Qwen, harness vs direct LLM, 3 repeats.
- **Robustness** [1 wk]: DeepSeek, GLM and GPT-5.5 with the harness, 1–2 repeats each.
- **Fig. 4a/4b** [1 wk]: the paper states the full configuration (tasks already exist in
  `evaluation/tasks/tier1/`).
- **Success** [Done]:
  - Fig. 3 figure in 3/3 runs, visual judge 8/8;
  - refusals (density above ice, illegal pairing).
- **Partial** [Done]:
  - Fig. 3 numbers: 4/6 curves within 3–4% of the authors' notebook; the sticky pair is about
    12% off because the paper never states stickiness;
  - reports scored 6, 6, 5 out of 10.
- **Failed, and what we learned** [Done]:
  - the direct-LLM baseline stopped after one page (fixed, with a test);
  - stickiness was an unlabelled default in 3/3 runs;
  - Fig. 6 needs MEMLS;
  - PROSAIL hybrid inversion is unsupported.
- **Do not show** the old direct-LLM column ("0 of 3 figures"): it predates the fix.

### 7. Live demo video (about 2 min)
1. Studio: register `models/examples/toy_model` → out-of-range call refused with the card's
   reason → cited run.
2. **Claude Code via the plugin**: ask Q1 → the approval gate holds → figure plus cited answer.
3. A 10-second cut of the same tools in Codex and DeepSeek Harness ("one server, three hosts").

### 8. Deliverables, future work and vision (about 1.5 min)
- **Deliverables:**
  - the open-source agent and Studio (ModelScope);
  - the registration contract;
  - the evaluation protocol with tasks and judge standards;
  - the test suite;
  - host plugins.
- **[PLACEHOLDER: embedded animation]** One MCP server fanning out to Claude Code, Codex and
  DeepSeek Harness, each lighting up as its install completes. The user will record a clip,
  or ask Claude to build it as an embedded animation.
- **Next:**
  - the numeric-claim gate;
  - laptop install;
  - new cases: TVC, FAO-56, pywatershed (HESS 30, 5195, 2026; Zenodo 17180693), PROSAIL
    hybrid inversion;
  - full land surface models;
  - comparison against coding agents.
- **Vision — from plugging in models to plugging in theories.**
  - Today, humans register models and the agent configures and runs them.
  - Next, the agent writes or revises physics code itself (a new parameterisation, an adapter
    for a published model, a fix to a process scheme), but that code must pass the same
    contract first:
    - a card declaring its ranges;
    - conservation and reference-output checks;
    - a regression test;
    - human approval.
  - Closing line: *"Declare, don't code" becomes "code only through the contract."*
  - Possible first targets: a MEMLS adapter (needed for Fig. 6), or a revised snow-density
    scheme in pywatershed.

Time check: 1 + 1.5 + 0.75 + 2 + 1 + 2.5 + 2 + 1.5 ≈ 12 min. If it runs long, trim the
results gallery, not the demo.

---

## One-week work list
1. **Q1 re-run.** Run `evaluation/runners/competition.py` with Qwen, configurations `full` and
   `no-harness`, 3 repeats. Approve the batch explicitly (`--approve-batch`). Pin exact model
   IDs: the fork's main switched the catalogue to DeepSeek-V4.1-Flash, Qwen3.8-Flash-Next and
   GLM-5.2.
2. **Robustness runs** with the other three LLMs; **Fig. 4a/4b** with Qwen.
3. **Provenance cross-check.** Score the plan's labels and the report's
   `<parameter_provenance>` against `defaulted_parameters`, and enable it for Q1
   (`evaluation/metrics/competition_score.py` currently skips scientific-question tasks).
4. **Numeric score against the authors' notebook** (`q1_figure3_oracle.json`): interpolate onto
   the oracle grid and report both "as the agent chose" and "with the notebook's settings".
5. **Plugins** (fork `zjuiEMLab/physearth-agent`):
   - merge branches `plugin/claude-geoai` (40 tests pass), `plugin/codex-geoai` (44) and
     `plugin/dsh-geoai` (27) into one shared `integrations/geoai/`;
   - make approval an operator setting at server start or via MCP elicitation, **not** the
     model-settable `approve_runs` argument;
   - add `verify_report` for answers the host writes.
6. **Record the demo video** and the plugin animation (or ask Claude to build the animation).

## Facts and numbers (verified in session; use as-is)
- **System:**
  - 6 registered models; 21 agent tools;
  - 8 CC-BY papers split into 79 sections; 23,658 TVC backscatter measurements;
  - test suite: 390 pass, 1 skipped, 1 known proxy-test failure that pre-exists;
  - 21 tests archived in `tests/archive/`.
- **Q1 harness runs** (qwen-plus, judge claude-opus-5):
  - figure 3/3; visual judge 8, 8, 8; report judge 6, 6, 5 out of 10 (pass mark 8);
  - 26–28 LLM calls, 0.65–0.74M tokens, 4–5 min per run.
- **Offline numeric check** against the authors' notebook (36.5 GHz, stickiness 0.15):
  - 4/6 curves have normalised RMSE of 3–4%; this is fully explained by the frequency
    (37 vs 36.5 GHz);
  - the two sticky curves are 12% off (up to 28%), because the agent used the card default
    stickiness of 0.2.
- **Provenance cross-check** (offline, 3 harness runs):
  - stickiness was an unlabelled default in 3/3 runs;
  - run 1 labelled frequency, temperature and thickness "paper_inferred" although the system
    recorded them as defaults.
- **Earlier 48-run ablation** (REPORT.md, older build, records no longer in the tree):
  - illegal calls executed: 0% with the harness vs 17% without;
  - citations resolving: 100% vs 67%.
  - Label it as an earlier build.

## Related agents (for the comparison slide)

| Agent | Tools | Similar to ours | Lacks |
|---|---|---|---|
| RS-Agent (arXiv 2406.07089) | 18 specialist RS models (denoise, super-resolution, detection, change detection, SAR, VQA) | Solution/Knowledge Space ≈ our method notes and corpus | Pre-run validation, approval, provenance |
| GeoGPT (arXiv 2307.07930) | LangChain GIS tool pool: OpenStreetMap / imagery download, spatial analysis, mapping | Predefined tool pool | Physical models, checks |
| GeoAgent (arXiv 2410.18792) | Code interpreter + RAG + MCTS refinement | RAG; error recovery | Writes code; no physical bounds |
| ThinkGeo (arXiv 2505.23752) | Benchmark: 14 tools (perception / logic / operation), 486 tasks | Step-wise and final-answer scoring ≈ our protocol | No configuration or provenance scoring |

Other sources:
- UnivEARTH / "Towards LLM Agents for Earth Observation" (ICML 2025, arXiv 2504.12110);
- Earth-Agent / Earth-Bench (arXiv 2509.23141);
- remote sensing agent survey (arXiv 2601.01891);
- Reichstein et al. 2019 (Nature) for the data-driven vs physical framing.

## Files in this folder
- `SLIDE-PLAN.md` — this file.
- `JUDGE-QA.md` — judge questions and answers, logic flow, philosophies.
- `AUDIT-2026-09.md` — the repository audit (local only).
- `deck-source/` — source of the current 20-slide deck (`deck.json` plus `slides/*.html`).
- `figures/`:
  - `paper_fig3_picard2018_CC-BY.png`, `agent_fig3_qwen-plus_full_r1.png` — Q1 comparison
    (the paper figure is CC BY 4.0, Picard et al. 2018);
  - `prosail_hybrid_hsi_reference_maps.png` — reference maps from the PROSAIL hybrid-inversion
    tutorial;
  - `user_*` — the reference images shared in the discussion (EE Genie slides, previous
    architecture comparison, organizers).
- `analysis-scripts/` — `sim_raw.py` and `sim_runone.py`: the scripted-LLM replay of the
  direct-LLM baseline and the end-to-end raw run with real SMRT.
- `references/` — the PROSAIL hybrid-HSI tutorial source (`hybrid_hsi.Rmd`) and the R
  functions defining the training distribution (`get_atbd_lut_input.R`,
  `set_options_prosail.R`).

## Git state at handoff
- `main` = `60f3c42`, merged from PR #1; it includes `b286597` (evaluation repair and test
  archive).
- The remote branch `claude/relaxed-pascal-twywbo` could not be deleted from the session.
  Delete it from GitHub (**Delete branch** on PR #1), then run `git fetch --prune`.
- Local-only files, ignored via `.git/info/exclude`: `docs/AUDIT-2026-09.md`,
  `docs/JUDGE-QA.md`, `docs/handoff/`.
