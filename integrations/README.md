# integrations — this project inside a coding agent

Everything in this directory exists to put the engine behind a *host*. None of it is the research
product: the engine, the interface, the corpus, the prompt stack and the registered models all live
at the repository root, and nothing here duplicates them. Every host reaches the engine through
`integrations/geoai/`, the one Python surface.

## Layout on this branch

```
integrations/
  geoai/      the shared surface — host-neutral, and the only way in
  codex/      Codex: the guide, the theme, the config blocks, and the installable bundle
  scripts/    the host's scripts, in one place
  README.md   this file
```

| Directory | What it is |
|---|---|
| `geoai/` | `service.py` (capabilities, knowledge, prompt stack, one call, one turn), `mcp_server.py` (28 tools over stdio), `bridge.py` (loopback JSON API), `__main__.py` (CLI) |
| `codex/README.md` | the install guide: two commands, the checks, and the honest limits |
| `codex/theme/` | `geoai.tmTheme` — the one visual surface a Codex plugin can change |
| `codex/config/` | `mcp.toml` (the registration block), `theme.toml` (verified keys), `mcp-example.toml` |
| `codex/plugin/` | the marketplace bundle: `.codex-plugin/plugin.json` plus its copy of the skill |
| `scripts/` | `doctor-codex.sh` (proves the interpreter, lists the tools), `theme-codex.sh` |

Three paths stay at the repository root because Codex looks for them *there* and nowhere else:

| Path | Why it cannot move |
|---|---|
| `.agents/skills/geoai/` | Codex discovers a repository skill only at this path. Opening the repository is the install. |
| `.agents/plugins/marketplace.json` | the repository marketplace, discovered at this path; its `source.path` points at `integrations/codex/plugin` |
| `AGENTS.md` | the working notes Codex reads at the start of a session |

`scripts/find-python.sh` also lives at the root rather than here: it is shared by the project's own
`scripts/studio.sh` and by every host's installer, so it belongs with the project's scripts and the
installers reach up to it.

The other two hosts are on their own branches with the same shape: `plugin/dsh-geoai` carries
`integrations/dsh/`, and `plugin/claude-geoai` carries `integrations/claude/`. A branch ships one
host's plugin plus the shared surface, so nothing here has to explain a second host's conventions.

## How Codex gets in

```bash
codex mcp add geoai -- "$PWD/.venv/bin/python" "$PWD/integrations/geoai/mcp_server.py" --stdio
integrations/scripts/doctor-codex.sh          # proves the interpreter, then lists the tools
integrations/scripts/theme-codex.sh           # installs the colour scheme

codex plugin marketplace add "$PWD"           # optional: the skill and metadata as one unit
codex plugin add geoai@physearth-agent
```

The skill is discovered by opening the repository, so the only required step is the MCP
registration. The colour scheme and the marketplace bundle are additions on top of that.

## Verified

`tests/test_codex_integration.py` (23 tests), plus the real binaries: `codex plugin marketplace add`
lists `geoai@physearth-agent`, `codex plugin add` installs it, `doctor-codex.sh` gets 28 tools over
stdio, and `theme-codex.sh` validates the plist before claiming success.

`integrations/geoai/README.md` documents the shared surface; `integrations/codex/README.md` is the
install guide.
