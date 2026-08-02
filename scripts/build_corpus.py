"""Build the bundled literature corpus from Copernicus JATS XML.

Run from the repository root:  python scripts/build_corpus.py
"""

import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "knowledge" / "literature"
SECTION_SPLIT_CHARS = 12000

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

SKIP_TAGS = {"fig", "table-wrap", "graphic", "media", "supplementary-material", "label"}


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


def clean(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


_REF_LABELS = {}


def load_ref_labels(root):
    _REF_LABELS.clear()
    for ref in root.findall(".//ref-list/ref"):
        label = ref.findtext("label") or ""
        label = re.sub(r"\s*\(\s*", ", ", label.strip()).rstrip(")")
        if ref.get("id") and label:
            _REF_LABELS[ref.get("id")] = label


def render_xref(node):
    rids = (node.get("rid") or "").split()
    if node.get("ref-type") == "bibr":
        labels = [_REF_LABELS[r] for r in rids if r in _REF_LABELS]
        return "(%s)" % "; ".join(labels) if labels else ""
    numbers = [m.group(0) for m in (re.search(r"\d+$", r) for r in rids) if m]
    return ", ".join(numbers)


def inline(node):
    parts = []
    if node.tag == "tex-math":
        return "$%s$" % (node.text or "").strip()
    if node.tag == "xref":
        return render_xref(node)
    if node.tag in SKIP_TAGS:
        return ""
    if node.text:
        parts.append(node.text)
    for child in node:
        parts.append(inline(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def render_block(node, depth):
    out = []
    for child in node:
        tag = child.tag
        if tag in SKIP_TAGS:
            continue
        if tag == "title":
            continue
        if tag == "sec":
            title = child.find("title")
            if title is not None:
                out.append("%s %s" % ("#" * min(depth + 1, 6), clean(inline(title))))
            out.append(render_block(child, depth + 1))
        elif tag == "p":
            out.append(clean(inline(child)))
        elif tag == "disp-formula":
            math = child.find(".//tex-math")
            if math is not None and math.text:
                out.append("$$%s$$" % math.text.strip())
        elif tag == "list":
            for item in child.findall("list-item"):
                out.append("- %s" % clean(inline(item)))
        else:
            text = clean(inline(child))
            if text:
                out.append(text)
    return "\n\n".join(p for p in out if p)


def text_of(node):
    return clean(inline(node)) if node is not None else ""


def front_matter(root, entry):
    meta = root.find("front/article-meta")
    authors = []
    for contrib in meta.findall("contrib-group/contrib"):
        given = text_of(contrib.find("name/given-names"))
        surname = text_of(contrib.find("name/surname"))
        name = " ".join(x for x in (given, surname) if x)
        if name:
            authors.append(name)
    permissions = text_of(meta.find("permissions"))
    license_url = ""
    match = re.search(r"https://creativecommons\.org/licenses/by/[\d.]+/", permissions)
    if match:
        license_url = match.group(0)
    license_id = "CC-BY-4.0" if "/by/4.0" in license_url else "CC-BY-3.0"
    return {
        "title": text_of(meta.find("title-group/article-title")),
        "authors": authors,
        "journal": JOURNAL_NAMES[entry["journal"]],
        "volume": text_of(meta.find("volume")),
        "pages": "%s-%s" % (text_of(meta.find("fpage")), text_of(meta.find("lpage"))),
        "year": entry["year"],
        "doi": text_of(meta.find("article-id[@pub-id-type='doi']")),
        "license": license_id,
        "license_url": license_url,
        "abstract": text_of(meta.find("abstract")),
    }


def build_sections(root):
    sections = []
    for sec in root.findall("body/sec"):
        title = text_of(sec.find("title")) or "Section"
        body = render_block(sec, 1)
        subs = sec.findall("sec")
        if len(body) > SECTION_SPLIT_CHARS and subs:
            lead = render_block_without_subs(sec)
            if lead:
                sections.append((title, lead))
            for sub in subs:
                sub_title = text_of(sub.find("title")) or "Subsection"
                sections.append(("%s - %s" % (title, sub_title), render_block(sub, 1)))
        else:
            sections.append((title, body))
    return sections


def render_block_without_subs(sec):
    out = []
    for child in sec:
        if child.tag in ("sec", "title") or child.tag in SKIP_TAGS:
            continue
        if child.tag == "p":
            out.append(clean(inline(child)))
    return "\n\n".join(p for p in out if p)


def slugify(text):
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:48] or "section"


def flatten(value):
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, list):
        return [flatten(v) for v in value]
    return value


def write_card(path, card):
    order = (
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
    document = {}
    for key in order:
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
    path.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )


def build(entry):
    url = xml_url(entry)
    root = ET.fromstring(fetch(url))
    load_ref_labels(root)
    meta = front_matter(root, entry)
    target = OUT / entry["slug"]
    (target / "sections").mkdir(parents=True, exist_ok=True)
    for stale in (target / "sections").glob("*.md"):
        stale.unlink()

    pieces = [("Abstract", meta.pop("abstract"))]
    pieces.extend(build_sections(root))

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
        name = "%s_%s.md" % (section_id, slugify(title))
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
