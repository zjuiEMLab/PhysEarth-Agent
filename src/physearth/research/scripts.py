"""Scripts that reproduce a finished study's figures, written from what was recorded.

Nothing here asks the model. A figure already names the runs behind each curve, and each
run was persisted with the exact specification it ran with, so a script can be written
out mechanically: the specifications as literals, the arrays as data files beside it, and
the plotting as a few lines of matplotlib. A script written that way says what was run.
A script the model wrote would only say what the model remembers running.
"""

import json
import time
import zipfile
from pathlib import Path

from physearth import artifacts
from physearth.harness import results

_SCRIPT = '''#!/usr/bin/env python3
"""Reproduce {title}

Written by PhysEarth-Agent on {date}, from session {session_id}, research plan v{version:03d}.
Each curve is one run of a registered model, with the specification it actually ran with.

    python {stem}.py              # re-run every model, then draw the figure
    python {stem}.py --recorded   # draw the arrays recorded in the session (data/)

Re-running needs the PhysEarth-Agent package importable (pip install -e . in the
repository) and each model's own dependency installed. --recorded needs only matplotlib.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

FIGURE = {figure}

SERIES = {series}

RUNS = {runs}


def run_model(model, spec):
    """One run through the model's registered adapter, as the agent ran it."""
    try:
        from physearth.registry import loader
    except ImportError:
        sys.exit(
            "physearth is not importable. Install the PhysEarth-Agent repository "
            "(pip install -e .) or draw the recorded arrays with --recorded."
        )
    entry = loader.get(model)
    if entry is None:
        sys.exit("Model %r is not registered in this installation." % model)
    if not entry.runnable:
        sys.exit(entry.unavailable_reason)
    return entry.run(dict(spec))


def recorded(handle):
    return json.loads((HERE / "data" / ("%s.json" % handle)).read_text(encoding="utf-8"))


def column(result, name):
    """A named axis or output from a run result."""
    axis = result.get("axis") or {{}}
    if axis.get("name") == name:
        return list(axis.get("values") or [])
    series = result.get("series") or {{}}
    if name in series:
        return list(series[name])
    return [point.get(name) for point in result.get("points") or []]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--recorded", action="store_true", help="draw the recorded arrays")
    parser.add_argument("--out", default=str(HERE / "{stem}.png"), help="output image path")
    parser.add_argument("--show", action="store_true", help="open a window as well")
    args = parser.parse_args()

    import matplotlib

    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for item in SERIES:
        run = RUNS[item["handle"]]
        if args.recorded:
            result = recorded(item["handle"])
        else:
            print("running %s (%s) ..." % (item["label"], run["model"]), flush=True)
            result = run_model(run["model"], run["spec"])
        x, y = column(result, item["x"]), column(result, item["y"])
        if FIGURE["kind"] == "scatter":
            ax.scatter(x, y, s=14, label=item["label"])
        else:
            ax.plot(x, y, marker="o" if len(x) < 12 else None, ms=3, lw=1.6, label=item["label"])
    ax.set_xlabel(FIGURE["x_label"])
    ax.set_ylabel(FIGURE["y_label"])
    ax.set_title(FIGURE["title"], fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(args.out, dpi=200)
    print("wrote %s" % args.out)
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
'''

_README = """# Figure scripts

Written by PhysEarth-Agent on {date} for:

> {question}

Session `{session_id}`, research plan v{version:03d}.

| Script | Figure | Runs |
|---|---|---|
{rows}

Each script holds the exact specification of every run behind its figure, as the run
record stored it, and `data/` holds the arrays those runs returned.

```bash
python {first}.py --recorded   # redraw from the recorded arrays (needs matplotlib)
python {first}.py              # re-run the models, then draw (needs PhysEarth-Agent)
```

Re-running goes through each model's registered adapter, which is how the agent ran it.
A re-run that does not match the recorded arrays is worth reporting: the specification
is the same, so the difference is in the installed model or its dependencies.
"""


def _run_record(session, research_id, handle):
    """A run as persisted at the time it ran, or as the in-memory store still holds it."""
    path = (
        artifacts.project_dir(session.get("id") or "shared")
        / "research" / str(research_id) / "runs" / ("%s.json" % handle)
    )
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            pass
    for owner in (session.get("id"), None):
        try:
            record = results.get(handle, owner)
        except Exception:
            record = None
        if record:
            return record
    return None


def _figures(session):
    return [
        figure for figure in session.get("figures") or []
        if not figure.get("preview") and not figure.get("research_preview")
        and any(s.get("handle") for s in figure.get("series") or [])
    ]


def has_figures(session):
    return bool(_figures(session or {}))


def script_bundle(session, out_dir=None):
    """Write one script per real figure, the run data and a README, zipped.

    Returns {"path", "files", "figures", "missing"}; `missing` lists run handles whose
    records could not be found, and whose curves the scripts therefore leave out.
    """
    session = session or {}
    project = session.get("research") or {}
    research_id = project.get("research_id") or session.get("id") or "shared"
    version = int(project.get("plan_version") or 1)
    figures = _figures(session)
    if not figures:
        return {"path": None, "files": [], "figures": 0, "missing": []}

    root = Path(out_dir) if out_dir else artifacts.project_dir(session.get("id") or "shared") / "exports"
    bundle = root / ("figure-scripts-v%03d" % version)
    (bundle / "data").mkdir(parents=True, exist_ok=True)
    date = time.strftime("%Y-%m-%d %H:%M")
    written, missing, rows = [], [], []
    for position, figure in enumerate(figures, 1):
        number = int(figure.get("figure_number") or position)
        stem = "reproduce_figure_%02d" % number
        series, runs = [], {}
        for item in figure.get("series") or []:
            handle = item.get("handle")
            record = _run_record(session, research_id, handle) if handle else None
            if not record or not record.get("spec"):
                if handle:
                    missing.append(handle)
                continue
            runs[handle] = {
                "model": record.get("model"),
                "version": record.get("version"),
                "spec": record.get("spec"),
            }
            series.append({
                "label": item.get("label") or handle,
                "handle": handle,
                "x": item.get("x"),
                "y": item.get("y"),
            })
            data = {key: record.get(key) for key in ("model", "version", "spec", "axis", "series", "units")}
            (bundle / "data" / ("%s.json" % handle)).write_text(
                json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
            )
        if not series:
            continue
        spec = {
            "title": str(figure.get("title") or "Figure %d" % number),
            "x_label": str(figure.get("x_label") or series[0]["x"]),
            "y_label": str(figure.get("y_label") or series[0]["y"]),
            "kind": str(figure.get("kind") or "line"),
        }
        script = _SCRIPT.format(
            title=spec["title"].replace('"""', "'''"),
            date=date,
            session_id=session.get("id") or "unknown",
            version=version,
            stem=stem,
            figure=json.dumps(spec, ensure_ascii=False, indent=4),
            series=json.dumps(series, ensure_ascii=False, indent=4),
            runs=json.dumps(runs, ensure_ascii=False, indent=4, default=str),
        )
        path = bundle / ("%s.py" % stem)
        path.write_text(script, encoding="utf-8")
        written.append(path)
        rows.append("| `%s.py` | %s | %d |" % (stem, spec["title"].replace("|", "/"), len(runs)))

    if not written:
        return {"path": None, "files": [], "figures": 0, "missing": missing}
    (bundle / "README.md").write_text(
        _README.format(
            date=date,
            question=str(project.get("question") or (project.get("plan") or {}).get("question") or "").replace("\n", " "),
            session_id=session.get("id") or "unknown",
            version=version,
            rows="\n".join(rows),
            first=written[0].stem,
        ),
        encoding="utf-8",
    )
    archive = root / ("figure-scripts-v%03d.zip" % version)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                handle.write(path, path.relative_to(root))
    return {
        "path": str(archive),
        "files": [str(path) for path in written],
        "figures": len(written),
        "missing": sorted(set(missing)),
    }
