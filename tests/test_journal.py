"""The append-only research journal: ordered facts, never a hard dependency."""

from physearth import agent, journal, session
from test_approval import _Chunk, _Delta, _call_chunk, _fake_client


def _box(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    return session.new_session("m")


def test_entries_are_ordered_continuous_and_append_only(tmp_path, monkeypatch):
    box = _box(tmp_path, monkeypatch)

    assert journal.record(box, "plan_proposed", plan_version=1) == 1
    assert journal.record(box, "run_executed", run_id="r1", status="success") == 2
    assert journal.record(box, "figure_created", chart_id="c1") == 3

    stored = journal.entries(box["id"])
    assert [entry["kind"] for entry in stored] == [
        "plan_proposed", "run_executed", "figure_created",
    ]
    assert [entry["seq"] for entry in stored] == [1, 2, 3]
    assert stored[1]["run_id"] == "r1"
    assert journal.verify(box["id"]) == (True, "3 entries")

    # Append-only: a later fact never rewrites an earlier one.
    journal.record(box, "report_written")
    assert [entry["seq"] for entry in journal.entries(box["id"])] == [1, 2, 3, 4]


def test_verify_reports_a_gap_in_the_sequence(tmp_path, monkeypatch):
    box = _box(tmp_path, monkeypatch)
    journal.record(box, "first")
    journal.record(box, "second")
    path = journal.path_for(box["id"])
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text(
        lines[0] + "\n" + lines[1].replace('"seq": 2', '"seq": 5') + "\n",
        encoding="utf-8",
    )

    ok, detail = journal.verify(box["id"])

    assert ok is False
    assert "seq 2" in detail


def test_credential_like_fields_are_not_written(tmp_path, monkeypatch):
    box = _box(tmp_path, monkeypatch)

    journal.record(
        box,
        "tool_result",
        tool="run_model",
        status="success",
        api_key="sk-should-not-be-stored",
        MODELSCOPE_TOKEN="also-not",
        Authorization="Bearer nope",
    )

    entry = journal.entries(box["id"])[0]
    assert entry["status"] == "success"
    assert entry["tool"] == "run_model"
    assert not [key for key in entry if key.lower() in ("api_key", "modelscope_token", "authorization")]


def test_a_failing_write_never_breaks_the_run(tmp_path, monkeypatch):
    box = _box(tmp_path, monkeypatch)

    def boom(_session_id):
        raise OSError("disk full")

    monkeypatch.setattr(journal, "path_for", boom)

    assert journal.record(box, "tool_result") is None
    assert "journal_seq" not in box
    assert journal.flush(box) is False
    assert journal.entries(box["id"]) == []


def test_agent_journals_tool_results_and_checkpoints_side_effects(tmp_path, monkeypatch):
    box = _box(tmp_path, monkeypatch)
    script = [
        [_call_chunk("run_model", '{"model": "smrt"}')],
        [_Chunk(_Delta(content="It ran."))],
    ]
    client, _ = _fake_client(script)
    monkeypatch.setattr(agent, "_client", lambda: client)
    monkeypatch.setattr(
        agent.tools,
        "call",
        lambda name, arguments, **_kwargs: {
            "status": "success",
            "summary": "ran one model",
            "data": {"model": "smrt", "version": "1.5.1"},
        },
    )

    agent.run("run smrt for me", session=box)

    kinds = [entry["kind"] for entry in journal.entries(box["id"])]
    # The checkpoint is written before the side effect, the outcome after it.
    assert kinds[:2] == ["tool_start", "tool_result"]
    assert journal.verify(box["id"])[0] is True


def test_drift_reports_state_the_journal_holds_and_the_session_lost(tmp_path, monkeypatch):
    box = _box(tmp_path, monkeypatch)
    box["research"] = {"phase": "approved", "plan_version": 3}
    box["successful_runs"] = [{"planned_run_id": "r1", "status": "success"}]
    journal.record(
        box,
        "tool_result",
        tool="run_planned_model",
        status="success",
        phase="approved",
        plan_version=3,
        successful_run_ids=["r1"],
    )
    assert journal.drift(box) == []

    # Losing the recorded run is exactly the drift that used to look like "the run is still
    # missing" forever: the journal says it happened, the live state does not hold it.
    box["successful_runs"] = []
    findings = journal.drift(box)
    assert findings and "r1" in findings[0]

    # A session that moved *forward* is ordinary progress, never drift.
    box["successful_runs"] = [{"planned_run_id": "r1", "status": "success"}]
    box["research"]["plan_version"] = 4
    assert journal.drift(box) == []


def test_drift_reports_a_session_that_went_backwards_in_plan_version(tmp_path, monkeypatch):
    box = _box(tmp_path, monkeypatch)
    box["research"] = {"phase": "approved", "plan_version": 5}
    journal.record(box, "tool_result", tool="research_plan", status="success", plan_version=5)

    box["research"]["plan_version"] = 2

    findings = journal.drift(box)
    assert findings and "v005" in findings[0] and "v002" in findings[0]


def test_agent_reports_no_drift_in_a_normal_run(tmp_path, monkeypatch):
    box = _box(tmp_path, monkeypatch)
    script = [
        [_call_chunk("list_models", '{"model": "smrt"}')],
        [_Chunk(_Delta(content="Listed."))],
    ]
    client, _ = _fake_client(script)
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

    _, events, _ = agent.run("list the models", session=box)

    assert not [event for event in events if event["kind"] == "state_drift"]
    assert journal.latest(box["id"])["tool"] == "list_models"
