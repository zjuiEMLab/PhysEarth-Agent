#!/usr/bin/env bash
# Start the PhysEarth-Agent Studio, and print the URL it is actually on.
#
# Two things this script exists to get right, both of which fail in a way that looks like a code
# defect rather than a missing step:
#
#   1. `physearth` lives under `backend/`, so `python app.py` on its own dies with
#      `ModuleNotFoundError: No module named 'physearth'` before Gradio is even imported. The
#      supported workflow (`uv sync --extra dev`) hides this by making an editable install; a
#      plain interpreter needs `PYTHONPATH=backend`.
#   2. The interpreter that can actually import the app is not necessarily `python3`. On macOS
#      that is frequently a bare system Python with no Gradio, so candidates are *proved* by
#      importing the frontend rather than found on PATH.
#
# Usage:
#   scripts/studio.sh              # start, print the URL
#   scripts/studio.sh --open       # and open it in the default browser
#   PHYSEARTH_PORT=8000 scripts/studio.sh
#   PHYSEARTH_PYTHON=/abs/py scripts/studio.sh
#
# Environment is the same one `backend/physearth/config.py` reads, so anything the app
# understands can be set here too (see `.env.example`).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPEN=0
for argument in "$@"; do
  case "$argument" in
    --open) OPEN=1 ;;
    -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown argument: $argument" >&2; exit 2 ;;
  esac
done

# ── Which interpreter ───────────────────────────────────────────────────────────────────────
# Candidates in order of how deliberate they are, and every one of them *proved* by importing the
# app rather than found on PATH. That distinction is the whole point: on this machine `python3` is
# a system interpreter with no Gradio, so a PATH lookup finds the one interpreter that cannot run
# the Studio. Conda environments are searched by glob for the same reason — a working environment
# is usually a named env, not whatever `python3` happens to point at.
interpreter_candidates() {
  [ -n "${PHYSEARTH_PYTHON:-}" ] && echo "$PHYSEARTH_PYTHON"
  echo "$ROOT/.venv/bin/python"
  [ -n "${CONDA_PREFIX:-}" ] && echo "$CONDA_PREFIX/bin/python"

  local root env_dir
  for root in "$HOME/miniconda3" "$HOME/anaconda3" "$HOME/mambaforge" "$HOME/miniforge3" \
              /opt/miniconda3 /opt/anaconda3 /opt/homebrew/Caskroom/miniconda/base; do
    [ -d "$root/envs" ] || continue
    [ -x "$root/bin/python" ] && echo "$root/bin/python"
    # An env named for this project first, then the rest, so `physearth-agent` wins over an
    # unrelated env that merely happens to import.
    for env_dir in "$root/envs"/*physearth* "$root/envs"/*geoai* "$root/envs"/*; do
      [ -x "$env_dir/bin/python" ] && echo "$env_dir/bin/python"
    done
  done

  echo python3
  echo python
}

find_python() {
  local candidate
  while IFS= read -r candidate; do
    [ -n "$candidate" ] || continue
    command -v "$candidate" >/dev/null 2>&1 || [ -x "$candidate" ] || continue
    # Prove it: the frontend is what the app imports first, and Gradio is the dependency missing
    # from a system Python.
    if (cd "$ROOT" && PYTHONPATH=backend "$candidate" -c "import gradio, physearth" >/dev/null 2>&1); then
      FOUND="$candidate"
      command -v "$candidate" >/dev/null 2>&1 && command -v "$candidate" || echo "$candidate"
      return 0
    fi
  done < <(interpreter_candidates)
  return 1
}

if ! PYTHON="$(find_python)"; then
  cat >&2 <<'MESSAGE'
No interpreter could import the Studio (gradio + physearth).

Looked at $PHYSEARTH_PYTHON, .venv, $CONDA_PREFIX, conda envs under the usual roots, python3 and
python — none of them satisfied `import gradio, physearth`.

  uv sync --extra dev            # the supported way; creates .venv with everything
  # or:  pip install -e backend  plus gradio

Then re-run, or name the one you built:
  PHYSEARTH_PYTHON=/path/to/env/bin/python scripts/studio.sh
MESSAGE
  exit 1
fi

# ── Which port ──────────────────────────────────────────────────────────────────────────────
# `PHYSEARTH_PORT` wins; otherwise the app's own default. A busy port is moved to a high one
# rather than met with an error, because "address already in use" reads as a broken app.
port_is_free() {
  ! lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

PORT="${PHYSEARTH_PORT:-7860}"
if ! port_is_free "$PORT"; then
  moved=""
  for candidate in $(seq 7871 7920); do
    if port_is_free "$candidate"; then moved="$candidate"; break; fi
  done
  if [ -z "$moved" ]; then
    echo "Port $PORT is busy and no high port was free. Set PHYSEARTH_PORT explicitly." >&2
    exit 1
  fi
  echo "Port $PORT is busy; using $moved instead." >&2
  PORT="$moved"
fi

HOST="${PHYSEARTH_HOST:-127.0.0.1}"
URL="http://127.0.0.1:$PORT/"

echo "PhysEarth-Agent Studio"
echo "  interpreter: $PYTHON"
echo "  URL:         $URL"
echo "  (stop with Ctrl-C)"

if [ "$OPEN" = "1" ]; then
  # Wait for the server to answer before asking the browser for the page: opening a dead URL
  # leaves a browser error page that looks like the app failed to start.
  (
    for _ in $(seq 1 60); do
      sleep 1
      if curl -sf -o /dev/null "$URL" 2>/dev/null; then
        /usr/bin/open "$URL?__theme=light" 2>/dev/null || true
        exit 0
      fi
    done
  ) &
fi

cd "$ROOT"
# Bind loopback unless the operator asked otherwise; the app's own default is 0.0.0.0, which puts
# a research tool on every interface of the machine.
exec env PYTHONPATH=backend PHYSEARTH_HOST="$HOST" PHYSEARTH_PORT="$PORT" "$PYTHON" app.py
