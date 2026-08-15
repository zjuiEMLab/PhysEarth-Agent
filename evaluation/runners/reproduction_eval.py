"""Run the four paper-reproduction questions on each configured LLM.

The runner follows the same research state machine as the UI.  It approves the authored
plan, generates and confirms pseudo-data layouts, authorizes formal execution, and then
lets the agent run the registered physical models.  Every cell is checkpointed as JSON,
so an interrupted 3 x 4 experiment resumes without spending the completed calls again.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageFilter, ImageOps

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from physearth import agent, approval, config, research  # noqa: E402

TASK_DIR = REPO / "evaluation" / "tasks" / "tier2"
RESULT_DIR = REPO / "evaluation" / "results" / "reproduction"
PAPER_FIGURE_DIR = REPO / "knowledge" / "literature" / "smrt-v1" / "figures"
CONTINUE = (
    "I approve formal execution of the reviewed research plan. Continue now: run every "
    "missing registered physical-model experiment, create and quality-review every selected "
    "figure from actual outputs, and only then report the interpretation and conclusion."
)


def _build_id():
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True
    )
    return result.stdout.strip() or "unknown"


def _safe(value):
    return "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value)


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _paper_image(path):
    image = Image.open(path).convert("L")
    image = ImageOps.contain(image, (320, 320))
    canvas = Image.new("L", (320, 320), 255)
    canvas.paste(image, ((320 - image.width) // 2, (320 - image.height) // 2))
    return np.asarray(canvas.filter(ImageFilter.FIND_EDGES), dtype=float)


def _visual_similarity(actual, reference):
    """Edge-layout correlation plus average-hash agreement; style-independent but coarse."""
    a = _paper_image(actual)
    b = _paper_image(reference)
    av, bv = a.ravel(), b.ravel()
    corr = float(np.corrcoef(av, bv)[0, 1]) if av.std() and bv.std() else 0.0
    ah = a > a.mean()
    bh = b > b.mean()
    hash_agreement = float(np.mean(ah == bh))
    return round(max(0.0, min(1.0, 0.5 * max(0.0, corr) + 0.5 * hash_agreement)), 4)


def _tokens(events):
    calls = [event for event in events if event.get("kind") == "model_call"]
    prompt = sum(int(event.get("prompt_tokens") or 0) for event in calls)
    completion = sum(int(event.get("completion_tokens") or 0) for event in calls)
    return {
        "prompt": prompt,
        "completion": completion,
        "total": prompt + completion,
        "peak_prompt": max([int(event.get("prompt_tokens") or 0) for event in calls] or [0]),
    }


def _review_to_execution(session):
    """Apply the same primary review actions as the UI and return their audit trail."""
    actions = []
    for _ in range(5):
        project = session.get("research") or {}
        phase = project.get("phase")
        if phase in ("approved", "completed", None):
            break
        result = research.review_action(session, "primary")
        actions.append(
            {"phase_before": phase, "phase_after": project.get("phase"), "summary": result["summary"]}
        )
    if research.allow_model(session):
        approval.set_mode(session, approval.ALWAYS)
    return actions


def _formal_figures(session):
    return [figure for figure in session.get("figures") or [] if not figure.get("preview")]


def _protocol_score(session):
    project = session.get("research") or {}
    plan = project.get("plan") or {}
    planned_runs = plan.get("runs") or []
    planned_ids = {run.get("id") for run in planned_runs if run.get("id")}
    successful_ids = {
        run.get("planned_run_id") for run in session.get("successful_runs") or []
        if run.get("planned_run_id")
    }
    selected = set(project.get("selected_charts") or [])
    figures = _formal_figures(session)
    plotted = {figure.get("planned_chart_id") for figure in figures}
    reviewed = [
        bool((figure.get("quality_review") or {}).get("passed")) for figure in figures
    ]
    run_coverage = len(planned_ids & successful_ids) / len(planned_ids) if planned_ids else 0.0
    figure_coverage = len(selected & plotted) / len(selected) if selected else 0.0
    qa_coverage = sum(reviewed) / len(reviewed) if reviewed else 0.0
    return {
        "planned_run_coverage": round(run_coverage, 4),
        "selected_figure_coverage": round(figure_coverage, 4),
        "figure_qa_pass_rate": round(qa_coverage, 4),
        "paper_protocol_similarity": round(0.5 * run_coverage + 0.3 * figure_coverage + 0.2 * qa_coverage, 4),
        "planned_runs": len(planned_ids),
        "successful_planned_runs": len(planned_ids & successful_ids),
    }


def run_cell(task, model, max_turns=8):
    started = time.time()
    session = agent.new_session(model)
    # Mirror app._new_session(): research tools deliberately reject an ordinary library
    # session even when it happens to contain a plan.
    session["research_required"] = True
    approval.set_mode(session, approval.ALWAYS)
    history = []
    all_events = []
    answers = []
    review_actions = []
    prompt = task["question"]
    stop_reason = None

    for turn in range(1, max_turns + 1):
        answer, events, state = agent.run(prompt, history=history, model=model, session=session)
        all_events.extend(events)
        answers.append(answer)
        history.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}])
        terminal = next(
            (
                event for event in reversed(events)
                if event.get("kind") in ("harness_stop", "harness_giveup")
                and event.get("rule") in ("upstream", "quota", "withdrawn", "global_budget")
            ),
            None,
        )
        if terminal:
            stop_reason = terminal.get("rule")
            break
        phase = (session.get("research") or {}).get("phase")
        if phase == "completed":
            break
        recovery = (session.get("research") or {}).get("recovery") or {}
        if phase == "plan_review" and recovery and not recovery.get("repairs"):
            # There is no scientifically safe automatic change left. The UI correctly
            # asks a person to revise the physical range; an unattended evaluation must
            # record that outcome instead of repeatedly approving the unchanged failure.
            stop_reason = "physical_model_failure"
            break
        review_actions.extend(_review_to_execution(session))
        phase = (session.get("research") or {}).get("phase")
        if phase == "completed":
            break
        if phase == "approved":
            gaps = research.execution_gaps(session)
            if gaps.get("missing_run_ids"):
                prompt = (
                    "Continue formal execution. Call run_planned_model once for each exact "
                    "missing run_id: %s. Do not use run_model or reconstruct parameters."
                    % ", ".join(gaps["missing_run_ids"])
                )
            elif gaps.get("figure_problem"):
                chart_ids = research.planned_chart_ids(session, missing_only=True)
                prompt = (
                    "All planned runs are already stored. Do not call the generic plot tool. "
                    "For each missing chart_id (%s), call plot_planned_chart with action=render, "
                    "then call it again with action=review. Finish the evidence-backed report."
                    % (", ".join(chart_ids) or "the selected planned charts")
                )
            else:
                prompt = CONTINUE
        elif phase is None:
            prompt = (
                "The previous planning attempt did not establish a research project. Read the "
                "paper section and model declaration, then submit a valid executable research_plan."
            )
        else:
            prompt = (
                "Continue the research workflow from phase %s. Repair the last validation error "
                "using the exact registered capabilities; do not abandon the reviewed question." % phase
            )
    else:
        stop_reason = "evaluation_turn_limit"

    phase = (session.get("research") or {}).get("phase")
    figures = _formal_figures(session)
    if phase != "completed" and stop_reason is None:
        stop_reason = "workflow_%s" % (phase or "missing")
    return {
        "task": task["id"],
        "question": task["question"],
        "llm": model,
        "build": _build_id(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(started)),
        "elapsed_s": round(time.time() - started, 2),
        "phase": phase,
        "completed": phase == "completed",
        "stop_reason": stop_reason,
        "answer": answers[-1] if answers else "",
        "answers": answers,
        "tokens": _tokens(all_events),
        "model_calls": sum(1 for event in all_events if event.get("kind") == "model_call"),
        "tool_calls": sum(1 for event in all_events if event.get("kind") == "tool_call"),
        "review_actions": review_actions,
        "event_kinds": [event.get("kind") for event in all_events],
        "events": _jsonable(all_events),
        "paper_figures": task["paper_figures"],
        "protocol": _protocol_score(session),
        "figure_count": len(figures),
        "figures": _jsonable(figures),
        "successful_runs": _jsonable(session.get("successful_runs") or []),
        "sections_read": sorted(session.get("sections_read") or []),
        "_session": session,
    }


def _persist(record, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    session = record.pop("_session")
    copied = []
    for index, figure in enumerate(_formal_figures(session), 1):
        source = Path(figure["image_path"])
        target = output_dir / ("figure-%02d.png" % index)
        shutil.copy2(source, target)
        copied.append(target)
        record["figures"][index - 1]["archived_path"] = str(target.relative_to(REPO))
    similarities = []
    for actual in copied:
        candidates = []
        for name in record["paper_figures"]:
            reference = PAPER_FIGURE_DIR / name
            if reference.is_file():
                candidates.append({"paper_figure": name, "score": _visual_similarity(actual, reference)})
        if candidates:
            best = max(candidates, key=lambda item: item["score"])
            similarities.append({"actual_figure": actual.name, "best_match": best, "all_matches": candidates})
    record["visual_similarity"] = {
        "method": "edge correlation + average-hash agreement; layout-only, not numeric curve error",
        "per_figure": similarities,
        "mean_best_match": round(float(np.mean([item["best_match"]["score"] for item in similarities])), 4)
        if similarities else None,
    }
    record["raw_sha256"] = hashlib.sha256(
        json.dumps(record, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()
    path = output_dir / "record.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def write_summary(records):
    cells = []
    for record in records:
        calls = [event for event in record.get("events") or [] if event.get("kind") == "model_call"]
        tokens = dict(record.get("tokens") or {})
        tokens.setdefault("peak_prompt", max([int(event.get("prompt_tokens") or 0) for event in calls] or [0]))
        stop_reason = record.get("stop_reason")
        if (
            not record.get("completed")
            and any(
                event.get("kind") == "research_revision"
                and event.get("rule") == "model_failure_recovery"
                for event in record.get("events") or []
            )
        ):
            stop_reason = "physical_model_failure"
        cells.append(
            {
                "task": record["task"], "llm": record["llm"], "completed": record["completed"],
                "phase": record["phase"], "stop_reason": stop_reason,
                "figures": record["figure_count"], "tokens": tokens,
                "protocol_similarity": record["protocol"]["paper_protocol_similarity"],
                "visual_similarity": record["visual_similarity"]["mean_best_match"],
                "elapsed_s": record["elapsed_s"],
            }
        )
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "methodology": {
            "success": "research phase completed with at least one formal figure and a final answer",
            "protocol_similarity": "50% planned-run coverage + 30% selected-figure coverage + 20% figure-QA pass rate",
            "visual_similarity": "coarse layout metric only; external comparison-model code is unavailable locally",
        },
        "cells": cells,
        "success_rate": round(sum(bool(c["completed"] and c["figures"]) for c in cells) / len(cells), 4)
        if cells else None,
        "total_tokens": sum(c["tokens"]["total"] for c in cells),
    }
    path = RESULT_DIR / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def load_all_records():
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(RESULT_DIR.glob("*/*/record.json"))
    ]


def load_canonical_tasks():
    """Load Tier-2 scientific questions without duplicating IDs in the runner."""
    tasks = []
    for path in sorted(TASK_DIR.glob("*.yaml")):
        task = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if (
            task.get("suite") == "tier2"
            and task.get("tier") == 2
            and task.get("evaluation_kind") == "scientific_question_demo"
        ):
            tasks.append(task)
    return tasks


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=None)
    parser.add_argument("--tasks", nargs="*", default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-turns", type=int, default=8)
    args = parser.parse_args(argv)
    config.load_dotenv()
    models = args.models or config.llm_models()
    tasks = load_canonical_tasks()
    if args.tasks:
        requested = set(args.tasks)
        tasks = [
            task for task in tasks
            if task.get("id") in requested or task.get("legacy_id") in requested
        ]
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    total = len(models) * len(tasks)
    index = 0
    for model in models:
        for task in tasks:
            index += 1
            output_dir = RESULT_DIR / _safe(model) / task["id"]
            record_path = output_dir / "record.json"
            if record_path.is_file() and not args.force:
                print("[%d/%d] cached %s / %s" % (index, total, model, task["id"]), flush=True)
                records.append(json.loads(record_path.read_text(encoding="utf-8")))
                continue
            print("[%d/%d] running %s / %s" % (index, total, model, task["id"]), flush=True)
            record = run_cell(task, model, max_turns=args.max_turns)
            path = _persist(record, output_dir)
            stored = json.loads(path.read_text(encoding="utf-8"))
            records.append(stored)
            print(
                "  -> phase=%s figures=%d tokens=%d stop=%s" % (
                    stored["phase"], stored["figure_count"], stored["tokens"]["total"],
                    stored["stop_reason"] or "none",
                ), flush=True,
            )
    # A filtered/resumed invocation must not erase the other cells from the matrix.
    summary = write_summary(load_all_records())
    print("success_rate=%.1f%% total_tokens=%d" % (100 * summary["success_rate"], summary["total_tokens"]))


if __name__ == "__main__":
    main()
