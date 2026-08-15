"""The guarantees, gathered: what is checked, who approves, and what is recorded.

These were eight modules scattered through the package. They belong together because
they are the same claim from different angles -- a parameter is checked before the run,
a human approves it, the result is checked after, text from outside is fenced, arrays
stay out of the model's context, and every one of those leaves an audit record.

`gates.py` holds the checks the agent cannot skip, and its names are re-exported here so
`from physearth import harness` keeps meaning what it meant when this was one module.
"""

# ruff: noqa: F401

from physearth.harness.gates import *  # noqa: F403
from physearth.harness.gates import (
    ABSTRACT_PATTERN,
    CITATION_PATTERN,
    DATA_PATTERN,
    FIGURE_PATTERN,
    GUIDELINE_PATTERN,
    MAX_INTERVENTIONS,
    MODEL_PATTERN,
    RESEARCH_PLAN_MAX_INTERVENTIONS,
    SKILL_PATTERN,
    UNCITED_ANSWER_CHARS,
)
