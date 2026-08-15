"""Where the content lives, resolved in one place.

The package used to sit at the repository root, and four modules reached the content
beside it with their own `Path(__file__).resolve().parent.parent / "knowledge"`. Those
were the most dangerous constants in the codebase, because they failed *silently*: a
wrong answer was an empty corpus and a citation that resolved to nothing, never an
exception. Now the package is one level further down and they would all have been wrong
at once.

So resolution happens here, once, and it is loud. `root()` raises rather than returning a
directory that is not there, and `PHYSEARTH_ROOT` overrides it for a deployment that
arranges the content differently.
"""

import os
from pathlib import Path

ROOT_ENV = "PHYSEARTH_ROOT"

# A directory is the repository root when the content the package reads is beside it.
# Two markers rather than one, so a stray empty `knowledge/` somewhere up the tree cannot
# be mistaken for the real thing.
_MARKERS = ("knowledge", "evaluation")

_root = None


def root():
    """The directory holding knowledge/, evaluation/ and assets/."""
    global _root
    if _root is not None:
        return _root
    override = os.environ.get(ROOT_ENV, "").strip()
    if override:
        candidate = Path(override).expanduser().resolve()
        if not candidate.is_dir():
            raise RuntimeError("%s points at %s, which is not a directory" % (ROOT_ENV, candidate))
        _root = candidate
        return _root
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if all((candidate / marker).is_dir() for marker in _MARKERS):
            _root = candidate
            return _root
    raise RuntimeError(
        "cannot find the content root above %s: expected a directory containing %s. "
        "This package reads its corpus, reference data and evaluation set from the "
        "repository beside it; set %s if they live somewhere else."
        % (here, " and ".join(_MARKERS), ROOT_ENV)
    )


def knowledge():
    """Bundled literature, method notes, reference data and model guidelines."""
    return root() / "knowledge"


def assets():
    """Shared with the interface: the typefaces, and the architecture diagram."""
    return root() / "assets"


def evaluation():
    """The task set, configurations and committed result records."""
    return root() / "evaluation"
