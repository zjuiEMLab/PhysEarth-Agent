"""The Codex-facing package: a skill, a config snippet, and a script that checks both.

These assertions exist because each artifact fails *quietly* without them. A skill with a
malformed front matter is not loaded and not mentioned; a config key with a typo is ignored by
the client; a tool documented in `references/tools.md` that the server does not publish is a
model calling something that is not there. None of those produce an error a user would see.
"""

from __future__ import annotations


import json
import os
import plistlib
import re
import tomllib
from pathlib import Path

import yaml

from integrations.geoai import mcp_server

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / ".agents" / "skills" / "geoai"
SKILL = SKILL_DIR / "SKILL.md"
CODEX_DIR = ROOT / "integrations" / "codex"

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
    "startup_timeout_ms",
    "tool_timeout_sec",
    "default_tools_approval_mode",
    "tools",
    "experimental_environment",
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
    for phrase in (
        "geoai_health",
        "geoai_evidence",
        "geoai_decide",
        "geoai_verify_report",
        "[abs:doi]",
        "needs_input",
    ):
        assert phrase in body, phrase
    assert "approve_runs" not in body
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
    guide = (CODEX_DIR / "README.md").read_text()

    # A hand-edited config is the thing users get wrong; the guide has to lead with the command
    # that writes it, and mention the file form as the alternative.
    assert "codex mcp add geoai --" in guide
    assert guide.index("codex mcp add geoai --") < guide.index("config.snippet.toml")
    assert "startup_timeout_sec" in guide
    assert "mcp_servers" in guide
    # The one thing it must not do.
    assert "does not write that file for you" in guide or "Nothing here writes that file" in guide


def test_the_doctor_script_is_executable_and_checks_the_engine_before_the_registration():
    script = ROOT / "integrations" / "codex" / "doctor.sh"

    assert script.is_file()
    assert os.access(script, os.X_OK), "the guide tells the reader to run it directly"
    body = script.read_text()
    # Order matters: "no tools" is the symptom, "no interpreter" is the cause.
    assert body.index("tools/list") < body.index("codex mcp list")
    assert "PHYSEARTH_PYTHON" in body


def test_the_shell_scripts_share_one_interpreter_search():
    # This script and `studio.sh` each carried their own candidate list, and both lists were the
    # same wrong shape: `python3` before the conda environments, proved against `import physearth`
    # — whose `__init__` is lazy, so a PyYAML-less interpreter passes and then offers no tools.
    library = ROOT / "integrations" / "lib" / "find-python.sh"
    assert library.is_file() and os.access(library, os.X_OK)
    for name, probe in (
        ("integrations/codex/doctor.sh", "physearth_find_python_for_engine"),
        ("scripts/studio.sh", "physearth_find_python_for_studio"),
        ("integrations/codex/theme-install.sh", '"import plistlib"'),
    ):
        body = (ROOT / name).read_text()
        assert "integrations/lib/find-python.sh" in body, name
        assert probe in body, name
        # The duplicate is gone, not merely bypassed: no script keeps a fallback `python3` loop.
        assert 'for candidate in "${PHYSEARTH_PYTHON:-}"' not in body, name


def test_the_agents_md_snippet_matches_the_skill_on_the_rules_that_matter():
    snippet = (ROOT / "integrations" / "geoai" / "AGENTS.snippet.md").read_text()
    skill = SKILL.read_text()

    # Two documents, one policy: a rule present in one and absent from the other is a model that
    # behaves differently depending on which surface it was loaded through.
    for rule in ("[abs:doi]", "geoai_decide", "geoai_evidence", "geoai_verify_report"):
        assert rule in snippet, f"AGENTS snippet lost {rule}"
        assert rule in skill, f"skill lost {rule}"


# ── the installable bundle (repo marketplace) ────────────────────────────────────────────────

PLUGIN = ROOT / "integrations" / "codex" / "geoai"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _plugin_manifest() -> dict:
    return json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text())


def test_the_plugin_manifest_carries_every_field_the_validator_requires():
    manifest = _plugin_manifest()

    # These are not style: the bundled validator rejects a manifest missing any of them, and a
    # rejected plugin fails at install time with a field list rather than a plugin.
    assert manifest["name"] == PLUGIN.name
    assert SEMVER_RE.fullmatch(manifest["version"]), manifest["version"]
    assert manifest["description"]
    assert manifest["author"]["name"]
    interface = manifest["interface"]
    required_strings = (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
    )
    for field in required_strings:
        assert interface[field], field
    assert isinstance(interface["capabilities"], list) and interface["capabilities"]
    assert interface.get("defaultPrompt") or interface.get("default_prompt")
    assert re.fullmatch(r"#[0-9A-Fa-f]{6}", interface["brandColor"])


def test_every_asset_the_plugin_names_exists():
    interface = _plugin_manifest()["interface"]

    for field in ("composerIcon", "logo", "logoDark"):
        path = interface.get(field)
        if path is not None:
            assert (PLUGIN / path).is_file(), path
    for path in interface.get("screenshots", []):
        assert (PLUGIN / path).is_file(), path


def test_the_plugin_declares_no_mcp_server_and_says_why():
    manifest = _plugin_manifest()
    readme = (PLUGIN / "README.md").read_text()

    # `codex plugin add` copies the plugin into a cache, so a bundled `mcpServers` entry could
    # only reach the engine through a machine-specific absolute path — a manifest that has to be
    # edited per machine is not repository content. The absence is deliberate and the README has
    # to keep explaining it, or the next person "fixes" it and ships a plugin that installs and
    # offers no tools.
    assert "mcpServers" not in manifest
    assert "copies" in readme and "cache" in readme
    assert "codex mcp add geoai --" in readme


def test_the_bundled_skill_is_byte_identical_to_the_repository_one():
    # Two copies exist because two discovery paths exist. A test rather than a symlink: the
    # installer copies the plugin root, so a symlink pointing outside it would arrive broken.
    for relative in ("SKILL.md", "references/tools.md", "references/troubleshooting.md"):
        bundled = (PLUGIN / "skills" / "geoai" / relative).read_bytes()
        assert bundled == (SKILL_DIR / relative).read_bytes(), relative


def test_the_repository_marketplace_points_at_the_plugin_it_catalogues():
    catalog = json.loads(MARKETPLACE.read_text())

    assert catalog["name"] == "physearth-agent"
    assert catalog["interface"]["displayName"]
    entry, = catalog["plugins"]
    assert entry["name"] == PLUGIN.name
    assert entry["source"]["source"] == "local"
    # The path is relative to the marketplace root, i.e. the repository root.
    target = (ROOT / entry["source"]["path"]).resolve()
    assert target == PLUGIN.resolve(), target
    # `policy.installation`, `policy.authentication` and `category` are required on every entry.
    installation = entry["policy"]["installation"]
    assert installation in {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}
    assert entry["policy"]["authentication"] in {"ON_INSTALL", "ON_USE"}
    assert entry["category"]
    installed_name = json.loads((target / ".codex-plugin" / "plugin.json").read_text())["name"]
    assert installed_name == entry["name"]


# ── text and colour: the only surface a CLI plugin has ───────────────────────────────────────

THEME = ROOT / "integrations" / "codex" / "geoai.tmTheme"
THEME_SNIPPET = ROOT / "integrations" / "codex" / "config-theme.snippet.toml"

# Every scope Codex names in its own theme scope list, plus the markdown ones an answer here
# actually uses. A colour scheme that misses one of these leaves that construct at the terminal
# default, which looks like a half-applied theme rather than a missing scope.
THEME_SCOPES_REQUIRED = [
    "comment",
    "keyword",
    "keyword.control",
    "keyword.operator",
    "storage.type",
    "storage.modifier",
    "entity.name.function",
    "entity.name.tag",
    "constant.language",
    "constant.other",
    "markup.heading",
    "markup.underline.link",
    "entity.name.section",
    "markup.inserted",
]


def test_the_theme_is_a_well_formed_plist():
    # A .tmTheme *is* an XML plist, so this is the first thing Codex's parser needs and the first
    # thing that breaks silently in hand-written XML. It caught exactly that while being written:
    # one `<key>guide</string>` made the whole scheme unusable.
    with open(THEME, "rb") as handle:
        theme = plistlib.load(handle)

    assert theme["name"] == "PhysEarth Geo-AI"
    settings = theme["settings"]
    assert isinstance(settings, list) and len(settings) >= 10
    globals_ = [entry for entry in settings if "scope" not in entry]
    assert globals_, "a theme needs one global block for background/foreground"
    for key in ("background", "foreground", "caret", "selection"):
        assert globals_[0]["settings"][key].startswith("#"), key


def test_the_theme_colours_every_scope_codex_emits():
    with open(THEME, "rb") as handle:
        theme = plistlib.load(handle)

    declared = set()
    for entry in theme["settings"]:
        scope = entry.get("scope")
        if isinstance(scope, str):
            declared.update(part.strip() for part in scope.split(","))
    missing = [scope for scope in THEME_SCOPES_REQUIRED if scope not in declared]
    assert not missing, f"scopes left at the terminal default: {missing}"


def test_the_theme_palette_is_the_same_product_as_the_other_integrations():
    with open(THEME, "rb") as handle:
        theme = plistlib.load(handle)
    by_scope = {
        entry["scope"]: entry["settings"]
        for entry in theme["settings"]
        if isinstance(entry.get("scope"), str)
    }
    globals_ = next(entry["settings"] for entry in theme["settings"] if "scope" not in entry)

    # The DSH plugin applies this field and this accent to that surface; two integrations of the
    # same product should not look like two experiments.
    assert globals_["background"] == "#05070D"
    assert globals_["foreground"] == "#E8EEFB"
    assert globals_["caret"] == "#22D3EE"
    # Amber marks what was measured or refused, which is this project's central distinction.
    assert by_scope["constant.other"]["foreground"] == "#F59E0B"


def test_the_theme_snippet_writes_only_keys_that_were_probed():
    data = tomllib.loads(THEME_SNIPPET.read_text())
    tui = data["tui"]

    # These two are the ones an installer can set safely: a string and a boolean. The list-valued
    # keys are deliberately absent — an unknown item id is accepted at load and filtered later, so
    # a wrong id is a silently empty slot, and guessing is worse than pointing at the picker.
    assert tui["theme"] == "geoai"
    assert tui["status_line_use_colors"] is True
    assert "status_line" not in tui
    assert "terminal_title" not in tui
    # The snippet has to record the evidence, or the next reader will "fix" it from memory.
    body = THEME_SNIPPET.read_text()
    assert "accepts a string; rejects a boolean" in body
    assert "/statusline" in body


def test_the_theme_installer_probes_the_theme_before_claiming_success():
    script = (ROOT / "integrations" / "codex" / "theme-install.sh").read_text()

    assert os.access(ROOT / "integrations" / "codex" / "theme-install.sh", os.X_OK)
    # It must validate, must not touch config.toml without being asked, and must say how to undo.
    assert "plistlib" in script
    assert "--write-config" in script
    assert "backed up" in script
    assert "--check" in script
    # A backtick inside the double-quoted block would run as a command substitution; that bug
    # shipped once (`terminal_title: command not found`), so the block is asserted to be free of
    # them.
    block = script.split('block="$BEGIN', 1)[1].split('$END"', 1)[0]
    assert "`" not in block, "backticks inside a double-quoted heredoc run as command substitution"


def test_the_marketplace_entry_carries_what_the_cli_needs_to_install_it():
    # Measured against Codex 0.155.1: `plugin marketplace add` reports the marketplace, and
    # `plugin add` copies the plugin to $CODEX_HOME/plugins/cache/<marketplace>/<plugin>/<version>.
    # There is no `validate` subcommand to lean on, so these are the fields that run proved
    # necessary — a missing `source.source` is the difference between "installed, enabled" and a
    # marketplace that lists nothing.
    catalog = json.loads(MARKETPLACE.read_text())
    entry, = catalog["plugins"]
    manifest = _plugin_manifest()

    assert entry["source"] == {"source": "local", "path": "./integrations/codex/geoai"}
    assert (ROOT / entry["source"]["path"]).resolve() == PLUGIN.resolve()
    # The version the CLI printed in `plugin list` is the manifest's, not the catalogue's.
    assert manifest["version"] == "1.0.0"
    assert entry["policy"]["installation"] == "AVAILABLE"
    assert "version" not in entry, "the manifest is the one place a version lives"
