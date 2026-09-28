#!/usr/bin/env bash
# Install this plugin into the local DeepSeek Harness web profile.
#
# What it does, in order, and why:
#   1. resolves the checkout root, because the bundle patch and the MCP row both need an
#      absolute path to this repository (the engine's knowledge, models and prompts are found
#      by walking up from backend/);
#   2. prefers `dsh plugin add`, which installs the package and applies its bundle patch the
#      supported way;
#   3. otherwise links the package into the profile's node_modules and writes the two rows
#      into the profile's own cordis.patch.yml — the layer that survives a restart, because
#      runtime loader updates are not persisted by the harness;
#   4. prints the two commands that prove it worked.
#
# Idempotent: running it twice leaves one row of each kind.

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKOUT="$(git -C "$PLUGIN_DIR" rev-parse --show-toplevel 2>/dev/null || echo "")"
PROFILE="${DSH_PROFILE:-web}"
DSH_HOME="${DSH_HOME:-$HOME/.dsh}"
PROFILE_DIR="$DSH_HOME/profiles/$PROFILE"
PATCH="$PROFILE_DIR/cordis.patch.yml"
PROFILE_PATCH="$PROFILE_DIR/physearth-geoai.patch.yml"

if [ -z "$CHECKOUT" ]; then
  echo "Cannot find the repository root: run this from a git checkout." >&2
  exit 1
fi
echo "checkout: $CHECKOUT"
echo "profile:  $PROFILE_DIR"

if command -v dsh >/dev/null 2>&1; then
  echo "==> dsh plugin add $PLUGIN_DIR"
  dsh plugin add "$PLUGIN_DIR" || echo "dsh plugin add reported a failure; falling back to a link + patch layer"
fi

if [ ! -d "$PROFILE_DIR" ]; then
  echo "No profile at $PROFILE_DIR yet: run 'dsh web' once, then re-run this script." >&2
  exit 1
fi

# Fallback / belt-and-braces: link the package so the loader can resolve its name, and write a
# profile-layer patch that carries the resolved checkout path (the bundle patch ships a
# placeholder so nobody has to trust a guess at where this repository lives).
NODE_MODULES="$PROFILE_DIR/node_modules"
mkdir -p "$NODE_MODULES"
if [ ! -e "$NODE_MODULES/dsh-plugin-physearth-geoai" ]; then
  ln -sfn "$PLUGIN_DIR" "$NODE_MODULES/dsh-plugin-physearth-geoai"
  echo "==> linked $NODE_MODULES/dsh-plugin-physearth-geoai"
fi

cat > "$PROFILE_PATCH" <<YAML
# Written by integrations/dsh/scripts/install.sh — the path-bearing layer.
#
# A profile layer is what makes the switch durable: the harness rewrites the generated root
# cordis.yml on every boot, so an entry only survives if it lives in a layer like this one.
# Later layers (--patch overlays) still override these rows by id.

- id: geoai
  config:
    projectRoot: $CHECKOUT

- id: mcp-geoai
  config:
    cwd: $CHECKOUT
YAML
echo "==> wrote $PROFILE_PATCH"

if [ -f "$PATCH" ]; then
  echo
  echo "If your profile does not already include this plugin's bundle patch, add:"
  echo "  - include: $PLUGIN_DIR/cordis.patch.yml"
  echo "to $PATCH"
fi

cat <<NEXT

Next steps
  1. start or restart the harness:      dsh web
  2. confirm the rows are live:         dsh --profile $PROFILE --dump-config | grep -A3 -E '(geoai|mcp-geoai)'
  3. confirm the Python side answers:   cd $CHECKOUT && python -m integrations.geoai health
  4. in the browser: 设置 → 插件 → PhysEarth Geo-AI → flip the switch, then refresh the page.
     On:  the palette turns Geo-AI (dark surface, ice/amber accent), tools appear as
          mcp__geoai__*, and the system prompt gains the citation and unit rules.
     Off: palette back to the host default, tools and prompt section gone, bridge process
          released.
NEXT
