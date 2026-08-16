import importlib
import importlib.util
import os
import re
import shutil
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

import yaml

from physearth import paths
from physearth.registry import contract

BUNDLED_DIR = paths.models() / "bundled"
ENTRY_POINT_GROUP = "physearth.models"
EXTRA_DIRS_ENV = "PHYSEARTH_MODEL_PATH"

_REGISTRY = None
_REJECTED = None
_ACTIVE_SESSION = ContextVar("physearth_model_session", default=None)


@contextmanager
def session_context(session):
    """Make session-only models visible to nested validation without global mutation."""
    token = _ACTIVE_SESSION.set(session)
    try:
        yield
    finally:
        _ACTIVE_SESSION.reset(token)


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
    def requires(self):
        """The import a `local` model needs before it can run anywhere."""
        return self.card.get("requires_import") or ""

    @property
    def available(self):
        return not self.requires or importlib.util.find_spec(self.requires) is not None

    @property
    def runnable(self):
        """A `demo` model runs everywhere; a `local` model runs where its dependency is.

        The second case is not a special case, it is the common one for a real scientific
        package: a hydrologic model that needs numpy 2 cannot run on a host pinned to
        numpy 1, and pretending otherwise would mean discovering it as an obscure crash
        instead of as a declared fact. Such a model still registers with its full
        declaration everywhere, so the agent can describe it and say why it cannot run it.
        """
        if self.tier == "demo":
            return True
        return self.tier == "local" and self.available and self.run is not None

    @property
    def unavailable_reason(self):
        if self.runnable:
            return ""
        if self.tier == "local" and not self.available:
            return (
                "%s is registered but its dependency %r is not installed in this "
                "environment. Install it to run the model here; everything else about it, "
                "including its parameter declaration, is available now."
                % (self.name, self.requires)
            )
        return "%s is registered but its tier is %r, so it cannot run in this environment." % (
            self.name,
            self.tier,
        )


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
    elif card["tier"] == "local":
        # Loaded so the model is genuinely runnable where its dependency exists. The
        # adapter must not import that dependency at module level, or a host without it
        # would reject the whole model instead of registering it as unavailable.
        try:
            run = _load_module(directory, card["entrypoint"])
        except Exception:
            run = None
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


def register_directory(directory, source="managed"):
    """Register one already-approved model directory.

    GitHub inspection never calls this function.  Callers must complete their own approval
    gate before allowing the adapter import that the normal registry contract requires.
    """
    _ensure()
    model = _load_directory(Path(directory), source)
    if model.name in _REGISTRY:
        raise contract.DeclarationError("name %r already registered" % model.name)
    _REGISTRY[model.name] = model
    return model


def register_session_directory(session, directory, source="temporary evaluation"):
    """Load an approved model into one session without mutating the global registry."""
    if session is None:
        raise ValueError("a session is required for temporary model registration")
    _ensure()
    model = _load_directory(Path(directory), source)
    if model.name in _REGISTRY:
        raise contract.DeclarationError(
            "temporary model name %r conflicts with a globally registered model" % model.name
        )
    temporary = session.setdefault("temporary_models", {})
    if model.name in temporary:
        raise contract.DeclarationError(
            "temporary model %r is already registered in this session" % model.name
        )
    temporary[model.name] = model
    session.setdefault("temporary_model_dirs", []).append(str(directory))
    return model


def clear_session(session):
    """Remove session-only models and their temporary source directories."""
    if not session:
        return
    session.pop("temporary_models", None)
    for raw in session.pop("temporary_model_dirs", []) or []:
        try:
            shutil.rmtree(Path(raw), ignore_errors=True)
        except (OSError, ValueError):
            pass


def all_models(session=None):
    _ensure()
    session = session if session is not None else _ACTIVE_SESSION.get()
    models = dict(_REGISTRY)
    models.update((session or {}).get("temporary_models") or {})
    return models


def rejected():
    _ensure()
    return list(_REJECTED)


def get(name, session=None):
    _ensure()
    session = session if session is not None else _ACTIVE_SESSION.get()
    temporary = (session or {}).get("temporary_models") or {}
    if name in temporary:
        return temporary[name]
    return _REGISTRY.get(name)


def _spelling_key(value):
    """How a name is spelled, ignoring only case and the separators people vary."""
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def resolve(name, session=None):
    """Find a model from a name written the way a person or a paper writes it.

    A paper says SMRT, the card says `smrt`. It says tau-omega, the card says `tau_omega`.
    Treating those as unregistered is what made a reproduction stop and ask the user to
    confirm a partial scope for a model that was sitting in the registry, runnable.

    This is deliberately narrow. It ignores case and non-alphanumeric characters and
    nothing else, so MEMLS and DMRT-ML still do not resolve -- they genuinely are not
    registered, and reporting that is the whole point of the capability check. It is not
    fuzzy matching: no edit distance, no prefixes, no synonyms. A model that is nearly
    named like a registered one is not that model.

    Ambiguity is refused rather than guessed. If two registered models differ only by
    those characters, no name can pick between them and this returns None.

    Returns (model, canonical_name) or (None, None). `get` stays exact: once a name is
    resolved, everything downstream uses the registered spelling.
    """
    exact = get(name, session)
    if exact is not None:
        return exact, name
    key = _spelling_key(name)
    if not key:
        return None, None
    matches = {n: m for n, m in all_models(session).items() if _spelling_key(n) == key}
    if len(matches) != 1:
        return None, None
    canonical, model = next(iter(matches.items()))
    return model, canonical


def resolve_configuration(name, session=None):
    """Find a model named as a formulation of itself: "SMRT IBA", "SMRT QCA short range".

    A paper names the theory, not the package. SMRT IBA and SMRT QCA short range are one
    registered model with `electromagnetic_model` set two ways -- the card says so, in the
    declared enum. Treating them as unregistered models made the capability check report
    that smrt "is not an equivalent implementation of SMRT IBA", which is exactly backwards:
    it is that implementation, configured.

    Returns (model, canonical_name, {parameter: value}) or (None, None, {}).

    As narrow as `resolve`. The prefix must resolve to a registered model, the remainder
    must match a value the card actually declares, and an exact enum match wins over a
    contained one -- otherwise "IBA" could not choose between `iba` and `iba_original`.
    Ambiguity is refused rather than guessed, and DMRT-QMS still resolves to nothing,
    because no registered card declares it.
    """
    model, canonical = resolve(name, session)
    if model is not None:
        return model, canonical, {}
    key = _spelling_key(name)
    if not key:
        return None, None, {}
    for registered, candidate in sorted(all_models(session).items()):
        prefix = _spelling_key(registered)
        if not prefix or not key.startswith(prefix) or key == prefix:
            continue
        remainder = key[len(prefix):]
        if not remainder:
            continue
        exact, contained = [], []
        for parameter, spec in (candidate.card.get("parameters") or {}).items():
            for value in (spec or {}).get("enum") or ():
                value_key = _spelling_key(value)
                if not value_key:
                    continue
                if value_key == remainder:
                    exact.append((parameter, value))
                elif remainder in value_key:
                    contained.append((parameter, value))
        chosen = exact or contained
        if len(chosen) != 1:
            continue
        parameter, value = chosen[0]
        return candidate, registered, {parameter: value}
    return None, None, {}


def names(runnable_only=False, session=None):
    session = session if session is not None else _ACTIVE_SESSION.get()
    return [n for n, m in all_models(session).items() if m.runnable or not runnable_only]


def summary(session=None):
    session = session if session is not None else _ACTIVE_SESSION.get()
    rows = []
    for name, model in all_models(session).items():
        rows.append(
            {
                "name": name,
                "version": model.card["version"],
                "tier": model.tier,
                "runnable": model.runnable,
                "requires_import": model.requires,
                "unavailable_reason": model.unavailable_reason,
                "description": model.card["description"],
                "outputs": sorted(model.card["outputs"]),
                "source": model.source,
                "instruction_id": model.card.get("instruction_id") or model.name,
                "instruction_version": str(model.card.get("instruction_version") or "1.0"),
                "instruction_available": bool(
                    model.card.get("instruction_path") or ""
                ),
            }
        )
    return rows


def capability_block(declared=True, session=None):
    """The models as the agent sees them.

    With `declared` false only the name, the description and the output names survive;
    every range, enum, default and legal combination is withheld. That is the capability
    ablation, and nothing else about the system changes with it.
    """
    session = session if session is not None else _ACTIVE_SESSION.get()
    lines = []
    for name, model in all_models(session).items():
        card = model.card
        head = "- %s v%s (%s)" % (name, card["version"], card["tier"])
        if not model.runnable:
            head += " [registered but not runnable in this environment]"
        lines.append("%s\n  %s" % (head, card["description"]))
        lines.append("  outputs: %s" % ", ".join(sorted(card["outputs"])))
        if not declared:
            lines.append("  parameters: %s" % ", ".join(card["parameters"]))
            continue
        for pname, spec in card["parameters"].items():
            lines.append("  %s" % _parameter_line(pname, spec))
        for rule in card.get("combinations") or []:
            lines.append("  constraint: %s" % rule["reason"])
    return "\n".join(lines)


def undeclared_parameters(card):
    """A parameter list stripped of everything the capability ablation withholds."""
    return {
        name: {"type": spec["type"], "unit": spec["unit"], "description": spec["description"]}
        for name, spec in card["parameters"].items()
    }


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
