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
