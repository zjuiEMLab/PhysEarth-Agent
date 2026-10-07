# Tests under archive/ exercise evaluation runners that were removed in 35eee2c. They are
# kept verbatim so each can be restored with its runner; see archive/README.md.
collect_ignore = ["archive"]

import os  # noqa: E402

from physearth import config  # noqa: E402

# The suite tests the code's defaults, not a developer's deployment. physearth.config loads
# .env on import, and a local .env that sets every budget cap to 0 failed two session tests
# and froze "unlimited" into the prompt fixtures. Pin the budgets back to their defaults
# before any test module imports the code that reads them.
for _name in (
    "PHYSEARTH_MAX_MODEL_CALLS",
    "PHYSEARTH_MAX_TOOL_CALLS",
    "PHYSEARTH_MAX_SESSION_MODEL_CALLS",
    "PHYSEARTH_MAX_SESSION_TOOL_CALLS",
    "PHYSEARTH_MAX_SESSION_COST_USD",
    "PHYSEARTH_MAX_QUESTIONS_PER_HOUR",
):
    os.environ[_name] = config._DEFAULTS[_name]
