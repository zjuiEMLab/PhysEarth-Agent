# Model validation and exploration of the microstructure - On the equivalence of microstructure models

Equipped with the confidence from the previous sections that SMRT is
working as desired, we shall address an actual, open scientific
question. Setting the correct microstructure parameters in microwave
model simulations from in situ observations or snowpack simulations is
notoriously difficult and nearly every study uses a different
approach. To this end we demonstrate how the equivalence between
different approaches can be investigated with SMRT.

The problem originates from the fact that high-level microstructural
characterization in terms of the ACF is commonly not available since complete
profiles of μCT or 2-D thin sections for the entire snowpack are rare.
Instead, density and SSA are commonly measured or
predicted by snowpack models and the initialization of microwave
microstructure models relies on them. The density is unambiguous, the
parameter is manifest for each microstructure model, and no problems should be
expected. In contrast, using SSA is a bit more involved. Theoretically, the
SSA is rigorously related to the slope of the ACF at the origin
(Debye et al., 1957) and therefore parameterizes a basic size of the
constituent scatterers. For microstructures comprising spheres, the SSA
(m2 kg-1) can be directly converted to sphere radius using a=3/(ρiceSSA). For an exponential ACF there is
also the well-known relationship (Debye et al., 1957) lex=4(1-f2)/(ρiceSSA), henceforth termed the Debye
relation. However most microstructure representations involve three
parameters (all except the exponential autocorrelation function) and the
additional parameters must be set as well. Although grain type is often
observed in the field, quantitative relationships with the microstructure
metrics (stickiness or autocorrelation function) have not yet been
established and we do not consider this information here.

These issues have been solved in different ways in literature. For the SHS
microstructure, (Liang et al., 2008) suggest setting the stickiness parameter to
“0.1 because it yields 2.8 for the frequency dependence of the extinction
coefficient which corresponds to the experimental values”
(Hallikainen et al., 1987). These experimental values are the basis of the
extinction formulation in the HUT model (Lemmetyinen et al., 2010). However
setting stickiness to 0.1 is insufficient to strictly determine the power
dependence as it also depends on the grain size and density, i.e., very small
scatterers always show a dependence of a power of 4 (Rayleigh scattering). Another
approach was elaborated in a series of empirical studies
(Brucker et al., 2010; Picard et al., 2014; Roy et al., 2013; Roy et al., 2016; Dupont et al., 2013). It consists
of using non-sticky spheres (i.e., infinite stickiness parameter) and scaling
the radius a computed from SSA by an empirical factor ϕSHS
(called “grain size scaling factor”). This factor is obtained by fitting
model results to microwave observations. To prevent over-fitting, a
single ϕSHS was applied to all SSA measurements and the fit
was performed using microwave observations at several frequencies,
polarizations, and/or angles.

To explore if this latter approach is equivalent to choose an optimal
stickiness value, we use SMRT to find the equivalent microstructure
representations for non-sticky spheres with grain size scaling and sticky
spheres. In the following, equivalent microstructures are interpreted as
microstructures with the same density but different size parameters that produce
the same electromagnetic behavior. This is exemplified by using SMRT IBA and
matching brightness temperatures at V polarization and 55∘ close to
the
Brewster angle to integrate properties of scattering and absorption
coefficients and phase function (Veysoglu and Kong, 1996).
Figure 7 shows the grain size scaling factor
of non-sticky hard spheres as a function of the stickiness value to obtain
this equivalence. For instance ϕSHS=2.1 (Picard et al., 2014) is equivalent to a stickiness value of around 0.13. Higher
values of ϕSHS up to 3.5 were used in the other studies
(Brucker et al., 2010; Roy et al., 2013; Roy et al., 2016; Dupont et al., 2013), corresponding to lower
stickiness values approaching 0.1 as suggested by (Liang et al., 2008). This
confirms that despite using different approaches, these studies converge
towards stickiness values in the range 0.1–0.2, in agreement with
(Löwe and Picard, 2015), who retrieved the stickiness from μCT of snow samples.
However, the relationship between stickiness and grain size factor depends on
density, especially for ϕSHS>2.5
(Fig. 7), and thus the approach of scaling
grain size cannot be strictly equivalent to selecting an optimal stickiness
value.

Though the approach of using a stickiness close to 0.1 seems more physical
compared to an empirical scaling factor, it also has weaknesses. Natural snow
is composed of grains with variable size, which more resembles a collection
of spheres with a distribution of radii (i.e., polydisperse spheres). Such
dispersion is important and generally leads to increased scattering compared
to the medium with monodisperse spheres with the mean radius of the
polydisperse spheres (Tsang and Kong, 1992). However, the analytical treatment
of the ACF for polydisperse SHSs is tedious
(Gazzillo et al., 2006) and choosing the distribution form and its parameters
is an open question. In the case of non-sticky small scatterers,
(Jin, 1994) showed that a polydisperse microstructure can be equivalent
to a monodisperse sphere assembly with an effective radius. This effective
radius was found to be about 1.4 times the radius derived from SSA when a
Rayleigh distribution of sizes was taken (Jin, 1994). This factor would
be slightly different for another distribution but this gives an order of
magnitude of the size distribution effect. Based on this, (Roy et al., 2013)
proposed a pragmatic approach mixing the scaling approach and a fixed
stickiness value. For this, they suggested using ϕSHS=1.4
found by (Jin, 1994) and optimizing the stickiness to obtain good fit
with observations. This proposition has not been evaluated in other studies.

The exponential autocorrelation is a different and attractive solution
because it involves only two parameters that should be fully determined by
density and SSA. However, in practice a “hidden” third parameter must be
introduced to empirically scale the correlation length in the Debye relation
(Mätzler, 2002). Based on comparisons between simulations and
observations, (Mätzler, 2002) suggested a scaling factor of 0.75 in the
Debye relation and justified this adaptation with the necessity of fitting the
exponential function to the real nature of snow, i.e., to the actual ACF of
snow. However, more recently (Montpetit et al., 2013) performed an optimization
of the simulations with MEMLS on a large set of observations on the Arctic
snowpack and found a different coefficient of 1.3. While the origin of this
large discrepancy can be understood from the effect of shape (or equivalently
size dispersity) of the 3-D microstructure (Krol and Löwe, 2016) it remains a
practical problem, similar to the freedom of choosing an appropriate
stickiness value. To this end we explore the connection between the Debye
scaling factor and stickiness, or in other words, the equivalence between the
exponential ACF with scaled correlation length and SHS.
Figure 8 shows the scaling factor
ϕexp of the correlation length in the Debye relationship
required to obtain the same electromagnetic behavior as with SHSs. Each curve is obtained, for a given density, by optimizing
ϕexp to obtain equivalence between exponential and SHS
microstructure. The results show that stickiness higher than 0.2 corresponds
to ϕexp lower than 0.5, with little dependence on density.
This range seems inadequate however for snow considering the values of
stickiness and ϕexp used in the literature. Conversely, the
value of ϕexp=0.75 corresponds to a stickiness of 0.13 at
300 kgm-3 and lower at higher densities. This means that scaling
the correlation length proposed by (Mätzler, 2002) is equivalent to
stickiness values suggested by various studies (Liang et al., 2008; Roy et al., 2013).
In contrast, ϕexp=1.3 found by (Montpetit et al., 2013) is
barely accessible for the scaled correlation length derived from the Debye
relation, indicating the limitations of the exponential ACF for snow.
Moreover, the large dependency on density indicates that a strict equivalence
between SHS and an unscaled exponential model is not possible.

The numerical experiments facilitated by SMRT from this section show
how different studies, which were hitherto not amenable to a comparison
due to apparently different approaches, are now comparable and can be
shown to be nearly equivalent for particular parameter choices.
Moreover the results unambiguously show that density and SSA are not
sufficient to appropriately characterize snow microstructure for
microwave modeling purposes and that the sensitivity to a third
parameter is highly significant. Until alternative measurement
techniques or progress in modeling the microstructure evolution are
available, the initialization of microstructure models relies on
μCT characterization or some empiricism to infer the missing
parameter.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
