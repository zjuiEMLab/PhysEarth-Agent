"""Dedicated label-blinded LLM judge using evaluation-only credentials."""

import base64
import json
import re
import time
from pathlib import Path

import yaml
from openai import OpenAI

from physearth import config

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
STANDARD_PATH = ROOT / "standards" / "report_judge.yaml"
FIGURE_STANDARD_PATH = ROOT / "standards" / "q1_figure3.yaml"
DIMENSIONS = ("factuality", "completeness", "evidence", "calibration", "clarity")
FIGURE_DIMENSIONS = ("line_count", "patterns", "grouping", "visual_correspondence")
PREFLIGHT_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "judge_preflight",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"status": {"type": "string", "const": "READY"}},
            "required": ["status"],
            "additionalProperties": False,
        },
    },
}
REPORT_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "scientific_report_score",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "scores": {
                    "type": "object",
                    "properties": {
                        name: {"type": "integer", "minimum": 0, "maximum": 2}
                        for name in DIMENSIONS
                    },
                    "required": list(DIMENSIONS),
                    "additionalProperties": False,
                },
                "factual_errors": {
                    "type": "array",
                    "maxItems": 3,
                    "items": {"type": "string", "maxLength": 240},
                },
                "summary": {"type": "string", "maxLength": 400},
            },
            "required": ["scores", "factual_errors", "summary"],
            "additionalProperties": False,
        },
    },
}
FIGURE_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "scientific_figure_visual_score",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "scores": {
                    "type": "object",
                    "properties": {
                        name: {"type": "integer", "minimum": 0, "maximum": 2}
                        for name in FIGURE_DIMENSIONS
                    },
                    "required": list(FIGURE_DIMENSIONS),
                    "additionalProperties": False,
                },
                "observations": {
                    "type": "array",
                    "maxItems": 4,
                    "items": {"type": "string", "maxLength": 240},
                },
                "summary": {"type": "string", "maxLength": 400},
            },
            "required": ["scores", "observations", "summary"],
            "additionalProperties": False,
        },
    },
}


class JudgeResponseError(ValueError):
    def __init__(self, message, meta):
        super().__init__(message)
        self.meta = meta


def standard():
    return yaml.safe_load(STANDARD_PATH.read_text(encoding="utf-8"))


def standard_figure():
    return yaml.safe_load(FIGURE_STANDARD_PATH.read_text(encoding="utf-8"))


def settings(candidate_models=()):
    values = {
        "api_key": config.eval_llm_api_key(),
        "base_url": config.eval_llm_api_base(),
        "model": config.eval_llm_model(),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError(f"missing evaluation judge setting(s): {', '.join(missing)}")
    candidate_aliases = set().union(*(_model_aliases(item) for item in candidate_models))
    if _model_aliases(values["model"]) & candidate_aliases:
        raise RuntimeError("EVAL_LLM_MODEL must differ from every candidate model")
    return values


def _model_aliases(value):
    normalized = str(value or "").strip().lower()
    if not normalized:
        return set()
    return {normalized, normalized.rsplit("/", 1)[-1]}


def _usage(response):
    raw = response.usage.model_dump() if response.usage else {}
    return {
        "prompt_tokens": raw.get("prompt_tokens"),
        "completion_tokens": raw.get("completion_tokens"),
        "total_tokens": raw.get("total_tokens"),
    }


def _safe_error(exc, api_key):
    return _redact(f"{type(exc).__name__}: {exc}", api_key)


def _redact(value, api_key=None):
    text = str(value or "")
    if api_key:
        text = text.replace(str(api_key), "[REDACTED]")
    text = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,}]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(api[_ -]?key\s*[:=]\s*)[^\s,}]+", r"\1[REDACTED]", text)
    return text[:600]


def _request(messages, candidate_models=(), max_tokens=1200, response_format=None):
    cfg = settings(candidate_models)
    started = time.perf_counter()
    response = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"]).chat.completions.create(
        model=cfg["model"],
        messages=messages,
        temperature=0,
        max_tokens=max_tokens,
        response_format=response_format or REPORT_RESPONSE_FORMAT,
    )
    content = response.choices[0].message.content or ""
    meta = {
        "model": cfg["model"],
        "response_model": response.model,
        "finish_reason": response.choices[0].finish_reason,
        "response_chars": len(content),
        "elapsed_s": round(time.perf_counter() - started, 3),
        "usage": _usage(response),
    }
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        meta["response_excerpt"] = _redact(content, cfg["api_key"])
        raise JudgeResponseError("judge response was not valid JSON", meta) from exc
    if not isinstance(value, dict):
        meta["response_excerpt"] = _redact(content, cfg["api_key"])
        raise JudgeResponseError("judge response must be a JSON object", meta)
    return value, meta


def preflight(candidate_models=()):
    """Make one tiny structured-output call before any candidate session starts."""
    try:
        settings(candidate_models)
    except Exception as exc:
        return {"passed": False, "error": _safe_error(exc, config.eval_llm_api_key())}
    attempts = []
    for _ in range(3):
        meta = None
        try:
            value, meta = _request(
                [
                    {
                        "role": "system",
                        "content": "Return one JSON object with exactly {\"status\":\"READY\"}.",
                    },
                    {"role": "user", "content": "Evaluation judge structured-output preflight."},
                ],
                candidate_models=candidate_models,
                max_tokens=64,
                response_format=PREFLIGHT_RESPONSE_FORMAT,
            )
            if value != {"status": "READY"}:
                raise ValueError("judge preflight returned an unexpected object")
            attempts.append({"status": "success", **meta})
            return {"passed": True, **meta, "attempts": attempts, "usage": _sum_usage(attempts)}
        except Exception as exc:
            failure = {"status": "error", "error": _safe_error(exc, config.eval_llm_api_key())}
            recovered_meta = getattr(exc, "meta", None) or meta
            if recovered_meta:
                failure.update(recovered_meta)
            attempts.append(failure)
    return {
        "passed": False,
        "error": "judge preflight failed after three attempts",
        "attempts": attempts,
        "usage": _sum_usage(attempts),
    }


def _valid_scores(value):
    scores = value.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
        raise ValueError(f"judge scores must contain exactly {', '.join(DIMENSIONS)}")
    for name in DIMENSIONS:
        score = scores[name]
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 2:
            raise ValueError(f"judge score {name} must be an integer from 0 to 2")
    errors = value.get("factual_errors")
    if not isinstance(errors, list) or any(not isinstance(item, str) for item in errors):
        raise ValueError("factual_errors must be an array of strings")
    if not isinstance(value.get("summary"), str):
        raise ValueError("summary must be a string")
    return scores


def _valid_figure_scores(value):
    scores = value.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(FIGURE_DIMENSIONS):
        raise ValueError(
            "figure judge scores must contain exactly "
            f"{', '.join(FIGURE_DIMENSIONS)}"
        )
    for name in FIGURE_DIMENSIONS:
        score = scores[name]
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 2:
            raise ValueError(f"figure judge score {name} must be an integer from 0 to 2")
    observations = value.get("observations")
    if not isinstance(observations, list) or any(
        not isinstance(item, str) for item in observations
    ):
        raise ValueError("figure judge observations must be an array of strings")
    if not isinstance(value.get("summary"), str):
        raise ValueError("figure judge summary must be a string")
    return scores


def _image_message(path, label):
    image = Path(path)
    if not image.is_absolute():
        image = REPO / image
    if not image.is_file():
        raise FileNotFoundError(f"{label} image is not available")
    encoded = base64.b64encode(image.read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{encoded}"},
    }


def _figure_paths(record, fixture):
    figure = next(
        (
            item
            for item in record.get("figures") or []
            if item.get("archived_image_path") or item.get("image_path")
        ),
        None,
    )
    if not figure:
        return None, None
    visual_reference = fixture.get("visual_reference") or {}
    return visual_reference.get("image_path"), (
        figure.get("archived_image_path") or figure.get("image_path")
    )


def judge_figure(record, candidate_models=()):
    """Blind-review a rendered figure against the versioned reference image.

    This is intentionally qualitative: it judges visible curve count and patterns, not
    captions, formatting, pixels, or numeric error metrics.
    """
    from .figure3 import reference

    settings(candidate_models)
    fixture = reference()
    visual_standard = (standard_figure().get("figure") or {}).get("visual_judge") or {}
    reference_path, candidate_path = _figure_paths(record, fixture)
    if not reference_path or not candidate_path:
        return {
            "complete": False,
            "passed": False,
            "status": "not_scoreable",
            "error": "reference or candidate figure image is unavailable",
            "attempts": [],
            "usage": _sum_usage([]),
        }
    expected_line_count = (fixture.get("visual_reference") or {}).get("expected_line_count", 6)
    rubric = {
        "dimensions": visual_standard.get("dimensions") or {},
        "ignored": visual_standard.get("ignored") or [],
        "score_scale": visual_standard.get("score_scale") or {},
        "pass": visual_standard.get("pass") or {},
    }
    system = (
        "You are a label-blinded visual scientific-figure evaluator. Compare the reference "
        "image with the candidate image. Judge only visible qualitative correspondence: "
        f"the candidate is expected to show {expected_line_count} distinct data curves, "
        "their qualitative patterns, their relative grouping/order, and whether the same "
        "scientific figure is communicated. Every score must be exactly 0, 1, or 2; a score "
        "of 3 is invalid. Do not use OCR or exact text matching as a "
        "substitute for visual comparison. Do not score exact title/caption wording, fonts, "
        "colors, layout, canvas dimensions, pixel similarity, RMSE, or any numeric error. "
        "Do not count legend samples or grid lines as data curves. Return only the strict "
        "JSON schema requested. Human-maintained rubric: "
        + json.dumps(rubric, ensure_ascii=False)
    )
    user_content = [
        {
            "type": "text",
            "text": (
                "Reference image comes first; candidate image comes second. "
                "Describe only material visual similarities or differences in the bounded "
                "observations field."
            ),
        },
        _image_message(reference_path, "reference"),
        _image_message(candidate_path, "candidate"),
    ]
    base_messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]
    attempts = []
    for _ in range(3):
        meta = None
        try:
            messages = list(base_messages)
            if attempts:
                messages[0] = {
                    "role": "system",
                    "content": (
                        system
                        + " Previous output was invalid. Return only the requested JSON "
                        "object with integer scores. Scores must be exactly 0, 1, or 2; "
                        "never output 3. Do not use Markdown."
                    ),
                }
            value, meta = _request(
                messages,
                candidate_models=candidate_models,
                max_tokens=1800,
                response_format=FIGURE_RESPONSE_FORMAT,
            )
            scores = _valid_figure_scores(value)
            attempts.append({"status": "success", **meta})
            pass_rule = visual_standard.get("pass") or {}
            required_scores = pass_rule.get("required_scores") or {}
            total = sum(scores.values())
            passed = bool(
                total >= int(pass_rule.get("minimum_total", 6))
                and all(scores[name] >= int(minimum) for name, minimum in required_scores.items())
            )
            return {
                "complete": True,
                "passed": passed,
                "status": "pass" if passed else "fail",
                "total": total,
                "scores": scores,
                "observations": value["observations"],
                "summary": value["summary"],
                "judge_model": meta["model"],
                "attempts": attempts,
                "usage": _sum_usage(attempts),
            }
        except Exception as exc:
            failure = {
                "status": "error",
                "error": _safe_error(exc, config.eval_llm_api_key()),
            }
            recovered_meta = getattr(exc, "meta", None) or meta
            if recovered_meta:
                failure.update(recovered_meta)
            attempts.append(failure)
    return {
        "complete": False,
        "passed": False,
        "status": "not_scoreable",
        "error": "figure judge failed after three attempts",
        "attempts": attempts,
        "usage": _sum_usage(attempts),
    }


def judge_report(
    record,
    task,
    figure_score,
    deterministic,
    candidate_models=(),
    figure_judgement=None,
):
    """Blind-review one final report; scenario/config names are intentionally omitted."""
    from .figure3 import reference

    settings(candidate_models)

    gold = reference()
    payload = {
        "research_question": task.get("question"),
        "reference_source": gold["source"],
        "reference_facts": gold["report_facts"],
        "required_curve_labels": [item["label"] for item in gold["curves"]],
        "measured_figure_result": {
            "passed": figure_score.get("passed"),
            "recipe": figure_score.get("recipe"),
            "numeric": figure_score.get("numeric"),
            "plot": {
                "passed": (figure_score.get("plot") or {}).get("passed"),
                "checks": (figure_score.get("plot") or {}).get("checks"),
            },
        },
        "visual_figure_judgement": {
            "status": (figure_judgement or {}).get("status"),
            "scores": (figure_judgement or {}).get("scores"),
            "summary": (figure_judgement or {}).get("summary"),
            "observations": (figure_judgement or {}).get("observations"),
        },
        "deterministic_report_checks": deterministic,
        "candidate_report": record.get("answer") or "",
    }
    rubric = standard()
    pass_rule = rubric.get("pass") or {}
    system = (
        "You are a label-blinded scientific report evaluator. You are not told which system "
        "produced the report. Judge only against the supplied source facts and measured run "
        "results. Score factuality, completeness, evidence, calibration, and clarity as "
        "integers 0, 1, or 2. Manual/LLM visual figure judgement is the primary evidence for "
        "qualitative figure success. Deterministic title, caption, legend, recipe, or numeric "
        "check failures caused by unspecified parameters are diagnostics, not automatic factual "
        "failure. Reject a success claim only when the required curves are missing, visual "
        "judgement fails, or an explicit paper condition is contradicted. Visual agreement does "
        "not waive a failed run, missing evidence, unsupported model/output, or an explicit user "
        "numeric/parameter requirement. Use the visual figure "
        "judgement and related source facts when checking claims. Return strict JSON with "
        "exactly "
        "three keys: scores (the five named integer fields), factual_errors (at most three "
        "concise strings, each under 240 characters), and summary (under 400 characters). "
        "Use this human-maintained rubric exactly: "
        + json.dumps(rubric, ensure_ascii=False)
    )
    attempts = []
    base_messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    for _ in range(3):
        meta = None
        try:
            messages = list(base_messages)
            if attempts:
                messages[0] = {
                    "role": "system",
                    "content": (
                        system
                        + " Previous output was invalid. Return only the requested JSON "
                        "object; do not use Markdown fences or explanatory text. Keep "
                        "factual_errors to at most three short items and summary under "
                        "400 characters."
                    ),
                }
            value, meta = _request(
                messages,
                candidate_models=candidate_models,
                max_tokens=3000,
                response_format=REPORT_RESPONSE_FORMAT,
            )
            scores = _valid_scores(value)
            attempts.append({"status": "success", **meta})
            total = sum(scores.values())
            passed = bool(
                deterministic.get("passed")
                and scores["factuality"] >= int(pass_rule.get("factuality", 2))
                and total >= int(pass_rule.get("minimum_total", 8))
            )
            return {
                "complete": True,
                "passed": passed,
                "total": total,
                "scores": scores,
                "factual_errors": value["factual_errors"],
                "summary": value["summary"],
                "judge_model": meta["model"],
                "attempts": attempts,
                "usage": _sum_usage(attempts),
            }
        except Exception as exc:
            failure = {
                "status": "error",
                "error": _safe_error(exc, config.eval_llm_api_key()),
            }
            recovered_meta = getattr(exc, "meta", None) or meta
            if recovered_meta:
                failure.update(recovered_meta)
            attempts.append(failure)
    return {
        "complete": False,
        "passed": False,
        "error": "judge failed after three attempts",
        "attempts": attempts,
        "usage": _sum_usage(attempts),
    }


def _sum_usage(attempts):
    usages = [item.get("usage") or {} for item in attempts]
    result = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        values = [item.get(name) for item in usages]
        result[name] = (
            sum(values)
            if values and all(isinstance(value, int) for value in values)
            else None
        )
    return result
