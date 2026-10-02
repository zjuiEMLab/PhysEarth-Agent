"""Building the request message list and compacting it under the character budget."""

import json

from physearth import prompt
from physearth.agent.constants import (
    MAX_KEPT_HISTORY_CHARS,
    MAX_KEPT_TOOL_CHARS,
    MAX_REQUEST_CHARS,
    SEGMENT_BREAK,
)


def transcript(segments, current=""):
    """Everything the agent has said this turn, oldest block first."""
    parts = [s for s in segments if s and s.strip()]
    if current and current.strip():
        parts.append(current)
    return SEGMENT_BREAK.join(parts)


def _messages(question, history, state):
    messages = [{"role": "system", "content": prompt.build(state, tail=False)}]
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


def request(messages, state):
    """What is sent: the conversation, then the run state as its last message."""
    return list(messages) + [{"role": "user", "content": prompt.state_note(state)}]


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
    # A tool result is only valid next to the assistant message that called it, so history
    # is kept or dropped in whole units: a message plus the tool results that answer it.
    # Cutting between them left an orphaned tool result, which the provider refuses
    # ("No tool call found for function call output").
    units = []
    for message in history:
        if message.get("role") == "tool" and units:
            units[-1].append(message)
        else:
            units.append([message])
    kept_units = []
    history_chars = 0
    for unit in reversed(units):
        shortened = []
        for message in unit:
            item = dict(message)
            item["content"] = _short_content(message.get("content", ""), 9000)
            shortened.append(item)
        size = sum(len(item["content"]) for item in shortened)
        if history_chars + size > MAX_KEPT_HISTORY_CHARS:
            break
        kept_units.append(shortened)
        history_chars += size
    kept_units.reverse()
    while kept_units and kept_units[0][0].get("role") == "tool":
        kept_units.pop(0)
    kept_history = [item for unit in kept_units for item in unit]

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
        if len(kept_units) > 1:
            kept_units.pop(0)
            kept_history = [item for unit in kept_units for item in unit]
            result = [system] + kept_history + compacted_current
        else:
            break
    return result

# Reads that serve the plan. Once a plan is accepted their content is in the plan and in the
# run state, and each can be called again if a revision needs it.
_PLANNING_READS = (
    "list_models", "read_model_instruction", "research_capability_check", "list_literature",
)
_REPAIR_PREFIX = "Repair the submitted reproduction plan"


def _tool_payload(message):
    try:
        payload = json.loads(message.get("content") or "")
    except (TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _stub(messages, index, payload, reason):
    stub = json.dumps(
        {"status": payload.get("status"), "summary": payload.get("summary"), "elided": reason},
        ensure_ascii=False,
    )
    if messages[index].get("content") != stub:
        messages[index] = {**messages[index], "content": stub}


def prune_superseded(messages):
    """Replace history that a later step has made obsolete with a one-line stub.

    Three rules, all from what the conversation itself shows, none from a summary:
    a research_plan submission is superseded by the next one, and an accepted plan by the
    next accepted plan; the planning reads before the first accepted plan are in that plan;
    and a call repeated with the same arguments is answered by its latest result. A call and
    its result stay paired, and its summary stays, so the model still sees that the step was
    taken and can call it again. The rules only fire on a new event, so between events the
    request prefix does not change and stays cacheable. Changed messages are replaced, never
    edited, so a request already built keeps what it was sent with.
    """
    messages = list(messages)
    calls = {}
    for index, message in enumerate(messages):
        if message.get("role") == "assistant":
            for position, call in enumerate(message.get("tool_calls") or ()):
                function = call.get("function") or {}
                calls[call.get("id")] = (
                    function.get("name"), function.get("arguments") or "", index, position,
                )
    results = []
    for index, message in enumerate(messages):
        if message.get("role") != "tool" or message.get("tool_call_id") not in calls:
            continue
        payload = _tool_payload(message)
        if payload is None:
            continue
        name, arguments, owner, position = calls[message["tool_call_id"]]
        results.append((index, payload, name, arguments, owner, position))

    plans = [item for item in results if item[2] == "research_plan"]
    accepted = [
        item for item in plans
        if item[1].get("status") == "needs_input"
        and not (item[1].get("data") or {}).get("error_code")
        and (item[1].get("data") or {}).get("plan")
    ]
    for rank, (index, payload, _name, arguments, owner, position) in enumerate(plans):
        later = plans[rank + 1:]
        refused = payload.get("status") == "terminal_error" or (payload.get("data") or {}).get(
            "error_code"
        )
        if refused and later:
            _stub(messages, index, payload, "superseded by a later research_plan call")
            try:
                action = json.loads(arguments).get("action")
            except (TypeError, ValueError, AttributeError):
                action = None
            short = json.dumps({"action": action, "elided": "superseded submission"})
            calls_list = list(messages[owner].get("tool_calls") or ())
            if calls_list[position]["function"].get("arguments") != short:
                calls_list[position] = {
                    **calls_list[position],
                    "function": {**calls_list[position]["function"], "arguments": short},
                }
                messages[owner] = {**messages[owner], "tool_calls": calls_list}
            for follower in range(index + 1, later[0][0]):
                content = str(messages[follower].get("content") or "")
                if messages[follower].get("role") == "user" and content.startswith(_REPAIR_PREFIX):
                    messages[follower] = {
                        **messages[follower],
                        "content": "Repair request for a superseded research_plan submission.",
                    }
        elif not refused and any(item[0] > index for item in accepted) and (
            (payload.get("data") or {}).get("plan")
        ):
            _stub(messages, index, payload, "superseded by a later plan version")

    if accepted:
        first = accepted[0][0]
        for index, payload, name, arguments, _owner, _position in results:
            if index > first:
                continue
            planning_guideline = name == "read_research_guideline" and '"report' not in arguments
            if name in _PLANNING_READS or planning_guideline:
                _stub(messages, index, payload, "used by the accepted plan; call again if needed")

    latest = {}
    for index, payload, name, arguments, _owner, _position in results:
        if payload.get("status") != "success" or name == "research_plan":
            continue
        key = (name, arguments)
        if key in latest:
            _stub(messages, latest[key][0], latest[key][1], "repeated by a later identical call")
        latest[key] = (index, payload)
    return messages
