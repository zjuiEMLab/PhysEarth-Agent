# PhysEarth Geo-AI — a DeepSeek Harness plugin

This plugin puts **PhysEarth-Agent** inside DeepSeek Harness: the six registered physical
models with their declared parameter ranges, the evidence and citation rules, the bundled
CC-BY corpus, and a visible Geo-AI restyle — switchable on and off from 设置 → 插件, with a
page refresh to see it.

It is an **out-of-tree** plugin: nothing here patches DeepSeek Harness itself. `package.json`
declares `dsh.bundle.patch` (this package's `cordis.patch.yml`) and `dsh.client` (the browser
half), which is exactly how the two working external plugins on this machine (`dsh-vision-router`,
`dsh-file-upload`) are mounted.

## What it contributes

| Piece | Where | What a user notices |
|---|---|---|
| Switch + settings | 设置 → 插件 → **PhysEarth Geo-AI** | one click enables/disables the whole surface |
| Tools | `mcp__geoai__*` via the harness' own MCP client row | `run_model`, `research_plan`, `read_literature`, … with validation, approval gate and QC behind them |
| Prompt rules | host half, `ctx.systemPrompt.section()` | numbers come from runs; citations resolve only against evidence the session gathered |
| Restyle | host token overrides + this plugin's own stylesheet | dark Geo-AI surface, ice/amber/deep-blue accent, Fira stack for numbers, tabular figures |

## Install

```bash
# 1. the Python side must answer first (repo root)
python -m integrations.geoai health

# 2. install the plugin into the running profile
integrations/dsh/scripts/install.sh

# 3. restart the harness, then open 设置 → 插件
dsh web
```

`install.sh` resolves this checkout, prefers `dsh plugin add`, links the package into the
profile's `node_modules` as a fallback, and writes the path-bearing layer the switch needs to
survive a restart (`$DSH_HOME/profiles/web/physearth-geoai.patch.yml`).

## The switch, and why it is ours

The shipped Plugins settings section is **read-only**: the host exposes a `list` remote, the UI
shows enablement (`!entry.disabled`) and can only expand a card. There is no enable/disable
control to reuse, so this plugin ships its own card with the one click, and it flips two things
together:

- `enabled` in the `physearth-geoai` settings namespace — the host half then registers or
  withdraws the prompt section and frees the Python bridge it started; the browser half adds or
  removes the token override, the stylesheet and the `body.geoai-restyled` class;
- the MCP row `mcp-geoai` through `ctx.loader.update('mcp-geoai', { disabled })`, so the model's
  tool list follows the switch instead of lingering after a disable.

Both are live in the web profile, so **a refresh is enough**. Toggling off leaves nothing behind:
no tools, no prompt text, no styles, no bridge process.

## Verify it

```bash
# the plugin's own logic and the three files a host loads (no harness needed)
cd integrations/dsh && node --test

# the Python surface the plugin drives
python -m integrations.geoai health
python -m integrations.geoai call list_models --arguments '{"model":"smrt"}'

# the two rows are live
dsh --profile web --dump-config | grep -A3 -E '(geoai|mcp-geoai)'
```

In the browser, the observable acceptance steps are:

1. 设置 → 插件 → **PhysEarth Geo-AI** → click the switch, save, refresh.
2. The shell palette changes (dark surface, accent rail, monospace numbers) and the accent
   selector changes it again; choosing 停用 and refreshing returns the host default palette
   exactly.
3. Ask the agent to sweep snow density: it should call `mcp__geoai__run_model` and produce a
   handle, not a remembered number.
4. Disable the plugin, refresh, and ask the same question again: the physics tools are gone,
   which is the intended behaviour rather than a defect.

## Design notes

- **Tools are discovered, not declared.** The engine already publishes an MCP server
  (`integrations/geoai/mcp_server.py`), so the harness' own MCP client row brings the tools and
  their schemas stay in step with the engine. No tool shape is re-invented in TypeScript.
- **The engine decides.** Validation, the approval gate, QC and evidence rules live in Python.
  `approveRuns` is off by default; turning it on says the deployment owns the consent step, and
  the card says so in those words.
- **One place per fact.** Settings, theme tokens, tool cards and the bridge command are defined
  once in `lib/logic.js`, consumed by both halves and asserted by the tests.
- **Loud, not silent.** A non-loopback bridge address, an unknown accent and an out-of-range
  timeout are corrected *with a warning*; a missing capability throws at load rather than
  quietly doing nothing.

## Known limitations

- **Runtime behaviour not yet exercised here.** The loader-based half of the switch
  (`ctx.loader.update`) and the theme cascade order (this stylesheet versus the six sheets
  `ui-theme` injects) are documented from the harness source, not measured in this checkout.
  Treat the first run as a verification step, not as a finished claim.
- The card writes settings through `scope.set`; if a host build names that differently, the card
  reports it instead of pretending to save (the card's status line says which method is missing).
- The MCP row and this plugin are two rows: disabling the *plugin row* in a profile layer (rather
  than using the switch) leaves the MCP row mounted, because a bundle patch cannot express "this
  row follows that switch". Use the card, or comment out both rows.
- Codex and other non-DSH hosts use the MCP server directly (see `integrations/geoai/README.md`);
  this package is only the Harness UI shell.
