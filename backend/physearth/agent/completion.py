"""The provider client and one normalised completion, however the provider shaped it."""

import ast
import json

from openai import OpenAI

from physearth import config


def _client():
    token = config.llm_api_key()
    if not token:
        raise RuntimeError("PHYSEARTH_LLM_API_KEY is not set; the agent cannot reach the model.")
    return OpenAI(api_key=token, base_url=config.llm_api_base())


class _Completion:
    """One streamed model response, accumulated as it arrives."""

    def __init__(self):
        self.content = ""
        self.reasoning = 0
        self.calls = {}
        self.prompt_tokens = None
        self.completion_tokens = None
        self.cost_usd = None
        self.cost_details = None

    def feed(self, chunk):
        usage = getattr(chunk, "usage", None)
        if usage:
            self.prompt_tokens = getattr(usage, "prompt_tokens", None) or self.prompt_tokens
            self.completion_tokens = (
                getattr(usage, "completion_tokens", None) or self.completion_tokens
            )
            cost = getattr(usage, "cost", None)
            if cost is not None:
                self.cost_usd = float(cost)
            details = getattr(usage, "cost_details", None)
            if details is not None:
                self.cost_details = (
                    details.model_dump() if hasattr(details, "model_dump") else details
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
