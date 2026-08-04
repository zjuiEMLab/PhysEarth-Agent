import json
import time

from openai import OpenAI

from physearth import approval, budget, config, harness, prompt, tools
from physearth import session as session_state
from physearth import switches as switch_flags

MAX_MODEL_CALLS = session_state.MAX_MODEL_CALLS
MAX_TOOL_CALLS = session_state.MAX_TOOL_CALLS
EMPTY_RESPONSE_RETRIES = 3
RETRY_BACKOFF_S = 1.5
RATE_LIMIT_FACTOR = 2
MAX_OUTPUT_TOKENS = 2048
CONTEXT_CEILING_TOKENS = session_state.CONTEXT_CEILING_TOKENS

CATALOGUE = [
    {
        "id": "Qwen/Qwen3.5-122B-A10B",
        "label": "Qwen3.5 122B-A10B",
        "vendor": "Qwen",
        "note": "mixture of experts, the default",
    },
    {
        # The endpoint re-dated this identifier. The undated form now answers "has no
        # provider supported", which reads like a withdrawal and is not one.
        "id": "deepseek-ai/DeepSeek-V4-Flash-0731",
        "label": "DeepSeek V4 Flash",
        "vendor": "DeepSeek",
        "note": "fast reasoning model",
    },
    {
        "id": "ZhipuAI/GLM-4.7-Flash",
        "label": "GLM 4.7 Flash",
        "vendor": "ZhipuAI",
        "note": "low latency",
    },
]


def default_model():
    wanted = config.get("MODELSCOPE_MODEL")
    known = [m["id"] for m in CATALOGUE]
    return wanted if wanted in known else (known[0] if known else wanted)


def resolve_model(name):
    """Only ever run a model from the catalogue, whatever the client sent."""
    known = [m["id"] for m in CATALOGUE]
    return name if name in known else default_model()


def new_session(model=None):
    return session_state.new_session(resolve_model(model))


def new_state(model=None, session=None):
    if session is None:
        return session_state.new_state(model=resolve_model(model))
    return session_state.new_state(session, resolve_model(model or session.get("model")))


def _client():
    token = config.get("MODELSCOPE_TOKEN")
    if not token:
        raise RuntimeError("MODELSCOPE_TOKEN is not set; the agent cannot reach the model.")
    return OpenAI(api_key=token, base_url=config.get("MODELSCOPE_API_BASE"))


def _event(kind, **fields):
    return dict(kind=kind, at=time.strftime("%H:%M:%S"), **fields)


def _fault(exc):
    """A short label for an upstream failure, carrying the HTTP status when there is one."""
    status = getattr(exc, "status_code", None)
    if status == 429:
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


def _dead_for_today(exc):
    """Faults that belong to one model and will not clear by retrying.

    Two are known: the free quota is per model and per day, and a model can be withdrawn
    from the endpoint entirely, which it reports as having no provider.
    """
    status = getattr(exc, "status_code", None)
    text = _upstream_text(exc).lower()
    if status == 429 and "quota" in text:
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


def _messages(question, history, state):
    messages = [{"role": "system", "content": prompt.build(state)}]
    for turn in history or []:
        role = turn.get("role") if isinstance(turn, dict) else turn[0]
        content = turn.get("content") if isinstance(turn, dict) else turn[1]
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})
    return messages


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
    session["model"] = resolve_model(model or session.get("model"))
    session["turns"] = session.get("turns", 0) + 1
    state = session_state.new_state(session, session["model"])
    state["switches"] = switch_flags.resolve(switches)
    events = []
    answer = ""

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

        completion = None
        last_fault = "no choices"
        last_upstream = ""
        model_dead = ""
        for attempt in range(1, EMPTY_RESPONSE_RETRIES + 1):
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
                        yield answer + candidate.content, events, state
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
                rate_limited = "RateLimit" in type(exc).__name__
                time.sleep(RETRY_BACKOFF_S * attempt * (RATE_LIMIT_FACTOR if rate_limited else 1))
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
                    "The free daily quota for %s is used up. That quota is per model, so pick "
                    "another one in the switcher at the top: %s. Nothing was computed, so "
                    "nothing here is a modelling result." % (model_id, others)
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
            messages.append(
                {
                    "role": "assistant",
                    "content": completion.content or "",
                    "tool_calls": [
                        {
                            "id": c["id"],
                            "type": "function",
                            "function": {"name": c["name"], "arguments": c["arguments"]},
                        }
                        for c in calls
                    ],
                }
            )
            for call in calls:
                name = call["name"]
                try:
                    arguments = json.loads(call["arguments"] or "{}")
                except ValueError:
                    arguments = {}
                state["phase"] = "running_tool"
                events.append(_event("tool_start", name=name, arguments=arguments))
                yield answer, events, state
                events.pop()

                started_tool = time.perf_counter()
                # The gate sits here, between deciding to run a model and running it. The
                # model has no way past it, because there is nothing it can put in a tool
                # call that reaches this branch.
                declined = False
                if name == "run_model" and approval.required(session):
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

                if result["status"] == "needs_input":
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

        answer = completion.content or ""
        check, correction = harness.review_final(answer, state)
        if correction and state["interventions"] < harness.MAX_INTERVENTIONS:
            session_state.bump(state, "interventions")
            events.append(
                _event(
                    "harness_block",
                    rule=check["rule"],
                    detail=check.get("reason") or "unresolved markers",
                    unresolved=check.get("unresolved") or [],
                    intervention=state["interventions"],
                )
            )
            messages.append({"role": "assistant", "content": answer})
            messages.append({"role": "user", "content": correction})
            answer = ""
            yield answer, events, state
            continue

        if correction:
            events.append(_event("harness_giveup", rule=check["rule"], detail=check.get("reason")))
        else:
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
