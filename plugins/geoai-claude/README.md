# plugins/geoai-claude — the Claude Code plugin

Installed from this repository's own marketplace:

```bash
claude plugin marketplace add /path/to/PhysEarth-Agent --scope user
claude plugin install geoai-claude@physearth-agent --scope user
```

Or in one step, which also registers the MCP server and writes the two settings a plugin cannot:

```bash
scripts/claude-plugin-install.sh
```

`claude/install-claude-code.md` is the full guide.

## Contents

| Path | Component | Notes |
|---|---|---|
| `.claude-plugin/plugin.json` | manifest | `name` is the only required key; nothing invented |
| `skills/geoai/` | skill | the workflow; byte-identical to the Codex copy, asserted by a test |
| `output-styles/geoai-brief.md` | output style | `force-for-plugin: true` + `keep-coding-instructions: true` |
| `themes/geoai-night.json` | theme | `experimental.themes`, because top-level `themes` warns it will be removed |
| `scripts/statusline.py` | — | the coloured status row; the installer points settings at it |

## No `.mcp.json`, on purpose

`claude plugin install` copies the plugin into `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`.
A bundled MCP entry therefore cannot reach the engine by a relative path, and the relative form
fails in the worst way available:

```
plugin:geoai-claude:geoai: python3 -m integrations.geoai serve - ✗ Failed to connect
```

A plugin that installs cleanly, reports an enabled MCP server, and offers no tools. The installer
registers the file form of the server instead, with an absolute interpreter — `mcp_server.py` adds
the repository root and `backend/` to `sys.path` itself, so that command needs no `cwd` and no
`PYTHONPATH`. Verified: `claude mcp list` → `✓ Connected`.

## Two facts about the cache

- Bump `version` in `.claude-plugin/plugin.json` and reinstall to see a change; editing this
  directory alone changes nothing for an installed copy.
- `claude plugin tag` creates `geoai-claude--v<version>` and walks up to the enclosing
  `.claude-plugin/marketplace.json`, validating that the two agree.
