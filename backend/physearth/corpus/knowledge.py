
import yaml

from physearth import paths

KNOWLEDGE_DIR = paths.knowledge()
CORPUS_DIR = KNOWLEDGE_DIR / "literature"
SKILLS_DIR = KNOWLEDGE_DIR / "skills"

_CARDS = None


def _load():
    global _CARDS
    if _CARDS is not None:
        return _CARDS
    cards = {}
    for root, kind in ((CORPUS_DIR, "paper"), (SKILLS_DIR, "skill")):
        if not root.is_dir():
            continue
        for card_path in sorted(root.glob("*/card.yaml")):
            card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
            card["_dir"] = card_path.parent
            card.setdefault("kind", kind)
            cards[card["slug"]] = card
    _CARDS = cards
    return _CARDS


def slugs(kind="paper"):
    return [s for s, c in _load().items() if kind is None or c.get("kind") == kind]


def card(slug):
    return _load().get(slug)


def catalogue():
    entries = []
    for slug, item in _load().items():
        if item.get("kind") != "paper":
            continue
        entries.append(
            {
                "slug": slug,
                "title": item["title"],
                "year": item["year"],
                "scenarios": item.get("scenarios", []),
                "outputs": item.get("outputs", []),
                "description": item["description"],
                "license": item["license"],
            }
        )
    return entries


def catalogue_block():
    lines = []
    for entry in catalogue():
        lines.append(
            "- %s (%s, %s | scenarios: %s | outputs: %s)\n  %s"
            % (
                entry["slug"],
                entry["title"],
                entry["year"],
                ", ".join(entry["scenarios"]) or "-",
                ", ".join(entry["outputs"]) or "-",
                entry["description"],
            )
        )
    return "\n".join(lines)


def search(query="", scenario=""):
    tokens = [t for t in (query or "").lower().split() if len(t) > 2]
    scenario = (scenario or "").strip().lower()
    scored = []
    for entry in catalogue():
        if scenario and scenario not in [s.lower() for s in entry["scenarios"]]:
            continue
        haystack = " ".join(
            [entry["slug"], entry["title"], entry["description"], " ".join(entry["scenarios"])]
        ).lower()
        score = sum(1 for token in tokens if token in haystack)
        scored.append((score, entry))
    if not scored:
        return []
    best = max(score for score, _ in scored)
    if tokens and best > 0:
        scored = [pair for pair in scored if pair[0] > 0]
    scored.sort(key=lambda pair: -pair[0])
    return [entry for _, entry in scored]


def section_index(slug):
    item = card(slug)
    if not item:
        return None
    return [
        {"id": s["id"], "title": s["title"], "chars": s["chars"]} for s in item.get("sections", [])
    ]


def read_section(slug, section_id):
    item = card(slug)
    if not item:
        return None
    for section in item.get("sections", []):
        if str(section["id"]) == str(section_id):
            path = item["_dir"] / section["file"]
            return {
                "slug": slug,
                "section_id": section["id"],
                "title": section["title"],
                "text": path.read_text(encoding="utf-8"),
                "doi": item.get("doi", ""),
                "license": item.get("license", ""),
                "citation_key": "%s#%s" % (slug, section["id"]),
            }
    return None


def citation_keys():
    keys = set()
    for slug, item in _load().items():
        for section in item.get("sections", []):
            keys.add("%s#%s" % (slug, section["id"]))
    return keys


def skills():
    return [
        {"slug": slug, "title": item["title"], "description": " ".join(item["description"].split())}
        for slug, item in _load().items()
        if item.get("kind") == "skill"
    ]


def skills_block():
    return "\n".join(
        "- %s (%s)\n  %s" % (item["slug"], item["title"], item["description"])
        for item in skills()
    )
