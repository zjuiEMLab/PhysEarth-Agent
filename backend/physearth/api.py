"""The surface the interface is allowed to touch.

The frontend imports this module and nothing else from the package. That is enforced by
a test, and the point is not the indirection -- the call sites are unchanged -- but that
the coupling is now declared in one place instead of accumulating silently. Adding a
line here is a deliberate act; before, any view could reach anywhere.

This declares the boundary rather than narrowing it. The 62 names the interface uses
today are reachable through the modules below, and reducing that number is separate work
from moving the files.
"""

# Re-exported for the frontend; unused here by construction.
# ruff: noqa: F401

from physearth import (
    agent,
    artifacts,
    config,
    diagnostics,
    evals,
    evaluation,
    registry,
    research,
    tools,
)
from physearth.corpus import knowledge, live, reference
from physearth.harness import approval, audit, budget

__all__ = [
    "agent",
    "approval",
    "artifacts",
    "audit",
    "budget",
    "config",
    "diagnostics",
    "evals",
    "evaluation",
    "knowledge",
    "live",
    "reference",
    "registry",
    "research",
    "tools",
]
