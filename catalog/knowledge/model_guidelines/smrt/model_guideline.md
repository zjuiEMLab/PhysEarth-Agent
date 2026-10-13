# SMRT model instruction

Use the registered SMRT declaration as the authority for parameter names, units, ranges, legal
theory/microstructure combinations, and output columns.  This note explains how to interpret
those declarations; it is not a replacement for the model card or a paper protocol.

`output=coefficients` answers a medium/scattering-property question and returns electromagnetic
properties such as `ks_per_m` and `ka_per_m`.  `output=tb` answers a passive sensor question and
uses the DORT radiative-transfer solver.  `output=sigma` answers an active backscatter question.
Do not compare these output families as though they were the same observable.

The electromagnetic theory and microstructure representation are separate controls.  A comparison
must hold frequency, density, temperature, layer thickness, particle/correlation scale, and any
other inherited defaults fixed unless that quantity is the declared independent variable.  The
registered combination rules determine which pairs are executable; an unavailable paper model is
not an executable substitute.

`independent_sphere`, `sticky_hard_spheres`, and `non_sticky_hard_spheres` are sphere-based
representations.  The non-sticky option is SMRT's explicit non-sticky limit, while sticky runs
must state the stickiness value.  `exponential` is a correlation-function representation and has
different parameter semantics.  Do not rename one representation as another to make a run pass
validation.

Report model outputs with their declared units and distinguish computed values from paper-reported
values.  A model result remains a single-layer idealisation unless the selected model instruction
and the user protocol say otherwise.

## Ground, wetness and snow water equivalent

The snow lies on a rough frozen soil by default (`substrate=rough_soil`): the Wegmüller and
Mätzler soil for emission and the IEM soil (Fung et al. 1992) for backscatter, as SMRT's own
examples use, with permittivity 4 - 0.5j. The soil is at the snow temperature unless
`soil_temperature_k` is given; in a sweep of `temperature_k` it therefore warms with the snow,
so set `soil_temperature_k` to hold the ground fixed and say which you did. `substrate=flat_soil`
is a mirror-flat soil from the 89 to 243 GHz tundra studies: below about 90 GHz it
over-polarises the ground, so H-pol brightness temperature can rise with depth. `substrate=none`
is snow over nothing: use it only for a layer thick enough to stand in for a semi-infinite
snowpack. Backscatter on the rough soil is valid up to 17.2 GHz (the IEM soil model's limit):
choose 17.2 GHz or lower for `output=sigma`, while brightness temperature can stay at 37 GHz. Every `tb` and `sigma` run also returns `swe_mm`, the layer's snow water equivalent:
sweep `thickness_m` at a fixed density and plot against `swe_mm`.

Wetness is `volumetric_liquid_water`, a volume fraction (0.01 is 1 %). Any wet run is at
`temperature_k=273.15`; the card refuses anything else. The signal changes between 0 and about
0.005; 1 %, 2 % and 5 % all draw the same flat line. A comparison across wetness needs a dry
case, values inside that transition, and one clearly wet case. Do not stand in another
parameter, such as density, for wetness.

What to expect, each confirmed by probes of this adapter (`physics.expectations` in the card):
brightness temperature, V and H, falls as SWE grows for dry snow on ground at 19 GHz and above
unless the grains are very fine; dry-snow backscatter rises with SWE; wet snow sits near 272 K
and stops depending on depth; wetness raises brightness temperature and lowers backscatter;
brightness temperature rises with snow temperature. Any run where brightness temperature rises
with SWE is flagged with a WARNING in its quality control. Do not report such a curve without
saying which physical case explains it (the warning lists them) or changing the configuration.
