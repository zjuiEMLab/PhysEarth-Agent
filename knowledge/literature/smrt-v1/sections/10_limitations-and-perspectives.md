# Limitations and perspectives

SMRT version 1.0 bears some limitations that are inherent to the architecture
as discussed in Sect. 1; others are related to the
current set of available modules and their approximation as shown in
Table 1. Some limitations could be simply overcome by
implementing new modules or formulations. This section focuses on the latter
category.

The scope of SMRT is currently limited to a snowpack over a surface (called
substrate), which is a common approach for some applications such as soils,
but may be inappropriate for other snow-covered environments in which
volume scattering, layering within the substrate, or temperature heterogeneity
may be important. For instance snow-covered sea ice or frozen lakes need to
account for bubbly and salty ice with a nonuniform temperature profile.
While the generic plane-parallel layered structure in SMRT and the DORT
solver are readily suited for this kind of modeling, the electromagnetic
behavior of these materials needs to be additionally implemented, which is
technically easy due to the modular architecture. Bubbly ice
(Dupont et al., 2013) has been modeled with DMRT for fresh ice. This should
also work for salted ice unless the scattering of brine becomes significant.

Considering soil as a volume scattering medium or accounting for
inhomogeneous temperatures or wetness can be treated within DMRT and
layered radiative transfer (Lu et al., 2009). Though promising, this
approach has still been hardly explored. Likewise, the atmosphere could
benefit from a multilayer representation as employed in specific,
atmospheric radiative transfer models (Eriksson et al., 2011).
Implementing atmospheric layers in SMRT would be of interest to deal
with cases of strong surface–atmosphere coupling as observed around
60 GHz near the oxygen absorption band. A simple non-scattering bulk
atmosphere can be prescribed in the current SMRT version; however this
requires the down- and upwelling brightness temperatures and
transmittance to be calculated externally.

Accurate simulations of snow on the ground in active mode would
require more advanced surface scattering models than implemented in the current
version. SMRT inherits from the soil modules implemented in DMRT-ML
and previously in HUT and MEMLS, which were tailored to the passive
mode. These modules mainly compute a specular reflection while a
faithful backscatter computation is required for the active
mode. DMRT-QMS includes an advanced rough surface treatment from
independent numerical simulations (Zhou et al., 2004). In SMRT soil
backscatter is prescribed in the current version, but an
implementation of a numerical approximate method for rough soil
surfaces such as the advanced integral equation method
(Chen et al., 2003) is foreseen in the future. Likewise, taking the
roughness of the snow surface and internal snow interfaces into
account is another interesting perspective
(Liang et al., 2009).

A strong assumption in SMRT version 1.0 is the isotropy of the
microstructure. Some types of snow have been shown to be highly anisotropic,
especially due to differences between the vertical and horizontal directions
(Löwe et al., 2013). This results in polarization effects in the volume
(Leinss et al., 2016). Implementing anisotropic microstructures is possible in
the existing architecture but requires significant developments at several
locations, namely (i) the effective permittivity tensor (ii) scattering and
absorption coefficients and phase function and (iii) solution of the
radiative transfer equation taking into account the ordinary and
extraordinary streams. Another, related assumption in the current version is
the isotropy at the snowpack scale. Accounting for anisotropically reflecting
interfaces would only require an improvement of the radiative transfer solver
and the implementation of anisotropic surface reflections. However, to include
all emergent effects (such as multiple scattering between surface and volume)
a full 3-D model is required, which is not compatible with the SMRT
architecture.

Some limitations of SMRT are inherent to the radiative transfer equation,
which does not keep track of the absolute phase. This obviously prevents
interferometric calculations and may be restrictive when the layer thickness
is smaller than the wavelength of the microwaves, that is, at low frequencies
(Tan et al., 2015a; Leduc-Leballeur et al., 2015) or in the
case of thin ice lenses in the snowpack (Mätzler and Wegmüller, 1987). In some cases,
ad hoc corrections of the radiative transfer solution can be implemented. For
instance MEMLS (Wiesmann and Mätzler, 1999) computes the effect of interferences
between the interfaces of
sub-wavelength layers for short phase differences at the condition that
scattering is negligible and these thin layers are surrounded by thick
layers. This correction is suitable for isolated ice lenses
(Montpetit et al., 2013) but not sufficient for low frequencies. Another
important case concerns the active mode in the backscatter direction – which
is the most common configuration for radars. In such a configuration, some of
the many possible trajectories of radiation propagation are paired, cyclical
double bounces involving reflections between one of the interfaces (soil or
air–snow surface) and the volume. Theses pairs constructively interfere with
each other, according to wave theory. As a result, the backscatter for these
bounces is increased by 3 dB compared to what is predicted by the incoherent
radiative transfer theory. This phenomenon called backscattering enhancement
has recently been taken into account by developing a specific solver of the
radiative transfer equation able to distinguish the noncyclical and cyclical
trajectories, and to apply a correction of 3 dB to the latter group
(Tan et al., 2015b).

Another limitation concerns simulations of altimetric signal or
frequency-modulated continuous-wave radar. The radiative transfer
equation solver available in SMRT version 1.0 considers the stationary
radiative transfer equation (Eq. 1), which is insufficient to
simulate altimetry waveform or time-resolved radar echo. However, the SMRT
architecture could accommodate such an enhancement with little change; only
an adequate solver needs to be added (Lacroix et al., 2008).

Finally we acknowledge that the Python implementation of SMRT bears
some peculiarities. By extensively using Python dynamic capabilities,
the model computation is probably less efficient than specialized
code, even though numerically critical code is delegated to optimized
libraries through SciPy. Because of Python, the model may be
inadequate for high-performance computation. In this case SMRT may still be
useful for prototyping and determining the optimal subset of
formulations that could then be implemented in compiled language since
a numerical reference greatly helps to achieve such an optimization
step. Moreover, it is worth noting that the Python ecosystem for high-performance computing is fast improving and that SMRT code may be
parallelized in the future.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
