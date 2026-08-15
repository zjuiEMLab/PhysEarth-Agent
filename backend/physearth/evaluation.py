"""Session-only Evaluation workbench helpers.

The normal Live Agent keeps approved papers and research artifacts in the project store.
Evaluation experiments deliberately use a separate ephemeral session so a visitor can
inspect a model, attach a guideline, ingest a DOI/PDF and run a test without changing the
bundled registry or persistent project evidence.
"""

import shutil
import time
from pathlib import Path

from physearth import agent, github_models, registry, tools
from physearth.corpus import model_guidelines
from physearth.harness import results
from physearth.ingest import http

SESSION_TTL_SECONDS = 60 * 60


def new_session(model=None):
    session = agent.new_session(model, unrestricted=True)
    session["ephemeral"] = True
    session["evaluation"] = True
    session["research_required"] = False
    session["evaluation_expires_at"] = time.time() + SESSION_TTL_SECONDS
    return session


def expired(session):
    return bool(session and session.get("evaluation_expires_at", 0) <= time.time())


def touch(session):
    if session is not None:
        session["evaluation_expires_at"] = time.time() + SESSION_TTL_SECONDS
    return session


def inspect_model(session, url, ref="main"):
    if session is None:
        return {"status": "terminal_error", "summary": "Evaluation session is missing."}
    if not http.online():
        return {
            "status": "terminal_error",
            "summary": "GitHub inspection is unavailable while online services are disabled.",
        }
    try:
        proposal, files = github_models.inspect(url, ref)
        github_models.hold_temporary_proposal(session, proposal, files)
    except Exception as exc:
        return {"status": "terminal_error", "summary": "GitHub inspection failed: %s" % exc}
    return {
        "status": "success" if proposal.get("safe_to_register") else "needs_input",
        "summary": "Inspected %s at %s. Remote code was not executed." % (url, ref),
        "data": proposal,
    }


def approve_model(session, proposal_id):
    if session is None:
        return {"status": "terminal_error", "summary": "Evaluation session is missing."}
    return github_models.approve_temporary(session, proposal_id)


def attach_guideline(session, model, content, version="1.0"):
    if registry.get(str(model or "").strip(), session) is None:
        return {
            "status": "needs_input",
            "summary": "Register or select a model before attaching its guideline.",
        }
    try:
        item = model_guidelines.register_temporary(model, content, version, session)
    except ValueError as exc:
        return {"status": "terminal_error", "summary": str(exc)}
    return {
        "status": "success",
        "summary": "Attached temporary guideline %s v%s." % (item["model"], item["version"]),
        "data": {key: value for key, value in item.items() if key != "text"},
    }


def ingest_doi(session, doi):
    return tools.ingest_paper(doi=doi, _session=session, _persist=False)


def ingest_pdf(session, file_path):
    return tools.ingest_paper(file_path=file_path, _session=session, _persist=False)


def run_test(session, question, physical_model=None):
    if session is None:
        return "", [], None, {"status": "terminal_error", "summary": "Evaluation session is missing."}
    question = str(question or "").strip()
    if not question:
        return "", [], None, {"status": "needs_input", "summary": "Enter a test question first."}
    if physical_model:
        session["evaluation_model"] = str(physical_model).strip()
        session["model"] = session["evaluation_model"]
    answer, events, state = agent.run(question, session=session)
    return answer, events, state, {
        "status": "success",
        "summary": "Temporary Evaluation test completed with %d event(s)." % len(events),
    }


def clear(session):
    if session is None:
        return
    results.clear_owner(session.get("id"))
    if session.get("temporary_figure_dir"):
        shutil.rmtree(Path(session["temporary_figure_dir"]), ignore_errors=True)
    registry.clear_session(session)
    session.clear()


def model_summary(session):
    result = tools.call("list_models", {}, session=session)
    return result.get("data") or {}
