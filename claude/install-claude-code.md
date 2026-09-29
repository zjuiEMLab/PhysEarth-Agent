# PhysEarth Geo-AI in Claude Code

A CLI integration. Claude Code gives a plugin **no UI** — no panel, no widget, no component that
touches the screen — so this package is shaped like the terminal: the engine's tools, the workflow
that uses them, an answer style, and colour.

Two commands:

```bash
# 1. the engine must be importable by some interpreter
.venv/bin/python -c "import sys; sys.path[:0]=['backend','.']; \
  from integrations.geoai import service; print('ok')"

# 2. install the plugin, register the MCP server, and write the two settings
scripts/claude-plugin-install.sh              # user scope; --scope project for a repo
```

Then start a **new** session — plugins, output styles and MCP servers are read at session start.

## What arrives, and which mechanism carries it

| Piece | Component | What a user notices |
|---|---|---|
| 28 engine tools | MCP server, registered by the installer | `run_model`, `research_plan`, `read_literature`, … as `mcp__geoai__*` |
| Workflow | `skills/geoai/` | the model knows which tool answers which geophysical question, and which refusals are results |
| Answer discipline | `output-styles/geoai-brief.md` | every unit-bearing number is sourced, every claim carries a resolvable marker |
| Colour | `themes/geoai-night.json` + the status line | ice/amber on a near-black field, and a coloured status row |

## Text and colour: the two levers, honestly ranked

Claude Code is stricter than it looks, so the ranking here is by *reliability*, not ambition.

**1. `statusLine` — the strongest colour lever.** Claude Code renders ANSI escape sequences from a
status-line command's stdout, and re-runs it on session start, on every assistant message, on
`/compact`, on a mode change and every `refreshInterval` seconds. `plugins/geoai-claude/scripts/statusline.py`
prints one coloured row: the model, the active output style, context remaining with a colour
threshold, the branch, and the effort level.

```json
"statusLine": {
  "type": "command",
  "command": "python3 \"/abs/path/plugins/geoai-claude/scripts/statusline.py\"",
  "padding": 0,
  "refreshInterval": 10
}
```

**A plugin cannot ship this.** Only `subagentStatusLine` is settable from a plugin's `settings`,
which is why the installer writes it into the user's settings file — backing the file up first.

**2. Output style — the only zero-action change to *text*.** `force-for-plugin: true` makes the
style apply without the user selecting anything, which no other mechanism does.
`keep-coding-instructions: true` keeps the ordinary software-engineering instructions alongside it,
so the style adds claim discipline rather than replacing the ability to write code.

**3. Theme — satisfies "colour", but needs one selection.** A plugin supplies a theme; it cannot
activate one. Claude Code reads `experimental.themes` and shows it as `custom:geoai-claude:geoai-night`,
then the user picks it in `/theme` — or the installer writes the settings key for them.

**4.** `subagentStatusLine` — the one status-line-shaped thing a plugin *can* default. Not used
here: it only decorates subagent rows, which is not where this project's work happens.

## Why the MCP server is registered by the script, not bundled

Measured, not assumed. `claude plugin install` copies the plugin into
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. A bundled `.mcp.json` therefore cannot
reach the engine by a relative path, and the relative form does something worse than fail loudly:

```
plugin:geoai-claude:geoai: python3 -m integrations.geoai serve - ✗ Failed to connect
```

— a plugin that installs cleanly, reports an enabled MCP server, and offers no tools. The
installer registers the **file form** of the server with an absolute interpreter instead, because
`mcp_server.py` adds the repository root and `backend/` to `sys.path` from its own location, so it
needs neither `cwd` nor `PYTHONPATH`:

```bash
claude mcp add geoai --scope user -- \
  /abs/python /abs/PhysEarth-Agent/integrations/geoai/mcp_server.py --stdio
```

Verified after install: `claude mcp list` → `geoai: … - ✓ Connected`.

## Verify

```bash
scripts/claude-plugin-install.sh --check     # plugin inventory, component list, settings
claude plugin details geoai-claude           # skills / agents / MCP servers / token cost
claude mcp list | grep geoai                 # must say ✓ Connected
```

In a session: `/output-style` shows `geoai-claude:geoai-brief`, and the status row carries the
Geo-AI palette. Ask a question only the engine can answer — *"sweep snow density in SMRT and plot
brightness temperature"* — and confirm it calls the tools instead of answering from memory.

## What this cannot do

- **No UI of any kind.** No panel, no dialog, no layout change. Claude Code gives a plugin no
  component that draws.
- **Cannot activate a theme or a status line.** Both are the user's settings, by design; the
  installer writes them, backs up first, and a deletion of the written keys reverts everything.
- **Cannot inject `CLAUDE.md`.** A plugin-root `CLAUDE.md` is not loaded, and Claude Code's own
  validator warns about it. The supported routes are the skill and the output style, which is what
  this package uses.
- **Cannot use settings keys other than `agent` and `subagentStatusLine`.** A plugin's `settings`
  block is filtered; the rest is ignored, which is why nothing here depends on it.

## Troubleshooting

`plugins/geoai-claude/skills/geoai/references/troubleshooting.md` — the same engine-side guide the
Codex and DSH integrations use. For this surface specifically:

- **`✗ Failed to connect`** — the interpreter cannot import the engine. The installer proves its
  choice with `from integrations.geoai import service`; if you registered by hand, do the same.
  `python3` on macOS is a system interpreter without PyYAML.
- **No Geo-AI palette after installing** — the theme needs selecting once (`/theme`, or the
  `theme` key the installer writes into the scope you chose). A project-scope settings file is only
  honoured after the workspace trust dialog.
- **Tools missing but the plugin is enabled** — start a new session. MCP servers are read at
  session start, not on reload.
