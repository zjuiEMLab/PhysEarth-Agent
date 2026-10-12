# integrations — this project inside three coding agents

Everything in this directory exists to put the engine behind a *host*: DeepSeek Harness, Codex, or
Claude Code. None of it is the research product. The engine, the interface, the corpus, the prompt
stack and the registered models all live at the repository root, and nothing here duplicates them —
each host reaches the engine through `integrations/geoai/`, the one Python surface.

## Layout

```
integrations/
  geoai/          the shared surface — host-neutral, and the only way in
  dsh/            DeepSeek Harness: the plugin package (host half + browser half + bundle patch)
  codex/          Codex: install guide, the .tmTheme, config snippets, and the installable bundle
  claude/         Claude Code: install guide and the installable bundle
  scripts/        every host's installer, in one place
  README.md       this file
```

| Directory | What it is | Loaded by |
|---|---|---|
| `geoai/` | `service.py` (capabilities, knowledge, prompt stack, one call, one turn), `mcp_server.py` (28 tools over stdio), `bridge.py` (loopback JSON API), `__main__.py` (CLI) | every host |
| `dsh/` | `entry.js` (host half: settings, prompt section, lifecycle), `lib/` (bridge client, settings logic, browser bundle, host-environment resolution), `cordis.patch.yml`, `tests/` (59 node tests) | DeepSeek Harness |
| `codex/` | `README.md` (install guide), `theme/geoai.tmTheme`, `config/*.toml`, `plugin/` (the marketplace bundle: `.codex-plugin/plugin.json` + its copy of the skill) | Codex CLI |
| `claude/` | `README.md` (install guide), `plugin/` (`.claude-plugin/plugin.json`, skill, output style, theme, `statusLine`) | Claude Code |
| `scripts/` | `install-dsh.sh`, `verify-dsh-profile.sh`, `install-claude.sh`, `doctor-codex.sh`, `theme-codex.sh` | you |

Three files stay at the repository root because a host looks for them *there* and nowhere else.
They are not clutter to be moved, and each one says so where it is used:

| Path | Why it cannot move |
|---|---|
| `.agents/skills/geoai/` | Codex discovers a repository skill only at this path. Opening the repository is the install. |
| `.agents/plugins/marketplace.json` | Codex's repository marketplace, discovered at this path; its `source.path` points into `integrations/codex/plugin/`. |
| `.claude-plugin/marketplace.json` | Claude Code's marketplace for this repository; its `source.path` points into `integrations/claude/plugin/`. |

`scripts/find-python.sh` at the root is the one exception in the other direction: it is shared by
the project's own `scripts/studio.sh` *and* by all three host installers, so it lives with the
project's scripts and the installers reach up to it.

## How each host gets in

```bash
# DeepSeek Harness — a plugin row, a settings card, a one-click switch
integrations/scripts/install-dsh.sh
integrations/scripts/verify-dsh-profile.sh geoai-verify 3199   # or into a throwaway profile
dsh web

# Codex — two commands from this repository's own marketplace
codex plugin marketplace add <repo>
codex plugin add geoai@physearth-agent
codex mcp add geoai -- <python> <repo>/integrations/geoai/mcp_server.py --stdio

# Claude Code — marketplace, plugin, and the two settings a plugin cannot set
integrations/scripts/install-claude.sh
```

The differences are the hosts', not a preference here: a Codex plugin may not change the interface
at all, so that branch works through text and text colour (a `.tmTheme`, a skill, a doctor); a
Claude Code plugin may not activate a theme or ship a status line, so that branch supplies both and
the installer writes them into the user's settings with a backup; DeepSeek Harness is the only one
of the three with a component API, so it is the only one that gets a card and a live switch.

## Verified, per host

Each branch carries its own test file, and the checks that need the real binary were run rather
than reasoned about:

| Host | Test file | What was measured |
|---|---|---|
| DSH | `tests/test_dsh_integration.py` + 59 node tests in `integrations/dsh/tests/` | the plugin boots in an isolated profile, the switch moves the palette, tools and prompt section together, and a one-shot headless run reports the engine's own rules in its system prompt |
| Codex | `tests/test_codex_integration.py` | `codex plugin marketplace add` lists `geoai@physearth-agent`, `codex plugin add` installs 1.0.0, the doctor proves the interpreter and gets 28 tools, the theme installer validates the plist |
| Claude Code | `tests/test_claude_integration.py` | `claude plugin validate` passes, `claude plugin tag --dry-run` agrees with the marketplace, `claude mcp list` says ✓ Connected, the status line renders colour |

`integrations/geoai/README.md` documents the shared surface itself; each host's guide is the
`README.md` in its own directory.
