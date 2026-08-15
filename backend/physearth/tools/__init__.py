"""The tools the agent may call, grouped by what they are for.

`call` is the single entry point: it strips the caller-only arguments the model must not
be able to forge, then dispatches. Everything the rest of the tree imported from the
single-module `tools` is re-exported here, so this split changes no import elsewhere.
"""

# Re-exported for callers that reach for them through this package.
# ruff: noqa: F401

from physearth import switches
from physearth.ingest import http
from physearth.models import registry
from physearth.tools import charts, common, figures, literature, planning, registration, runs, specs
from physearth.tools.charts import plot, plot_planned_chart
from physearth.tools.common import _fail, _ledger, _ok
from physearth.tools.literature import (
    OUTPUT_BUDGET_CHARS,
    discover_literature,
    ingest_paper,
    inspect_paper_figure,
    list_literature,
    read_literature,
    read_model_instruction,
    read_paper_figure,
    read_research_guideline,
    research_capability_check,
)
from physearth.tools.planning import research_plan
from physearth.tools.registration import (
    inspect_github_model_repo,
    list_models,
    register_github_model_repo,
    register_model_guideline,
)
from physearth.tools.runs import (
    MAX_RUN_SECONDS,
    read_reference_dataset,
    run_model,
    run_planned_model,
)
from physearth.tools.specs import SPECS

DISPATCH = {
    "list_literature": list_literature,
    "read_reference_dataset": read_reference_dataset,
    "read_literature": read_literature,
    "read_research_guideline": read_research_guideline,
    "read_model_instruction": read_model_instruction,
    "research_capability_check": research_capability_check,
    "read_paper_figure": read_paper_figure,
    "inspect_paper_figure": inspect_paper_figure,
    "register_model_guideline": register_model_guideline,
    "inspect_github_model_repo": inspect_github_model_repo,
    "register_github_model_repo": register_github_model_repo,
    "list_models": list_models,
    "run_model": run_model,
    "run_planned_model": run_planned_model,
    "plot": plot,
    "plot_planned_chart": plot_planned_chart,
    "discover_literature": discover_literature,
    "ingest_paper": ingest_paper,
    "research_plan": research_plan,
}

# Values supplied by the caller, never by the model. A leading underscore is stripped
# from whatever the model sent before dispatch, so none of these can be forged from a
# tool call.
OWNER_SCOPED = ("run_model", "run_planned_model", "read_reference_dataset", "plot", "plot_planned_chart")
SWITCH_AWARE = ("run_model", "run_planned_model", "list_models")
SESSION_SCOPED = (
    "list_literature", "read_literature", "list_models", "read_research_guideline", "read_model_instruction",
    "research_capability_check",
    "read_paper_figure", "inspect_paper_figure", "register_model_guideline",
    "inspect_github_model_repo", "register_github_model_repo", "discover_literature", "ingest_paper"
)
SESSION_SCOPED = SESSION_SCOPED + ("research_plan", "run_model", "run_planned_model", "plot_planned_chart")
SESSION_SCOPED = SESSION_SCOPED + ("plot",)
CORPUS_TOOLS = (
    "list_literature", "read_literature", "read_research_guideline",
    "read_paper_figure", "inspect_paper_figure", "discover_literature", "ingest_paper",
)
ONLINE_TOOLS = ("discover_literature", "inspect_github_model_repo")


def specs(switches_in=None):
    """The tool list the model is offered.

    The corpus ablation removes the literature tools. The online layer removes the two
    that reach outside, so with PHYSEARTH_ONLINE=0 the model is never offered a tool that
    cannot work; it is not left to discover that by being refused.
    """
    hidden = set()
    if not switches.resolve(switches_in)["literature"]:
        hidden |= set(CORPUS_TOOLS)
    if not http.online():
        hidden |= set(ONLINE_TOOLS)
    return [s for s in SPECS if s["function"]["name"] not in hidden]


def call(name, arguments, owner=None, switches_in=None, session=None):
    flags = switches.resolve(switches_in)
    offered = {t["function"]["name"] for t in specs(switches_in)}
    if name in DISPATCH and name not in offered:
        return _fail("Unknown tool %r. Available tools: %s." % (name, ", ".join(sorted(offered))))
    handler = DISPATCH.get(name)
    if handler is None:
        return _fail("Unknown tool %r. Available tools: %s." % (name, ", ".join(sorted(offered))))
    arguments = {k: v for k, v in (arguments or {}).items() if not str(k).startswith("_")}
    if name in OWNER_SCOPED:
        arguments["_owner"] = owner
    if name in SWITCH_AWARE:
        arguments["_switches"] = flags
    if name in SESSION_SCOPED:
        arguments["_session"] = session
    try:
        with registry.session_context(session):
            return handler(**arguments)
    except TypeError as exc:
        return _fail("Bad arguments for %s: %s" % (name, exc))

# The remaining names the single-module version exposed, kept reachable at the same
# address so nothing outside this package has to know the split happened.
from physearth.tools.charts import (
    _condition_subtitle,
    _review_planned_figure,
    _temporary_figure_dir,
)
from physearth.tools.common import _offline_note
from physearth.tools.figures import (
    _extract_vector_figure_observations,
    _figure_id_key,
    _paper_figure,
    _trusted_asset_bytes,
)
from physearth.tools.literature import _vision_enabled
from physearth.tools.runs import _model_failure
from physearth.tools.specs import (
    CAPABILITY_CHECK_SPEC,
    DISCOVER_SPEC,
    GITHUB_INSPECT_SPEC,
    GITHUB_REGISTER_SPEC,
    INGEST_SPEC,
    LIST_MODELS_SPEC,
    MODEL_GUIDELINE_REGISTRATION_SPEC,
    MODEL_INSTRUCTION_SPEC,
    PAPER_FIGURE_INSPECTION_SPEC,
    PAPER_FIGURE_SPEC,
    PLOT_PLANNED_CHART_SPEC,
    PLOT_SPEC,
    READ_REFERENCE_SPEC,
    RESEARCH_GUIDELINE_SPEC,
    RESEARCH_PLAN_SPEC,
    RUN_MODEL_SPEC,
    RUN_PLANNED_MODEL_SPEC,
)
