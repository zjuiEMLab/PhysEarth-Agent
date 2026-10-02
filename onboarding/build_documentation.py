"""Build corpus entries from open-licensed software documentation.

A model's own documentation can be the source a reproduction cites: a documented benchmark
case is a stated result with stated inputs, just as a paper figure is. Each entry declares
where it comes from in <slug>/documentation.yaml -- repository, pinned commit, licence and
which files to take -- and this script fetches those files at that commit, writes them as
sections word for word, and writes the card. The entry is marked source_type:
documentation, so nothing presents it as a peer-reviewed paper.

Run from the repository root:  python onboarding/build_documentation.py
"""

import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "knowledge" / "literature"
CODE_SUFFIXES = {".py": "python"}


def fetch(repository, commit, path):
    owner_repo = repository.rstrip("/").split("github.com/")[1]
    url = "https://raw.githubusercontent.com/%s/%s/%s" % (owner_repo, commit, path)
    request = urllib.request.Request(url, headers={"User-Agent": "physearth-corpus-builder"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read().decode("utf-8")


def slugify(text):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in text)
    return "-".join(part for part in keep.split("-") if part)[:40]


def build(entry_dir):
    entry = yaml.safe_load((entry_dir / "documentation.yaml").read_text(encoding="utf-8"))
    sections_dir = entry_dir / "sections"
    sections_dir.mkdir(exist_ok=True)
    for stale in sections_dir.glob("*.md"):
        stale.unlink()
    attribution = "%s, %s at %s (%s), %s. Licensed under %s. %s" % (
        entry["title"],
        entry["repository"],
        entry["ref"],
        entry["commit"][:12],
        entry["year"],
        entry["license"],
        " ".join(entry["license_notice"].split()),
    )
    sections = []
    for index, item in enumerate(entry["sections"]):
        text = fetch(entry["repository"], entry["commit"], item["path"]).strip()
        language = CODE_SUFFIXES.get(Path(item["path"]).suffix)
        if language:
            text = "```%s\n%s\n```" % (language, text)
        # A section ends at its first "---" rule, before the attribution; a rule inside the
        # file becomes the equivalent "***" so the body is not cut short.
        text = text.replace("\n\n---\n\n", "\n\n***\n\n")
        section_id = "%02d" % index
        name = "%s_%s.md" % (section_id, slugify(item["title"]))
        content = "# %s\n\n%s\n\n---\n\nSource file `%s`. %s\n" % (
            item["title"], text, item["path"], attribution
        )
        (sections_dir / name).write_text(content, encoding="utf-8")
        sections.append(
            {"id": section_id, "title": item["title"], "file": "sections/%s" % name,
             "chars": len(text)}
        )
    if entry.get("license_file"):
        (entry_dir / "LICENSE").write_text(
            fetch(entry["repository"], entry["commit"], entry["license_file"]), encoding="utf-8"
        )
    card = {
        "slug": entry_dir.name,
        "title": entry["title"],
        "authors": entry["authors"],
        "source_type": "documentation",
        "version": entry["version"],
        "year": entry["year"],
        "url": "%s/tree/%s" % (entry["repository"].rstrip("/"), entry["ref"]),
        "commit": entry["commit"],
        "license": entry["license"],
        "license_url": entry["license_url"],
        "scenarios": entry["scenarios"],
        "outputs": entry["outputs"],
        "modified": (
            "Files taken from the repository at the pinned commit, one section per file. "
            "Code is wrapped in a code block; wording unchanged."
        ),
        "description": " ".join(entry["description"].split()),
        "sections": sections,
    }
    (entry_dir / "card.yaml").write_text(
        yaml.safe_dump(card, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8"
    )
    return card


def main():
    for path in sorted(OUT.glob("*/documentation.yaml")):
        card = build(path.parent)
        print("%s: %d sections" % (card["slug"], len(card["sections"])))


if __name__ == "__main__":
    main()
