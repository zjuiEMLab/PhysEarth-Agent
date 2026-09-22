"""One Python surface that plugin hosts drive.

Codex reaches this repository through an MCP server, DeepSeek Harness through a Cordis
plugin, and both need the same three things: the capabilities the engine declares, the
prompt stack that makes an answer scientific, and a way to run one tool call or one agent
turn. Keeping that in one module means a plugin never reaches past the package's declared
surface, and the two hosts cannot drift into calling the engine two different ways.

Two facts shape the design:

- a physical model run returns a *handle*, not a number, and the handle resolves only
  inside the session that produced it, so sessions live here and are addressed by id
  instead of being rebuilt per call;
- a run is approved by a human in the interactive product, so a headless host must say
  what it wants: `approve_runs=False` keeps the approval gate on (a plugin that has its
  own consent step can then answer it), and `approve_runs=True` states plainly that the
  host is taking that responsibility.
"""

from __future__ import annotations

import threading
import uuid

from physearth import agent, config, paths, prompt, registry, research, tools
from physearth import session as session_state
from physearth.corpus import knowledge, reference
from physearth.harness import approval

_LOCK = threading.Lock()
_SESSIONS: dict = {}


def _jsonable(value):
    """Session state holds sets, tuples and objects; a plugin host needs plain JSON."""
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_jsonable(item) for item in value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def new_session(model=None, approve_runs=False):
    """Create one engine session and return the address a host keeps for later calls."""
    session = agent.new_session(model or agent.default_model())
    approval.set_mode(session, approval.ALWAYS if approve_runs else approval.ASK)
    session["research_required"] = False
    with _LOCK:
        _SESSIONS[session["id"]] = session
    return {
        "session_id": session["id"],
        "model": session.get("model"),
        "approval": "always" if approve_runs else "ask",
    }


def get_session(session_id):
    """The live session, or None when the id is unknown to this process."""
    if session_id and session_id in _SESSIONS:
        return _SESSIONS[session_id]
    return None


def resolve_session(session_id=None, model=None, approve_runs=False):
    """Return the named session, or create one; unknown ids are not silently replaced."""
    session = get_session(session_id)
    if session is not None:
        return session, None
    if session_id:
        return None, {
            "status": "terminal_error",
            "error": "unknown_session",
            "summary": (
                "Session %r is not held by this process. Run results resolve only inside the "
                "session that produced them, so call new_session first." % session_id
            ),
        }
    created = new_session(model=model, approve_runs=approve_runs)
    return get_session(created["session_id"]), None


def sessions():
    """Every session this process holds, newest id last."""
    with _LOCK:
        return [_session_summary(session) for session in _SESSIONS.values()]


def drop_session(session_id):
    with _LOCK:
        return _SESSIONS.pop(session_id, None) is not None


def _session_summary(session):
    project = session.get("research") or {}
    return {
        "session_id": session.get("id"),
        "model": session.get("model"),
        "turns": session.get("turns", 0),
        "model_runs": session.get("model_runs", 0),
        "tool_calls": session.get("tool_calls", 0),
        "evidence": _evidence_counts(session),
        "research_phase": project.get("phase"),
        "plan_version": project.get("plan_version"),
    }


def _evidence_counts(session):
    return {
        "sections": len(session.get("sections_read") or ()),
        "models_run": len(session.get("models_run") or ()),
        "datasets": len(session.get("datasets_read") or ()),
        "skills": len(session.get("skills_read") or ()),
        "abstracts": len(session.get("abstracts_seen") or ()),
        "figures": len([f for f in session.get("figures") or () if not f.get("preview")]),
        "handles": len(session.get("handles") or ()),
    }


def _models():
    """Every registered model; the registry addresses them by name."""
    registered = registry.all_models()
    return list(registered.values()) if hasattr(registered, "values") else list(registered)


def health():
    """What this checkout can actually do, in one call, without touching the network."""
    models = _models()
    return {
        "root": str(paths.root()) if hasattr(paths, "root") else "",
        "models": len(models),
        "runnable_models": len([item for item in models if item.runnable]),
        "tools": len(tools.SPECS),
        "knowledge": _knowledge_counts(),
        "credentials": bool(config.has_token()),
        "online": str(config.get("PHYSEARTH_ONLINE")) != "0",
    }


def _knowledge_counts():
    papers = list(knowledge.slugs("paper"))
    return {
        "papers": len(papers),
        "sections": sum(len(knowledge.section_index(slug) or []) for slug in papers),
        "skills": len(knowledge.skills() or []),
        "reference_datasets": len(reference.slugs() or []),
    }


def tools_manifest():
    """Every tool the agent may call, as the model sees it."""
    manifest = []
    for spec in tools.SPECS:
        function = spec.get("function") or {}
        manifest.append(
            {
                "name": function.get("name"),
                "description": function.get("description", ""),
                "parameters": function.get("parameters") or {},
            }
        )
    return manifest


def models_manifest():
    """Every registered model with the declaration a run is validated against."""
    manifest = []
    for item in _models():
        card = item.card
        manifest.append(
            {
                "name": item.name,
                "version": card.get("version"),
                "tier": item.tier,
                "runnable": item.runnable,
                "unavailable_reason": item.unavailable_reason,
                "description": card.get("description", ""),
                "citation": card.get("citation", ""),
                "license": card.get("license", ""),
                "parameters": {
                    name: {
                        key: spec.get(key)
                        for key in ("type", "unit", "description", "minimum", "maximum", "default", "enum")
                        if key in spec
                    }
                    for name, spec in (card.get("parameters") or {}).items()
                },
                "outputs": {
                    name: {
                        key: spec.get(key)
                        for key in ("unit", "description", "valid_min", "valid_max")
                        if key in spec
                    }
                    for name, spec in (card.get("outputs") or {}).items()
                },
            }
        )
    return manifest


def knowledge_manifest():
    """The evidence the agent may read, and how it is addressed when cited."""
    papers = []
    for slug in sorted(knowledge.slugs("paper")):
        card = knowledge.card(slug) or {}
        papers.append(
            {
                "slug": slug,
                "title": card.get("title"),
                "license": card.get("license"),
                "sections": sorted(
                    str(section.get("id")) for section in (knowledge.section_index(slug) or [])
                ),
                "citation_key": "[%s#<section>]" % slug,
            }
        )
    return {
        "papers": papers,
        "skills": [
            {
                "slug": item.get("slug"),
                "title": item.get("title"),
                "citation_key": "[skill:%s]" % item.get("slug"),
            }
            for item in sorted(knowledge.skills() or [], key=lambda entry: str(entry.get("slug")))
        ],
        "reference_datasets": [
            {"slug": slug, "citation_key": "[data:%s]" % slug}
            for slug in sorted(reference.slugs() or ())
        ],
    }


def prompt_stack():
    """The L0-L2 prompt blocks plus the generated context: what makes an answer scientific.

    This is the text a host injects so the model it runs behaves like this project's agent:
    identity and style, the citation and evidence-tier rules, the untrusted-text boundary,
    and the explore → plan → approve → run → report workflow.
    """
    blocks = [
        prompt.ROLE,
        prompt.STYLE,
        prompt.CITATION_RULES,
        prompt.ABSTRACT_RULE,
        prompt.ONLINE_RULES,
        prompt.WORKFLOW,
        prompt.RESEARCH_WORKFLOW,
        prompt.TRIGGERS,
        prompt.models_section(),
        prompt.reference_section(),
        prompt.skills_section(),
        prompt.catalogue_section(),
    ]
    return "\n\n".join(block.strip() for block in blocks if block and block.strip())


def call(name, arguments=None, session_id=None, switches=None, approve_runs=False):
    """Run one tool call inside a session and report what the engine decided."""
    session, problem = resolve_session(session_id, approve_runs=approve_runs)
    if problem is not None:
        return problem
    # A tool call is bookkept where the loop bookkeeps it.  Without this, a host that
    # drives tools directly would hold a result handle the session never registered, and
    # every later question about "what has been run here" would answer with nothing --
    # the engine's own recorder is the one place that decides what a run means.
    state = session_state.new_state(session)
    result = tools.call(
        name,
        arguments or {},
        owner=session["id"],
        switches_in=switches,
        session=session,
    )
    session_state.bump(state, "tool_calls")
    agent._record_tool_result(name, result, state, [])
    return _jsonable(result)


def ask(question, session_id=None, model=None, switches=None, approve_runs=False):
    """Run one agent turn and return the answer, the trace and the session address.

    A host without credentials gets a structured refusal rather than a traceback: the
    answer to a physics question must never be invented locally to fill the gap.
    """
    if not config.has_token() and not str(config.get("PHYSEARTH_LLM_API_BASE") or "").startswith(
        ("http://127.0.0.1", "http://localhost")
    ):
        return {
            "status": "terminal_error",
            "error": "no_credentials",
            "summary": (
                "No inference credentials are configured (PHYSEARTH_LLM_API_KEY or "
                "MODELSCOPE_TOKEN). Nothing was computed."
            ),
        }
    session, problem = resolve_session(session_id, model=model, approve_runs=approve_runs)
    if problem is not None:
        return problem
    answer, events, state = agent.run(question, model=model, session=session, switches=switches)
    return {
        "status": "success",
        "session_id": session["id"],
        "answer": answer,
        "events": _jsonable(events),
        "counters": {
            "model_calls": state.get("model_calls", 0),
            "tool_calls": state.get("tool_calls", 0),
            "model_runs": state.get("model_runs", 0),
            "interventions": state.get("interventions", 0),
        },
        "evidence": evidence(session["id"]),
    }


def evidence(session_id):
    """What the session actually read, ran and drew: the material a citation may resolve to."""
    session = get_session(session_id)
    if session is None:
        return {"status": "terminal_error", "error": "unknown_session", "summary": session_id}
    project = session.get("research") or {}
    plan = project.get("plan") or {}
    return {
        "session_id": session["id"],
        "counts": _evidence_counts(session),
        "sections_read": sorted(session.get("sections_read") or ()),
        "models_run": sorted(session.get("models_run") or ()),
        "datasets_read": sorted(session.get("datasets_read") or ()),
        "skills_read": sorted(session.get("skills_read") or ()),
        "successful_runs": [
            {
                "planned_run_id": run.get("planned_run_id"),
                "model": run.get("model"),
                "handle": run.get("handle"),
            }
            for run in session.get("successful_runs") or ()
        ],
        "figures": [
            {
                "figure_number": figure.get("figure_number"),
                "planned_chart_id": figure.get("planned_chart_id"),
                "image_path": figure.get("image_path"),
                "preview": bool(figure.get("preview")),
            }
            for figure in session.get("figures") or ()
        ],
        "research": {
            "phase": project.get("phase"),
            "plan_version": project.get("plan_version"),
            "planned_runs": [run.get("id") for run in plan.get("runs") or ()],
            "planned_charts": [chart.get("id") for chart in plan.get("charts") or ()],
        },
        "handles": [
            {"handle": item.get("handle"), "line": item.get("line")}
            for item in (session.get("handles") or ())[-10:]
        ],
    }


def plan_status(session_id):
    """The research plan and its review state, so a host can show a review step."""
    session = get_session(session_id)
    if session is None:
        return {"status": "terminal_error", "error": "unknown_session", "summary": session_id}
    project = session.get("research") or {}
    if not project:
        return {
            "status": "success",
            "phase": None,
            "plan": None,
            "next_action": _next_action(None),
        }
    return {
        "status": "success",
        "phase": project.get("phase"),
        "plan_version": project.get("plan_version"),
        "plan": _jsonable(project.get("plan") or {}),
        "review_actions": _jsonable(project.get("review_log") or []),
        "next_action": _next_action(project.get("phase")),
    }


def _next_action(phase):
    return {
        "plan_review": "review the plan, then approve or revise it",
        "plan_approved": "generate the pseudo-data preview",
        "pseudo_preview": "choose the charts to produce",
        "chart_selected": "approve formal execution",
        "approved": "run the planned models, then plot and review the figures",
        "completed": "read the report",
    }.get(phase, "start a research plan")


def review(session_id, choice):
    """Advance the human review gate: the same single entry point the Studio uses."""
    session = get_session(session_id)
    if session is None:
        return {"status": "terminal_error", "error": "unknown_session", "summary": session_id}
    result = research.review_action(session, choice)
    return _jsonable(result)
