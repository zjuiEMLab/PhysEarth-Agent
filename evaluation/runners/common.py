"""Shared plumbing for the evaluation runners.

Everything here is import-only: no module runs work when it is loaded, so a runner can
be imported from a notebook or another script without side effects.
"""

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
TASKS = ROOT / "tasks"
CONFIGS = ROOT / "configs"
RESULTS = ROOT / "results"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_tasks(suite):
    directory = TASKS / suite
    if not directory.is_dir():
        return []
    tasks = []
    for path in sorted(directory.glob("*.yaml")):
        task = load_yaml(path)
        task["_path"] = str(path.relative_to(REPO)).replace("\\", "/")
        tasks.append(task)
    return tasks


def load_configs(names=None):
    configs = []
    for path in sorted(CONFIGS.glob("*.yaml")):
        config = load_yaml(path)
        if names and config["name"] not in names:
            continue
        configs.append(config)
    return configs


def write_json(name, payload):
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def read_json(name):
    path = RESULTS / name
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def table(headers, rows):
    """A GitHub-flavoured markdown table, so REPORT.md renders on the repository page."""
    widths = [len(h) for h in headers]
    body = [[("" if cell is None else str(cell)) for cell in row] for row in rows]
    for row in body:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row, strict=True)]
    lines = ["| %s |" % " | ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True))]
    lines.append("| %s |" % " | ".join("-" * w for w in widths))
    for row in body:
        lines.append("| %s |" % " | ".join(cell.ljust(w) for cell, w in zip(row, widths, strict=True)))
    return "\n".join(lines)
