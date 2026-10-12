# integrations — this project inside a coding agent

Everything in this directory exists to put the engine behind a *host*. None of it is the research
product: the engine, the interface, the corpus, the prompt stack and the registered models all live
at the repository root, and nothing here duplicates them. Every host reaches the engine through
`integrations/geoai/`, the one Python surface.

## Layout on this branch

```
integrations/
  geoai/      the shared surface — host-neutral, and the only way in
  claude/     Claude Code: the guide and the installable bundle
  scripts/    the host's installer, in one place
  README.md   this file
```

| Directory | What it is |
|---|---|
| `geoai/` | `service.py` (capabilities, knowledge, prompt stack, one call, one turn), `mcp_server.py` (28 tools over stdio), `bridge.py` (loopback JSON API), `__main__.py` (CLI) |
| `claude/README.md` | the install guide: what a plugin can and cannot do, and how each lever was verified |
| `claude/plugin/` | the bundle: `.claude-plugin/plugin.json`, `skills/geoai/`, `output-styles/geoai-brief.md`, `themes/geoai-night.json`, `scripts/statusline.py` |
| `scripts/` | `install-claude.sh` — installs the plugin, registers the MCP server, writes the two settings a plugin cannot set |

One path stays at the repository root because Claude Code looks for it *there* and nowhere else:

| Path | Why it cannot move |
|---|---|
| `.claude-plugin/marketplace.json` | the marketplace for this repository; its `source.path` points at `integrations/claude/plugin` |

`scripts/find-python.sh` also lives at the root rather than here: it is shared by the project's own
`scripts/studio.sh` and by every host's installer, so it belongs with the project's scripts and the
installers reach up to it.

The other two hosts are on their own branches with the same shape: `plugin/dsh-geoai` carries
`integrations/dsh/`, and `plugin/codex-geoai` carries `integrations/codex/`. A branch ships one
host's plugin plus the shared surface, so nothing here has to explain a second host's conventions.

## How Claude Code gets in

```bash
integrations/scripts/install-claude.sh                  # plugin + MCP + settings (user scope)
integrations/scripts/install-claude.sh --scope project  # or repo-local
integrations/scripts/install-claude.sh --check          # report state, change nothing
```

Two of the three steps exist because a plugin cannot do them itself: Claude Code gives a plugin no
way to activate a theme or to ship a default status line. The installer writes both into the user's
settings, after backing the file up, and deleting those two keys reverts everything.

## Verified

`tests/test_claude_integration.py` (20 tests), plus the real binary: `claude plugin validate`
passes, `claude plugin tag --dry-run` agrees with the marketplace entry, `claude mcp list` reports
`✓ Connected` from the bundle's new paths, and the status line renders colour.

One claim is recorded as documented-not-measured: that `force-for-plugin: true` applies the output
style with no user action. Observing it needs a real session with a login, which a throwaway
`CLAUDE_CONFIG_DIR` cannot borrow (the credential lives in the login keychain). The guide gives the
one command that settles it.

`integrations/geoai/README.md` documents the shared surface; `integrations/claude/README.md` is the
install guide.
