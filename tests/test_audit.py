import json

from physearth import session
from physearth.harness import audit


def test_structured_audit_log_is_persistent_session_scoped_and_redacted(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("PHYSEARTH_AUDIT_TEST", "1")
    audit.configure(tmp_path)
    box = session.new_session("test-model")
    box["turns"] = 2
    box["research"] = {
        "phase": "approved",
        "plan_version": 3,
        "selected_charts": ["density"],
        "plan": {"runs": [{"id": "run-a"}]},
    }
    audit.bind(box)

    audit.emit(
        "test_event",
        session=box,
        api_key="sk-this-must-never-appear",
        nested={"authorization": "Bearer this-must-never-appear"},
        detail="token ms-this-must-never-appear",
    )

    global_record = audit.recent(1)[0]
    session_record = audit.recent(1, box["id"])[0]
    assert global_record == session_record
    assert global_record["event_type"] == "test_event"
    assert global_record["session_id"] == box["id"]
    assert global_record["research_phase"] == "approved"
    assert global_record["plan_version"] == 3
    assert global_record["planned_run_ids"] == ["run-a"]
    serialized = json.dumps(global_record)
    assert "this-must-never-appear" not in serialized
    assert serialized.count("<redacted>") >= 3


def test_audit_writes_exception_traceback(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("PHYSEARTH_AUDIT_TEST", "1")
    audit.configure(tmp_path)
    try:
        raise RuntimeError("diagnostic failure")
    except RuntimeError as exc:
        audit.exception("test_exception", exc)

    record = audit.recent(1)[0]
    assert record["event_type"] == "test_exception"
    assert record["level"] == "ERROR"
    assert record["exception_type"] == "RuntimeError"
    assert "diagnostic failure" in record["traceback"]


def test_token_accounting_is_not_mistaken_for_a_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("PHYSEARTH_AUDIT_TEST", "1")
    audit.configure(tmp_path)
    box = session.new_session("test-model")

    audit.emit(
        "model_usage",
        session=box,
        prompt_tokens=1234,
        completion_tokens=56,
        token="sk-this-is-a-real-secret",
    )

    record = audit.recent(1, box["id"])[0]
    assert record["prompt_tokens"] == 1234
    assert record["completion_tokens"] == 56
    assert record["token"] == "<redacted>"
