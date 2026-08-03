import json
import time

from openai import OpenAI

from physearth import budget, config, harness, prompt, tools

MAX_MODEL_CALLS = 12
MAX_TOOL_CALLS = 10
EMPTY_RESPONSE_RETRIES = 3
RETRY_BACKOFF_S = 1.5
RATE_LIMIT_FACTOR = 6
MAX_OUTPUT_TOKENS = 2048
CONTEXT_CEILING_TOKENS = 96000

CATALOGUE = [
    {
        "id": "Qwen/Qwen3.5-122B-A10B",
        "label": "Qwen3.5 122B-A10B",
        "vendor": "Qwen",
        "note": "mixture of experts, the default",
    },
    {
        "id": "deepseek-ai/DeepSeek-V4-Flash",
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


def new_state(model=None):
    return {
        "model": model or default_model(),
        "phase": "idle",
        "model_calls": 0,
        "tool_calls": 0,
        "max_model_calls": MAX_MODEL_CALLS,
        "max_tool_calls": MAX_TOOL_CALLS,
        "context_ceiling": CONTEXT_CEILING_TOKENS,
        "sections_read": set(),
        "model_runs": 0,
        "models_run": set(),
        "datasets_read": set(),
        "figures": [],
        "qc_failures": 0,
        "rejected_calls": 0,
        "interventions": 0,
        "boundary_flags": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }


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


def _quota_exhausted(exc):
    """The free quota is per model and per day, so retrying it cannot help."""
    return getattr(exc, "status_code", None) == 429 and "quota" in _upstream_text(exc).lower()


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


def _record_tool_result(name, result, state, events):
    for key in result.get("citations", []):
        state["sections_read"].add(key)
    data = result.get("data") or {}
    if name == "list_models" and result["status"] == "success":
        if data.get("version"):
            state["models_run"].add("%s@%s" % (data["name"], data["version"]))
        for row in data.get("models") or []:
            state["models_run"].add("%s@%s" % (row["name"], row["version"]))
    for finding in data.get("external_source_findings") or []:
        state["boundary_flags"] += 1
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
            state["model_runs"] += 1
            state["models_run"].add("%s@%s" % (data["model"], data["version"]))
            if result.get("qc") and not result["qc"]["passed"]:
                state["qc_failures"] += 1
        elif result["status"] == "needs_input":
            state["rejected_calls"] += 1
    if name == "plot" and result["status"] == "success":
        state["figures"].append((result.get("ui") or {})["figure"])


def stream(question, history=None, model=None):
    """Run one turn, yielding (answer, events, state) every time something happens."""
    state = new_state(resolve_model(model))
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
        session_budget = harness.check_budget(state)
        if not session_budget["passed"]:
            events.append(_event("harness_stop", rule="budget", reason=session_budget["reason"]))
            answer = answer or "Stopped: %s." % session_budget["reason"]
            break

        state["phase"] = "calling_model"
        yield answer, events, state

        completion = None
        last_fault = "no choices"
        last_upstream = ""
        quota_spent = False
        for attempt in range(1, EMPTY_RESPONSE_RETRIES + 1):
            started = time.perf_counter()
            candidate = _Completion()
            try:
                chunks = client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    tools=tools.SPECS,
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
                if _quota_exhausted(exc):
                    quota_spent = True
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
                    rule="quota" if quota_spent else "upstream",
                    reason=last_fault,
                    model=model_id,
                    upstream=last_upstream,
                )
            )
            others = [m["label"] for m in CATALOGUE if m["id"] != model_id]
            answer = answer or (
                "The free daily quota for %s is used up. That quota is per model, so pick "
                "another one in the switcher at the top: %s. Nothing was computed, so nothing "
                "here is a modelling result." % (model_id, " or ".join(others))
                if quota_spent
                else "The inference endpoint refused %d times in a row: %s. This is an upstream "
                "fault, not a modelling result; the run trace has what the endpoint said."
                % (EMPTY_RESPONSE_RETRIES, last_fault)
            )
            break

        state["model_calls"] += 1
        state["prompt_tokens"] += completion.prompt_tokens or 0
        state["completion_tokens"] += completion.completion_tokens or 0
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
                result = tools.call(name, arguments)
                state["tool_calls"] += 1
                _record_tool_result(name, result, state, events)

                if result["status"] == "needs_input":
                    state["interventions"] += 1
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
            state["interventions"] += 1
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


def run(question, history=None, model=None):
    """Blocking form of stream. Returns (answer, events, state)."""
    last = ("", [], new_state(resolve_model(model)))
    for step in stream(question, history, model):
        last = step
    return last
