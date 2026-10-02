"""What this branch has to get right that the other two do not.

The DSH plugin is the only integration that runs the engine as a *row inside a host*, so it is
the only one where the interpreter is decided by an installer rather than by the user's shell.
That makes the shared interpreter search load-bearing here in a way it is not elsewhere, and it
makes the file form of the MCP server — which is what every other host's documentation shows —
worth actually running rather than merely reading.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "integrations" / "dsh"
SERVER = ROOT / "integrations" / "geoai" / "mcp_server.py"


def test_the_installer_uses_the_shared_interpreter_search():
    body = (PLUGIN / "scripts" / "install.sh").read_text()

    # Sourced after the checkout is known, because the library lives in the checkout.
    assert '. "$CHECKOUT/integrations/lib/find-python.sh"' in body
    assert "physearth_find_python_for_engine" in body
    # The private copy is gone rather than left as a fallback beside the shared one.
    assert "resolve_python" not in body
    assert 'for candidate in "${PHYSEARTH_PYTHON:-}"' not in body


def test_the_shared_library_answers_the_probe_this_branch_needs():
    library = ROOT / "integrations" / "lib" / "find-python.sh"
    assert library.is_file() and os.access(library, os.X_OK)

    # The engine, not `physearth`: that package's `__init__` is lazy, so an interpreter with no
    # PyYAML passes the weaker probe and then mounts a row with an empty tool list.
    probe = subprocess.run(
        ["bash", "-c", f'. "{library}"; physearth_find_python_for_engine "{ROOT}"'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert probe.returncode == 0, probe.stderr
    interpreter = probe.stdout.strip()
    assert Path(interpreter).is_absolute(), interpreter
    again = subprocess.run(
        [interpreter, "-c", "from integrations.geoai import service"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert again.returncode == 0, again.stderr


def test_the_server_runs_as_a_file_from_an_unrelated_directory(tmp_path):
    # Why this branch cares: its own row invokes `python -m integrations.geoai serve` with a
    # `cwd` and a `PYTHONPATH` written into the profile patch, so the file form is never
    # exercised by the plugin itself. A reader who copies the file form out of any other host's
    # guide would get `ModuleNotFoundError` and a server that "starts but has no tools".
    requests = "\n".join(
        [
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                }
            ),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
            "",
        ]
    )
    # An environment with nothing in it: no PYTHONPATH, no PHYSEARTH_ROOT, no cwd on sys.path.
    run = subprocess.run(
        [sys.executable, str(SERVER), "--stdio"],
        cwd=tmp_path,
        input=requests,
        capture_output=True,
        text=True,
        env={"PATH": os.environ.get("PATH", "")},
        timeout=120,
        check=False,
    )
    replies = [json.loads(line) for line in run.stdout.splitlines() if line.strip()]
    assert [reply["id"] for reply in replies] == [1, 2], run.stdout + run.stderr
    assert replies[0]["result"]["serverInfo"]["name"] == "physearth-geoai"
    assert len(replies[1]["result"]["tools"]) >= 28
    # `--stdio` is what every host's guide spells; it must be accepted, not argued with.
    assert "unrecognised argument" not in run.stdout


def test_the_studio_launcher_is_here_and_does_not_reimplement_the_search():
    for name in ("scripts/studio.sh", "start-local.command"):
        path = ROOT / name
        assert path.is_file(), name
        assert os.access(path, os.X_OK), name
    studio = (ROOT / "scripts" / "studio.sh").read_text()
    assert "integrations/lib/find-python.sh" in studio
    assert "physearth_find_python_for_studio" in studio
