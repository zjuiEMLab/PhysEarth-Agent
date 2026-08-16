"""One turn of the agent: prompt, completion, tool calls, and the trace of both."""

import json
import time

from physearth import harness, prompt, research, tools
from physearth import session as session_state
from physearth.agent import completion as _completion
from physearth.agent.catalogue import CATALOGUE, new_session, new_state, resolve_model
from physearth.agent.completion import _Completion, _tool_arguments
from physearth.agent.constants import (
    _TOOL_BYPASS_PATTERNS,
    EMPTY_RESPONSE_RETRIES,
    MAX_OUTPUT_TOKENS,
    RATE_LIMIT_BACKOFF_S,
    RATE_LIMIT_RETRIES,
    RETRY_BACKOFF_S,
)
from physearth.agent.faults import _dead_for_today, _fault, _rate_limited, _upstream_text
from physearth.agent.messages import _compact_messages, _messages, transcript
from physearth.agent.results import _allowed_marker_correction, _record_tool_result
from physearth.agent.trace import _event
from physearth.harness import approval, audit, budget
from physearth.harness import switches as switch_flags


def _requests_tool_bypass(question):
    """Recognize an explicit request to disable evidence/model tools.

    This is a generic safety boundary. If a user asks for a scientific claim while
    explicitly disabling the tools that establish evidence, the agent must not silently
    turn that request into an unsupported answer or execute a tool anyway.
    """
    text = str(question or "")
    return any(pattern.search(text) for pattern in _TOOL_BYPASS_PATTERNS)


def stream(question, history=None, model=None, session=None, switches=None):
    """Run one turn, yielding (answer, events, state) every time something happens.

    `session` carries everything the conversation has already read, run and stored. It
    is created by the caller and lives until the visitor clears the conversation.

    `switches` is the ablation control. It is only ever passed by the evaluation suite;
    the application leaves it None, which turns everything on.
    """
    session = new_session(model) if session is None else session
    session["model"] = resolve_model(
        model or session.get("model"), session.get("unrestricted", False)
    )
    session["turns"] = session.get("turns", 0) + 1
    audit.bind(session, turn=session["turns"])
    audit.emit(
        "agent_turn_started",
        session=session,
        question=question,
        history_messages=len(history or []),
    )
    state = session_state.new_state(session, session["model"])
    state["switches"] = switch_flags.resolve(switches)
    events = []
    answer = ""
    if _requests_tool_bypass(question):
        session["tool_bypass_requested"] = True
        events.append(
            _event(
                "tool_bypass_requested",
                rule="explicit_user_tool_bypass",
                detail="The user explicitly prohibited evidence and model tools.",
            )
        )
        answer = (
            "I can’t provide an evidence-backed scientific or model-result claim while the "
            "tools are explicitly disabled. Enable the literature and model tools, and I can "
            "verify the relevant source, parameters, and result before answering."
        )
        events.append(
            _event(
                "tool_bypass_blocked",
                rule="evidence_required",
                detail="No model, literature, dataset, or other tool was called.",
            )
        )
        state["phase"] = "done"
        yield answer, events, state
        return
    context = session.get("research_context") or {}
    guided_reproduction = bool(session.get("research_required")) or context.get("reproduction_case") == "paper-reproduction"
    reproduction_preflight = research.is_reproduction_question(question) or guided_reproduction
    if reproduction_preflight:
        session["research_required"] = True
        context = session.setdefault("research_context", {})
        context["reproduction_case"] = "paper-reproduction"
        context["question"] = question
        events.append(
            _event(
                "research_mode_selected",
                rule="agent_preflight_reproduction",
                case_id="paper-reproduction",
                detail=(
                    "The agent selected the reviewed research workflow before the first model "
                    "request because this question matches a registered paper reproduction."
                ),
            )
        )
    review_attempts = {}
    tool_failure_streak = {"name": None, "count": 0, "detail": ""}
    repeated_success = {"signature": None, "count": 0}
    last_plan_error = ""
    last_plan_problems = []
    forced_tool_name = None
    # A turn that reaches the review gate without having called research_plan has not
    # acted on what the user asked; see the gate below.
    plan_tool_called = False
    revision_forced = False
    segments = []

    allowed, message = budget.acquire()
    if not allowed:
        events.append(_event("harness_stop", rule="global_budget", reason=message))
        state["phase"] = "done"
        yield message, events, state
        return

    messages = _messages(question, history, state)
    # Resolved through the module rather than bound at import, so a test can substitute
    # the provider client on physearth.agent.completion and have this call see it.
    client = _completion._client()
    model_id = state["model"]

    while True:
        spend = harness.check_budget(state)
        if not spend["passed"]:
            events.append(
                _event("harness_stop", rule="budget", scope=spend["scope"], reason=spend["reason"])
            )
            answer = answer or (
                "Stopped: %s. Clear the conversation to start a fresh budget."
                % spend["reason"]
                if spend["scope"] == "session"
                else "Stopped: %s. Ask a narrower follow-up question." % spend["reason"]
            )
            break

        state["phase"] = "calling_model"
        yield answer, events, state

        messages = _compact_messages(messages)

        completion = None
        requested_tool = forced_tool_name
        last_fault = "no choices"
        last_upstream = ""
        model_dead = ""
        attempt, budget_left = 0, EMPTY_RESPONSE_RETRIES
        while attempt < budget_left:
            attempt += 1
            started = time.perf_counter()
            candidate = _Completion()
            try:
                chunks = client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    tools=tools.specs(state["switches"]),
                    tool_choice=(
                        {"type": "function", "function": {"name": requested_tool}}
                        if requested_tool else "auto"
                    ),
                    parallel_tool_calls=False,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    stream=True,
                    stream_options={"include_usage": True},
                )
                for chunk in chunks:
                    if candidate.feed(chunk) and candidate.content:
                        # Keep the authoritative answer in sync with the streamed frame.
                        # Several lifecycle events are yielded immediately after streaming
                        # finishes (model_call, tool_start, validation gates).  If ``answer``
                        # still contains the previous block, those frames briefly replace the
                        # visible response with stale or empty text before it comes back on the
                        # next token, which looks like the Conversation panel is flashing.
                        answer = transcript(segments, candidate.content)
                        yield answer, events, state
            except Exception as exc:
                last_fault = _fault(exc)
                last_upstream = _upstream_text(exc)
                dead = _dead_for_today(exc)
                if dead:
                    model_dead = dead
                    break
                events.append(
                    _event(
                        "empty_response",
                        attempt=attempt,
                        detail=last_fault,
                        model=model_id,
                        upstream=last_upstream,
                    )
                )
                yield answer, events, state
                # A rate limit is worth waiting out rather than reporting: it clears on
                # its own, and it is the one upstream fault where giving up quickly turns
                # a slow answer into no answer. It gets its own, longer, retry budget.
                if _rate_limited(exc):
                    budget_left = max(budget_left, RATE_LIMIT_RETRIES)
                    time.sleep(RATE_LIMIT_BACKOFF_S * attempt)
                else:
                    time.sleep(RETRY_BACKOFF_S * attempt)
                continue
            if not candidate.empty():
                completion = candidate
                break
            last_fault = "no choices"
            events.append(_event("empty_response", attempt=attempt, detail=last_fault))
            yield answer, events, state
            time.sleep(RETRY_BACKOFF_S * attempt)

        if completion is None:
            events.append(
                _event(
                    "harness_stop",
                    rule=model_dead or "upstream",
                    reason=last_fault,
                    model=model_id,
                    upstream=last_upstream,
                )
            )
            others = " or ".join(m["label"] for m in CATALOGUE if m["id"] != model_id)
            if model_dead == "quota":
                answer = answer or (
                    "The available quota or account balance for %s is exhausted. Pick another "
                    "configured model in the switcher at the top: %s, or update the provider "
                    "credentials/billing. Nothing was computed, so nothing here is a modelling "
                    "result." % (model_id, others)
                )
            elif model_dead == "withdrawn":
                answer = answer or (
                    "%s is not being served by the endpoint right now, so this run never "
                    "started. Pick another model in the switcher at the top: %s."
                    % (model_id, others)
                )
            else:
                answer = answer or (
                    "The inference endpoint refused %d times in a row: %s. This is an upstream "
                    "fault, not a modelling result; the run trace has what the endpoint said."
                    % (EMPTY_RESPONSE_RETRIES, last_fault)
                )
            break

        # A forced choice applies to one completed provider response. If that response
        # still fails validation, the relevant gate below can force the corrective turn
        # again with the exact error in context.
        forced_tool_name = None

        session_state.bump(state, "model_calls")
        session_state.bump(state, "prompt_tokens", completion.prompt_tokens or 0)
        session_state.bump(state, "completion_tokens", completion.completion_tokens or 0)
        events.append(
            _event(
                "model_call",
                index=state["model_calls"],
                elapsed_s=round(time.perf_counter() - started, 2),
                prompt_tokens=completion.prompt_tokens,
                completion_tokens=completion.completion_tokens,
                cost_usd=completion.cost_usd,
                cost_details=completion.cost_details,
                reasoning_chars=completion.reasoning,
            )
        )
        yield answer, events, state

        calls = completion.tool_calls()
        if calls:
            parsed_calls = []
            invalid_call = None
            for call in calls:
                try:
                    arguments, canonical, repair_note = _tool_arguments(call["arguments"])
                except ValueError as exc:
                    invalid_call = (call, str(exc))
                    break
                parsed_calls.append((call, arguments, canonical, repair_note))
            if invalid_call is not None:
                call, detail = invalid_call
                gate_key = "invalid_tool_json:%s" % (call.get("name") or "unknown")
                attempts = review_attempts.get(gate_key, 0) + 1
                review_attempts[gate_key] = attempts
                argument_text = str(call.get("arguments") or "")
                output_truncated = bool(
                    call.get("name") == "research_plan"
                    and completion.completion_tokens is not None
                    and completion.completion_tokens >= MAX_OUTPUT_TOKENS
                )
                events.append(
                    _event(
                        "tool_arguments_invalid",
                        rule="invalid_tool_json",
                        tool=call.get("name") or "unknown",
                        detail=detail,
                        argument_chars=len(argument_text),
                        completion_tokens=completion.completion_tokens,
                        output_truncated=output_truncated,
                    )
                )
                if attempts >= harness.max_interventions(tool=call.get("name")):
                    answer = (
                        "Stopped after %d invalid %s tool calls with no progress: %s. "
                        "Start a new turn with a simpler request or revise the plan explicitly."
                        % (
                            attempts,
                            call.get("name") or "unknown",
                            detail,
                        )
                    )
                    events.append(
                        _event("harness_stop", rule="no_progress", reason=answer)
                    )
                    break
                # Crucially, do not append the malformed assistant tool call. DashScope
                # validates historical function.arguments and would reject every retry.
                if completion.content and completion.content.strip():
                    messages.append({"role": "assistant", "content": completion.content})
                if call.get("name") == "research_plan":
                    has_recovery_state = bool(
                        session.get("research") or session.get("research_draft")
                    )
                    if output_truncated:
                        retry_content = (
                            "The previous research_plan arguments reached the output limit and "
                            "were truncated. "
                        )
                    else:
                        retry_content = (
                            "The previous research_plan arguments were incomplete. Keep the next "
                            "tool call compact. "
                        )
                    if has_recovery_state:
                        retry_content += (
                            "Use action=revise_plan with only the affected fields inside changes; "
                            "preserve existing runs, charts, evidence, and physical values. "
                        )
                    else:
                        retry_content += (
                            "Use a concise action=propose with short strings and no repeated "
                            "explanatory prose inside the JSON. "
                        )
                    retry_content += (
                        "Arguments must be one strict JSON object with double-quoted keys and "
                        "strings, no Markdown fence, comments, trailing comma, or prose. "
                        "Parser detail: " + detail
                    )
                else:
                    retry_content = (
                        "Your %s function arguments were not a valid JSON object (%s). "
                        "Generate the tool call again with strict JSON: double-quoted keys "
                        "and strings, no Markdown fence, comments, trailing comma, or prose."
                        % (call.get("name") or "tool", detail)
                    )
                messages.append({"role": "user", "content": retry_content})
                yield answer, events, state
                continue
            # Prose the model wrote before reaching for a tool is a finished block: the next
            # one goes underneath it rather than over it.
            if completion.content and completion.content.strip():
                segments.append(completion.content)
                answer = transcript(segments)
            messages.append(
                {
                    "role": "assistant",
                    "content": completion.content or "",
                    "tool_calls": [
                        {
                            "id": call["id"],
                            "type": "function",
                            "function": {"name": call["name"], "arguments": canonical},
                        }
                        for call, _arguments, canonical, _repair_note in parsed_calls
                    ],
                }
            )
            for call, arguments, _canonical, repair_note in parsed_calls:
                name = call["name"]
                if name == "research_plan":
                    plan_tool_called = True
                success_signature = "%s:%s" % (
                    name,
                    json.dumps(arguments, sort_keys=True, ensure_ascii=False),
                )
                if repair_note:
                    events.append(
                        _event(
                            "tool_arguments_repaired",
                            rule="normalized_tool_json",
                            tool=name,
                            detail=repair_note,
                        )
                    )
                state["phase"] = "running_tool"
                events.append(_event("tool_start", name=name, arguments=arguments))
                yield answer, events, state
                events.pop()

                # Research may be selected by the agent-side preflight for an unambiguous
                # reproduction question, or by the model's first explicit research_plan call
                # for an otherwise ordinary question.
                if name == "research_plan" and not session.get("research_required"):
                    session["research_required"] = True
                    events.append(
                        _event(
                            "research_mode_selected",
                            rule="agent_selected_research",
                            detail=(
                                "The agent selected the reviewed research workflow by calling "
                                "research_plan."
                            ),
                        )
                    )

                started_tool = time.perf_counter()
                # The gate sits here, between deciding to run a model and running it. The
                # model has no way past it, because there is nothing it can put in a tool
                # call that reaches this branch.
                declined = False
                if (
                    name == "run_model"
                    and approval.required(session)
                    and not session.get("research_required")
                ):
                    approval.request(session, name, arguments)
                    state["phase"] = "needs_approval"
                    events.append(
                        _event("approval_wait", rule="human_approval", name=name, arguments=arguments)
                    )
                    yield answer, events, state
                    verdict = approval.wait(session)
                    session.pop("approval_resuming", None)
                    events.pop()
                    state["phase"] = "running_tool"
                    if verdict["decision"] == "reject":
                        declined = True
                    elif verdict["decision"] == "edit" and verdict["arguments"]:
                        arguments = verdict["arguments"]
                    events.append(
                        _event(
                            "approval",
                            rule="human_approval",
                            decision=verdict["decision"],
                            name=name,
                            arguments=arguments,
                        )
                    )
                    yield answer, events, state
                result = (
                    approval.declined_result(name, arguments)
                    if declined
                    else tools.call(
                        name,
                        arguments,
                        owner=session["id"],
                        switches_in=state["switches"],
                        session=session,
                    )
                )
                session_state.bump(state, "tool_calls")
                _record_tool_result(name, result, state, events)

                # Unlimited total budgets must not mean unlimited identical work. A model
                # occasionally redraws the same handles with the generic plot tool forever,
                # or replays another successful call without changing research state. Stop
                # that exact signature after three successes; different arguments and any
                # failed/corrective call remain available without a hard global cap.
                if result["status"] == "success":
                    if repeated_success["signature"] == success_signature:
                        repeated_success["count"] += 1
                    else:
                        repeated_success = {"signature": success_signature, "count": 1}
                    if repeated_success["count"] >= harness.MAX_INTERVENTIONS:
                        answer = (
                            "Stopped after %d identical successful %s calls with no state "
                            "progress. Reuse the existing result or call the required planned "
                            "workflow tool instead of repeating it."
                            % (repeated_success["count"], name)
                        )
                        events.append(
                            _event(
                                "harness_stop",
                                rule="duplicate_success_no_progress",
                                tool=name,
                                reason=answer,
                            )
                        )
                        state["phase"] = "done"
                        yield answer, events, state
                        return
                else:
                    repeated_success = {"signature": None, "count": 0}

                # Successful execution is state progress. Do not let an intervention count
                # from an earlier stage leak into a later QA repair and cause a premature
                # three-attempt stop.
                if name == "run_planned_model" and result["status"] == "success":
                    review_attempts.pop("research_gate:formal_model_required", None)
                if name == "plot_planned_chart" and result["status"] == "success":
                    review_attempts.pop("research_gate:figure_required", None)

                human_wait = (
                    name == "research_plan"
                    and result["status"] == "needs_input"
                    and bool(session.get("research"))
                )
                if result["status"] == "success" or human_wait:
                    tool_failure_streak = {"name": None, "count": 0, "detail": ""}
                else:
                    failure_data = result.get("data") or {}
                    failure_code = failure_data.get("error_code")
                    # A broad error code is not a complete no-progress signature. If the
                    # planner removes invalid relationships between retries, its structured
                    # problem list shrinks and it is making progress rather than looping.
                    structured_problems = failure_data.get("problems") or []
                    failure_detail = (
                        json.dumps(sorted(map(str, structured_problems)), ensure_ascii=False)
                        if structured_problems
                        else (result.get("error") or result["summary"])
                    )
                    failure_signature = "%s:%s:%s" % (
                        name,
                        failure_code or "unclassified",
                        failure_detail,
                    )
                    if tool_failure_streak.get("signature") == failure_signature:
                        tool_failure_streak["count"] += 1
                    else:
                        tool_failure_streak = {
                            "name": name,
                            "signature": failure_signature,
                            "count": 1,
                            "detail": "",
                        }
                    tool_failure_streak["detail"] = result.get("error") or result["summary"]
                    if name == "research_plan":
                        last_plan_error = result["summary"]
                        last_plan_problems = list(failure_data.get("problems") or [])
                        if not session.get("research"):
                            # Resource gates are actionable workflow repairs. Force the
                            # missing read operation instead of asking the model to submit
                            # the same plan again; otherwise a valid plan can loop forever
                            # on messages such as ``Read every selected model instruction``.
                            forced_tool_name = {
                                "reference_read_required": "read_literature",
                                "research_guideline_read_required": "read_research_guideline",
                                "model_instruction_read_required": "read_model_instruction",
                                "capability_review_required": "research_capability_check",
                                "capability_resources_required": "research_capability_check",
                            }.get(failure_code, "research_plan")

                if result["status"] == "needs_input" and (
                    name == "research_plan"
                    or (name == "run_model" and result.get("error") == "research workflow approval required")
                ):
                    events.append(
                        _event(
                            "research_wait",
                            phase=((result.get("data") or {}).get("phase") or "review"),
                            detail=result["summary"],
                        )
                    )
                elif result["status"] == "needs_input":
                    session_state.bump(state, "interventions")
                    events.append(
                        _event(
                            "harness_block",
                            rule="physical_domain",
                            tool=name,
                            detail=result["error"],
                            problems=(result.get("data") or {}).get("problems") or [],
                            given=(result.get("data") or {}).get("rejected_parameters")
                            or (result.get("data") or {}).get("rejected_filters")
                            or {},
                            intervention=state["interventions"],
                        )
                    )
                else:
                    events.append(
                        _event(
                            "tool_call",
                            name=name,
                            arguments=arguments,
                            status=result["status"],
                            summary=result["summary"],
                            qc=(result.get("qc") or {}).get("passed"),
                            data=result.get("data") or {},
                            elapsed_s=round(time.perf_counter() - started_tool, 3),
                        )
                    )
                if (
                    name == "research_capability_check"
                    and result["status"] == "needs_input"
                    and (
                        (result.get("data") or {}).get("error_code") == "capability_review_required"
                        or arguments.get("action") == "reject"
                    )
                ):
                    answer = result["summary"]
                    events.append(
                        _event(
                            "research_wait",
                            phase="capability_review",
                            detail="Capability review requires the user's partial-scope decision.",
                        )
                    )
                    state["phase"] = "done"
                    yield answer, events, state
                    return
                yield answer, events, state

                # A valid revision already has a complete, validated status message from
                # the backend. Do not spend another model call composing a redundant
                # "plan is back in review" response; the UI can show the structured
                # revision summary and the new plan immediately.
                revision_summary = (result.get("data") or {}).get("revision_summary")
                if (
                    name == "research_plan"
                    and arguments.get("action") == "revise_plan"
                    and result["status"] == "needs_input"
                    and revision_summary
                    and ((session.get("research") or {}).get("phase") == "plan_review")
                ):
                    answer = research.revision_summary_text(revision_summary)
                    events.append(
                        _event(
                            "research_revision",
                            phase="plan_review",
                            detail=answer,
                            revision_summary=revision_summary,
                        )
                    )
                    state["phase"] = "done"
                    yield answer, events, state
                    return

                if (
                    name == "run_planned_model"
                    and result["status"] == "terminal_error"
                    and (result.get("data") or {}).get("planned_run_id")
                ):
                    gaps = research.execution_gaps(session)
                    failed = gaps.get("failed_runs") or []
                    if failed:
                        revision = research.revise_after_run_failures(session, failed)
                        answer = (
                            "%s The failed run was not repeated. Successful outputs were retained, "
                            "formal figures from the old plan were withdrawn, and no completion "
                            "claim was published."
                            % revision["summary"]
                        )
                        events.append(
                            _event(
                                "research_revision",
                                rule="model_failure_recovery",
                                phase="plan_review",
                                detail=revision["summary"],
                                failed_run_ids=gaps.get("failed_run_ids") or [],
                            )
                        )
                        state["phase"] = "done"
                        yield answer, events, state
                        return

                if tool_failure_streak["count"] >= harness.max_interventions(tool=name):
                    stop_detail = tool_failure_streak["detail"]
                    if name == "research_plan":
                        structured_stop_problems = [
                            {
                                key: item.get(key)
                                for key in (
                                    "field", "source", "actual", "expected",
                                    "allowed_values", "repair", "blocking",
                                )
                                if key in item
                            }
                            for item in (failure_data.get("problems") or [])
                            if isinstance(item, dict)
                        ]
                        if structured_stop_problems:
                            stop_detail += " Structured repair gaps: %s" % json.dumps(
                                structured_stop_problems,
                                ensure_ascii=False,
                            )
                    answer = (
                        "Stopped after %d consecutive failed %s calls with no state progress. "
                        "Last error: %s"
                        % (
                            tool_failure_streak["count"],
                            name,
                            stop_detail,
                        )
                    )
                    events.append(
                        _event(
                            "harness_stop",
                            rule="no_progress",
                            tool=name,
                            reason=answer,
                        )
                    )
                    state["phase"] = "done"
                    yield answer, events, state
                    return

                payload = {k: v for k, v in result.items() if k not in ("qc", "ui")}
                tool_content = json.dumps(payload, ensure_ascii=False)
                # A figure inspection carries one bounded image part for a configured
                # multimodal endpoint. Keep the base64 out of the tool transcript and send
                # the image as a user content block, which is the OpenAI-compatible format
                # accepted by vision models. The textual tool result remains auditable.
                image_data_url = (result.get("data") or {}).get("image_data_url")
                if image_data_url:
                    text_payload = json.loads(tool_content)
                    text_data = dict(text_payload.get("data") or {})
                    text_data.pop("image_data_url", None)
                    text_payload["data"] = text_data
                    tool_content = json.dumps(text_payload, ensure_ascii=False)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": tool_content,
                    }
                )
                if image_data_url:
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Inspect the attached source-paper figure itself. Read the "
                                        "axes, units, legend, panels, annotations, and visible "
                                        "qualitative trends. Use the image as evidence; do not "
                                        "digitize curve values automatically."
                                    ),
                                },
                                {"type": "image_url", "image_url": {"url": image_data_url}},
                            ],
                        }
                    )
                if (
                    name == "research_plan"
                    and result["status"] == "terminal_error"
                    and (result.get("data") or {}).get("error_code") in (
                        "reproduction_evidence_incomplete",
                        "research_plan_validation",
                        "paper_condition_conflict",
                        "chart_axis_mismatch",
                    )
                ):
                    problems = (result.get("data") or {}).get("problems") or []
                    blocking_problems = [
                        item for item in problems
                        if isinstance(item, dict) and item.get("blocking", True)
                    ]
                    mapping_only = bool(blocking_problems) and all(
                        str(item.get("field", "")).startswith("parameter_mapping")
                        for item in blocking_problems
                    )
                    failure_code = (result.get("data") or {}).get("error_code")
                    if failure_code == "chart_axis_mismatch":
                        recovery_instruction = (
                            "This is a chart-axis repair. Preserve all evidence, reproduction "
                            "targets, outputs, physical parameters, and unrelated runs. Submit "
                            "action=revise_plan with changes containing only the runs that produce "
                            "the affected charts and those charts if necessary. Every compared run "
                            "must use the exact same numeric sweep_parameter as chart.x and include "
                            "sweep_start, sweep_stop, and sweep_points. If the source figure has "
                            "an axis sweep, derive that axis from the inspected figure. Do not "
                            "resubmit the complete plan or change an unrelated experiment."
                        )
                    elif mapping_only:
                        recovery_instruction = (
                            "These are mapping-only errors. Preserve every existing run, chart, "
                            "evidence reference, physical parameter, sweep range, output, and "
                            "target. Repair only the listed mapping fields. For a model_input "
                            "problem, use one exact value from allowed_values or the input names "
                            "returned by list_models; do not submit an alias or the same invalid "
                            "mapping object again. Add model when the error requests model-scoped "
                            "coverage."
                        )
                    else:
                        recovery_instruction = (
                            "Preserve all existing physical runs, the theory/microstructure choices, "
                            "sweep ranges, radii, frequencies, and outputs; this is a metadata-only "
                            "repair. Do not submit the same invalid object again. Fill evidence_refs, "
                            "deterministic target coverage, and parameter mappings, marking backend "
                            "defaults or model assumptions explicitly. If a source figure asset is "
                            "unavailable, mark the target partial with an availability reason."
                        )
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Repair the submitted reproduction plan using the structured "
                                "validation problems below. %s "
                                "Paper conditions are provenance/context, not model-validity "
                                "constraints; only registered model declarations and opened model "
                                "instructions determine legal model inputs. Problems: %s"
                                % (recovery_instruction, json.dumps(problems, ensure_ascii=False))
                            ),
                        }
                    )
                messages[0] = {"role": "system", "content": prompt.build(state)}
            continue

        answer = transcript(segments, completion.content or "")

        # If this turn has explicitly entered research mode but the model tries to answer
        # an executable question without proposing a plan, return that attempt to the model
        # and require a structured research_plan call. Ordinary Q&A never reaches this gate.
        if session.get("research_required") and not session.get("research"):
            gate_key = "research_gate:plan_required"
            attempts = review_attempts.get(gate_key, 0) + 1
            review_attempts[gate_key] = attempts
            if attempts >= harness.max_interventions(rule=gate_key):
                detail = last_plan_error or "the model did not submit a valid research_plan proposal"
                if last_plan_problems:
                    detail += " Structured gaps: %s" % json.dumps(last_plan_problems, ensure_ascii=False)
                answer = (
                    "Research planning stopped after %d no-progress attempts. Last validation "
                    "error: %s No model run or scientific result was produced. Revise the "
                    "question/plan in a new message."
                    % (attempts, detail)
                )
                events.append(
                    _event("harness_stop", rule="plan_no_progress", reason=answer)
                )
                break
            forced_tool_name = "research_plan"
            events.append(
                _event(
                    "research_block",
                    rule="plan_required",
                    detail="No LLM-authored research proposal has been submitted.",
                    intervention=attempts,
                )
            )
            messages.append({"role": "assistant", "content": completion.content or ""})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your next response must be a research_plan function call, not prose. "
                        "Analyse this specific research question from the evidence already read, "
                        "then call research_plan "
                        "with action=propose and a question-specific objective, hypothesis, "
                        "executable steps, parameters, chart options, assumptions, limitations and "
                        "success criteria."
                    ),
                }
            )
            yield transcript(segments), events, state
            continue

        # A research question may produce a fluent literature-based paragraph before the
        # reviewed protocol is complete. Do not present that paragraph as the final result:
        # it can be mistaken for a formal model reproduction even though no approved run has
        # happened yet. The next user turn advances the plan, preview, chart and execution
        # gates; only the approved phase may publish a scientific result.
        project = (session.get("research") or {})
        if session.get("research_required") and project and not research.allow_model(session):
            phase = project.get("phase", "plan_review")
            next_step = {
                "plan_review": "Click Approve plan, or describe the changes you want in Conversation.",
                "plan_approved": "Click Generate preview to inspect demonstration data and chart layouts.",
                "pseudo_preview": "Click one of the named chart options inside Research review; confirming the plan again does not select a chart.",
                "chart_selected": "Click Approve execution to authorize the registered physical-model run.",
            }.get(phase, "Use the active control in Research review to continue.")
            # The gate exists so a fluent literature paragraph is never mistaken for a
            # reproduced result. But it also caught the turn where the user had just
            # described the changes they wanted: the agent answered in prose, the gate
            # replaced it with "describe the changes you want in Conversation", and the
            # revision was lost. So a review phase gets one forced attempt at
            # research_plan first, and only a turn that still will not call it is paused.
            if phase in ("plan_review", "plan_approved") and not plan_tool_called and not revision_forced:
                revision_forced = True
                forced_tool_name = "research_plan"
                events.append(
                    _event(
                        "research_block",
                        rule="revision_required",
                        detail=(
                            "The turn reached the review gate without calling research_plan. "
                            "Submit the requested change as revise_plan, or say why it cannot "
                            "be made."
                        ),
                    )
                )
                messages.append({"role": "assistant", "content": completion.content or ""})
                messages.append({
                    "role": "user",
                    "content": (
                        "Apply that as a revision: call research_plan with "
                        "action=revise_plan and only the fields that change. If nothing "
                        "should change, say so plainly instead."
                    ),
                })
                state["phase"] = "calling_model"
                yield transcript(segments), events, state
                continue
            answer = (
                "Research is paused at the human-review stage (%s). No formal physical result "
                "has been computed yet. %s"
                % (phase, next_step)
            )
            events.append(_event("research_wait", phase=phase))
            break

        project = session.get("research") or {}
        if session.get("research_required") and research.allow_model(session):
            gaps = research.execution_gaps(session)
            if gaps["missing_runs"]:
                if gaps.get("failed_runs"):
                    revision = research.revise_after_run_failures(
                        session, gaps["failed_runs"]
                    )
                    answer = (
                        "%s Successful outputs were retained, but formal figures from the old "
                        "plan were withdrawn. Review and approve the recovery plan before any rerun; "
                        "no completion claim has been published."
                        % revision["summary"]
                    )
                    events.append(
                        _event(
                            "research_revision",
                            rule="model_failure_recovery",
                            phase="plan_review",
                            detail=revision["summary"],
                            failed_run_ids=gaps.get("failed_run_ids") or [],
                        )
                    )
                    break
                gate_key = "research_gate:formal_model_required"
                attempts = review_attempts.get(gate_key, 0) + 1
                review_attempts[gate_key] = attempts
                if attempts >= harness.MAX_INTERVENTIONS:
                    answer = (
                        "Research execution stopped after %d attempts with no progress on planned "
                        "run IDs: %s. No completion claim was published."
                        % (attempts, ", ".join(gaps["missing_run_ids"]))
                    )
                    events.append(
                        _event("harness_stop", rule="model_run_no_progress", reason=answer)
                    )
                    break
                events.append(
                    _event(
                        "research_block",
                        rule="formal_model_required",
                        detail="Approved research is missing planned model runs: %s."
                        % ", ".join(gaps["missing_runs"]),
                        intervention=attempts,
                    )
                )
                messages.append(
                    {"role": "assistant", "content": completion.content or ""}
                )
                messages.append(
                    {
                        "role": "user",
                        "content": "The approved protocol is still missing planned run IDs: %s. Call run_planned_model once for each exact run_id. Do not reconstruct or modify their parameters."
                        % ", ".join(gaps["missing_run_ids"]),
                    }
                )
                forced_tool_name = "run_planned_model"
                yield transcript(segments), events, state
                continue
            if gaps["figure_problem"]:
                if gaps.get("failed_figure_reviews"):
                    failed = gaps["failed_figure_reviews"][0]
                    chart_id = failed["requirement"]["chart"].get("id")
                    revision = research.revise_after_figure_quality(
                        session, chart_id, failed["issues"]
                    )
                    if revision["status"] == "success":
                        next_action = (revision.get("data") or {}).get("next")
                        if next_action == "continue_with_qualified_figure":
                            events.append(
                                _event(
                                    "research_revision",
                                    rule="figure_quality_scientific_anomaly",
                                    phase="approved",
                                    detail=revision["summary"],
                                    anomaly=(revision.get("data") or {}).get("scientific_anomaly"),
                                )
                            )
                            messages.append(
                                {"role": "assistant", "content": completion.content or ""}
                            )
                            messages.append(
                                {
                                    "role": "user",
                                    "content": (
                                        "Maximum safe sampling refinement confirmed a persistent "
                                        "Figure discontinuity. It is retained as a qualified "
                                        "scientific diagnostic. Continue to research_plan(action='complete') "
                                        "and report it explicitly as a possible numerical or model-validity "
                                        "boundary, not a verified physical transition. Do not regenerate "
                                        "the plan or rerun the same model configuration."
                                    ),
                                }
                            )
                            yield transcript(segments), events, state
                            continue
                        rerun_ids = (revision.get("data") or {}).get("affected_run_ids") or []
                        events.append(
                            _event(
                                "research_revision",
                                rule="figure_quality_auto_repair",
                                phase="approved",
                                detail=revision["summary"],
                                affected_run_ids=rerun_ids,
                            )
                        )
                        messages.append(
                            {"role": "assistant", "content": completion.content or ""}
                        )
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "Figure QA safely increased sampling without changing the "
                                    "approved scientific question or controls. Continue the same "
                                    "execution now. Call run_planned_model once for each exact "
                                    "affected run_id: %s. Then regenerate every selected chart and "
                                    "call plot_planned_chart(action='review') for each. Do not call "
                                    "research_plan and do not publish a conclusion until QA passes."
                                    % ", ".join(rerun_ids)
                                ),
                            }
                        )
                        forced_tool_name = "run_planned_model"
                        yield transcript(segments), events, state
                        continue
                    if revision["status"] == "needs_input":
                        answer = (
                            "%s The failed formal figures were withdrawn. Review the revised "
                            "sampling and axes, then approve the new plan; no scientific conclusion "
                            "has been published yet."
                            % revision["summary"]
                        )
                        events.append(
                            _event(
                                "research_revision",
                                rule="figure_quality_repair",
                                phase="plan_review",
                                detail=revision["summary"],
                            )
                        )
                    else:
                        answer = (
                            "%s No new research plan was generated. Describe a deliberate sampling, "
                            "model, or axis revision in Conversation before resuming."
                            % revision["summary"]
                        )
                        events.append(
                            _event(
                                "harness_stop",
                                rule="figure_quality_unresolved",
                                reason=answer,
                                chart_id=chart_id,
                                issues=failed["issues"],
                            )
                        )
                    break
                gate_key = "research_gate:figure_required"
                attempts = review_attempts.get(gate_key, 0)
                if attempts >= harness.MAX_INTERVENTIONS:
                    detail = (
                        "%s Automatic correction stopped after %d attempts to prevent a loop."
                        % (gaps["figure_problem"], harness.MAX_INTERVENTIONS)
                    )
                    events.append(_event("harness_stop", rule="figure_required", reason=detail))
                    answer = (
                        "Research execution paused because the selected result figure is incomplete. "
                        "%s No scientific completion claim has been published." % detail
                    )
                    break
                review_attempts[gate_key] = attempts + 1
                session_state.bump(state, "interventions")
                events.append(
                    _event(
                        "research_block",
                        rule="figure_required",
                        detail=gaps["figure_problem"],
                        intervention=review_attempts[gate_key],
                    )
                )
                messages.append(
                    {"role": "assistant", "content": completion.content or ""}
                )
                if gaps.get("unreviewed_chart_ids"):
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "The formal plot exists but has not passed post-render quality "
                                "review. Call plot_planned_chart(chart_id=%r, action='review') now. Inspect its "
                                "point-count, finite-value, trend, label, legend and redraw report; "
                                "only write the interpretation after every selected Figure passes."
                                % gaps["unreviewed_chart_ids"][0]
                            ),
                        }
                    )
                    yield transcript(segments), events, state
                    continue
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "The approved figure package is incomplete. Call "
                            "plot_planned_chart(chart_id=%r). It deterministically uses all approved "
                            "series for this chart: %s. Then check whether another selected chart "
                            "is still missing before writing the final report."
                            % (
                                gaps["selected_chart"].get("id"),
                                json.dumps(gaps["expected_figure_series"], ensure_ascii=False),
                            )
                        ),
                    }
                )
                yield transcript(segments), events, state
                continue

        report_warning = research.report_warnings(session, answer) if session.get("research_required") else ""
        if report_warning:
            session.setdefault("report_warnings", [])
            if report_warning not in session["report_warnings"]:
                session["report_warnings"].append(report_warning)
            events.append(
                _event(
                    "harness_warning",
                    rule="report_completeness",
                    detail=report_warning,
                )
            )
        # Report completeness is advisory. Evidence, citation, abstract-depth and budget
        # checks remain blocking and are handled by the strict final harness below.
        check, correction = harness.review_final(answer, state)
        if correction and check.get("rule") == "citation_integrity":
            correction = _allowed_marker_correction(state, check.get("unresolved") or [])
        attempts = review_attempts.get(check["rule"], 0)
        if correction and attempts < harness.MAX_INTERVENTIONS:
            review_attempts[check["rule"]] = attempts + 1
            session_state.bump(state, "interventions")
            events.append(
                _event(
                    "harness_block",
                    rule=check["rule"],
                    detail=check.get("reason") or "unresolved markers",
                    unresolved=check.get("unresolved") or [],
                    intervention=review_attempts[check["rule"]],
                )
            )
            messages.append({"role": "assistant", "content": completion.content or ""})
            messages.append({"role": "user", "content": correction})
            # A final report is one replaceable document. Tool-round narration used to
            # survive here, so an invalid marker emitted before a tool call was prepended
            # again after every rewrite and could never be removed by the model.
            segments = []
            answer = ""
            yield answer, events, state
            continue

        if correction:
            answer = research.safe_report(session)
            safe_check, safe_correction = harness.review_final(answer, state)
            if safe_correction:
                answer = (
                    "The generated scientific narrative could not pass evidence validation. "
                    "No interpretation or conclusion is published from this run."
                )
            events.append(
                _event(
                    "harness_fallback",
                    rule=check["rule"],
                    detail="Repeated drafts failed validation; an evidence-only safe report replaced them.",
                )
            )
        else:
            if session.get("research_required") and research.allow_model(session):
                completed = research.complete(session)
                if completed["status"] == "success":
                    events.append(
                        _event(
                            "research_complete",
                            detail="A registered model run, figure and validated report are complete.",
                        )
                    )
            events.append(
                _event("harness_pass", rule="citation_integrity", markers=check.get("markers", []))
            )
        break

    state["phase"] = "done"
    yield answer, events, state


def run(question, history=None, model=None, session=None, switches=None):
    """Blocking form of stream. Returns (answer, events, state)."""
    last = ("", [], new_state(model, session))
    for step in stream(question, history, model, session, switches):
        last = step
    return last
