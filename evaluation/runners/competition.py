"""Run the frozen competition matrix through the deployed research workflow.

The default command is deliberately a no-cost plan. Add ``--execute`` to make LLM calls.
Every cell is cached independently by task, prompt profile, LLM, config and repeat.

    python evaluation/runners/competition.py
    python evaluation/runners/competition.py --execute --tasks t1-smrt-fig4-passive
"""

import argparse
import hashlib
import json
import re
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_tasks  # noqa: E402
import common  # noqa: E402

from physearth import agent, approval, config, harness, research  # noqa: E402

MANIFEST = common.ROOT / "competition.yaml"
PROMPTS = common.ROOT / "prompts"
RUNS = common.RESULTS / "competition" / "runs"
SAFE = re.compile(r"[^A-Za-z0-9._-]+")
FAULTS = ("quota", "withdrawn", "upstream", "global_budget")

PROVENANCE_APPENDIX = """
For this controlled evaluation, end the final report with these exact XML tags. Put a
valid JSON array between the first pair; include every parameter used in the approved
physical-model run. source_kind must be one of paper, user, derived, model_default,
assumption, or unknown. source_ref must identify the paper section, user question, or
reason for the choice; for paper-derived values also include a short source_span. Do not
relabel a guess as paper-derived.

<parameter_provenance>
[{"field":"parameter_name","value":"actual value","source_kind":"paper","source_ref":"paper-id#section","source_span":"short supporting span","reason":"short reason","sensitivity_checked":false}]
</parameter_provenance>
<reproduction_outcome>reproduced|partial|not_identifiable|failed</reproduction_outcome>
""".strip()


def load_manifest():
    return common.load_yaml(MANIFEST)


def load_profiles(ids=None):
    profiles = []
    for path in sorted(PROMPTS.glob("*.yaml")):
        profile = common.load_yaml(path)
        if ids and profile["id"] not in ids:
            continue
        profile["_path"] = str(path.relative_to(common.REPO)).replace("\\", "/")
        profiles.append(profile)
    return profiles


def load_task_index():
    tasks = {}
    for suite in ("tier0", "tier2", "probe"):
        for task in common.load_tasks(suite):
            tasks[task["id"]] = task
    return tasks


def condition_text(profile, question):
    return (
        "[REPRODUCTION PROTOCOL: %s v%s]\n%s\n\n%s\n\n"
        "Research question (unchanged):\n%s"
        % (
            profile["title"],
            profile["version"],
            profile["instructions"].strip(),
            PROVENANCE_APPENDIX,
            question.strip(),
        )
    )


def key(task_id, profile_id, config_name, llm, repeat):
    return "%s__%s__%s__%s__r%d.json" % (
        task_id,
        profile_id,
        config_name,
        SAFE.sub("-", llm),
        repeat,
    )


def _stop_rule(events):
    for event in events:
        if event.get("kind") in ("harness_stop", "harness_giveup"):
            return event.get("rule")
    return None


def _tool_log(events):
    log = []
    for event in events:
        if event.get("kind") == "tool_call":
            data = event.get("data") or {}
            log.append(
                {
                    "turn": event.get("turn"),
                    "name": event.get("name"),
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
        elif event.get("kind") == "harness_block" and event.get("tool"):
            log.append(
                {
                    "turn": event.get("turn"),
                    "name": event.get("tool"),
                    "arguments": event.get("given") or {},
                    "status": "needs_input",
                    "problems": event.get("problems") or [],
                }
            )
    return log


def _event_summary(events):
    keep = (
        "kind", "turn", "rule", "name", "status", "phase", "tool", "qc",
        "intervention", "detail", "reason", "prompt_tokens", "completion_tokens",
        "cost_usd", "reasoning_chars", "elapsed_s",
    )
    return [{field: event.get(field) for field in keep if event.get(field) is not None}
            for event in events]


def _provider_name(base_url):
    value = str(base_url or "").lower()
    if "openrouter.ai" in value:
        return "openrouter"
    if "modelscope.cn" in value:
        return "modelscope"
    return "openai_compatible"


def _llm_usage(events):
    calls = [event for event in events if event.get("kind") == "model_call"]
    prompt = [event.get("prompt_tokens") for event in calls]
    completion = [event.get("completion_tokens") for event in calls]
    costs = [event.get("cost_usd") for event in calls]
    known_prompt = [int(value) for value in prompt if isinstance(value, (int, float))]
    known_completion = [
        int(value) for value in completion if isinstance(value, (int, float))
    ]
    known_costs = [float(value) for value in costs if isinstance(value, (int, float))]
    prompt_total = sum(known_prompt) if len(known_prompt) == len(calls) else None
    completion_total = (
        sum(known_completion) if len(known_completion) == len(calls) else None
    )
    return {
        "calls": len(calls),
        "prompt_tokens": prompt_total,
        "completion_tokens": completion_total,
        "total_tokens": (
            prompt_total + completion_total
            if prompt_total is not None and completion_total is not None
            else None
        ),
        "cost_usd": sum(known_costs) if len(known_costs) == len(calls) else None,
        "cost_complete": len(known_costs) == len(calls),
        "per_call": [
            {
                "turn": event.get("turn"),
                "index": event.get("index"),
                "prompt_tokens": event.get("prompt_tokens"),
                "completion_tokens": event.get("completion_tokens"),
                "cost_usd": event.get("cost_usd"),
                "reasoning_chars": event.get("reasoning_chars"),
                "elapsed_s": event.get("elapsed_s"),
            }
            for event in calls
        ],
    }


def _extract_provenance(answer):
    match = re.search(
        r"<parameter_provenance>\s*(\[.*?\])\s*</parameter_provenance>",
        answer or "",
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return [], "appendix_missing"
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        return [], "invalid_json: %s" % exc
    if not isinstance(value, list):
        return [], "appendix_is_not_an_array"
    return value, None


def _extract_outcome(answer):
    match = re.search(
        r"<reproduction_outcome>\s*([^<]+)\s*</reproduction_outcome>",
        answer or "",
        flags=re.IGNORECASE,
    )
    return match.group(1).strip().lower() if match else None


def _approve_unmodified(session):
    log = []
    for _ in range(4):
        before = (session.get("research") or {}).get("phase")
        if before == "approved":
            break
        result = research.review_action(session, "primary")
        after = (session.get("research") or {}).get("phase")
        log.append(
            {
                "actor": "scripted_human_reviewer",
                "policy": "accept_unmodified_plan",
                "before": before,
                "after": after,
                "status": result.get("status"),
                "summary": result.get("summary"),
            }
        )
    if (session.get("research") or {}).get("phase") != "approved":
        raise RuntimeError("scripted review did not reach approved phase")
    approval.set_mode(session, approval.ALWAYS)
    return log


def run_one(task, profile, config_entry, llm, repeat, build):
    started = time.perf_counter()
    prompt = condition_text(profile, task["question"])
    session = agent.new_session(llm, unrestricted=True)
    # A physically impossible premise should be rejected before experiment planning.
    # Requiring a plan in that case rewards needless workflow ceremony and can push an
    # otherwise correct refusal into a forced tool call. Paper-reproduction cells retain
    # the full plan -> review -> approved execution gate.
    research_required = task.get("quality") != "false_premise"
    session["research_required"] = research_required
    approval.set_mode(session, approval.ASK if research_required else approval.ALWAYS)

    first_answer, first_events, _ = agent.run(
        prompt, model=llm, session=session, switches=config_entry["switches"]
    )
    first_events = [{**event, "turn": 1} for event in first_events]
    if not session.get("research"):
        review_log = []
        second_answer, second_events = "", []
    else:
        review_log = _approve_unmodified(session)
        continuation = (
            "The research plan, pseudo-data chart package, and formal execution are now "
            "approved without modification. Execute every approved run by its exact run_id, "
            "render and review every selected planned chart, then deliver the report and the "
            "required provenance/outcome appendix."
        )
        second_answer, second_events, _ = agent.run(
            continuation, model=llm, session=session, switches=config_entry["switches"]
        )
        second_events = [{**event, "turn": 2} for event in second_events]

    events = first_events + second_events
    answer = second_answer or first_answer
    provenance, provenance_error = _extract_provenance(answer)
    project = session.get("research")
    figures = [
        {
            "planned_chart_id": figure.get("planned_chart_id"),
            "figure_number": figure.get("figure_number"),
            "title": figure.get("title"),
            "series": figure.get("series"),
            "quality_review": figure.get("quality_review"),
            "provenance": figure.get("provenance"),
        }
        for figure in session.get("figures") or []
        if not figure.get("preview")
    ]
    return {
        "schema_version": "competition-run-v1",
        "task": task["id"],
        "suite": task["suite"],
        "quality": task.get("quality"),
        "config": config_entry["name"],
        "switches": config_entry["switches"],
        "prompt_profile": profile["id"],
        "prompt_version": profile["version"],
        "prompt_path": profile["_path"],
        "condition_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "provider": _provider_name(config.llm_api_base()),
        "llm": llm,
        "repeat": repeat,
        "build": build,
        "question": task["question"],
        "answer": answer,
        "planning_answer": first_answer,
        "elapsed_s": round(time.perf_counter() - started, 2),
        "stop_rule": _stop_rule(events),
        "model_calls": session.get("model_calls", 0),
        "llm_usage": _llm_usage(events),
        "tool_calls": session.get("tool_calls", 0),
        "interventions": session.get("interventions", 0),
        "qc_failures": session.get("qc_failures", 0),
        "workflow": {
            "research_required": research_required,
            "approval_policy": (
                "scripted_accept_unmodified_plan"
                if research_required
                else "not_applicable_safe_refusal"
            ),
            "review_actions": review_log,
            "final_phase": (project or {}).get("phase"),
            "plan_version": (project or {}).get("plan_version"),
        },
        "research": project,
        "successful_runs": session.get("successful_runs") or [],
        "tool_log": _tool_log(events),
        "event_log": _event_summary(events),
        "evidence": {
            "sections": sorted(session["sections_read"]),
            "models": sorted(session["models_run"]),
            "datasets": sorted(session["datasets_read"]),
        },
        "figures": figures,
        "markers": {
            "literature": harness.find_markers(answer),
            "model": harness.find_model_markers(answer),
            "data": harness.find_data_markers(answer),
        },
        "parameter_provenance": provenance,
        "provenance_parse_error": provenance_error,
        "reproduction_outcome": _extract_outcome(answer),
    }


def matrix(args):
    manifest = load_manifest()
    execution = manifest["execution"]
    wanted_tasks = args.tasks or [
        *manifest["competition_required"]["t2_paper_reconstruction"]["core_tasks"],
        *manifest["competition_required"]["t2_paper_reconstruction"]["probe_tasks"],
    ]
    task_index = load_task_index()
    missing = [task_id for task_id in wanted_tasks if task_id not in task_index]
    if missing:
        raise ValueError("unknown task id(s): %s" % ", ".join(missing))
    profiles = load_profiles(args.profiles or execution["prompt_profiles"])
    profile_ids = {profile["id"] for profile in profiles}
    missing_profiles = set(args.profiles or execution["prompt_profiles"]) - profile_ids
    if missing_profiles:
        raise ValueError("unknown prompt profile(s): %s" % ", ".join(sorted(missing_profiles)))
    configs = common.load_configs(execution["configs"])
    llms = args.llm or execution["llms"]
    repeats = args.repeats or execution["repeats"]
    return [
        (task_index[task_id], profile, config_entry, llm, repeat)
        for task_id in wanted_tasks
        for profile in profiles
        for config_entry in configs
        for llm in llms
        for repeat in range(1, repeats + 1)
    ]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="make LLM/model calls; omitted means plan only")
    parser.add_argument("--tasks", nargs="*")
    parser.add_argument("--profiles", nargs="*")
    parser.add_argument("--llm", nargs="*")
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--pace", type=float, default=3.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    cells = matrix(args)
    build = agent_tasks.build_id()
    RUNS.mkdir(parents=True, exist_ok=True)
    pending = []
    for task, profile, config_entry, llm, repeat in cells:
        name = key(task["id"], profile["id"], config_entry["name"], llm, repeat)
        if not args.force and (RUNS / name).is_file():
            continue
        pending.append((name, task, profile, config_entry, llm, repeat))

    print("competition matrix: %d cells (%d cached, %d pending), build %s" %
          (len(cells), len(cells) - len(pending), len(pending), build))
    for name, task, profile, _, llm, repeat in pending:
        print("  %s | %s | %s | r%d" % (task["id"], profile["id"], llm, repeat))
    if not args.execute:
        print("Plan only: no LLM evaluation was run. Add --execute to run pending cells.")
        return 0

    config.load_dotenv()
    written = 0
    for index, (name, task, profile, config_entry, llm, repeat) in enumerate(pending, 1):
        print("[%d/%d] %s" % (index, len(pending), name), flush=True)
        try:
            record = run_one(task, profile, config_entry, llm, repeat, build)
        except Exception:
            print(traceback.format_exc())
            return 2
        (RUNS / name).write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        written += 1
        if record.get("stop_rule") in FAULTS:
            print("Stopped on external fault %s; cached cells remain reusable." % record["stop_rule"])
            return 2
        if args.pace and index < len(pending):
            time.sleep(args.pace)
    print("%d competition record(s) written." % written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
