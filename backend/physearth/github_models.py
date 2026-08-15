"""Read-only GitHub model inspection and human-approved registration."""

import ast
import hashlib
import json
import re
import secrets
import shutil
import tempfile
import urllib.parse
from pathlib import Path

import yaml

from physearth import artifacts
from physearth.ingest import http
from physearth.models import contract, registry

REPO = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")
MAX_FILE = 300_000


def _repo(url):
    match = REPO.fullmatch(str(url or "").strip())
    if not match:
        raise ValueError("only an https://github.com/owner/repository URL is allowed")
    return match.group(1), match.group(2)


def _api(owner, repo, ref):
    return "https://api.github.com/repos/%s/%s/contents?ref=%s" % (
        owner,
        repo,
        urllib.parse.quote(ref, safe=""),
    )


def _raw(owner, repo, ref, path):
    safe_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    return "https://raw.githubusercontent.com/%s/%s/%s/%s" % (
        owner,
        repo,
        urllib.parse.quote(ref, safe=""),
        safe_path,
    )


def _tree(owner, repo, ref):
    return "https://api.github.com/repos/%s/%s/git/trees/%s?recursive=1" % (
        owner,
        repo,
        urllib.parse.quote(ref, safe=""),
    )


def inspect(url, ref="main"):
    owner, repo = _repo(url)
    ref = str(ref or "main").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.\-/]+", ref):
        raise ValueError("invalid GitHub ref")
    tree_payload, elapsed = http.get_json(_tree(owner, repo, ref), max_bytes=MAX_FILE)
    tree_items = tree_payload.get("tree") if isinstance(tree_payload, dict) else None
    if not isinstance(tree_items, list):
        listing, elapsed = http.get_json(_api(owner, repo, ref), max_bytes=MAX_FILE)
        tree_items = listing if isinstance(listing, list) else []
    names = {
        item.get("path"): item for item in tree_items
        if isinstance(item, dict) and item.get("type") in ("blob", "file")
    }
    wanted = [
        "model_card.yaml", "model_card.yml", "adapter.py", "README.md",
        "model_guideline.md", "guideline.md", "LICENSE",
    ]
    selected = {}
    for name in wanted:
        if name in names:
            selected[name] = name
            continue
        matches = [path for path in names if path.endswith("/" + name)]
        if matches:
            selected[name] = sorted(matches, key=lambda item: (item.count("/"), item))[0]
    files = {}
    for public_name, remote_path in selected.items():
        item = names.get(remote_path)
        if not item:
            continue
        payload, _ = http.get_bytes(_raw(owner, repo, ref, remote_path), max_bytes=MAX_FILE)
        text = payload.decode("utf-8", errors="replace")
        files[public_name] = text
        if remote_path != public_name:
            files[remote_path] = text

    card_text = files.get("model_card.yaml") or files.get("model_card.yml")
    card = yaml.safe_load(card_text) if card_text else None
    problems = [] if isinstance(card, dict) else ["repository does not contain a valid model_card.yaml"]
    if isinstance(card, dict):
        problems.extend(contract.validate_card(card))
    adapter_name = str((card or {}).get("entrypoint", "adapter:run")).split(":", 1)[0] + ".py"
    adapter = files.get(adapter_name) or files.get("adapter.py", "")
    if adapter:
        try:
            ast.parse(adapter)
        except SyntaxError as exc:
            problems.append("adapter.py is not valid Python: %s" % exc)
    else:
        problems.append("declared adapter source was not found")
    guideline_name = next((name for name in ("model_guideline.md", "guideline.md") if name in files), "")
    proposal = {
        "proposal_id": "gh_" + hashlib.sha256((url + "@" + ref).encode()).hexdigest()[:16],
        "repository": url,
        "ref": ref,
        "files": sorted(files),
        "model": {
            key: (card or {}).get(key)
            for key in ("name", "version", "tier", "description", "license", "requires_import")
            if (card or {}).get(key) is not None
        },
        "guideline_file": guideline_name,
        "problems": problems,
        "safe_to_register": not problems and bool(card),
        "elapsed_s": elapsed,
    }
    return proposal, files


def save_proposal(session, proposal, files):
    project = artifacts.project_dir(session.get("id") or "shared") / "model_registrations"
    project.mkdir(parents=True, exist_ok=True)
    proposal_id = proposal["proposal_id"]
    root = project / proposal_id
    root.mkdir(exist_ok=True)
    for name, text in files.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            continue
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    proposal = dict(proposal)
    proposal["root"] = str(root)
    (root / "proposal.json").write_text(json.dumps(proposal, indent=2), encoding="utf-8")
    session.setdefault("github_proposals", {})[proposal_id] = proposal
    return proposal


def hold_temporary_proposal(session, proposal, files):
    """Keep an inspection result in memory for a temporary Evaluation session."""
    if session is None:
        raise ValueError("a session is required")
    proposal = dict(proposal)
    session.setdefault("temporary_github_proposals", {})[proposal["proposal_id"]] = {
        "proposal": proposal,
        "files": dict(files or {}),
    }
    return proposal


def approve_temporary(session, proposal_id):
    """Human UI approval for a session-only GitHub model."""
    token = secrets.token_urlsafe(24)
    session.setdefault("temporary_approval_tokens", {})[str(proposal_id)] = token
    return register_temporary(session, proposal_id, token)


def register_temporary(session, proposal_id, approval_token=""):
    """Register inspected code only in the approved Evaluation session."""
    item = (session.get("temporary_github_proposals") or {}).get(str(proposal_id))
    if not item:
        return {"status": "terminal_error", "summary": "Unknown temporary GitHub proposal %r." % proposal_id}
    proposal = item["proposal"]
    if not proposal.get("safe_to_register"):
        return {
            "status": "terminal_error",
            "summary": "The GitHub proposal has validation problems and cannot be registered.",
            "data": proposal,
        }
    expected = (session.get("temporary_approval_tokens") or {}).get(str(proposal_id))
    if not approval_token or approval_token != expected:
        return {
            "status": "needs_input",
            "summary": "Explicit human approval is required before registering this temporary model.",
            "data": {"proposal_id": proposal_id, "repository": proposal["repository"], "ref": proposal["ref"]},
        }
    root = Path(tempfile.mkdtemp(prefix="physearth-eval-model-"))
    for name, text in (item.get("files") or {}).items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            continue
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    try:
        registered = registry.register_session_directory(
            session, root, source="temporary approved GitHub repository"
        )
    except Exception as exc:
        shutil.rmtree(root, ignore_errors=True)
        return {"status": "terminal_error", "summary": "Temporary model registration failed: %s" % exc}
    session.setdefault("temporary_github_proposals", {})[str(proposal_id)]["registered"] = registered.name
    return {
        "status": "success",
        "summary": "Registered temporary model %s for this Evaluation session." % registered.name,
        "data": {
            "name": registered.name,
            "version": registered.card["version"],
            "source": proposal["repository"],
            "ref": proposal["ref"],
        },
    }


def register(session, proposal_id, approval_token=""):
    proposal = (session.get("github_proposals") or {}).get(str(proposal_id))
    if not proposal:
        return {"status": "terminal_error", "summary": "Unknown GitHub registration proposal %r." % proposal_id}
    if not proposal.get("safe_to_register"):
        return {"status": "terminal_error", "summary": "The GitHub proposal has validation problems and cannot be registered.", "data": proposal}
    expected = (session.get("github_approval_tokens") or {}).get(str(proposal_id))
    if not approval_token or approval_token != expected:
        return {
            "status": "needs_input",
            "summary": "Human approval is required before installing code from this GitHub repository.",
            "data": {"proposal_id": proposal_id, "repository": proposal["repository"], "ref": proposal["ref"]},
            "error": "human approval required",
        }
    model_dir = Path(proposal["root"]) / "model"
    model_dir.mkdir(exist_ok=True)
    for name in ("model_card.yaml", "model_card.yml", "adapter.py", "README.md"):
        source = Path(proposal["root"]) / name
        if source.is_file():
            target = model_dir / ("model_card.yaml" if name == "model_card.yml" else name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
    card = yaml.safe_load((model_dir / "model_card.yaml").read_text(encoding="utf-8"))
    entrypoint = str(card.get("entrypoint") or "adapter:run").split(":", 1)[0] + ".py"
    source = Path(proposal["root"]) / entrypoint
    if source.is_file() and entrypoint != "adapter.py":
        target = model_dir / entrypoint
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    registered = registry.register_directory(model_dir, source="approved GitHub repository")
    return {
        "status": "success",
        "summary": "Registered approved GitHub model %s." % registered.name,
        "data": {"name": registered.name, "version": registered.card["version"], "source": proposal["repository"]},
    }
