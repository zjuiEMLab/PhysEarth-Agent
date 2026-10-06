# PhysEarth-Agent: judge Q&A (competition prep, local only)

Pitch: *a trust layer and benchmark for LLM agents that run physical Earth models.*

## Logic flow (what happens to one query)
1. **Read and plan.** For a user query, the LLM reads the paper's sections and figures, then writes a research plan against the registered model card, labelling every parameter's source.
2. **Check, approve, run.** The harness checks the plan against the card's physical ranges, a human approves, and the model runs. Outputs are checked against declared bounds and stored as handles.
3. **Report and score.** A chart is drawn from a spec beside the paper's figure. The report must cite what was read or run and declare an outcome, and the evaluation protocol scores the run.
4. **Evaluation-driven improvement loop.** A low score is traced to its cause, which is fixed in the general mechanism (never written into the task or prompt). The fix gets a regression test, it is approved by a human, and the run is scored again.

## Problem-solving philosophies (the rules behind every step)
1. **Declare, don't code.** What a model can do lives in its card (ranges, legal combinations, output bounds), not in code the LLM writes.
2. **Plan before compute.** The whole experiment is planned and approved by a human before anything runs. Unstated values are labelled, not hidden.
3. **Verify in code, not by self-scoring.** Gates check before the run, after the run and at the answer, and an external rubric scores the result.
4. **Persist evidence, not functions.** Sections read, results (as handles) and parameter provenance carry across turns and are reused rather than recomputed.

## Q&A

**1. Goal?**
Make physical Earth models usable by an LLM with justified confidence, for (1) reproducing published experiments and (2) running trustworthy new ones. Physical models fail silently: snow denser than ice still gives a plausible curve. So the checks live in code, not in the prompt.

**2. How is it different from other agents?**
(1) An evaluation protocol that scores any agent on execution, reproduction, provenance, safety, report quality and cost.
(2) A light registration contract: a YAML card plus `run(spec)`, and the model inherits every check.
(3) Provenance as an output: the system records which parameters were defaults, so a "from the paper" label can be verified.
(4) Guarantees in code: refusal before a run, human approval, output bounds.

**3. Technology?**
- Python backend: agent loop, 21 tools, harness (validation, approval, gates, audit, budgets, untrusted-text boundary), research planner, literature corpus, registry.
- Gradio Studio, talking to the backend through one declared API.
- Any OpenAI-compatible LLM (Qwen, DeepSeek, GLM).
- 6 models across 4 domains; 8 CC-BY papers split into 79 sections; 23,658 measurements; 390 tests.

**4. Bottleneck and failed cases?**
- **Narration.** SMRT Fig. 3: the figure was right in 3/3 runs (visual judge 8/8), but the reports scored 6, 6 and 5 out of 10 (pass mark 8), with weak factuality.
- **Provenance.** Stickiness was an unlabelled default in 3/3 runs; one run labelled three defaults as coming from the paper.
- **Cost.** About 0.7M tokens and 4–5 min per run.
- **Coverage.** PROSAIL is forward-only, so no hybrid inversion; only one paper has extracted figures.
- **Next fixes:** a gate that ties every reported number to a stored result, and provenance scoring.

**5. Long tasks?**
- A versioned research plan, revisable at review.
- Human checkpoints between planning and execution.
- Session memory: sections read, models run and result handles are reused.
- Old turns compacted.
- Handles keep large arrays out of the context.
- Per-turn and per-session budgets.
- A JSONL audit log per session.
- Limitation: the prompt grows from about 14k to 39k tokens, and a project cannot resume across days yet.

**6. How do you know a reproduction is correct?**
Paper-stated fields are scored exactly; outputs are compared numerically against the authors' own code where it exists; a blind visual and report judge scores the rest. Against the authors' notebook, 4/6 Fig. 3 curves are within 3–4%; the gap comes from values the paper never states.

**7. What if the paper doesn't state a parameter?**
A default or assumption is legitimate, but it must be labelled, and the outcome is declared partial or not identifiable. The label is scored, not the guess.

**8. Why not Claude Code or another coding agent?**
They are more flexible and often faster to a figure, but they fail silently (library defaults, out-of-range values, overstated accuracy). Our protocol scores them too, and the plan is to provide our checks to them as a plugin.

**9. How do I add my own model or paper?**
- Model: a folder with `model_card.yaml` and `adapter.py`; validate with `python -m physearth.registry.check`, then point `PHYSEARTH_MODEL_PATH` at it. Also possible from a GitHub repo via `register_github_model_repo`.
- Paper: `ingest_paper` by DOI or file, licence-gated.
- Demo: `models/examples/toy_model`.

**10. Does it improve itself, or overfit the benchmark?**
It has an evaluation-driven improvement loop with a human gate: failure → general mechanism fix → regression test → re-score. The rule is never to write the answer into a task, card or prompt. Counterfactual tasks and a recent paper check that it configures rather than recalls.

**11. Does it depend on a strong LLM? Cost?**
It is LLM-agnostic through an OpenAI-compatible client. The checks do not depend on the model's judgment. A cross-LLM scorecard is still needed.

**12. Safety: hallucination, prompt injection?**
- Claims must cite something actually read or run.
- Abstract-only evidence cannot carry values.
- External text is wrapped as evidence.
- URLs are built from DOIs by the system.
- A human approves every run.
- An earlier 48-run ablation (older build, re-run pending): illegal calls executed 0% with the harness vs 17% without; citations resolving 100% vs 67%.

**13. Does it generalise beyond snow?**
The mechanism covers 6 models in 4 domains. The evidence is still SMRT-heavy; next are Trail Valley Creek measurements, FAO-56, pywatershed (HESS 2026) and the PROSAIL hybrid inversion.

**14. What's next?**
More cases with numeric gold, the numeric-claim gate, provenance scoring, a fair comparison with coding agents, an MCP plugin, and laptop install.

## Before presenting
- Re-run Q1 with the fixed direct-LLM baseline. The old "0 of 3 figures" baseline predates the fix.
- Present the plugin as the model-folder registration and `ingest_paper`. The MCP plugin and laptop install are roadmap items.
