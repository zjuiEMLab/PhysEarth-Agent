#!/usr/bin/env python3
"""Write this plugin's two rows into a DeepSeek Harness profile's patch layer.

Called by `install-dsh.sh`, and separate from it because this is the part that can be tested
without a harness, a profile, or a package manager — and because it has already been wrong twice
in ways only a real boot exposed.

Two facts shape it.

**A row's `config` is replaced, not merged.** The harness composes patch layers with a shallow
per-entry assignment, so a layer that names one field of `config` gives the row that field and
nothing else. An earlier revision wrote a partial override and silently stripped `serverName` and
`args` off the MCP row; the loader then refused the whole tree. So both rows are read back out of
the bundle patch — one description of each row, in the repository — and completed here with the
two answers only this machine has: the interpreter it proved, and the checkout it resolved.

**A patch list is one YAML document.** The block is written inside sentinel comments so a human
can find and delete it. An earlier revision replaced the block in place, which broke the case
where a profile file holds both the placeholder `[]` and an existing block: the result parsed as
two documents and the harness refused the profile with a parse error at the block's first line.
So the order is now: remove any existing block, drop a placeholder, append one fresh block.

Usage:

    merge-patch-block.py <patch.yml> <bundle-patch.yml> <checkout> <python> [--dry-run]

Exit status 0 when the file was written, 1 when it could not be read or parsed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

BEGIN = "# >>> physearth-geoai"
END = "# <<< physearth-geoai"

HEADER = """# Id-targeted overrides for this plugin's two rows. Complete, not partial: the harness composes
# patch layers with a shallow per-entry assignment, so a `config` here REPLACES the row's own —
# which is why this block restates every key rather than adding one field to it. The keys come
# from the bundle patch (integrations/dsh/cordis.patch.yml), with the interpreter and the
# checkout resolved for this machine. Re-run the installer after moving the checkout; delete the
# block to fall back to the bundle patch's path-free defaults.
#
# A --patch overlay or a later layer still wins over these rows, so the switch and any
# per-boot override behave as documented."""


class _Lenient(yaml.SafeLoader):
    """A loader that reads a patch list with the harness' own tags in it.

    The harness' patch DSL allows `!!js` scalars — a real profile has them, e.g.
    `headers: !!js >` — and `yaml.safe_load` refuses the whole file on an unknown tag. That is a
    *validation* detail, not a reason to stop: this module never interprets those nodes, it only
    needs to know the file is still one patch list with both of our rows in it. Refusing to parse
    them made the installer crash on the operator's profile while working on every throwaway one,
    which is the worst possible split.
    """


_Lenient.add_multi_constructor("", lambda loader, suffix, node: None)


def _load(text: str):
    return yaml.load(text, Loader=_Lenient)


def rows_for(bundle_path: Path, checkout: str, python_cmd: str) -> list[dict]:
    """The two complete rows, derived from the bundle patch so there is one description of each."""
    bundle = yaml.safe_load(bundle_path.read_text())
    rows = {entry["id"]: entry for group in bundle for entry in group.get("insert", [])}

    plugin_config = dict(rows["geoai"]["config"])
    plugin_config["projectRoot"] = checkout
    plugin_config["pythonCmd"] = python_cmd

    mcp_config = dict(rows["mcp-geoai"]["config"])
    mcp_config["command"] = python_cmd
    mcp_config["cwd"] = checkout
    mcp_config["env"] = {**mcp_config.get("env", {}), "PYTHONPATH": f"{checkout}/backend:{checkout}"}

    return [
        {"id": "geoai", "config": plugin_config},
        {"id": "mcp-geoai", "config": mcp_config},
    ]


def merge(current: str, block: str) -> tuple[str, str]:
    """(new file contents, what happened) for a patch file that may already hold a block."""
    action = "appended"
    if BEGIN in current and END in current:
        # Matched by prefix, so a block written by an older revision — whose BEGIN line carried
        # the script's path in parentheses — is still found, and replaced rather than duplicated.
        head, rest = current.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        current = head + tail.lstrip("\n")
        action = "replaced"

    # The empty-list placeholder is a whole-document placeholder, so it goes wherever it sits —
    # but only when it *is* the whole document: a `[]` after a list item is somebody's data.
    stripped = current.rstrip("\n")
    if stripped.rstrip().endswith("[]"):
        lines = stripped.split("\n")
        for index in range(len(lines) - 1, -1, -1):
            if lines[index].strip() == "[]":
                del lines[index]
                break
        stripped = "\n".join(lines).rstrip("\n")

    return (f"{stripped}\n\n{block}" if stripped.strip() else block), action


def block_for(rows: list[dict]) -> str:
    body = yaml.safe_dump(rows, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return f"{BEGIN}\n{HEADER}\n{body.rstrip()}\n{END}\n"


def main(argv: list[str]) -> int:
    args = [item for item in argv if not item.startswith("--")]
    dry_run = "--dry-run" in argv
    if len(args) != 4:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("usage: merge-patch-block.py <patch.yml> <bundle.yml> <checkout> <python>", file=sys.stderr)
        return 2
    patch_path, bundle_path, checkout, python_cmd = args

    try:
        current = Path(patch_path).read_text()
    except FileNotFoundError:
        current = "# Your patch layer for this dsh profile.\n[]\n"

    updated, action = merge(current, block_for(rows_for(Path(bundle_path), checkout, python_cmd)))

    # Refuse to write something the harness will refuse to load: a parse error here is a profile
    # that boots to an exception, which is a much more confusing symptom than a failed install.
    # Other rows may be present — this is somebody's patch layer, not ours alone — so the check is
    # "one list, both of our rows exactly once", not "exactly our rows".
    try:
        parsed = _load(updated)
    except yaml.YAMLError as error:
        print(f"refusing to write {patch_path}: the result is not valid YAML: {error}", file=sys.stderr)
        return 1
    ids = [row.get("id") for row in parsed] if isinstance(parsed, list) else []
    if not isinstance(parsed, list) or ids.count("geoai") != 1 or ids.count("mcp-geoai") != 1:
        print(
            f"refusing to write {patch_path}: expected one patch list with one geoai and one "
            f"mcp-geoai row, found {ids or type(parsed).__name__}",
            file=sys.stderr,
        )
        return 1

    if dry_run:
        print(updated)
        return 0

    Path(patch_path).write_text(updated)
    print(f"==> {action} the managed block in {patch_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
