from physearth import harness, knowledge, tools


def test_markers_resolve_only_against_sections_read():
    read = {"smrt-v1#05"}
    good = harness.check_citations("IBA uses the ACF [smrt-v1#05].", read)
    assert good["passed"]
    bad = harness.check_citations("Snow is cold [memls3a#02] and wet [smrt-v1#99].", read)
    assert not bad["passed"]
    assert bad["unresolved"] == ["memls3a#02", "smrt-v1#99"]


def test_evidence_gate_blocks_long_answer_without_reading():
    long_answer = "x" * (harness.UNCITED_ANSWER_CHARS + 1)
    blocked = harness.check_evidence(long_answer, set())
    assert not blocked["passed"]
    assert harness.check_evidence("Out of scope, sorry.", set())["passed"]
    assert harness.check_evidence(long_answer, {"smrt-v1#00"})["passed"]


def test_budget_stops_the_loop():
    state = {"model_calls": 12, "max_model_calls": 12, "tool_calls": 0, "max_tool_calls": 10}
    assert not harness.check_budget(state)["passed"]


def test_every_corpus_citation_key_is_reachable():
    keys = knowledge.citation_keys()
    assert len(keys) == 80
    for slug in knowledge.slugs(kind=None):
        for section in knowledge.section_index(slug):
            assert knowledge.read_section(slug, section["id"])["text"]


def test_tool_errors_are_structured_not_exceptions():
    result = tools.call("read_literature", {"slug": "does-not-exist"})
    assert result["status"] == "terminal_error"
    assert "Available slugs" in result["summary"]
    assert tools.call("no_such_tool", {})["status"] == "terminal_error"
