"""Every pixel of the interface, as plain strings.

Nothing here imports Gradio, so all of it is testable without a browser. Every value
that reaches the page goes through `html.escape` first: literature text, dataset rows
and model output are all untrusted input on a public deployment.

Split by panel. Everything the interface imported from the single-module `render` is
re-exported here, so `from physearth.ui import render` and every `render.x` call keep
working unchanged.
"""

# Re-exported for the Gradio layer and the interface tests.
# ruff: noqa: F401

from physearth.ui.render.context import (
    current_activity_status,
    research_context,
    research_status,
)
from physearth.ui.render.conversation import (
    PLACEHOLDER,
    conversation_head,
    guided_brief,
    hero,
    history,
    live,
    live_result,
)
from physearth.ui.render.evidence import _dataset_card, evidence
from physearth.ui.render.parts import _mapping_text, _reproduction_state
from physearth.ui.render.review import approval_bar
from physearth.ui.render.text import _e, _markers, _mono, _svg, answer_html
from physearth.ui.render.trace import trace, trace_metrics
