"""Append-only research journal.

Live state currently lives in the session dict, the plan, the figure list and the run
ledger, and every gate reads those separately; that is why one gate can judge a run
complete while another still calls it missing.  This journal is the first half of the fix
DeepSeek Harness applies with its session log: every fact that decides what happens next is
appended once, in order, under a monotonic sequence number, so the same facts can later be
projected for the gates instead of being re-derived from scattered bookkeeping.

Two properties matter more than the file format:

- **append-only and ordered**: ``seq`` is stored in the entry and asserted continuous by
  :func:`verify`, so a truncated, duplicated or reordered file is detectable rather than
  silently accepted;
- **failure never breaks a run**: a write that fails is swallowed and returns ``None``.  A
  missing journal entry costs diagnosability, never a physical model result, which is the
  same containment the file logger already applies.

Callers pass identifiers, statuses and counts.  Fields whose names look like credentials
are dropped before serialisation, because the journal is a diagnostic artifact and must be
safe to hand to another reader.
"""

import json
import os
import time
from pathlib import Path

from physearth import config

SEQ_KEY = "journal_seq"
SECRET_HINTS = ("token", "secret", "password", "api_key", "apikey", "authorization")


def _safe_fields(fields):
    return {
        key: value
        for key, value in fields.items()
        if not any(hint in str(key).lower() for hint in SECRET_HINTS)
    }


def path_for(session_id):
    """Where one session's journal lives; created on demand."""
    directory = Path(config.state_dir()) / "journal"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / ("%s.jsonl" % session_id)


def record(session, kind, **fields):
    """Append one fact and return its sequence number, or ``None`` if it was not written."""
    if not session or not session.get("id") or not kind:
        return None
    seq = int(session.get(SEQ_KEY) or 0) + 1
    entry = {"seq": seq, "ts": round(time.time(), 6), "kind": str(kind)}
    entry.update(_safe_fields(fields))
    try:
        path = path_for(session["id"])
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
            handle.flush()
    except Exception:
        return None
    session[SEQ_KEY] = seq
    return seq


def flush(session):
    """Durability barrier, used before a side effect so a crash cannot lose its reason.

    Returns True when the journal was synced.  A missing file or a failing sync returns
    False; callers decide whether that is fatal, and for now it is not: the entry itself
    already reached the file, this only forces it out of the page cache.
    """
    if not session or not session.get("id"):
        return False
    try:
        path = path_for(session["id"])
        if not path.is_file():
            return False
        with path.open("a", encoding="utf-8") as handle:
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        return False
    return True


def entries(session_id):
    """Read one session's journal in order; an unreadable or malformed file yields nothing.

    Reading is diagnostics too: a missing directory, a permission problem or a torn last
    line must not become an exception in a run that is otherwise healthy.
    """
    try:
        path = path_for(session_id)
        if not path.is_file():
            return []
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def verify(session_id):
    """Check that the stored sequence is continuous from 1.

    Returns ``(ok, detail)``.  This is the cheap integrity check that makes the file usable
    as evidence: a gap means entries were lost, a duplicate means the writer ran twice over
    the same position.
    """
    stored = entries(session_id)
    expected = 1
    for entry in stored:
        seq = entry.get("seq")
        if seq != expected:
            return False, "expected seq %d, found %r" % (expected, seq)
        expected += 1
    return True, "%d entries" % len(stored)
