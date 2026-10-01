"""A local HTTP bridge: the plugin surface for hosts that are not Python.

DeepSeek Harness plugins are TypeScript, so the engine needs an address they can call.
This is deliberately the smallest thing that works: a loopback-only JSON API over the same
service layer the MCP server uses, with no framework and no state beyond the sessions the
engine already holds.

Two properties are not negotiable here:

- **loopback only.** The bind address defaults to 127.0.0.1 and is refused otherwise unless
  the operator passes `--allow-remote` explicitly, because every endpoint can run a physical
  model and read the bundled corpus.
- **the engine decides.** Validation, the approval gate, quality control and evidence rules
  all stay in the engine; this layer only transports a call and its result, and a refusal is
  returned as a structured result with its own HTTP status so a client cannot mistake it for
  a number. Whether a run waits for a person is chosen with `--approval` when the bridge
  starts; no request body can change it. A run that waits comes back as 202 with the
  pending request, and `/decide` carries the person's verdict.
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from integrations.geoai import service

REFUSED_STATUS = 422
AWAITING_STATUS = 202


def _status_for(payload):
    """Transport status derived from what the engine said, never invented here."""
    if not isinstance(payload, dict):
        return 200
    status = payload.get("status")
    if status == "terminal_error":
        return 400
    if status == "needs_input":
        return REFUSED_STATUS
    if status == "awaiting_approval":
        return AWAITING_STATUS
    return 200


class _Handler(BaseHTTPRequestHandler):
    server_version = "physearth-geoai-bridge"

    def log_message(self, *args):  # keep stdout clean for the plugin host
        return

    def _send(self, payload, status=None):
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status or _status_for(payload))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except ValueError as exc:
            raise ValueError("body is not JSON: %s" % exc) from exc
        return parsed if isinstance(parsed, dict) else {}

    def do_GET(self):
        path = urlparse(self.path).path
        routes = {
            "/health": service.health,
            "/tools": service.tools_manifest,
            "/models": service.models_manifest,
            "/knowledge": service.knowledge_manifest,
            "/sessions": service.sessions,
        }
        if path == "/prompt":
            return self._send({"prompt_stack": service.prompt_stack()})
        handler = routes.get(path)
        if handler is None:
            return self._send({"status": "terminal_error", "error": "unknown_route", "summary": path}, 404)
        try:
            return self._send(handler())
        except Exception as exc:
            return self._send(
                {"status": "terminal_error", "error": "bridge_error", "summary": str(exc)}, 500
            )

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = self._body()
        except ValueError as exc:
            return self._send(
                {"status": "terminal_error", "error": "bad_request", "summary": str(exc)}, 400
            )
        if path == "/session":
            return self._send(service.new_session(model=body.get("model")))
        if path == "/call":
            name = body.get("name")
            if not name:
                return self._send(
                    {"status": "terminal_error", "error": "missing_tool", "summary": "name is required"},
                    400,
                )
            return self._send(
                service.call(
                    name,
                    body.get("arguments") or {},
                    session_id=body.get("session_id"),
                    switches=body.get("switches"),
                )
            )
        if path == "/ask":
            question = body.get("question")
            if not question:
                return self._send(
                    {
                        "status": "terminal_error",
                        "error": "missing_question",
                        "summary": "question is required",
                    },
                    400,
                )
            return self._send(
                service.ask(
                    question,
                    session_id=body.get("session_id"),
                    model=body.get("model"),
                    switches=body.get("switches"),
                )
            )
        if path == "/decide":
            return self._send(service.decide(body.get("session_id"), body.get("decision")))
        if path == "/verify":
            return self._send(service.verify_report(body.get("session_id"), body.get("text", "")))
        if path == "/evidence":
            return self._send(service.evidence(body.get("session_id")))
        if path == "/plan":
            return self._send(service.plan_status(body.get("session_id")))
        if path == "/review":
            return self._send(service.review(body.get("session_id"), body.get("choice")))
        if path == "/session/drop":
            return self._send({"dropped": service.drop_session(body.get("session_id"))})
        return self._send({"status": "terminal_error", "error": "unknown_route", "summary": path}, 404)


def serve(host="127.0.0.1", port=8799, allow_remote=False):
    """Run the bridge. Returns the server so a caller can shut it down."""
    if host not in ("127.0.0.1", "localhost", "::1") and not allow_remote:
        raise SystemExit(
            "refusing to bind %s: every endpoint runs physical models and reads the corpus. "
            "Pass --allow-remote to override deliberately." % host
        )
    server = ThreadingHTTPServer((host, port), _Handler)
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(prog="geoai-bridge", description="PhysEarth-Agent HTTP bridge")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8799)
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument(
        "--approval",
        choices=service.APPROVAL_MODES,
        default=os.environ.get("PHYSEARTH_GEOAI_APPROVAL") or "ask",
    )
    args = parser.parse_args(argv)
    service.configure(approval_mode=args.approval)
    server = serve(args.host, args.port, args.allow_remote)
    print("physearth-geoai bridge on http://%s:%d" % server.server_address[:2], flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
