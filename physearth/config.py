import os
from pathlib import Path

_DEFAULTS = {
    "MODELSCOPE_TOKEN": "",
    "MODELSCOPE_NAMESPACE": "",
    "MODELSCOPE_API_BASE": "https://api-inference.modelscope.cn/v1",
    "MODELSCOPE_MODEL": "Qwen/Qwen3.5-122B-A10B",
    "PHYSEARTH_STATE_DIR": "_state",
    "PHYSEARTH_PORT": "7860",
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


def state_dir():
    path = Path(get("PHYSEARTH_STATE_DIR"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def has_token():
    return bool(get("MODELSCOPE_TOKEN"))
