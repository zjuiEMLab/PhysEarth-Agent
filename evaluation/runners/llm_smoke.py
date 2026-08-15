"""Check provider/model readiness and optionally run one tiny paid completion.

Model discovery is read-only. Inference only happens with ``--execute`` so this runner
can be used safely while editing the competition model matrix.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

from physearth import config  # noqa: E402

MANIFEST = common.ROOT / "competition.yaml"
OUT = common.RESULTS / "competition" / "llm_readiness.json"


def _provider_specs(manifest):
    candidates = manifest.get("model_candidates") or {}
    modelscope = candidates.get("modelscope_provider_diversity") or candidates.get(
        "modelscope_optional", {}
    )
    return [
        {
            "provider": "openrouter",
            "base_url": config.llm_api_base(),
            "api_key": config.llm_api_key(),
            "selection_status": candidates.get("openrouter_selected", {}).get(
                "status", "selected"
            ),
            "models": candidates.get("openrouter_selected", {}).get("models")
            or manifest["execution"]["llms"],
        },
        {
            "provider": "modelscope",
            "base_url": config.get("MODELSCOPE_API_BASE"),
            "api_key": config.get("MODELSCOPE_TOKEN"),
            "selection_status": modelscope.get("status", "pending_confirmation"),
            "note": modelscope.get("note"),
            "models": modelscope.get("models") or [],
        },
    ]


def inspect_provider(spec):
    record = {
        key: value for key, value in spec.items() if key not in {"api_key", "models"}
    }
    record["credential_present"] = bool(spec.get("api_key"))
    record["connected"] = False
    record["visible_model_count"] = None
    record["models"] = []
    if not spec.get("api_key"):
        record["error"] = "credential_missing"
        return record
    try:
        visible = {
            item.id
            for item in OpenAI(
                api_key=spec["api_key"], base_url=spec["base_url"]
            ).models.list().data
        }
        record["connected"] = True
        record["visible_model_count"] = len(visible)
        record["models"] = [
            {"id": model, "available": model in visible} for model in spec["models"]
        ]
    except Exception as exc:
        record["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:300])
        record["models"] = [
            {"id": model, "available": None} for model in spec["models"]
        ]
    return record


def _usage_payload(response):
    raw = response.usage.model_dump() if response.usage else {}
    return {
        "prompt_tokens": raw.get("prompt_tokens"),
        "completion_tokens": raw.get("completion_tokens"),
        "total_tokens": raw.get("total_tokens"),
        "reasoning_tokens": (raw.get("completion_tokens_details") or {}).get(
            "reasoning_tokens"
        ),
        "cost_usd": raw.get("cost"),
        "cost_details": raw.get("cost_details"),
    }


def run_smoke(model):
    started = time.perf_counter()
    response = OpenAI(
        api_key=config.llm_api_key(), base_url=config.llm_api_base()
    ).chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Reply with exactly CONNECTED and no other text.",
            },
            {"role": "user", "content": "PhysEarth inference connectivity test."},
        ],
        temperature=0,
        max_tokens=96,
        extra_body={"reasoning": {"enabled": False}},
    )
    content = response.choices[0].message.content or ""
    return {
        "provider": "openrouter",
        "requested_model": model,
        "response_model": response.model,
        "response_id_present": bool(response.id),
        "content": content,
        "semantic_pass": content.strip().upper() == "CONNECTED",
        "elapsed_s": round(time.perf_counter() - started, 3),
        "llm_usage": _usage_payload(response),
    }


def build_payload(execute=False, model=None):
    config.load_dotenv()
    manifest = common.load_yaml(MANIFEST)
    providers = [inspect_provider(spec) for spec in _provider_specs(manifest)]
    selected = model or manifest["execution"]["llms"][0]
    smoke = run_smoke(selected) if execute else None
    return {
        "schema_version": "llm-readiness-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inference_executed": bool(execute),
        "providers": providers,
        "smoke": smoke,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args(argv)
    payload = build_payload(args.execute, args.model)
    if not args.execute and args.output.is_file():
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        payload["smoke"] = previous.get("smoke")
        payload["inference_executed"] = bool(payload["smoke"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    for provider in payload["providers"]:
        available = sum(item.get("available") is True for item in provider["models"])
        print(
            "%s: %s; %d visible; %d/%d candidate models available"
            % (
                provider["provider"],
                "CONNECTED" if provider["connected"] else "FAILED",
                provider["visible_model_count"] or 0,
                available,
                len(provider["models"]),
            )
        )
    if payload["smoke"]:
        usage = payload["smoke"]["llm_usage"]
        print(
            "smoke %s: %s, %s tokens, $%.7f"
            % (
                payload["smoke"]["requested_model"],
                "PASS" if payload["smoke"]["semantic_pass"] else "FAIL",
                usage.get("total_tokens"),
                usage.get("cost_usd") or 0.0,
            )
        )
    else:
        print("Discovery only: no inference call. Add --execute for one smoke completion.")
    print("result -> %s" % args.output)
    return 0 if all(provider["connected"] for provider in payload["providers"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
