#!/usr/bin/env bash
# Install the PhysEarth Geo-AI colour scheme for the Codex TUI.
#
# Why a theme at all: a Codex plugin cannot add a panel, a widget or a status-line item of its
# own. Colour is what is left, and Codex supports it properly — it reads TextMate/Sublime
# `.tmTheme` files from $CODEX_HOME/themes/, offers them under `/theme`, and persists the choice
# as `tui.theme`. So this script puts the scheme where Codex looks for it, checks that it is a
# well-formed plist before claiming success, and prints the one step that is the user's.
#
# It does NOT edit config.toml unless asked (`--write-config`), because the convention for Codex
# is that the tool writes the config, not the installer — and there is no `codex` command for
# "select this theme". With `--write-config` it backs the file up first and appends a managed
# block, so removing it is deleting a marked region rather than untangling a merge.
#
# Usage:
#   scripts/codex-theme-install.sh                  # copy the theme, print the next step
#   scripts/codex-theme-install.sh --write-config   # and set tui.* in $CODEX_HOME/config.toml
#   CODEX_HOME=/tmp/scratch scripts/codex-theme-install.sh
#   scripts/codex-theme-install.sh --check          # verify an installed copy, change nothing

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME_SRC="$ROOT/codex/geoai.tmTheme"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
THEMES_DIR="$CODEX_HOME/themes"
THEME_ID="geoai"
CONFIG="$CODEX_HOME/config.toml"
BEGIN="# >>> physearth-geoai (written by scripts/codex-theme-install.sh)"
END="# <<< physearth-geoai"

WRITE_CONFIG=0
CHECK=0
for argument in "$@"; do
  case "$argument" in
    --write-config) WRITE_CONFIG=1 ;;
    --check) CHECK=1 ;;
    -h|--help) sed -n '2,18p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown argument: $argument" >&2; exit 2 ;;
  esac
done

echo "codex home: $CODEX_HOME"

# A Python that can read a plist is the validator: a .tmTheme *is* an XML plist, so "did Codex
# accept it" starts with "is it a plist at all". Finding one that imports plistlib is the same
# candidate search the rest of this repository uses, for the same reason — `python3` on PATH is
# not reliably the interpreter with the libraries.
PY=""
for candidate in "${PHYSEARTH_PYTHON:-}" python3 python; do
  [ -n "$candidate" ] || continue
  command -v "$candidate" >/dev/null 2>&1 || continue
  if "$candidate" -c "import plistlib" >/dev/null 2>&1; then PY="$candidate"; break; fi
done
if [ -z "$PY" ]; then
  echo "No Python with plistlib was found, so the theme cannot be validated. Install python3." >&2
  exit 1
fi

validate() {
  "$PY" - "$1" <<'PY'
import plistlib
import sys

path = sys.argv[1]
with open(path, "rb") as handle:
    theme = plistlib.load(handle)

problems = []
if not isinstance(theme, dict):
    problems.append("the root is not a dict")
name = theme.get("name")
if not isinstance(name, str) or not name.strip():
    problems.append("no `name` (Codex shows this in /theme)")
settings = theme.get("settings")
if not isinstance(settings, list) or not settings:
    problems.append("no `settings` array")
else:
    globals_ = [s for s in settings if "scope" not in s]
    if not globals_:
        problems.append("no global setting block (background/foreground live there)")
    for entry in settings:
        if not isinstance(entry, dict) or "settings" not in entry:
            problems.append(f"malformed entry: {entry!r}")
            continue
        colours = [v for k, v in entry["settings"].items() if k in {"background", "foreground", "caret", "selection"}]
        for value in colours:
            if not isinstance(value, str) or not value.startswith("#"):
                problems.append(f"colour {value!r} is not a #rrggbb string")

if problems:
    print("INVALID: " + "; ".join(problems))
    raise SystemExit(1)
print(f"valid plist: name={name!r}, {len(settings)} blocks, "
      f"{sum(1 for s in settings if 'scope' in s)} scoped")
PY
}

if [ "$CHECK" = "1" ]; then
  target="$THEMES_DIR/$THEME_ID.tmTheme"
  [ -f "$target" ] || { echo "not installed: $target" >&2; exit 1; }
  validate "$target"
  grep -q '^theme = "geoai"' "$CONFIG" 2>/dev/null \
    && echo "config: tui.theme is set" \
    || echo "config: tui.theme is not set — pick the theme in /theme, or run with --write-config"
  exit 0
fi

mkdir -p "$THEMES_DIR"
cp "$THEME_SRC" "$THEMES_DIR/$THEME_ID.tmTheme"
echo "==> copied to $THEMES_DIR/$THEME_ID.tmTheme"
validate "$THEMES_DIR/$THEME_ID.tmTheme"

if [ "$WRITE_CONFIG" = "0" ]; then
  cat <<NEXT

Next step — pick it in the TUI:
  /theme        then choose "PhysEarth Geo-AI"

To make it the stored default instead, add this to $CONFIG yourself, or re-run with
--write-config and let this script append it:

  [tui]
  theme = "$THEME_ID"
  status_line_use_colors = true

For the status line's own item list, use the TUI picker — it writes the correct ids, and an
unknown id would be silently empty rather than an error:
  /statusline

(\`codex/config-theme.snippet.toml\` records which keys were verified, how, and why the item ids
are left to the picker.)
NEXT
  exit 0
fi

# ── --write-config: append, never merge into, an existing file ───────────────────────────────
mkdir -p "$CODEX_HOME"
if [ -f "$CONFIG" ]; then
  backup="$CONFIG.bak-$(date +%Y%m%d-%H%M%S)"
  cp "$CONFIG" "$backup"
  echo "==> backed up $CONFIG to $backup"
else
  : > "$CONFIG"
  echo "==> created $CONFIG"
fi

block="$BEGIN
# Geo-AI colour scheme, plus the one text surface a config file can set safely on its own.
# Delete this block to go back to the default theme; the scheme file itself is inert until
# something selects it.
#
# Only these two keys are written, and each was probed against codex-cli for its type: theme is a
# string, status_line_use_colors is a boolean. The status_line and terminal_title keys take lists
# of item ids, and an unknown id is accepted at load and filtered later — so a wrong id is
# silently empty rather than an error. Codex's own picker writes those ids correctly, which is why
# this script does not guess them:  /statusline
[tui]
theme = \"$THEME_ID\"
status_line_use_colors = true
$END"

if grep -qF "$BEGIN" "$CONFIG"; then
  "$PY" - "$CONFIG" "$BEGIN" "$END" "$block" <<'PY'
import sys

path, begin, end, block = sys.argv[1:5]
with open(path) as handle:
    text = handle.read()
head, rest = text.split(begin, 1)
_, tail = rest.split(end, 1)
with open(path, "w") as handle:
    handle.write(head + block + tail)
print("==> replaced the managed block")
PY
else
  printf '\n%s\n' "$block" >> "$CONFIG"
  echo "==> appended the managed block"
fi

cat <<NEXT

Restart Codex (or open /theme once) and the scheme is active.

Verify:
  scripts/codex-theme-install.sh --check
NEXT
