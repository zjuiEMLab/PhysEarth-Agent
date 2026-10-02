"""Persistent, structured audit logging for service and research execution.

The browser trace is deliberately transient UI state.  This module is the durable copy:
every agent event is written both to one rotating deployment stream and to a session JSONL
file.  Secrets are redacted before serialization, and logging failures never interrupt a
scientific run.
"""

import json
import logging
import os
import re
import threading
import time
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from physearth import config

_CONTEXT = ContextVar("physearth_audit_context", default={})
_SESSION = ContextVar("physearth_audit_session", default=None)
_LOCK = threading.RLock()
_ROOT = None
_APPLICATION = logging.getLogger("physearth.application")
_EVENTS = logging.getLogger("physearth.events")
# Redact credential-bearing fields, but keep ordinary accounting fields such as
# prompt_tokens and completion_tokens.  The previous substring match erased the very
# counters needed to diagnose context growth.
_SECRET_KEY = re.compile(
    r"^(?:api[_-]?key|access[_-]?token|auth[_-]?token|refresh[_-]?token|token|"
    r"authorization|cookie|password|secret)$",
    re.I,
)
_SECRET_VALUE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._~+\-/=]+|\b(?:sk|ms)-[a-z0-9][a-z0-9-]{12,})"
)
_MAX_TEXT = 12000


def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _int_setting(name, default):
    try:
        return max(1, int(config.get(name) or default))
    except (TypeError, ValueError):
        return default


def _formatter():
    formatter = logging.Formatter(
        "%(asctime)sZ %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    formatter.converter = time.gmtime
    return formatter


def configure(root=None):
    """Configure rotating human-readable and JSONL logs. Safe to call repeatedly."""
    global _ROOT
    wanted = Path(root or config.state_dir()) / "logs"
    wanted.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        if _ROOT == wanted and _APPLICATION.handlers and _EVENTS.handlers:
            return wanted
        for logger in (_APPLICATION, _EVENTS):
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
            logger.propagate = False
            logger.setLevel(logging.DEBUG)
        max_bytes = _int_setting("PHYSEARTH_LOG_MAX_BYTES", 5 * 1024 * 1024)
        backups = _int_setting("PHYSEARTH_LOG_BACKUP_COUNT", 5)
        app_handler = RotatingFileHandler(
            wanted / "application.log", maxBytes=max_bytes, backupCount=backups, encoding="utf-8"
        )
        app_handler.setFormatter(_formatter())
        _APPLICATION.addHandler(app_handler)
        error_handler = RotatingFileHandler(
            wanted / "errors.log", maxBytes=max_bytes, backupCount=backups, encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(_formatter())
        _APPLICATION.addHandler(error_handler)
        event_handler = RotatingFileHandler(
            wanted / "events.jsonl", maxBytes=max_bytes, backupCount=backups, encoding="utf-8"
        )
        event_handler.setFormatter(logging.Formatter("%(message)s"))
        _EVENTS.addHandler(event_handler)
        (wanted / "sessions").mkdir(exist_ok=True)
        _ROOT = wanted
    return wanted


def bind(session=None, **fields):
    """Bind session metadata to subsequent events on this request context."""
    current = dict(_CONTEXT.get() or {})
    if isinstance(session, dict):
        _SESSION.set(session)
        current.update(
            session_id=session.get("id"),
            model=session.get("model"),
            turn=session.get("turns"),
        )
    current.update({key: value for key, value in fields.items() if value is not None})
    _CONTEXT.set(current)
    return current


def _scrub(value, key="", depth=0):
    if depth > 8:
        return "<max-depth>"
    if key and _SECRET_KEY.search(str(key)):
        return "<redacted>"
    if isinstance(value, dict):
        return {str(k): _scrub(v, str(k), depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        result = [_scrub(item, "", depth + 1) for item in items[:200]]
        if len(items) > 200:
            result.append("<%d more>" % (len(items) - 200))
        return result
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, BaseException):
        return "%s: %s" % (type(value).__name__, value)
    if isinstance(value, str):
        text = _SECRET_VALUE.sub("<redacted>", value)
        return text if len(text) <= _MAX_TEXT else text[:_MAX_TEXT] + "…<truncated>"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _scrub(str(value), key, depth + 1)


def session_snapshot(session):
    project = (session or {}).get("research") or {}
    plan = project.get("plan") or {}
    return {
        "session_id": (session or {}).get("id"),
        "turn": (session or {}).get("turns"),
        "model": (session or {}).get("model"),
        "research_phase": project.get("phase"),
        "plan_version": project.get("plan_version"),
        "selected_chart_ids": list(project.get("selected_charts") or []),
        "planned_run_ids": [item.get("id") for item in plan.get("runs") or []],
        "model_calls": (session or {}).get("model_calls", 0),
        "tool_calls": (session or {}).get("tool_calls", 0),
        "model_runs": (session or {}).get("model_runs", 0),
        "figure_count": len((session or {}).get("figures") or []),
    }


def _rotate_session(path, max_bytes, backups):
    if not path.exists() or path.stat().st_size < max_bytes:
        return
    oldest = path.with_suffix(path.suffix + ".%d" % backups)
    if oldest.exists():
        oldest.unlink()
    for index in range(backups - 1, 0, -1):
        source = path.with_suffix(path.suffix + ".%d" % index)
        if source.exists():
            source.replace(path.with_suffix(path.suffix + ".%d" % (index + 1)))
    path.replace(path.with_suffix(path.suffix + ".1"))


def emit(event_type, session=None, level="INFO", **fields):
    """Write one redacted event. Logging must never become an execution failure."""
    if os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("PHYSEARTH_AUDIT_TEST"):
        return None
    try:
        root = configure()
        context = dict(_CONTEXT.get() or {})
        active_session = session if isinstance(session, dict) else _SESSION.get()
        if isinstance(active_session, dict):
            context.update(session_snapshot(active_session))
        record = {
            "timestamp": _utc_now(),
            "event_id": "evt_" + uuid.uuid4().hex[:16],
            "event_type": event_type,
            "level": str(level).upper(),
            "pid": os.getpid(),
            "thread": threading.current_thread().name,
            **context,
            **fields,
        }
        record = _scrub(record)
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        numeric_level = getattr(logging, str(level).upper(), logging.INFO)
        _EVENTS.log(numeric_level, line)
        session_id = record.get("session_id")
        if session_id:
            safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", str(session_id))[:80]
            path = root / "sessions" / (safe_id + ".jsonl")
            with _LOCK:
                _rotate_session(
                    path,
                    _int_setting("PHYSEARTH_SESSION_LOG_MAX_BYTES", 10 * 1024 * 1024),
                    _int_setting("PHYSEARTH_LOG_BACKUP_COUNT", 5),
                )
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(line + "\n")
        return record
    except Exception:
        return None


def runtime(event_type, level="INFO", **fields):
    if os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("PHYSEARTH_AUDIT_TEST"):
        return
    try:
        configure()
        payload = json.dumps(_scrub({"event_type": event_type, **fields}), ensure_ascii=False)
        _APPLICATION.log(getattr(logging, str(level).upper(), logging.INFO), payload)
    except Exception:
        pass


def exception(event_type, exc, session=None, **fields):
    detail = {
        **fields,
        "exception_type": type(exc).__name__,
        "exception": str(exc),
        "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    }
    runtime(event_type, level="ERROR", **detail)
    return emit(event_type, session=session, level="ERROR", **detail)


def recent(limit=100, session_id=None):
    """Read the newest structured events for diagnostics and tests."""
    root = configure()
    path = root / "events.jsonl"
    if session_id:
        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", str(session_id))[:80]
        path = root / "sessions" / (safe_id + ".jsonl")
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max(1, limit):]
    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records
