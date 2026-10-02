"""History a later step has made obsolete is stubbed, by rule, never summarised."""

import copy
import json

from physearth import agent, session
from physearth.agent.loop import _plan_result_for_model
from physearth.agent.messages import prune_superseded

from tests.test_approval import _call_chunk, _Chunk, _Delta, _fake_client


def _call(call_id, name, arguments):
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{
            "id": call_id, "type": "function",
            "function": {"name": name, "arguments": json.dumps(arguments)},
        }],
    }


def _result(call_id, status, summary, data=None):
    return {
        "role": "tool", "tool_call_id": call_id,
        "content": json.dumps({"status": status, "summary": summary, "data": data or {}}),
    }


def _conversation():
    return [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "reproduce figure 3"},
        _call("a", "read_research_guideline", {"topic": "planning"}),
        _result("a", "success", "guideline open", {"text": "long guideline " * 50}),
        _call("b", "list_models", {"model": "smrt"}),
        _result("b", "success", "declaration", {"parameters": {"x": 1}}),
        _call("c", "read_literature", {"slug": "smrt-v1", "section": "08"}),
        _result("c", "success", "section open", {"text": "evidence " * 50}),
        _call("d", "research_plan", {"action": "propose", "runs": ["big"] * 50}),
        _result(
            "d", "terminal_error", "refused", {"error_code": "plan_quality", "problems": ["x"]}
        ),
        {"role": "user", "content": "Repair the submitted reproduction plan using these problems."},
        _call("e", "research_plan", {"action": "revise_plan", "changes": {"limitations": ["a"]}}),
        _result("e", "needs_input", "plan ready", {"plan": {"runs": []}}),
        _call("f", "read_research_guideline", {"topic": "reporting"}),
        _result("f", "success", "reporting open", {"text": "report rules"}),
    ]


def _content(messages, index):
    return json.loads(messages[index]["content"])


def test_a_refused_submission_is_stubbed_once_a_later_one_exists():
    messages = prune_superseded(_conversation())
    assert _content(messages, 9)["elided"] == "superseded by a later research_plan call"
    assert _content(messages, 9)["summary"] == "refused"
    arguments = json.loads(messages[8]["tool_calls"][0]["function"]["arguments"])
    assert arguments == {"action": "propose", "elided": "superseded submission"}
    assert messages[10]["content"].startswith("Repair request for a superseded")
    assert "elided" not in _content(messages, 12)


def test_planning_reads_are_stubbed_after_the_plan_but_evidence_is_kept():
    messages = prune_superseded(_conversation())
    assert "elided" in _content(messages, 3)
    assert "elided" in _content(messages, 5)
    assert "elided" not in _content(messages, 7)
    assert "elided" not in _content(messages, 14)


def test_nothing_is_stubbed_before_there_is_a_reason():
    messages = _conversation()[:10]
    before = copy.deepcopy(messages)
    assert prune_superseded(messages) == before


def test_a_repeated_identical_call_keeps_only_its_latest_result():
    messages = _conversation()[:8] + [
        _call("g", "read_literature", {"slug": "smrt-v1", "section": "08"}),
        _result("g", "success", "section open", {"text": "evidence again"}),
    ]
    messages = prune_superseded(messages)
    assert _content(messages, 7)["elided"] == "repeated by a later identical call"
    assert "elided" not in _content(messages, 9)


def test_pruning_twice_changes_nothing_more():
    once = prune_superseded(_conversation())
    assert prune_superseded(copy.deepcopy(once)) == once


def test_each_request_extends_the_one_before_it(monkeypatch):
    script = [
        [_call_chunk("list_models", '{"model": "smrt"}')],
        [_Chunk(_Delta(content="Listed."))],
    ]
    client, sent = _fake_client(script)
    monkeypatch.setattr(agent.completion, "_client", lambda: client)
    for _ in agent.stream("what can smrt compute", session=session.new_session("m")):
        pass
    assert len(sent) == 2
    first, second = sent
    assert first[-1]["content"].startswith("PhysEarth run state")
    assert second[: len(first) - 1] == first[:-1]


def test_the_model_sees_an_accepted_plan_once_with_repairs_by_field():
    payload = {
        "status": "needs_input",
        "summary": "ready",
        "data": {
            "plan": {
                "runs": [{"id": "r"}],
                "capability_review": {"big": "copy"},
                "parameter_resolution": [{"big": "copy"}],
                "automatic_repairs": [{"field": "baseline_run_id", "to": "r"}],
            },
            "protocol": {"plan": "again"},
            "protocol_yaml": "plan: again",
        },
    }
    view = _plan_result_for_model(payload)["data"]
    assert set(view) == {"plan"}
    assert view["plan"] == {"runs": [{"id": "r"}], "automatic_repairs": ["baseline_run_id"]}
    assert "protocol" in payload["data"]
