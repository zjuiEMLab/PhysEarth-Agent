"""The assembled prompt must not change when the prompt text moves out into files.

Every committed record in `evaluation/results/` was produced against a particular system
prompt. If moving that text between files alters it by so much as a blank line, every
ablation contrast in REPORT.md silently stops comparing like with like, and nothing else
in the suite would notice.

So the prompt is pinned here byte for byte, across all 48 combinations of the three
ablation switches, the online layer and the session state, independently of how it comes
to be stored. Coverage is by digest, because the full text of 48 prompts is nearly two
megabytes of fixture; two representative cases are kept in full so that a failure has
something readable to diff against.

Regenerate deliberately with:

    PHYSEARTH_UPDATE_PROMPT_FIXTURES=1 .venv/bin/python -m pytest tests/test_prompt_layers.py

and read what that produces as a change to the agent's behaviour, not as housekeeping.
"""

import hashlib
import itertools
import json
import os
from pathlib import Path

import pytest
from physearth import paths, prompt
from physearth import session as session_state

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "prompts"
DIGESTS = FIXTURES / "digests.json"
UPDATE = os.environ.get("PHYSEARTH_UPDATE_PROMPT_FIXTURES") == "1"

SWITCH_NAMES = ("harness", "literature", "capability")

# Kept in full, because these two are the ones a failure will usually be about: what the
# deployed Studio sends, and what the corpus ablation sends.
SAMPLED = (
    "harnesson-literatureon-capabilityon__onlineon__state",
    "harnesson-literatureoff-capabilityon__onlineoff__nostate",
)


def _session(**overrides):
    """A real session with the volatile fields pinned.

    Built through new_session rather than hand-rolled: the prompt reaches into the
    held-evidence block, and a hand-made dict silently lacks the keys that block reads.
    """
    session = session_state.new_session("fixture-model")
    session["id"] = "ses_fixture"
    session.update(
        turns=4,
        model_calls=11,
        tool_calls=23,
        sections_read={"smrt-v1#03", "smrt-v1#04"},
        models_run={"smrt"},
        datasets_read={"tvc-backscatter"},
        skills_read={"research-planning"},
    )
    session.update(overrides)
    return session


def _states():
    return {
        "nostate": None,
        "state": {
            "model_calls": 3,
            "tool_calls": 7,
            "max_model_calls": 0,
            "max_tool_calls": 0,
            "session": _session(),
        },
        "research": {
            "model_calls": 3,
            "tool_calls": 7,
            "max_model_calls": 0,
            "max_tool_calls": 0,
            "session": _session(
                research_required=True,
                research=None,
                capability_review={"status": "waiting_user"},
            ),
        },
    }


def _cases():
    states = _states()
    for values in itertools.product((True, False), repeat=len(SWITCH_NAMES)):
        switches = dict(zip(SWITCH_NAMES, values, strict=True))
        label = "-".join(
            "%s%s" % (name, "on" if switches[name] else "off") for name in SWITCH_NAMES
        )
        for online in (True, False):
            for state_name, state in states.items():
                name = "%s__online%s__%s" % (label, "on" if online else "off", state_name)
                yield name, switches, online, state


CASES = list(_cases())


def _build(prompt_module, switches, online, state, monkeypatch):
    monkeypatch.setattr(prompt_module, "online_available", lambda: online)
    payload = state if state is None else {**state, "switches": switches}
    return prompt_module.build(payload)


def test_the_assembled_prompt_is_unchanged(monkeypatch):
    """All 48 combinations at once, so one report names every case that moved."""
    built = {
        name: _build(prompt, switches, online, state, monkeypatch)
        for name, switches, online, state in CASES
    }
    digests = {
        name: {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "chars": len(text)}
        for name, text in built.items()
    }

    if UPDATE:
        FIXTURES.mkdir(parents=True, exist_ok=True)
        DIGESTS.write_text(json.dumps(digests, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        for name in SAMPLED:
            (FIXTURES / ("sample__%s.txt" % name)).write_text(built[name], encoding="utf-8")
        pytest.skip("regenerated %d digests and %d samples" % (len(digests), len(SAMPLED)))

    assert DIGESTS.is_file(), (
        "no prompt digests; regenerate with PHYSEARTH_UPDATE_PROMPT_FIXTURES=1"
    )
    expected = json.loads(DIGESTS.read_text(encoding="utf-8"))
    assert sorted(expected) == sorted(digests), "the set of prompt cases changed"

    moved = [name for name in sorted(digests) if digests[name] != expected[name]]
    assert not moved, (
        "the assembled prompt changed for %d case(s): %s. If that was intended, "
        "regenerate the fixtures and say so in the commit, because it invalidates "
        "comparisons against the committed evaluation records."
        % (len(moved), ", ".join(moved[:5]))
    )


@pytest.mark.parametrize("name", SAMPLED)
def test_the_sampled_prompts_match_in_full(name, monkeypatch):
    """A digest says something moved; this says what."""
    case = next(c for c in CASES if c[0] == name)
    built = _build(prompt, case[1], case[2], case[3], monkeypatch)
    path = FIXTURES / ("sample__%s.txt" % name)
    assert path.is_file(), "no sample for %s" % name
    assert built == path.read_text(encoding="utf-8")


def test_the_files_are_actually_the_source_of_the_text():
    """The byte-identity test proves nothing changed. This proves the files are read.

    Both were true at once for a while: prompt.py loaded each block from `prompts/` and
    then three of them were redefined further down as literals, so the file was read,
    overwritten, and the digests still matched perfectly. Editing 22-triggers.md would
    have done nothing at all. A negative check cannot see that; only this can.
    """
    import importlib

    canary = "CANARY-e6f1a2-do-not-ship"
    path = paths.prompts() / "22-triggers.md"
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original + canary + "\n", encoding="utf-8")
        reloaded = importlib.reload(prompt)
        assert canary in reloaded.TRIGGERS, "prompts/22-triggers.md is not the source of TRIGGERS"
        assert canary in reloaded.build(None), "the block never reaches the assembled prompt"
    finally:
        path.write_text(original, encoding="utf-8")
        importlib.reload(prompt)

    assert canary not in prompt.build(None)


def test_no_prompt_text_is_left_in_python():
    """A block defined in both places is the failure mode above, waiting to come back."""
    import ast

    source = Path(prompt.__file__).read_text(encoding="utf-8")
    literals = [
        node.targets[0].id
        for node in ast.parse(source).body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        and len(node.value.value) > 200
    ]
    assert literals == [], "prompt text still written in Python: %s" % literals


def test_every_switch_combination_is_covered():
    """A fixture set with a hole in it is worse than none: it looks like coverage."""
    assert len(CASES) == 2 ** len(SWITCH_NAMES) * 2 * 3 == 48
    assert len({name for name, _, _, _ in CASES}) == len(CASES)
    assert set(SAMPLED) <= {name for name, _, _, _ in CASES}
