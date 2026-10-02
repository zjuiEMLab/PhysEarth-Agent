"""Literature that arrived during one conversation.

A paper pulled in mid-session is readable and citable exactly like a bundled one, and is
never confused with one. The corpus lives in the session object, so it disappears when
the visitor clears the conversation and is invisible to every other visitor sharing the
process. The session keeps bounded text for fast access, while the project artifact store keeps
a manifest, extracted assets and source provenance under state_dir/projects/<session_id>.

The three tiers of the citation contract meet here:

  bundled   shipped with the repository, full text        [slug#id]
  session   fetched in this conversation, full text       [slug#id], marked session
  abstract  seen in a discovery result, metadata only     [abs:doi]

The first two carry the same marker on purpose. Both are full text the agent actually
opened, and a claim resting on either is a claim resting on a paragraph someone can go
and read. What separates them is provenance, which belongs in the run trace, not in a
different grade of evidence. The third is a different grade of evidence, and it gets a
different marker.
"""

import re

from physearth import artifacts
from physearth.corpus import knowledge
from physearth.harness import untrusted
from physearth.ingest import fulltext

MAX_PAPERS = 4
MAX_SECTIONS = 30
MAX_SECTION_CHARS = 16000
MAX_ABSTRACTS = 40


def slug_for(doi, taken=()):
    """A readable, marker-safe slug derived from the DOI and nothing else."""
    suffix = fulltext.normalise(doi).split("/", 1)[-1]
    slug = re.sub(r"[^a-z0-9]+", "-", suffix.lower()).strip("-")[:40] or "paper"
    if slug[0].isdigit():
        slug = "p-" + slug
    if slug not in taken:
        return slug
    for n in range(2, 40):
        candidate = "%s-%d" % (slug, n)
        if candidate not in taken:
            return candidate
    raise ValueError("no free slug for %s" % doi)


def corpus(session):
    return (session or {}).get("corpus") or {}


def abstracts(session):
    return (session or {}).get("abstracts") or {}


def held_dois(session):
    """Every DOI the session can already reach, bundled or ingested."""
    dois = {
        (card.get("doi") or "").lower()
        for card in (knowledge.card(s) for s in knowledge.slugs())
        if card
    }
    dois |= {card["doi"].lower() for card in corpus(session).values()}
    return {d for d in dois if d}


def remember_abstracts(session, candidates):
    """Record what a discovery call showed, so an [abs:doi] marker can resolve."""
    if session is None:
        return
    store = session.setdefault("abstracts", {})
    seen = session.setdefault("abstracts_seen", set())
    for item in candidates:
        seen.add(item["doi"])
        store[item["doi"]] = {
            "title": item["title"],
            "year": item["year"],
            "authors": item["authors"],
            "venue": item["venue"],
            "license": item["license"],
            "abstract": item["abstract"],
        }
    while len(store) > MAX_ABSTRACTS:
        # The cache of abstract text is bounded; the set of DOIs the session has seen is
        # not dropped with it, so a marker earned earlier keeps resolving.
        store.pop(next(iter(store)))


def add(session, record, persist=True):
    """Turn a fetched paper into a session card. Returns the card."""
    store = session.setdefault("corpus", {})
    if len(store) >= MAX_PAPERS:
        raise ValueError(
            "this conversation has already taken in %d papers, which is the limit. Clear "
            "the conversation to start again." % MAX_PAPERS
        )
    front = record["front"]
    slug = slug_for(record["doi"], taken=set(store) | set(knowledge.slugs(kind=None)))
    attribution = "%s (%s). %s. %s. https://doi.org/%s. Licensed under %s." % (
        ", ".join(front.get("authors") or []) or "unknown authors",
        front.get("year") or "n.d.",
        front.get("title") or slug,
        front.get("journal") or "",
        record["doi"],
        front.get("license") or "unknown licence",
    )
    sections = []
    for index, (title, body) in enumerate(record["sections"][:MAX_SECTIONS]):
        text = body[:MAX_SECTION_CHARS]
        sections.append(
            {
                "id": "%02d" % index,
                "title": " ".join(title.split()),
                "text": text,
                "chars": len(text),
                "truncated": len(body) > MAX_SECTION_CHARS,
            }
        )
    card = {
        "slug": slug,
        "kind": "paper",
        "source": "session",
        "title": " ".join((front.get("title") or slug).split()),
        "authors": front.get("authors") or [],
        "journal": front.get("journal") or "",
        "year": front.get("year"),
        "doi": record["doi"],
        "license": front.get("license") or "",
        "license_url": front.get("license_url") or "",
        "url": "https://doi.org/%s" % record["doi"],
        "fetched_from": record["source"],
        "fetch_url": record["url"],
        "attribution": attribution,
        "description": (front.get("abstract") or "")[:600],
        "scenarios": [],
        "outputs": [],
        "sections": sections,
        "figures": [dict(item) for item in (record.get("figures") or [])],
        "tables": [dict(item) for item in (record.get("tables") or [])],
    }
    if persist:
        artifact = artifacts.persist_paper(session.get("id") or "shared", card, record)
        # Keep binary PDF/JATS assets out of gr.State.  The session holds metadata and points to
        # the persistent artifact; the UI can request the asset by its manifest path.
        card["figures"] = artifact["manifest"].get("figures") or []
        card["artifact"] = {
            "paper_id": artifact["paper_id"],
            "root": artifact["root"],
            "manifest": artifact["root"] + "/manifest.json",
        }
    store[slug] = card
    return card


def card(session, slug):
    """A session paper first, then a bundled one. Session slugs never shadow bundled."""
    return corpus(session).get(slug) or knowledge.card(slug)


def source_of(session, slug):
    if slug in corpus(session):
        return "session"
    item = knowledge.card(slug)
    if item is None:
        return ""
    return "skill" if item.get("kind") == "skill" else "bundled"


def section_index(session, slug):
    item = corpus(session).get(slug)
    if item is None:
        return knowledge.section_index(slug)
    return [
        {"id": s["id"], "title": s["title"], "chars": s["chars"]} for s in item["sections"]
    ]


def read_section(session, slug, section_id):
    item = corpus(session).get(slug)
    if item is None:
        return knowledge.read_section(slug, section_id)
    for section in item["sections"]:
        if str(section["id"]) == str(section_id):
            return {
                "slug": slug,
                "section_id": section["id"],
                "title": section["title"],
                "text": section["text"],
                "doi": item["doi"],
                "license": item["license"],
                "citation_key": "%s#%s" % (slug, section["id"]),
                "truncated": section["truncated"],
            }
    return None


def catalogue(session, kind="paper"):
    """The bundled catalogue with the session's own papers appended, each labelled."""
    entries = []
    if kind in (None, "paper"):
        for entry in knowledge.catalogue():
            entries.append(dict(entry, source="bundled", kind="paper"))
    if kind in (None, "skill"):
        for item in knowledge.skills():
            entries.append(dict(item, source="bundled", kind="skill", license="Apache-2.0"))
    if kind in (None, "paper"):
        for item in corpus(session).values():
            entries.append(
                {
                    "slug": item["slug"],
                    "title": item["title"],
                    "year": item["year"],
                    "scenarios": [],
                    "outputs": [],
                    "description": item["description"],
                    "license": item["license"],
                    "source": "session",
                    "kind": "paper",
                    "doi": item["doi"],
                    "sections": len(item["sections"]),
                }
            )
    return entries


def search(session, query="", scenario="", kind="paper"):
    tokens = [t for t in (query or "").lower().split() if len(t) > 2]
    scenario = (scenario or "").strip().lower()
    scored = []
    for entry in catalogue(session, kind):
        if scenario and scenario not in [s.lower() for s in entry.get("scenarios") or ()]:
            continue
        haystack = " ".join(
            [
                entry["slug"],
                entry.get("title", ""),
                entry.get("description", ""),
                " ".join(entry.get("scenarios") or ()),
            ]
        ).lower()
        scored.append((sum(1 for token in tokens if token in haystack), entry))
    if not scored:
        return []
    if tokens and max(score for score, _ in scored) > 0:
        scored = [pair for pair in scored if pair[0] > 0]
    scored.sort(key=lambda pair: -pair[0])
    return [entry for _, entry in scored]


def wrapped_section(session, slug, section_id, budget_chars):
    """A section as a tool returns it: bounded, scanned, and labelled as external."""
    section = read_section(session, slug, section_id)
    if section is None:
        return None
    item = card(session, slug)
    text = section["text"]
    truncated = section.get("truncated", False)
    if len(text) > budget_chars:
        text = text[:budget_chars] + "\n\n[truncated at output budget]"
        truncated = True
    findings = untrusted.scan(text)
    origin = source_of(session, slug)
    kind = {
        "session": "open-access paper fetched in this conversation",
        "bundled": "published paper",
        "skill": "method note",
    }.get(origin, "published paper")
    return {
        "section": section,
        "text": untrusted.wrap(text, section["citation_key"], kind, item.get("license", "")),
        "findings": findings,
        "truncated": truncated,
        "source": origin,
    }
