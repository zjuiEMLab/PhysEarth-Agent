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
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

from physearth import agent, config, harness  # noqa: E402

RUNS = common.RESULTS / "runs"
SUITES = ("tier1", "probe")
SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def key(task_id, config_name, llm, repeat):
    return "%s__%s__%s__r%d.json" % (task_id, config_name, SAFE.sub("-", llm), repeat)


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
                    "spec": data.get("spec"),
                    "handle": data.get("handle"),
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


def run_one(task, config_entry, llm, repeat):
    started = time.perf_counter()
    session = agent.new_session(llm)
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
        "repeat": repeat,
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
    parser.add_argument("--llm", default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    config.load_dotenv()
    llm = args.llm or agent.default_model()
    configs = common.load_configs(args.configs)
    tasks = [t for suite in args.suites for t in common.load_tasks(suite)]
    if args.tasks:
        tasks = [t for t in tasks if t["id"] in args.tasks]

    planned = [
        (task, entry, repeat)
        for task in tasks
        for entry in configs
        for repeat in range(1, args.repeats + 1)
    ]
    RUNS.mkdir(parents=True, exist_ok=True)
    todo = [p for p in planned if args.force or not (RUNS / key(p[0]["id"], p[1]["name"], llm, p[2])).is_file()]

    print("%d task(s) x %d config(s) x %d repeat(s) = %d run(s) on %s"
          % (len(tasks), len(configs), args.repeats, len(planned), llm))
    print("%d already cached, %d to run" % (len(planned) - len(todo), len(todo)))
    if args.dry_run:
        for task, entry, repeat in todo:
            print("  would run %s" % key(task["id"], entry["name"], llm, repeat))
        return 0

    failures = 0
    for index, (task, entry, repeat) in enumerate(todo, 1):
        name = key(task["id"], entry["name"], llm, repeat)
        print("[%3d/%3d] %s" % (index, len(todo), name), flush=True)
        try:
            record = run_one(task, entry, llm, repeat)
        except Exception:
            failures += 1
            print(traceback.format_exc())
            continue
        (RUNS / name).write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print("          %s, %d LLM calls, %d tool calls, stop=%s"
              % ("answered" if record["answer"] else "no answer",
                 record["model_calls"], record["tool_calls"], record["stop_rule"]), flush=True)

    print("\n%d run(s) written, %d failed" % (len(todo) - failures, failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
