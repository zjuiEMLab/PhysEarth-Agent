# When the server does not work

Each entry is a symptom, what actually happened, and the check that distinguishes it. The
first four are the ones that cost real time in this repository; the rest are the engine's own
refusals, which are results rather than faults.

## The server starts but lists no tools

Almost always the process died during import. An MCP client reports a server that failed to
start as a server with an empty tool list.

```bash
# the same command the client runs, by hand:
python3 /abs/path/to/PhysEarth-Agent/integrations/geoai/mcp_server.py --stdio </dev/null
```

- `ModuleNotFoundError: No module named 'integrations'` or `... 'physearth'` — `mcp_server.py`
  bootstraps both roots itself (`integrations/geoai/…` → repository root, and `…/backend`), so
  this means the file has been moved out of the repository or the repository is incomplete.
  The module form needs the caller to set them: `cwd` = repository root, `env.PYTHONPATH` =
  `backend`.
- `ModuleNotFoundError: No module named 'yaml'` (or `numpy`, `xarray`, …) — the interpreter is
  not the one the engine is installed into. `python` is absent on macOS and most Linux
  distributions; `python3` is frequently a bare system interpreter. Point the server at the
  environment that has the dependencies:

  ```bash
  codex mcp add geoai -- python3 .venv/bin/python  # wrong: see below for the right shape
  codex mcp remove geoai
  codex mcp add geoai -- /abs/path/.venv/bin/python /abs/path/integrations/geoai/mcp_server.py --stdio
  ```

  Or keep the interpreter and set `PHYSEARTH_PYTHON`.

A useful one-liner before blaming the client:

```bash
/abs/path/.venv/bin/python -c "import sys; sys.path[:0]=['src','.']; from integrations.geoai import service; print('engine importable')"
```

## The agent says the tools are unavailable, but the server works in a shell

The client's own startup timeout. The default is 10 s and this server imports a scientific
Python stack; on a cold filesystem that is tight. In the client's config:

```toml
startup_timeout_sec = 30
tool_timeout_sec = 300     # engine runs are genuinely long
```

`codex mcp get <name> --json` shows what the client thinks the timeouts are.

## `no_credentials`, or `geoai_ask` refuses in one line

No inference credential in the server's environment. Everything except the agent turn works
without one — the tools, the resources, `run_model`, the corpus. Set
`PHYSEARTH_LLM_API_KEY` (and `PHYSEARTH_LLM_API_BASE` if it is not the default) in the server's
`env`. The refusal is deliberate: it is better than an invented answer, and the server never
falls back to a locally generated one.

## "session not found", or a handle does not resolve

Handles are session-scoped. A `run_model` handle answers only inside the session that produced
it, and an unknown session is reported rather than guessed at. Call `geoai_session_new` first,
pass its `session_id` to the calls that need one, and do not reuse a handle from an earlier
session.

## A call is refused with `status: "needs_input"`

This is the engine working. It validates parameters against the model card's declared physical
range **before** a run and outputs against declared bounds after it. Expect this for:

- density above solid ice, or any value outside the card's declared range;
- a microstructure no registered theory derives (the model exists; the configuration is not
  covered);
- a liquid-water dielectric or scattering model asked about frozen ground;
- an output the chosen model does not declare;
- a required input that a previous step never produced.

Read the refusal's own wording, report it, and stop. **Do not** vary parameters until something
passes: that turns a boundary into a number. If the refusal looks wrong, `list_models` with the
model name shows the declared range the check used.

## `bridge_unreachable`

The optional HTTP bridge, not the MCP server. The DSH plugin starts it only when
`autoStartBridge` is on; from Codex it is normally not running at all and nothing needs it.
Ignore it unless you deliberately use the HTTP surface.

## `read_literature` returns an index instead of text

By design: called with only a slug it returns the paper's section index. Call it again with
`section_id`. A citation `[paper#section]` must name a section you actually read this way.

## A figure request returns metadata but no image

`read_paper_figure` returns metadata and the stored asset; only `inspect_paper_figure` renders
the image, and only when a vision-capable endpoint is configured. Without one, the metadata is
still the answer — figure titles, axes, legends and labels are extracted facts and are usually
enough to decide whether the figure is reproducible here.

## `discover_literature` finds nothing useful, or `ingest_paper` fails

`discover_literature` queries OpenAlex: metadata and abstracts only, so a hit is `[abs:doi]`
evidence and may not carry a unit-bearing value. `ingest_paper` needs either a DOI that resolves
to an open-access full text or a `file_path` to a PDF the user uploaded; a paywalled DOI is
reported as such rather than fetched.

## Where the logs are

This server writes JSON-RPC on stdout and nothing else; diagnostics go to stderr. If a client
swallows stderr, run it by hand (first section above) and read what it says. For the DeepSeek
Harness plugin instead of Codex, see `integrations/dsh/README.md`.
