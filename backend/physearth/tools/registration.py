"""Inspecting and registering a model: the guideline, the repository, the catalogue."""

from physearth import github_models, registry
from physearth.corpus import model_guidelines
from physearth.harness import switches
from physearth.ingest import http
from physearth.tools.common import _fail, _ledger, _offline_note, _ok


def register_model_guideline(model, content, version="1.0", _session=None):
    entry = registry.get(str(model or "").strip(), _session)
    if entry is None:
        return _fail("Unknown model %r. Register the model before its guideline." % model)
    if _session is None:
        return _fail("register_model_guideline requires a session.")
    try:
        if _session.get("ephemeral"):
            item = model_guidelines.register_temporary(entry.name, content, version, _session)
        else:
            item = model_guidelines.register(entry.name, content, version, _session.get("id"), source="user")
    except ValueError as exc:
        return _fail(str(exc))
    _session.setdefault("model_guidelines", {})[entry.name] = item
    return _ok(
        "Registered user guideline %s v%s for %s." % (item["instruction_id"], item["version"], entry.name),
        {key: value for key, value in item.items() if key != "text"},
    )


def inspect_github_model_repo(url, ref="main", _session=None):
    if not http.online():
        return _offline_note("inspecting a GitHub model repository")
    if _session is None:
        return _fail("GitHub inspection requires a session.")
    try:
        proposal, files = github_models.inspect(url, ref)
        proposal = github_models.save_proposal(_session, proposal, files)
    except (ValueError, LookupError, http.Upstream) as exc:
        return _fail("GitHub repository inspection failed: %s" % exc)
    return _ok(
        "Inspected GitHub repository %s at %s. No remote code was executed; human approval is required before registration." % (url, ref),
        {key: value for key, value in proposal.items() if key != "root"},
    )


def register_github_model_repo(proposal_id, approval_token="", _session=None):
    if _session is None:
        return _fail("GitHub registration requires a session.")
    return github_models.register(_session, proposal_id, approval_token)


def list_models(model=None, _switches=None, _session=None):
    declared = switches.resolve(_switches)["capability"]
    if model in (None, ""):
        rows = registry.summary(_session)
        rejected = registry.rejected()
        for row in rows:
            _ledger(
                _session,
                "model_declaration",
                {
                    "model": row.get("name"),
                    "version": row.get("version"),
                    "source": "list_models",
                    "parameters": row.get("parameters") or {},
                    "outputs": row.get("outputs") or {},
                    "defaults": row.get("defaults") or {},
                },
            )
        return _ok(
            "%d registered model(s), %d rejected." % (len(rows), len(rejected)),
            {"models": rows, "rejected": rejected},
        )
    entry = registry.get(model, _session)
    if entry is None:
        return _fail(
            "Unknown model %r. Registered models: %s." % (model, ", ".join(registry.names(session=_session)) or "none")
        )
    card = entry.card
    if _session is not None:
        _session.setdefault("models_inspected", set()).add(
            "%s@%s" % (card["name"], card["version"])
        )
    result = _ok(
        "Capability declaration for %s v%s." % (card["name"], card["version"])
        if declared
        else "Parameter names for %s v%s. Ranges and combinations are not published."
        % (card["name"], card["version"]),
        {
            "name": card["name"],
            "version": card["version"],
            "tier": card["tier"],
            "runnable_here": entry.runnable,
            "citation": card["citation"],
            "license": card["license"],
            "parameters": card["parameters"]
            if declared
            else registry.undeclared_parameters(card),
            "combinations": (card.get("combinations") or []) if declared else [],
            "outputs": card["outputs"],
            "resource_profile": card.get("resource_profile") or {},
            "instruction_id": card.get("instruction_id") or card["name"],
            "instruction_version": str(card.get("instruction_version") or "1.0"),
            "instruction_available": bool(model_guidelines.read(card["name"], card, _session)),
        },
    )
    _ledger(
        _session,
        "model_declaration",
        {
            "model": card["name"],
            "version": card["version"],
            "source": "list_models",
            "parameters": card.get("parameters") or {},
            "outputs": card.get("outputs") or {},
            "combinations": card.get("combinations") or [],
            "defaults": {
                name: spec.get("default")
                for name, spec in (card.get("parameters") or {}).items()
                if isinstance(spec, dict) and "default" in spec
            },
        },
    )
    if _session is not None:
        _session.setdefault("model_declarations", {})[card["name"]] = {
            "model": card["name"],
            "version": card["version"],
            "parameters": card.get("parameters") or {},
            "outputs": card.get("outputs") or {},
            "combinations": card.get("combinations") or [],
        }
    return result
