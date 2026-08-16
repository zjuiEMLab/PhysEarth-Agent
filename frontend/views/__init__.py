"""Every pixel of the interface, as plain strings.

Nothing here imports Gradio, so all of it is testable without a browser. Every value
that reaches the page goes through `html.escape` first: literature text, dataset rows
and model output are all untrusted input on a public deployment.

Split by panel. Everything the interface imported from the single-module `render` is
re-exported here, so the Gradio layer keeps calling `render.x` unchanged
working unchanged.
"""

# Re-exported for the Gradio layer and the interface tests.
# ruff: noqa: F401

from frontend.views.context import (
    current_activity_status,
    research_context,
)

# The remaining names the single-module version exposed, kept reachable at the same
# address so nothing outside this package has to know the split happened.
from frontend.views.conversation import (
    next_step,
    PLACEHOLDER,
    _message,
    _plan_run_rows,
    _user_body,
    conversation_head,
    guided_brief,
    hero,
    history,
    live,
    live_result,
)
from frontend.views.evidence import (
    SOURCE_BADGE,
    _abstract_card,
    _agreement_row,
    _comparison_table,
    _corpus_card,
    _dataset_card,
    _figure_card,
    _model_card,
    _rejected_card,
    _section_card,
    evidence,
)
from frontend.views.parts import (
    _disclosure,
    _kv,
    _mapping_text,
    _meter,
    _plan_cell,
    _plan_disclosure,
    _plan_table,
    _reproduction_state,
)
from frontend.views.review import (
    _revision_changes_html,
    _structured_approval_bar,
    approval_bar,
)
from frontend.views.text import (
    ABS_CITE,
    BOLD,
    CITE,
    CODE,
    DATA_CITE,
    ICONS,
    MODEL_CITE,
    SAFE_SUB,
    SECTION_PREVIEW_CHARS,
    SKILL_CITE,
    _e,
    _inline,
    _markers,
    _mono,
    _paragraphs,
    _svg,
    answer_html,
)
from frontend.views.trace import (
    APPROVAL_WORDS,
    BADGES,
    _event_body,
    _event_card,
    _trace_metrics,
    trace,
    trace_metrics,
)
