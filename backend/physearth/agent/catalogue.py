"""Which language models this deployment will talk to, and session creation.

The catalogue is built from configuration, never from the browser: `resolve_model`
is the guard that keeps a crafted model name from reaching an arbitrary endpoint.
"""

from physearth import config
from physearth import session as session_state

_MODEL_LABELS = {
    "Qwen/Qwen3.5-122B-A10B": "Qwen3.5 122B-A10B",
    "deepseek-ai/DeepSeek-V4-Flash-0731": "DeepSeek V4 Flash",
    "ZhipuAI/GLM-4.7-Flash": "GLM 4.7 Flash",
    "qwen-plus": "Qwen Plus",
    "qwen-turbo": "Qwen Turbo",
    "qwen-max": "Qwen Max",
}


def _model_card(model_id):
    label = _MODEL_LABELS.get(model_id, model_id.replace("/", " · "))
    vendor = "Qwen" if "qwen" in model_id.lower() else model_id.split("/", 1)[0]
    return {"id": model_id, "label": label, "vendor": vendor, "note": "configured in .env"}


CATALOGUE = [_model_card(model_id) for model_id in config.llm_models()]


def default_model():
    wanted = config.llm_model()
    known = [m["id"] for m in CATALOGUE]
    return wanted if wanted in known else (known[0] if known else wanted)


def resolve_model(name, unrestricted=False):
    """Only ever run a model from the catalogue, whatever the client sent.

    The guard exists because the chosen model arrives from the browser, and without it a
    crafted value would make this process call an arbitrary endpoint. `unrestricted` is
    for callers that are not a browser: the evaluation suite drives the agent on models
    outside the switcher on purpose, so that a sweep never competes for the quota of the
    three the interface offers. It is passed by the process that starts the run and is
    reachable from nothing else.
    """
    known = [m["id"] for m in CATALOGUE]
    if unrestricted and name:
        return name
    return name if name in known else default_model()


def new_session(model=None, unrestricted=False):
    session = session_state.new_session(resolve_model(model, unrestricted))
    session["unrestricted"] = bool(unrestricted)
    return session


def new_state(model=None, session=None):
    if session is None:
        return session_state.new_state(model=resolve_model(model))
    return session_state.new_state(session, resolve_model(model or session.get("model")))
