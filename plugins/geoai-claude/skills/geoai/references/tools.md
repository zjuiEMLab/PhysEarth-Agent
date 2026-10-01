# Tool reference

Everything below arrives with the `physearth-geoai` MCP server. Names are as the MCP host
shows them; when a host prefixes by server name (Codex does), the tool is
`mcp__physearth-geoai__run_model`.

**Required** lists only parameters the call cannot omit. Optional ones are described in the
tool's own schema, which is the authority — this page is for choosing the right tool, not for
replacing the schema.

## Start here

| Tool | Required | What it is for |
|---|---|---|
| `geoai_health` | — | Once per session. Registered models, runnable models, declared tools, bundled evidence, whether inference credentials are configured. |
| `geoai_session_new` | — | Open a research session. Optional `model`, `approve_runs`. Handles resolve **only** inside the session that produced them, so this comes before any run. |
| `geoai_ask` | `question` | A whole question in one call: the agent plans, runs registered models and reports the evidence it used. Optional `session_id`, `model`, `approve_runs`. |
| `geoai_evidence` | — | The audit trail for a session: sections read, models run, datasets queried, method notes, result handles, figures. Cite this, not your recollection. |
| `geoai_prompt_stack` | — | The rules the engine itself answers under: citation and evidence-tier policy, the untrusted-text boundary, the research workflow. |

## Models and runs

| Tool | Required | What it is for |
|---|---|---|
| `list_models` | — | The registry. With no argument: every model, its tier and outputs. With `model`: that model's full parameter declaration, including the ranges a run is validated against. |
| `run_model` | `model` | The core operation. Parameters you omit take the card's defaults; `sweep` runs a range. Returns a **handle**, a bounded preview, units and quality control. |
| `run_planned_model` | `run_id` | Execute one run of an approved research plan. The backend uses the parameters stored in the plan — never reconstruct them yourself. |
| `run_raw_smrt` | `recipe` | The escape hatch: one free-form scattering-coefficient recipe against the installed upstream SMRT. It deliberately publishes no model names, so nothing here substitutes for a registered model. |

## Evidence you may read

| Tool | Required | What it is for |
|---|---|---|
| `list_literature` | — | Search what this conversation can already read: the bundled corpus, papers taken in with `ingest_paper`, the method notes. Optional `query`, `scenario`, `kind`. |
| `read_literature` | — | One paper. With only `slug`: its section index. With `section_id`: that section's full text. This is what a `[paper#section]` citation resolves against. |
| `read_paper_figure` | `paper`, `figure_id` | Metadata and the stored source asset for one extracted figure. Not model output, and not digitised automatically. |
| `inspect_paper_figure` | `paper`, `figure_id` | Look at the figure itself rather than its caption. Returns the source image when a vision endpoint is configured, plus an audit trail. |
| `read_reference_dataset` | — | Measured data. No argument lists datasets; `dataset` plus optional `filters` returns how many rows match and a preview. |
| `discover_literature` | `query` | OpenAlex, i.e. beyond what this deployment ships. Optional `from_year`, `limit`. Metadata and abstracts only — abstracts are `[abs:doi]` evidence. |
| `ingest_paper` | — | Take one paper's full text into the session, by `doi` or `file_path`. Afterwards it is readable with `read_literature`. |
| `read_raw_paper` | `doi`, `page` | One page of the publisher PDF as extracted text, optionally with a rendering of the page. No section index, no figure metadata. |

## Figures

| Tool | Required | What it is for |
|---|---|---|
| `plot` | `series` | Draw from result **handles**, never from numbers you retyped and never from code you wrote. Optional `kind`, labels, `dry_run`, `metrics`. |
| `plot_planned_chart` | `chart_id` | Render one approved chart from a research plan; the backend collects the compatible planned runs. Optional `action`. |

## The research workflow

| Tool | Required | What it is for |
|---|---|---|
| `read_research_guideline` | — | Read before proposing or reporting research. Optional `topic`. |
| `research_plan` | `action` | `propose`, then the review transitions. The plan is structured: steps, parameter mapping, outputs, charts, success criteria, stop conditions. |
| `geoai_plan_status` | — | The plan and its review state, so a host can show the human review step before anything expensive runs. |
| `geoai_review` | `session_id`, `choice` | Advance the human review gate — the same single action the Studio's review button takes. |

## Registering and extending

| Tool | Required | What it is for |
|---|---|---|
| `read_model_instruction` | `model` | The versioned instruction for one model, before using it in a plan. Optional `section`. |
| `register_model_guideline` | `model`, `content` | Store a user-provided guideline for an existing model. Stored as untrusted method guidance, not as system instruction. |
| `research_capability_check` | `action` | The capability checkpoint before a paper-reproduction plan: what the opened evidence names versus what this deployment can actually run. |
| `inspect_github_model_repo` | `url` | Read-only, pinned inspection of a model repository. Statically validates the card and adapter; never executes remote code. |
| `register_github_model_repo` | `proposal_id` | Register an inspected repository **only** after a human approval token. Without one it returns a review request and installs nothing. |

## Result shapes

Every engine tool answers in the same envelope, and the difference between its three meaningful
states is the point:

- `status: "success"` — the run happened. Look for `handle`, `units`, `qc`, `citations`.
- `status: "needs_input"` — **a refusal**. The configuration was rejected (parameter outside the
  declared range, a theory with no derivation for the chosen microstructure, a tool asked
  something outside its domain), or a required input is missing. Report it with the engine's own
  wording and do not retry variations until something passes.
- `status: "terminal_error"` — an error, including `bridge_unreachable` and `no_credentials`.

Full numeric arrays never enter your context. A run returns a handle and a bounded preview; the
arrays stay in the session. `plot` and `read_reference_dataset` are how you get at them.

## Credentials

The tools, resources and prompts work without an inference credential. `geoai_ask` and the
planning agent need one, and refuse in one line when it is missing rather than inventing an
answer. Set `PHYSEARTH_LLM_API_KEY` (and optionally `PHYSEARTH_LLM_API_BASE`) in the server's
`env` if you want that path.

## Resources and prompts

The server also publishes MCP **resources** — `geoai://prompt-stack`, `geoai://models`,
`geoai://knowledge`, `geoai://tools`, and `geoai://paper/<slug>/<section>` — and three MCP
**prompts** (`geoai-reproduce-figure`, `geoai-sweep-parameter`, `geoai-compare-models`).

Not every MCP host surfaces resources and prompts to the model, and Codex's documentation does
not describe them as reachable. Treat the tools as the contract and the resources as a bonus;
`geoai_prompt_stack`, `list_models` and `read_literature` cover the same ground through tools
that are definitely available.
