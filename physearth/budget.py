"""Process-wide rate limit.

The Studio is public and every visitor shares one inference quota, so the cap has to
live outside the session. Nothing here is per-user; it protects the quota as a whole.
"""

import threading
import time

WINDOW_SECONDS = 3600.0
MAX_RUNS_PER_WINDOW = 120

_LOCK = threading.Lock()
_STARTS = []


def _prune(now):
    cutoff = now - WINDOW_SECONDS
    while _STARTS and _STARTS[0] < cutoff:
        _STARTS.pop(0)


def acquire():
    """Return (allowed, message). One call per agent turn."""
    now = time.time()
    with _LOCK:
        _prune(now)
        if len(_STARTS) >= MAX_RUNS_PER_WINDOW:
            wait = int(WINDOW_SECONDS - (now - _STARTS[0]))
            return False, (
                "This deployment has run %d questions in the last hour, which is its shared "
                "limit. Try again in about %d minutes, or run PhysEarth locally with your own "
                "token." % (MAX_RUNS_PER_WINDOW, max(1, wait // 60))
            )
        _STARTS.append(now)
        return True, ""


def used():
    with _LOCK:
        _prune(time.time())
        return len(_STARTS), MAX_RUNS_PER_WINDOW
