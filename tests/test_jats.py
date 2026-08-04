"""Golden-file pin for the JATS extractor.

Written before the parser moved out of `scripts/build_corpus.py`, against a fixture that
exercises every construct the real Copernicus articles use: nested sections, two kinds of
cross-reference, inline and display maths, lists, and the figure and table blocks that
must be dropped. The expected strings below are what the original script produced. If a
change here is deliberate the corpus has to be rebuilt, which is exactly the signal this
test exists to raise.
"""

from pathlib import Path

from physearth.ingest import jats

FIXTURE = Path(__file__).parent / "fixtures" / "jats_sample.xml"

INTRODUCTION = (
    "A citation to (Debye et al., 1957) and to two at\n"
    "once (Debye et al., 1957; Picard et al., 2018).\n"
    "\n"
    "A figure reference 03 keeps only its number.\n"
    "\n"
    "- first item\n"
    "\n"
    "- second item\n"
    "\n"
    "$$T_b = T e$$"
)

METHOD = (
    "Lead paragraph of the method section.\n"
    "\n"
    "## First step\n"
    "\n"
    "Text of the first step.\n"
    "\n"
    "## Second step\n"
    "\n"
    "Text of the second step."
)


def _parsed():
    return jats.parse(FIXTURE.read_text(encoding="utf-8"), journal="Geoscientific Model Development")


def test_front_matter_is_extracted_field_by_field():
    front = _parsed()["front"]
    assert front["title"] == "A test article for the JATS extractor"
    assert front["authors"] == ["Henning Lowe", "Ghislain Picard"]
    assert front["journal"] == "Geoscientific Model Development"
    assert front["volume"] == "1"
    assert front["pages"] == "1-20"
    assert front["doi"] == "10.5194/test-1-1-2026"
    assert front["license"] == "CC-BY-4.0"
    assert front["license_url"] == "https://creativecommons.org/licenses/by/4.0/"


def test_the_abstract_keeps_inline_maths_and_collapses_whitespace():
    front = _parsed()["front"]
    assert front["abstract"] == (
        "An abstract with collapsing whitespace and an inline formula\n$\\kappa_s$ in it."
    )


def test_sections_render_exactly_as_they_did_before_the_move():
    sections = dict(_parsed()["sections"])
    assert sections["Introduction"] == INTRODUCTION
    assert sections["Method"] == METHOD


def test_a_section_with_nothing_but_a_table_is_dropped():
    titles = [title for title, _ in _parsed()["sections"]]
    assert "Empty section" not in titles
    assert titles == ["Abstract", "Introduction", "Method"]


def test_figures_tables_and_captions_never_reach_the_text():
    body = "\n".join(text for _, text in _parsed()["sections"])
    assert "This caption must not appear" not in body
    assert "Dropped." not in body
    assert "fig03.png" not in body
    assert "Figure 3" not in body


def test_nothing_in_the_parser_survives_between_two_calls():
    first = _parsed()
    second = jats.parse("<article><front><article-meta/></front><body/></article>")
    assert second["sections"] == []
    assert _parsed() == first


def test_the_bundled_corpus_still_matches_its_declared_section_sizes():
    from physearth import knowledge

    for slug in knowledge.slugs(kind="paper"):
        for declared in knowledge.section_index(slug):
            section = knowledge.read_section(slug, declared["id"])
            body = section["text"].split("\n\n---\n\n")[0]
            body = body.split("\n\n", 1)[1] if "\n\n" in body else body
            assert len(body) == declared["chars"], "%s#%s" % (slug, declared["id"])
