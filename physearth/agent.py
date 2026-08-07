import ast
import json
import time

from openai import OpenAI

from physearth import approval, budget, config, harness, prompt, tools, research
from physearth import session as session_state
from physearth import switches as switch_flags

MAX_MODEL_CALLS = session_state.MAX_MODEL_CALLS
MAX_TOOL_CALLS = session_state.MAX_TOOL_CALLS
EMPTY_RESPONSE_RETRIES = 3
RETRY_BACKOFF_S = 1.5
# A rate limit is counted over a window, so a backoff shorter than the window cannot
# clear it. The account limit here is per minute, and three attempts at a few seconds
# each used to report an upstream fault after eighteen seconds of trying, when waiting
# would have worked. These three attempts span just over a minute instead.
RATE_LIMIT_BACKOFF_S = 12.0
RATE_LIMIT_RETRIES = 4
# A three-configuration research_plan is itself a sizeable JSON tool call.  At 2048 the
# provider stopped exactly at the limit and left function.arguments without its closing
# braces, which then poisoned the next OpenAI-compatible request.  This still leaves ample
# room under the conservative request/context ceilings below.
MAX_OUTPUT_TOKENS = 4096
# ModelScope providers differ slightly in their advertised context windows. Keep a
# conservative request budget and compact old tool output before the provider rejects the
# request. This is a character budget because the tokenizer is model-specific; it leaves
# room for the system prompt and the requested completion.
MAX_REQUEST_CHARS = 240000
MAX_KEPT_HISTORY_CHARS = 48000
MAX_KEPT_TOOL_CHARS = 12000
# A turn can produce several stretches of prose, one before each round of tool calls. They
# are separate thoughts and belong in separate blocks, so they travel joined by a character
# that cannot occur in the text itself rather than run together into one paragraph.
SEGMENT_BREAK = ""
CONTEXT_CEILING_TOKENS = session_state.CONTEXT_CEILING_TOKENS

_MODEL_LABELS = {
    "Qwen/Qwen3.5-122B-A10B": "Qwen3.5 122B-A10B",
    "deepseek-ai/DeepSeek-V4-Flash-0731": "DeepSeek V4 Flash",
    "ZhipuAI/GLM-4.7-Flash": "GLM 4.7 Flash",
    "qwen-plus": "Qwen Plus",
    "qwen-turbo": "Qwen Turbo",
    "qwen-max": "Qwen Max",
}


def _model_card(model_id):
    label = _MODEL_LABELS.get(model_id, model_id.replace("/", " · "))
    vendor = "Qwen" if "qwen" in model_id.lower() else model_id.split("/", 1)[0]
    return {"id": model_id, "label": label, "vendor": vendor, "note": "configured in .env"}


CATALOGUE = [_model_card(model_id) for model_id in config.llm_models()]


def default_model():
    wanted = config.llm_model()
    known = [m["id"] for m in CATALOGUE]
    return wanted if wanted in known else (known[0] if known else wanted)


def resolve_model(name, unrestricted=False):
    """Only ever run a model from the catalogue, whatever the client sent.

    The guard exists because the chosen model arrives from the browser, and without it a
    crafted value would make this process call an arbitrary endpoint. `unrestricted` is
    for callers that are not a browser: the evaluation suite drives the agent on models
    outside the switcher on purpose, so that a sweep never competes for the quota of the
    three the interface offers. It is passed by the process that starts the run and is
    reachable from nothing else.
    """
    known = [m["id"] for m in CATALOGUE]
    if unrestricted and name:
        return name
    return name if name in known else default_model()


def new_session(model=None, unrestricted=False):
    session = session_state.new_session(resolve_model(model, unrestricted))
    session["unrestricted"] = bool(unrestricted)
    return session


def new_state(model=None, session=None):
    if session is None:
        return session_state.new_state(model=resolve_model(model))
    return session_state.new_state(session, resolve_model(model or session.get("model")))


def _client():
    token = config.llm_api_key()
    if not token:
        raise RuntimeError("PHYSEARTH_LLM_API_KEY is not set; the agent cannot reach the model.")
    return OpenAI(api_key=token, base_url=config.llm_api_base())


def _event(kind, **fields):
    return dict(kind=kind, at=time.strftime("%H:%M:%S"), **fields)


def _fault(exc):
    """A short label for an upstream failure, carrying the HTTP status when there is one."""
    status = getattr(exc, "status_code", None)
    if status == 429:
        if _dead_for_today(exc) == "quota":
            return "model quota or balance exhausted (HTTP 429)"
        return "rate limited (HTTP 429)"
    if status:
        return "HTTP %s" % status
    return type(exc).__name__


def _upstream_text(exc):
    """Whatever the endpoint actually said, bounded. This is what makes a fault diagnosable."""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        message = body.get("message") or (body.get("error") or {}).get("message")
        if message:
            return str(message)[:400]
    return str(exc)[:400]


def _rate_limited(exc):
    """A limit counted over a window, which waiting clears. Not the same as a spent quota.

    The endpoint expresses this two ways: an SDK RateLimitError, and a plain message about
    requests per minute. Both mean wait, not stop.
    """
    if "RateLimit" in type(exc).__name__:
        return True
    text = _upstream_text(exc).lower()
    return "rpm" in text or "rate limit" in text or "too many requests" in text


def _dead_for_today(exc):
    """Faults that belong to one model and will not clear by retrying.

    Two are known: the free quota is per model and per day, and a model can be withdrawn
    from the endpoint entirely, which it reports as having no provider.
    """
    status = getattr(exc, "status_code", None)
    text = _upstream_text(exc).lower()
    exhausted = (
        "quota" in text
        or "insufficient balance" in text
        or "insufficient credit" in text
        or "balance is insufficient" in text
    )
    if status == 429 and exhausted:
        return "quota"
    if status == 400 and "no provider" in text:
        return "withdrawn"
    return ""


class _Completion:
    """One streamed model response, accumulated as it arrives."""

    def __init__(self):
        self.content = ""
        self.reasoning = 0
        self.calls = {}
        self.prompt_tokens = None
        self.completion_tokens = None

    def feed(self, chunk):
        usage = getattr(chunk, "usage", None)
        if usage:
            self.prompt_tokens = getattr(usage, "prompt_tokens", None) or self.prompt_tokens
            self.completion_tokens = (
                getattr(usage, "completion_tokens", None) or self.completion_tokens
            )
        if not chunk.choices:
            return False
        delta = chunk.choices[0].delta
        if delta is None:
            return False
        grew = False
        if getattr(delta, "reasoning_content", None):
            self.reasoning += len(delta.reasoning_content)
            grew = True
        if getattr(delta, "content", None):
            self.content += delta.content
            grew = True
        for part in getattr(delta, "tool_calls", None) or []:
            slot = self.calls.setdefault(part.index, {"id": "", "name": "", "arguments": ""})
            if part.id:
                slot["id"] = part.id
            fn = getattr(part, "function", None)
            if fn is not None:
                if fn.name:
                    slot["name"] = fn.name
                if fn.arguments:
                    slot["arguments"] += fn.arguments
            grew = True
        return grew

    def tool_calls(self):
        return [self.calls[index] for index in sorted(self.calls)]

    def empty(self):
        return not self.content and not self.calls and not self.reasoning


def _tool_arguments(raw):
    """Return (object, canonical JSON, repair note), or raise ValueError.

    Some OpenAI-compatible endpoints occasionally stream a Python-style mapping or a
    fenced JSON object.  The next request must still contain strict JSON in the assistant
    tool-call history; replaying the provider's malformed string makes DashScope reject
    the entire conversation with InvalidParameter before the model can correct itself.
    """
    text = str(raw or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    candidates = [text]
    if "{" in text and "}" in text:
        candidates.append(text[text.find("{") : text.rfind("}") + 1])
    last_error = "empty arguments"
    for candidate in dict.fromkeys(candidates):
        if not candidate:
            candidate = "{}"
        try:
            value = json.loads(candidate)
            note = ""
        except (TypeError, ValueError) as exc:
            last_error = str(exc)
            try:
                value = ast.literal_eval(candidate)
                note = "provider arguments normalized from Python-style syntax"
            except (SyntaxError, ValueError) as literal_error:
                last_error = str(literal_error)
                continue
        if not isinstance(value, dict):
            last_error = "function arguments must decode to a JSON object"
            continue
        return value, json.dumps(value, ensure_ascii=False, separators=(",", ":")), note
    raise ValueError(last_error)


def transcript(segments, current=""):
    """Everything the agent has said this turn, oldest block first."""
    parts = [s for s in segments if s and s.strip()]
    if current and current.strip():
        parts.append(current)
    return SEGMENT_BREAK.join(parts)


def _messages(question, history, state):
    messages = [{"role": "system", "content": prompt.build(state)}]
    for turn in history or []:
        role = turn.get("role") if isinstance(turn, dict) else turn[0]
        content = turn.get("content") if isinstance(turn, dict) else turn[1]
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            # The break is ours, for laying the answer out. The model gets plain prose.
            messages.append(
                {"role": role, "content": content.replace(SEGMENT_BREAK, "\n\n")}
            )
    messages.append({"role": "user", "content": question})
    return messages


def _short_content(content, limit):
    content = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    if len(content) <= limit:
        return content
    kept = max(0, limit - 120)
    return content[:kept] + "\n...[older context compacted by PhysEarth]..."


def _compact_messages(messages):
    """Keep a long research run below the provider context window.

    The current question and the latest tool round are authoritative. Older turns remain
    useful for conversational continuity, but their full prose and raw tool payloads do not
    need to be sent on every call: the session state already retains citations, handles,
    plans and model outputs, and the agent can re-read a section when needed.
    """
    if not messages:
        return messages
    system = dict(messages[0])
    system["content"] = _short_content(system.get("content", ""), 72000)
    last_user = max(
        (index for index, message in enumerate(messages) if message.get("role") == "user"),
        default=0,
    )
    history = messages[1:last_user]
    current = messages[last_user:]
    kept_history = []
    history_chars = 0
    for message in reversed(history):
        content = _short_content(message.get("content", ""), 9000)
        if history_chars + len(content) > MAX_KEPT_HISTORY_CHARS:
            break
        item = dict(message)
        item["content"] = content
        kept_history.append(item)
        history_chars += len(content)
    kept_history.reverse()

    compacted_current = []
    for message in current:
        item = dict(message)
        if item.get("role") == "tool":
            item["content"] = _short_content(item.get("content", ""), MAX_KEPT_TOOL_CHARS)
        elif isinstance(item.get("content"), str):
            item["content"] = _short_content(item["content"], 18000)
        compacted_current.append(item)

    result = [system] + kept_history + compacted_current
    while sum(len(str(message.get("content", ""))) for message in result) > MAX_REQUEST_CHARS:
        # Drop the oldest complete history item first. Never remove the system prompt or
        # the current user/tool round, since an orphaned tool message is invalid API input.
        if len(kept_history) > 1:
            kept_history.pop(0)
            result = [system] + kept_history + compacted_current
        else:
            break
    return result


def _handle_line(name, data):
    """One line describing a stored result, for the session's `already held` block."""
    if name == "run_model":
        axis = data.get("axis") or {}
        span = (
            "%d points over %s" % (data.get("n_points", 0), axis["name"])
            if axis.get("name")
            else "%d point(s)" % data.get("n_points", 0)
        )
        return "%s@%s, %s, columns %s" % (
            data.get("model"),
            data.get("version"),
            span,
            ", ".join(sorted((data.get("series_summary") or {}))) or "none",
        )
    return "measured %s, %d row(s), columns %s" % (
        data.get("dataset"),
        data.get("n_rows", 0),
        ", ".join(sorted((data.get("summary") or {}))) or "none",
    )


def _allowed_marker_correction(state, unresolved):
    """A strict citation whitelist for a from-scratch report rewrite."""
    allowed = []
    allowed.extend("[%s]" % key for key in sorted(state.get("sections_read") or ()))
    allowed.extend("[model:%s]" % key for key in sorted(state.get("models_run") or ()))
    allowed.extend("[data:%s]" % key for key in sorted(state.get("datasets_read") or ()))
    allowed.extend("[skill:%s]" % key for key in sorted(state.get("skills_read") or ()))
    allowed.extend("[abs:%s]" % key for key in sorted(state.get("abstracts_seen") or ()))
    return (
        "Rewrite the entire report from scratch. The previous draft is discarded. Invalid "
        "markers were: %s. The complete marker whitelist for this conversation is: %s. "
        "Use only markers in that whitelist; it is also valid to make a clearly labelled "
        "interpretation without a marker. Do not invent paper sections, datasets, skills, or "
        "model names, and remove any factual claim that depended only on an invalid marker."
        % (", ".join(unresolved) or "unknown", ", ".join(allowed) or "none")
    )


def _record_tool_result(name, result, state, events):
    for key in result.get("citations", []):
        state["sections_read"].add(key)
    data = result.get("data") or {}
    if name == "read_literature" and result["status"] == "success" and data.get("section_id"):
        if data.get("source") == "skill":
            state["skills_read"].add(data["slug"])
            events.append(
                _event(
                    "protocol",
                    rule="skill_followed",
                    detail="%s is now open, so [skill:%s] resolves in this answer."
                    % (data["slug"], data["slug"]),
                )
            )
    if name == "discover_literature" and result["status"] == "success":
        for item in data.get("candidates") or []:
            state["abstracts_seen"].add(item["doi"])
        events.append(
            _event(
                "literature_tier",
                rule="abstract_level",
                detail="%d candidate(s) recorded at abstract level; none of them is full text."
                % len(data.get("candidates") or []),
            )
        )
    if name == "ingest_paper" and result["status"] == "success" and data.get("fetched_from"):
        events.append(
            _event(
                "literature_tier",
                rule="session_full_text",
                detail="%s arrived from %s as %s, %d section(s), licensed %s."
                % (
                    data["doi"],
                    data["fetched_from"],
                    data["slug"],
                    len(data.get("sections") or []),
                    data.get("license") or "unknown",
                ),
            )
        )
    if name == "list_models" and result["status"] == "success":
        if data.get("version"):
            state["models_run"].add("%s@%s" % (data["name"], data["version"]))
        for row in data.get("models") or []:
            state["models_run"].add("%s@%s" % (row["name"], row["version"]))
    for finding in data.get("external_source_findings") or []:
        session_state.bump(state, "boundary_flags")
        events.append(
            _event(
                "untrusted_content",
                rule="external_source_boundary",
                detail="%s: %s" % (finding["kind"], finding["excerpt"]),
            )
        )
    if name == "read_reference_dataset" and result["status"] == "success":
        if data.get("dataset"):
            state["datasets_read"].add(data["dataset"])
        for row in data.get("datasets") or []:
            state["datasets_read"].add(row["slug"])
    if name == "run_model":
        if result["status"] == "success":
            session_state.bump(state, "model_runs")
            state["models_run"].add("%s@%s" % (data["model"], data["version"]))
            state["session"]["successful_runs"].append(
                {"model": data["model"], "spec": dict(data.get("spec") or {}), "handle": data.get("handle")}
            )
            if result.get("qc") and not result["qc"]["passed"]:
                session_state.bump(state, "qc_failures")
        elif result["status"] == "needs_input":
            session_state.bump(state, "rejected_calls")
    if data.get("handle") and result["status"] == "success":
        session_state.remember_handle(state, data["handle"], _handle_line(name, data))
    if name == "plot" and result["status"] == "success":
        session_state.remember_figure(state, (result.get("ui") or {})["figure"])


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
    state = session_state.new_state(session, session["model"])
    state["switches"] = switch_flags.resolve(switches)
    events = []
    answer = ""
    review_attempts = {}
    segments = []

    allowed, message = budget.acquire()
    if not allowed:
        events.append(_event("harness_stop", rule="global_budget", reason=message))
        state["phase"] = "done"
        yield message, events, state
        return

    messages = _messages(question, history, state)
    client = _client()
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
                    tool_choice="auto",
                    parallel_tool_calls=False,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    stream=True,
                    stream_options={"include_usage": True},
                )
                for chunk in chunks:
                    if candidate.feed(chunk) and candidate.content:
                        yield transcript(segments, candidate.content), events, state
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
                events.append(
                    _event(
                        "tool_arguments_invalid",
                        rule="invalid_tool_json",
                        tool=call.get("name") or "unknown",
                        detail=detail,
                    )
                )
                # Crucially, do not append the malformed assistant tool call. DashScope
                # validates historical function.arguments and would reject every retry.
                if completion.content and completion.content.strip():
                    messages.append({"role": "assistant", "content": completion.content})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your %s function arguments were not a valid JSON object (%s). "
                            "Generate the tool call again with strict JSON: double-quoted keys "
                            "and strings, no Markdown fence, comments, trailing comma, or prose."
                            % (call.get("name") or "tool", detail)
                        ),
                    }
                )
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
                yield answer, events, state

                payload = {k: v for k, v in result.items() if k not in ("qc", "ui")}
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(payload, ensure_ascii=False),
                    }
                )
            messages[0] = {"role": "system", "content": prompt.build(state)}
            continue

        answer = transcript(segments, completion.content or "")

        # The planner is an agent action, not a question classifier in application code.
        # If the model tries to answer an executable question without proposing a plan,
        # return that attempt to the model and require a structured research_plan call.
        if session.get("research_required") and not session.get("research"):
            events.append(
                _event(
                    "research_block",
                    rule="plan_required",
                    detail="No LLM-authored research proposal has been submitted.",
                )
            )
            messages.append({"role": "assistant", "content": completion.content or ""})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Do not answer yet. Analyse this specific research question, inspect the "
                        "relevant literature/model declarations as needed, then call research_plan "
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
                events.append(
                    _event(
                        "research_block",
                        rule="formal_model_required",
                        detail="Approved research is missing planned model runs: %s."
                        % ", ".join(gaps["missing_runs"]),
                    )
                )
                messages.append(
                    {"role": "assistant", "content": completion.content or ""}
                )
                messages.append(
                    {
                        "role": "user",
                        "content": "The approved protocol is still missing these successful planned runs: %s. Execute them with the declared compatible parameters before answering."
                        % ", ".join(gaps["missing_runs"]),
                    }
                )
                yield transcript(segments), events, state
                continue
            if gaps["figure_problem"]:
                events.append(
                    _event(
                        "research_block",
                        rule="figure_required",
                        detail=gaps["figure_problem"],
                    )
                )
                messages.append(
                    {"role": "assistant", "content": completion.content or ""}
                )
                messages.append(
                    {
                        "role": "user",
                        "content": "Call plot using the successful result handle before writing the final answer. The final research result must include a figure.",
                    }
                )
                yield transcript(segments), events, state
                continue

        report_problem = research.report_problem(session, answer) if session.get("research_required") else ""
        if report_problem:
            check = {"rule": "research_scope", "passed": False, "reason": report_problem}
            correction = report_problem + " Re-send the complete corrected report."
        else:
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
