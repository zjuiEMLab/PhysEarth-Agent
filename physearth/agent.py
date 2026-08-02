import json
import time

from openai import OpenAI

from physearth import config, harness, prompt, tools

MAX_MODEL_CALLS = 12
MAX_TOOL_CALLS = 10
EMPTY_RESPONSE_RETRIES = 3
RETRY_BACKOFF_S = 1.5


def new_state():
    return {
        "model_calls": 0,
        "tool_calls": 0,
        "max_model_calls": MAX_MODEL_CALLS,
        "max_tool_calls": MAX_TOOL_CALLS,
        "sections_read": set(),
        "model_runs": 0,
        "models_run": set(),
        "qc_failures": 0,
        "rejected_calls": 0,
        "interventions": 0,
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


def run(question, history=None):
    """Run one turn. Returns (answer, events, state)."""
    state = new_state()
    events = []
    messages = [{"role": "system", "content": prompt.build(state)}]
    for role, content in history or []:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})

    client = _client()
    model = config.get("MODELSCOPE_MODEL")
    answer = ""

    while True:
        budget = harness.check_budget(state)
        if not budget["passed"]:
            events.append(_event("harness_stop", rule="budget", reason=budget["reason"]))
            answer = answer or "Stopped: %s." % budget["reason"]
            break

        started = time.perf_counter()
        response = None
        for attempt in range(1, EMPTY_RESPONSE_RETRIES + 1):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools.SPECS,
                tool_choice="auto",
                parallel_tool_calls=False,
                max_tokens=2048,
            )
            if response.choices:
                break
            events.append(_event("empty_response", attempt=attempt))
            response = None
            time.sleep(RETRY_BACKOFF_S * attempt)
        if response is None:
            events.append(_event("harness_stop", rule="upstream", reason="empty response from the inference endpoint"))
            answer = answer or (
                "The inference endpoint returned an empty response %d times in a row. "
                "This is an upstream fault, not a modelling result. Please retry."
                % EMPTY_RESPONSE_RETRIES
            )
            break
        state["model_calls"] += 1
        usage = getattr(response, "usage", None)
        if usage:
            state["prompt_tokens"] += usage.prompt_tokens or 0
            state["completion_tokens"] += usage.completion_tokens or 0
        events.append(
            _event(
                "model_call",
                index=state["model_calls"],
                elapsed_s=round(time.perf_counter() - started, 2),
                prompt_tokens=getattr(usage, "prompt_tokens", None),
                completion_tokens=getattr(usage, "completion_tokens", None),
            )
        )

        message = response.choices[0].message
        calls = message.tool_calls or []

        if calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": c.id,
                            "type": "function",
                            "function": {"name": c.function.name, "arguments": c.function.arguments},
                        }
                        for c in calls
                    ],
                }
            )
            for call in calls:
                name = call.function.name
                try:
                    arguments = json.loads(call.function.arguments or "{}")
                except ValueError:
                    arguments = {}
                started = time.perf_counter()
                result = tools.call(name, arguments)
                state["tool_calls"] += 1
                for key in result.get("citations", []):
                    state["sections_read"].add(key)
                if name == "run_model":
                    if result["status"] == "success":
                        state["model_runs"] += 1
                        state["models_run"].add(
                            "%s@%s" % (result["data"]["model"], result["data"]["version"])
                        )
                        if result.get("qc") and not result["qc"]["passed"]:
                            state["qc_failures"] += 1
                    elif result["status"] == "needs_input":
                        state["rejected_calls"] += 1
                kind = "harness_block" if result["status"] == "needs_input" else "tool_call"
                if kind == "harness_block":
                    events.append(
                        _event(
                            "harness_block",
                            rule="physical_domain",
                            detail=result["error"],
                            intervention=None,
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
                            elapsed_s=round(time.perf_counter() - started, 3),
                        )
                    )
                payload = {k: v for k, v in result.items() if k != "qc"}
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(payload, ensure_ascii=False),
                    }
                )
            messages[0] = {"role": "system", "content": prompt.build(state)}
            continue

        answer = message.content or ""
        check, correction = harness.review_final(answer, state)
        if correction and state["interventions"] < harness.MAX_INTERVENTIONS:
            state["interventions"] += 1
            events.append(
                _event(
                    "harness_block",
                    rule=check["rule"],
                    detail=check.get("unresolved") or check.get("reason"),
                    intervention=state["interventions"],
                )
            )
            messages.append({"role": "assistant", "content": answer})
            messages.append({"role": "user", "content": correction})
            continue

        if correction:
            events.append(_event("harness_giveup", rule=check["rule"], detail=check.get("reason")))
        else:
            events.append(
                _event("harness_pass", rule="citation_integrity", markers=check.get("markers", []))
            )
        break

    return answer, events, state


def render_trace(events, state):
    lines = ["| # | event | detail |", "| ---: | --- | --- |"]
    for index, event in enumerate(events, 1):
        kind = event["kind"]
        if kind == "model_call":
            detail = "%.2fs, prompt %s, completion %s" % (
                event["elapsed_s"],
                event["prompt_tokens"],
                event["completion_tokens"],
            )
        elif kind == "tool_call":
            qc = event.get("qc")
            badge = "" if qc is None else (" [QC ok]" if qc else " [QC FAILED]")
            detail = "%s %s -> %s%s (%.3fs)" % (
                event["name"],
                json.dumps(event["arguments"], ensure_ascii=False),
                event["summary"],
                badge,
                event["elapsed_s"],
            )
        elif kind == "harness_block":
            detail = "BLOCKED by %s: %s" % (event["rule"], event["detail"])
        elif kind == "harness_pass":
            detail = "%s ok, markers: %s" % (
                event["rule"],
                ", ".join(event["markers"]) or "none",
            )
        else:
            detail = json.dumps({k: v for k, v in event.items() if k not in ("kind", "at")}, ensure_ascii=False)
        lines.append("| %d | %s | %s |" % (index, kind, detail))
    lines.append("")
    lines.append(
        "LLM calls %d/%d, tool calls %d/%d, model runs %d, rejected calls %d, QC failures %d, "
        "interventions %d, tokens %d in / %d out."
        % (
            state["model_calls"],
            state["max_model_calls"],
            state["tool_calls"],
            state["max_tool_calls"],
            state["model_runs"],
            state["rejected_calls"],
            state["qc_failures"],
            state["interventions"],
            state["prompt_tokens"],
            state["completion_tokens"],
        )
    )
    lines.append("Sections read: %s" % (", ".join(sorted(state["sections_read"])) or "none"))
    lines.append("Models run: %s" % (", ".join(sorted(state["models_run"])) or "none"))
    return "\n".join(lines)
