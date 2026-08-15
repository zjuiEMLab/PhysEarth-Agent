"""Declarative chart rendering.

The agent never sends code here, only a specification naming result handles and the
columns to draw. The arrays travel from the result store straight to the renderer and
never enter the language model's context.
"""

import hashlib
import io
import math
from pathlib import Path
from urllib.parse import quote

from physearth import config, paths
from physearth.harness import results

FONT_DIR = paths.assets() / "fonts"
KINDS = ("line", "scatter", "line+markers")
MAX_SERIES = 8
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


def outline(spec):
    """Resolve a chart that has no data behind it yet.

    A sweep costs model evaluations, so it is worth being sure the chart is the one you
    wanted before paying for it. A preview names the axes, their units, the series and
    which of them will be drawn as a measurement, and deliberately carries no values.
    """
    problems = []
    raw = spec.get("series") or []
    if not isinstance(raw, list) or not raw:
        return [], ["series must be a non-empty list of {x, y} objects."]
    if len(raw) > MAX_SERIES:
        return [], ["at most %d series can be drawn in one chart." % MAX_SERIES]
    resolved = []
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            problems.append("series %d is not an object." % index)
            continue
        xname, yname = item.get("x"), item.get("y")
        if not xname or not yname:
            problems.append("series %d needs both an x and a y column name." % index)
            continue
        source = item.get("source") or "model_run"
        if source not in SOURCE_COLOURS:
            problems.append(
                "series %d: source must be one of %s." % (index, ", ".join(SOURCE_COLOURS))
            )
            continue
        units = {}
        payload = results.get(item.get("handle"), spec.get("owner")) if item.get("handle") else None
        if payload:
            units = payload.get("units") or {}
            source = _source(payload)
        resolved.append(
            {
                "handle": item.get("handle") or "",
                "label": str(item.get("label") or "%s vs %s" % (yname, xname))[:80],
                "x": [],
                "y": [],
                "x_name": xname,
                "y_name": yname,
                "source": source,
                "origin": "not run yet" if not payload else _origin(payload),
                "units": units,
            }
        )
    return resolved, problems


def resolve(spec, owner=None):
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
        payload = results.get(handle, owner) if handle else None
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


METRICS = ("bias", "rmse", "mae", "r")


def _unit(series, axis):
    return (series.get("units") or {}).get(series["%s_name" % axis], "")


def agreement(series, metrics):
    """Statistics between exactly two series, or the reason there are none.

    This is the comparison method note turned into code. The note says to establish that
    two results are comparable before differencing them; here the difference simply does
    not happen until they are. Refusing is the useful behaviour: a bias in kelvin between
    a brightness temperature and a backscatter is a number with no meaning, and printing
    it would be worse than printing nothing.
    """
    wanted = [m for m in (metrics or []) if m in METRICS] or list(METRICS)
    if len(series) != 2:
        return None, [
            "agreement statistics need exactly two series, got %d. Draw the model run and "
            "the thing you are comparing it with, and nothing else." % len(series)
        ]
    a, b = series
    problems = []
    if _unit(a, "y") != _unit(b, "y"):
        problems.append(
            "the two series are in different units, %r and %r, so their difference is not a "
            "physical quantity. Brightness temperature and backscatter cannot be differenced."
            % (_unit(a, "y") or "unstated", _unit(b, "y") or "unstated")
        )
    if a["x_name"] != b["x_name"]:
        problems.append(
            "the two series are indexed by different quantities, %s and %s, so there is no "
            "common axis to compare them on." % (a["x_name"], b["x_name"])
        )
    if problems:
        return None, problems

    low = max(min(a["x"]), min(b["x"]))
    high = min(max(a["x"]), max(b["x"]))
    if low > high:
        return None, [
            "the two series do not overlap: %s runs %g to %g and %s runs %g to %g."
            % (a["label"], min(a["x"]), max(a["x"]), b["label"], min(b["x"]), max(b["x"]))
        ]

    xs = [x for x in a["x"] if low <= x <= high]
    if len(xs) < 2:
        return None, [
            "only %d point of %s falls inside the range %s covers, which is too few to "
            "compare." % (len(xs), a["label"], b["label"])
        ]
    left = [a["y"][a["x"].index(x)] for x in xs]
    right = _interpolate(b["x"], b["y"], xs)
    pairs = [(p, q) for p, q in zip(left, right, strict=True) if q is not None]
    n = len(pairs)
    differences = [p - q for p, q in pairs]

    values = {"n_points": n, "overlap": [low, high], "unit": _unit(a, "y")}
    if "bias" in wanted:
        values["bias"] = round(sum(differences) / n, 4)
    if "mae" in wanted:
        values["mae"] = round(sum(abs(d) for d in differences) / n, 4)
    if "rmse" in wanted:
        values["rmse"] = round(math.sqrt(sum(d * d for d in differences) / n), 4)
    if "r" in wanted:
        values["r"] = _pearson([p for p, _ in pairs], [q for _, q in pairs])
    values["of"] = a["label"]
    values["against"] = b["label"]
    values["provenance"] = [a["source"], b["source"]]
    return values, []


def _interpolate(xs, ys, targets):
    pairs = sorted(zip(xs, ys, strict=True))
    px = [p[0] for p in pairs]
    py = [p[1] for p in pairs]
    out = []
    for target in targets:
        if target < px[0] or target > px[-1]:
            out.append(None)
            continue
        lo = max(i for i in range(len(px)) if px[i] <= target)
        hi = min(len(px) - 1, lo + 1)
        if hi == lo or abs(px[hi] - px[lo]) < 1e-15:
            out.append(py[lo])
            continue
        weight = (target - px[lo]) / (px[hi] - px[lo])
        out.append(py[lo] + weight * (py[hi] - py[lo]))
    return out


def _pearson(left, right):
    n = len(left)
    if n < 2:
        return None
    mean_l = sum(left) / n
    mean_r = sum(right) / n
    cov = sum((a - mean_l) * (b - mean_r) for a, b in zip(left, right, strict=True))
    var_l = sum((a - mean_l) ** 2 for a in left)
    var_r = sum((b - mean_r) ** 2 for b in right)
    if var_l <= 0 or var_r <= 0:
        return None
    return round(cov / math.sqrt(var_l * var_r), 4)


def render(spec, series, preview=False, temporary_dir=None):
    """Draw a chart and return a small record pointing at a server-owned PNG file."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    families = _install_font()
    kind = spec.get("kind") if spec.get("kind") in KINDS else "line"
    with matplotlib.rc_context({"font.family": families + ["serif"] if families else ["serif"]}):
        return _draw(plt, spec, series, kind, preview, temporary_dir=temporary_dir)


def _draw(plt, spec, series, kind, preview=False, temporary_dir=None):
    publication = spec.get("quality_profile") == "publication"
    figure, axes = plt.subplots(
        figsize=(7.2, 4.7) if publication else (5.8, 3.65),
        dpi=170,
    )
    figure.patch.set_facecolor(PAPER)
    axes.set_facecolor(PAPER)

    seen = {}
    model_styles = ("-", "--", "-.", ":")
    model_keys = []
    categorical_singletons = bool(
        not preview
        and kind == "scatter"
        and len(series) > 1
        and all(len(item.get("x") or []) == 1 for item in series)
        and len({item["x"][0] for item in series}) == 1
    )
    category_labels = []
    for index, item in enumerate(series):
        y_name = str(item.get("y_name") or "").lower()
        if y_name.endswith(("_v", "_vv", "_vv_db")):
            colour = "#2b7bba"
        elif y_name.endswith(("_h", "_hh", "_hh_db")):
            colour = "#e56b2f"
        elif y_name.endswith(("_hv", "_hv_db")):
            colour = "#4f7a48"
        else:
            colour = SOURCE_COLOURS.get(item["source"])
            if seen.get(item["source"]):
                colour = EXTRA_COLOURS[index % len(EXTRA_COLOURS)]
        seen[item["source"]] = True
        model_key = str(item.get("label") or "").rsplit(" · ", 1)[0]
        if model_key not in model_keys:
            model_keys.append(model_key)
        style = model_styles[model_keys.index(model_key) % len(model_styles)]
        if preview:
            # An empty artist still earns its legend entry, which is the whole point: the
            # preview shows what will be drawn and in which style, and no values.
            axes.plot([], [], style, color=colour, linewidth=1.8, label=item["label"])
            continue
        if kind == "scatter" or (kind == "line+markers" and item["source"] == "measured"):
            plot_x = [index] if categorical_singletons else item["x"]
            if categorical_singletons:
                model_name = model_key.replace("SMRT ", "").replace(" coefficients", "")
                quantity = str(item.get("y_name") or "").replace("_per_m", "")
                category_labels.append("%s\n%s" % (model_name, quantity))
            axes.plot(
                plot_x, item["y"], "*" if item["source"] == "measured" else "o",
                color=colour, markersize=5.0, label=item["label"]
            )
            if kind == "line+markers":
                axes.plot(plot_x, item["y"], style, color=colour, linewidth=1.4, alpha=0.55)
        else:
            axes.plot(
                item["x"], item["y"], style, color=colour, linewidth=1.8,
                marker="o" if kind == "line+markers" else None,
                markersize=2.8, label=item["label"],
            )

    if preview:
        axes.text(
            0.5,
            0.5,
            "preview\nno data yet",
            transform=axes.transAxes,
            ha="center",
            va="center",
            fontsize=11,
            color=INK_MUTE,
            alpha=0.65,
        )

    first = series[0]
    axes.set_xlabel(spec.get("x_label") or _label(first, "x"), fontsize=8.5, color=INK_SOFT)
    axes.set_ylabel(spec.get("y_label") or _label(first, "y"), fontsize=8.5, color=INK_SOFT)
    if spec.get("title"):
        axes.set_title(
            str(spec["title"])[:110], fontsize=9.2, color=INK,
            pad=20 if spec.get("subtitle") else 8,
        )
        if spec.get("subtitle"):
            axes.text(
                0.5, 1.015, str(spec["subtitle"])[:140], transform=axes.transAxes,
                ha="center", va="bottom", fontsize=6.8, color=INK_MUTE,
            )
    axes.grid(True, color=LINE, linewidth=0.7, alpha=0.9)
    axes.set_axisbelow(True)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axes.spines[side].set_color(LINE)
    axes.tick_params(colors=INK_MUTE, labelsize=7.5, length=3)
    if categorical_singletons:
        axes.set_xticks(list(range(len(category_labels))))
        axes.set_xticklabels(category_labels, rotation=20, ha="right", fontsize=6.5)
        axes.margins(x=0.08)
    if preview:
        axes.set_xticks([])
        axes.set_yticks([])
    if (len(series) > 1 and not categorical_singletons) or preview:
        legend_options = {
            "fontsize": 7.0,
            "frameon": True,
            "framealpha": 0.9,
            "edgecolor": LINE,
            "facecolor": PAPER,
            "ncol": 2 if len(series) > 4 else 1,
        }
        if publication and len(series) > 3:
            legend_options.update(loc="upper center", bbox_to_anchor=(0.5, -0.19))
        else:
            legend_options["loc"] = "best"
        legend = axes.legend(**legend_options)
        for text in legend.get_texts():
            text.set_color(INK_SOFT)
    figure.tight_layout(pad=0.8, rect=(0, 0.12, 1, 1) if publication and len(series) > 3 else None)

    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", facecolor=PAPER, bbox_inches="tight", pad_inches=0.08)
    plt.close(figure)
    payload = buffer.getvalue()
    digest = hashlib.sha256(payload).hexdigest()[:24]
    figure_dir = Path(temporary_dir) if temporary_dir else config.state_dir().resolve() / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    image_path = figure_dir / ("%s.png" % digest)
    if not image_path.exists():
        image_path.write_bytes(payload)
    # Gradio's file route keeps the large PNG out of gr.State and out of every dynamic
    # HTML update.  Inlining 40-60 KB data URIs made the tab counter update while the
    # browser silently retained an empty image node in the full three-panel application.
    image_url = "/gradio_api/file=%s" % quote(str(image_path), safe="/")

    sources = sorted({item["source"] for item in series})
    return {
        "image_path": str(image_path),
        "image_url": image_url,
        "title": spec.get("title") or first["label"],
        "subtitle": spec.get("subtitle") or "",
        "x_label": spec.get("x_label") or _label(first, "x"),
        "y_label": spec.get("y_label") or _label(first, "y"),
        "kind": "preview" if preview else kind,
        "preview": preview,
        "provenance": sources,
        "series": [
            {
                "label": item["label"],
                "source": item["source"],
                "origin": item["origin"],
                "n_points": len(item["x"]),
                "handle": item["handle"],
                "x": item["x_name"],
                "y": item["y_name"],
            }
            for item in series
        ],
    }


def review_quality(spec, series, figure):
    """Review scientific and visual legibility from the exact plotted arrays and PNG."""
    issues = []
    warnings = []
    redraw_reasons = []
    kind = spec.get("kind", "line")
    for item in series:
        xs = list(item.get("x") or [])
        ys = list(item.get("y") or [])
        label = item.get("label") or item.get("y_name") or "series"
        if len(xs) != len(ys) or not xs:
            issues.append("%s has missing or misaligned x/y values" % label)
            continue
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in xs + ys):
            issues.append("%s contains non-finite values" % label)
        if kind in ("line", "line+markers") and len(set(xs)) < min(6, len(xs)):
            issues.append("%s has too few distinct x values for a scientific trend" % label)
        if kind in ("line", "line+markers") and len(xs) < 6:
            issues.append("%s has only %d points; at least 6 are required for a trend plot" % (label, len(xs)))
        if len(xs) > 1 and not all(xs[index] <= xs[index + 1] for index in range(len(xs) - 1)):
            warnings.append("%s x values are not monotonic" % label)
        if len(set(ys)) == 1:
            warnings.append("%s is constant; verify this is physically expected" % label)
        if kind in ("line", "line+markers") and len(ys) >= 6:
            deltas = [abs(ys[index + 1] - ys[index]) for index in range(len(ys) - 1)]
            nonzero = sorted(value for value in deltas if value > 0)
            if nonzero:
                median_delta = nonzero[len(nonzero) // 2]
                y_span = max(ys) - min(ys)
                largest = max(deltas)
                jump_index = deltas.index(largest)
                if (
                    y_span > 0
                    and largest > 4.0 * median_delta
                    and largest > 0.25 * y_span
                ):
                    message = (
                        "%s has an abrupt adjacent jump between x=%s and x=%s"
                        % (label, xs[jump_index], xs[jump_index + 1])
                    )
                    if jump_index in (0, len(deltas) - 1):
                        warnings.append(
                            message + "; endpoint behaviour should be noted in interpretation"
                        )
                    else:
                        issues.append(
                            message + "; inspect numerical stability or refine the sweep before interpretation"
                        )
    if len(series) > 4:
        redraw_reasons.append("crowded legend with %d series" % len(series))
    if any(len(str(item.get("label") or "")) > 48 for item in series):
        redraw_reasons.append("long series labels need a wider publication layout")
    image_path = Path(figure.get("image_path") or "")
    if not image_path.is_file() or image_path.stat().st_size < 2000:
        issues.append("rendered PNG is missing or unexpectedly small")
    return {
        "reviewed": True,
        "passed": not issues,
        "issues": issues,
        "warnings": warnings,
        "redraw_reasons": redraw_reasons,
        "n_series": len(series),
        "point_counts": [len(item.get("x") or []) for item in series],
    }


def _label(series, axis):
    name = series["%s_name" % axis]
    unit = (series.get("units") or {}).get(name)
    return "%s (%s)" % (name, unit) if unit else name
