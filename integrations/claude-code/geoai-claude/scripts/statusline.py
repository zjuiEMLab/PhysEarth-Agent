#!/usr/bin/env python3
"""The Geo-AI status line: colour is the one visual surface Claude Code gives a plugin.

Claude Code runs this command on session start, on every assistant message, on `/compact`, on a
mode change, on a vim-mode toggle, on `command` change, and every `refreshInterval` seconds —
and it renders ANSI escape sequences in stdout. That makes a coloured line the most reliable way
an integration can be visible in a terminal that has no plugin UI at all.

It reads Claude Code's status-line JSON on stdin and writes one line. What it shows is chosen for
this project rather than for general appeal: the model, the output style (so you can see whether
the Geo-AI discipline is active), how much context is left, and the branch. Context is the number
that actually ends a long reproduction, so it is the one given a colour threshold.

Design rules, from the same place as the rest of this repository:

  - **Degrade, never fail.** Any field may be absent, any section may be missing. A status line
    that raises leaves a blank line and no clue why, so every access is total.
  - **Colour is never the only signal.** The context reading carries its percentage as text as
    well as a colour, for the same reason the engine's own cards do.
  - **Nothing is written anywhere.** It reads stdin and prints; it has no side effects and no
    network access.

Usage: configured by `integrations/claude-code/install.sh --write-settings`, or by hand:

  {"statusLine": {"type": "command", "command": "python3 /abs/path/statusline.py",
                  "padding": 0, "refreshInterval": 10}}
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# ── ANSI ─────────────────────────────────────────────────────────────────────────────────────
# True-colour with a graceful fallback: NO_COLOR and a non-TTY both mean "plain text", because a
# status line piped somewhere must not carry escape codes.

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def _truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() not in {"", "0", "false", "off", "no"}


def _enabled() -> bool:
    """Whether to emit escape sequences.

    The precedence is the one the colour conventions actually specify, which is worth writing down
    because getting it backwards makes the whole feature invisible:

      - `FORCE_COLOR` is an explicit request and wins over everything, including NO_COLOR. Without
        this, a shell that exports NO_COLOR=1 for other tools would silently disable the one
        visual surface this integration has — which is exactly what happened while testing it.
      - `NO_COLOR` is the standing opt-out: its *presence* means plain text, whatever its value,
        per the convention of that name.
      - `TERM=dumb` means the terminal cannot do it at all.
      - otherwise, only a TTY: output piped into a file or another program must not carry escapes.
    """
    if _truthy(os.environ.get("FORCE_COLOR")):
        return True
    if os.environ.get("NO_COLOR") is not None:
        return False
    if not _truthy(os.environ.get("CLAUDE_STATUSLINE_COLOR", "1")):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return sys.stdout.isatty()


def fg(r: int, g: int, b: int) -> str:
    if not _enabled():
        return ""
    if os.environ.get("COLORTERM", "").lower() in {"truecolor", "24bit"}:
        return f"\033[38;2;{r};{g};{b}m"
    # 256-colour approximation, so an older terminal still gets a distinguishable palette
    # rather than nothing.
    index = 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)
    return f"\033[38;5;{index}m"


# The same palette as the Codex theme and the DSH plugin.
ICE = fg(0x22, 0xD3, 0xEE)
ICE_SOFT = fg(0x67, 0xE8, 0xF9)
TEXT = fg(0xE8, 0xEE, 0xFB)
MUTED = fg(0x71, 0x86, 0xA6)
AMBER = fg(0xF5, 0x9E, 0x0B)
GREEN = fg(0x34, 0xD3, 0x99)
RED = fg(0xF8, 0x71, 0x71)


def reset() -> str:
    return RESET if _enabled() else ""


def bold() -> str:
    return BOLD if _enabled() else ""


def dim() -> str:
    return DIM if _enabled() else ""


# ── Reading stdin ────────────────────────────────────────────────────────────────────────────


def read_payload() -> dict:
    """Whatever Claude Code sent, as a dict. Never raises."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def dig(payload: dict, *path, default=None):
    """Walk a nested dict, returning `default` at the first missing or wrong-typed step."""
    node = payload
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node if node is not None else default


# ── Pieces ───────────────────────────────────────────────────────────────────────────────────


def context_piece(payload: dict) -> str:
    """Context remaining, as a number and a colour.

    Claude Code reports usage in more than one shape depending on version, so every plausible
    field is tried and an unknown shape simply produces no piece rather than a wrong one.
    """
    window = dig(payload, "context_window", default={})
    used_pct = None
    for key in ("used_percentage", "used_percent", "percent_used"):
        value = window.get(key) if isinstance(window, dict) else None
        if isinstance(value, (int, float)):
            used_pct = float(value)
            break
    if used_pct is None:
        window = dig(payload, "context_window", "window", default={})
        remaining = dig(window, "remaining_tokens")
        size = dig(window, "size") or dig(window, "total_tokens")
        if isinstance(remaining, (int, float)) and isinstance(size, (int, float)) and size:
            used_pct = 100.0 * (1 - remaining / size)

    if used_pct is None:
        exceeds = payload.get("exceeds_200k_tokens")
        if exceeds is True:
            return f"{RED}ctx>200k{reset()}"
        return ""

    left = max(0.0, min(100.0, 100.0 - used_pct))
    colour = GREEN if left >= 50 else AMBER if left >= 20 else RED
    # Text carries the same information as the colour, never colour alone.
    return f"{colour}ctx {left:.0f}% left{reset()}"


def style_piece(payload: dict) -> str:
    """Which output style is active — i.e. whether the Geo-AI discipline is on."""
    name = dig(payload, "output_style", "name")
    if not isinstance(name, str) or not name:
        return ""
    if "geoai" in name.lower():
        return f"{ICE}{bold()}◆ {name}{reset()}"
    return f"{dim()}style {name}{reset()}"


def model_piece(payload: dict) -> str:
    model = dig(payload, "model", "display_name") or dig(payload, "model", "id")
    return f"{ICE_SOFT}{model}{reset()}" if isinstance(model, str) and model else ""


def branch_piece(payload: dict) -> str:
    """Branch, preferring what Claude Code reported and falling back to git once.

    The fallback exists because the field is absent on some versions; it is a single `git`
    invocation with the output silenced, and a failure simply yields no piece.
    """
    branch = dig(payload, "workspace", "git_branch")
    if not isinstance(branch, str) or not branch:
        if dig(payload, "workspace", "repo") is None and not dig(payload, "workspace"):
            return ""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=dig(payload, "workspace", "current_dir") or dig(payload, "cwd") or None,
                capture_output=True,
                text=True,
                timeout=1,
            )
            branch = result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            branch = ""
    return f"{MUTED}{branch}{reset()}" if branch and branch != "HEAD" else ""


def effort_piece(payload: dict) -> str:
    level = dig(payload, "effort", "level")
    return f"{MUTED}effort {level}{reset()}" if isinstance(level, str) and level else ""


def worktree_piece(payload: dict) -> str:
    name = dig(payload, "worktree", "name")
    return f"{AMBER}wt:{name}{reset()}" if isinstance(name, str) and name else ""


def main() -> int:
    payload = read_payload()

    parts = [f"{ICE}{bold()}PhysEarth Geo-AI{reset()}"]
    for piece in (
        model_piece(payload),
        style_piece(payload),
        context_piece(payload),
        branch_piece(payload),
        effort_piece(payload),
        worktree_piece(payload),
    ):
        if piece:
            parts.append(piece)

    separator = f"{dim()}  ·  {reset()}"
    line = separator.join(parts)
    # One row per print; Claude Code renders each printed line as a row.
    sys.stdout.write(line + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
