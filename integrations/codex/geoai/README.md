# integrations/codex/geoai — the installable bundle

This directory exists so the skill and the author metadata can be delivered as one unit from a
repository marketplace:

```bash
codex plugin marketplace add /path/to/PhysEarth-Agent
codex plugin add geoai@physearth-agent
```

**This is not the recommended install.** `integrations/codex/README.md` is, and it needs one command
against a repository you already have. Read the next section before choosing this one.

## What it does and does not deliver

| Delivered | Not delivered |
|---|---|
| The `geoai` skill, so the workflow reaches the model without the checkout being its working directory | **The MCP server** — see below |
| Catalog metadata: display name, description, brand colour, starter prompts | Any UI. Codex gives a plugin no panel or widget to fill |
| Author, licence, homepage, keywords | A remote endpoint for public marketplace submission |

## Why the MCP server is not declared here

`codex plugin add` **copies** the plugin into `$CODEX_HOME/plugins/cache/<marketplace>/<name>/<version>/`
— verified, real directories rather than symlinks. The engine, however, is not inside this
directory and cannot be: it is the whole repository under `src/`, `catalog/`
and `integrations/`. So an `mcpServers` entry here would have to name the checkout by absolute
path, and a manifest that must be edited per machine is not repository content.

The honest arrangement is therefore two steps, and only the second is machine-specific:

```bash
codex plugin marketplace add /path/to/PhysEarth-Agent
codex plugin add geoai@physearth-agent
codex mcp add geoai -- "$PWD/.venv/bin/python" "$PWD/integrations/geoai/mcp_server.py" --stdio
```

That third command is the same one `integrations/codex/README.md` gives, and it is the one that has to
know where your interpreter and checkout are. Nothing is lost by leaving it out of the manifest:
a plugin that installs cleanly and then offers no tools, with nothing in any log, is exactly the
failure mode this package spent its effort removing.

## Verified

```
codex plugin marketplace add <repo>              → Added marketplace `physearth-agent`
codex plugin add geoai@physearth-agent           → Installed plugin root: …/plugins/cache/physearth-agent/geoai/1.0.0
codex debug prompt-input "sweep snow…"           → skill root: …/plugins/cache/physearth-agent
                                                   Available skills: … geoai: Answer geophysical …
```

That last line is the point of the plugin: from a working directory with no relationship to this
repository, the skill still reaches the model. Run
`python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .` from here before
changing anything — the manifest has required fields (`author.name`, five `interface` strings,
`interface.defaultPrompt` or `default_prompt`) and rejects unknown ones.

## Two maintenance facts

- The skill here is a **copy** of `.agents/skills/geoai/`, because the repository-scoped skill is
  what Codex finds in the checkout and this one is what it finds after an install.
  `tests/test_codex_integration.py` asserts the two are byte-identical, so they cannot drift.
- The cache is keyed by `version`. Bump it in `.codex-plugin/plugin.json` and reinstall to see a
  change; editing this directory alone changes nothing for an installed copy.
