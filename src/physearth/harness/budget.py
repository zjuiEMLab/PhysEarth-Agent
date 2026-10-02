"""Optional process-wide rate limit.

Public deployments may set a shared hourly cap. Local development and the default
configuration leave it disabled so a scientific workflow is not stopped mid-run.
"""

import threading
import time

from physearth import config

WINDOW_SECONDS = 3600.0
MAX_RUNS_PER_WINDOW = config.nonnegative_int("PHYSEARTH_MAX_QUESTIONS_PER_HOUR")

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
        if MAX_RUNS_PER_WINDOW and len(_STARTS) >= MAX_RUNS_PER_WINDOW:
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
