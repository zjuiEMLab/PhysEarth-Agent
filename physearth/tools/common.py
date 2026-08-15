"""The shape of every tool result, and the ledger line that records one."""


def _ok(summary, data, citations=None, qc=None, ui=None):
    """`ui` never reaches the language model; the agent strips it before serialising."""
    return {
        "status": "success",
        "summary": summary,
        "data": data,
        "citations": citations or [],
        "qc": qc,
        "ui": ui,
        "error": None,
    }


def _ledger(session, kind, record):
    """Record evidence/resource metadata without retaining unbounded source text."""
    if session is None:
        return
    item = {"kind": str(kind), **dict(record or {})}
    key = (
        item.get("kind"), item.get("reference"), item.get("model"),
        item.get("version"), item.get("figure_id"), item.get("section_id"),
    )
    ledger = session.setdefault("evidence_ledger", [])
    for index, entry in enumerate(ledger):
        if not isinstance(entry, dict):
            continue
        entry_key = (
            entry.get("kind"), entry.get("reference"), entry.get("model"),
            entry.get("version"), entry.get("figure_id"), entry.get("section_id"),
        )
        if entry_key == key:
            ledger[index] = {**entry, **item}
            return
    ledger.append(item)


def _fail(message, data=None):
    return {
        "status": "terminal_error",
        "summary": message,
        "data": data or {},
        "citations": [],
        "qc": None,
        "ui": None,
        "error": message,
    }


def _offline_note(action):
    return _fail(
        "This deployment is running with PHYSEARTH_ONLINE=0, so %s is switched off. The "
        "bundled corpus, the registered models and the reference data are all unaffected; "
        "work from those, and say plainly that the online literature layer was unavailable "
        "rather than that nothing was found." % action
    )
