# TODO

Three workstreams. They are ordered by what unblocks what, not by importance.

Topic 1 is the foundation: until session state survives a turn, nothing else compounds.
Topics 2 and 3 can start immediately and in parallel.

One piece of housekeeping first, before anyone branches: `SPECS` in `physearth/tools.py` is a
flat list with specs appended at the bottom, and all three topics add tools there. Convert it
to per-tool registration so three people are not conflicting on the same six lines.

---

## 1. Step-by-step research

The agent forgets everything between turns, so every question restarts from zero, and the
human cannot steer before compute happens.

- [ ] **Make state session-scoped.** `agent.stream` calls `new_state()` per turn
      (`physearth/agent.py:206`). Thread a session object from `app.py` through instead.
- [ ] **Carry evidence forward.** Persist `sections_read`, `models_run`, `datasets_read` and
      result handles across turns. Verify `harness.review_final` resolves a turn-1 citation
      in turn 3 without re-reading.
- [ ] **Add an "already gathered" prompt block.** In `physearth/prompt.py`, list held handles
      with one-line summaries so the agent reuses rather than re-runs.
- [ ] **Make budgets cumulative.** Rework `harness.check_budget` for a session ceiling with a
      per-turn soft cap. Show what is left in the trace.
- [ ] **Add `propose_plan(steps[])`.** Each step declares intent, tool and parameters. The
      agent must call it before any `run_model`.
- [ ] **Render the plan as an editable checklist.** `physearth/ui/render.py` and
      `assets/ui.js`. The turn pauses on a `needs_approval` phase until the human approves,
      edits a parameter, or drops a step.
- [ ] **Add `plot(dry_run=True)`.** Axes, labels, units, series names and source styling with
      no data, so the human confirms the intended figure before the sweep runs.
- [ ] **Add `compare(model_handle, data_handle, metric=[bias, rmse, mae, r])`.** Refuses on
      mismatched observable, frequency or angle. No dependency on the items above; start it
      whenever.

**Done when** a user asks a question, edits a frequency in the proposed plan, approves it, and
the run ends in a quantified model-versus-measurement number citing sections read two turns
earlier.

---

## 2. Skills

The `kind: skill` mechanism works and holds exactly one card. It is the cheapest way to raise
answer quality, because it is domain writing against an existing loader.

- [ ] **Write seven skill cards** in `knowledge/skills/`, same shape as `model-comparison`:
      sensitivity analysis; uncertainty propagation; model-measurement comparison protocol;
      sensor configuration choice (frequency, polarisation, angle); validity-boundary
      checking; reporting a null result; literature triage.
- [ ] **Expose skills in `list_literature`** behind a `kind` filter. `knowledge.catalogue()`
      drops them today, so they are visible only through the system prompt.
- [ ] **Add a `[skill:slug]` marker** to `physearth/harness.py`, resolving only against skills
      actually read. "I followed the comparison protocol" should be verifiable, not asserted.
- [ ] **Name the trigger situation for each skill** in the workflow prompt, rather than
      listing the skills.
- [ ] **Enforce one skill in code.** Have `compare` apply the comparison matrix, so the
      protocol is a constraint rather than advice.
- [ ] **Test** that every card loads, reads through `read_literature`, and that its marker
      resolves.

**Done when** the trace shows which protocol was followed, and a comparison across mismatched
configurations is refused in the skill's own wording.

---

## 3. Knowledge

Two problems. Retrieval is metadata-only, so the corpus does not scale: `knowledge.search`
matches slug, title, description and scenarios, and never the 79 section bodies. And the
corpus is fixed at eight papers, so anything recent or off-centre is unanswerable.

### Make the corpus scale

- [ ] **Index the section bodies and rank with BM25.** No new dependencies.
- [ ] **Add `search_literature(query, top_k)`** returning `slug#id`, title, score and a
      snippet. Full text stays behind `read_literature`.
- [ ] **Shrink the catalogue block** in `physearth/prompt.py`, which grows linearly with the
      corpus and is only load-bearing while search does not exist.
- [ ] **Extend the corpus to roughly 25 papers** through the `MANIFEST` in
      `scripts/build_corpus.py`, and add a third reference dataset in a medium other than snow.
- [ ] **Add a retrieval regression test:** ten questions, each with an expected section,
      asserting it ranks in the top three.

### Reach live literature

Extend the corpus contract with a live tier rather than bolting a web search onto the agent,
so `read_literature` and the citation harness work unchanged. Three tiers: **bundled** (full
text, redistributable, `[slug#id]`), **session** (open-access full text fetched on request,
same marker, tier flagged in the trace), **abstract** (metadata only, `[abs:doi]`, supports
"the paper reports X" and never a verified number). Separate markers mean the harness enforces
the distinction instead of the prompt requesting it.

Discovery through OpenAlex, which carries topics, related works, publication date and
open-access licence in one call. Full text through Europe PMC and Copernicus. The section
splitter in `scripts/build_corpus.py` is generic JATS and already handles both; only
`xml_url()` and `JOURNAL_NAMES` are publisher-specific.

- [ ] **Extract the JATS parser** into `physearth/ingest/jats.py`, with the build script
      importing it. Golden-file test first; no behaviour change.
- [ ] **Add `discover_literature(query, from_year, limit)`** returning candidates with licence
      and an ingestible flag, deduplicated against the local corpus by DOI. Never full text.
- [ ] **Add `ingest_paper(doi)`**, gated on an open licence, writing a sectioned card into a
      session corpus that `knowledge.py` merges with the bundled one.
- [ ] **Add a related-topics panel.** Cluster candidates by OpenAlex topic, render them as
      chips the user opens and pulls papers from, and route selection through the same
      `needs_approval` gate as topic 1 rather than inventing a second one.
- [ ] **Safety and operations.** Domain allowlist, with the agent passing a DOI and the system
      building every URL; every fetched section through `untrusted.scan` and `wrap`; timeout,
      size and per-session ingest caps; `PHYSEARTH_ONLINE=0` disabling the tier entirely, with
      the offline path confirmed to still work. Verify whether the Studio deployment has
      outbound network before shipping any of this.
- [ ] **Add `scripts/promote_paper.py`**, a human-run step moving a session paper into
      `knowledge/literature/` and updating `NOTICE`. Never automatic: redistribution carries
      attribution obligations.
- [ ] **Extend the literature-triage skill:** newest is not most relevant. A 2018 model
      description outranks a 2026 application paper for how the model works, and preprints are
      labelled unreviewed.

**Done when** adding seventeen papers improves answers instead of degrading them, and a user
can pull in two open-access papers mid-session and get an answer citing them, with the trace
showing which citations are bundled, which are session-ingested and which are abstract-only.

---

## 4. Open follow-ups (recorded 2026-09-25)

Not blocking the current Q1 comparison; each can be fixed later.

- [ ] **Test every new registration, and show the user its progress.** When a model is
      registered (a card and adapter, or `register_github_model_repo`) or a paper is added
      (`ingest_paper`, or a new `knowledge/literature/` card), run the same checks the
      bundled ones pass: card validation, an adapter smoke run, an oracle or replay check,
      and for a paper, section and figure extraction. Stream each step into the trace as it
      runs (pending, running, passed or failed, with the reason), so the user sees a
      registration being tested rather than a silent success.
- [ ] **Install on a local laptop.** Today it is `git clone`, `uv sync`, `python app.py`.
      Target: `pipx install physearth-agent` (or `uvx`), with the corpus and models shipped
      as package data (CC-BY and Apache licensed), console scripts `physearth studio`,
      `physearth mcp` and `physearth approve <ticket>`, Gradio moved to an optional
      `[studio]` extra, and a local OpenAI-compatible LLM (Ollama, LM Studio) with
      `PHYSEARTH_ONLINE=0`. Check macOS, Windows and Linux, since pywatershed and pymupdf
      have native dependencies.
- [ ] **Audit parameter provenance against what the system recorded.** The research plan
      already records `defaulted_parameters` for each run, independently of what the LLM
      claims. Score the LLM's `condition_provenance` and the report's
      `<parameter_provenance>` against it: a card default labelled as paper-derived is a
      mislabel, and a default left unlabelled is an omission. A `paper` label also needs a
      source span found in a section that was actually opened. Enable this for the
      scientific-question tasks; `competition_score.provenance_score` skips them today.
      The six committed Q1 reports all lack the provenance appendix (`appendix_missing`).
- [ ] **Re-run Q1, harness against direct LLM.** The committed no-harness records predate
      the forced read -> run -> plot progression (regression test:
      `test_raw_reproduction_cannot_stop_after_reading_one_page`), so they are not a valid
      baseline. Needs `PHYSEARTH_LLM_*` and `EVAL_LLM_*` credentials.
- [ ] **Make the raw baseline general.** `run_raw_smrt` only returns a scattering
      coefficient over density, so the direct-LLM arm cannot attempt any case but Figure 3.
- [ ] **Add the pywatershed reproduction case** from HESS 30, 5195 (2026), with inputs from
      Zenodo record 17180693. Neither host is reachable from the cloud environment yet.
- [ ] **Restore or retire the archived tests** in `tests/archive/` together with their
      runners. tier0.py, model_registration.py and registry_contract.py are restored;
      the dashboard, registration demo, robustness and reproduction runners remain.
