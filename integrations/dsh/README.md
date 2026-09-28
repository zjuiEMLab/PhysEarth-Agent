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
| Restyle | 60 host semantic tokens + this plugin's own stylesheet | dark Geo-AI surface, ice/amber/deep-blue accent, Fira stack for numbers, tabular figures, 44px touch targets |

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

The link is what makes the client half work at all: `@deepseek-ai/dsh-client-modules` resolves
a row's package with `createRequire(ctx.baseUrl)` — the **profile** directory — reads
`exports["./client"]` off disk, hashes it and serves it at `/plugins/<entry name>/client.js`.
No build step is involved, which is why the two halves here are hand-written plain JS.

## The switch, and why it is ours

The shipped Plugins settings section is **read-only**: the host exposes a `list` remote, the UI
shows enablement (`!entry.disabled`) and can only expand a card. There is no enable/disable
control to reuse, so this plugin ships its own card under the `settings.plugin.item` slot, and
that one click flips two things together:

- `enabled` in the `physearth-geoai` settings namespace — the host half then registers or
  withdraws the prompt section and frees the Python bridge it started; the browser half adds or
  removes the 60-token override layer, the stylesheet and the `body.geoai-restyled` class;
- the MCP row `mcp-geoai` through `ctx.loader.update('mcp-geoai', { disabled })`, so the model's
  tool list follows the switch instead of lingering after a disable. This runs on **both**
  transitions: with the row left composed while the plugin is off, the tools would still be
  callable and "off" would be cosmetic.

Both are live in the web profile, so **no restart is needed** — the client bundle stays loaded
while the plugin is merely switched off, which is why the card is still there to switch it back
on. A page refresh picks up the boot-manifest change (the tools and the prompt section are
server-side and change immediately). Toggling off leaves nothing behind: no tools, no prompt
text, no styles, no bridge process.

## Verify it

```bash
# the plugin's logic, the shape of the files a host loads, and both halves against stubs
cd integrations/dsh && node --test

# the Python surface the plugin drives
python -m integrations.geoai health
python -m integrations.geoai call list_models --arguments '{"model":"smrt"}'

# the two rows are live
dsh --profile web --dump-config | grep -A3 -E '(geoai|mcp-geoai)'
```

The 36 tests are split by what they can prove. `logic.test.mjs` covers the settings coercion,
the tool cards and the shipped file shapes. `host.test.mjs` mounts `entry.js` against a stub
cordis context and is the reason three real bugs are not in this revision: the prompt section
was registered as `{ id, content }` instead of `{ name, order, text }` (which throws), the
settings scope was watched through `subscribe()` (a method the scope does not have, so the
switch would have applied only at mount), and the MCP row was only touched while the plugin was
already on. `client.test.mjs` evaluates the browser half for real — the module-loader global and
`react` are stubbed, everything else records — and asserts the token layer is `{ light, dark }`
pairs, because the theme service throws a teaching error on a bare string and nothing else would
catch it before a browser did.

In the browser, the observable acceptance steps are:

1. 设置 → 插件 → **PhysEarth Geo-AI** → click the switch. It writes immediately (there is
   no separate save), and the restyle changes in place.
2. The shell palette changes (dark surface, accent rail, monospace numbers) and the accent
   selector changes it again; choosing 停用 returns the host default palette exactly.
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
- **The restyle is tokens first.** 60 of the host's 89 `--dsw-alias-*` / `--dsw-specific-*`
  names are overridden — surfaces, four border weights, three label weights, the state colours,
  code blocks, bubbles, the sidebar, the scrollbars — so the whole interface moves together
  without this plugin guessing at a single component class name. The stylesheet only adds what
  tokens cannot express: type, focus rings, scrollbar thumbs, selection, motion policy, and the
  card itself.
- **Two exposures, not one design plus a fallback.** Every token carries a light and a dark
  value, and the accent has separate fills per exposure, because a bright cyan fill with dark
  text is legible on an OLED field and the same pair is not on a white one.
- **One place per fact, within each half.** Settings, tool cards and the bridge command are
  defined once in `lib/logic.js` and read by the host half and the tests. The palette lives
  entirely in `lib/client.js`, because a client bundle cannot value-import a sibling file — a
  relative `require` misses the module table and throws — so duplicating it into `logic.js`
  would only create a copy that drifts. `host.test.mjs` asserts the two settings key sets match.
- **Loud, not silent.** A non-loopback bridge address, an unknown accent and an out-of-range
  timeout are corrected *with a warning*; a host without `loader.update`, a scope without
  `watch`, or a missing `theme.overrideTokens` is named in the log rather than ignored.

## Known limitations

- **Runtime behaviour not yet exercised here.** The loader-based half of the switch
  (`ctx.loader.update`), the theme cascade order (this layer versus the six sheets `ui-theme`
  injects) and the visual result at 375/768/1024/1440 px are read out of the harness source and
  pinned by the stub tests, not measured in a live browser. Treat the first run as a
  verification step, not as a finished claim.
- The switch's effect on the MCP row lives in the running process: it is a loader update, and
  the harness does not persist runtime loader updates. On restart the profile layer
  (`physearth-geoai.patch.yml`) is what decides, and the plugin re-applies the row state from the
  stored `enabled` setting as soon as it mounts.
- The MCP row and this plugin are two rows: disabling the *plugin row* in a profile layer (rather
  than using the switch) leaves the MCP row mounted, because a bundle patch cannot express "this
  row follows that switch". Use the card, or comment out both rows.
- Codex and other non-DSH hosts use the MCP server directly (see `integrations/geoai/README.md`);
  this package is only the Harness UI shell.

