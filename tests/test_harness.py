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


def test_three_marker_kinds_resolve_independently():
    good = harness.check_citations(
        "A [smrt-v1#04] B [model:smrt@1.5.1] C [data:tvc-backscatter].",
        {"smrt-v1#04"},
        {"smrt@1.5.1"},
        {"tvc-backscatter"},
    )
    assert good["passed"]
    assert good["markers"] == ["smrt-v1#04", "model:smrt@1.5.1", "data:tvc-backscatter"]
    bad = harness.check_citations("[data:nope] and [other@9.9]", set(), {"smrt@1.5.1"}, {"tvc-backscatter"})
    assert bad["unresolved"] == ["other@9.9", "nope"]


def test_reading_a_dataset_satisfies_the_evidence_gate():
    long_answer = "x" * (harness.UNCITED_ANSWER_CHARS + 1)
    assert not harness.check_evidence(long_answer, set(), 0)["passed"]
    assert harness.check_evidence(long_answer, set(), 1)["passed"]


def test_a_short_refusal_is_not_treated_as_an_unsupported_claim():
    refusal = "The reference data does not contain backscatter observations at S-band."
    assert harness.check_evidence(refusal, set(), 0)["passed"]


def test_the_deployment_budget_blocks_when_the_window_is_full():
    from physearth import budget

    original = budget.MAX_RUNS_PER_WINDOW
    budget._STARTS.clear()
    budget.MAX_RUNS_PER_WINDOW = 2
    try:
        assert budget.acquire()[0]
        assert budget.acquire()[0]
        allowed, message = budget.acquire()
        assert not allowed and "shared" in message
    finally:
        budget.MAX_RUNS_PER_WINDOW = original
        budget._STARTS.clear()
