"""Redraw a recorded run's figures at print resolution from the record alone.

The chart specification (title, axes, series and the result handles they name) and the
result arrays are both in the record, so the figure is drawn again by the same renderer
the agent used, physearth.plotting, with no model re-run and no new numbers. Only the
output resolution differs.

    python evaluation/render/rerender_run_figures.py RECORD.json OUTDIR [--dpi 380]
"""

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

from physearth import plotting  # noqa: E402


def redraw(record, outdir, dpi=380, stem=None):
    payloads = {item["handle"]: item for item in record.get("numeric_results") or []}
    original = plotting.results.get
    plotting.results.get = lambda handle, owner=None: payloads.get(handle)
    written = []
    try:
        for index, figure in enumerate(record.get("figures") or [], 1):
            spec = {
                "title": figure.get("title"),
                "subtitle": figure.get("subtitle"),
                "x_label": figure.get("x_label"),
                "y_label": figure.get("y_label"),
                "kind": figure.get("kind") or "line",
                "series": [
                    {"handle": item["handle"], "x": item["x"], "y": item["y"],
                     "label": item.get("label")}
                    for item in figure.get("series") or []
                ],
            }
            series, problems = plotting.resolve(spec)
            if problems or not series:
                print(f"figure {index}: not redrawn: {'; '.join(problems) or 'no series'}")
                continue
            with tempfile.TemporaryDirectory() as scratch, matplotlib.rc_context(
                {"savefig.dpi": dpi}
            ):
                drawn = plotting.render(spec, series, temporary_dir=scratch)
                target = Path(outdir) / f"{stem or record.get('task')}_fig{index}.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(drawn["image_path"], target)
            written.append(target)
            print(target)
    finally:
        plotting.results.get = original
    return written


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("record")
    parser.add_argument("outdir")
    parser.add_argument("--dpi", type=int, default=380)
    parser.add_argument("--stem")
    args = parser.parse_args(argv)
    record = json.loads(Path(args.record).read_text(encoding="utf-8"), strict=False)
    redraw(record, args.outdir, args.dpi, args.stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
