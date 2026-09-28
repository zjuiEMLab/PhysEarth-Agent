"""The Codex-facing package: a skill, a config snippet, and a script that checks both.

These assertions exist because each artifact fails *quietly* without them. A skill with a
malformed front matter is not loaded and not mentioned; a config key with a typo is ignored by
the client; a tool documented in `references/tools.md` that the server does not publish is a
model calling something that is not there. None of those produce an error a user would see.
"""

from __future__ import annotations


import os
import re
import tomllib
from pathlib import Path

import yaml

from integrations.geoai import mcp_server

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / ".agents" / "skills" / "geoai"
SKILL = SKILL_DIR / "SKILL.md"
CODEX_DIR = ROOT / "codex"

# Every key Codex 0.155.1 documents for `mcp_servers.<name>`. A key outside this set is a typo
# the client silently ignores, which is exactly the failure this test is for.
MCP_SERVER_KEYS = {
    "command",
    "args",
    "env",
    "cwd",
    "enabled",
    "required",
    "env_vars",
    "enabled_tools",
    "disabled_tools",
    "startup_timeout_sec",
    "tool_timeout_sec",
    "default_tools_approval_mode",
    "tools",
}


def _front_matter(text: str) -> dict:
    assert text.startswith("---\n"), "front matter must open the file"
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


def _mcp_tool_names() -> set[str]:
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    return {item["name"] for item in mcp_server.handle(request)["result"]["tools"]}


def test_the_skill_is_where_codex_looks_for_a_repository_skill():
    # Codex searches $CWD/.agents/skills up to the repository root, so this path is what makes
    # the skill discoverable without any install step. `codex debug prompt-input` was used to
    # confirm it is listed to the model from this location on 0.155.1.
    assert SKILL.is_file(), SKILL
    assert SKILL_DIR.name == "geoai"
    assert (SKILL_DIR / "references").is_dir()


def test_the_skill_front_matter_carries_a_name_and_a_triggering_description():
    matter = _front_matter(SKILL.read_text())

    assert matter["name"] == "geoai"
    # Required by the loader; also the only thing the model sees before deciding to open the file.
    assert isinstance(matter["description"], str)
    assert len(matter["description"]) > 200
    # The trigger vocabulary has to be in the description, not only in the body.
    for word in ("SMRT", "PROSAIL", "soil moisture", "snow", "microwave"):
        assert word.lower() in matter["description"].lower(), word
    # And the boundary, so a general programming question does not open this skill.
    assert "Does not do" in matter["description"]


def test_every_document_the_skill_points_at_exists():
    body = SKILL.read_text()

    for reference in re.findall(r"references/[a-z_-]+\.md", body):
        assert (SKILL_DIR / reference).is_file(), reference


def test_the_skill_states_the_rules_the_engine_actually_enforces():
    body = SKILL.read_text()

    # Each of these is a guarantee in the engine, so an omission here is a model that will
    # confidently break one.
    for phrase in ("geoai_health", "geoai_evidence", "approve_runs", "[abs:doi]", "needs_input"):
        assert phrase in body, phrase
    assert "comes from a tool result" in body


def test_the_tool_reference_names_only_tools_the_server_publishes():
    reference = (SKILL_DIR / "references" / "tools.md").read_text()
    documented = set(re.findall(r"^\| `([a-z_]+)` \|", reference, re.M))

    published = _mcp_tool_names()
    assert documented, "the reference lists no tools"
    missing = sorted(documented - published)
    assert not missing, f"documented but not published: {missing}"
    # And the reference is not silently missing most of the catalogue.
    assert len(documented) >= len(published) - 2, sorted(published - documented)


def test_the_openai_metadata_is_parseable_and_its_assets_exist():
    meta = yaml.safe_load((SKILL_DIR / "agents" / "openai.yaml").read_text())

    interface = meta["interface"]
    assert interface["display_name"]
    assert re.fullmatch(r"#[0-9A-Fa-f]{6}", interface["brand_color"])
    for key in ("icon_small", "icon_large"):
        assert (SKILL_DIR / interface[key]).is_file(), interface[key]
    # The dependency names the MCP server the skill expects, which is what ties the two halves
    # together on a surface that has no other way to express it.
    dependency = meta["dependencies"]["tools"][0]
    assert dependency["type"] == "mcp"
    assert dependency["value"] == "geoai"


def test_the_config_snippet_uses_the_key_codex_reads_and_no_invented_keys():
    data = tomllib.loads((CODEX_DIR / "config.snippet.toml").read_text())

    assert "mcp_servers" in data, "the key is mcp_servers, never mcpServers"
    assert "mcpServers" not in data
    server = data["mcp_servers"]["geoai"]
    unknown = set(server) - MCP_SERVER_KEYS
    assert not unknown, f"keys Codex does not read: {sorted(unknown)}"
    for required in ("command", "args", "cwd", "startup_timeout_sec", "tool_timeout_sec"):
        assert required in server, required


def test_the_config_snippet_does_not_promise_a_python_that_does_not_exist():
    server = tomllib.loads((CODEX_DIR / "config.snippet.toml").read_text())["mcp_servers"]["geoai"]

    # A bare `python` is the hazard: it is absent on macOS and on most Linux distributions, and a
    # server pointed at a missing or dependency-free interpreter starts and offers an empty tool
    # list, which reads as "the plugin does nothing". An absolute path — a virtualenv's
    # `bin/python` included — is the fix, so absolute-ness is what is asserted.
    assert os.path.isabs(server["command"]), server["command"]
    assert server["command"].startswith("/absolute/path") or "/" in server["command"]
    assert "--stdio" in server["args"]
    assert server["args"][0].endswith("integrations/geoai/mcp_server.py")
    # A scientific Python import exceeds the 10 s default.
    assert server["startup_timeout_sec"] >= 30
    assert server["tool_timeout_sec"] >= 120


def test_the_install_guide_keeps_the_cli_command_primary():
    guide = (CODEX_DIR / "install-codex.md").read_text()

    # A hand-edited config is the thing users get wrong; the guide has to lead with the command
    # that writes it, and mention the file form as the alternative.
    assert "codex mcp add geoai --" in guide
    assert guide.index("codex mcp add geoai --") < guide.index("config.snippet.toml")
    assert "startup_timeout_sec" in guide
    assert "mcp_servers" in guide
    # The one thing it must not do.
    assert "does not write that file for you" in guide or "Nothing here writes that file" in guide


def test_the_doctor_script_is_executable_and_checks_the_engine_before_the_registration():
    script = ROOT / "scripts" / "codex-doctor.sh"

    assert script.is_file()
    assert os.access(script, os.X_OK), "the guide tells the reader to run it directly"
    body = script.read_text()
    # Order matters: "no tools" is the symptom, "no interpreter" is the cause.
    assert body.index("tools/list") < body.index("codex mcp list")
    assert "PHYSEARTH_PYTHON" in body


def test_the_agents_md_snippet_matches_the_skill_on_the_rules_that_matter():
    snippet = (ROOT / "integrations" / "geoai" / "AGENTS.snippet.md").read_text()
    skill = SKILL.read_text()

    # Two documents, one policy: a rule present in one and absent from the other is a model that
    # behaves differently depending on which surface it was loaded through.
    for rule in ("[abs:doi]", "approve_runs", "geoai_evidence"):
        assert rule in snippet, f"AGENTS snippet lost {rule}"
        assert rule in skill, f"skill lost {rule}"
