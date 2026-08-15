"""The agent loop, split by concern.

Everything the rest of the package imported from the single-module `agent` is re-exported
here, so this split changes no import anywhere else. Run one turn without the interface
with `python -m physearth.agent "your question"`.
"""

# The private names below are re-exported on purpose: the test suite and the evaluation
# runners reach for them through this package, and moving them must not move their address.
# ruff: noqa: F401

from physearth import tools
from physearth.agent.catalogue import (
    CATALOGUE,
    default_model,
    new_session,
    new_state,
    resolve_model,
)
from physearth.agent.completion import _client, _Completion, _tool_arguments
from physearth.agent.constants import (
    CONTEXT_CEILING_TOKENS,
    EMPTY_RESPONSE_RETRIES,
    MAX_KEPT_HISTORY_CHARS,
    MAX_KEPT_TOOL_CHARS,
    MAX_MODEL_CALLS,
    MAX_OUTPUT_TOKENS,
    MAX_REQUEST_CHARS,
    MAX_TOOL_CALLS,
    RATE_LIMIT_BACKOFF_S,
    RATE_LIMIT_RETRIES,
    RETRY_BACKOFF_S,
    SEGMENT_BREAK,
)
from physearth.agent.faults import _dead_for_today, _fault, _rate_limited, _upstream_text
from physearth.agent.loop import _requests_tool_bypass, run, stream
from physearth.agent.messages import _compact_messages, _messages, _short_content, transcript
from physearth.agent.results import (
    _allowed_marker_correction,
    _handle_line,
    _record_tool_result,
)
from physearth.agent.trace import _event

__all__ = [
    "CATALOGUE",
    "CONTEXT_CEILING_TOKENS",
    "EMPTY_RESPONSE_RETRIES",
    "MAX_KEPT_HISTORY_CHARS",
    "MAX_KEPT_TOOL_CHARS",
    "MAX_MODEL_CALLS",
    "MAX_OUTPUT_TOKENS",
    "MAX_REQUEST_CHARS",
    "MAX_TOOL_CALLS",
    "RATE_LIMIT_BACKOFF_S",
    "RATE_LIMIT_RETRIES",
    "RETRY_BACKOFF_S",
    "SEGMENT_BREAK",
    "default_model",
    "new_session",
    "new_state",
    "resolve_model",
    "run",
    "stream",
    "tools",
    "transcript",
]

# The remaining names the single-module version exposed, kept reachable at the same
# address so nothing outside this package has to know the split happened.
from physearth.agent.catalogue import (
    _MODEL_LABELS,
    _model_card,
)
from physearth.agent.constants import _TOOL_BYPASS_PATTERNS
