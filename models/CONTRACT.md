# The model card contract

Enforced by `backend/physearth/models/contract.py`. Every rule below exists because
breaking it would let a model be validated against one description and executed against
another — which is the failure this whole system is built to prevent.

A card that violates any of these is **rejected**. The model does not appear, and
`registry.rejected()` reports the problems. Nothing is repaired for you.

## Required at the top level

| Field | What it is |
|---|---|
| `name` | the identifier used in `[model:name@version]` markers |
| `version` | the version those markers carry |
| `description` | what the model computes, in one or two sentences |
| `citation` | what to cite. Not optional, including for a toy |
| `license` | the model's licence, not this repository's |
| `tier` | `demo` or `local` |
| `entrypoint` | `module:function`, e.g. `adapter:run` |

`requires_import` is **required for `local`** and **forbidden for `demo`**: it names the
module whose presence decides whether the model can run on a given host.

## Parameters

`parameters` must be a non-empty mapping. Each one declares `type`, `unit` and
`description`.

- `type` is one of `number`, `integer`, `string`, `boolean`.
- **A numeric parameter must declare `minimum` and `maximum`.** Without a range, the
  physical domain check silently passes everything — which is worse than having no check,
  because the run trace will still show that validation ran.
- A `string` parameter may declare `enum`, but not an empty one.

### The YAML exponent trap

Write `1.0e+9`, never `1.0e9`.

YAML 1.1 requires an explicit sign in an exponent. Without it the value loads as the
*string* `"1.0e9"`, the bound is text, and the range check compares a number against a
string and passes everything. The contract rejects non-numeric bounds for exactly this
reason, and the error message names it, because it is invisible on inspection — the card
looks right.

## Outputs

`outputs` must be a non-empty mapping, and **every output must declare a `unit`**. The
unit is what stops two models being differenced when one answers in kelvin and the other
in decibels; the comparison is refused rather than printed.

## Combinations

Optional. Each rule declares which parameter values are legal together:

```yaml
combinations:
  - when: {microstructure: [exponential]}
    allow: {theory: [iba, iba_original]}
    reason: >-
      DMRT has no derivation for an exponential autocorrelation function, so this
      pairing would return a number with no theory behind it.
```

- `when` and `allow` are both required, and each maps a parameter name to a non-empty
  list of values.
- Every parameter named must exist in `parameters`.
- **`reason` is required**, and it is not documentation: it is handed to the agent when
  the call is refused, so it must explain the physics well enough to choose differently.
  A rule the agent cannot understand produces a retry loop against the same wall.

## How a name is matched

The card's `name` is the identifier, exactly as written, and everything downstream uses
it: validation, execution, and the `[model:name@version]` marker.

Names arriving from prose are resolved once, at the edge. A paper writes `SMRT` and the
card says `smrt`; `tau-omega` and `tau_omega` are the same model. `registry.resolve`
ignores **case and non-alphanumeric characters, and nothing else**, so `MEMLS` and
`DMRT-ML` still do not resolve — they are genuinely not registered, and saying so is what
the capability check is for. It is not fuzzy matching: `smrtt` is not `smrt`. Two models
whose names differ only in those characters are ambiguous, and neither resolves.

Once resolved, the registered spelling is what is recorded. `registry.get` stays exact.

## The adapter

```python
def run(spec):
    """spec holds validated parameters. Return a mapping of output name to values."""
```

By the time `run` is called, every parameter is inside its declared range and every
combination rule has passed. The adapter does not re-check, and must not accept anything
the card does not declare.

A `local` model's adapter **must not import its dependency at module level**. Import it
inside `run`.

The registry loads the adapter on every host, including hosts without that package. For a
`local` model it tolerates the failure — the model registers with no callable and reports
as not runnable rather than vanishing — so a module-level import degrades rather than
breaks. It is still wrong: importing the registry would drag in the dependencies of every
registered model, and a model that is merely slow to import makes startup slow for
everyone. `models/bundled/smrt/adapter.py` is the worked example.
