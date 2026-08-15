"""Loading a registered model, and refusing one that cannot be trusted.

The mechanism only. The models themselves are content and live in `models/` at the top of
the repository, where they can be read and copied; this decides what counts as a model,
validates its card against the contract, and refuses the ones that do not hold up.

`loader.py` does the work and its names are re-exported here, so `from physearth import
registry` reaches the registry itself rather than a package that merely contains one.
"""

# ruff: noqa: F401

from physearth.registry import contract
from physearth.registry.loader import (
    BUNDLED_DIR,
    ENTRY_POINT_GROUP,
    EXTRA_DIRS_ENV,
    Model,
    all_models,
    capability_block,
    clear_session,
    get,
    names,
    register_directory,
    register_session_directory,
    rejected,
    reload,
    resolve,
    session_context,
    summary,
    undeclared_parameters,
)
