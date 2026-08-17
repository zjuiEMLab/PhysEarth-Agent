"""Record what each bundled figure shows, in the card that already describes it.

A figure is reproduced from its axes, its labels and its legend -- the legend says how
many curves are on it, the axes say what is plotted against what. That text is already in
the publisher's vector PDF, and `inspect_paper_figure` extracts it on demand. Extracting
it once into the card makes it available to anything that reads the card: the capability
check, the plan's coverage warnings, and a reader deciding which figure to reproduce.

Generic over the corpus. It reads whatever papers carry figure assets and writes back only
fields it actually extracted, so a paper with raster-only figures is left as it is.

    python scripts/extract_figure_metadata.py            # write
    python scripts/extract_figure_metadata.py --dry-run  # show what would change
"""

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from physearth import paths  # noqa: E402
from physearth.tools.figures import _extract_vector_figure_observations  # noqa: E402

# What a reader needs to reproduce a figure: which quantity is on each axis and over
# what range, what the curves are called, and -- when the figure has subplots -- all of
# that per panel rather than merged into one list.
FIELDS = ("x_axis", "y_axis", "legend", "panels", "panel_detail")


def _observations(paper_dir, figure):
    """Whatever the figure's own vector text yields. Never invented, never guessed."""
    source = figure.get("original_asset_path") or figure.get("asset_path") or ""
    path = paper_dir / source
    if not path.is_file() or path.suffix.lower() != ".pdf":
        return {}
    try:
        return _extract_vector_figure_observations(path.read_bytes()) or {}
    except Exception as exc:  # a malformed asset must not stop the corpus
        print("    ! %s: %s: %s" % (source, type(exc).__name__, exc))
        return {}


def update(card_path, dry_run=False):
    card = yaml.safe_load(card_path.read_text(encoding="utf-8")) or {}
    figures = card.get("figures") or []
    if not figures:
        return 0
    changed = 0
    for figure in figures:
        observed = _observations(card_path.parent, figure)
        for field in FIELDS:
            value = observed.get(field)
            # A single-panel figure carries no panel detail, and an empty axis label is
            # an honest answer for a schematic. Write only what was found.
            if field == "panels" and value in (None, 1):
                continue
            if field in ("x_axis", "y_axis") and not (value or {}).get("label"):
                continue
            if not value or figure.get(field) == value:
                continue
            print("    %s.%s <- %s" % (figure.get("id"), field, str(value)[:66]))
            if not dry_run:
                figure[field] = value
            changed += 1
    if changed and not dry_run:
        card_path.write_text(
            yaml.safe_dump(card, sort_keys=False, allow_unicode=True, width=100),
            encoding="utf-8",
        )
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    total = 0
    for card_path in sorted(paths.knowledge().glob("literature/*/card.yaml")):
        print(card_path.parent.name)
        total += update(card_path, dry_run=args.dry_run)
    print("\n%d field(s) %s" % (total, "would change" if args.dry_run else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
