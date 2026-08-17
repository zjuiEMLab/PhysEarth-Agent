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

MANIFEST = [
    {
        "slug": "smrt-v1",
        "journal": "gmd",
        "volume": 11,
        "fpage": 2763,
        "year": 2018,
        "scenarios": ["snow"],
        "outputs": ["tb", "sigma"],
        "description": (
            "Reference description of the SMRT model itself: how snowpacks are declared, which "
            "electromagnetic theories (IBA, DMRT, Rayleigh) and microstructure representations "
            "(exponential, sticky hard spheres, Gaussian random field, Teubner-Strey) are "
            "available, how they relate, and what each one assumes. Read this first when "
            "choosing or justifying SMRT run parameters."
        ),
    },
    {
        "slug": "arctic-snow-emission",
        "journal": "tc",
        "volume": 18,
        "fpage": 3971,
        "year": 2024,
        "scenarios": ["snow"],
        "outputs": ["tb"],
        "description": (
            "SMRT applied to Arctic snow emission in surface-sensitive atmospheric sounding "
            "channels at 89 to 243 GHz, evaluated against airborne radiometry with measured "
            "snow microstructure. Read this for a high-frequency validation case, for how "
            "measured microstructure is turned into model input, and for the limits of the "
            "model at frequencies far above the usual 19 to 37 GHz range."
        ),
    },
    {
        "slug": "memls3a",
        "journal": "gmd",
        "volume": 8,
        "fpage": 2611,
        "year": 2015,
        "scenarios": ["snow"],
        "outputs": ["tb", "sigma"],
        "description": (
            "MEMLS3&a: the Microwave Emission Model of Layered Snowpacks extended to also "
            "compute backscatter. Explains the improved Born approximation, correlation length "
            "as the microstructure parameter, and how an emission model is turned into an "
            "active one. Read this when comparing passive and active formulations of the same "
            "snowpack."
        ),
    },
    {
        "slug": "tvc-ku-swe",
        "journal": "tc",
        "volume": 18,
        "fpage": 3857,
        "year": 2024,
        "scenarios": ["snow", "soil"],
        "outputs": ["sigma"],
        "description": (
            "Trail Valley Creek 2018/19 experiment: retrieval of snow and soil properties for "
            "forward modelling of airborne Ku-band SAR to estimate snow water equivalent. Uses "
            "SMRT end to end with real field measurements at C, X and Ku band, and reports the "
            "retrieved soil roughness, soil permittivity and grain polydispersity values. Read "
            "this for a complete worked application and for realistic parameter values."
        ),
    },
    {
        "slug": "soil-dielectric-freezethaw",
        "journal": "hess",
        "volume": 25,
        "fpage": 1117,
        "year": 2021,
        "scenarios": ["soil"],
        "outputs": ["tb"],
        "description": (
            "Laboratory characterisation of the soil dielectric constant at L-band through "
            "freeze-thaw transitions, using coaxial and soil moisture probes. Read this for how "
            "soil permittivity depends on moisture, temperature and frozen state, which is the "
            "input every soil microwave forward model needs."
        ),
    },
    {
        "slug": "cmem-sampling-density",
        "journal": "hess",
        "volume": 24,
        "fpage": 1957,
        "year": 2020,
        "scenarios": ["soil", "vegetation"],
        "outputs": ["tb"],
        "description": (
            "Uses the Community Microwave Emission Modelling platform (CMEM) to simulate L-band "
            "brightness temperature over land and to ask how densely ground soil moisture and "
            "brightness temperature must be sampled to calibrate and validate satellite "
            "observations. Read this for the tau-omega emission chain and for scale and "
            "sampling arguments."
        ),
    },
    {
        "slug": "vod-sensitivity",
        "journal": "bg",
        "volume": 20,
        "fpage": 1027,
        "year": 2023,
        "scenarios": ["vegetation"],
        "outputs": ["tb"],
        "description": (
            "Sensitivity of multi-frequency passive microwave vegetation optical depth to "
            "vegetation properties. Read this when a question involves how canopy water "
            "content, biomass or structure changes the vegetation contribution, or when "
            "designing a sensitivity study over vegetation parameters."
        ),
    },
    {
        "slug": "backscatter-forward-operator",
        "journal": "hess",
        "volume": 25,
        "fpage": 6283,
        "year": 2021,
        "scenarios": ["soil", "vegetation"],
        "outputs": ["sigma"],
        "description": (
            "Calibration of a Water Cloud Model backscatter forward operator against Sentinel-1 "
            "over irrigated land. Read this for the active counterpart of tau-omega: how "
            "vegetation and soil contributions combine into total backscatter and how the "
            "model coefficients are fitted."
        ),
    },
]

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


# The card template: the order fields appear in, and the only fields this script owns.
# Edit this to change the shape of every card the builder writes.
CARD_ORDER = (
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
    for key in CARD_ORDER:
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
    for entry in MANIFEST:
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
