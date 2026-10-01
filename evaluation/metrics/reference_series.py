"""B3 for any task whose fixture names an upstream oracle: curve error against a reference
series computed by calling the authors' package directly, never through an adapter.

The fixture describes the reference -- the package, its inputs, the swept axis, which run
and output each curve comes from -- and `build_oracle` computes it. Nothing here knows
which model a task is about; a curve is matched to the agent's runs by the model name, the
output and the spec values the fixture lists under `match`.
"""

import json
from pathlib import Path

import yaml

from . import oracles
from .figure3 import _errors_on_overlap, _interpolate

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent


def load_fixture(path):
    path = Path(path)
    if not path.is_absolute():
        path = REPO / path
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_oracle(fixture):
    block = fixture["oracle"]
    result = oracles.UPSTREAM[block["package"]](block)
    result["schema_version"] = "reference-series-oracle-v1"
    result["task"] = fixture["task"]
    result["reference"] = fixture["source"]
    return result


def oracle_path(fixture):
    return REPO / fixture["oracle"]["path"]


def load_oracle(fixture):
    path = oracle_path(fixture)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _same(left, right):
    if isinstance(right, (int, float)) and not isinstance(right, bool):
        return isinstance(left, (int, float)) and abs(float(left) - float(right)) <= 1e-9 * max(
            1.0, abs(float(right))
        )
    return str(left).lower() == str(right).lower()


def _match(available, curve, axis_name):
    for item in available:
        if str(item.get("model") or "") != curve["model"]:
            continue
        if str((item.get("axis") or {}).get("name") or "") != axis_name:
            continue
        if curve["output"] not in (item.get("series") or {}):
            continue
        axis = (item.get("axis") or {}).get("values") or []
        if len(axis) != len(item["series"][curve["output"]]):
            continue
        spec = item.get("spec") or {}
        if all(_same(spec.get(key), value) for key, value in (curve.get("match") or {}).items()):
            return item
    return None


def numeric_error(record, fixture, oracle):
    """Per curve: normalised RMSE and maximum error on the part of the oracle axis the
    agent's own run covers, normalised by the reference curve's range. A flat reference
    curve has no range of its own, so it is normalised by the widest curve on the figure,
    the scale a reader sees it at. Points outside the run's axis are counted."""
    axis = [float(value) for value in oracle["axis"]["values"]]
    available = record.get("numeric_results") or []
    figure_span = max(max(values) - min(values) for values in oracle["series"].values()) or 1.0
    rows = []
    for curve in fixture["curves"]:
        wanted = [float(value) for value in oracle["series"][curve["id"]]]
        item = _match(available, curve, oracle["axis"]["name"])
        if item is None:
            rows.append({"curve": curve["id"], "present": False})
            continue
        got = _interpolate(
            [float(value) for value in item["axis"]["values"]],
            [float(value) for value in item["series"][curve["output"]]],
            axis,
        )
        kept = [(a, b) for a, b in zip(got, wanted, strict=True) if a is not None]
        if kept and max(wanted) == min(wanted):
            errors = [abs(a - b) for a, b in kept]
            nrmse = (sum(e * e for e in errors) / len(errors)) ** 0.5 / figure_span
            nmax = max(errors) / figure_span
            compared = len(kept)
        else:
            nrmse, nmax, compared = _errors_on_overlap(got, wanted)
        rows.append(
            {
                "curve": curve["id"],
                "present": True,
                "normalized_rmse": nrmse,
                "normalized_max_absolute_error": nmax,
                "points_compared": compared,
                "points_in_reference": len(axis),
            }
        )
    published = []
    for point in fixture.get("published") or []:
        curve = next(item for item in fixture["curves"] if item["id"] == point["curve"])
        item = _match(available, curve, oracle["axis"]["name"])
        oracle_value = _interpolate(axis, oracle["series"][curve["id"]], [float(point["x"])])[0]
        agent_value = (
            _interpolate(
                [float(value) for value in item["axis"]["values"]],
                [float(value) for value in item["series"][curve["output"]]],
                [float(point["x"])],
            )[0]
            if item
            else None
        )
        published.append(
            {
                "curve": point["curve"],
                "x": point["x"],
                "published_value": point["value"],
                "published_resolution": point.get("resolution"),
                "source": point.get("source"),
                "oracle_value": oracle_value,
                "agent_value": agent_value,
                "agent_minus_published": (
                    None if agent_value is None else agent_value - float(point["value"])
                ),
                "oracle_minus_published": (
                    None if oracle_value is None else oracle_value - float(point["value"])
                ),
            }
        )
    return {
        "oracle_package": oracle.get("package"),
        "oracle_package_version": oracle.get("package_version"),
        "curves": rows,
        "published": published,
    }


def score(record, fixture, oracle):
    rendered = any(not figure.get("preview") for figure in record.get("figures") or [])
    if oracle is None:
        return {
            "passed": None,
            "complete": False,
            "status": "not_scoreable",
            "numeric": {"passed": None, "status": "not_scoreable", "curves": []},
            "plot": {"passed": rendered},
        }
    b3 = numeric_error(record, fixture, oracle)
    threshold = float((fixture.get("thresholds") or {}).get("normalized_rmse", 0.05))
    present = [row for row in b3["curves"] if row["present"]]
    complete = len(present) == len(b3["curves"]) and all(
        row["normalized_rmse"] is not None for row in present
    )
    within = complete and all(row["normalized_rmse"] <= threshold for row in present)
    status = "pass" if within and rendered else "fail" if present else "not_scoreable"
    return {
        "passed": True if status == "pass" else False if status == "fail" else None,
        "complete": True,
        "status": status,
        "numeric": {
            "passed": within if present else None,
            "status": "pass" if within else "fail" if present else "not_scoreable",
            "threshold_normalized_rmse": threshold,
            "curves": b3["curves"],
        },
        "numeric_b3": b3,
        "plot": {"passed": rendered},
    }


def render_reference(fixture, oracle, output_path):
    """The reference image the label-blinded figure judge compares against."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot = fixture.get("plot") or {}
    axis = oracle["axis"]["values"]
    figure, axes = plt.subplots(figsize=(10, 6))
    for curve in fixture["curves"]:
        axes.plot(axis, oracle["series"][curve["id"]], linewidth=2.0, label=curve["label"])
    for point in fixture.get("published") or []:
        axes.plot(
            [point["x"]], [point["value"]], marker="o", color="black", linestyle="none",
            label=point.get("label") or "published value",
        )
    axes.set_xlabel(plot.get("x_label") or oracle["axis"]["name"])
    axes.set_ylabel(plot.get("y_label") or "")
    axes.set_title(plot.get("title") or fixture["task"])
    axes.grid(alpha=0.25)
    axes.legend(fontsize=9)
    figure.tight_layout()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=220)
    plt.close(figure)
    return output_path
