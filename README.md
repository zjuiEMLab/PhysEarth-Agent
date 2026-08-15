---
domain:
tags:
- geoai
- remote-sensing
- radiative-transfer
- agent
- physics
datasets:
models:
deployspec:
  entry_file: app.py
license: Apache License 2.0
---

# PhysEarth-Agent

An open-source GeoAI agent that turns geophysical models into research instruments you can
talk to, check and reproduce. **Register a model and it inherits the whole system: parameter
validation, illegal-call refusal, result quality control, citation integrity and a visible
run trace.** None of that has to be rewritten for the next model.

Most GeoAI systems are data-driven. This one runs physics, and its point is not that it can
run a physical model — a notebook can do that — but that a physical model can be
**configured with justified confidence**. Deep models fail visibly: a bad configuration
gives a bad score. Physical models fail silently. Snow density entered as 2000 kg/m³, a
microstructure representation that does not apply at the chosen frequency, a unit off by an
order of magnitude — none of these crash. Each returns a curve that is physically
meaningless and numerically entirely plausible.

So the checks live in the system rather than in the prompt:

- parameters are checked against each model's declared physical ranges and legal
  combinations **before** the model runs;
- a human approves the run, and the model has no way to approve on its own behalf;
- the result is checked against the declared output bounds **after** it runs;
- every claim in an answer must carry a marker that resolves to a paper section the agent
  actually opened, a model it actually ran, a dataset it actually queried, or a method note
  it actually followed;
- a paper the agent has only seen listed carries a weaker marker that may never carry a
  value in kelvin, decibels or volumetric soil moisture;
- text that came from outside the system arrives inside a labelled boundary and is treated
  as evidence, never as instruction;
- numeric arrays never enter the model's context. A run returns a handle and a bounded
  preview, and the full result stays in the session store;
- charts are drawn from a declarative specification naming those handles, never from code
  the agent wrote, and a measured series is never drawn like a simulated one;
- two curves are not differenced until they are shown to be comparable, so a bias between a
  brightness temperature and a backscatter is refused rather than printed.

None of these is a tool the agent may skip. The run trace shows each one, including the
refusals.

## What the evidence is, and how far each kind reaches

| Tier | What it is | Marker | What it can support |
|---|---|---|---|
| bundled | shipped with this repository, full text | `[slug#id]` | anything |
| session | fetched by DOI during the conversation, full text | `[slug#id]`, marked in the trace | anything |
| abstract | seen in a search result, metadata only | `[abs:doi]` | what a study was about, never a value |
| method | a procedure note the agent opened before acting | `[skill:slug]` | that the procedure was followed |

The agent can search the open-access literature through OpenAlex and take a paper's full
text into the conversation by DOI, from Copernicus or Europe PMC. It passes a DOI and never
a URL: every address is constructed here, only over HTTPS, only to an allowed host.
`PHYSEARTH_ONLINE=0` closes that layer entirely and nothing else changes.

## Evaluation

`evaluation/` holds a reproducible task set, four ablation configurations and the runners
that produce [`evaluation/REPORT.md`](evaluation/REPORT.md). Tier 0 costs nothing to re-run
and pins the bundled models against the upstream packages they wrap. The agent task set
reproduces figures from the SMRT paper and probes what happens when the harness, the corpus
or the capability declarations are removed. See [`evaluation/README.md`](evaluation/README.md).

## Registered models

Few and deliberate. Breadth is meant to come from the registration mechanism, not from us
piling models in.

| Model | Domain | Output | Runs here |
|---|---|---|---|
| `smrt` | snow and ice, microwave | brightness temperature, backscatter, electromagnetic coefficients | yes |
| `tau_omega` | soil and vegetation, passive microwave | brightness temperature, emissivity | yes |
| `water_cloud` | soil and vegetation, active microwave | backscatter | yes |
| `pywatershed` | catchment hydrology, PRMS | SWE, snowmelt, surface runoff, soil-zone and groundwater flow | yes |
| `prosail` | vegetation, optical | canopy reflectance in four bands, NDVI | yes |
| `pyet` | land surface, water balance | reference evapotranspiration, six formulations | yes |

Every one of them is a `demo` model: it ships in this package and runs where the package
runs. The `local` tier exists for a model an operator registers themselves, and nothing
published here uses it.

The first three answer what a surface looks like to a microwave sensor, `prosail` answers
what the same vegetated surface looks like to an optical one, and `pyet` and `pywatershed`
answer what the water in it is doing. `pywatershed` runs
the PRMS process chain over the official five-year Sagehen Creek domain and answers what the
water in that surface is doing, which is why the harness is not written around any one
physics: the same parameter validation, quality control and citation rules apply to a
hydrologic model that never emits a photon. See
[`docs/pywatershed-prms-3.0.0.md`](docs/pywatershed-prms-3.0.0.md).

Its pinned Sagehen domain is fetched once into the state directory and checksummed on first
use; it is not redistributed here.

## Next steps

- [Reproduce the SMRT v1 Section 3 experiments](docs/smrt_section3_scientific_questions_and_steps.md):
  the paper's sparse-medium, reference-model and microstructure-equivalence investigations
  as an end-to-end research-agent baseline. Reading that document is what prompted the
  `coefficients` output, `iba_original`, cross-polarised backscatter and the widened
  density and thickness bounds below; what remains out of reach is the part that needs
  DMRT-ML, DMRT-QMS and MEMLS, which are three separate packages.

## Bundled literature and method notes

Eight open-access Copernicus papers, redistributed under their CC-BY licences, split into 79
citable sections, plus three method notes the agent reads before acting: planning a run,
comparing two models, and reporting a result. See `NOTICE` for the per-paper attribution.

## Bundled measurements

Radar backscatter measured at Trail Valley Creek in 2018/19 at C, X and Ku band, 23658 rows,
plus per-station soil roughness from airborne lidar. Published under the Open Government
Licence - Canada. The agent can run a model at the configuration a measurement was taken at
and compare the two. `scripts/build_reference.py` regenerates the tables from the published
files.

## Running it

```bash
uv pip install -r requirements.txt
export MODELSCOPE_TOKEN=...        # or put it in .env
python app.py
```

`MODELSCOPE_MODEL` sets the language model the agent starts with. The interface offers
three, and the choice is per session: Qwen3.5-122B-A10B, DeepSeek-V4-Flash and
GLM-4.7-Flash, all reached through the public ModelScope API-Inference endpoint.

Every setting has a working default, so the application starts with no `.env` present.

| Variable | Default | What it does |
|---|---|---|
| `MODELSCOPE_TOKEN` | empty | the only secret; needed to reach the inference endpoint |
| `MODELSCOPE_MODEL` | `Qwen/Qwen3.5-122B-A10B` | which language model a session starts on |
| `PHYSEARTH_ONLINE` | `1` | `0` removes the two online literature tools entirely |
| `PHYSEARTH_MODEL_PATH` | empty | extra model directories to register |
| `PHYSEARTH_STATE_DIR` | `_state` | the one directory written to |
| `PHYSEARTH_HOST`, `PHYSEARTH_PORT` | `0.0.0.0`, `7860` | where it listens |
| `PHYSEARTH_LOG_MAX_BYTES` | `5242880` | rotating application/global-event log size |
| `PHYSEARTH_SESSION_LOG_MAX_BYTES` | `10485760` | rotating log size for one research session |
| `PHYSEARTH_LOG_BACKUP_COUNT` | `5` | old log generations retained |

### Persistent audit logs

The browser Run trace is mirrored to disk, so a stopped or restarted process can still be
diagnosed. Logs are written beneath `PHYSEARTH_STATE_DIR/logs/`:

- `application.log` records service lifecycle messages;
- `errors.log` records uncaught exceptions with tracebacks;
- `events.jsonl` records every structured agent, tool, gate, QA and human-review event;
- `sessions/<session_id>.jsonl` contains the same events for one conversation only.

Each JSONL event includes UTC time, event ID, process/thread, session and turn IDs, active
model, research phase, plan version, selected charts, planned runs and counters. API keys,
tokens, authorization headers, cookies and passwords are redacted before serialization.
All files rotate according to the settings above; a logging failure never stops a model run.

---

# Adding your own model

This is the part worth reading. A model is a folder with two files in it, and you never
import PhysEarth to write either one.

```
my_model/
  model_card.yaml
  adapter.py
```

We will build one from scratch. It computes how much microwave energy gets through a layer,
which is the simplest thing that is still shaped like a real model.

## 1. Write the adapter

Create `my_model/adapter.py`:

```python
import math


def run(spec):
    transmissivity = math.exp(-spec["optical_depth"] / math.cos(math.radians(spec["angle_deg"])))
    return {
        "axis": None,
        "points": [{"index": 0, "transmissivity": transmissivity}],
        "series": {"transmissivity": [transmissivity]},
    }
```

That is the whole contract. You get a `spec` dict and you return three keys.

`spec` arrives clean. Defaults are already filled in, types are already coerced, ranges are
already checked. You do not need to validate anything, and you should not: if you range-check
inside the adapter, the agent sees a crash instead of an explanation.

`series` is what gets checked and plotted. `points` is the row-wise version of the same
numbers. `axis` is `None` unless you are sweeping, which we will add in step 4.

## 2. Write the card

Create `my_model/model_card.yaml`:

```yaml
name: my_model
version: "0.1.0"
tier: demo
entrypoint: adapter:run
license: Apache-2.0
citation: Where this model comes from.
description: >-
  One paragraph. The agent reads this to decide whether your model is the right one for the
  question, so write what it is for, not how it works.

parameters:
  optical_depth:
    type: number
    unit: none
    description: Optical depth of the layer.
    minimum: 0.0
    maximum: 20.0
    default: 1.0
  angle_deg:
    type: number
    unit: degree
    description: Incidence angle from nadir.
    minimum: 0.0
    maximum: 80.0
    default: 55.0

outputs:
  transmissivity:
    unit: none
    description: Fraction of energy transmitted.
    valid_min: 0.0
    valid_max: 1.0
```

Two things will trip you up.

**Every numeric parameter needs `minimum` and `maximum`.** A card without them is rejected.
This is deliberate: a missing range does not fail loudly, it makes the range check pass
everything, and you would never notice.

**In YAML an exponent needs a sign.** Write `1.0e+9`, not `1.0e9`. Without the sign it loads
as the string `"1.0e9"` and your bound is text, not a number. The card checker catches this,
but it costs you a minute if you do not know.

## 3. Check it

```bash
python -m physearth.models.check my_model
```

```
card is valid: my_model v0.1.0 (tier demo)
adapter loaded: adapter:run
parameters: 2, outputs: transmissivity
```

Run this before you wire anything up. It reads the card, applies the same rules the registry
applies, and loads your adapter.

## 4. Add a sweep

Most questions are about a trend, not a number, so a model that can only do one point at a
time is half a model. Add four parameters to the card:

```yaml
  sweep_parameter:
    type: string
    unit: none
    description: Numeric parameter to sweep instead of holding fixed.
    enum: [none, optical_depth, angle_deg]
    default: none
    required: false
  sweep_start:
    type: number
    unit: same as the swept parameter
    description: First value of the sweep.
    minimum: -1.0e+9
    maximum: 1.0e+9
    required: false
  sweep_stop:
    type: number
    unit: same as the swept parameter
    description: Last value of the sweep.
    minimum: -1.0e+9
    maximum: 1.0e+9
    required: false
  sweep_points:
    type: integer
    unit: count
    description: Number of points in the sweep.
    minimum: 2
    maximum: 60
    default: 10
    required: false
```

and handle them in the adapter:

```python
def run(spec):
    swept = spec.get("sweep_parameter") or "none"
    if swept == "none":
        value = transmit(spec)
        return {"axis": None,
                "points": [{"index": 0, "transmissivity": value}],
                "series": {"transmissivity": [value]}}

    start, stop = spec["sweep_start"], spec["sweep_stop"]
    count = int(spec["sweep_points"])
    step = (stop - start) / (count - 1)

    points, values = [], []
    for i in range(count):
        axis_value = start + step * i
        local = dict(spec)
        local[swept] = axis_value
        value = transmit(local)
        points.append({"index": i, swept: axis_value, "transmissivity": value})
        values.append(value)

    return {"axis": {"name": swept, "values": [start + step * i for i in range(count)]},
            "points": points,
            "series": {"transmissivity": values}}
```

You get the sweep bounds checked against the swept parameter's own declared range for free.
Ask for optical depth from 0 to 999 and the call is refused before your code runs.

## 5. Rule out combinations that make no sense

If two parameters interact, say so and say why:

```yaml
combinations:
  - when: {optical_depth: [0.0]}
    allow: {angle_deg: [0.0]}
    reason: >-
      With no layer there is nothing for the path length to lengthen, so the angle has no
      effect and a non-zero value would be misleading.
```

The `reason` is not a comment. It is handed to the agent verbatim when the call is refused,
and it is what stops the agent from simply trying again with a different wrong value. Write
it as a sentence you would say to a colleague.

## 6. Register it

Pick whichever fits:

```bash
# a directory on disk, nothing to package
export PHYSEARTH_MODEL_PATH=/path/to/my_model
```

```toml
# from your own installed package
[project.entry-points."physearth.models"]
my_model = "my_package:model_dir"
```

```
# or contribute it, by dropping the folder into
backend/physearth/models/bundled/
```

Start the app and it is there:

```
registered: ['my_model', 'smrt', 'tau_omega', 'water_cloud']
```

## What you got

You wrote a card and a function. Without writing anything else, your model now:

- appears in the agent's capability table with its parameters, units and ranges;
- refuses out-of-range and illegal calls with your wording, before your code runs;
- has its output checked against your declared bounds after every call;
- shows up in the run trace, refusals included;
- can be cited in an answer as `[model:my_model@0.1.0]`, which the system verifies against
  the runs actually performed.

If a card is broken, that model alone is rejected and the reason is listed under "Registered
models" in the interface. The rest of the application starts normally.

A finished example is in `examples/toy_model/`.

## Licence

Apache-2.0. Third-party components keep their own licences; see `NOTICE`.
