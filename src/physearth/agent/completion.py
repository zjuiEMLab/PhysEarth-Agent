"""The provider client and one normalised completion, however the provider shaped it."""

import ast
import json
import time

import httpx
from openai import OpenAI

from physearth import config
from physearth.agent.constants import CONNECT_TIMEOUT_S, REQUEST_TIMEOUT_S


def _client():
    token = config.llm_api_key()
    if not token:
        raise RuntimeError("PHYSEARTH_LLM_API_KEY is not set; the agent cannot reach the model.")
    # The agent loop retries with its own backoff and counts each attempt; the SDK's
    # hidden retries would multiply every one of them.
    return OpenAI(
        api_key=token,
        base_url=config.llm_api_base(),
        max_retries=0,
        timeout=httpx.Timeout(REQUEST_TIMEOUT_S, connect=CONNECT_TIMEOUT_S),
    )


class _Completion:
    """One streamed model response, accumulated as it arrives."""

    def __init__(self):
        self.content = ""
        self.reasoning = 0
        self.reasoning_tokens = None
        self.calls = {}
        self.finish_reason = None
        self.prompt_tokens = None
        self.completion_tokens = None
        self.cost_usd = None
        self.cost_details = None
        self.cached_prompt_tokens = None
        self.started = time.perf_counter()
        self.first_token_s = None

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
            prompt_details = getattr(usage, "prompt_tokens_details", None)
            cached = getattr(prompt_details, "cached_tokens", None) if prompt_details else None
            if cached is not None:
                self.cached_prompt_tokens = int(cached)
            completion_details = getattr(usage, "completion_tokens_details", None)
            thought = getattr(completion_details, "reasoning_tokens", None) if completion_details else None
            if thought is not None:
                self.reasoning_tokens = int(thought)
            details = getattr(usage, "cost_details", None)
            if details is not None:
                self.cost_details = (
                    details.model_dump() if hasattr(details, "model_dump") else details
                )
        if not chunk.choices:
            return False
        choice = chunk.choices[0]
        finish_reason = getattr(choice, "finish_reason", None)
        if finish_reason:
            self.finish_reason = finish_reason
        delta = choice.delta
        if delta is None:
            return False
        grew = False
        # DashScope names the streamed reasoning `reasoning_content`; OpenRouter names it
        # `reasoning`. Reading only the first made every OpenRouter call look like a long
        # silence followed by an answer, when the silence was the model thinking.
        thought = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
        if isinstance(thought, str) and thought:
            self.reasoning += len(thought)
            grew = True
            # first_token_s stays the first token of the answer itself, so the wait before
            # it still shows how long the model thought.
            reasoning_only = True
        else:
            reasoning_only = False
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
        answered = grew and not (reasoning_only and not self.content and not self.calls)
        if answered and self.first_token_s is None:
            self.first_token_s = round(time.perf_counter() - self.started, 2)
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
