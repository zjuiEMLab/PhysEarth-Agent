"""The MCP server: the same capabilities and knowledge, addressed by a coding agent."""

import base64

from integrations.geoai import mcp_server

# The smallest thing the host will accept as an image: a real PNG, so the test exercises the bytes
# rather than a placeholder string.
_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8AAAwAB/wFH"
    "CgAAAABJRU5ErkJggg=="
)


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


# ── one conversation, one session ─────────────────────────────────────────────────────────────

def _payload(name, arguments=None, request_id=7):
    import json

    result = _call("tools/call", {"name": name, "arguments": arguments or {}}, request_id=request_id)
    return json.loads(result["content"][0]["text"])


def test_consecutive_tool_calls_share_one_session():
    # The bug this pins, found by driving the plugin from a real harness: a host calls tool by
    # tool and knows no session id, so every call used to land in a fresh session. `read_literature`
    # recorded its section in one, `run_model` ran in another, and the research capability
    # checkpoint then reported that nothing had been read — after it had been. The agent's
    # response was to start reading this repository's source to debug its own plugin.
    # `session_new` starts a fresh conversation *and* becomes the process default, so the calls
    # that follow join it — that is how a host resets a conversation.
    first = _payload("geoai_session_new", {})["session_id"]
    second = _payload("geoai_session_new", {})["session_id"]
    assert first != second

    read = _payload("read_literature", {"slug": "research-planning", "section_id": "00"})
    models = _payload("list_models", {"model": "smrt"})
    evidence = _payload("geoai_evidence", {})

    assert read["session_id"] == models["session_id"] == evidence["session_id"] == second
    # And what the engine recorded is what a later check will look at.
    assert "research-planning#00" in evidence["sections_read"]


def test_an_explicit_session_id_still_wins():
    # A host that manages its own sessions keeps working: the process default is a default, not a
    # cage.
    mine = _payload("geoai_session_new", {})["session_id"]
    other = _payload("geoai_session_new", {})["session_id"]
    assert mine != other

    read = _payload("read_literature", {"slug": "research-planning", "section_id": "00", "session_id": other})
    assert read["session_id"] == other
    # Reads land in the session that was named, and the process default is untouched by them.
    assert "research-planning#00" in _payload("geoai_evidence", {"session_id": other})["sections_read"]


def test_the_payload_names_the_session_that_answered():
    # Without this a host could not be explicit even if it wanted to: nothing told it which
    # session its handle belonged to.
    read = _payload("read_literature", {"slug": "research-planning"})
    assert read["session_id"].startswith("ses_")


def _png(tmp_path, name="drawn.png"):
    path = tmp_path / "figures" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = base64.b64decode(_ONE_PIXEL_PNG)
    path.write_bytes(payload)
    return path, payload


def _engine_says(monkeypatch, result, session):
    """Stand in for the engine: one call that returns `result`, one session holding `session`."""
    monkeypatch.setattr(mcp_server.service, "call", lambda *a, **k: result)
    monkeypatch.setattr(mcp_server.service, "get_session", lambda *a, **k: session)
    monkeypatch.setattr(mcp_server, "_DELIVERED_FIGURES", {})


def test_a_drawn_figure_travels_as_an_image_and_not_only_as_a_path(tmp_path, monkeypatch):
    # The product's answer to "plot it" is the picture. The engine hands every chart back with
    # `ui.figure.image_path` — that is how the Studio shows it — but a host that only forwards the
    # JSON text renders nothing, so the user reads a file name where the plot should be.
    monkeypatch.setattr(mcp_server, "_figure_root", lambda: tmp_path)
    path, payload = _png(tmp_path)
    _engine_says(
        monkeypatch,
        {"status": "success", "ui": {"figure": {"image_path": str(path)}}},
        {"figures": [{"image_path": str(path)}]},
    )

    result = mcp_server.call_tool("plot", {"kind": "line"})

    assert result["isError"] is False
    assert result["content"][0]["type"] == "text"
    images = [block for block in result["content"] if block["type"] == "image"]
    assert len(images) == 1, "the same figure must not be sent twice"
    assert images[0]["mimeType"] == "image/png"
    assert base64.b64decode(images[0]["data"]) == payload


def test_the_preview_figures_the_human_chooses_between_are_sent_too(tmp_path, monkeypatch):
    # Measured in the browser run: the engine renders one preview figure per planned chart into
    # `session["figures"]` and asks the human to confirm the package, but its own reply is built
    # with `ui=None` (`research/common.py`), so the carousel of choices reached the conversation as
    # text only. Reading the session is what puts them in front of the person choosing.
    monkeypatch.setattr(mcp_server, "_figure_root", lambda: tmp_path)
    first, _ = _png(tmp_path, "preview-1.png")
    second, _ = _png(tmp_path, "preview-2.png")
    _engine_says(
        monkeypatch,
        {"status": "needs_input", "ui": None, "summary": "Pseudo-data preview v001 is ready"},
        {"figures": [
            {"image_path": str(first), "preview": True, "research_preview": True},
            {"image_path": str(second), "preview": True, "research_preview": True},
        ]},
    )

    result = mcp_server.call_tool("research_plan", {"action": "preview"})

    images = [block for block in result["content"] if block["type"] == "image"]
    assert len(images) == 2, "both candidate layouts belong to the choice the human is making"

    # And only once: the session keeps them, the conversation is shown them once.
    again = mcp_server.call_tool("research_plan", {"action": "status"})
    assert [b for b in again["content"] if b["type"] == "image"] == []


def test_a_figure_path_from_outside_the_state_directory_is_not_read_out(tmp_path, monkeypatch):
    # A tool result is data from a subprocess and a model; if any path in it were read and attached,
    # a result naming ~/.ssh/id_rsa or .env would hand the file to the host.
    monkeypatch.setattr(mcp_server, "_figure_root", lambda: tmp_path / "state")
    (tmp_path / "state").mkdir()
    secret = tmp_path / "secret.png"
    secret.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    _engine_says(
        monkeypatch,
        {"status": "success", "ui": {"figure": {"image_path": str(secret)}}},
        {"figures": [{"image_path": str(secret)}]},
    )

    result = mcp_server.call_tool("plot", {"kind": "line"})

    assert [block["type"] for block in result["content"]] == ["text"]


def test_the_figure_root_is_the_engines_state_directory():
    # Previews live in a session subdirectory of the state directory and results live in
    # `<state>/figures`, so one root covers both.
    from physearth import config

    assert mcp_server._figure_root() == config.state_dir().resolve()


def test_the_session_tool_says_when_a_host_has_to_call_it():
    # Measured, in the browser run of the Studio cover cases: the first case completed a SMRT
    # reproduction and left `research_context.reproduction_case` on the session. The second case
    # ran in the same session, so every plan it proposed was checked against the *previous*
    # question's paper-reproduction targets and refused three times; the agent spent twenty
    # minutes diagnosing it and then opened a new session itself.
    #
    # The description is the only place a model learns the contract, so the rule that prevents
    # that has to live there and has to survive an edit.
    tools = {item["name"]: item for item in _call("tools/list")["tools"]}
    description = tools["geoai_session_new"]["description"]

    assert "new conversation" in description
    assert "first" in description
