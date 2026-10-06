"""Versioned, data-driven instructions for registered physical models.

Model instructions are deliberately kept outside the system prompt.  They are read as a
method resource immediately before a reviewed research plan and are tracked in the session
so the harness can require them without hardcoding model-specific science into Python prompt
strings.
"""

import hashlib
import re
from pathlib import Path

from physearth import config, paths

ROOT = paths.knowledge() / "model_guidelines"
MAX_CHARS = 24000
SAFE_NAME = re.compile(r"^[a-zA-Z0-9_.-]+$")


def _safe(value, label="name"):
    value = str(value or "").strip()
    if not value or not SAFE_NAME.fullmatch(value):
        raise ValueError("invalid model guideline %s" % label)
    return value


def _read(path):
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n[guideline truncated at output limit]"
    return text


def bundled(model, card=None):
    """Return the bundled instruction record for a registered model, if present."""
    model = _safe(model, "model")
    card = card or {}
    relative = card.get("instruction_path") or "model_guideline.md"
    relative = Path(str(relative))
    if relative.is_absolute() or ".." in relative.parts:
        return None
    path = ROOT / model / relative
    text = _read(path)
    source = "bundled"
    if text is None:
        # A registered model without a separate prose file still has a safe, minimal
        # instruction assembled from its validated card.  Domain maintainers can replace
        # this fallback with a richer user guideline without changing the global prompt.
        parameters = card.get("parameters") or {}
        outputs = card.get("outputs") or {}
        text = "# %s model instruction\n\n%s\n\n" % (model, card.get("description") or "")
        text += "Use the model card as the authority for parameters, units, ranges, combinations and outputs.\n"
        text += "Parameters: %s. Outputs: %s." % (", ".join(parameters), ", ".join(outputs))
        source = "model_card_fallback"
    version = str(card.get("instruction_version") or "1.0")
    instruction_id = str(card.get("instruction_id") or model)
    return {
        "model": model,
        "instruction_id": instruction_id,
        "version": version,
        "source": source,
        "path": str(path),
        "text": text,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "temporary": True,
    }


def project_root(project_id):
    project_id = _safe(project_id, "project id")
    path = config.state_dir() / "projects" / project_id / "model_guidelines"
    path.mkdir(parents=True, exist_ok=True)
    return path


def register(model, text, version="1.0", project_id=None, source="user"):
    """Persist a user guideline in the project artifact store.

    The caller supplies model identity after checking that the model is registered.  The
    guideline is not executed and is not merged into the global prompt.
    """
    model = _safe(model, "model")
    text = str(text or "").strip()
    if not text:
        raise ValueError("model guideline content cannot be empty")
    if len(text) > MAX_CHARS:
        raise ValueError("model guideline exceeds the %d character limit" % MAX_CHARS)
    project_id = project_id or "shared"
    root = project_root(project_id) / model
    root.mkdir(parents=True, exist_ok=True)
    path = root / "model_guideline.md"
    path.write_text(text, encoding="utf-8")
    meta = {
        "model": model,
        "instruction_id": "%s-user" % model,
        "version": str(version or "1.0"),
        "source": source,
        "path": str(path),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    (root / "manifest.json").write_text(
        __import__("json").dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    meta["text"] = text
    return meta


def register_temporary(model, text, version="1.0", session=None, source="user"):
    """Register guideline text only in a temporary evaluation session."""
    if session is None:
        raise ValueError("a session is required for a temporary model guideline")
    model = _safe(model, "model")
    text = str(text or "").strip()
    if not text:
        raise ValueError("model guideline content cannot be empty")
    if len(text) > MAX_CHARS:
        raise ValueError("model guideline exceeds the %d character limit" % MAX_CHARS)
    meta = {
        "model": model,
        "instruction_id": "%s-user" % model,
        "version": str(version or "1.0"),
        "source": source,
        "path": "session:%s/model_guideline.md" % session.get("id", "evaluation"),
        "text": text,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "temporary": True,
    }
    session.setdefault("model_guidelines", {})[model] = meta
    return meta


def read(model, card=None, session=None):
    """Resolve a project/user instruction first, then the bundled instruction."""
    model = _safe(model, "model")
    temporary = (session or {}).get("model_guidelines") or {}
    if model in temporary and temporary[model].get("temporary"):
        return dict(temporary[model])
    project_id = (session or {}).get("id") if session else None
    if project_id:
        path = config.state_dir() / "projects" / project_id / "model_guidelines" / model / "model_guideline.md"
        text = _read(path)
        if text is not None:
            return {
                "model": model,
                "instruction_id": "%s-user" % model,
                "version": "user",
                "source": "user",
                "path": str(path),
                "text": text,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
    return bundled(model, card)
