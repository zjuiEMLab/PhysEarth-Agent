"""Budgets, retry policy and the few literals the loop is tuned around."""

import re

from physearth import session as session_state

MAX_MODEL_CALLS = session_state.MAX_MODEL_CALLS
MAX_TOOL_CALLS = session_state.MAX_TOOL_CALLS
EMPTY_RESPONSE_RETRIES = 3
RETRY_BACKOFF_S = 1.5
# A rate limit is counted over a window, so a backoff shorter than the window cannot
# clear it. The account limit here is per minute, and three attempts at a few seconds
# each used to report an upstream fault after eighteen seconds of trying, when waiting
# would have worked. These three attempts span just over a minute instead.
RATE_LIMIT_BACKOFF_S = 12.0
RATE_LIMIT_RETRIES = 4
# A three-configuration research_plan is itself a sizeable JSON tool call.  At 2048 the
# provider stopped exactly at the limit and left function.arguments without its closing
# braces, which then poisoned the next OpenAI-compatible request.  This still leaves ample
# room under the conservative request/context ceilings below.
MAX_OUTPUT_TOKENS = 4096
# ModelScope providers differ slightly in their advertised context windows. Keep a
# conservative request budget and compact old tool output before the provider rejects the
# request. This is a character budget because the tokenizer is model-specific; it leaves
# room for the system prompt and the requested completion.
MAX_REQUEST_CHARS = 240000
MAX_KEPT_HISTORY_CHARS = 48000
MAX_KEPT_TOOL_CHARS = 12000
# A turn can produce several stretches of prose, one before each round of tool calls. They
# are separate thoughts and belong in separate blocks, so they travel joined by a character
# that cannot occur in the text itself rather than run together into one paragraph.
SEGMENT_BREAK = ""
CONTEXT_CEILING_TOKENS = session_state.CONTEXT_CEILING_TOKENS

_TOOL_BYPASS_PATTERNS = (
    re.compile(r"\b(?:do not|don't|dont|without)\s+(?:use|call|invoke)\s+(?:any\s+)?tools?\b", re.I),
    re.compile(r"\bno\s+tools?\b", re.I),
    re.compile(r"(?:不要|勿|禁止)\s*(?:使用|调用|调用任何)\s*工具", re.I),
)
