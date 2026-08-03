"""Declarative chart rendering.

The agent never sends code here, only a specification naming result handles and the
columns to draw. The arrays travel from the result store straight to the renderer and
never enter the language model's context.
"""

import base64
import io
from pathlib import Path

from physearth import results

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
KINDS = ("line", "scatter", "line+markers")
MAX_SERIES = 4
MAX_POINTS = 400

PAPER = "#faf9f5"
INK = "#141413"
INK_SOFT = "#3d3d3a"
INK_MUTE = "#73726c"
LINE = "#d5d3c9"
SOURCE_COLOURS = {"model_run": "#6b5b8a", "measured": "#4f7a48"}
EXTRA_COLOURS = ["#d97757", "#3d3d3a", "#8a7a5b", "#4a6b8a"]

_FONT_READY = None


def _install_font():
    global _FONT_READY
    if _FONT_READY is not None:
        return _FONT_READY
    from matplotlib import font_manager

    families = []
    for name in ("anthropic-serif.ttf", "anthropic-mono.ttf"):
        path = FONT_DIR / name
        if not path.is_file():
            continue
        try:
            font_manager.fontManager.addfont(str(path))
            families.append(font_manager.FontProperties(fname=str(path)).get_name())
        except Exception:
            continue
    _FONT_READY = families
    return families


def _numeric(values):
    return [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]


def _columns(payload):
    """Every drawable column of a stored result, keyed by name."""
    if payload.get("source") == "measured":
        return dict(payload.get("columns") or {})
    columns = {}
    axis = payload.get("axis")
    if axis:
        columns[axis["name"]] = list(axis["values"])
    for name, values in (payload.get("series") or {}).items():
        columns[name] = list(values)
    for point in payload.get("points") or []:
        for key, value in point.items():
            if key not in columns and isinstance(value, (int, float)):
                columns.setdefault(key, []).append(value)
    return columns


def _source(payload):
    return "measured" if payload.get("source") == "measured" else "model_run"


def _origin(payload):
    if payload.get("source") == "measured":
        return payload.get("dataset", "reference data")
    return "%s@%s" % (payload.get("model", "?"), payload.get("version", "?"))


def resolve(spec):
    """Return (series, problems). Each series carries its own arrays and provenance."""
    problems = []
    raw = spec.get("series") or []
    if not isinstance(raw, list) or not raw:
        return [], ["series must be a non-empty list of {handle, x, y} objects."]
    if len(raw) > MAX_SERIES:
        return [], ["at most %d series can be drawn in one chart." % MAX_SERIES]

    resolved = []
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            problems.append("series %d is not an object." % index)
            continue
        handle = item.get("handle")
        payload = results.get(handle) if handle else None
        if payload is None:
            problems.append(
                "series %d: %r is not a live result handle. Use the handle returned by "
                "run_model or read_reference_dataset in this conversation." % (index, handle)
            )
            continue
        columns = _columns(payload)
        names = sorted(columns)
        xname, yname = item.get("x"), item.get("y")
        if xname not in columns:
            problems.append(
                "series %d: %r is not a column of %s. Available: %s."
                % (index, xname, handle, ", ".join(names))
            )
            continue
        if yname not in columns:
            problems.append(
                "series %d: %r is not a column of %s. Available: %s."
                % (index, yname, handle, ", ".join(names))
            )
            continue
        xs, ys = _numeric(columns[xname]), _numeric(columns[yname])
        if len(xs) != len(ys) or not xs:
            problems.append(
                "series %d: %s has %d numeric values and %s has %d, so they cannot be paired."
                % (index, xname, len(xs), yname, len(ys))
            )
            continue
        if len(xs) > MAX_POINTS:
            problems.append(
                "series %d has %d points, above the %d point limit for one chart."
                % (index, len(xs), MAX_POINTS)
            )
            continue
        pairs = sorted(zip(xs, ys, strict=False))
        resolved.append(
            {
                "handle": handle,
                "label": str(item.get("label") or "%s vs %s" % (yname, xname))[:80],
                "x": [p[0] for p in pairs],
                "y": [p[1] for p in pairs],
                "x_name": xname,
                "y_name": yname,
                "source": _source(payload),
                "origin": _origin(payload),
                "units": payload.get("units") or {},
            }
        )
    return resolved, problems


def render(spec, series):
    """Draw the chart and return a figure record with the PNG inlined as a data URI."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    families = _install_font()
    kind = spec.get("kind") if spec.get("kind") in KINDS else "line"
    with matplotlib.rc_context({"font.family": families + ["serif"] if families else ["serif"]}):
        return _draw(plt, spec, series, kind)


def _draw(plt, spec, series, kind):
    figure, axes = plt.subplots(figsize=(4.6, 2.9), dpi=170)
    figure.patch.set_facecolor(PAPER)
    axes.set_facecolor(PAPER)

    seen = {}
    for index, item in enumerate(series):
        colour = SOURCE_COLOURS.get(item["source"])
        if seen.get(item["source"]):
            colour = EXTRA_COLOURS[index % len(EXTRA_COLOURS)]
        seen[item["source"]] = True
        style = "--" if item["source"] == "model_run" and len(series) > 1 else "-"
        if kind == "scatter" or (kind == "line+markers" and item["source"] == "measured"):
            axes.plot(
                item["x"], item["y"], "o", color=colour, markersize=4.2, label=item["label"]
            )
            if kind == "line+markers":
                axes.plot(item["x"], item["y"], style, color=colour, linewidth=1.4, alpha=0.55)
        else:
            axes.plot(item["x"], item["y"], style, color=colour, linewidth=2.0, label=item["label"])

    first = series[0]
    axes.set_xlabel(spec.get("x_label") or _label(first, "x"), fontsize=8.5, color=INK_SOFT)
    axes.set_ylabel(spec.get("y_label") or _label(first, "y"), fontsize=8.5, color=INK_SOFT)
    if spec.get("title"):
        axes.set_title(str(spec["title"])[:90], fontsize=9.5, color=INK, pad=8)
    axes.grid(True, color=LINE, linewidth=0.7, alpha=0.9)
    axes.set_axisbelow(True)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axes.spines[side].set_color(LINE)
    axes.tick_params(colors=INK_MUTE, labelsize=7.5, length=3)
    if len(series) > 1:
        legend = axes.legend(fontsize=7.5, frameon=False, loc="best")
        for text in legend.get_texts():
            text.set_color(INK_SOFT)
    figure.tight_layout(pad=0.6)

    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", facecolor=PAPER, bbox_inches="tight", pad_inches=0.08)
    plt.close(figure)
    payload = base64.b64encode(buffer.getvalue()).decode("ascii")

    sources = sorted({item["source"] for item in series})
    return {
        "png": "data:image/png;base64,%s" % payload,
        "title": spec.get("title") or first["label"],
        "kind": kind,
        "provenance": sources,
        "series": [
            {
                "label": item["label"],
                "source": item["source"],
                "origin": item["origin"],
                "n_points": len(item["x"]),
                "handle": item["handle"],
            }
            for item in series
        ],
    }


def _label(series, axis):
    name = series["%s_name" % axis]
    unit = (series.get("units") or {}).get(name)
    return "%s (%s)" % (name, unit) if unit else name
