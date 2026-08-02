# Registering a model

A model is a directory with two files.

```
my_model/
  model_card.yaml
  adapter.py
```

Nothing else is required, and you never import PhysEarth. The card declares what your model
accepts and returns; the adapter runs it. Everything the system does for the bundled models
it will also do for yours: parameter validation against your declared ranges, rejection of
illegal parameter combinations with the reason you wrote, automatic quality control of the
result against your declared output bounds, and a visible entry in the run trace.

## The card

```yaml
name: my_model                 # unique registry key
version: "0.1.0"
tier: demo                     # demo runs here; local is registered but not run
entrypoint: adapter:run        # module:function inside this directory
license: Apache-2.0
citation: How to cite the model.
description: One paragraph. The agent reads this to decide whether to use you.

parameters:
  optical_depth:
    type: number               # number, integer, string, boolean
    unit: none
    description: Shown to the agent, so write it for a reader who does not know your model.
    minimum: 0.0               # required for number and integer
    maximum: 20.0
    default: 1.0
    required: false            # defaults to true

combinations:                  # optional
  - when: {solver: [fast]}
    allow: {microstructure: [spheres]}
    reason: The fast solver is only derived for spheres.

outputs:
  transmissivity:
    unit: none
    description: Fraction of energy transmitted.
    valid_min: 0.0             # used by quality control
    valid_max: 1.0

resource_profile:
  typical_call_seconds: 0.0001
  needs_gpu: false
  needs_external_data: false
```

Two rules are enforced when the card is loaded, and a card that breaks them is refused rather
than half-trusted:

- every numeric parameter must declare `minimum` and `maximum`, because a missing range would
  make the physical domain check pass everything silently;
- every bound must actually be a number. In YAML an exponent needs an explicit sign, so write
  `1.0e+9`, not `1.0e9`, or it loads as text.

Each entry in `combinations` must carry a `reason`. The reason is what the agent is told when
its call is rejected, so write it as an explanation, not as an error code.

## The adapter

```python
def run(spec):
    ...
    return {
        "axis": {"name": "optical_depth", "values": [...]},   # or None for a single point
        "points": [{"index": 0, "optical_depth": 1.0, "transmissivity": 0.16}],
        "series": {"transmissivity": [0.16]},
    }
```

`spec` arrives fully resolved: defaults filled in, types coerced, ranges and combinations
already checked. You do not need to validate anything. Keys in `series` must match the names
you declared under `outputs`.

## Making it visible

Three ways, in increasing permanence:

```bash
# 1. point at a directory
export PHYSEARTH_MODEL_PATH=/path/to/my_model

# 2. ship it in a package, declaring an entry point that returns the directory
[project.entry-points."physearth.models"]
my_model = "my_package:model_dir"

# 3. contribute it to physearth/models/bundled/
```

Check it before you rely on it:

```bash
python -m physearth.models.check /path/to/my_model
```

A working example lives in `examples/toy_model/`.
