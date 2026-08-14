"""Local PDF paper ingestion.

PyMuPDF is an optional runtime dependency for deployments that expose PDF upload.  The parser
keeps page text and embedded image assets; it never guesses numeric series from a plot.
"""

import re
from pathlib import Path

MAX_PDF_BYTES = 50_000_000


def parse(path):
    path = Path(path).resolve()
    if path.suffix.lower() != ".pdf":
        raise ValueError("paper upload must be a PDF")
    if not path.is_file():
        raise ValueError("uploaded PDF does not exist")
    if path.stat().st_size > MAX_PDF_BYTES:
        raise ValueError("uploaded PDF exceeds the 50 MB limit")
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF ingestion requires PyMuPDF; install pymupdf") from exc

    doc = fitz.open(str(path))
    metadata = doc.metadata or {}
    sections = []
    figures = []
    for page_index, page in enumerate(doc, 1):
        text = (page.get_text("text") or "").strip()
        if text:
            sections.append(("Page %d" % page_index, text))
        for image_index, image in enumerate(page.get_images(full=True), 1):
            xref = image[0]
            try:
                extracted = doc.extract_image(xref)
            except Exception:
                continue
            payload = extracted.get("image")
            if not payload:
                continue
            figures.append(
                {
                    "id": "page-%d-image-%d" % (page_index, image_index),
                    "label": "Page %d image %d" % (page_index, image_index),
                    "caption": _caption(text),
                    "page": page_index,
                    "source_uri": "",
                    "asset_bytes": payload,
                    "asset_format": extracted.get("ext") or "bin",
                    "asset_status": "extracted",
                }
            )
    title = (metadata.get("title") or "").strip() or path.stem
    return {
        "doi": "",
        "front": {
            "title": title,
            "authors": [item.strip() for item in (metadata.get("author") or "").split(",") if item.strip()],
            "journal": "",
            "year": _year(metadata.get("creationDate") or ""),
            "license": "",
            "license_url": "",
            "abstract": "",
        },
        "sections": sections,
        "figures": figures,
        "tables": [],
        "source": "pdf_upload",
        "url": str(path),
        "filename": path.name,
    }


def _year(value):
    match = re.search(r"(19|20)\d{2}", str(value or ""))
    return int(match.group(0)) if match else None


def _caption(text):
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if re.match(r"^(figure|fig\.?|table)\s+\d+", line, re.I):
            return " ".join(lines[index:index + 3])[:1200]
    return ""
