"""The MCP server: the same capabilities and knowledge, addressed by a coding agent."""

from integrations.geoai import mcp_server, service


def _call(method, params=None, request_id=1):
    response = mcp_server.handle(
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
    )
    assert response is not None, method
    assert response["id"] == request_id
    return response["result"]


def test_initialize_announces_tools_resources_and_prompts():
    result = _call("initialize", {"protocolVersion": mcp_server.PROTOCOL_VERSION})

    assert result["protocolVersion"] == mcp_server.PROTOCOL_VERSION
    assert set(result["capabilities"]) == {"tools", "resources", "prompts"}
    assert result["serverInfo"]["name"] == mcp_server.SERVER_NAME


def test_notifications_get_no_response():
    assert mcp_server.handle(
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    ) is None


def test_tools_list_offers_the_engine_catalogue_and_the_host_tools():
    names = {item["name"] for item in _call("tools/list")["tools"]}

    for name in ("list_models", "run_model", "research_plan", "plot", "read_literature"):
        assert name in names, name
    for name in (
        "geoai_health",
        "geoai_session_new",
        "geoai_ask",
        "geoai_evidence",
        "geoai_decide",
        "geoai_verify_report",
    ):
        assert name in names, name
    assert len(names) >= 25


def test_health_reports_this_checkout():
    result = _call("tools/call", {"name": "geoai_health"})

    assert result["isError"] is False
    assert '"models": 6' in result["content"][0]["text"]


def test_no_tool_argument_offers_a_way_past_the_approval_gate():
    for tool in _call("tools/list")["tools"]:
        properties = (tool.get("inputSchema") or {}).get("properties") or {}
        assert not {"approve_runs", "approval"} & set(properties), tool["name"]
    decide = next(t for t in _call("tools/list")["tools"] if t["name"] == "geoai_decide")
    assert decide["inputSchema"]["properties"]["decision"]["enum"] == ["approve", "reject"]


def test_a_real_sweep_runs_through_mcp_after_the_verdict_and_registers_in_the_session():
    session = _call(
        "tools/call",
        {"name": "geoai_session_new", "arguments": {"model": "smrt", "approve_runs": True}},
    )
    session_id = _read_json(session)["session_id"]
    assert _read_json(session)["approval"] == "ask"

    run = _call(
        "tools/call",
        {
            "name": "run_model",
            "arguments": {
                "session_id": session_id,
                "model": "smrt",
                "parameters": {
                    "output": "tb",
                    "sweep_parameter": "density_kg_m3",
                    "sweep_start": 100,
                    "sweep_stop": 300,
                    "sweep_points": 3,
                },
            },
        },
    )

    assert run["isError"] is False, run
    assert _read_json(run)["status"] == "awaiting_approval"

    run = _call(
        "tools/call",
        {"name": "geoai_decide", "arguments": {"session_id": session_id, "decision": "approve"}},
    )
    payload = _read_json(run)
    assert payload["status"] == "success"
    assert payload["data"]["handle"]

    evidence = _read_json(
        _call("tools/call", {"name": "geoai_evidence", "arguments": {"session_id": session_id}})
    )
    assert evidence["handles"], evidence


def test_a_refused_call_is_reported_as_an_error_the_model_can_read(monkeypatch):
    monkeypatch.setitem(service._OPERATOR, "approval", "always")
    session = _read_json(
        _call("tools/call", {"name": "geoai_session_new", "arguments": {"model": "smrt"}})
    )

    refused = _call(
        "tools/call",
        {
            "name": "run_model",
            "arguments": {
                "session_id": session["session_id"],
                "model": "smrt",
                "parameters": {"density_kg_m3": 2000.0},
            },
        },
    )

    assert refused["isError"] is True
    assert "density" in refused["content"][0]["text"].lower()


def test_resources_expose_the_prompt_stack_models_and_a_paper_section():
    listed = {item["uri"] for item in _call("resources/list")["resources"]}
    assert {"geoai://prompt-stack", "geoai://models", "geoai://knowledge", "geoai://tools"} <= listed

    stack = _call("resources/read", {"uri": "geoai://prompt-stack"})["contents"][0]
    assert "citation" in stack["text"].lower()

    section = _call("resources/read", {"uri": "geoai://paper/smrt-v1/03"})["contents"][0]
    assert len(section["text"]) > 200


def test_prompts_carry_the_evidence_rules_with_the_task():
    listed = {item["name"] for item in _call("prompts/list")["prompts"]}
    assert {"geoai-reproduce-figure", "geoai-sweep-parameter", "geoai-compare-models"} <= listed

    prompt = _call(
        "prompts/get",
        {"name": "geoai-reproduce-figure", "arguments": {"paper": "smrt-v1", "figure": "fig03"}},
    )
    text = prompt["messages"][0]["content"]["text"]

    assert "smrt-v1#fig03" in text
    assert "never estimate one" in text
    assert "abstract-only" in text.lower()


def test_an_unknown_method_is_a_protocol_error():
    response = mcp_server.handle({"jsonrpc": "2.0", "id": 7, "method": "nope"})

    assert response["error"]["code"] == -32601


def _read_json(result):
    import json

    return json.loads(result["content"][0]["text"])


def test_initialize_negotiates_the_protocol_version_and_elicitation():
    for asked in mcp_server.PROTOCOL_VERSIONS:
        assert _call("initialize", {"protocolVersion": asked})["protocolVersion"] == asked
    assert _call("initialize", {"protocolVersion": "2099-01-01"})["protocolVersion"] == (
        mcp_server.PROTOCOL_VERSION
    )

    asks = {"capabilities": {"elicitation": {}}}
    _call("initialize", {"protocolVersion": "2025-06-18", **asks})
    assert mcp_server._CLIENT["elicitation"] is True
    _call("initialize", {"protocolVersion": "2024-11-05", **asks})
    assert mcp_server._CLIENT["elicitation"] is False


def test_only_the_tools_the_engine_offers_are_listed():
    names = {tool["name"] for tool in _call("tools/list", {})["tools"]}
    assert not names & {"run_raw_smrt", "read_raw_paper"}
    assert "run_model" in names
