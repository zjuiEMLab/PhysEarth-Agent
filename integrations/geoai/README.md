# PhysEarth-Agent in a coding agent

Codex gets this repository's physics, evidence rules and bundled literature as **tools,
resources and prompts** over MCP. Codex cannot change this project's interface — that is a
Gradio app in `frontend/` — so this integration is deliberately text-and-tool shaped:
capability plus knowledge, no pixels.

Four artifacts make that up, and only the first needs installing:

| Artifact | Where | Why |
|---|---|---|
| MCP server | `integrations/geoai/mcp_server.py` | the capability: 28 tools, resources, prompts |
| Skill | `.agents/skills/geoai/` | the procedure: which tool for which question, what a valid run looks like, which refusals are results. Discovered from the repository, so nothing to install |
| Config | `codex/config.snippet.toml` | the file form of the registration |
| Guide | `codex/install-codex.md` | the two commands, the checks, and the honest limits |

## What ships

| Host tool | What it is for |
|---|---|
| `geoai_health` | registered models, runnable models, declared tools, bundled evidence, credentials |
| `geoai_session_new` | open a session; result handles resolve only inside it |
| `geoai_ask` | one agent turn: plan → run registered models → answer with citations |
| `geoai_evidence` | what a session actually read, ran and drew |
| `geoai_plan_status` | the research plan and the review action a human should take |
| `geoai_review` | advance the human review gate (the same call the Studio makes) |
| `geoai_prompt_stack` | the L0–L2 prompt stack plus the generated registry context |

Plus **every declared engine tool** (`list_models`, `run_model`, `run_planned_model`,
`read_literature`, `research_plan`, `plot`, …), each carrying the validation, approval gate
and quality control the interactive product applies.

Resources: `geoai://prompt-stack`, `geoai://models`, `geoai://knowledge`, `geoai://tools`,
and `geoai://paper/<slug>/<section>` for every bundled paper section — the same
`slug#section` id a citation resolves to.

Prompts: `geoai-reproduce-figure`, `geoai-sweep-parameter`, `geoai-compare-models`. Each
carries the evidence rules with the task, so the host's own reasoning is held to them.

## Install

The server is stdio JSON-RPC and has no third-party dependency; it only needs this checkout
importable. **`codex/install-codex.md` is the authoritative guide** — this is the short form.

```bash
# from the repository root
.venv/bin/python -c "import sys; sys.path[:0]=['backend','.']; \
  from integrations.geoai import service; print('ok')"    # which interpreter to register
scripts/codex-doctor.sh                                   # checks the interpreter, then the tools
```

Register it with Codex (`codex.toml.example` has the same thing in file form):

```bash
codex mcp add geoai -- "$PWD/.venv/bin/python" "$PWD/integrations/geoai/mcp_server.py" --stdio
codex mcp list
```

Two things the older revision of this file got wrong, both of which produce a server that
**starts and lists no tools**, with nothing said anywhere:

- `python` does not exist on macOS or on most Linux distributions, and `python3` is frequently a
  system interpreter without PyYAML. Register an interpreter you have proved can import the
  engine — an absolute path.
- The file form of the server (`mcp_server.py`) is used rather than `-m integrations.geoai`,
  because a script run that way gets its own directory on `sys.path` and finds neither
  `integrations` nor `physearth`; the file therefore adds both roots itself. That removes the
  dependence on getting `cwd` and `PYTHONPATH` right.

The skill in `.agents/skills/geoai/` needs no install step: Codex discovers it from the
repository. `AGENTS.snippet.md` remains for a project that is *not* this one — here the rules
already live in this repository's own `AGENTS.md`.

## Verify

```bash
# the surface answers without a host
python -m integrations.geoai health
python -m integrations.geoai models | head -40
python -m integrations.geoai prompt | head -40

# one real physics call, offline except for the model itself
python -m integrations.geoai call list_models --arguments '{"model":"smrt"}'

# the MCP protocol itself
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | PYTHONPATH=backend python -m integrations.geoai serve
```

`pytest tests/test_geoai_bridge.py tests/test_geoai_mcp.py -q` covers the same ground
offline: the tool catalogue, the model declarations, a real SMRT sweep through the bridge
and through MCP, a refused call, resources and prompts.

## Design notes

- **One engine, one route.** The service layer imports the package's own surface; a plugin
  never reaches past it, so the Studio and both plugins cannot drift into calling the
  engine three different ways.
- **A refusal is a result.** A worked-out validation, a missing credential or an unknown
  session comes back as a structured error the model can read and route around. Nothing is
  estimated locally to fill a gap.
- **The approval gate stays on** unless the caller passes `approve_runs: true`, which states
  that the host owns that consent decision. A plugin cannot approve a physical model run on
  the user's behalf by accident.
- **Numbers come from runs.** `run_model` returns a handle and a bounded preview; the
  arrays stay in the session store, and a citation marker resolves only against evidence the
  session actually gathered.

## Known limitations

- Codex cannot change this project's UI; the Studio remains the place to see figures, the run
  trace and the evidence panel.
- `geoai_ask` needs inference credentials (`PHYSEARTH_LLM_API_KEY` or `MODELSCOPE_TOKEN`).
  Without them it refuses in one line instead of inventing an answer; the tool-only and
  knowledge-only paths work offline.
- Sessions live in the server process: restarting it invalidates handles, and
  `geoai_evidence` says so rather than pretending.
