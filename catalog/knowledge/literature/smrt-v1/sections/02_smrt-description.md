# SMRT description

SMRT was designed to be easy to use and computationally efficient and to allow
exploration of the various approximations or formulations available for
computing snow scattering and emission in the microwave domain. Even though
the goal was to maximize flexibility and versatility, some specific choices
and compromises were nevertheless necessary: (i) SMRT is a radiative transfer
model. This implies that interlayer interferences and coherent effects are
neglected. It is not suitable for interferometric computation. (ii) SMRT
considers media composed of plane-parallel, horizontally infinite,
homogeneous layers and is therefore not suitable to compute
3-D effects. (iii) The current version is limited to isotropic
media at the microstructure scale as well as at the scale of the snowpack.
This means that microstructural anisotropy of snow is neglected
(Leinss et al., 2016) and that structures formed by wind (sastrugi, dunes)
are not taken into account yet. Even though SMRT is primarily designed for
microwaves and snow, restrictions on spectral range and materials are not
made explicit to allow for future extensions to the optical range and other
random media (sea ice, layered soil, atmosphere). As a consequence of these
decisions on design, the model is therefore composed of a fixed architecture,
described in Sect. 1, and many switchable formulations
described in Sect. 2 and 3 and in
Appendix 1.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
