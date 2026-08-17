"""Build the bundled literature corpus from Copernicus JATS XML.

Run from the repository root:  python scripts/build_corpus.py
"""

import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from physearth.ingest import jats  # noqa: E402

OUT = ROOT / "knowledge" / "literature"


JOURNAL_NAMES = {
    "gmd": "Geoscientific Model Development",
    "tc": "The Cryosphere",
    "hess": "Hydrology and Earth System Sciences",
    "bg": "Biogeosciences",
}


def xml_url(entry):
    stem = "%s-%s-%s-%s" % (entry["journal"], entry["volume"], entry["fpage"], entry["year"])
    return "https://%s.copernicus.org/articles/%s/%s/%s/%s.xml" % (
        entry["journal"],
        entry["volume"],
        entry["fpage"],
        entry["year"],
        stem,
    )


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "physearth-corpus-builder"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def flatten(value):
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, list):
        return [flatten(v) for v in value]
    return value


TEMPLATE = ROOT / "knowledge" / "TEMPLATE" / "card.yaml"

# Fields the builder does not produce and must never destroy. `figures` is written by
# scripts/extract_figure_metadata.py from the publisher PDFs; rebuilding the corpus used
# to drop it silently, because the writer emitted the field order and nothing else.
CARD_PRESERVED = ("figures",)


def card_order():
    """The key order, read from knowledge/TEMPLATE/card.yaml.

    The shape of a card is data, not code: edit the template and every card the builder
    writes follows it. Falling back to the built-in order keeps the builder usable if the
    template is missing, but the template is the thing to change.
    """
    if TEMPLATE.is_file():
        document = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8")) or {}
        keys = [key for key in document if key not in CARD_PRESERVED]
        if keys:
            return tuple(keys)
    return CARD_ORDER_FALLBACK


def papers():
    """Every paper that declares where it came from, discovered rather than listed.

    This was a MANIFEST of eight dictionaries in this file: journal, volume, first page,
    year, and a paragraph of description, per paper. None of that is code, and keeping it
    here meant a new paper required editing a script. Each paper now carries its own
    source.yaml beside its sections, and the corpus is whatever declares itself.
    """
    found = []
    for source in sorted(OUT.glob("*/source.yaml")):
        entry = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
        entry["slug"] = source.parent.name
        found.append(entry)
    return found


CARD_ORDER_FALLBACK = (
    "slug",
    "title",
    "authors",
    "journal",
    "volume",
    "pages",
    "year",
    "doi",
    "url",
    "license",
    "license_url",
    "scenarios",
    "outputs",
    "modified",
    "description",
    "sections",
)

# Fields the builder does not produce and must never destroy. `figures` is written by
# scripts/extract_figure_metadata.py from the publisher PDFs; rebuilding the corpus used
# to drop it silently, because the writer emitted CARD_ORDER and nothing else. Anything
# listed here is carried through from the card already on disk, after the owned fields.
CARD_PRESERVED = ("figures",)


def write_card(path, card):
    existing = {}
    if path.is_file():
        existing = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    document = {}
    for key in card_order():
        if key not in card:
            continue
        value = card[key]
        if key == "sections":
            document[key] = [
                {
                    "id": str(s["id"]),
                    "title": flatten(s["title"]),
                    "file": s["file"],
                    "chars": s["chars"],
                }
                for s in value
            ]
        else:
            document[key] = flatten(value)
    for key in CARD_PRESERVED:
        if key in card:
            document[key] = card[key]
        elif key in existing:
            document[key] = existing[key]
    path.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )


def build(entry):
    parsed = jats.parse(fetch(xml_url(entry)).decode("utf-8"), JOURNAL_NAMES[entry["journal"]])
    meta = dict(parsed["front"], year=entry["year"])
    meta.pop("abstract", None)
    target = OUT / entry["slug"]
    (target / "sections").mkdir(parents=True, exist_ok=True)
    for stale in (target / "sections").glob("*.md"):
        stale.unlink()

    pieces = parsed["sections"]

    attribution = "%s (%s). %s. %s %s, %s. https://doi.org/%s. Licensed under %s." % (
        ", ".join(meta["authors"]),
        meta["year"],
        meta["title"],
        meta["journal"],
        meta["volume"],
        meta["pages"],
        meta["doi"],
        meta["license"],
    )

    sections = []
    for index, (title, body) in enumerate(pieces):
        if not body:
            continue
        section_id = "%02d" % index
        name = "%s_%s.md" % (section_id, jats.slugify(title))
        content = "# %s\n\n%s\n\n---\n\n%s\n" % (title, body, attribution)
        (target / "sections" / name).write_text(content, encoding="utf-8")
        sections.append(
            {"id": section_id, "title": title, "file": "sections/%s" % name, "chars": len(body)}
        )

    card = dict(meta)
    card.update(
        slug=entry["slug"],
        url="https://doi.org/%s" % meta["doi"],
        scenarios=entry["scenarios"],
        outputs=entry["outputs"],
        description=" ".join(entry["description"].split()),
        modified=(
            "Full text extracted from the publisher JATS XML and split into sections. "
            "Figures, tables and reference lists removed. Wording unchanged."
        ),
        sections=sections,
    )
    write_card(target / "card.yaml", card)
    return card


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for entry in papers():
        card = build(entry)
        chars = sum(s["chars"] for s in card["sections"])
        total += chars
        print(
            "%-30s %2d sections %7d chars  %s"
            % (card["slug"], len(card["sections"]), chars, card["license"])
        )
    print("total %d chars across %d papers" % (total, len(MANIFEST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
