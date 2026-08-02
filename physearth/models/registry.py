import importlib
import importlib.util
import os
import sys
from pathlib import Path

import yaml

from physearth.models import contract

BUNDLED_DIR = Path(__file__).resolve().parent / "bundled"
ENTRY_POINT_GROUP = "physearth.models"
EXTRA_DIRS_ENV = "PHYSEARTH_MODEL_PATH"

_REGISTRY = None
_REJECTED = None


class Model:
    def __init__(self, card, run, source):
        self.card = card
        self.run = run
        self.source = source

    @property
    def name(self):
        return self.card["name"]

    @property
    def tier(self):
        return self.card["tier"]

    @property
    def runnable(self):
        return self.tier == "demo"


def _load_module(directory, entrypoint):
    module_name, _, attribute = entrypoint.partition(":")
    attribute = attribute or "run"
    path = directory / (module_name + ".py")
    if not path.is_file():
        raise contract.DeclarationError("entrypoint module %s not found in %s" % (path.name, directory))
    spec = importlib.util.spec_from_file_location(
        "physearth_model_%s_%s" % (directory.name, module_name), path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, attribute):
        raise contract.DeclarationError("module %s does not expose %r" % (path.name, attribute))
    return getattr(module, attribute)


def _load_directory(directory, source):
    card_path = directory / "model_card.yaml"
    if not card_path.is_file():
        raise contract.DeclarationError("no model_card.yaml in %s" % directory)
    card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
    problems = contract.validate_card(card)
    if problems:
        raise contract.DeclarationError("; ".join(problems))
    card["_dir"] = directory
    run = None
    if card["tier"] == "demo":
        run = _load_module(directory, card["entrypoint"])
    return Model(card, run, source)


def _candidate_dirs():
    found = []
    if BUNDLED_DIR.is_dir():
        for child in sorted(BUNDLED_DIR.iterdir()):
            if child.is_dir() and (child / "model_card.yaml").is_file():
                found.append((child, "bundled"))
    for raw in (os.environ.get(EXTRA_DIRS_ENV) or "").split(os.pathsep):
        if not raw.strip():
            continue
        root = Path(raw.strip())
        if (root / "model_card.yaml").is_file():
            found.append((root, "local directory"))
        elif root.is_dir():
            for child in sorted(root.iterdir()):
                if child.is_dir() and (child / "model_card.yaml").is_file():
                    found.append((child, "local directory"))
    return found


def _entry_point_dirs():
    found = []
    try:
        from importlib.metadata import entry_points

        selected = entry_points(group=ENTRY_POINT_GROUP)
    except Exception:
        return found
    for entry in selected:
        try:
            target = entry.load()
            root = Path(target() if callable(target) else target)
            if (root / "model_card.yaml").is_file():
                found.append((root, "entry point %s" % entry.name))
        except Exception:
            continue
    return found


def _build():
    global _REGISTRY, _REJECTED
    registry, rejected = {}, []
    for directory, source in _candidate_dirs() + _entry_point_dirs():
        try:
            model = _load_directory(directory, source)
        except Exception as exc:
            rejected.append(
                {"directory": str(directory), "source": source, "reason": "%s: %s" % (type(exc).__name__, exc)}
            )
            continue
        if model.name in registry:
            rejected.append(
                {"directory": str(directory), "source": source, "reason": "name %r already registered" % model.name}
            )
            continue
        registry[model.name] = model
    _REGISTRY, _REJECTED = registry, rejected


def _ensure():
    if _REGISTRY is None:
        _build()


def reload():
    _build()


def all_models():
    _ensure()
    return dict(_REGISTRY)


def rejected():
    _ensure()
    return list(_REJECTED)


def get(name):
    _ensure()
    return _REGISTRY.get(name)


def names(runnable_only=False):
    _ensure()
    return [n for n, m in _REGISTRY.items() if m.runnable or not runnable_only]


def summary():
    _ensure()
    rows = []
    for name, model in _REGISTRY.items():
        rows.append(
            {
                "name": name,
                "version": model.card["version"],
                "tier": model.tier,
                "runnable": model.runnable,
                "description": model.card["description"],
                "outputs": sorted(model.card["outputs"]),
                "source": model.source,
            }
        )
    return rows


def capability_block():
    _ensure()
    lines = []
    for name, model in _REGISTRY.items():
        card = model.card
        head = "- %s v%s (%s)" % (name, card["version"], card["tier"])
        if not model.runnable:
            head += " [registered but not runnable in this environment]"
        lines.append("%s\n  %s" % (head, card["description"]))
        lines.append("  outputs: %s" % ", ".join(sorted(card["outputs"])))
        for pname, spec in card["parameters"].items():
            lines.append("  %s" % _parameter_line(pname, spec))
        for rule in card.get("combinations") or []:
            lines.append("  constraint: %s" % rule["reason"])
    return "\n".join(lines)


def _parameter_line(name, spec):
    bits = [spec["type"]]
    if spec.get("enum"):
        bits.append("one of %s" % ", ".join(str(v) for v in spec["enum"]))
    elif spec["type"] in contract.NUMERIC_TYPES:
        bits.append("%s to %s %s" % (spec["minimum"], spec["maximum"], spec["unit"]))
    if spec.get("default") is not None:
        bits.append("default %s" % spec["default"])
    if not spec.get("required", True):
        bits.append("optional")
    return "%s: %s -- %s" % (name, "; ".join(bits), spec["description"])
