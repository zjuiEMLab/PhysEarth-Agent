"""Deterministic context relief: prune oversized tool output before anything summarises.

The request builder keeps a long research conversation inside the provider window by
shortening history, and the cheapest shortening is the one that needs no model call and
changes no meaning: an oversized tool result is truncated at both ends, keeping the head
(what the call returned, in schema order) and the tail (counts, error codes, trailing
records) with an explicit marker for what was removed.

This mirrors the deterministic pruner DeepSeek Harness runs before its summarising
compaction: prefer the change that can be proven correct, and only reach for a model when
that is not enough.  The report is returned, not logged, so the caller decides whether it
belongs in the run trace or the journal.
"""

from physearth import config

DEFAULT_MAX_CHARS = 8192
HEAD_SHARE = 0.55
SECRET_HINTS = ("token", "secret", "password", "api_key", "apikey", "authorization")


def max_chars():
    try:
        value = int(config.get("PHYSEARTH_TOOL_OUTPUT_MAX_CHARS") or DEFAULT_MAX_CHARS)
    except (TypeError, ValueError):
        return DEFAULT_MAX_CHARS
    return value if value >= 256 else DEFAULT_MAX_CHARS


def marker(removed, original):
    return "\n… [pruned %d of %d characters]\n" % (removed, original)


def prune(text, limit=None):
    """Head/tail truncate one payload, or return it unchanged when it already fits.

    The marker counts against the limit, and the removed-character count inside it changes
    the marker's own width, so the split is solved twice before it is applied.  The result
    therefore always fits the limit and a second pass is a no-op, which is what makes this
    safe to run on every request instead of only when a provider complains.
    """
    limit = max_chars() if limit is None else limit
    if not isinstance(text, str) or len(text) <= limit:
        return text
    original = len(text)
    reserved = len(marker(original, original))
    head = tail = 0
    for _ in range(3):
        budget = max(limit - reserved, 1)
        head = int(budget * HEAD_SHARE)
        tail = max(budget - head, 0)
        reserved = len(marker(original - head - tail, original))
    return text[:head] + marker(original - head - tail, original) + (
        text[-tail:] if tail else ""
    )


def prune_tool_outputs(messages, limit=None):
    """Prune every oversized ``tool`` message and report what changed.

    Returns ``(messages, report)`` where the report lists one record per pruned message:
    its index, the tool name when it is known from the payload, and the character counts
    before and after.  Non-tool messages are left alone; a payload that already fits is
    left alone; nothing here can grow a message.
    """
    limit = max_chars() if limit is None else limit
    report = []
    pruned_messages = []
    for index, message in enumerate(messages or ()):
        item = dict(message)
        content = item.get("content")
        if item.get("role") == "tool" and isinstance(content, str) and len(content) > limit:
            item["content"] = prune(content, limit)
            report.append(
                {
                    "index": index,
                    "tool": _tool_name(content),
                    "before_chars": len(content),
                    "after_chars": len(item["content"]),
                }
            )
        pruned_messages.append(item)
    return pruned_messages, report


def _tool_name(content):
    """Best-effort tool identity from the recorded payload, for the report only."""
    head = content[:200]
    for key in ('"tool"', '"name"', '"model"'):
        position = head.find(key)
        if position < 0:
            continue
        tail = head[position + len(key):]
        if ":" not in tail:
            continue
        value = tail.split(":", 1)[1].strip()
        if value.startswith('"'):
            return value[1:].split('"', 1)[0][:60]
    return ""


def total_chars(messages):
    return sum(len(str((message or {}).get("content", ""))) for message in messages or ())


def estimated_tokens(messages):
    """Fixed-density estimate, deliberately not a tokenizer: stable and cheap.

    Four characters per token is the same conservative heuristic the token meters in this
    project already use; it exists to decide *when* to relieve pressure, not to bill a
    provider.
    """
    return int(total_chars(messages) / 4)
