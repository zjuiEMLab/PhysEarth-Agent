# Conclusions

A new radiative transfer model to simulate emission or radar echo from a
snowpack has been presented in this paper. It is built around the radiative
transfer equation and specifically tailored to model snow but in the future
also other plane-parallel media in the cryosphere. SMRT differs from other
models in its scope in many aspects. SMRT is not a new model with a more
advanced theory, it is rather a repository of established formulations or
widely used model configurations that can be easily interchanged. The
novelty is thus to allow testing of different existing configurations and
exploration of new ones, in particular regarding the microstructure. Using SMRT, we
have highlighted the equivalence between different widely used microstructure
representations (SHS and exponential autocorrelation function) and different
approaches proposed in the literature to run simulations based on in situ
measurements. These results show that to fully describe snow in microwave
models requires at least three main metrics, the density, grain size, and
another parameter characterizing larger-scale structural correlations of the
ice matrix. The fact that these latter properties are presently inaccessible
by other measurements or snowpack modeling contributes to the uncertainties
in microwave simulations, and actually constitutes one of biggest challenges
to solve.

The numerical validation of SMRT has shown the numerical equivalence
with DMRT-ML for the DMRT QCA-CP electromagnetic formulation and has
shown close results with DMRT-QMS under DMRT QCA under the small
scatterer assumption in passive and active modes even though small
differences remain unexplained. Larger differences are observed with
respect to MEMLS, which we attribute to the six-flux method used by
MEMLS to solve the radiative transfer equation. Regarding HUT, SMRT
contains no sufficiently similar configuration to perform a
validation. Nevertheless the language binding to the HUT code has
been included for future comparisons with other configurations. Not
all SMRT configurations and available microstructure representations
have been tested in this study because of the large number of possible
combinations; this is left to future work.

Several limitations of SMRT version 1.0 have been outlined that can be
readily overcome by model extensions which are supported by
modularity. The developed code is highly structured for each step of
the radiative transfer calculation. The model is designed to
facilitate future developments of existing and new formulations
without changing existing code, which should foster community-based
contributions and consolidate SMRT as a repository of the community
knowledge. Future work includes implementation of new features to
account for different media (e.g., sea ice), variants of
electromagnetic models (e.g., DMRT QCA long range) or radiative
transfer solver (e.g., six-flux solver or time-resolved radiative
transfer equation) to increase the scope of applications. In this
paper we focused on two widely used microstructure representations;
SMRT already includes other representations and new ones, such as empirical autocorrelation functions derived from
μCT, could be
included, which opens a new promising way to characterize the
microstructure.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
