"""Run the agent task set once per ablation configuration and record what happened.

One task is one fresh session and one question, so nothing leaks between tasks. Every
run is written to results/runs/ under a key naming the task, the configuration, the
language model and the repeat index, and an existing file is reused rather than re-run.
That cache is what makes the suite affordable: the free inference quota is per model and
per day, so a re-run of the report must not cost a second quota.

  python evaluation/runners/agent_tasks.py --dry-run
  python evaluation/runners/agent_tasks.py --repeats 3
  python evaluation/runners/agent_tasks.py --configs full no-harness --tasks p-smrt-density-above-ice
"""

import argparse
import json
import re
import subprocess
import sys
import time
import traceback
from urllib.parse import urlparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

from physearth import agent, config, harness  # noqa: E402

RUNS = common.RESULTS / "runs"
SUITES = ("tier2", "probe")
SAFE = re.compile(r"[^A-Za-z0-9._-]+")
FAULTS = ("quota", "withdrawn", "upstream", "global_budget")

# Deliberately none of the three the interface offers. Those are reserved for a person
# driving the deployed Studio; a sweep of a few hundred calls would spend their daily
# quota and trip the account's requests-per-minute limit underneath them.
#
# A pool rather than one model, because the free quota is counted per model per day and
# one model does not hold enough of it for the whole sweep. The sweep is therefore run as
# a blocked design: a task is a block, and every configuration of that task runs on the
# same model, so the comparison the report makes -- between configurations, within a task
# -- never straddles two models. A block whose model runs out is discarded whole and
# retried on the next model, never left half finished.
DEFAULT_POOL = [
    "Qwen/Qwen3-Next-80B-A3B-Instruct",
    "Qwen/Qwen3.5-35B-A3B",
    "Qwen/Qwen3-30B-A3B",
    "Qwen/Qwen3-14B",
    "stepfun-ai/Step-3.5-Flash",
]
PACE_S = 3.0


def key(task_id, config_name, llm, repeat):
    return "%s__%s__%s__r%d.json" % (task_id, config_name, SAFE.sub("-", llm), repeat)


def build_id():
    """Which commit produced a record.

    A run is only comparable with the other cells of its table if the system under test
    was the same. The quota is spent over more than one day, so the cache holds records
    made at different times, and without this there is no way to notice that half a table
    describes an older system.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(common.REPO),
            capture_output=True,
            text=True,
            timeout=10,
        )
        head = out.stdout.strip() or "unknown"
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=str(common.REPO),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return head + ("+dirty" if dirty.stdout.strip() else "")
    except Exception:
        return "unknown"


def _tool_log(events):
    """Every tool call the run made, with what it was given and what came back."""
    log = []
    for event in events:
        if event["kind"] == "tool_call":
            data = event.get("data") or {}
            log.append(
                {
                    "name": event["name"],
                    "arguments": event.get("arguments") or {},
                    "status": event.get("status"),
                    "model": data.get("model"),
                    "version": data.get("version"),
                    "spec": data.get("spec"),
                    "handle": data.get("handle"),
                    "planned_run_id": data.get("planned_run_id"),
                    "planned_chart_id": data.get("planned_chart_id"),
                    "quality_review": data.get("quality_review"),
                    "unguarded_problems": data.get("unguarded_problems") or [],
                    "qc_passed": event.get("qc"),
                }
            )
        elif event["kind"] == "harness_block" and event.get("tool"):
            log.append(
                {
                    "name": event["tool"],
                    "arguments": event.get("given") or {},
                    "status": "needs_input",
                    "spec": None,
                    "problems": event.get("problems") or [],
                }
            )
    return log


def _stop_rule(events):
    for event in events:
        if event["kind"] in ("harness_stop", "harness_giveup"):
            return event.get("rule")
    return None


def _provider_metadata():
    """Non-secret provider identity needed for dimension-D comparisons."""
    base = config.llm_api_base()
    parsed = urlparse(base)
    return {
        "name": parsed.netloc or "unrecorded",
        "api_base_origin": "%s://%s" % (parsed.scheme, parsed.netloc)
        if parsed.scheme and parsed.netloc
        else "unrecorded",
    }


def run_one(task, config_entry, llm, repeat, build, prompt_profile="P0_direct"):
    started = time.perf_counter()
    # Unrestricted on purpose: the sweep runs on a model outside the interface's switcher,
    # so it never competes for the daily quota of the three a reviewer might be using.
    session = agent.new_session(llm, unrestricted=True)
    answer, events, state = agent.run(
        task["question"], model=llm, session=session, switches=config_entry["switches"]
    )
    return {
        "task": task["id"],
        "suite": task["suite"],
        "quality": task.get("quality"),
        "config": config_entry["name"],
        "switches": config_entry["switches"],
        "llm": llm,
        "provider": _provider_metadata(),
        "prompt_profile": prompt_profile,
        # The client currently leaves these at provider defaults. Recording null is
        # intentional: an unknown value must not be mistaken for temperature=0 or a seed.
        "temperature": None,
        "seed": None,
        "repeat": repeat,
        "build": build,
        "question": task["question"],
        "answer": answer,
        "elapsed_s": round(time.perf_counter() - started, 2),
        "stop_rule": _stop_rule(events),
        "model_calls": state.get("model_calls", 0),
        "tool_calls": state.get("tool_calls", 0),
        "interventions": state.get("interventions", 0),
        "qc_failures": state.get("qc_failures", 0),
        "tool_log": _tool_log(events),
        "evidence": {
            "sections": sorted(session["sections_read"]),
            "models": sorted(session["models_run"]),
            "datasets": sorted(session["datasets_read"]),
        },
        "figures": [
            {"provenance": f.get("provenance"), "series": f.get("series")}
            for f in session["figures"]
        ],
        "markers": {
            "literature": harness.find_markers(answer),
            "model": harness.find_model_markers(answer),
            "data": harness.find_data_markers(answer),
        },
        "event_kinds": [e["kind"] for e in events],
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--configs", nargs="*", default=None)
    parser.add_argument("--tasks", nargs="*", default=None)
    parser.add_argument("--suites", nargs="*", default=list(SUITES))
    parser.add_argument("--llm", nargs="*", default=None,
                        help="model pool; a task's configurations all run on one of them")
    parser.add_argument("--pace", type=float, default=PACE_S,
                        help="seconds to wait between runs, to stay under the account RPM limit")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--prompt-profile",
        default="P0_direct",
        help="declared prompt condition stored with every record; the question is unchanged",
    )
    args = parser.parse_args(argv)

    config.load_dotenv()
    pool = args.llm or list(DEFAULT_POOL)
    build = build_id()
    configs = common.load_configs(args.configs)
    tasks = [t for suite in args.suites for t in common.load_tasks(suite)]
    if args.tasks:
        requested = set(args.tasks)
        tasks = [
            t for t in tasks
            if t["id"] in requested or t.get("legacy_id") in requested
        ]
    RUNS.mkdir(parents=True, exist_ok=True)

    print("%d task(s) x %d config(s) x %d repeat(s) = %d run(s) at build %s"
          % (len(tasks), len(configs), args.repeats,
             len(tasks) * len(configs) * args.repeats, build))
    print("model pool: %s" % ", ".join(pool))

    def block_of(task, repeat):
        """Which model already holds a complete block for this task, if any."""
        for llm in pool:
            names = [key(task["id"], c["name"], llm, repeat) for c in configs]
            if all((RUNS / n).is_file() for n in names):
                return llm, names
        return None, []

    planned, cached = [], 0
    for task in tasks:
        for repeat in range(1, args.repeats + 1):
            done, _ = block_of(task, repeat)
            if done and not args.force:
                cached += 1
            else:
                planned.append((task, repeat))
    print("%d block(s) already complete, %d to run" % (cached, len(planned)))
    if args.dry_run:
        for task, repeat in planned:
            print("  would run block %s r%d (%d configs)" % (task["id"], repeat, len(configs)))
        return 0

    dead = set()
    written, abandoned = 0, []
    for index, (task, repeat) in enumerate(planned, 1):
        placed = False
        for llm in pool:
            if llm in dead:
                continue
            print("[%2d/%2d] block %s r%d on %s"
                  % (index, len(planned), task["id"], repeat, llm), flush=True)
            made, spent = [], False
            for entry in configs:
                name = key(task["id"], entry["name"], llm, repeat)
                if (RUNS / name).is_file() and not args.force:
                    made.append(name)
                    continue
                try:
                    record = run_one(
                        task, entry, llm, repeat, build, prompt_profile=args.prompt_profile
                    )
                except Exception:
                    print(traceback.format_exc())
                    spent = True
                    break
                if record["stop_rule"] in FAULTS:
                    print("        %s: %s" % (entry["name"], record["stop_rule"]))
                    spent = True
                    break
                (RUNS / name).write_text(
                    json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                made.append(name)
                print("        %-14s %d LLM calls, %d tool calls"
                      % (entry["name"], record["model_calls"], record["tool_calls"]), flush=True)
                if args.pace:
                    time.sleep(args.pace)
            if not spent:
                written += len(made)
                placed = True
                break
            # The block is only meaningful whole. Keep the partial records off disk so a
            # later run cannot mistake them for a comparison.
            for name in made:
                if (RUNS / name).is_file():
                    (RUNS / name).unlink()
            dead.add(llm)
            print("        %s is spent for today; retrying this block on the next model" % llm)
        if not placed:
            abandoned.append((task["id"], repeat))
            print("        no model in the pool has quota left for this block")
            break

    print("\n%d run(s) written. %d model(s) spent today: %s"
          % (written, len(dead), ", ".join(sorted(dead)) or "none"))
    if abandoned:
        print("%d block(s) not run. Re-run this command tomorrow; complete blocks are cached."
              % (len(planned) - index + 1))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
