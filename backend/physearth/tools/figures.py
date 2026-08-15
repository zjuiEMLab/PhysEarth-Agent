"""Reading a figure out of a bundled paper: its identity, its bytes, its vector labels.

Nothing here reaches the network. A figure is served only from the bundled corpus, and
only from a path that resolves inside it.
"""

import re
from pathlib import Path

from physearth import config
from physearth.corpus import knowledge


def _figure_id_key(value):
    """Return a tolerant comparison key for paper figure identifiers.

    Literature providers use several equivalent spellings (``fig03``, ``fig-03``,
    ``figure 3`` and filenames such as ``fig03.png``).  An LLM can also repeat the
    namespace prefix and produce ``fig-fig03``.  Normalisation is only used to find
    an already-declared figure; it never creates a missing figure or changes the
    citation identifier returned to the agent.
    """
    text = str(value or "").strip().lower().replace("\\", "/").rsplit("/", 1)[-1]
    text = re.sub(r"\.(?:png|jpg|jpeg|pdf|svg|webp)$", "", text)
    text = re.sub(r"^figure[\s_-]*", "fig", text)
    while text.startswith("fig-fig"):
        text = "fig" + text[len("fig-fig") :]
    while text.startswith("fig-"):
        text = "fig" + text[len("fig-") :]
    match = re.fullmatch(r"fig(\d+)", text)
    if match:
        return "fig%d" % int(match.group(1))
    return text


def _paper_figure(item, figure_id):
    requested_key = _figure_id_key(figure_id)
    for figure in item.get("figures") or []:
        if _figure_id_key(figure.get("id")) == requested_key:
            return figure
    return None


def _trusted_asset_bytes(item, asset_path):
    """Read a paper asset only from a managed literature or artifact directory."""
    if not asset_path:
        return None, None
    try:
        state_root = config.state_dir().resolve()
        trusted_roots = [state_root, knowledge.KNOWLEDGE_DIR.resolve()]
        artifact_root = ((item.get("artifact") or {}).get("root") or "").strip()
        if artifact_root:
            trusted_roots.append(Path(artifact_root).resolve())
        raw_candidate = Path(str(asset_path))
        candidates = [raw_candidate]
        if not raw_candidate.is_absolute():
            for root in trusted_roots:
                candidates.append(root / raw_candidate)
            paper_dir = item.get("_dir")
            if paper_dir:
                candidates.append(Path(str(paper_dir)) / raw_candidate)
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_file() and any(
                resolved.is_relative_to(root) for root in trusted_roots
            ):
                return resolved.read_bytes(), str(resolved)
    except (OSError, RuntimeError, ValueError):
        pass
    return None, str(asset_path)


def _extract_vector_figure_observations(raw_pdf):
    """Extract labels and ticks from a vector source figure without digitizing curves.

    Publisher figure PDFs commonly retain axis and legend text even when the raster preview
    has no OCR layer. This gives the agent auditable labels and ranges while keeping plotted
    lines as visual evidence rather than silently converting pixels into numeric data.
    """
    if not raw_pdf:
        return {}
    try:
        import fitz

        document = fitz.open(stream=raw_pdf, filetype="pdf")
        if not document:
            return {}
        page = document[0]
        width, height = float(page.rect.width), float(page.rect.height)
        blocks = page.get_text("blocks")
        text_lines = []
        axes = []
        x_ticks = []
        y_ticks = []
        legend = []

        def clean(text):
            value = re.sub(r"\s+", " ", str(text or "")).strip()
            # Superscripts are often emitted as a separate line by PDF text extraction.
            value = re.sub(r"\bm\s+(-?\d+)\b", r"m^\1", value)
            return value

        for block in blocks:
            if len(block) < 5:
                continue
            x0, y0, x1, y1, raw_text = block[:5]
            value = clean(raw_text)
            if not value:
                continue
            lines = [clean(line) for line in str(raw_text).splitlines() if clean(line)]
            text_lines.extend(lines)
            block_width, block_height = x1 - x0, y1 - y0
            numeric_lines = [line for line in lines if re.fullmatch(r"[-+]?\d*\.?\d+", line)]
            if y0 >= height * 0.86 and numeric_lines:
                x_ticks.extend(numeric_lines)
            if x0 <= width * 0.10 and numeric_lines:
                y_ticks.extend(numeric_lines)
            if y0 >= height * 0.78 and block_width > block_height and not numeric_lines:
                axes.append(value)
            if x0 <= width * 0.18 and block_height > block_width and not numeric_lines:
                axes.append(value)
            if (
                len(lines) >= 2
                and block_width > block_height
                and y0 <= height * 0.55
                and x0 >= width * 0.12
            ):
                legend.extend(lines)

        def unique(values):
            return list(dict.fromkeys(value for value in values if value))

        return {
            "source": "publisher figure PDF text layer",
            "axes": unique(axes),
            "legend": unique(legend),
            "x_ticks": unique(x_ticks),
            "y_ticks": unique(y_ticks),
            "panels": 1,
            "panel_detection": "single source-page asset",
            "text": unique(text_lines),
        }
    except (ImportError, OSError, RuntimeError, ValueError):
        return {}
