#!/usr/bin/env bash
# Is the PhysEarth-Agent MCP server actually usable from Codex on this machine?
#
# Every check here exists because its absence looked like something else:
#
#   - an interpreter that cannot import the engine makes the server start with an EMPTY tool
#     list and no error anywhere, so "no tools" is checked before "is it registered";
#   - `python` is absent on macOS and most Linux distributions;
#   - the default 10 s startup timeout is tight for a scientific Python import;
#   - a missing inference credential breaks exactly one tool (`geoai_ask`), so it is reported as
#     a degradation rather than a failure.
#
# Exit code 0 when the tools are reachable, 1 otherwise. Safe to run any time: it starts the
# server, asks it two questions over stdio, and stops it.
#
# Usage:
#   scripts/codex-doctor.sh                 # discover the interpreter
#   PHYSEARTH_PYTHON=/abs/py scripts/codex-doctor.sh
#   CODEX_HOME=/tmp/scratch scripts/codex-doctor.sh   # inspect a different Codex home

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/find-python.sh
. "$ROOT/scripts/lib/find-python.sh"
SERVER="$ROOT/integrations/geoai/mcp_server.py"
NAME="${GEOAI_MCP_NAME:-geoai}"
failures=0
notes=()

ok()   { printf '  \033[32mok\033[0m    %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; failures=$((failures + 1)); }
warn() { printf '  \033[33mwarn\033[0m  %s\n' "$1"; notes+=("$1"); }

echo "repository: $ROOT"
echo

# ── 1. The server itself ────────────────────────────────────────────────────────────────────
echo "server"
if [ ! -f "$SERVER" ]; then
  bad "integrations/geoai/mcp_server.py is missing"
  exit 1
fi
ok "found $SERVER"

PYTHON="$(physearth_find_python_for_engine "$ROOT" || true)"
if [ -z "$PYTHON" ]; then
  bad "no interpreter could import the engine."
  echo "        Install it (uv sync --extra dev), then re-run with PHYSEARTH_PYTHON=/path/to/python."
  echo "        Codex would show this as a server with no tools."
  exit 1
fi
ok "interpreter: $PYTHON"

# The file form is what the docs register, so exercise that one, with cwd somewhere unrelated
# to prove the file bootstraps its own paths.
probe="$(mktemp -d)"
reply="$(
  cd "$probe" && printf '%s\n' \
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"doctor","version":"1"}}}' \
    '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | "$PYTHON" "$SERVER" --stdio 2>"$probe/stderr.log"
)"
rm -rf "$probe"

if [ -z "$reply" ]; then
  bad "the server produced no JSON-RPC response"
  exit 1
fi

count="$(printf '%s' "$reply" | "$PYTHON" -c '
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    message = json.loads(line)
    if message.get("id") == 2:
        print(len(message["result"]["tools"]))
        break
else:
    print(0)
')"
if [ "${count:-0}" -ge 1 ]; then
  ok "tools/list answered with $count tools"
else
  bad "tools/list answered with no tools"
  exit 1
fi

for tool in run_model plot geoai_health geoai_evidence; do
  if printf '%s' "$reply" | grep -q "\"$tool\""; then
    ok "tool present: $tool"
  else
    bad "tool missing: $tool"
  fi
done

# ── 2. Registration in Codex ────────────────────────────────────────────────────────────────
echo
echo "codex"
if ! command -v codex >/dev/null 2>&1; then
  warn "the codex CLI is not on PATH; skipping the registration checks"
else
  version="$(codex --version 2>/dev/null | head -1)"
  ok "codex CLI: ${version:-unknown}"

  if codex mcp list 2>/dev/null | grep -q "^$NAME\b\|[[:space:]]$NAME[[:space:]]"; then
    ok "registered as '$NAME'"
    if command -v python3 >/dev/null 2>&1; then
      codex mcp get "$NAME" --json 2>/dev/null | python3 -c '
import json, sys
try:
    entry = json.load(sys.stdin)
except Exception:
    raise SystemExit(0)
transport = entry.get("transport") or {}
print("  ok    transport: %s" % transport.get("type"))
print("  ok    command:   %s" % transport.get("command"))
if not entry.get("enabled", True):
    print("  warn  enabled:   false — the server is registered but switched off")
if transport.get("command") and transport["command"] in ("python",):
    print("  warn  command is bare `python`, which does not exist on macOS or most Linux systems")
'
    fi
  else
    warn "not registered with this Codex home."
    echo "        codex mcp add $NAME -- $PYTHON $SERVER --stdio"
  fi
fi

# ── 3. The one optional credential ──────────────────────────────────────────────────────────
echo
echo "credentials"
if [ -n "${PHYSEARTH_LLM_API_KEY:-}" ]; then
  ok "PHYSEARTH_LLM_API_KEY is set: the agent turn (geoai_ask) is available"
else
  warn "PHYSEARTH_LLM_API_KEY is unset. Everything except geoai_ask works; that tool refuses in one line"
fi

echo
if [ "$failures" -eq 0 ]; then
  echo "Geo-AI tools are reachable from "$PYTHON"."
  [ "${#notes[@]}" -gt 0 ] && printf 'Notes:\n' && for note in "${notes[@]}"; do printf '  - %s\n' "$note"; done
  exit 0
fi
echo "$failures check(s) failed."
exit 1
