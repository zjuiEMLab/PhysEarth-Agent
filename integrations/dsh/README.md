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

## Verified, with the transcript

This plugin has been run inside a real harness, in an isolated profile on port 3199, with a
headless browser driven over it. What that pass found is what the code now handles; the values
below are measurements, not expectations.

| Claim | Measured |
|---|---|
| The rows compose with this machine's paths | `dsh --profile geoai-verify --dump-config` shows both rows patched by the profile layer |
| The harness boots with the plugin mounted | OK; the plugin row is in `window.__DSH_BOOT__` with its four inject edges |
| The browser half is served | `/plugins/dsh-plugin-physearth-geoai/client.js` → 200, 41 KB, `rev` changes with content |
| The restyle applies | `body.geoai-restyled`, `data-geoai-accent=ice`, `--dsw-alias-bg-base` = `#05070d`, `--dsw-alias-brand-primary` = `#22d3ee` (host default background: `rgb(21, 21, 23)`) |
| The card appears in 设置 → 插件 | `.geoai-card` found; full zh copy, switch, two selects, three inputs, three checkboxes, probe button |
| The switch turns it off live, without a reload | after one click: class gone, `data-geoai-enabled=false`, `--dsw-alias-bg-base` back to `rgb(21, 21, 23)` |
| The switch turns it back on live | after a second click: restyled again, `#05070d` |
| The engine tools exist | 28 over stdio MCP: `run_model`, `plot`, `research_plan`, `read_literature`, `read_reference_dataset`, the `geoai_*` host tools, … |
| The optional bridge answers when asked | started through `BridgeClient`: `{"models":6,"runnable_models":6,"tools":21,"knowledge":{"papers":8,"sections":79,"skills":3}}` |
| No console errors | 0 at every step |
| Four viewport widths | 1440/1024 → 564 px card, two 255 px columns; 768 → 484 px, two 215 px columns, 44 px touch target; 390 → 106 px column (the host keeps a 154 px options rail), one column, no clipping and no page overflow at any width |

The pass also produced the five fixes recorded in the commit messages: `schemastery` was not
resolvable through a symlinked package (the installer now copies the package into the profile);
the `mcp-geoai` override was partial, and a `config` is *replaced* rather than merged (the
installer now writes both rows complete, derived from the bundle patch); the spawned bridge had no
`PYTHONPATH` and died silently inside a `stdio: 'ignore'` spawn; the client bundle registered
under the wrong id, so the row was dropped with a console error and nothing happened in the
browser at all; and the token layer stayed stacked after the switch went off, so the palette did
not come back.

### Reproducing it

```bash
# an isolated profile: base + web-app bundles, this plugin, nothing else of the operator's
integrations/dsh/scripts/verify-profile.sh geoai-verify 3199

# boot it, optionally turning the plugin on through the composition
cat > /tmp/geoai-on.yml <<'YAML'
- id: geoai
  config:
    enabled: true
YAML
dsh --profile geoai-verify --patch /tmp/geoai-on.yml --port 3199
# then open http://127.0.0.1:3199/ and go to 设置 → 插件
```

**A `config`-targeted patch replaces the whole config.** That is why the overlay above is three
lines and why the installer writes its managed block the way it does. If you turn
`autoStartBridge` on through such a patch, restate `projectRoot` and `pythonCmd` in the same
object or the plugin loses them — the optional bridge then has no interpreter to start.

## Known limitations

- **One host, one harness build.** Everything above ran against DeepSeek Harness 0.1.0-rc.7 on
  macOS, with the `anaconda3/envs/physearth-agent` interpreter. Another build could name a token,
  a slot key or a scope method differently; the failure modes are then named in the log rather
  than swallowed, and `tests/` pins the contracts read out of this one.
- **The 390 px case is the host's layout, not a card defect.** The settings shell keeps a 154 px
  options rail at that width, leaving 106 px for any plugin card. This card degrades to one narrow
  column without overflow rather than widening past its container; the host's own cards face the
  same column.
- The switch's effect on the MCP row lives in the running process: it is a loader update, and the
  harness does not persist runtime loader updates. The `enabled` setting itself *is* persisted
  (into the host's settings document), so a restart re-applies the row state on mount.
- The MCP row and this plugin are two rows: disabling the *plugin row* in a profile layer (rather
  than using the switch) leaves the MCP row mounted, because a bundle patch cannot express "this
  row follows that switch". Use the card, or comment out both rows.
- Codex and other non-DSH hosts use the MCP server directly (see `integrations/geoai/README.md`);
  this package is only the Harness UI shell.


