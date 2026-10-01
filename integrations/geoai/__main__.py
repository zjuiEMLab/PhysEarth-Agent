"""Command line entry point: the same surface the plugins use, for a human or a script.

`serve` speaks MCP on stdio and is what a coding-agent host launches; the rest exist so the
capabilities, the knowledge and one call can be inspected without a host in the loop.
"""

from __future__ import annotations

import argparse
import json
import sys

from integrations.geoai import bridge, mcp_server, service


def _emit(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="geoai", description="PhysEarth-Agent plugin surface")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health", help="what this checkout can do")
    sub.add_parser("tools", help="the declared tool catalogue")
    sub.add_parser("models", help="registered models and their declarations")
    sub.add_parser("knowledge", help="bundled papers, method notes and datasets")
    prompt_cmd = sub.add_parser("prompt", help="the prompt stack the agent is given")
    prompt_cmd.add_argument(
        "--scopes",
        default=",".join(service.PROMPT_SCOPES),
        help=(
            "comma-separated: %s (default: all). `rules` is the group that changes what a model "
            "does without replacing the host's identity." % ",".join(service.PROMPT_SCOPES)
        ),
    )
    prompt_cmd.add_argument("--list", action="store_true", help="print the scopes and their sizes")
    sub.add_parser("serve", help="serve MCP on stdio")

    http = sub.add_parser("serve-http", help="serve the loopback HTTP bridge")
    http.add_argument("--host", default="127.0.0.1")
    http.add_argument("--port", type=int, default=8799)
    http.add_argument("--allow-remote", action="store_true")

    call = sub.add_parser("call", help="run one declared tool")
    call.add_argument("name")
    call.add_argument("--arguments", default="{}", help="JSON object")
    call.add_argument("--session-id", default=None)
    call.add_argument("--approve-runs", action="store_true")

    ask = sub.add_parser("ask", help="run one agent turn")
    ask.add_argument("question")
    ask.add_argument("--session-id", default=None)
    ask.add_argument("--model", default=None)
    ask.add_argument("--approve-runs", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "health":
        _emit(service.health())
    elif args.command == "tools":
        _emit(service.tools_manifest())
    elif args.command == "models":
        _emit(service.models_manifest())
    elif args.command == "knowledge":
        _emit(service.knowledge_manifest())
    elif args.command == "prompt":
        scopes = [scope.strip() for scope in args.scopes.split(",") if scope.strip()]
        if args.list:
            sections = service.prompt_sections()
            _emit(
                {
                    "scopes": list(service.PROMPT_SCOPES),
                    "sections": {
                        scope: {
                            "chars": len("\n\n".join(block.strip() for block in blocks if block and block.strip())),
                            "blocks": len(blocks),
                        }
                        for scope, blocks in sections.items()
                    },
                }
            )
        else:
            sys.stdout.write(service.prompt_stack(scopes) + "\n")
    elif args.command == "serve":
        # `argv=[]`, not `argv=None`: this subcommand has already consumed the word `serve`, and
        # leaving it in `sys.argv` made the server warn about "unrecognised argument(s): serve"
        # on every launch by a host that spells the invocation `-m integrations.geoai serve`.
        mcp_server.main([])
    elif args.command == "serve-http":
        argv = ["--host", args.host, "--port", str(args.port)]
        if args.allow_remote:
            argv.append("--allow-remote")
        bridge.main(argv)
    elif args.command == "call":
        _emit(
            service.call(
                args.name,
                json.loads(args.arguments),
                session_id=args.session_id,
                approve_runs=args.approve_runs,
            )
        )
    elif args.command == "ask":
        _emit(
            service.ask(
                args.question,
                session_id=args.session_id,
                model=args.model,
                approve_runs=args.approve_runs,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
