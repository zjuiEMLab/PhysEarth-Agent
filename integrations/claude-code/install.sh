#!/usr/bin/env bash
# Install the PhysEarth Geo-AI plugin for Claude Code, and the two settings a plugin cannot set.
#
# What the plugin brings on its own (installed by `claude plugin install`, no script needed):
#   skills/geoai/          the workflow the model follows with the engine's tools
#   output-styles/         the answer discipline — the one mechanism that changes every
#                          response's *text* with no user action (`force-for-plugin: true`)
#   themes/                the Geo-AI colour scheme
#
# The server's 28 tools are NOT in that list on purpose; this script registers the MCP server
# instead. The measurement behind that is in the MCP section below.
#
# What only a settings file can do, and why this script exists:
#   statusLine             Claude Code renders ANSI colour from a status-line command's stdout,
#                          but a plugin cannot supply a default one — only `subagentStatusLine`.
#                          So the coloured line is written here, into the user's settings.
#   theme                  a plugin supplies a theme; it cannot activate it either.
#
# Scopes: `project` writes <repo>/.claude/settings.json (honoured only after the workspace trust
# dialog), `user` writes ~/.claude/settings.json. Default is `user`, because the colour of your
# terminal is not a property of this repository.
#
# Usage:
#   integrations/claude-code/install.sh                     # install plugin + settings (user scope)
#   integrations/claude-code/install.sh --scope project
#   integrations/claude-code/install.sh --plugin-only       # no settings changes at all
#   integrations/claude-code/install.sh --check             # report state, change nothing
#   HOME=/tmp/scratch integrations/claude-code/install.sh   # test in a throwaway home

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=integrations/lib/find-python.sh
. "$ROOT/integrations/lib/find-python.sh"
PLUGIN_NAME="geoai-claude"
MARKETPLACE="physearth-agent"
SCOPE="user"
DO_SETTINGS=1
CHECK=0

while [ $# -gt 0 ]; do
  case "$1" in
    --scope) SCOPE="${2:-user}"; shift 2 ;;
    --plugin-only) DO_SETTINGS=0; shift ;;
    --check) CHECK=1; shift ;;
    -h|--help) sed -n '2,26p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if ! command -v claude >/dev/null 2>&1; then
  cat >&2 <<'MESSAGE'
The `claude` CLI is not on PATH.

  npm install -g @anthropic-ai/claude-code     # or see https://code.claude.com/docs

Then re-run this script.
MESSAGE
  exit 1
fi
echo "claude:    $(claude --version 2>/dev/null | head -1)"
echo "plugin:    $PLUGIN_NAME@$MARKETPLACE (scope: $SCOPE)"
echo "settings:  $([ "$DO_SETTINGS" = 1 ] && echo "will be written" || echo "left alone")"

settings_path() {
  case "$SCOPE" in
    user) echo "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" ;;
    project) echo "$ROOT/.claude/settings.json" ;;
    local) echo "$ROOT/.claude/settings.local.json" ;;
    *) echo "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" ;;
  esac
}

# Both interpreters are resolved here, before the --check branch, rather than after it. That
# branch reads the settings file with one of them, and under `set -u` reaching it unset is an
# "unbound variable" crash — inside the one code path whose whole job is to keep working on a
# broken install.
#
# ENGINE_PYTHON is the interpreter that can import `integrations.geoai.service`; PYTHON_BIN is
# whatever runs the status line. The status line needs nothing but the standard library, so it
# prefers the engine interpreter and falls back to any interpreter at all: a coloured status line
# in a checkout whose environment is still being built is worth more than a blank one.
ENGINE_PYTHON="$(physearth_find_python_for_engine "$ROOT" || true)"
PYTHON_BIN="${ENGINE_PYTHON:-$(physearth_find_python "import json" || true)}"

if [ "$CHECK" = "1" ]; then
  echo
  claude plugin list 2>&1 | head -20
  echo
  claude plugin details "$PLUGIN_NAME" 2>&1 | head -30
  echo
  path="$(settings_path)"
  if [ -f "$path" ]; then
    echo "settings: $path"
    "$PYTHON_BIN" - "$path" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
print(f"  theme:      {data.get('theme', '(default)')}")
line = data.get("statusLine")
print(f"  statusLine: {line.get('command') if isinstance(line, dict) else '(none)'}")
PY
  else
    echo "settings: $path does not exist"
  fi
  exit 0
fi

# ── The plugin ───────────────────────────────────────────────────────────────────────────────
echo
echo "==> claude plugin marketplace add $ROOT --scope $SCOPE"
claude plugin marketplace add "$ROOT" --scope "$SCOPE" 2>&1 | head -5
echo "==> claude plugin install $PLUGIN_NAME@$MARKETPLACE --scope $SCOPE"
claude plugin install "$PLUGIN_NAME@$MARKETPLACE" --scope "$SCOPE" 2>&1 | head -5

# ── The MCP server, registered with absolute paths ───────────────────────────────────────────
#
# The plugin does NOT bundle an MCP entry, and that is a measured decision rather than a
# preference. `claude plugin install` copies the plugin into
# ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/, so a bundled `.mcp.json` could only
# reach the engine through a machine-specific absolute path. The relative form is worse than
# useless: with `command: python3, env.PYTHONPATH: src` it resolved to a system Python without
# PyYAML and reported "✗ Failed to connect" — a plugin that installs cleanly and offers no tools.
#
# The file form of the server is registered instead, because it needs neither `cwd` nor
# PYTHONPATH: `mcp_server.py` adds the repository root and `src/` to sys.path from its own
# location. That reduces this step to naming an interpreter that can import the engine.
if [ -z "$ENGINE_PYTHON" ]; then
  echo "WARNING: no interpreter could import integrations.geoai.service." >&2
  echo "         The skill, output style and theme still work; every engine tool will fail." >&2
  echo "         Install the environment (uv sync --extra dev), then re-run." >&2
else
  echo "==> claude mcp add geoai -- $ENGINE_PYTHON $ROOT/integrations/geoai/mcp_server.py --stdio"
  claude mcp remove geoai --scope "$SCOPE" >/dev/null 2>&1 || true
  claude mcp add geoai --scope "$SCOPE" -- \
    "$ENGINE_PYTHON" "$ROOT/integrations/geoai/mcp_server.py" --stdio 2>&1 | head -5
fi

# ── The two settings a plugin cannot set ─────────────────────────────────────────────────────
if [ -z "$PYTHON_BIN" ]; then
  echo "No interpreter on PATH can run the status line. Skipping the settings half." >&2
  exit 1
fi

if [ "$DO_SETTINGS" = "1" ]; then
  PATH_JSON="$(settings_path)"
  mkdir -p "$(dirname "$PATH_JSON")"
  if [ -f "$PATH_JSON" ]; then
    cp "$PATH_JSON" "$PATH_JSON.bak-$(date +%Y%m%d-%H%M%S)"
    echo "==> backed up $PATH_JSON"
  fi
  "$PYTHON_BIN" - "$PATH_JSON" "$ROOT/integrations/claude-code/$PLUGIN_NAME/scripts/statusline.py" "$PLUGIN_NAME" "$PYTHON_BIN" <<'PY'
import json
import os
import shlex
import sys

path, statusline, plugin, python_bin = sys.argv[1:5]
data = {}
if os.path.exists(path):
    try:
        with open(path) as handle:
            data = json.load(handle)
    except ValueError:
        data = {}

data["theme"] = f"custom:{plugin}:geoai-night"
data["statusLine"] = {
    "type": "command",
    # The interpreter this script *proved*, not `python3`: the status line is rendered by a
    # subprocess of the editor, whose PATH is not this shell's, and quoting is shlex's job
    # because a checkout path may contain spaces.
    "command": f"{shlex.quote(python_bin)} {shlex.quote(statusline)}",
    "padding": 0,
    "refreshInterval": 10,
}
with open(path, "w") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
print(f"==> wrote theme + statusLine to {path}")
PY
fi

cat <<NEXT

Next steps
  1. start a NEW Claude Code session — plugins, the output style and the MCP server are read at
     session start
  2. confirm the tools are there:     claude mcp list | grep geoai
  3. confirm the plugin is enabled:   claude plugin list
  4. in the session:  /output-style geoai-brief   (or rely on force-for-plugin, which applies it
     without asking), then look at the status line for the coloured Geo-AI row

Verify later without changing anything:
  integrations/claude-code/install.sh --check
NEXT
