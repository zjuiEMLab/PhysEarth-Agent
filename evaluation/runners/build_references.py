"""Compute every task's upstream reference series and render its reference image.

For each task whose fixture has `scorer: reference_series`, call the authors' package
directly (never an adapter), write the series to the fixture's oracle path, and render
the image the label-blinded figure judge compares against. No language model.

    python evaluation/runners/build_references.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

sys.path.insert(0, str(common.ROOT))
from metrics import reference_series  # noqa: E402


def main():
    built = 0
    for task in common.load_tasks("tier2"):
        if not task.get("reference_fixture"):
            continue
        fixture = reference_series.load_fixture(task["reference_fixture"])
        if fixture.get("scorer") != "reference_series":
            continue
        oracle = reference_series.build_oracle(fixture)
        path = reference_series.oracle_path(fixture)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(oracle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        image = reference_series.render_reference(
            fixture, oracle, common.REPO / fixture["visual_reference"]["image_path"]
        )
        print(f"{task['id']:<32} {oracle['package']} {oracle['package_version']}: "
              f"{len(oracle['series'])} curves x {len(oracle['axis']['values'])} points -> "
              f"{image.relative_to(common.REPO)}")
        built += 1
    print(f"{built} reference(s) built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
