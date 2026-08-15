"""One entry point for the evaluation suite.

There are twelve runners and no obvious order to try them in. This lists them with what
each costs, and dispatches to one. Everything it can do can still be done by calling the
runner directly; this exists so that a first-time reader does not have to guess.

    python evaluation/run.py                    what is available, and what it costs
    python evaluation/run.py tier0              deterministic, free, ~20 s
    python evaluation/run.py registration       deterministic, no LLM
    python evaluation/run.py agent --dry-run    show the plan and the cache state
    python evaluation/run.py report             rebuild REPORT.md from the cache

Arguments after the name are passed to the runner untouched, so
`run.py agent --repeats 3` is `agent_tasks.py --repeats 3`.
"""

import subprocess
import sys
from pathlib import Path

RUNNERS = Path(__file__).resolve().parent / "runners"

# name -> (script, cost, what it does)
COMMANDS = {
    "tier0": (
        "tier0.py",
        "free, deterministic, ~20 s",
        "Does each bundled model still compute what it computed before? Drives the "
        "upstream package directly and requires the adapter to agree to nine decimals.",
    ),
    "registration": (
        "model_registration.py",
        "free, deterministic, no LLM",
        "Competition dimension A. Validates every model card plus one deliberately bad "
        "fixture, re-runs the Tier-0 oracles, and checks the four tool-layer gates.",
    ),
    "contract": (
        "registry_contract.py",
        "free, deterministic, no LLM",
        "The registry contract on its own: discovery, validation, refusal.",
    ),
    "demo": (
        "registration_demo.py",
        "free, deterministic, no LLM",
        "Registers the example model end to end, as a worked demonstration.",
    ),
    "agent": (
        "agent_tasks.py",
        "COSTS LLM QUOTA unless --dry-run",
        "The agent task set across the four ablation configurations. Writes one file per "
        "run and skips any run already cached, which is what makes the report rebuildable.",
    ),
    "competition": (
        "competition.py",
        "COSTS LLM QUOTA",
        "The competition matrix: tasks by prompt profile by configuration by model.",
    ),
    "robustness": (
        "llm_robustness.py",
        "free, rebuilds from cached runs",
        "Competition dimension D. Admits a comparison only when task, prompt profile, "
        "build and configuration match and at least two models have records.",
    ),
    "smoke": (
        "llm_smoke.py",
        "COSTS LLM QUOTA, one call",
        "Is the configured provider reachable and answering?",
    ),
    "reproduction": (
        "reproduction_eval.py",
        "COSTS LLM QUOTA",
        "The four SMRT reproduction questions, end to end.",
    ),
    "report": (
        "report.py",
        "free, rebuilds from cached runs",
        "Rebuilds REPORT.md. Writes to the repository; commit it deliberately.",
    ),
    "dashboard": (
        "dashboard.py",
        "free, rebuilds from cached runs",
        "Rebuilds the competition dashboard HTML from the committed records.",
    ),
}


def _usage():
    print(__doc__.strip().split("\n\n")[0])
    print()
    width = max(len(name) for name in COMMANDS)
    for name, (_, cost, what) in COMMANDS.items():
        print("  %-*s  %s" % (width, name, cost))
        for line in _wrap(what, 72):
            print("  %-*s  %s" % (width, "", line))
        print()
    print("Anything after the name is passed to the runner unchanged.")
    print("The runners themselves are in evaluation/runners/ and still work directly.")


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for word in words:
        if line and len(line) + 1 + len(word) > width:
            out.append(line)
            line = word
        else:
            line = "%s %s" % (line, word) if line else word
    if line:
        out.append(line)
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        _usage()
        return 0
    name = argv[0]
    if name not in COMMANDS:
        print("unknown command %r\n" % name, file=sys.stderr)
        _usage()
        return 2
    script = RUNNERS / COMMANDS[name][0]
    # A subprocess rather than an import, so each runner keeps its own argument parsing
    # and its own idea of __main__, and this file cannot change what any of them does.
    return subprocess.call([sys.executable, str(script), *argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
