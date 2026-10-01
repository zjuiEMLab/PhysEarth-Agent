#!/usr/bin/env bash
# One interpreter-discovery implementation, sourced by every script that needs it.
#
# Why this exists as a shared file rather than a function copied into each script: the same bug
# was written three times. A PATH lookup finds `python3`, which on this machine is a system
# interpreter with no scientific stack, and the resulting failure is always silent — an MCP server
# that reports "✗ Failed to connect", a plugin that installs and offers no tools, a Studio that
# refuses to start. Each script had its own list of candidates, and each list was missing the
# conda environments where the engine actually lives.
#
# The rule the three failures taught: *prove* the interpreter against what the caller needs, and
# look in the places an environment is actually kept — not just PATH.
#
# Source it, then call one of:
#
#   physearth_find_python <probe>        # probe: a Python statement, e.g. "from integrations.geoai import service"
#   physearth_find_python_for_studio     # gradio + physearth
#   physearth_find_python_for_engine     # the bridge service (what the MCP server and bridge need)
#
# Every function echoes the chosen interpreter and returns 0, or returns 1 with no output.
# Diagnostics go to stderr so `$(...)` capture stays clean.

# Candidate interpreters, most deliberate first. De-duplicated by the caller's first match.
physearth_python_candidates() {
  local root="${PHYSEARTH_ROOT:-${PHYSEARTH_CHECKOUT:-}}"
  local env_dir candidate

  # 1. An explicit answer always wins.
  [ -n "${PHYSEARTH_PYTHON:-}" ] && echo "$PHYSEARTH_PYTHON"

  # 2. The documented workflow: `uv sync --extra dev` in a checkout.
  [ -n "$root" ] && echo "$root/.venv/bin/python"

  # 3. An activated environment.
  [ -n "${CONDA_PREFIX:-}" ] && echo "$CONDA_PREFIX/bin/python"
  [ -n "${VIRTUAL_ENV:-}" ] && echo "$VIRTUAL_ENV/bin/python"

  # 4a. If conda is installed, ask it where its environments are. This is the one source that
  #     does not depend on guessing a home directory, so it comes before the globs — and it is
  #     what makes the search survive a caller that has moved $HOME (a test harness, a sandbox).
  if command -v conda >/dev/null 2>&1; then
    local conda_base
    conda_base="$(conda info --base 2>/dev/null)"
    if [ -n "$conda_base" ] && [ -d "$conda_base" ]; then
      [ -x "$conda_base/bin/python" ] && echo "$conda_base/bin/python"
      for env_dir in "$conda_base/envs"/*physearth* "$conda_base/envs"/*geoai* "$conda_base/envs"/*; do
        [ -x "$env_dir/bin/python" ] && echo "$env_dir/bin/python"
      done
    fi
  fi

  # 4b. Named environments under the usual conda roots. An environment named for this project
  #    first, then the rest: a researcher's working environment is usually a named env, not
  #    whatever `python3` points at, which is exactly the mistake this file exists to prevent.
  for candidate in \
    "$HOME/miniconda3" "$HOME/anaconda3" "$HOME/mambaforge" "$HOME/miniforge3" \
    /opt/miniconda3 /opt/anaconda3 /opt/homebrew/Caskroom/miniconda/base \
    /usr/local/miniconda3 /usr/local/anaconda3; do
    [ -d "$candidate/envs" ] || continue
    [ -x "$candidate/bin/python" ] && echo "$candidate/bin/python"
    for env_dir in "$candidate/envs"/*physearth* "$candidate/envs"/*geoai* "$candidate/envs"/*; do
      [ -x "$env_dir/bin/python" ] && echo "$env_dir/bin/python"
    done
  done

  # 5. Last resort: PATH. Frequently the wrong answer, which is why it is last.
  echo python3
  echo python
}

# Echo the first candidate for which `python -c <probe>` succeeds, optionally from a directory.
#
# @param probe   a Python statement to execute; success means the interpreter is usable.
# @param cwd     directory to run the probe from (some probes need the checkout on sys.path).
physearth_find_python() {
  local probe="$1" cwd="${2:-}" candidate resolved
  while IFS= read -r candidate; do
    [ -n "$candidate" ] || continue
    command -v "$candidate" >/dev/null 2>&1 || [ -x "$candidate" ] || continue
    if [ -n "$cwd" ]; then
      (cd "$cwd" && PYTHONPATH="backend:." "$candidate" -c "$probe" >/dev/null 2>&1) || continue
    else
      "$candidate" -c "$probe" >/dev/null 2>&1 || continue
    fi
    # Prefer the absolute path `command -v` yields, so a caller that writes it into a settings
    # file records something that survives a different PATH.
    resolved="$(command -v "$candidate" 2>/dev/null || echo "$candidate")"
    echo "$resolved"
    return 0
  done < <(PHYSEARTH_ROOT="${PHYSEARTH_ROOT:-$cwd}" physearth_python_candidates)
  return 1
}

# The interpreter the Studio needs: gradio plus the package.
physearth_find_python_for_studio() {
  physearth_find_python "import gradio, physearth" "${1:-}"
}

# The interpreter the MCP server and the HTTP bridge need. Deliberately the *service*, not
# `import physearth`: that package's __init__ is lazy, so `import physearth` succeeds on an
# interpreter with no PyYAML, which is how a broken interpreter got written into a profile once.
physearth_find_python_for_engine() {
  physearth_find_python "from integrations.geoai import service" "${1:-}"
}
