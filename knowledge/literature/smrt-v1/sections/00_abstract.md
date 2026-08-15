# Abstract

The Snow Microwave Radiative Transfer (SMRT) thermal emission and backscatter
model was developed to determine uncertainties in forward modeling through
intercomparison of different model ingredients. The model differs from
established models by the high degree of flexibility in switching between
different electromagnetic theories, representations of snow microstructure,
and other modules involved in various calculation steps. SMRT v1.0 includes
the dense media radiative transfer theory (DMRT), the improved Born
approximation (IBA), and independent Rayleigh scatterers to compute the
intrinsic electromagnetic properties of a snow layer. In the case of IBA,
five different formulations of the autocorrelation function to describe the
snow microstructure characteristics are available, including the sticky hard
sphere model, for which close equivalence between the IBA and DMRT theories has
been shown here. Validation is demonstrated against established theories and
models. SMRT was used to identify that several former studies conducting
simulations with in situ measured snow properties are now comparable and
moreover appear to be quantitatively nearly equivalent. This study also
proves that a third parameter is needed in addition to density and specific
surface area to characterize the microstructure. The paper provides a
comprehensive description of the mathematical basis of SMRT and its numerical
implementation in Python. Modularity supports model extensions foreseen in
future versions comprising other media (e.g., sea ice, frozen lakes),
different scattering theories, rough surface models, or new microstructure
models.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
