import os
from pathlib import Path

_DEFAULTS = {
    "PHYSEARTH_LLM_API_KEY": "",
    "PHYSEARTH_LLM_API_BASE": "",
    "PHYSEARTH_LLM_MODEL": "",
    "PHYSEARTH_LLM_MODELS": "",
    "MODELSCOPE_TOKEN": "",
    "MODELSCOPE_NAMESPACE": "",
    "MODELSCOPE_API_BASE": "https://api-inference.modelscope.cn/v1",
    "MODELSCOPE_MODEL": "Qwen/Qwen3.5-122B-A10B",
    "PHYSEARTH_ONLINE": "1",
    "PHYSEARTH_STATE_DIR": "_state",
    # Zero means unlimited. Provider quotas and context checks remain independent.
    "PHYSEARTH_MAX_MODEL_CALLS": "0",
    "PHYSEARTH_MAX_TOOL_CALLS": "0",
    "PHYSEARTH_MAX_SESSION_MODEL_CALLS": "0",
    "PHYSEARTH_MAX_SESSION_TOOL_CALLS": "0",
    "PHYSEARTH_MAX_QUESTIONS_PER_HOUR": "0",
    "PHYSEARTH_PORT": "7860",
    "PHYSEARTH_LOG_MAX_BYTES": str(5 * 1024 * 1024),
    "PHYSEARTH_SESSION_LOG_MAX_BYTES": str(10 * 1024 * 1024),
    "PHYSEARTH_LOG_BACKUP_COUNT": "5",
    "PHYSEARTH_HOST": "0.0.0.0",
}


def load_dotenv(path=".env"):
    f = Path(path)
    if not f.is_file():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def get(name):
    return os.environ.get(name, _DEFAULTS.get(name, ""))


def llm_api_key():
    """Provider-neutral key, with the old ModelScope name kept for deployments."""
    return get("PHYSEARTH_LLM_API_KEY") or get("MODELSCOPE_TOKEN")


def llm_api_base():
    return get("PHYSEARTH_LLM_API_BASE") or get("MODELSCOPE_API_BASE")


def llm_model():
    return get("PHYSEARTH_LLM_MODEL") or get("MODELSCOPE_MODEL")


def llm_models():
    raw = get("PHYSEARTH_LLM_MODELS")
    if raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    return [
        "Qwen/Qwen3.5-122B-A10B",
        "deepseek-ai/DeepSeek-V4-Flash-0731",
        "ZhipuAI/GLM-4.7-Flash",
    ]


def state_dir():
    path = Path(get("PHYSEARTH_STATE_DIR"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def has_token():
    return bool(llm_api_key())


def nonnegative_int(name, default=0):
    try:
        return max(0, int(get(name) or default))
    except (TypeError, ValueError):
        return max(0, int(default))


# Load local provider selection before agent.py builds its model switcher catalogue.
load_dotenv()
