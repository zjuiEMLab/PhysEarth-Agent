#!/usr/bin/env bash
# Create (or refresh) an isolated profile that carries only this plugin, and install into it.
#
# Why a separate profile rather than the live one: verifying this plugin means flipping a
# switch that mounts and unmounts rows and overrides the whole theme. Doing that inside
# somebody's working profile is how you lose an afternoon. A second profile on a high port has
# its own sessions, its own settings document and its own patch layers, so the two cannot
# interfere, and the result is either "the plugin works" or "the plugin is broken" with nothing
# else in the way.
#
# A profile is created by writing a manifest with `dsh.profile.bundles`; the harness resolves
# those bundle packages from its own installation, so no network install is involved. The name
# is not one of the shipped templates, which is exactly why it does not touch `web`.
#
# Usage:
#   scripts/verify-profile.sh [name] [port]
#
# Then:
#   dsh --profile <name> --port <port>      # boot it
#   open http://127.0.0.1:<port>/           # 设置 → 插件 → PhysEarth Geo-AI
#
# Remove it when done:  rm -rf "${DSH_HOME:-$HOME/.dsh}/profiles/<name>"

set -euo pipefail

NAME="${1:-physearth-verify}"
PORT="${2:-3199}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$HERE/.." && pwd)"
DSH_HOME="${DSH_HOME:-$HOME/.dsh}"
PROFILE_DIR="$DSH_HOME/profiles/$NAME"

if [ "$NAME" = "web" ]; then
  echo "Refusing to overwrite the 'web' profile: this script is for a throwaway profile." >&2
  exit 1
fi

mkdir -p "$PROFILE_DIR"
if [ ! -f "$PROFILE_DIR/package.json" ]; then
  cat > "$PROFILE_DIR/package.json" <<JSON
{
  "name": "dsh-profile-$NAME",
  "private": true,
  "dependencies": {},
  "dsh": {
    "profile": {
      "bundles": [
        "@deepseek-ai/dsh-base",
        "@deepseek-ai/dsh-web-app"
      ]
    }
  }
}
JSON
  echo "==> created $PROFILE_DIR (base + web-app bundles)"
fi

# The empty user layer, in the shape `initProfile` writes it, so the installer's "include the
# bundle patch" hint is not needed: the bundle patch comes in through the package manifest.
if [ ! -f "$PROFILE_DIR/cordis.patch.yml" ]; then
  cat > "$PROFILE_DIR/cordis.patch.yml" <<'YAML'
# The verification profile's own layer, applied after every bundle layer.
#
# Deliberately empty: everything this profile mounts arrives through
# dsh-plugin-physearth's own bundle patch, which is the thing under test.
[]
YAML
fi

if [ ! -f "$PROFILE_DIR/pnpm-workspace.yaml" ]; then
  cat > "$PROFILE_DIR/pnpm-workspace.yaml" <<'YAML'
packages:
  - .

nodeLinker: hoisted
autoInstallPeers: false
YAML
fi

# The installer owns everything else: the link, `dsh.profile.bundles`, the resolved interpreter,
# and the id-targeted overrides inside this profile's own patch layer.
DSH_PROFILE="$NAME" "$HERE/install.sh"

cat <<NEXT

Boot it with:
  dsh --profile $NAME --port $PORT

Then open http://127.0.0.1:$PORT/ and go to 设置 → 插件 → PhysEarth Geo-AI.

Rows must appear in the composed tree:
  dsh --profile $NAME --dump-config | grep -A4 -E '(physearth|mcp-physearth)'

Tear it down with:
  rm -rf "$PROFILE_DIR"
NEXT
