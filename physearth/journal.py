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


def latest(session_id, kind="tool_result"):
    """The newest entry of one kind, or None when the journal holds nothing yet."""
    for entry in reversed(entries(session_id)):
        if entry.get("kind") == kind:
            return entry
    return None


def drift(session):
    """Report state the journal says happened but the live session does not hold.

    This is the invariant half of "the log is the source of truth": it does not police
    ordinary progress (a revision may raise the plan version, a recovery may withdraw a
    figure), so it only reports the impossible direction — the journal is *ahead* of the
    session.  A recorded successful run the session never registered, or a plan version the
    session has gone backwards from, means state was lost or overwritten somewhere, which is
    exactly the class of drift that used to surface as an endless "run is still missing"
    gate.  Returns a list of human-readable findings; empty means consistent.
    """
    if not session or not session.get("id"):
        return []
    entry = latest(session["id"])
    if entry is None:
        return []
    findings = []
    recorded_runs = set(entry.get("successful_run_ids") or ())
    live_runs = {
        str(item.get("planned_run_id"))
        for item in session.get("successful_runs") or ()
        if item.get("planned_run_id")
    }
    lost = sorted(recorded_runs - live_runs)
    if lost:
        findings.append(
            "journal records successful planned run(s) %s that the session does not hold"
            % ", ".join(lost)
        )
    recorded_version = entry.get("plan_version")
    live_version = (session.get("research") or {}).get("plan_version")
    if isinstance(recorded_version, int) and isinstance(live_version, int):
        if live_version < recorded_version:
            findings.append(
                "journal is at plan v%03d while the session is at v%03d" % (recorded_version, live_version)
            )
    return findings
