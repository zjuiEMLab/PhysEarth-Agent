"""Project-scoped persistence for source papers and generated research artifacts."""

import hashlib
import json
import re
import shutil
from pathlib import Path

from physearth import config

MAX_ASSET_BYTES = 8_000_000
SAFE = re.compile(r"^[a-zA-Z0-9_.-]+$")


def _safe(value, label):
    value = str(value or "").strip()
    if not value or not SAFE.fullmatch(value):
        raise ValueError("invalid %s" % label)
    return value


def project_dir(project_id):
    project_id = _safe(project_id, "project id")
    path = config.state_dir() / "projects" / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def paper_dir(project_id, paper_id):
    path = project_dir(project_id) / "papers" / _safe(paper_id, "paper id")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def persist_paper(project_id, card, record):
    """Persist metadata, sections, tables and any already-fetched figure bytes."""
    paper_id = hashlib.sha256(
        (str(record.get("doi") or card.get("slug") or "paper")).encode("utf-8")
    ).hexdigest()[:20]
    root = paper_dir(project_id, paper_id)
    sections_dir = root / "sections"
    sections_dir.mkdir(exist_ok=True)
    for section in card.get("sections") or []:
        (sections_dir / (str(section["id"]) + ".md")).write_text(
            section.get("text", ""), encoding="utf-8"
        )

    figures = []
    for index, figure in enumerate(record.get("figures") or card.get("figures") or [], 1):
        item = dict(figure)
        payload = item.pop("asset_bytes", None)
        if payload and len(payload) <= MAX_ASSET_BYTES:
            digest = hashlib.sha256(payload).hexdigest()[:20]
            extension = str(item.get("asset_format") or "bin").lower().strip(".")
            if not re.fullmatch(r"[a-z0-9]{1,8}", extension):
                extension = "bin"
            filename = "figure-%s.%s" % (digest, extension)
            asset_path = root / "figures" / filename
            asset_path.parent.mkdir(exist_ok=True)
            if not asset_path.exists():
                asset_path.write_bytes(payload)
            item.update({"asset_path": str(asset_path), "asset_status": "stored"})
        item.setdefault("id", "fig-%d" % index)
        figures.append(item)

    tables = [dict(item) for item in (record.get("tables") or card.get("tables") or [])]
    manifest = {
        "paper_id": paper_id,
        "slug": card.get("slug"),
        "doi": record.get("doi"),
        "source": record.get("source"),
        "source_url": record.get("url"),
        "title": card.get("title"),
        "license": card.get("license"),
        "figures": figures,
        "tables": tables,
        "sections": [
            {key: section.get(key) for key in ("id", "title", "chars", "truncated")}
            for section in card.get("sections") or []
        ],
    }
    _write_json(root / "manifest.json", manifest)
    return {"paper_id": paper_id, "root": str(root), "manifest": manifest}


def persist_run(project_id, research_id, run_id, payload):
    root = project_dir(project_id) / "research" / _safe(research_id, "research id") / "runs"
    root.mkdir(parents=True, exist_ok=True)
    path = root / ("%s.json" % _safe(run_id, "run id"))
    _write_json(path, payload)
    return str(path)


def persist_figure(project_id, research_id, figure_number, payload):
    root = project_dir(project_id) / "research" / _safe(research_id, "research id") / "figures"
    root.mkdir(parents=True, exist_ok=True)
    record = dict(payload or {})
    image_path = Path(str(record.get("image_path") or ""))
    if image_path.is_file():
        stored_image = root / image_path.name
        if not stored_image.exists():
            shutil.copyfile(image_path, stored_image)
        record["artifact_image_path"] = str(stored_image)
    path = root / ("figure-%02d.json" % int(figure_number))
    _write_json(path, record)
    return str(path)
