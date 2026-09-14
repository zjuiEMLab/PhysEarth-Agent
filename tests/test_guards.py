"""The loop-hygiene guard: advisory reminders before any hard stop."""

from physearth import agent, guards, session, tools
from test_approval import _Chunk, _Delta, _call_chunk, _fake_client


def _box():
    return session.new_session("m")


def test_guard_counts_identical_calls_and_escalates_before_anything_blocks():
    box = _box()
    calls = [guards.observe(box, "list_models", {"model": "smrt"}) for _ in range(8)]

    assert [item for item in calls if item] == [calls[2], calls[4], calls[7]]
    assert calls[2]["threshold"] == 3
    assert calls[4]["threshold"] == 5
    assert calls[7]["threshold"] == 8
    assert calls[7]["count"] == 8
    assert "identical arguments" in calls[2]["detail"]
    assert "cannot produce a different result" in calls[7]["detail"]


def test_guard_treats_argument_order_and_formatting_as_the_same_call():
    box = _box()
    guards.observe(box, "run_model", {"model": "smrt", "parameters": {"a": 1, "b": 2.0}})
    guards.observe(box, "run_model", {"parameters": {"b": 2.0, "a": 1}, "model": "smrt"})
    third = guards.observe(box, "run_model", {"model": "smrt", "parameters": {"a": 1, "b": 2}})

    assert third and third["count"] == 3


def test_guard_starts_a_new_chain_when_the_arguments_change():
    box = _box()
    for _ in range(2):
        guards.observe(box, "run_model", {"model": "smrt"})
    changed = guards.observe(box, "run_model", {"model": "tau_omega"})

    assert changed is None
    assert box["guard_repeats"]["count"] == 1


def test_guard_reset_makes_a_new_question_a_fresh_chain():
    box = _box()
    for _ in range(3):
        guards.observe(box, "list_models", {})
    assert box["guard_repeats"]["count"] == 3

    guards.reset(box)

    assert "guard_repeats" not in box
    assert guards.observe(box, "list_models", {}) is None


def test_excluded_tool_neither_counts_nor_resets_the_chain(monkeypatch):
    monkeypatch.setenv("PHYSEARTH_REPEAT_GUARD_EXCLUDE", "todo_write")
    box = _box()
    guards.observe(box, "list_models", {})
    guards.observe(box, "list_models", {})

    assert guards.observe(box, "todo_write", {"items": []}) is None
    third = guards.observe(box, "list_models", {})

    assert third and third["count"] == 3


def test_guard_preview_is_capped_in_the_detailed_reminder(monkeypatch):
    monkeypatch.setenv("PHYSEARTH_REPEAT_GUARD_PREVIEW_CHARS", "40")
    box = _box()
    long_argument = {"model": "smrt", "note": "x" * 400}
    for _ in range(5):
        reminder = guards.observe(box, "run_model", long_argument)

    assert "more chars" in reminder["detail"]
    assert "x" * 200 not in reminder["detail"]


def test_hard_stop_count_sits_one_call_past_the_last_threshold(monkeypatch):
    monkeypatch.setenv("PHYSEARTH_REPEAT_GUARD_THRESHOLDS", "2,4")
    assert guards.hard_stop_count() == 5
    monkeypatch.setenv("PHYSEARTH_REPEAT_GUARD_THRESHOLDS", "not-a-number")
    assert guards.hard_stop_count() == 9


def test_repeated_identical_tool_call_gets_reminders_before_the_hard_stop(monkeypatch):
    box = _box()
    script = [
        [_call_chunk("list_models", '{"model": "smrt"}')]
        for _ in range(guards.hard_stop_count())
    ]
    client, sent = _fake_client(script)
    monkeypatch.setattr(agent, "_client", lambda: client)
    monkeypatch.setattr(
        agent.tools,
        "call",
        lambda name, arguments, **_kwargs: {
            "status": "success",
            "summary": "registered models",
            "data": {},
        },
    )

    answer, events, _ = agent.run("list the models", session=box)

    reminders = [
        event for event in events
        if event["kind"] == "harness_warning" and event.get("rule") == "repeat_tool_reminder"
    ]
    assert [event["threshold"] for event in reminders] == [3, 5, 8]
    assert any(
        event["kind"] == "harness_stop" and event["rule"] == "duplicate_success_no_progress"
        for event in events
    )
    # The advice reaches the model as a message after the repeated result, not as a veto.
    third_request = sent[3]
    assert any(
        message.get("role") == "user" and "identical arguments" in (message.get("content") or "")
        for message in third_request
    )
    assert "identical successful list_models calls" in answer


def test_failure_chain_remembers_repeats_and_resets_on_progress():
    box = _box()
    assert guards.remember_failure(box, "research_plan", "sig-a") == 1
    assert guards.remember_failure(box, "research_plan", "sig-a") == 2
    # A different failure is progress, not a repeat of the first one.
    assert guards.remember_failure(box, "research_plan", "sig-b") == 1
    assert guards.failure_count(box, "research_plan", "sig-a") == 0
    assert guards.failure_count(box, "research_plan") == 1

    guards.clear_failure(box, "research_plan")

    assert guards.failure_count(box, "research_plan") == 0
    assert "guard_failures" not in box


def test_plan_loop_does_not_restart_for_free_after_a_new_message(monkeypatch):
    from physearth import harness

    box = _box()
    box["research_required"] = True
    problem = {
        "field": "parameter_mapping[0].model_input",
        "source": "registered_model_declaration",
        "actual": "density",
        "expected": "an exact registered model input",
        "allowed_values": ["density_kg_m3"],
        "repair": "Replace the unknown input with an exact parameter returned by list_models.",
        "blocking": True,
    }

    def failing_call(name, arguments, **_kwargs):
        assert name == "research_plan"
        return {
            "status": "terminal_error",
            "summary": "Reproduction plan incomplete: 1 parameter mapping issue(s).",
            "data": {
                "error_code": "reproduction_evidence_incomplete",
                "problems": [problem],
            },
            "error": "mapping incomplete",
        }

    monkeypatch.setattr(agent.tools, "call", failing_call)
    budget = harness.max_interventions(tool="research_plan")

    first = [[_call_chunk("research_plan", '{"action":"propose"}')] for _ in range(budget + 2)]
    client, _ = _fake_client(first)
    monkeypatch.setattr(agent, "_client", lambda: client)
    _, events, _ = agent.run("Reproduce the paper result", session=box)

    assert any(
        event["kind"] == "harness_stop" and event["rule"] == "no_progress"
        for event in events
    )
    assert guards.failure_count(box, "research_plan") == budget

    # The next message must not buy another full corrective budget for the same failure.
    second = [[_call_chunk("research_plan", '{"action":"propose"}')] for _ in range(budget + 2)]
    client2, sent2 = _fake_client(second)
    monkeypatch.setattr(agent, "_client", lambda: client2)
    answer2, events2, _ = agent.run("Try the plan again", session=box)

    assert len(sent2) == 1
    stops = [
        event for event in events2
        if event["kind"] == "harness_stop" and event["rule"] == "plan_loop_no_progress"
    ]
    assert stops and stops[0]["session_repeats"] == budget + 1
    assert "identical research_plan validation failure" in answer2
