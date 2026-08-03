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

An open-source GeoAI agent that runs physical Earth models for microwave remote sensing of
snow, soil and vegetation.

Most GeoAI systems are data-driven. This one runs physics, and its point is not that it can
talk about physics but that it cannot assert physics it did not read or run. A misconfigured
forward model does not crash; it returns numbers that look entirely reasonable and mean
nothing. So the checks live in the system rather than in the prompt:

- parameters are checked against each model's declared physical ranges and legal
  combinations **before** the model runs;
- the result is checked against the declared output bounds **after** it runs;
- every claim in an answer must carry a marker that resolves to a paper section the agent
  actually opened, a model it actually ran, or a dataset it actually queried;
- text that came from outside the system arrives inside a labelled boundary and is treated
  as evidence, never as instruction;
- numeric arrays never enter the model's context. A run returns a handle and a bounded
  preview, and the full result stays in the session store;
- charts are drawn from a declarative specification naming those handles, never from code
  the agent wrote, and a measured series is never drawn like a simulated one.

None of these is a tool the agent may skip. The run trace shows each one, including the
refusals.

## Bundled models

| Model | Medium | Output |
|---|---|---|
| `smrt` | snow and ice | brightness temperature, backscatter |
| `tau_omega` | soil and vegetation | brightness temperature, emissivity |
| `water_cloud` | soil and vegetation | backscatter |

## Bundled literature

Eight open-access Copernicus papers, redistributed under their CC-BY licences, split into 79
citable sections. See `NOTICE` for the per-paper attribution.

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
physearth/models/bundled/
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
