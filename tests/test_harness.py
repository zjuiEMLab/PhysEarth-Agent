from physearth import harness, tools
from physearth.corpus import knowledge


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
    sections = sum(len(knowledge.section_index(s)) for s in knowledge.slugs(kind=None))
    assert len(keys) == sections == 82
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
    from physearth.harness import budget

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


def test_the_deployment_budget_is_unlimited_when_cap_is_zero():
    from physearth.harness import budget

    original = budget.MAX_RUNS_PER_WINDOW
    budget._STARTS.clear()
    budget.MAX_RUNS_PER_WINDOW = 0
    try:
        for _ in range(125):
            assert budget.acquire()[0]
        assert budget.used() == (125, 0)
    finally:
        budget.MAX_RUNS_PER_WINDOW = original
        budget._STARTS.clear()


def test_a_forced_call_turns_reasoning_off_in_each_provider_s_terms(monkeypatch):
    from physearth import config
    from physearth.agent import loop

    monkeypatch.setattr(config, "llm_api_base", lambda: "https://openrouter.ai/api/v1")
    assert loop._thinking_off() == {"enable_thinking": False, "reasoning": {"enabled": False}}
    monkeypatch.setattr(config, "llm_api_base", lambda: "https://api-inference.modelscope.cn/v1")
    assert loop._thinking_off() == {"enable_thinking": False}


def test_a_router_fault_keeps_what_the_provider_said():
    from physearth.agent.faults import _upstream_text

    class Fault(Exception):
        body = {"message": "Provider returned error", "metadata": {"raw": "invalid_image"}}

    assert _upstream_text(Fault("HTTP 400")) == "Provider returned error: invalid_image"


def test_compaction_never_leaves_a_tool_result_without_its_call(monkeypatch):
    from physearth.agent import messages as compaction

    monkeypatch.setattr(compaction, "MAX_KEPT_HISTORY_CHARS", 1500)
    rounds = []
    for n in range(6):
        rounds += [
            {"role": "assistant", "content": "y" * 300,
             "tool_calls": [{"id": f"call_{n}", "type": "function",
                             "function": {"name": "read_literature", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": f"call_{n}", "content": "x" * 600},
        ]
    sent = compaction._compact_messages(
        [{"role": "system", "content": "s"}, {"role": "user", "content": "question"}]
        + rounds
        + [{"role": "user", "content": [{"type": "text", "text": "inspect the figure"}]}]
    )
    called = set()
    for message in sent:
        for call in message.get("tool_calls") or ():
            called.add(call["id"])
        if message.get("role") == "tool":
            assert message["tool_call_id"] in called
    assert any(message.get("role") == "tool" for message in sent)
