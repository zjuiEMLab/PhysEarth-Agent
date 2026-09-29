"""The Claude Code package: a manifest, a skill, an output style, a theme, a status line.

Every assertion here is for something that fails *quietly* on this surface. Claude Code strips an
unknown top-level manifest key with a warning, ignores a theme token it does not know, and accepts
an MCP entry that cannot start — `claude plugin install` then reports success and the session has
no tools. None of that raises, so it has to be asserted.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "geoai-claude"
MANIFEST = PLUGIN / ".claude-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
STATUSLINE = PLUGIN / "scripts" / "statusline.py"
SKILL = PLUGIN / "skills" / "geoai" / "SKILL.md"

# Every key Claude Code documents for plugin.json. A key outside this set is stripped at load with
# a warning nobody reads, so it is a typo that looks like a feature.
MANIFEST_KEYS = {
    "$schema", "name", "displayName", "version", "description", "author", "homepage",
    "repository", "license", "keywords", "defaultEnabled", "dependencies", "settings",
    "userConfig", "channels", "skills", "commands", "agents", "hooks", "mcpServers",
    "lspServers", "outputStyles", "workflows", "experimental",
}

# The alias tokens Claude Code's theme documentation names. A token outside this set is ignored in
# silence: the theme loads, and that one colour stays at the built-in value.
THEME_TOKENS = {
    "claude", "text", "inverseText", "inactive", "subtle", "suggestion", "permission",
    "remember", "success", "error", "warning", "merged", "promptBorder", "planMode",
    "autoAccept",
}
THEME_VALUE_FORMS = re.compile(r"^(#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}|rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)|ansi256\(\d+\)|ansi:[a-z-]+)$")


def manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_the_manifest_uses_only_keys_claude_code_reads():
    data = manifest()

    assert data["name"] == "geoai-claude"
    unknown = set(data) - MANIFEST_KEYS
    assert not unknown, f"keys Claude Code strips: {sorted(unknown)}"
    # `name` is the only required field; the rest is what a reader needs to trust the package.
    assert data["version"] and re.fullmatch(r"\d+\.\d+\.\d+", data["version"])
    assert data["description"] and data["author"]["name"]
    # `homepage` must parse as a URL or the plugin fails to load outright.
    assert data["homepage"].startswith("https://")


def test_the_theme_is_declared_where_claude_code_reads_it():
    data = manifest()

    # Top-level `themes` loads but warns that it "will be removed in a future release".
    assert "themes" not in data
    assert data["experimental"]["themes"] == "./themes/"
    assert data["outputStyles"] == "./output-styles/"
    assert data["skills"] == "./skills/"


def test_the_plugin_declares_no_mcp_server_and_the_readme_says_why():
    data = manifest()
    readme = (PLUGIN / "README.md").read_text()

    # `claude plugin install` copies the plugin into a cache, so a bundled entry could only reach
    # the engine by an absolute path. The relative form was measured: "✗ Failed to connect" — a
    # plugin that installs cleanly and offers no tools. The absence is deliberate.
    assert "mcpServers" not in data
    assert not (PLUGIN / ".mcp.json").exists()
    assert "Failed to connect" in readme
    assert "cache" in readme


def test_the_theme_only_names_tokens_that_exist():
    theme = json.loads((PLUGIN / "themes" / "geoai-night.json").read_text())

    assert theme["base"] == "dark"
    overrides = theme["overrides"]
    unknown = set(overrides) - THEME_TOKENS
    assert not unknown, f"tokens Claude Code ignores silently: {sorted(unknown)}"
    for token, value in overrides.items():
        assert THEME_VALUE_FORMS.match(value), f"{token}: {value}"
    # The same palette as the Codex theme and the DSH plugin, not a third one.
    assert overrides["claude"] == "#22D3EE"
    assert overrides["permission"] == "#F59E0B"


def test_the_output_style_forces_itself_on_and_keeps_the_coding_instructions():
    body = (PLUGIN / "output-styles" / "geoai-brief.md").read_text()

    assert body.startswith("---\n")
    front, _, prose = body[4:].partition("\n---")
    fields = dict(
        line.split(":", 1) for line in front.strip().splitlines() if ":" in line
    )
    fields = {key.strip(): value.strip() for key, value in fields.items()}

    assert fields["name"] == "geoai-brief"
    # The only mechanism that changes every response's text with no user action...
    assert fields["force-for-plugin"] == "true"
    # ...while leaving ordinary engineering behaviour in place: this adds claim discipline, it
    # does not remove the ability to write code.
    assert fields["keep-coding-instructions"] == "true"
    for rule in ("[abs:doi]", "approve_runs", "needs_input"):
        assert rule in prose, rule


def test_the_skill_is_the_same_one_the_codex_plugin_ships():
    # Two copies for two discovery paths; a drifted copy is a model that behaves differently
    # depending on the host. (The Codex copy is on its own branch, so this compares against the
    # repository-scoped copy when it exists and otherwise just checks the shape.)
    assert SKILL.is_file()
    text = SKILL.read_text()
    assert text.startswith("---\n")
    assert "name: geoai" in text.split("---", 2)[1]
    sibling = ROOT / ".agents" / "skills" / "geoai" / "SKILL.md"
    if sibling.is_file():
        assert text == sibling.read_text()
    for reference in re.findall(r"references/[a-z_-]+\.md", text):
        assert (SKILL.parent / reference).is_file(), reference


def run_statusline(payload: dict, env: dict | None = None) -> str:
    process = subprocess.run(
        [sys.executable, str(STATUSLINE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, **(env or {})},
    )
    assert process.returncode == 0, process.stderr
    return process.stdout


def test_the_status_line_prints_one_coloured_row():
    out = run_statusline(
        {
            "model": {"display_name": "Sonnet 4.6"},
            "output_style": {"name": "geoai-claude:geoai-brief"},
            "context_window": {"used_percentage": 37},
        },
        env={"FORCE_COLOR": "1", "COLORTERM": "truecolor", "NO_COLOR": ""},
    )

    assert out.count("\n") == 1, "Claude Code renders one row per printed line"
    assert "\033[38;2;" in out, "the row carries true-colour escapes"
    assert "PhysEarth Geo-AI" in out
    # The context reading is text as well as colour, never colour alone.
    assert "ctx 63% left" in out


def test_colour_precedence_is_the_one_the_conventions_specify():
    payload = {"model": {"display_name": "M"}}
    # An explicit request wins, including over an inherited NO_COLOR — which is the ambient
    # environment of the harness this was written in, and it silently disabled the colour until
    # the precedence was fixed.
    assert "\033[" in run_statusline(payload, env={"FORCE_COLOR": "1", "NO_COLOR": "1", "TERM": "xterm"})
    # The standing opt-out is honoured whatever its value.
    for value in ("1", "", "0"):
        assert "\033[" not in run_statusline(payload, env={"NO_COLOR": value, "FORCE_COLOR": ""})
    # A terminal that cannot do it, and a pipe, both mean plain text.
    assert "\033[" not in run_statusline(payload, env={"NO_COLOR": "", "FORCE_COLOR": "", "TERM": "dumb"})


def test_the_status_line_degrades_on_every_shape_it_does_not_know():
    # An empty payload, a wrong-typed payload and an unknown context shape must all produce a
    # line rather than a traceback: a status line that raises leaves a blank row and no clue.
    for payload in ({}, {"model": "a string"}, {"context_window": {"anything": 1}}, {"context_window": None}):
        out = run_statusline(payload, env={"NO_COLOR": "1"})
        assert out.endswith("\n")
        assert "\033[" not in out, "NO_COLOR must mean plain text"
        assert "PhysEarth Geo-AI" in out


def test_the_status_line_thresholds_context_in_three_steps():
    def ctx(used: int) -> str:
        return run_statusline({"context_window": {"used_percentage": used}}, env={"NO_COLOR": "1"}).strip()

    assert "ctx 80% left" in ctx(20)
    assert "ctx 30% left" in ctx(70)
    assert "ctx 5% left" in ctx(95)


def test_the_marketplace_points_at_the_plugin_it_catalogues():
    catalog = json.loads(MARKETPLACE.read_text())

    assert catalog["name"] == "physearth-agent"
    assert catalog["owner"]["name"]
    entry, = catalog["plugins"]
    assert entry["name"] == PLUGIN.name
    target = (ROOT / entry["source"]).resolve()
    assert target == PLUGIN.resolve(), target
    assert json.loads((target / ".claude-plugin" / "plugin.json").read_text())["name"] == entry["name"]


def test_the_installer_proves_the_interpreter_and_is_reversible():
    script = (ROOT / "scripts" / "claude-plugin-install.sh").read_text()

    assert os.access(ROOT / "scripts" / "claude-plugin-install.sh", os.X_OK)
    # It must prove the engine imports, register the server by absolute path, back the settings up
    # before writing them, and offer a read-only mode.
    assert "physearth_find_python_for_engine" in script
    assert "claude mcp add geoai" in script
    assert "backed up" in script
    assert "--check" in script
    assert "--plugin-only" in script


def test_every_script_sources_the_shared_interpreter_search():
    # The same discovery bug was written three times — PATH finds a python3 without the scientific
    # stack, and the failure is always silent. One implementation, sourced, is the fix.
    library = ROOT / "scripts" / "lib" / "find-python.sh"
    assert library.is_file()
    body = library.read_text()
    assert "physearth_find_python_for_engine" in body
    assert "conda info --base" in body, "asking conda beats guessing a home directory"
    for script in ("claude-plugin-install.sh",):
        text = (ROOT / "scripts" / script).read_text()
        assert "scripts/lib/find-python.sh" in text, script


def test_the_studio_launcher_is_here_too_and_uses_the_same_search():
    # "The plugin must carry the whole project" includes the way the project is started. The
    # launcher that existed only on the Codex branch failed on `python app.py` for the two reasons
    # its header names, so it belongs on every branch and must not re-implement the search.
    launcher = ROOT / "scripts" / "studio.sh"
    assert launcher.is_file() and os.access(launcher, os.X_OK)
    body = launcher.read_text()
    assert "scripts/lib/find-python.sh" in body
    assert "physearth_find_python_for_studio" in body
    assert "PYTHONPATH=backend" in body, "the package lives under backend/"
    wrapper = ROOT / "start-local.command"
    assert wrapper.is_file() and os.access(wrapper, os.X_OK)
    assert "scripts/studio.sh" in wrapper.read_text(), "one implementation, not a second copy"


def test_the_settings_half_resolves_its_interpreter_before_the_read_only_path():
    # `--check` reads the settings file with PYTHON_BIN. When that assignment sat below the branch,
    # `set -u` turned the report into "unbound variable" — a crash in the one mode that exists to
    # keep working on a broken install. Order is the assertion, so it is asserted positionally.
    script = (ROOT / "scripts" / "claude-plugin-install.sh").read_text()
    assignment = script.index('PYTHON_BIN=')
    read_only = script.index('if [ "$CHECK" = "1" ]; then')
    assert assignment < read_only
    # And the status line names the interpreter that was proved, shlex-quoted because a checkout
    # path may contain spaces; `python3` is exactly the interpreter the search exists to distrust.
    assert 'command": f"{shlex.quote(python_bin)} {shlex.quote(statusline)}"' in script
    assert script.count('PYTHON_BIN=') == 1, "assigned once, before it is used"


def test_the_server_can_be_run_as_a_file_without_cwd_or_pythonpath():
    # This is what makes the installer's one command enough. A file run gets its own directory on
    # sys.path, finding neither `integrations` nor `physearth`, so the file adds both roots itself.
    source = (ROOT / "integrations" / "geoai" / "mcp_server.py").read_text()
    assert "_bootstrap_path" in source
    assert "if __package__ in (None, \"\"):" in source


def test_the_manifest_and_the_marketplace_entry_describe_the_same_plugin():
    # This is the check `claude plugin tag --dry-run` makes, and it is the one `validate` cannot:
    # a manifest and a catalogue entry that disagree on name or version produce a tag pointing at
    # something other than what a user installs. Measured: both commands pass on this tree.
    data = manifest()
    entry = next(
        item
        for item in json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())["plugins"]
        if item["name"] == data["name"]
    )
    assert (ROOT / entry["source"]).resolve() == PLUGIN.resolve()
    # Only `name` and `source` are required in an entry; a version here would have to be kept in
    # step with the manifest by hand, and `tag` reads the manifest when it is absent.
    assert entry.get("version", data["version"]) == data["version"]


def test_the_plugin_declares_no_settings_block_because_only_two_keys_survive():
    # Claude Code filters a plugin's `settings` down to `agent` and `subagentStatusLine`; every
    # other key is dropped without an error. Declaring one would look like configuration and
    # configure nothing, so the theme and the status line are written by the installer instead.
    assert "settings" not in manifest()


def test_the_theme_id_is_the_prefixed_form_claude_code_resolves():
    # A plugin *supplies* a theme; it cannot activate one, and the id a session resolves is
    # `custom:<plugin-name>:<slug>`. The installer builds that from the manifest name rather than
    # from a literal, so renaming the plugin cannot leave a theme id pointing at nothing.
    installer = (ROOT / "scripts" / "claude-plugin-install.sh").read_text()

    assert 'PLUGIN_NAME="geoai-claude"' in installer
    assert 'f"custom:{plugin}:geoai-night"' in installer
    assert 'settings.json' in installer and 'backed up' in installer
