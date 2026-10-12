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
    body = (ROOT / "integrations" / "scripts" / "install-dsh.sh").read_text()

    # Sourced after the checkout is known, because the library lives in the checkout.
    assert '. "$CHECKOUT/scripts/find-python.sh"' in body
    assert "physearth_find_python_for_engine" in body
    # The private copy is gone rather than left as a fallback beside the shared one.
    assert "resolve_python" not in body
    assert 'for candidate in "${PHYSEARTH_PYTHON:-}"' not in body


def test_the_shared_library_answers_the_probe_this_branch_needs():
    library = ROOT / "scripts" / "find-python.sh"
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
    assert "scripts/find-python.sh" in studio
    assert "physearth_find_python_for_studio" in studio


# ── the patch-block writer ────────────────────────────────────────────────────────────────────
# Extracted from the installer's shell heredoc into `integrations/scripts/merge-patch-block.py`
# because it has the edge cases and needs no harness, profile or package manager to test. Both
# bugs below were found by a real boot refusing the profile, not by reading the code.

sys.path.insert(0, str(ROOT / "integrations" / "scripts"))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "merge_patch_block", ROOT / "integrations" / "scripts" / "merge-patch-block.py"
)
merge_patch_block = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(merge_patch_block)

BUNDLE = ROOT / "integrations" / "dsh" / "cordis.patch.yml"
OLD_BLOCK = (
    "# The profile's own layer.\n[]\n\n"
    "# >>> physearth-geoai (written by integrations/dsh/scripts/install.sh)\n"
    "- id: geoai\n  config:\n    enabled: false\n"
    "# <<< physearth-geoai\n"
)


def _merged(current: str) -> tuple[str, str]:
    rows = merge_patch_block.rows_for(BUNDLE, "/repo", "/opt/python")
    return merge_patch_block.merge(current, merge_patch_block.block_for(rows))


def test_the_block_writer_replaces_an_older_block_instead_of_adding_a_second():
    # Matched by prefix: the sentinel used to carry the installer's path in parentheses, so a
    # profile installed by the previous layout has a BEGIN line that no longer matches exactly.
    updated, action = _merged(OLD_BLOCK)

    assert action == "replaced"
    assert updated.count(merge_patch_block.BEGIN) == 1
    assert "written by" not in updated, "the old parenthetical is gone, not left behind"
    assert "/somewhere" not in updated


def test_the_block_writer_leaves_one_yaml_document():
    # The bug this pins: a file holding both the placeholder `[]` and a block used to come out as
    # two documents — `[]` then a list — and the harness refused the whole profile with a parse
    # error at the block's first line.
    import yaml

    updated, _ = _merged(OLD_BLOCK)
    parsed = yaml.safe_load(updated)

    assert isinstance(parsed, list), "one document, not a document per fragment"
    assert [row["id"] for row in parsed] == ["geoai", "mcp-geoai"]
    assert parsed[0]["config"]["projectRoot"] == "/repo"
    assert parsed[1]["config"]["command"] == "/opt/python"
    # And the bundle patch is the one description of each row, so nothing else was dropped.
    assert parsed[1]["config"]["serverName"] == "geoai"
    assert parsed[1]["config"]["env"]["PYTHONPATH"] == "/repo/backend:/repo"


def test_the_block_writer_is_idempotent_and_keeps_data_that_looks_like_a_placeholder():
    # Running the installer twice leaves one block, not two.
    once, _ = _merged(OLD_BLOCK)
    twice, action = _merged(once)
    assert action == "replaced"
    assert twice == once

    # A `[]` that is somebody's data — an empty id list inside a real row — is not a placeholder.
    with_data = (
        "- id: geoai\n  config:\n    enabled: false\n    tags: []\n"
    )
    kept, _ = _merged(with_data)
    assert "tags: []" in kept, "only the whole-document placeholder is removed"
