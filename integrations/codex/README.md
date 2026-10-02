# PhysEarth-Agent in Codex

Two commands and a check. Everything the engine offers — 28 tools, the bundled CC-BY corpus,
reference measurements, the research workflow with its approval gate — arrives through one MCP
server; the skill in `.agents/skills/geoai/` is what tells Codex *how* to use it, and it is
already in the repository, so there is nothing to install for it.

Verified against **codex-cli 0.155.1**.

Run approval is the operator's setting, fixed when the server starts: `ask` by default, or
`--approval always` appended to the server's arguments to pre-approve. With `ask`, a physical run stops with
`awaiting_approval`; Codex shows you the pending run and passes your answer to `geoai_decide`.

## 1. Point Codex at an interpreter that has the engine

```bash
cd /path/to/PhysEarth-Agent

# Which Python can import the engine? Use exactly this path below.
.venv/bin/python -c "import sys; sys.path[:0]=['backend','.']; \
  from integrations.geoai import service; print('ok')"     # (uv sync --extra dev creates .venv)
```

If nothing prints `ok`, install the environment first (`uv sync --extra dev`, or
`pip install -e backend` plus PyYAML). A server pointed at an interpreter without the
dependencies **starts and offers an empty tool list**, with nothing in the log — this is the
single most common way this integration appears broken.

## 2. Register the server

```bash
codex mcp add geoai -- \
  /path/to/PhysEarth-Agent/.venv/bin/python \
  /path/to/PhysEarth-Agent/integrations/geoai/mcp_server.py --stdio
```

Use absolute paths: Codex launches the command from its own working directory.

The file form of the server (`.../integrations/geoai/mcp_server.py`) is deliberate. A script run
that way gets its own directory on `sys.path`, which finds neither `integrations` nor
`physearth`, so the file adds the repository root and `backend/` to `sys.path` itself. That means
no `cwd` and no `PYTHONPATH` are needed, and it removes the failure where the module form dies of
`ModuleNotFoundError` in a subprocess whose stderr nobody reads.

Prefer the TOML? Merge `integrations/codex/config.snippet.toml` into `~/.codex/config.toml` instead. The key
is `mcp_servers`, not `mcpServers`, and `startup_timeout_sec = 30` is worth setting: the default
10 s is tight for a scientific Python import.

## 3. Check it

```bash
codex mcp list                                   # geoai should be listed, enabled
codex mcp get geoai --json                       # transport, command, args, timeouts
integrations/codex/doctor.sh                          # both of the above, plus an import check
```

Then, in a Codex session, ask for something only the engine can answer — *"sweep snow density in
SMRT and plot brightness temperature"* — and confirm it calls the tools rather than answering
from memory. Start a **new** session after registering: MCP servers are read at session start.

## 4. Skills (already present, nothing to do)

`.agents/skills/geoai/SKILL.md` is discovered from the repository root, per Codex's search order
(`$CWD/.agents/skills`, up to the repo root, then `$HOME/.agents/skills`). It gives the model the
*procedure* the tools cannot: which tool answers which kind of question, what a valid run looks
like, which refusals are results, and the citation rules. Invoke it explicitly with `/skills` or
by typing `$`, or let the description trigger it.

Two notes on it:

- Its front matter carries `name` and `description`, and the description is the trigger — it
  front-loads the geophysics vocabulary and states the boundaries ("does not run arbitrary
  Python for a number").
- `agents/openai.yaml` declares the MCP dependency formally. If a validator rejects the
  `dependencies` block, delete it; nothing in `SKILL.md` needs it.

## 5. Rules for the whole repository (optional)

`integrations/geoai/AGENTS.snippet.md` is the same rules in `AGENTS.md` form. This repository
ships no `AGENTS.md`; if you want the Geo-AI rules to be unconditional rather than
skill-triggered, put the snippet in an `AGENTS.md` at the root of the project you work in — or in
a global `~/.codex/AGENTS.md`.

Nothing here writes that file for you. It is the user's own instructions, and a tool that
silently edits it is a tool that has decided what your agent should believe.

Discovery order Codex uses, for reference: `$CODEX_HOME/AGENTS.override.md`, else
`$CODEX_HOME/AGENTS.md` (first non-empty only); then, per directory from the repository root down
to the working directory, `AGENTS.override.md`, else `AGENTS.md`, **one per directory**; merged
root-first so deeper files win; truncated at `project_doc_max_bytes` (32 KiB).

## What this integration deliberately does not do

- **No UI.** Codex gives a third-party plugin no panel, no widget, no status-line item. The
  engine's output here is text, tool results and generated figures. A `.tmTheme` in
  `$CODEX_HOME/themes` can recolour the terminal (`/theme`, persisted as `tui.theme`), but that
  is a global user preference — a plugin cannot activate it, so it is not part of this package.
- **No `instructions` key.** Codex's own config reference marks it "reserved for future use".
  `developer_instructions` and `model_instructions_file` exist but are reported unreliable
  across Codex surfaces (issues #11004, #33238), so nothing here depends on them.
- **No `~/.codex/prompts/*.md`.** That directory is deprecated in favour of skills ("Custom
  prompts are deprecated. Use skills."), which is why the workflow lives in
  `.agents/skills/geoai/`.
- **No `codex mcp-server`.** That command and its standalone binary were removed; use the app
  server if you need that shape.
- **No `codex mcp login`.** It exists, but it is OAuth for streamable-HTTP servers; a stdio
  server has nothing to authenticate.
- **No assumption that MCP resources or prompts reach the model.** The server publishes
  `geoai://…` resources and three prompts, and they work in hosts that surface them; Codex's
  documentation does not describe them as reachable, so every one of them is also available as a
  tool (`geoai_prompt_stack`, `list_models`, `read_literature`).
- **No IDE-extension story.** Codex's docs are explicit that plugins are not available there,
  though skills are, and the MCP server is shared through the same `~/.codex/config.toml`. So
  the skill is the part of this package that still works in the extension.

## 6. Text and colour

A Codex plugin cannot add a panel, a widget or a status-line item of its own, so colour and text
are the whole surface a third party can change. Both are supported properly, and both are
shipped here.

```bash
integrations/codex/theme-install.sh              # installs the scheme, prints the one manual step
integrations/codex/theme-install.sh --check      # verifies an installed copy
```

Then, in the TUI, `/theme` and choose **PhysEarth Geo-AI**. The scheme is
`integrations/codex/geoai.tmTheme` — a TextMate/Sublime plist, which is what Codex parses (with the `two-face`
crate) from `$CODEX_HOME/themes/`. `integrations/codex/config-theme.snippet.toml` explains each config key.

The three levers, and how far each reaches:

| Lever | Effect | Who activates it |
|---|---|---|
| `tui.theme` + a `.tmTheme` | rewrites the colours of every syntax scope Codex emits | the user, once, in `/theme` (or the config key) |
| `tui.status_line_use_colors` | makes the status line follow the active theme's colours | the config key |
| `tui.status_line`, `tui.terminal_title` | choose which items appear — i.e. the *text* | the TUI pickers (`/statusline`), which write the ids |

**Why this file pins only two keys.** `theme` (string) and `status_line_use_colors` (boolean)
were probed against codex-cli by writing a value of the wrong type and reading the error, which
names both the key and the type it expects:

```
$ printf '[tui]\ntheme = true\n' > $CODEX_HOME/config.toml && codex mcp list
Error: failed to load bootstrap configuration
Caused by:
    invalid type: boolean `true`, expected a string
    in `tui.theme`
```

That probe also corrected the record: an earlier version of this guide said `tui.terminal_title`
was a boolean. It is a list, and the mistake came from probing several keys against one shared
config file, where a stale invalid key from the previous probe masked the next one. One probe,
one fresh config, and read the key name out of the error rather than trusting your own label.

The item **ids** for `status_line` and `terminal_title` are deliberately not pinned: the config
layer accepts any string and filters unknown ids later, so a wrong id is not an error — it is a
silently empty slot. `/statusline` writes the right ones, so let it.

What this cannot do: a plugin cannot force a theme. Switching back to `dark` or `light` stays the
user's choice in `/theme`, and the plugin neither fights it nor reapplies itself.

## Where this package stops, and why

`integrations/codex/geoai/` plus `.agents/plugins/marketplace.json` make this installable in two commands
from a repository marketplace:

```bash
codex plugin marketplace add /path/to/PhysEarth-Agent
codex plugin add geoai@physearth-agent
```

That path exists for people who want the skill and the author metadata delivered as a unit. It
is **not** the recommended install, and it does not register the MCP server — see
`integrations/codex/geoai/README.md` for why, and for the one command that finishes the job.

Both commands were run against this tree, in a throwaway `CODEX_HOME`, so what follows is a
measurement rather than an expectation:

```
$ codex plugin marketplace add /path/to/PhysEarth-Agent
Added marketplace `physearth-agent` from /path/to/PhysEarth-Agent.
Installed marketplace root: /path/to/PhysEarth-Agent
Marketplace `physearth-agent`
  /path/to/PhysEarth-Agent/.agents/plugins/marketplace.json

PLUGIN                 STATUS         VERSION  SOURCE
geoai@physearth-agent  not installed           /path/to/PhysEarth-Agent/integrations/codex/geoai

$ codex plugin add geoai@physearth-agent
Added plugin `geoai` from marketplace `physearth-agent`.
Installed plugin root: $CODEX_HOME/plugins/cache/physearth-agent/geoai/1.0.0

$ codex plugin list
PLUGIN                 STATUS              VERSION  SOURCE
geoai@physearth-agent  installed, enabled  1.0.0    /path/to/PhysEarth-Agent/integrations/codex/geoai
```

The install copies the plugin into `$CODEX_HOME/plugins/cache/<marketplace>/<plugin>/<version>/`,
which is the same constraint that decides how the MCP server is registered: a plugin cannot ship
a path to anything outside itself, so the server's absolute command is written by the user's own
`codex mcp add`.

Unlike `claude plugin`, Codex 0.155.1 has **no `validate` subcommand** — `plugin add|list|remove`
and `plugin marketplace add|list|upgrade|remove` only. The shape the CLI accepts is therefore
pinned by `tests/test_codex_integration.py` instead and confirmed by the run above; a rejection
would show up as a marketplace listing zero plugins, or an `add` failing on a field name.

Public submission to a remote marketplace is a different thing and needs something this
repository cannot provide: an official requirement of a remotely hosted HTTPS MCP endpoint. That
is an infrastructure project (expose the engine behind a streamable-HTTP MCP server and keep it
alive), not a packaging one.

## Troubleshooting

`.agents/skills/geoai/references/troubleshooting.md` covers the four failures that cost real time
here — reaching for `python` where only `python3` exists, an interpreter without PyYAML, the 10 s
startup timeout, and a refusal mistaken for an error — plus the engine's own refusals and what
they mean.
