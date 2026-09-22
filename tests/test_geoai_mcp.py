"""The MCP server: the same capabilities and knowledge, addressed by a coding agent."""

from integrations.geoai import mcp_server


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
    for name in ("geoai_health", "geoai_session_new", "geoai_ask", "geoai_evidence"):
        assert name in names, name
    assert len(names) >= 25


def test_health_reports_this_checkout():
    result = _call("tools/call", {"name": "geoai_health"})

    assert result["isError"] is False
    assert '"models": 6' in result["content"][0]["text"]


def test_a_real_sweep_runs_through_mcp_and_registers_in_the_session():
    session = _call(
        "tools/call",
        {"name": "geoai_session_new", "arguments": {"model": "smrt", "approve_runs": True}},
    )
    session_id = _read_json(session)["session_id"]

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
    payload = _read_json(run)
    assert payload["status"] == "success"
    assert payload["data"]["handle"]

    evidence = _read_json(
        _call("tools/call", {"name": "geoai_evidence", "arguments": {"session_id": session_id}})
    )
    assert evidence["handles"], evidence


def test_a_refused_call_is_reported_as_an_error_the_model_can_read():
    session = _read_json(
        _call(
            "tools/call",
            {"name": "geoai_session_new", "arguments": {"model": "smrt", "approve_runs": True}},
        )
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
