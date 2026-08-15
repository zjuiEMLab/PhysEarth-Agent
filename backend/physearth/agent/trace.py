"""One trace event, emitted to the durable audit log as it is built."""

import time

from physearth import audit


def _event(kind, **fields):
    event = dict(kind=kind, at=time.strftime("%H:%M:%S"), **fields)
    audit.emit("agent_event", agent_event=event)
    return event
