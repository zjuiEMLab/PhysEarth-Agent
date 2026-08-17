# models/

Every model the agent can run. A model here is content you read, copy and edit — not
library code. The machinery that loads and validates these lives in
`backend/physearth/models/`; nothing in this directory imports anything.

```
bundled/           the six models that ship with the repository
examples/          toy_model, the smallest thing that registers
CONTRACT.md        what the card must declare, and why each rule exists

The starting point lives with the other templates, at the top of the repository:
TEMPLATES/model_card.yaml and TEMPLATES/model_adapter.py.
```

## Register a model in five minutes

```bash
mkdir models/bundled/my_model
cp TEMPLATES/model_card.yaml models/bundled/my_model/model_card.yaml
cp TEMPLATES/model_adapter.py models/bundled/my_model/adapter.py
```

Then edit two files.

**`model_card.yaml`** declares what your model is and what it will accept. This is the
single source of truth: the system prompt, the tool schema and the parameter validation
are all generated from it, so the model cannot be described one way and executed another.

**`adapter.py`** exposes `run(spec) -> dict`. It receives parameters that have already
been checked against the ranges and combinations in your card, and returns arrays.

Start the app and the model is there — in the prompt, in `list_models`, in the validator,
in the approval gate, in the citation rules. None of that is written per model.

Check it before running the app:

```bash
.venv/bin/python -c "from physearth.models import registry; print(registry.summary())"
.venv/bin/python evaluation/runners/model_registration.py
```

A card that fails validation is **rejected, not repaired** — the model does not appear,
and `registry.rejected()` says why. That is deliberate: a model that half-registers would
be validated against one description and run against another.

## Where a model can live

| Where | How it is found | Use it for |
|---|---|---|
| `models/bundled/` | scanned at startup | a model you want in the repository |
| `$PHYSEARTH_MODEL_PATH` | colon-separated directories | your own model, kept outside this repo |
| `physearth.models` entry point | installed distribution | a model shipped as its own package |

`PHYSEARTH_MODEL_PATH` is the one to reach for first if you are trying something out:

```bash
PHYSEARTH_MODEL_PATH=/path/to/my_models .venv/bin/python app.py
```

## demo or local

Every card declares a `tier`.

- **`demo`** — runs wherever this repository runs. It has no dependency beyond what is
  already installed.
- **`local`** — needs a package that may not be present, declared in `requires_import`.
  The registry checks for that import and reports the model as not runnable on a host
  that lacks it, rather than failing at run time. `smrt` is the bundled example.

## These are not in the wheel

`models/` sits outside the installable package, alongside `knowledge/` and `prompts/`.
A built distribution contains the loader, not the models. That is the point: the models
are yours, and an operator's own model is registered by exactly the mechanism the bundled
six use, not a lesser one bolted on beside it.

An installed distribution therefore needs `PHYSEARTH_ROOT` pointing at a checkout, or
`PHYSEARTH_MODEL_PATH` pointing at your own directory.
