"""The frontend/backend split, as two rules a test can check.

A layout is a suggestion until something enforces it. These two are what stop the split
from eroding one convenient import at a time, and they are cheap enough to run always.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "physearth"
FRONTEND = ROOT / "frontend"


def _imports(path):
    """Every module named by an import in this file, including inside functions."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.append(node.module)
    return found


def _sources(root):
    """Every source file under `root`, and never an empty list by accident.

    A rule that scans a directory which has moved passes without checking anything. That
    happened once already, when the package went under backend/ and this file still named
    the old path, so the emptiness is the assertion.
    """
    assert root.is_dir(), "%s does not exist; this rule would pass without checking" % root
    found = [p for p in root.rglob("*.py") if "__pycache__" not in str(p)]
    assert found, "no sources under %s; this rule would pass without checking" % root
    return found


def test_the_backend_never_imports_gradio():
    """The agent has to run without a browser, headless and in the evaluation suite.

    Gradio belongs to one deployment of this package, not to the package.
    """
    offenders = sorted(
        str(path.relative_to(ROOT))
        for path in _sources(BACKEND)
        if any(name == "gradio" or name.startswith("gradio.") for name in _imports(path))
    )
    assert offenders == [], "gradio is imported under physearth/: %s" % offenders


def test_the_frontend_reaches_the_package_only_through_the_api_module():
    """One declared surface, so the coupling cannot grow without someone deciding to.

    physearth.api names what the interface may touch. A view that needs something new
    adds it there deliberately, rather than reaching into the package from wherever it
    happens to be standing.
    """
    offenders = []
    for path in _sources(FRONTEND):
        for name in _imports(path):
            if name == "physearth.api" or not name.startswith("physearth"):
                continue
            offenders.append("%s imports %s" % (path.relative_to(ROOT), name))
    offenders = sorted(offenders)
    assert offenders == [], "the frontend reaches past physearth.api: %s" % offenders


def test_the_root_entry_point_the_deployspec_names_still_exists():
    """README front-matter pins `deployspec: entry_file: app.py`; it may only ever be a shim."""
    app = ROOT / "app.py"
    assert app.is_file()
    assert "frontend.studio" in app.read_text(encoding="utf-8")
