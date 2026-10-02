"""Run the frozen competition matrix through the deployed research workflow.

The default command is deliberately a no-cost plan. Add ``--execute`` to make LLM calls.
Every cell is cached independently by task, prompt profile, LLM, config and repeat.

    python evaluation/runners/competition.py
    python evaluation/runners/competition.py --execute --tasks q1-sparse-medium
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_tasks  # noqa: E402
import common  # noqa: E402
from physearth.harness import approval, results  # noqa: E402

from physearth import agent, config, harness, research  # noqa: E402

sys.path.insert(0, str(common.ROOT))
from metrics import figure3, judge, reference_series  # noqa: E402

MANIFEST = common.ROOT / "competition.yaml"
PROMPTS = common.ROOT / "prompts"
RUNS = common.RESULTS / "competition" / "runs"
FIGURES = common.RESULTS / "competition" / "figures"
REPORTS = common.RESULTS / "competition" / "reports"
JUDGE_PREFLIGHT = common.RESULTS / "competition" / "judge_preflight.json"
FIGURE_STANDARD = "evaluation/standards/q1_figure3.yaml"
REPORT_STANDARD = "evaluation/standards/report_judge.yaml"
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




# What the scripted reviewer sends once it has approved the plan unmodified. The report is
# written in this turn, so the appendix the evaluation scores is restated here: asked for
# only in the first turn, it was lost in every recorded Q1 report before this.
CONTINUATION = (
    "The research plan, pseudo-data chart package, and formal execution are now "
    "approved without modification. Execute every approved run by its exact run_id, "
    "render and review every selected planned chart, then deliver the report and the "
    "required provenance/outcome appendix.\n\n" + PROVENANCE_APPENDIX
)


# What the scripted reviewer answers when the capability check asks whether to plan the
# supported components only, and how many times in one cell it answers.
CAPABILITY_CONFIRMATIONS = 3
CAPABILITY_CONFIRMATION = (
    "Yes. I confirm the partial scope exactly as your capability check reported it. "
    "Generate the research plan for the supported components only, and name everything "
    "outside that scope as unavailable in the report."
)


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
            if task.get("legacy_id"):
                tasks[task["legacy_id"]] = task
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
                    "render_check": data.get("render_check"),
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
        "intervention", "detail", "reason", "upstream", "prompt_tokens",
        "cached_prompt_tokens", "completion_tokens", "first_token_s", "attempt", "cost_usd",
        "reasoning_chars", "elapsed_s",
    )
    # What the trace view needs to redraw a step: the one-line result, the arguments the
    # model sent, and the reasons a gate gave. Bounded, and passed through the redactor.
    trace_fields = ("summary", "problems", "unresolved", "markers", "decision", "model")
    secret_values = [config.llm_api_key(), config.eval_llm_api_key()]

    def redact(value):
        text = str(value or "")
        for secret in secret_values:
            if secret:
                text = text.replace(str(secret), "[REDACTED]")
        return re.sub(
            r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,}]+",
            r"\1[REDACTED]",
            text,
        )

    def safe(value):
        return redact(value)[:800]

    summary = []
    for event in events:
        item = {field: event.get(field) for field in keep if event.get(field) is not None}
        if "upstream" in item:
            item["upstream"] = safe(item["upstream"])
        # Why a tool call failed is in its data, not its one-line summary: keep the error
        # code and the structured problems, bounded, so a refused plan can be diagnosed
        # from the record after the session log is gone.
        data = event.get("data") or {}
        if event.get("kind") == "tool_call" and event.get("status") != "success":
            if data.get("error_code"):
                item["error_code"] = safe(data["error_code"])
            if data.get("problems") and event.get("problems") is None:
                item["problems"] = [
                    safe(json.dumps(entry, ensure_ascii=False, default=str))
                    if isinstance(entry, dict) else safe(entry)
                    for entry in list(data["problems"])[:8]
                ]
        for field in trace_fields:
            value = event.get(field)
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                item[field] = [safe(entry) for entry in list(value)[:8]]
            else:
                item[field] = safe(value)
        if event.get("arguments") is not None:
            text = redact(json.dumps(event["arguments"], ensure_ascii=False, default=str))
            item["arguments"] = json.loads(text) if len(text) <= 6000 else {
                "_truncated": text[:6000]
            }
        summary.append(item)
    return summary


def _provider_name(base_url):
    value = str(base_url or "").lower()
    if "openrouter.ai" in value:
        return "openrouter"
    if "modelscope.cn" in value:
        return "modelscope"
    return "openai_compatible"


def _llm_usage(events):
    calls = [event for event in events if event.get("kind") == "model_call"]
    failed = [event for event in events if event.get("kind") == "empty_response"]
    cached = [event.get("cached_prompt_tokens") for event in calls]
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
        # A failed attempt is billed when it fails mid-stream but reports no usage, so it is
        # counted here rather than silently dropped.
        "failed_attempts": len(failed),
        "failed_attempt_faults": sorted({str(event.get("detail"))[:120] for event in failed}),
        "cached_prompt_tokens": (
            sum(int(value) for value in cached)
            if calls and all(isinstance(value, (int, float)) for value in cached)
            else None
        ),
        "per_call": [
            {
                "turn": event.get("turn"),
                "index": event.get("index"),
                "prompt_tokens": event.get("prompt_tokens"),
                "cached_prompt_tokens": event.get("cached_prompt_tokens"),
                "completion_tokens": event.get("completion_tokens"),
                "cost_usd": event.get("cost_usd"),
                "reasoning_chars": event.get("reasoning_chars"),
                "elapsed_s": event.get("elapsed_s"),
                "first_token_s": event.get("first_token_s"),
                "attempt": event.get("attempt"),
            }
            for event in calls
        ],
    }


def _judge_usage(*judgements):
    """Combine report and visual-figure judge usage without exposing credentials."""
    usage = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens", "cost_usd"):
        values = [
            (judgement.get("usage") or {}).get(name)
            for judgement in judgements
            if judgement.get("complete")
        ]
        usage[name] = (
            sum(values)
            if values and all(isinstance(value, (int, float)) for value in values)
            else None
        )
    return usage


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


def _artifact_suffix(config_name):
    return {"full": "full", "no-harness": "baseline"}.get(
        str(config_name or ""), SAFE.sub("-", str(config_name or "scenario"))
    )


def _artifact_tag(record):
    return "_".join(
        SAFE.sub("-", str(value or "unknown"))
        for value in (
            record.get("task"),
            record.get("prompt_profile"),
            record.get("llm"),
            "r%s" % (record.get("repeat") or "1"),
        )
    )


def _archive_figure(figure, config_name, artifact_tag):
    source = Path(str(figure.get("image_path") or figure.get("archived_image_path") or ""))
    if not source.is_absolute():
        source = common.REPO / source
    if not source.is_file():
        return None
    suffix = _artifact_suffix(config_name)
    if not figure.get("image_path") and source.stem.endswith(f"_{artifact_tag}_{suffix}"):
        return str(source.relative_to(common.REPO)).replace("\\", "/")
    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / (
        f"{source.stem}_{artifact_tag}_{suffix}"
        f"{source.suffix or '.png'}"
    )
    if not target.exists():
        shutil.copyfile(source, target)
    return str(target.relative_to(common.REPO)).replace("\\", "/")


def _archive_report(answer, config_name, artifact_tag):
    REPORTS.mkdir(parents=True, exist_ok=True)
    # Named by the report's own digest, as a figure is by its source file: a rerun of the
    # same cell writes its own report instead of inheriting an older run's file.
    digest = hashlib.sha256(str(answer or "").encode("utf-8")).hexdigest()[:24]
    target = REPORTS / f"{digest}_{artifact_tag}_report_{_artifact_suffix(config_name)}.md"
    if not target.exists():
        target.write_text(
            "# Reproduction report\n\n<!-- Generated artifact; this file is human-editable. -->\n\n"
            + str(answer or "")
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return str(target.relative_to(common.REPO)).replace("\\", "/")


def archive_record_artifacts(record):
    """Archive editable report and scenario-labelled figures for a stored run."""
    tag = _artifact_tag(record)
    config_name = record.get("config")
    for figure in record.get("figures") or []:
        archived = _archive_figure(figure, config_name, tag)
        if archived:
            figure["archived_image_path"] = archived
    report_path = _archive_report(record.get("answer"), config_name, tag)
    record["archived_report_path"] = report_path
    record["report_artifact"] = {
        "path": report_path,
        "format": "markdown",
        "editable": True,
    }
    record["evaluation_standards"] = {
        "figure": FIGURE_STANDARD,
        "report_judge": REPORT_STANDARD,
    }
    return record


def _numeric_results(session):
    owner = session.get("id")
    archived = []
    for item in session.get("successful_runs") or []:
        payload = results.get(item.get("handle"), owner)
        if payload is None:
            continue
        archived.append(
            {
                "handle": item.get("handle"),
                "planned_run_id": item.get("planned_run_id"),
                "model": payload.get("model"),
                "version": payload.get("version"),
                "spec": payload.get("spec") or {},
                "axis": payload.get("axis"),
                "series": payload.get("series") or {},
                "units": payload.get("units") or {},
            }
        )
    return archived


def _success_metric(record):
    workflow = record.get("workflow") or {}
    workflow_finished = (
        not workflow.get("research_required") or workflow.get("final_phase") == "completed"
    )
    return bool(
        str(record.get("answer") or "").strip()
        and record.get("numeric_results")
        and record.get("figures")
        and not workflow.get("review_error")
        and workflow_finished
        and record.get("stop_rule") is None
    )


def _balanced_pending_order(pending):
    """Latin-square the conditions of a batch so timing is not confounded by order.

    Repeat r runs the conditions rotated by r - 1, so every condition takes every position
    once per cycle whatever conditions the batch holds.
    """
    names = []
    for item in pending:
        if item[3]["name"] not in names:
            names.append(item[3]["name"])

    def order(item):
        _name, task, _profile, config_entry, _llm, repeat = item
        shift = (repeat - 1) % len(names)
        sequence = names[shift:] + names[:shift]
        return (task["id"], repeat, sequence.index(config_entry["name"]))

    return sorted(pending, key=order)


def _figure_score(record, fixture, oracle):
    """The task's own scorer; a scorer fault is recorded, never allowed to lose the run."""
    plot = {"passed": any(not item.get("preview") for item in record.get("figures") or [])}
    try:
        if fixture.get("scorer") == "figure3":
            return figure3.score(record, oracle=oracle)
        if fixture.get("scorer") == "reference_series":
            return reference_series.score(record, fixture, reference_series.load_oracle(fixture))
    except Exception as exc:
        return {
            "passed": None,
            "status": "not_scoreable",
            "scoring_error": f"{type(exc).__name__}: {exc}",
            "plot": plot,
        }
    return {"passed": None, "status": "not_scoreable", "plot": plot}


def run_one(
    task,
    profile,
    config_entry,
    llm,
    repeat,
    build,
    *,
    batch_approved=False,
    oracle=None,
    judge_enabled=False,
):
    started = time.perf_counter()
    prompt = condition_text(profile, task["question"])
    session = agent.new_session(llm, unrestricted=True)
    session["evaluation_batch_approved"] = bool(batch_approved)
    # A physically impossible premise should be rejected before experiment planning.
    # Requiring a plan in that case rewards needless workflow ceremony and can push an
    # otherwise correct refusal into a forced tool call. Paper-reproduction cells retain
    # the full plan -> review -> approved execution gate.
    raw_mode = config_entry["switches"].get("execution_access") == "raw_smrt"
    research_required = task.get("quality") != "false_premise" and not raw_mode
    session["research_required"] = research_required
    approval.set_mode(session, approval.ASK if research_required else approval.ALWAYS)

    first_answer, first_events, _ = agent.run(
        prompt, model=llm, session=session, switches=config_entry["switches"]
    )
    first_events = [{**event, "turn": 1} for event in first_events]
    review_error = None
    capability_log = []
    while (
        batch_approved
        and len(capability_log) < CAPABILITY_CONFIRMATIONS
        and not session.get("research")
        and (session.get("capability_review") or {}).get("status") == "waiting_user"
    ):
        # The capability check stopped to ask whether a partial scope is acceptable. The
        # scripted reviewer answers as it answers a plan: it accepts what was reported,
        # unmodified, and the agent records that consent itself. A failed plan can send
        # the agent back to the check, which asks again; a person would answer again.
        capability_log.append(
            {
                "actor": "scripted_human_reviewer",
                "policy": "confirm_reported_partial_scope",
                "before": "capability waiting_user",
                "summary": CAPABILITY_CONFIRMATION,
            }
        )
        first_answer, more_events, _ = agent.run(
            CAPABILITY_CONFIRMATION, model=llm, session=session,
            switches=config_entry["switches"],
        )
        turn = max((event["turn"] for event in first_events), default=1) + 1
        first_events += [{**event, "turn": turn} for event in more_events]
        status = (session.get("capability_review") or {}).get("status")
        capability_log[-1]["after"] = f"capability {status}"
    next_turn = max((event["turn"] for event in first_events), default=1) + 1
    if not session.get("research"):
        review_log = list(capability_log)
        second_answer, second_events = "", []
    else:
        if not batch_approved:
            review_error = "evaluation batch approval required before physical execution"
            review_log = [
                {
                    "actor": "evaluation_runner",
                    "status": "waiting_user",
                    "summary": review_error,
                }
            ]
        try:
            if not review_error:
                review_log = capability_log + _approve_unmodified(session)
        except RuntimeError as exc:
            # A text-only paper may correctly be unable to produce a reviewable figure-
            # reproduction plan. Archive that stopped outcome instead of crashing the
            # scenario matrix or pretending that an invalid plan was approved.
            review_error = str(exc)
            review_log = [
                {
                    "actor": "scripted_human_reviewer",
                    "policy": "accept_unmodified_plan",
                    "status": "not_approvable",
                    "summary": review_error,
                }
            ]
        if review_error:
            second_answer, second_events = "", []
        else:
            continuation = CONTINUATION
            second_answer, second_events, _ = agent.run(
                continuation, model=llm, session=session, switches=config_entry["switches"]
            )
            second_events = [{**event, "turn": next_turn} for event in second_events]

    events = first_events + second_events
    answer = second_answer or first_answer
    provenance, provenance_error = _extract_provenance(answer)
    project = session.get("research")
    citation_check = harness.check_citations(
        answer,
        session["sections_read"],
        session["models_run"],
        session["datasets_read"],
        session["abstracts_seen"],
        session["skills_read"],
        session["guidelines_read"],
        session["paper_figures_read"],
    )
    figures = []
    for figure in session.get("figures") or []:
        if figure.get("preview"):
            continue
        figures.append({
            "planned_chart_id": figure.get("planned_chart_id"),
            "figure_number": figure.get("figure_number"),
            "title": figure.get("title"),
            "subtitle": figure.get("subtitle"),
            "x_label": figure.get("x_label"),
            "y_label": figure.get("y_label"),
            "kind": figure.get("kind"),
            "series": figure.get("series"),
            "quality_review": figure.get("quality_review"),
            "provenance": figure.get("provenance"),
            "image_path": figure.get("image_path"),
        })
    record = {
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
            "review_error": review_error,
            "final_phase": (project or {}).get("phase"),
            "plan_version": (project or {}).get("plan_version"),
        },
        "research": project,
        "successful_runs": session.get("successful_runs") or [],
        "numeric_results": _numeric_results(session),
        "tool_log": _tool_log(events),
        "event_log": _event_summary(events),
        "evidence": {
            "sections": sorted(session["sections_read"]),
            "models": sorted(session["models_run"]),
            "datasets": sorted(session["datasets_read"]),
            "abstracts": sorted(session["abstracts_seen"]),
            "skills": sorted(session["skills_read"]),
            "guidelines": sorted(session["guidelines_read"]),
            "paper_figures": sorted(session["paper_figures_read"]),
            "raw_pdf_pages": sorted(session.get("raw_pdf_pages_read") or []),
        },
        "citation_check": citation_check,
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
    archive_record_artifacts(record)
    for figure in record.get("figures") or []:
        figure.pop("image_path", None)
    fixture_path = task.get("reference_fixture")
    if fixture_path:
        fixture = common.load_yaml(common.REPO / fixture_path)
        figure_score = _figure_score(record, fixture, oracle)
        figure_judgement = (
            judge.judge_figure(record, candidate_models=(llm,), fixture=fixture)
            if judge_enabled
            else {"complete": False, "passed": False, "status": "not_run"}
        )
        deterministic = figure3.deterministic_report_checks(
            record, figure_score, figure_judgement, fixture=fixture
        )
        report_judgement = (
            judge.judge_report(
                record,
                task,
                figure_score,
                deterministic,
                candidate_models=(llm,),
                figure_judgement=figure_judgement,
                fixture=fixture,
            )
            if judge_enabled
            else {"complete": False, "passed": False, "status": "not_run"}
        )
        successful = _success_metric(record)
        report_correct = bool(report_judgement.get("passed"))
        figure_status = (
            figure_judgement.get("status", "not_scoreable")
            if figure_judgement.get("complete")
            else "not_scoreable"
        )
        record["dashboard_metrics"] = {
            "evaluation_complete": bool(
                figure_judgement.get("complete") and report_judgement.get("complete")
            ),
            "successful": successful,
            "figure_result_correct": figure_status,
            "report_correct": (
                "not_scoreable"
                if not report_judgement.get("complete")
                else "pass" if report_correct else "fail"
            ),
            "overall_correct": (
                "not_scoreable"
                if figure_status == "not_scoreable"
                or not report_judgement.get("complete")
                else "pass"
                if successful and figure_status == "pass" and report_correct
                else "fail"
            ),
            "figure_result": figure_score,
            "figure_judgement": figure_judgement,
            "deterministic_report": deterministic,
            "report_judgement": report_judgement,
            "judge_usage": _judge_usage(figure_judgement, report_judgement),
            "figure_judge_usage": figure_judgement.get("usage") or {},
        }
    return record


def grid(args):
    """The per-model grid: one reproduction task per registered model, harness on."""
    manifest = load_manifest()
    block = manifest["model_grid"]
    task_index = load_task_index()
    missing = [task_id for task_id in block["tasks"] if task_id not in task_index]
    if missing:
        raise ValueError(f"unknown model-grid task id(s): {', '.join(missing)}")
    profiles = load_profiles(manifest["execution"]["prompt_profiles"])
    llms = args.llm or block.get("llms") or manifest["execution"]["llms"]
    repeats = args.repeats or block["repeats"]
    return [
        (task_index[task_id], profile, config_entry, llm, repeat)
        for task_id in (args.tasks or block["tasks"])
        for profile in profiles
        for config_entry in common.load_configs(block["configs"])
        for llm in llms
        for repeat in range(1, repeats + 1)
    ]


def matrix(args):
    if getattr(args, "grid", False):
        return grid(args)
    manifest = load_manifest()
    execution = manifest["execution"]
    wanted_tasks = args.tasks or [
        *manifest["competition_required"]["t2_paper_reconstruction"]["core_tasks"],
        *manifest["competition_required"]["t2_paper_reconstruction"]["probe_tasks"],
    ]
    task_index = load_task_index()
    missing = [task_id for task_id in wanted_tasks if task_id not in task_index]
    if missing:
        raise ValueError(f"unknown task id(s): {', '.join(missing)}")
    profiles = load_profiles(args.profiles or execution["prompt_profiles"])
    profile_ids = {profile["id"] for profile in profiles}
    missing_profiles = set(args.profiles or execution["prompt_profiles"]) - profile_ids
    if missing_profiles:
        raise ValueError(
            f"unknown prompt profile(s): {', '.join(sorted(missing_profiles))}"
        )
    configs = common.load_configs(getattr(args, "configs", None) or execution["configs"])
    llms = args.llm or execution["llms"]
    repeats = args.repeats or execution["repeats"]
    cells = [
        (task_index[task_id], profile, config_entry, llm, repeat)
        for task_id in wanted_tasks
        for profile in profiles
        for config_entry in configs
        for llm in llms
        for repeat in range(1, repeats + 1)
    ]
    # The robustness block joins only the frozen default; an explicit narrowing on the
    # command line means exactly the cells asked for.
    robustness = manifest.get("robustness") or {}
    narrowed = args.tasks or args.llm or args.repeats or getattr(args, "configs", None)
    if robustness and not narrowed:
        unknown = [task_id for task_id in robustness["tasks"] if task_id not in task_index]
        if unknown:
            raise ValueError(f"unknown robustness task id(s): {', '.join(unknown)}")
        cells += [
            (task_index[task_id], profile, config_entry, llm, repeat)
            for task_id in robustness["tasks"]
            for profile in profiles
            for config_entry in common.load_configs(robustness["configs"])
            for llm in robustness["llms"]
            for repeat in range(1, robustness["repeats"] + 1)
        ]
    return cells


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="make LLM/model calls; omitted means plan only",
    )
    parser.add_argument("--tasks", nargs="*")
    parser.add_argument("--profiles", nargs="*")
    parser.add_argument(
        "--configs",
        nargs="*",
        help="override the manifest configurations for a bounded ablation run",
    )
    parser.add_argument("--llm", nargs="*")
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--pace", type=float, default=3.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--runs-dir",
        help="write records here instead of the evaluation record directory (a smoke run)",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="run the per-model grid (model_grid in competition.yaml) instead of the matrix",
    )
    parser.add_argument(
        "--approve-batch",
        action="store_true",
        help="record explicit human approval for the printed fixed evaluation batch",
    )
    parser.add_argument(
        "--max-spend-usd",
        type=float,
        default=3.0,
        help="stop before the next cell once the batch's candidate LLM cost reaches this; 0 "
        "disables",
    )
    args = parser.parse_args(argv)

    cells = matrix(args)
    build = agent_tasks.build_id()
    runs = Path(args.runs_dir).resolve() if args.runs_dir else RUNS
    if args.runs_dir:
        # A smoke run keeps its figures and reports beside its records, so it can never
        # stand in for an evaluation cell's artifacts.
        global FIGURES, REPORTS
        FIGURES, REPORTS = runs / "figures", runs / "reports"
    runs.mkdir(parents=True, exist_ok=True)
    pending = []
    for task, profile, config_entry, llm, repeat in cells:
        name = key(task["id"], profile["id"], config_entry["name"], llm, repeat)
        if not args.force and (runs / name).is_file():
            continue
        pending.append((name, task, profile, config_entry, llm, repeat))
    pending = _balanced_pending_order(pending)

    print(
        f"competition matrix: {len(cells)} cells "
        f"({len(cells) - len(pending)} cached, {len(pending)} pending), build {build}"
    )
    for _name, task, profile, config_entry, llm, repeat in pending:
        print(
            f"  {task['id']} | {profile['id']} | {config_entry['name']} | {llm} | r{repeat}"
        )
    if not args.execute:
        print("Plan only: no LLM evaluation was run. Add --execute to run pending cells.")
        return 0
    if not pending:
        print("All requested cells are cached; no judge, LLM, or physical-model call was made.")
        return 0

    if not args.approve_batch:
        print("\nCAPACITY AND APPROVAL REQUIRED")
        print(f"  candidate sessions: {len(pending)}")
        print(
            "  judge requests: one preflight (up to 3 attempts) plus up to 3 attempts "
            "per completed report (30 maximum)"
        )
        print(
            "No LLM or physical-model call was made. Re-run the identical command with "
            "--approve-batch only after the user explicitly approves this batch."
        )
        return 3

    config.load_dotenv()
    preflight = judge.preflight(candidate_models={llm for _, _, _, _, llm, _ in pending})
    preflight["batch"] = {
        "build": build,
        "candidate_models": sorted({llm for _, _, _, _, llm, _ in pending}),
        "candidate_sessions": len(pending),
        "conditions": sorted({item[3]["name"] for item in pending}),
        "repeats": sorted({item[5] for item in pending}),
    }
    JUDGE_PREFLIGHT.parent.mkdir(parents=True, exist_ok=True)
    JUDGE_PREFLIGHT.write_text(
        json.dumps(preflight, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if not preflight.get("passed"):
        print(f"Judge preflight failed before candidate execution: {preflight.get('error')}")
        return 2
    oracle = None
    if any(
        common.load_yaml(common.REPO / item[1]["reference_fixture"]).get("scorer") == "figure3"
        for item in pending
        if item[1].get("reference_fixture")
    ):
        oracle = figure3.build_oracle()
        figure3.ORACLE_PATH.parent.mkdir(parents=True, exist_ok=True)
        figure3.ORACLE_PATH.write_text(
            json.dumps(oracle, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"Figure 3 oracle uses SMRT {oracle.get('smrt_version')}.")
    print(f"Judge preflight passed with {preflight.get('model')}.")
    written = 0
    spent = 0.0
    for index, (name, task, profile, config_entry, llm, repeat) in enumerate(pending, 1):
        if args.max_spend_usd and spent >= args.max_spend_usd:
            print(
                f"Stopped: the batch spent USD {spent:.2f} of its USD {args.max_spend_usd:.2f} "
                "limit; cached cells remain reusable."
            )
            return 2
        print(f"[{index}/{len(pending)}] {name}", flush=True)
        try:
            record = run_one(
                task,
                profile,
                config_entry,
                llm,
                repeat,
                build,
                batch_approved=True,
                oracle=oracle,
                judge_enabled=True,
            )
        except Exception:
            print(traceback.format_exc())
            return 2
        (runs / name).write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        written += 1
        spent += (record.get("llm_usage") or {}).get("cost_usd") or 0.0
        if not (record.get("dashboard_metrics") or {}).get("evaluation_complete", True):
            print(
                "Evaluation incomplete for this cell; recording it and continuing the "
                "remaining fixed batch."
            )
        if record.get("stop_rule") in FAULTS:
            print(
                f"Stopped on external fault {record['stop_rule']}; "
                "cached cells remain reusable."
            )
            return 2
        if args.pace and index < len(pending):
            time.sleep(args.pace)
    print(f"{written} competition record(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
