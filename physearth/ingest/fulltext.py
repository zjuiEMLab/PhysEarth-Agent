"""Fetching the full text of one open-access paper, by DOI.

The agent passes a DOI and nothing else. Every URL below is constructed here from that
DOI, or from an identifier an allowed host returned, so there is no path by which a
string the model wrote becomes an address this process opens.

Two routes, because between them they cover the open-access literature of this field:

  copernicus   the EGU journals publish JATS at an address derivable from the DOI alone
  europepmc    a DOI lookup gives a PMC identifier, which gives JATS

A DOI on neither route is not a failure. It stays at abstract level, which the citation
contract already has a marker for.
"""

import re
import urllib.parse

from physearth.ingest import http, jats

COPERNICUS = re.compile(r"^10\.5194/([a-z]+)-(\d+)-(\d+)-(\d{4})$", re.I)
EUROPEPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPEPMC_FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest/%s/fullTextXML"
PMCID = re.compile(r"^PMC\d+$")

JOURNAL_NAMES = {
    "gmd": "Geoscientific Model Development",
    "tc": "The Cryosphere",
    "hess": "Hydrology and Earth System Sciences",
    "bg": "Biogeosciences",
    "acp": "Atmospheric Chemistry and Physics",
    "essd": "Earth System Science Data",
    "nhess": "Natural Hazards and Earth System Sciences",
    "os": "Ocean Science",
    "soil": "SOIL",
    "esurf": "Earth Surface Dynamics",
}

LICENCE_NAMES = {
    "cc-by": "CC-BY-4.0",
    "cc by": "CC-BY-4.0",
    "cc-by-sa": "CC-BY-SA-4.0",
    "cc-by-nc": "CC-BY-NC-4.0",
    "cc0": "CC0-1.0",
    "public-domain": "public domain",
}


def normalise(doi):
    doi = (doi or "").strip().lower()
    doi = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi)
    return doi.strip().strip("/")


def route(doi):
    """Which route a DOI can be fetched by, without fetching anything."""
    doi = normalise(doi)
    if not doi.startswith("10."):
        return ""
    match = COPERNICUS.match(doi)
    if match and match.group(1).lower() in JOURNAL_NAMES:
        return "copernicus"
    return "europepmc"


def copernicus_url(doi):
    match = COPERNICUS.match(normalise(doi))
    if not match:
        return "", ""
    journal, volume, fpage, year = match.groups()
    journal = journal.lower()
    stem = "%s-%s-%s-%s" % (journal, volume, fpage, year)
    url = "https://%s.copernicus.org/articles/%s/%s/%s/%s.xml" % (
        journal,
        volume,
        fpage,
        year,
        stem,
    )
    return url, JOURNAL_NAMES.get(journal, "")


def europepmc_record(doi):
    """Ask Europe PMC whether it holds this DOI, and under what identifier."""
    url = "%s?%s" % (
        EUROPEPMC_SEARCH,
        urllib.parse.urlencode(
            {
                "query": 'DOI:"%s"' % normalise(doi),
                "format": "json",
                "resultType": "core",
                "pageSize": 1,
            }
        ),
    )
    payload, _ = http.get_json(url)
    hits = ((payload.get("resultList") or {}).get("result")) or []
    return hits[0] if hits else None


def fetch(doi, licence_hint=""):
    """Return a record with the parsed sections, or raise.

    Raises http.Offline when the layer is closed, http.Upstream when an allowed host
    failed, and LookupError when the host answered and simply does not hold the paper.
    Those three are deliberately different exceptions: an outage must never be reported
    to the user as an absence.
    """
    doi = normalise(doi)
    if not doi.startswith("10."):
        raise ValueError("%r is not a DOI" % doi)

    chosen = route(doi)
    if chosen == "copernicus":
        url, journal = copernicus_url(doi)
        xml, elapsed = http.get_text(url)
        parsed = jats.parse(xml, journal)
        source, landing = "copernicus", url
    else:
        record = europepmc_record(doi)
        if not record:
            raise LookupError("Europe PMC has no record for %s" % doi)
        pmcid = record.get("pmcid") or ""
        if not PMCID.match(pmcid) or record.get("inEPMC") != "Y":
            raise LookupError(
                "Europe PMC knows %s but does not hold its full text openly" % doi
            )
        licence_hint = licence_hint or (record.get("license") or "")
        xml, elapsed = http.get_text(EUROPEPMC_FULLTEXT % pmcid)
        parsed = jats.parse(xml, record.get("journalTitle") or "")
        source, landing = "europepmc", EUROPEPMC_FULLTEXT % pmcid

    if not parsed["sections"]:
        raise LookupError("%s was fetched but no readable section came out of it" % doi)

    front = parsed["front"]
    # The XML's own permissions block is authoritative when it carries a licence URL.
    # Several publishers omit it, and then the licence the discovery API reported is the
    # better answer than a default guess.
    if not front.get("license_url") and licence_hint:
        front["license"] = LICENCE_NAMES.get(licence_hint.strip().lower(), front["license"])
    front["doi"] = front.get("doi") or doi
    return {
        "doi": doi,
        "front": front,
        "sections": parsed["sections"],
        "source": source,
        "url": landing,
        "elapsed_s": elapsed,
    }
