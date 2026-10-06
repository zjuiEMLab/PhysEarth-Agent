# Five readable shapes for a research plan (proposals for review)

**The problem.** The plan the reviewer sees is the plan the agent sends: a list of runs, each with
its own JSON object of 15 to 20 parameters, most of them identical from run to run, and the source of
each value (read from the paper, a default, an assumption) is not on the page. For Figure 3 that is six
copies of the same snowpack with one or two values changed, and the reviewer has to diff them by eye.

**What a reviewer needs to see**
1. Each value once, with where it came from.
2. What differs between runs, and only that.
3. Which values need a human decision.
4. Which figure each run feeds, and what the paper's figure is being compared with.

**One vocabulary for the source of a value.** It maps onto the five classes the system records today
(`paper_explicit`, `paper_inferred`, `user_specified`, `backend_default`, `model_assumption`), with the last
one split by whether the agent can say why.

| Tag | Meaning | Today's class | Needs the reviewer? |
|---|---|---|---|
| `extracted` | Stated in the manuscript text or read off the figure, with the marker | `paper_explicit` | No |
| `derived` | Follows from extracted values, with the reasoning | `paper_inferred` | Glance |
| `user` | Given in the question | `user_specified` | No |
| `default` | Not in the paper; the model card's own default | `backend_default` | Glance |
| `assumed` | Not in the paper, the agent chose it and says why, and a sensitivity run covers it | `model_assumption` with a reason | **Yes** |
| `guessed` | No basis at all; should be rare, and blocks approval until someone decides | `model_assumption` without a reason | **Yes** |

The examples below are the Figure 3 task: six theory and microstructure combinations of SMRT, scattering
coefficient against density, compared with the paper's Figure 3. Values are the ones the corpus supports:
100 µm spheres and the density axis come from the manuscript and the figure, 37 GHz from section 07, and the
rest from the SMRT card.

---

## Proposal 1: Conditions sheet and run matrix

One table of conditions, then a matrix in which a row is a run and a column is only a factor that varies.

```
EXPERIMENT   SMRT 1.5.1 · scattering coefficient against snow density · reproduces Figure 3 (smrt-v1 §3.1.1)

CONDITIONS (the same in every run)
  parameter       value        source      note
  frequency       37 GHz       extracted   "single snowpack-sensor configuration of 37 GHz" [smrt-v1#07]
  sphere radius   100 µm       extracted   "results for 100 µm radius spheres" [smrt-v1#08]
  thickness       1 m          default     card default; the figure does not state a depth
  temperature     265 K        default     card default
  angle           55 deg       default     card default; a scattering coefficient does not depend on it
  stickiness      0.2          default     only used by the two sticky-sphere runs; see decision D1
  solver streams  32           default     numerics, not physics

SWEEP (the x axis of every run)
  density 1 to 100 kg m-3, 30 points            extracted from the figure's axis

RUNS (what differs)
  run   microstructure         theory       feeds
  R1    independent spheres    Rayleigh     Figure A
  R2    independent spheres    IBA          Figure A
  R3    non-sticky hard spheres  DMRT QCA-CP  Figure A
  R4    non-sticky hard spheres  IBA          Figure A
  R5    sticky hard spheres    DMRT QCA-CP  Figure A
  R6    sticky hard spheres    IBA          Figure A

FIGURE A  scattering coefficient (m-1) against density (kg m-3), R1 to R6, six curves
```

*Reads like a methods table. Each value appears once. The cost is that a run is no longer a self-contained
object, so the stored plan needs a base block and per-run overrides.*

---

## Proposal 2: Methods paragraph with inline badges

A short paragraph a reader can approve without opening a table, with the source on every number.

```
We will run SMRT 1.5.1 on a 1 m snowpack [default] at 265 K [default], observed at 37 GHz [extracted §07]
and 55° [default], with 100 µm spheres [extracted §08]. Density is swept from 1 to 100 kg m-3 in 30 steps
[extracted, Figure 3 axis]. Six runs cross three microstructures (independent spheres, non-sticky hard
spheres, sticky hard spheres [extracted, Figure 3 legend]) with the two theories the paper pairs with
each (Rayleigh or DMRT QCA-CP, and IBA). The two sticky-sphere runs also need a stickiness, which the
paper does not state; we use the card's 0.2 [default] and add a sensitivity run at 0.5 [assumed: the value
the paper uses elsewhere, Figure 4].

Output: one chart, scattering coefficient against density, six curves, compared with Figure 3.
Reproduced if the three families separate in the paper's order and agree near zero density.
```

*Most readable and quickest to approve. Harder to edit a single value, so it works as a view over one of the
other shapes rather than as the stored form.*

---

## Proposal 3: Base conditions plus variants

A hierarchy that mirrors how the experiment is thought about: base, then what each variant changes. Compact
and still machine-readable.

```
plan: fig3-sparse-medium
model: smrt 1.5.1
base:                                   # source
  frequency_ghz: 37                     # extracted [smrt-v1#07]
  radius_m: 1.0e-4                      # extracted [smrt-v1#08]
  thickness_m: 1.0                      # default
  temperature_k: 265                    # default
  angle_deg: 55                         # default
sweep: {density_kg_m3: [1, 100, 30]}   # extracted (figure axis)
variants:
  independent spheres:   {microstructure: independent_sphere,       theory: [rayleigh, iba]}
  non-sticky hard:       {microstructure: non_sticky_hard_spheres,  theory: [dmrt_qcacp_shortrange, iba]}
  sticky hard:           {microstructure: sticky_hard_spheres,      theory: [dmrt_qcacp_shortrange, iba],
                          stickiness: 0.2}   # default, see sensitivity
sensitivity:
  stickiness: [0.1, 0.5]                # assumed: brackets the card default
figures:
  - id: fig3  x: density_kg_m3  y: ks_per_m  draws: all variants x theories
```

*Smallest to store and the easiest to extend: six runs are three lines because a variant can list several
theories. Needs the planner to expand it into runs, which also removes the chance of six copies drifting
apart.*

---

## Proposal 4: Figure-first plan

Starts from the paper's figure and says what each curve is, so the reviewer checks the plan against the
thing being reproduced.

```
TARGET  Figure 3, "Sparse-medium scattering coefficient comparison" (Picard et al. 2018)
  x axis  Density (kg m-3), 0 to 100                         extracted (figure)
  y axis  Scattering coefficient (m-1)                       extracted (figure)

CURVES (legend of the paper's figure  ->  what we run)
  "Independent spheres (Rayleigh)"             -> R1  independent_sphere + rayleigh
  "Independent spheres (IBA)"                  -> R2  independent_sphere + iba
  "Non-sticky hard spheres (DMRT QCA-CP)"      -> R3  non_sticky_hard_spheres + dmrt_qcacp_shortrange
  "Non-sticky hard spheres (IBA)"              -> R4  non_sticky_hard_spheres + iba
  "Sticky hard spheres (DMRT QCA-CP)"          -> R5  sticky_hard_spheres + dmrt_qcacp_shortrange
  "Sticky hard spheres (IBA)"                  -> R6  sticky_hard_spheres + iba

CONDITIONS FOR ALL CURVES
  37 GHz extracted · 100 µm extracted · 1 m default · 265 K default · stickiness 0.2 default (R5, R6)

THE QUESTION  Over what density range do the six converge, and where do they diverge?
  The paper gives about 10 to 20 kg m-3 for the sparse-medium range [smrt-v1#08]; the report must state it.
JUDGED BY  same three families, same order, same shared slope at the origin
```

*Best for reproduction, because curves are traceable to legend entries and the question the report must answer
is on the plan. Specific to a figure target; a free-form experiment has no legend to start from.*

---

## Proposal 5: Review form with decisions first

Orders the plan by what the reviewer must act on, not by how the model is configured.

```
PLAN  Reproduce Figure 3 with SMRT 1.5.1                                   [Approve] [Edit] [Ask why]

SETTLED BY THE PAPER (6)       frequency 37 GHz · radius 100 µm · density axis 1 to 100 · six curves ·
                               three microstructures · two theories
SETTLED BY THE MODEL CARD (5)  thickness 1 m · temperature 265 K · angle 55° · solver 32 streams ·
                               stickiness 0.2          (the card's values; the paper does not say)

NEEDS YOUR DECISION (2)
  D1  Stickiness for the two sticky-sphere runs.
      The paper does not state it for Figure 3. Options:
        (a) card default 0.2            recommended: no invented value
        (b) 0.5, used in the paper's Figure 4   sensitivity run added either way
  D2  Number of density points.
      Not stated. 30 gives a smooth curve in about a minute.  [30] [60] [other]

WILL BE RUN (6 runs, 1 chart)   [expand]
WILL BE COMPARED WITH           Figure 3, qualitatively; report states the 10 to 20 kg m-3 range
```

*Puts the human where they are needed and nothing else in front of them; a plan with no decisions is a
one-click approval. Needs the plan to carry decisions as first-class items (today they are implicit in
`model_assumption` entries).*

---

## How they compare

| | Reads quickly | Source of each value | Repetition removed | Editable | Needs data-model change |
|---|---|---|---|---|---|
| P1 Conditions sheet | good | column | yes | by cell | base + per-run overrides |
| P2 Methods paragraph | best | inline badge | yes | poor | none (a view) |
| P3 Base + variants | good | comment, can be a field | yes | by line | variants expand into runs |
| P4 Figure-first | good for reproduction | per axis and condition | yes | by curve | legend-to-run link (already extracted) |
| P5 Review form | best for approval | grouped by source | yes | by decision | decisions as items |

## Suggested combination

Store **P3** (base, variants, sweep, sensitivity, figures, each value carrying a source tag and a reason for
anything assumed). Render **P5** as the review screen, with **P1** and **P4** one click away as "show
conditions" and "show against the paper". **P2** becomes the opening paragraph of the report, generated from
the same data. That keeps one source of truth and removes the six copies, and the source tag per value is
also what the report's provenance table and the parameter-source check already need.

Changing what the agent sends changes the tool contract and the prompt text, so it invalidates comparison
with existing evaluation records, and it is the natural point to adopt the draft schema in
`research-plan-schema/`.
