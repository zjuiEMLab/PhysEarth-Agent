"""Asking OpenAlex what exists, and never reading it.

One call returns the title, the year, the venue, the licence, the open-access status, the
topic clustering and the abstract. That is enough to decide what to read next and not
enough to state a result from, which is exactly the boundary the abstract tier of the
citation contract draws. Full text comes from `fulltext`, by DOI, or not at all.
"""

import urllib.parse

from physearth.ingest import fulltext, http

WORKS = "https://api.openalex.org/works"
SELECT = ",".join(
    [
        "id",
        "doi",
        "title",
        "publication_year",
        "publication_date",
        "cited_by_count",
        "open_access",
        "primary_location",
        "best_oa_location",
        "topics",
        "authorships",
        "abstract_inverted_index",
    ]
)
MAX_LIMIT = 10
ABSTRACT_CHARS = 900
OPEN_LICENCES = ("cc-by", "cc-by-sa", "cc0", "public-domain", "cc-by-nc", "cc-by-nc-sa")


def _abstract(index):
    """OpenAlex stores abstracts as a word to positions map, for copyright reasons."""
    if not index:
        return ""
    positions = []
    for word, places in index.items():
        positions.extend((place, word) for place in places)
    positions.sort()
    text = " ".join(word for _, word in positions)
    return text[:ABSTRACT_CHARS] + ("..." if len(text) > ABSTRACT_CHARS else "")


def _authors(work):
    names = [
        (a.get("author") or {}).get("display_name")
        for a in (work.get("authorships") or [])[:3]
    ]
    names = [n for n in names if n]
    if not names:
        return ""
    more = len(work.get("authorships") or []) - len(names)
    return ", ".join(names) + (" and %d others" % more if more > 0 else "")


def _doi(work):
    raw = work.get("doi") or ""
    return raw.replace("https://doi.org/", "").strip().lower()


def _licence(work):
    for key in ("best_oa_location", "primary_location"):
        location = work.get(key) or {}
        if location.get("license"):
            return location["license"]
    return ""


def _full_text(doi, licence):
    """How reachable the full text is, without spending a request to find out.

    A Copernicus DOI resolves to a JATS document at an address derivable from the DOI
    alone, so that one is certain. Everything else needs a Europe PMC lookup that may
    come back empty, and saying so is the difference between an honest catalogue and one
    that promises what it cannot deliver.
    """
    if licence not in OPEN_LICENCES:
        return "unavailable"
    route = fulltext.route(doi)
    if route == "copernicus":
        return "available"
    return "lookup_required" if route else "unavailable"


def candidate(work, held_slugs=(), held_dois=()):
    doi = _doi(work)
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    licence = _licence(work)
    return {
        "doi": doi,
        "title": work.get("title") or "",
        "year": work.get("publication_year"),
        "authors": _authors(work),
        "venue": source.get("display_name") or "",
        "open_access": (work.get("open_access") or {}).get("oa_status") or "closed",
        "license": licence,
        "topics": [t.get("display_name") for t in (work.get("topics") or [])[:2]],
        "cited_by": work.get("cited_by_count"),
        "abstract": _abstract(work.get("abstract_inverted_index")),
        "full_text": _full_text(doi, licence),
        "already_held": doi in set(held_dois) or doi.replace("/", "-") in set(held_slugs),
    }


def search(query, from_year=None, limit=6, held_slugs=(), held_dois=()):
    """Return (candidates, elapsed_s). Raises http.Offline or http.Upstream, never lies."""
    limit = max(1, min(int(limit or 6), MAX_LIMIT))
    filters = ["open_access.is_oa:true"]
    if from_year:
        filters.append("from_publication_date:%d-01-01" % int(from_year))
    url = "%s?%s" % (
        WORKS,
        urllib.parse.urlencode(
            {
                "search": query,
                "filter": ",".join(filters),
                "per-page": limit,
                "select": SELECT,
                "sort": "relevance_score:desc",
                "mailto": "linjmshc@gmail.com",
            }
        ),
    )
    payload, elapsed = http.get_json(url)
    works = payload.get("results") or []
    return [candidate(w, held_slugs, held_dois) for w in works if _doi(w)], elapsed


def topics(candidates):
    """Group the candidates by their leading OpenAlex topic, biggest cluster first."""
    clusters = {}
    for item in candidates:
        name = (item["topics"] or ["Unclassified"])[0]
        clusters.setdefault(name, []).append(item["doi"])
    return sorted(
        ({"topic": name, "dois": dois} for name, dois in clusters.items()),
        key=lambda entry: -len(entry["dois"]),
    )
