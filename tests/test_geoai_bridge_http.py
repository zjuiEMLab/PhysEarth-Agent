"""The loopback HTTP bridge a TypeScript plugin calls."""

import json
import threading
import urllib.error
import urllib.request

import pytest

from integrations.geoai import bridge, service


@pytest.fixture()
def bridge_url():
    server = bridge.serve("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield "http://%s:%d" % (host, port)
    finally:
        server.shutdown()
        server.server_close()


def _get(url, path):
    try:
        with urllib.request.urlopen(url + path, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _post(url, path, payload):
    request = urllib.request.Request(
        url + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_health_and_catalogues_are_readable(bridge_url):
    status, health = _get(bridge_url, "/health")
    assert status == 200
    assert health["models"] == 6

    _, tools = _get(bridge_url, "/tools")
    assert any(item["name"] == "run_model" for item in tools)

    _, prompt = _get(bridge_url, "/prompt")
    assert len(prompt["prompt_stack"]) > 4000


def test_a_run_over_http_waits_for_a_verdict_then_returns_a_handle(bridge_url):
    _, session = _post(bridge_url, "/session", {"model": "smrt", "approve_runs": True})
    assert session["approval"] == "ask"

    status, run = _post(
        bridge_url,
        "/call",
        {
            "session_id": session["session_id"],
            "name": "run_model",
            "model": "smrt",
            "arguments": {
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

    assert status == 202
    assert run["status"] == "awaiting_approval"
    assert run["pending"]["description"]["model"] == "smrt"

    status, run = _post(
        bridge_url, "/decide", {"session_id": session["session_id"], "decision": "approve"}
    )
    assert status == 200
    assert run["status"] == "success"
    handle = run["data"]["handle"]

    _, evidence = _post(bridge_url, "/evidence", {"session_id": session["session_id"]})
    assert any(item["handle"] == handle for item in evidence["handles"])


def test_a_refusal_keeps_its_own_http_status(bridge_url, monkeypatch):
    monkeypatch.setitem(service._OPERATOR, "approval", "always")
    _, session = _post(bridge_url, "/session", {"model": "smrt"})

    status, refused = _post(
        bridge_url,
        "/call",
        {
            "session_id": session["session_id"],
            "name": "run_model",
            "arguments": {"model": "smrt", "parameters": {"density_kg_m3": 2000.0}},
        },
    )

    assert status == 422
    assert refused["status"] == "needs_input"
    assert "density" in refused["error"].lower()


def test_unknown_routes_and_missing_arguments_are_named(bridge_url):
    status, payload = _get(bridge_url, "/nope")
    assert status == 404 and payload["error"] == "unknown_route"

    status, payload = _post(bridge_url, "/call", {})
    assert status == 400 and payload["error"] == "missing_tool"

    status, payload = _post(bridge_url, "/ask", {})
    assert status == 400 and payload["error"] == "missing_question"


def test_a_missing_credential_is_a_structured_refusal(bridge_url, monkeypatch):
    monkeypatch.setattr(service.config, "has_token", lambda: False)
    monkeypatch.setattr(service.config, "get", lambda name, default="": default)

    status, payload = _post(bridge_url, "/ask", {"question": "How bright is snow at 37 GHz?"})

    assert status == 400
    assert payload["error"] == "no_credentials"


def test_binding_a_public_interface_needs_an_explicit_opt_in():
    with pytest.raises(SystemExit):
        bridge.serve("0.0.0.0", 0)


def test_a_report_is_verified_against_the_session(bridge_url):
    _, session = _post(bridge_url, "/session", {})

    status, report = _post(
        bridge_url, "/verify", {"session_id": session["session_id"], "text": "See [smrt-v1#03]."}
    )

    assert status == 200
    assert report["passed"] is False
    assert report["checks"][1]["unresolved"] == ["smrt-v1#03"]
