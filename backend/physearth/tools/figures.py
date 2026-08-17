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
    # A bare number is a figure number. The agent reached read_paper_figure with "03"
    # -- the paper's own section numbering -- and was told the figure did not exist,
    # which is true of the string and false of the figure. This argument only ever
    # names a figure, so a number in it can only mean one thing.
    match = re.fullmatch(r"fig(\d+)", text) or re.fullmatch(r"(\d+)", text)
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



def _group_panels(marks, placed):
    """How many subplots the page text evidences. Markers only, never a guess."""
    labels = {label.strip("()").lower() for _x, _y, label in marks}
    return len(labels) if len(labels) > 1 else 1


def _blank_axis():
    return {"label": [], "ticks": []}


def _panel_detail(marks, placed, x_ticks=(), y_ticks=()):
    """One entry per panel, always -- a figure with one plot is one panel and says so.

    Axes and legends belong to a panel, not to the figure. Hoisting them up when there
    was only one plot meant every reader and every check had to handle two shapes, and
    the single-panel case is the common one.

    Panels are assigned by nearest marker, which is what a reader does. It is a reading
    of the layout, not a claim about the figure: a panel with no text near it comes back
    empty rather than borrowing its neighbour's. Tick values are only attributed to a
    single panel, because ticks carry no marker to sit beside.
    """
    seen, ordered = set(), []
    for x, y, label in marks:
        key = label.strip("()").lower()
        if key not in seen:
            seen.add(key)
            ordered.append((x, y, key))

    if len(ordered) < 2:
        entry = {"panel": "1", "subtitle": "", "x_axis": _blank_axis(), "y_axis": _blank_axis(),
                 "legend": []}
        for _x, _y, kind, value in placed:
            if kind == "legend":
                entry["legend"].extend(v for v in value if v not in entry["legend"])
            elif kind == "x_axis" and not entry["x_axis"]["label"]:
                entry["x_axis"]["label"] = [value]
            elif kind == "y_axis" and not entry["y_axis"]["label"]:
                entry["y_axis"]["label"] = [value]
        entry["x_axis"]["ticks"] = list(x_ticks)
        entry["y_axis"]["ticks"] = list(y_ticks)
        return [entry]

    detail = {
        key: {"panel": key, "subtitle": "", "x_axis": _blank_axis(), "y_axis": _blank_axis(),
              "legend": []}
        for _x, _y, key in ordered
    }
    for x, y, kind, value in placed:
        nearest = min(ordered, key=lambda m: (m[0] - x) ** 2 + (m[1] - y) ** 2)
        entry = detail[nearest[2]]
        if kind == "legend":
            entry["legend"].extend(v for v in value if v not in entry["legend"])
        elif kind == "x_axis" and not entry["x_axis"]["label"]:
            entry["x_axis"]["label"] = [value]
        elif kind == "y_axis" and not entry["y_axis"]["label"]:
            entry["y_axis"]["label"] = [value]
    return [detail[key] for _x, _y, key in ordered]


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
        x_axis = []
        y_axis = []
        x_ticks = []
        y_ticks = []
        legend = []
        panel_marks = []
        placed = []

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
            # A horizontal caption along the bottom is the x label; a block taller than
            # it is wide on the left edge is the y label, set on its side. They were
            # being merged into one `axes` list, which loses which is which -- and a
            # figure is reproduced from knowing that.
            # One line, not several: an axis label is a single caption, while a legend
            # sitting low on the page is a stack of series names. Without that test a
            # legend block was read as the x label -- "SMRT QCA VV SMRT QCA HH ..." is a
            # legend, not an axis.
            # A caption broken by a superscript is still one caption: "Density (kg m"
            # then "3)". Treat trailing fragments of a few characters as continuation,
            # and never take a panel marker for a label.
            marker = bool(re.fullmatch(r"\(?[a-h]\)", value.strip(), re.I))
            single = not marker and (
                len(lines) == 1 or all(len(line) <= 3 for line in lines[1:])
            )
            if y0 >= height * 0.78 and block_width > block_height and not numeric_lines:
                axes.append(value)
                if single:
                    x_axis.append(value)
                    placed.append((x0, y0, "x_axis", value))
                else:
                    legend.extend(lines)
                    placed.append((x0, y0, "legend", lines))
            if x0 <= width * 0.18 and block_height > block_width and not numeric_lines:
                axes.append(value)
                if single:
                    y_axis.append(value)
                    placed.append((x0, y0, "y_axis", value))
            # Panel markers: "(a)", "b)", "(c)". Two or more mean subplots, and then the
            # legends and axes belong to a panel rather than to the figure.
            for line in lines:
                if re.fullmatch(r"\(?([a-h])\)", line.strip(), re.I):
                    panel_marks.append((x0, y0, line.strip()))
            if (
                len(lines) >= 2
                and block_width > block_height
                and y0 <= height * 0.55
                and x0 >= width * 0.12
            ):
                legend.extend(lines)
                placed.append((x0, y0, "legend", lines))

        def unique(values):
            return list(dict.fromkeys(value for value in values if value))

        panels = _group_panels(panel_marks, placed)
        return {
            "source": "publisher figure PDF text layer",
            # Kept: callers and committed records read these, and they are still what the
            # figure says along its edges. The per-panel detail is the structured form.
            "axes": unique(axes),
            "legend": unique(legend),
            "x_ticks": unique(x_ticks),
            "y_ticks": unique(y_ticks),
            "panels": panels or 1,
            "panel_detail": _panel_detail(
                panel_marks, placed, unique(x_ticks), unique(y_ticks)
            ),
            "panel_detection": (
                "panel markers in the page text" if panels > 1 else "single source-page asset"
            ),
            "text": unique(text_lines),
        }
    except (ImportError, OSError, RuntimeError, ValueError):
        return {}
