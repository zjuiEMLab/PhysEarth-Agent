"""Bounded store for full numeric results.

A model run can produce hundreds of numbers. None of them belong in the language
model's context: the model needs the shape of the result, not every value. So a run
returns a handle plus a bounded preview, and the full arrays stay here for whatever
consumes them next.

Handles are unguessable and the store is capped, so nothing accumulates.

The store is process wide because one Studio process serves every visitor, so each
entry records the session that produced it. A handle only reads back for its own
session, and eviction takes that session's oldest entry first, so a busy visitor
cannot push another visitor's results out from under them.
"""

import statistics
import threading
import uuid
from collections import OrderedDict

MAX_STORED = 400
MAX_PER_OWNER = 40
PREVIEW_POINTS = 12

_LOCK = threading.Lock()
_STORE = OrderedDict()


def _evict(owner):
    """Oldest first, within the owner that just grew, then globally."""
    mine = [h for h, entry in _STORE.items() if entry["owner"] == owner]
    while len(mine) > MAX_PER_OWNER:
        del _STORE[mine.pop(0)]
    while len(_STORE) > MAX_STORED:
        _STORE.popitem(last=False)


def put(payload, owner=None):
    handle = "res_" + uuid.uuid4().hex[:12]
    with _LOCK:
        _STORE[handle] = {"owner": owner, "payload": payload}
        _evict(owner)
    return handle


def get(handle, owner=None):
    with _LOCK:
        entry = _STORE.get(handle)
    if entry is None or entry["owner"] != owner:
        return None
    return entry["payload"]


def size():
    with _LOCK:
        return len(_STORE)


def summarise_series(series, units):
    summary = {}
    for name, values in (series or {}).items():
        numbers = [v for v in values if isinstance(v, (int, float))]
        if not numbers:
            summary[name] = {"unit": units.get(name, ""), "note": "no numeric values"}
            continue
        entry = {
            "unit": units.get(name, ""),
            "first": round(numbers[0], 4),
            "last": round(numbers[-1], 4),
            "min": round(min(numbers), 4),
            "max": round(max(numbers), 4),
        }
        if len(numbers) > 2:
            entry["mean"] = round(statistics.fmean(numbers), 4)
            entry["monotonic"] = (
                "increasing"
                if numbers == sorted(numbers)
                else "decreasing"
                if numbers == sorted(numbers, reverse=True)
                else "not monotonic"
            )
        summary[name] = entry
    return summary


def preview(points, limit=PREVIEW_POINTS):
    """Evenly spaced points, always including the first and the last."""
    if not points:
        return []
    if len(points) <= limit:
        return points
    step = (len(points) - 1) / (limit - 1)
    picked = sorted({int(round(i * step)) for i in range(limit)} | {0, len(points) - 1})
    return [points[i] for i in picked]
