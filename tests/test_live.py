"""The live literature layer, tested without touching the network.

Everything that talks to a host is exercised against a recorded document rather than a
live one, so the suite stays deterministic and runnable offline. What is checked here is
the part that has to be right regardless of what the network says: the tier a piece of
evidence lands in, the marker it earns, what that marker may carry, and the difference
between a service failing and a paper not existing.
"""

from pathlib import Path

import pytest

from physearth import harness, live, prompt, session, tools
from physearth.ingest import fulltext, http, jats

FIXTURE = Path(__file__).parent / "fixtures" / "jats_sample.xml"


@pytest.fixture
def ingested():
    """A session holding one paper, taken in through the real ingest path."""
    box = session.new_session("m")
    parsed = jats.parse(FIXTURE.read_text(encoding="utf-8"), "Test Journal")
    record = {
        "doi": "10.5194/test-1-1-2026",
        "front": dict(parsed["front"], year=2026),
        "sections": parsed["sections"],
        "source": "copernicus",
        "url": "https://tc.copernicus.org/articles/1/1/2026/test-1-1-2026.xml",
        "elapsed_s": 0.1,
    }
    card = live.add(box, record)
    return box, card


def test_a_doi_becomes_a_marker_safe_slug_that_cannot_shadow_a_bundled_one():
    assert live.slug_for("10.5194/tc-18-3971-2024") == "tc-18-3971-2024"
    assert live.slug_for("https://doi.org/10.3390/rs10020170") == "rs10020170"
    assert live.slug_for("10.1029/2021AV000630").startswith("p-2021")
    taken = {"tc-18-3971-2024"}
    assert live.slug_for("10.5194/tc-18-3971-2024", taken) == "tc-18-3971-2024-2"
    assert harness.CITATION_PATTERN.match("[%s#03]" % live.slug_for("10.5194/tc-18-3971-2024"))


def test_an_ingested_paper_reads_and_cites_exactly_like_a_bundled_one(ingested):
    box, card = ingested
    slug = card["slug"]
    index = live.section_index(box, slug)
    assert [s["id"] for s in index] == ["00", "01", "02"]

    opened = tools.call("read_literature", {"slug": slug, "section_id": "01"}, session=box)
    assert opened["status"] == "success"
    assert opened["data"]["source"] == "session"
    key = opened["data"]["citation_key"]
    box["sections_read"].add(key)
    assert harness.check_citations("A claim [%s]." % key, box["sections_read"])["passed"]


def test_the_trace_can_tell_a_fetched_paper_from_a_shipped_one(ingested):
    box, card = ingested
    assert live.source_of(box, card["slug"]) == "session"
    assert live.source_of(box, "smrt-v1") == "bundled"
    assert live.source_of(box, "model-comparison") == "skill"
    sources = {e["source"] for e in live.catalogue(box)}
    assert sources == {"bundled", "session"}


def test_an_ingested_section_is_wrapped_as_external_and_scanned(ingested):
    box, card = ingested
    opened = live.wrapped_section(box, card["slug"], "01", 16000)
    assert opened["text"].startswith("<<<EXTERNAL SOURCE")
    assert "kind=open-access paper fetched in this conversation" in opened["text"]
    assert opened["findings"] == []


def test_a_session_cannot_take_in_more_papers_than_its_limit(ingested):
    box, _ = ingested
    parsed = jats.parse(FIXTURE.read_text(encoding="utf-8"))
    for n in range(live.MAX_PAPERS):
        record = {
            "doi": "10.5194/test-%d-1-2026" % (n + 2),
            "front": parsed["front"],
            "sections": parsed["sections"],
            "source": "copernicus",
            "url": "",
        }
        if n < live.MAX_PAPERS - 1:
            live.add(box, record)
        else:
            with pytest.raises(ValueError, match="already taken in"):
                live.add(box, record)


def test_an_abstract_marker_resolves_only_for_a_doi_the_session_actually_saw():
    box = session.new_session("m")
    live.remember_abstracts(
        box,
        [
            {
                "doi": "10.5194/tc-18-3971-2024",
                "title": "t",
                "year": 2024,
                "authors": "a",
                "venue": "v",
                "license": "cc-by",
                "abstract": "x",
            }
        ],
    )
    seen = box["abstracts_seen"]
    assert harness.check_citations(
        "That study existed [abs:10.5194/tc-18-3971-2024].", set(), abstracts_seen=seen
    )["passed"]
    missed = harness.check_citations(
        "Some other study [abs:10.9999/never-seen].", set(), abstracts_seen=seen
    )
    assert missed["unresolved"] == ["abs:10.9999/never-seen"]


def test_an_abstract_may_describe_a_study_but_never_carry_a_result_value():
    doi = "10.5194/tc-18-3971-2024"
    allowed = "That study observed tundra snow at 17.2 GHz and 40 degrees [abs:%s]." % doi
    assert harness.check_abstract_depth(allowed)["passed"]
    for refused in (
        "The brightness temperature was 213.4 K [abs:%s]." % doi,
        "They report a bias of 1.8 dB [abs:%s]." % doi,
        "Soil moisture reached 0.32 m3 m-3 [abs:%s]." % doi,
    ):
        result = harness.check_abstract_depth(refused)
        assert not result["passed"], refused
        assert result["offending"][0]["doi"] == doi
    assert "read the paper" in harness.abstract_depth_correction(
        harness.check_abstract_depth("It was 213 K [abs:%s]." % doi)
    )


def test_the_value_rule_does_not_reach_into_a_neighbouring_sentence():
    doi = "10.5194/tc-18-3971-2024"
    text = "That study looked at tundra snow [abs:%s]. Our own run gave 213.4 K [model:smrt@1.5.1]." % doi
    assert harness.check_abstract_depth(text)["passed"]


def test_the_final_review_applies_all_three_rules_in_order():
    box = session.new_session("m")
    box["sections_read"].add("smrt-v1#05")
    box["abstracts_seen"].add("10.5194/tc-18-3971-2024")
    state = session.new_state(box)
    state["model_runs"] = 1

    check, correction = harness.review_final("Fine [smrt-v1#05].", state)
    assert correction is None and check["rule"] == "citation_integrity"

    check, correction = harness.review_final("Bad [smrt-v1#99].", state)
    assert check["rule"] == "citation_integrity" and "smrt-v1#99" in correction

    check, correction = harness.review_final(
        "It was 213 K [abs:10.5194/tc-18-3971-2024].", state
    )
    assert check["rule"] == "abstract_depth" and "abstract" in correction


def test_only_https_on_an_allowed_host_can_be_opened():
    for url in (
        "http://api.openalex.org/works",
        "https://evil.example.com/works",
        "https://api.openalex.org.evil.com/works",
    ):
        with pytest.raises(ValueError):
            http.get_bytes(url)


def test_a_copernicus_url_is_derived_from_the_doi_and_nothing_else():
    url, journal = fulltext.copernicus_url("10.5194/tc-18-3971-2024")
    assert url == "https://tc.copernicus.org/articles/18/3971/2024/tc-18-3971-2024.xml"
    assert journal == "The Cryosphere"
    assert fulltext.route("10.5194/tc-18-3971-2024") == "copernicus"
    assert fulltext.route("10.3390/rs10020170") == "europepmc"
    assert fulltext.route("not-a-doi") == ""
    assert fulltext.normalise("https://doi.org/10.5194/TC-18-3971-2024") == (
        "10.5194/tc-18-3971-2024"
    )


def test_the_agent_never_supplies_an_address(monkeypatch):
    """Whatever the model writes in the doi field, only a derived URL is ever opened."""
    opened = []

    def spy(url, **kwargs):
        opened.append(url)
        raise http.Upstream("test", "not actually fetched")

    monkeypatch.setattr(http, "get_text", spy)
    monkeypatch.setattr(http, "get_json", spy)
    box = session.new_session("m")
    tools.call(
        "ingest_paper",
        {"doi": "https://evil.example.com/payload.xml"},
        session=box,
    )
    tools.call("ingest_paper", {"doi": "10.5194/tc-13-3045-2019"}, session=box)
    assert all(url.startswith("https://") for url in opened)
    assert all("evil.example.com" not in url for url in opened)
    assert opened == ["https://tc.copernicus.org/articles/13/3045/2019/tc-13-3045-2019.xml"]


def test_a_doi_already_shipped_is_never_fetched_again(monkeypatch):
    def refuse(url, **kwargs):
        raise AssertionError("a bundled paper must not be fetched: %s" % url)

    monkeypatch.setattr(http, "get_text", refuse)
    box = session.new_session("m")
    result = tools.call("ingest_paper", {"doi": "10.5194/tc-18-3971-2024"}, session=box)
    assert result["status"] == "success"
    assert result["data"]["slug"] == "arctic-snow-emission"


def test_an_outage_is_reported_as_an_outage_and_not_as_an_absence(monkeypatch):
    def down(url, **kwargs):
        raise http.Upstream("api.openalex.org", "HTTP 503")

    monkeypatch.setattr(http, "get_json", down)
    box = session.new_session("m")
    result = tools.call("discover_literature", {"query": "snow"}, session=box)
    assert result["status"] == "terminal_error"
    assert "upstream fault" in result["summary"]
    assert "not an empty result" in result["summary"]


def test_a_paper_no_route_holds_stays_at_abstract_level(monkeypatch):
    monkeypatch.setattr(http, "get_json", lambda url, **kw: ({"resultList": {"result": []}}, 0.1))
    box = session.new_session("m")
    result = tools.call("ingest_paper", {"doi": "10.1109/tgrs.2021.3086412"}, session=box)
    assert result["status"] == "terminal_error"
    assert "abstract level" in result["summary"]
    assert "[abs:10.1109/tgrs.2021.3086412]" in result["summary"]


def test_switching_the_layer_off_leaves_the_offline_path_whole(monkeypatch):
    monkeypatch.setenv("PHYSEARTH_ONLINE", "0")
    assert not http.online()
    offered = {s["function"]["name"] for s in tools.specs()}
    assert offered == {
        "list_literature",
        "read_literature",
        "list_models",
        "run_model",
        "read_reference_dataset",
        "plot",
        "research_plan",
    }
    box = session.new_session("m")
    assert tools.call("read_literature", {"slug": "smrt-v1", "section_id": "05"}, session=box)[
        "status"
    ] == "success"
    assert tools.call("run_model", {"model": "smrt"}, session=box)["status"] == "success"
    assert tools.call("list_literature", {"scenario": "snow"}, session=box)["status"] == "success"

    text = prompt.build(session.new_state(box))
    assert "discover_literature" not in text
    assert "[abs:doi]" not in text
    assert "read_literature" in text


def test_the_online_prompt_only_promises_what_is_offered(monkeypatch):
    monkeypatch.setenv("PHYSEARTH_ONLINE", "1")
    text = prompt.build(session.new_state(session.new_session("m")))
    offered = {s["function"]["name"] for s in tools.specs()}
    assert "discover_literature" in offered and "ingest_paper" in offered
    assert "[abs:doi]" in text
    assert "upstream fault, not an absence" in text
