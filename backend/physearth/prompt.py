"""The system prompt, assembled from the levelled text in `prompts/`.

The text itself is no longer here. It lives one file per block under `prompts/`, so a
scientist can change what the agent is told without opening Python, and a change to the
wording shows up in review as a change to that file rather than buried in a module.

What stays in Python is the part that is not text: which blocks are in play for a given
set of ablation switches, and the four sections that are generated per turn from live
state -- the registered models, the reference datasets, the corpus catalogue and the run
status. Those cannot be a file, because they are different on every call.

The levels, and where each one lives:

    L0  identity   prompts/00-role.md, 01-style.md
    L1  policy     prompts/10-citations.md, 11-abstract-only.md, 12-online.md,
                   13-citations-no-corpus.md, plus untrusted.RULE, which stays with the
                   boundary code that enforces it
    L2  workflow   prompts/20-workflow.md, 21-research.md, 22-triggers.md,
                   23-workflow-no-corpus.md
    L3  context    generated below: models_section, reference_section,
                   catalogue_section, skills_section, status_block
    L4  methods    knowledge/skills/ -- not prompt text. Those are cited evidence, read
                   through the tools and carrying [skill:slug] markers; only a listing of
                   them reaches the prompt, through skills_section()
    L5  profiles   evaluation/prompts/*.yaml -- per-experiment instructions belonging to
                   the evaluation harness, which loads them itself

`prompts/README.md` says the same thing for a reader who is not in Python.
"""

from physearth import paths, registry
from physearth import session as session_state
from physearth.corpus import knowledge, reference
from physearth.harness import switches, untrusted


def _text(name):
    """One block of prompt text, exactly as written, without its final newline.

    The file carries a trailing newline because every text file should; the block it
    stands for does not, because it is joined to its neighbours by a blank line.
    """
    body = (paths.prompts() / name).read_text(encoding="utf-8")
    return body[:-1] if body.endswith("\n") else body


ROLE = _text("00-role.md")
STYLE = _text("01-style.md")
CITATION_RULES = _text("10-citations.md")
ABSTRACT_RULE = _text("11-abstract-only.md")
ONLINE_RULES = _text("12-online.md")
NO_CORPUS_CITATION_RULES = _text("13-citations-no-corpus.md")
WORKFLOW = _text("20-workflow.md")
RESEARCH_WORKFLOW = _text("21-research.md")
TRIGGERS = _text("22-triggers.md")
NO_CORPUS_WORKFLOW = _text("23-workflow-no-corpus.md")
RAW_EVALUATION_WORKFLOW = _text("24-raw-evaluation.md")


def models_section(declared=True, session=None):
    if not declared:
        return (
            "Registered physical models. These are the only sources of numerical results. "
            "Their parameter ranges and legal combinations are not published here; infer "
            "suitable values yourself.\n\n%s" % registry.capability_block(
                declared=False, session=session
            )
        )
    return (
        "Registered physical models. These are the only sources of numerical results; the "
        "declaration below is what the system validates your calls against.\n\n"
        "This table is here so you can choose a model and get a call right the first time. "
        "Reading it is not an act you performed in the conversation, so it earns no "
        "citation: a [model:name@version] marker resolves only after you have run that "
        "model or called list_models on it. If you want to state its version, a range or a "
        "constraint in the answer, call list_models first. Do not cite a version you have "
        "only seen here.\n\n%s" % registry.capability_block(session=session)
    )


def reference_section():
    return (
        "Measured reference data. These are observations, not model output. Use "
        "read_reference_dataset to look at them, and use them when a question asks how a "
        "model compares with reality.\n\n%s" % reference.catalogue_block()
    )


def skills_section():
    return (
        "Methods. These are short procedure notes, not papers.\n\n%s\n\n%s"
        % (knowledge.skills_block(), TRIGGERS)
    )


def catalogue_section():
    return "Literature corpus (%d papers). Slug, title, coverage, and what each is for:\n\n%s" % (
        len(knowledge.slugs()),
        knowledge.catalogue_block(),
    )


def online_available():
    """The online layer is a deployment choice, so the prompt only claims it when it is on."""
    from physearth.ingest import http

    return http.online()


def status_block(state):
    session = state.get("session") or {}
    def usage(value, cap):
        return "%d/%s" % (value, cap if cap else "unlimited")
    status = (
        "Run status. This question has used %s LLM calls and %s tool calls. This "
        "conversation has used %s LLM calls and %s tool calls in total, over %d "
        "question(s)."
        % (
            usage(state.get("model_calls", 0), state.get("max_model_calls", 0)),
            usage(state.get("tool_calls", 0), state.get("max_tool_calls", 0)),
            usage(session.get("model_calls", 0), session.get("max_model_calls", 0)),
            usage(session.get("tool_calls", 0), session.get("max_tool_calls", 0)),
            session.get("turns", 0),
        )
    )
    if session.get("research_required") and not session.get("research"):
        status += (
            " Research mode is active for this turn. Complete the resource reads and submit "
            "research_plan before any run_model call; do not answer with a direct simulation."
        )
    capability = session.get("capability_review") or {}
    if capability.get("status") == "waiting_user":
        status += (
            " A reproduction capability checkpoint is waiting for explicit user confirmation "
            "of partial scope; do not call research_plan until the user confirms."
        )
    return status


def build(state=None):
    flags = switches.resolve((state or {}).get("switches"))
    if flags["paper_access"] == "raw_pdf":
        blocks = [
            ROLE,
            RAW_EVALUATION_WORKFLOW,
            untrusted.RULE,
            STYLE,
        ]
        if state:
            blocks.append(status_block(state))
        return "\n\n".join(blocks)
    research_workflow = RESEARCH_WORKFLOW
    if not flags["literature"]:
        research_workflow = research_workflow.replace(
            "read_literature", "the available source tools"
        )
    if flags["literature"]:
        blocks = [
            ROLE,
            models_section(flags["capability"], (state or {}).get("session")),
            reference_section(),
            catalogue_section(),
            skills_section(),
            WORKFLOW,
            research_workflow,
        ]
        citations = CITATION_RULES
        if online_available():
            blocks.append(ONLINE_RULES)
            citations = citations.replace(
                "\n\nModels: [model:", "\n\n%s\n\nModels: [model:" % ABSTRACT_RULE
            )
        blocks += [untrusted.RULE, citations, STYLE]
    else:
        blocks = [
            ROLE,
            models_section(flags["capability"], (state or {}).get("session")),
            reference_section(),
            NO_CORPUS_WORKFLOW,
            research_workflow,
            untrusted.RULE,
            NO_CORPUS_CITATION_RULES,
            STYLE,
        ]
    if state:
        held = session_state.held_block(state.get("session"))
        if held:
            blocks.append(held)
        blocks.append(status_block(state))
    return "\n\n".join(blocks)
