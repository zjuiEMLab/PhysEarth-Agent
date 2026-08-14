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
