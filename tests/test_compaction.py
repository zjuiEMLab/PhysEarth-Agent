"""Deterministic context relief before anything summarises."""

from physearth import agent, compaction, journal, session


def _box(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    return session.new_session("m")


def test_a_payload_that_fits_is_left_exactly_alone():
    text = "x" * 100
    messages = [{"role": "tool", "content": text}]

    pruned, report = compaction.prune_tool_outputs(messages, limit=256)

    assert report == []
    assert pruned[0]["content"] == text


def test_an_oversized_tool_output_keeps_its_head_and_tail():
    head, tail = "HEAD-" + "a" * 400, "b" * 400 + "-TAIL"
    messages = [{"role": "system", "content": "sys"}, {"role": "tool", "content": head + tail}]

    pruned, report = compaction.prune_tool_outputs(messages, limit=256)

    assert len(report) == 1
    record = report[0]
    assert record["index"] == 1
    assert record["before_chars"] == len(head + tail)
    assert record["after_chars"] < record["before_chars"]
    body = pruned[1]["content"]
    assert body.startswith("HEAD-")
    assert body.endswith("-TAIL")
    assert "pruned" in body
    # Non-tool messages are never touched.
    assert pruned[0]["content"] == "sys"


def test_pruning_is_monotonic_and_reports_the_tool_identity():
    payload = '{"tool": "run_planned_model", "data": "' + "z" * 900 + '"}'
    messages = [{"role": "tool", "content": payload}]

    first, _ = compaction.prune_tool_outputs(messages, limit=300)
    second, again = compaction.prune_tool_outputs(first, limit=300)

    assert len(first[0]["content"]) <= 300 + len(compaction.marker(0, 0)) + 5
    assert again == [], "a pruned payload is already below the limit and must not grow"
    assert second[0]["content"] == first[0]["content"]


def test_estimate_is_a_fixed_density_heuristic():
    messages = [{"role": "tool", "content": "a" * 400}]
    assert compaction.total_chars(messages) == 400
    assert compaction.estimated_tokens(messages) == 100


def test_compaction_route_prunes_and_journals_what_it_removed(tmp_path, monkeypatch):
    box = _box(tmp_path, monkeypatch)
    monkeypatch.setenv("PHYSEARTH_TOOL_OUTPUT_MAX_CHARS", "512")
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "question"},
        {"role": "tool", "content": "y" * 4000},
    ]

    result = agent._compact_messages(messages, box)

    tool_message = [item for item in result if item.get("role") == "tool"][-1]
    assert len(tool_message["content"]) < 4000
    entries = [entry for entry in journal.entries(box["id"]) if entry["kind"] == "context_pruned"]
    assert entries and entries[0]["messages"] == 1
    assert entries[0]["before_chars"] == 4000
    assert entries[0]["after_chars"] < 4000


def test_compaction_route_without_a_session_still_prunes(monkeypatch):
    monkeypatch.setenv("PHYSEARTH_TOOL_OUTPUT_MAX_CHARS", "512")
    result = agent._compact_messages([{"role": "tool", "content": "q" * 4000}])
    assert len(result[0]["content"]) < 4000
