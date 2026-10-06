#!/usr/bin/env bash
# Install this plugin into a local DeepSeek Harness profile.
#
# Usage:
#   integrations/dsh/scripts/install.sh                              # into $DSH_PROFILE (default web)
#   DSH_PROFILE=physearth-verify integrations/dsh/scripts/install.sh
#   scripts/verify-profile.sh physearth-verify 3199                      # create + install a throwaway one
#
# Four things happen, and each one exists because a live boot said so.
#
# 1. RESOLVE THE INTERPRETER. The search is `integrations/lib/find-python.sh`, shared with the Codex
#    and Claude integrations — every one of them had written the same wrong candidate list. A
#    candidate is accepted only after it imports `integrations.physearth.service`, and not
#    `physearth`: that package's `__init__` is lazy, so `import physearth` succeeds on an
#    interpreter with no PyYAML, and the row then mounts and offers an empty tool list with
#    nothing in the log.
#
# 2. MAKE THE PACKAGE RESOLVABLE FROM THE PROFILE. `@deepseek-ai/schemastery` is a peer the host
#    supplies; the entry imports it by name. Node resolves a bare specifier from the *realpath*
#    of the importing file, so a symlink pointing back into the checkout resolves from the
#    checkout and finds nothing. The package is therefore COPIED into the profile's
#    node_modules, which both puts it inside the resolution walk that reaches
#    `<profile>/node_modules/@deepseek-ai/schemastery` and keeps `require.resolve` working from
#    the profile as `createRequire(ctx.baseUrl)` needs. `dsh plugin add` is preferred when the
#    CLI is on PATH, because that is the supported path and does all of this itself.
#
# 3. WRITE THE PATH-BEARING OVERRIDE. The bundle patch ships a complete, path-free MCP row; a
#    patch layer cannot carry a checkout path. It also cannot *add* one field to that row: the
#    harness composes layers with a shallow per-entry assignment, so `config` is replaced
#    wholesale. So this step reads the row's config out of the bundle patch — one source of
#    truth — substitutes absolute `command`, `cwd` and `env.PYTHONPATH`, and writes the complete
#    object into the profile's own cordis.patch.yml, inside a managed block. That layer is the
#    one the harness reads at boot and the one that survives a restart.
#
# 4. SAY WHAT TO CHECK. The printed commands are the ones that actually distinguish success
#    from a plugin that mounted and does nothing.
#
# Idempotent: running it twice leaves one copy, one block and one bundle membership.

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKOUT="$(git -C "$PLUGIN_DIR" rev-parse --show-toplevel 2>/dev/null || echo "")"
PROFILE="${DSH_PROFILE:-web}"
DSH_HOME="${DSH_HOME:-$HOME/.dsh}"
PROFILE_DIR="$DSH_HOME/profiles/$PROFILE"
PATCH="$PROFILE_DIR/cordis.patch.yml"
PACKAGE_NAME="dsh-plugin-physearth"
BLOCK_BEGIN="# >>> physearth (written by integrations/dsh/scripts/install.sh)"
BLOCK_END="# <<< physearth"

if [ -z "$CHECKOUT" ]; then
  echo "Cannot find the repository root: run this from a git checkout." >&2
  exit 1
fi
echo "checkout:  $CHECKOUT"
echo "profile:   $PROFILE_DIR"

# ── 1. The interpreter ──────────────────────────────────────────────────────────────────────
# The search itself is `integrations/lib/find-python.sh`, shared with the Codex and Claude
# integrations. It has to be sourced after the checkout is known, which is why the root is
# resolved with git rather than assumed to be two directories up: this script also ships inside
# the plugin bundle.
# shellcheck source=integrations/lib/find-python.sh
. "$CHECKOUT/integrations/lib/find-python.sh"

if PYTHON="$(physearth_find_python_for_engine "$CHECKOUT" || true)" && [ -n "$PYTHON" ]; then
  echo "python:    $PYTHON (imports the bridge service)"
else
  PYTHON="python3"
  echo "python:    $PYTHON — WARNING: no candidate could import integrations.physearth.service." >&2
  echo "           The rows will mount and every physics tool will refuse. Install first:" >&2
  echo "             uv sync --extra dev        # or: pip install -e backend, plus pyyaml/numpy" >&2
  echo "           then re-run as:  PHYSEARTH_PYTHON=/path/to/python $0" >&2
fi

# ── 2. The package, resolvable from the profile ─────────────────────────────────────────────
if command -v dsh >/dev/null 2>&1; then
  echo "==> dsh plugin --profile $PROFILE add $PLUGIN_DIR"
  dsh plugin --profile "$PROFILE" add "$PLUGIN_DIR" \
    || echo "    dsh plugin add reported a failure; continuing with the copy below"
fi

if [ ! -d "$PROFILE_DIR" ]; then
  echo "No profile at $PROFILE_DIR yet: run 'dsh web' once (or scripts/verify-profile.sh), then re-run." >&2
  exit 1
fi

NODE_MODULES="$PROFILE_DIR/node_modules"
TARGET="$NODE_MODULES/$PACKAGE_NAME"
mkdir -p "$NODE_MODULES"
rm -rf "$TARGET"
mkdir -p "$TARGET"
# `cp -R` of an explicit list rather than of the directory: a symlink would resolve from the
# checkout, and a wholesale copy would drag in tests and a leftover node_modules.
for item in entry.js lib cordis.patch.yml package.json README.md; do
  cp -R "$PLUGIN_DIR/$item" "$TARGET/"
done
echo "==> copied the package to $TARGET"

# The host supplies schemastery; make sure it is reachable from the profile. Walking up from the
# copied package, Node skips `<profile>/node_modules` (it is already named node_modules) and
# lands on `<profile>/node_modules` — so this one link is what the entry's import needs.
#
# The harness installation is found rather than assumed: `dsh` is not on PATH when the profile is
# booted through npx, which is how this was discovered. Candidates in order of how deliberate
# they are.
find_dsh_install() {
  local candidate
  for candidate in "${DSH_INSTALL_DIR:-}" "$DSH_HOME/node_modules"; do
    [ -n "$candidate" ] && [ -d "$candidate/@deepseek-ai/schemastery" ] && { echo "$candidate"; return 0; }
  done
  if command -v dsh >/dev/null 2>&1; then
    local bin
    bin="$(readlink -f "$(command -v dsh)" 2>/dev/null || readlink "$(command -v dsh)" 2>/dev/null || echo "")"
    # …/node_modules/@deepseek-ai/dsh/lib/bin.js -> …/node_modules
    candidate="$(cd "$(dirname "$bin")/../../.." 2>/dev/null && pwd || echo "")"
    [ -n "$candidate" ] && [ -d "$candidate/@deepseek-ai/schemastery" ] && { echo "$candidate"; return 0; }
  fi
  # npx keeps each package under ~/.npm/_npx/<hash>/node_modules.
  for candidate in "$HOME"/.npm/_npx/*/node_modules; do
    [ -d "$candidate/@deepseek-ai/schemastery" ] && { echo "$candidate"; return 0; }
  done
  return 1
}

mkdir -p "$NODE_MODULES/@deepseek-ai"
if DSH_INSTALL_DIR="$(find_dsh_install)"; then
  for peer in schemastery cosmokit; do
    if [ ! -e "$NODE_MODULES/@deepseek-ai/$peer" ] && [ -d "$DSH_INSTALL_DIR/@deepseek-ai/$peer" ]; then
      ln -sfn "$DSH_INSTALL_DIR/@deepseek-ai/$peer" "$NODE_MODULES/@deepseek-ai/$peer"
      echo "==> linked @deepseek-ai/$peer from $DSH_INSTALL_DIR"
    fi
  done
else
  echo "    NOTE: no directory holding @deepseek-ai/schemastery was found." >&2
  echo "          Set DSH_INSTALL_DIR to the harness' node_modules, or run" >&2
  echo "          'dsh plugin --profile $PROFILE install', or the plugin row will fail to import." >&2
fi

# Bundle membership is what mounts the plugin's own bundle patch, which is what inserts the rows.
"$PYTHON" - "$PROFILE_DIR/package.json" "$PACKAGE_NAME" <<'PY'
import json
import sys

path, package = sys.argv[1], sys.argv[2]
with open(path) as handle:
    manifest = json.load(handle)
bundles = manifest.setdefault("dsh", {}).setdefault("profile", {}).setdefault("bundles", [])
if package in bundles:
    print(f"==> {package} is already a profile bundle")
else:
    bundles.append(package)
    with open(path, "w") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(f"==> added {package} to dsh.profile.bundles")
PY

# ── 3. The path-bearing override ────────────────────────────────────────────────────────────
# Both rows are read back out of the bundle patch and completed with this machine's answers, so
# there is exactly one description of each row in the repository and the override is always a
# complete object. Two facts force that:
#
#   - a patch layer cannot carry an absolute checkout path;
#   - the harness composes layers with a shallow per-entry assignment, so a targeted `config`
#     REPLACES the row's own rather than merging into it. A partial override here silently
#     stripped `serverName`/`args` off the MCP row and the loader refused the whole tree.
#
# The plugin row needs one field the plugin cannot discover: which Python. It resolves the
# checkout itself (walking up from its own file) and it *verifies* interpreters it is offered,
# but `python3` on this machine is a bare system interpreter with no PyYAML, so guessing is not
# good enough — the installer knows, because it proved it above.
"$PYTHON" - "$PATCH" "$PLUGIN_DIR/cordis.patch.yml" "$CHECKOUT" "$PYTHON" "$BLOCK_BEGIN" "$BLOCK_END" <<'PY'
import sys

import yaml

patch_path, bundle_path, checkout, python_cmd, begin, end = sys.argv[1:7]

with open(bundle_path) as handle:
    bundle = yaml.safe_load(handle)
rows = {entry["id"]: entry for group in bundle for entry in group.get("insert", [])}

plugin_config = dict(rows["physearth"]["config"])
plugin_config["projectRoot"] = checkout
plugin_config["pythonCmd"] = python_cmd

mcp_config = dict(rows["mcp-physearth"]["config"])
mcp_config["command"] = python_cmd
mcp_config["cwd"] = checkout
mcp_config["env"] = {**mcp_config.get("env", {}), "PYTHONPATH": f"{checkout}/src:{checkout}"}

body = yaml.safe_dump(
    [
        {"id": "physearth", "config": plugin_config},
        {"id": "mcp-physearth", "config": mcp_config},
    ],
    sort_keys=False,
    default_flow_style=False,
    allow_unicode=True,
).rstrip("\n")

block = f"""{begin}
# Id-targeted overrides for this plugin's two rows. Complete, not partial: the harness composes
# patch layers with a shallow per-entry assignment, so a `config` here REPLACES the row's own —
# which is why this block restates every key rather than adding one field to it. The keys come
# from the bundle patch (integrations/dsh/cordis.patch.yml), with the interpreter and the
# checkout resolved for this machine. Re-run the installer after moving the checkout; delete the
# block to fall back to the bundle patch's path-free defaults.
#
# A --patch overlay or a later layer still wins over these rows, so the switch and any
# per-boot override behave as documented.
{body}
{end}
"""

try:
    with open(patch_path) as handle:
        current = handle.read()
except FileNotFoundError:
    current = "# Your patch layer for this dsh profile.\n[]\n"

if begin in current and end in current:
    head, rest = current.split(begin, 1)
    _, tail = rest.split(end, 1)
    updated = head + block + tail.lstrip("\n")
    action = "replaced"
else:
    stripped = current.rstrip("\n")
    if stripped.endswith("[]"):
        stripped = stripped[: -len("[]")].rstrip("\n")
    updated = f"{stripped}\n\n{block}"
    action = "appended"

with open(patch_path, "w") as handle:
    handle.write(updated)
print(f"==> {action} the managed block in {patch_path}")
PY

cat <<NEXT

Next steps
  1. start or restart the harness:      dsh --profile $PROFILE
  2. confirm the row carries your paths:
       dsh --profile $PROFILE --dump-config | grep -A12 'id: mcp-physearth'
  3. confirm the Python side answers:
       cd $CHECKOUT && PYTHONPATH=src:. $PYTHON -m integrations.physearth health
  4. confirm the browser half is served (with the harness running on PORT):
       curl -s http://127.0.0.1:PORT/ | grep -o '$PACKAGE_NAME[^"]*'
       curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:PORT/plugins/$PACKAGE_NAME/client.js
  5. in the browser: 设置 → 插件 → PhysEarth Geo-AI → flip the switch.
     On:  the palette turns Geo-AI (dark surface, ice/amber accent, monospace numbers),
          tools appear as mcp__physearth__*, and the system prompt gains the citation and unit rules.
     Off: palette back to the host default, tools and prompt section gone, bridge released.
NEXT
