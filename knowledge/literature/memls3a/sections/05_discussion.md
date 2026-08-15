# Discussion

As shown in Sect. 4, MEMLS3&a simulations
were in reasonable agreement with SnowScat observations. To achieve this
agreement, however, several parameters were chosen to match model and
observation. This was necessary, since the active part contains, in contrast
to the passive part, empirical parameters (ss0,q and m)
which could not be measured. Likewise, the ground parameters s0 and
rmsg are subject to uncertainties.

The specular part of the snow–ground reflectivity ss0 was
chosen to be proportional to s0 and the same factor of 0.75 could be
applied for all frequencies and polarizations to convert s0 into
ss0. With ss0=0.75s0, the main part of the
snow–ground reflectivity is specular. This requires the ground to be smooth
and the overlaying snow layer to be transparent. The vegetation is subject to
very low temperatures and a steady temperature gradient, which forces the
water of the soft vegetation (lichen, mosses, shrubs (myrtillus species);
Fig. 14) to move upwards into the snow. Given the height of the
vegetation of less than 10 cm, it seems reasonable to assume that the
vegetation dries out during winter and can be treated as fully transparent
for the present microwave frequencies. This allows the soil interface to act
as specular reflector, which is then accounted for by ss0 in
the model. Though being reasonable, a sound justification of this line of
argumentation requires further investigations.

The cross-polarization in MEMLS3&a is solely determined empirically via the parameter q. This
pragmatic approach was chosen since the physical origin of cross-polarization in snow is still
the subject of ongoing research. In the DMRT based approach (Tsang et al., 2007)Tsang, Pan, Liang, Li, Cline, and Tan), cross-polarization
emerges from non-spherical shapes of aggregated sphere clusters. A different route to
cross-polarization can be taken via the discrete dipole approximation (DDA),
e.g., from (Von Lerber et al., 2006)Von Lerber, Sarvas, and Pulliainen) or (Xu et al., 2012), which principally accounts for multiple reflections and
polarizations inside a given snow volume. DDA requires the full three-dimensional description of the
microstructure, which can be provided by μCT. A comparison to such a model could further
elucidate the justification and the value of the parameter q.

Another parameter chosen empirically is the mean slope of surface undulations
m. In principle, this parameter could be obtained from the analysis of the
surface height, similar to what has been done in (Löwe et al., 2007)Löwe, Egli, Bartlett, Guala, and Manes) and
(Manes et al., 2008)Manes, Guala, Löwe, Bartlett, Egli, and Lehning) for fresh snow. In a simple reasoning, the mean squared
slope m can be expressed as the ratio between the standard deviation of the
surface height and the lateral correlation length of the height correlation
function. According to (Manes et al., 2008)Manes, Guala, Löwe, Bartlett, Egli, and Lehning) m would then take a value of 0.14
for fresh snow which is in the same order of magnitude as applied in our
simulations (m=0.1). This small-scale roughness of the snow surface is
not taken into account by the model, where only slight surface undulations
are allowed.

The individual magnitudes of the specular and diffuse contributions are shown
in Fig. 15. Towards higher frequencies, the diffuse component
increases and outweighs the specular reflectivity from 12.5 GHz for v-pol
and from 14.5 GHz for h-pol. Note that the magnitude of the specular
component also depends on the undulation of the surface and therefore on the
value of m. However, a pronounced impact of m is limited to small incidence
angles (Fig. 12 and Sect. 2) for reasonable
values of m (m≈0.1).

In contrast to MEMLS3&a, MEMLS does not require free empirical parameters.
In this regard, we attribute the fact that MEMLS3&a matches the SnowScat
observation better than MEMLS the SodRad observations to the additional free
parameters in MEMLS3&a, foremost ss0 and q. However,
for the passive simulations, parameters also had to be chosen without direct
experimental justification, namely s0 and rmsg, which
determine the contribution of the snow–ground interface. This contribution is
dominant and critical in our frequency range, as dry snowpacks thinner than
∼1 m are highly transparent. Unfortunately, the knowledge about
the scattering at the ground surface is limited. Therefore, the snow–ground
reflectivity s0 was modeled using the model of (Wegmüller and Mätzler, 1999). This
model is an empirical parametrization of the Fresnel formula depending on the
standard deviation of the soil surface height rmsg and the soil
permittivities. For the soil permittivities, (Hallikainen et al., 1985)Hallikainen, Ulaby, Dobson, El-Rayes, and Wu) provide
experimental data and (Mironov et al., 2010)Mironov, DeRoo, and Savin) an empirical model based on
experimental data, but dielectric models for the permittivities of frozen
soils are still under development. For rmsg of the soil below
the snowpack no measurements were available. In addition, the model of
(Wegmüller and Mätzler, 1999) does not account for vegetation, which is in our case
consistent with the argument on transparency given above. We note that
estimating the snow–ground reflectivity is critical for all microwave models,
which was also concluded from recent experiments
(Roy et al., 2013)Roy, Picard, Royer, Montpetit, Dupont, and Langlois; Montpetit et al., 2013)Montpetit, Royer, Roy, Langlois, and Derksen). However, at 10 GHz, the frequency
which is most influenced by the soil; MEMLS and SodRad were in good
agreement.

In contrast, the mismatch between model and measurements was largest at
36 GHz and is most sensitive to details of the snow
microstructure. MEMLS assumes an exponential fit of the density correlation
function of the snow microstructure. The exponential fit is a reasonable
starting point but small deviations can have a large influence on
scattering. As detailed by (Löwe et al., 2011)Löwe, Spiegel, and Schneebeli), the correlation function of snow
can take different shapes and its representation by means of a single
correlation length might be inappropriate. Instead the Teubner–Strey form,
a two-scale form for bicontinuous media might be more appropriate. The
inclusion of other types of correlation functions into MEMLS is possible by
adapting the calculation of the scattering coefficient. We thus believe that
the present model provides a suitable test case to investigate the impact of
more sophisticated representations of the snow microstructure.

We further tried to assess the influence of the spatial variability of the
snowpack. The standard deviation obtained from the 15 MEMLS runs is
8 K at 36.5 GHz, h- and v-pol, implying a non-negligible
influence of the location of the in situ snow measurements on the modeled
brightness temperatures.

We also found that the higher values measured by SodRad throughout the whole
frequency range at h-pol for an azimuth angle of 140∘ indicate an
effect of the surrounding environment, such as trees, which were closer to
the field of view at this azimuth angle. The spatial variability of the
snowpack together with the influence of the environment is potentially able
to bias simulated and measured brightness temperatures.

The degree of complexity of existing models simulating microwave
backscattering from snow range from single-layer approaches (Rott et al., 2010)Rott, Yueh, Cline, and Duguay)
to numerical solutions of Maxwell's equations (Xu et al., 2012; Ding et al., 2010)Ding, Xu, and Tsang). In
this context, we propose MEMLS3&a as a model of intermediate complexity. In
contrast to the HUT model (Pulliainen et al., 1999)Pulliainen, Grandell, and Hallikainen; Lemmetyinen et al., 2010)Lemmetyinen, Pulliainen, Rees, Kontu, and Derksen), which has
comparable complexity, MEMLS avoids traditional grain size as input
parameter, which is prone to uncertainties in the visual estimation method
(Painter et al., 2007)Painter, Molotch, Cassidy, Flanner, and Steffen). The advantage of MEMLS3&a (as well as MEMLS) is the
correlation length as microstructural quantity, which can be obtained from
objective measurements without conversion and, given the SMP retrieval
method, with high efficiency in the field.

Presently, models differ not only in the representation of snow
microstructure but also in the solution of the radiative transfer or the
type of interfaces between the layers, which makes it difficult to attribute
the discrepancies in model performance to a particular part of the model.
A comparison by (Tedesco and Kim, 2006) of at least the passive models showed
that no model was able to reproduce all of the investigated microwave
observations. For a detailed model assessment in view of future developments,
various effects (spatial variability, snow microstructure, soil) must be
isolated. A promising way is by using measurements of specifically prepared snow
slabs, as already presented by (Wiesmann et al., 1998)Wiesmann, Mätzler, and Weise). Together with complete
3-D microstructural information, these types of idealized experiments will
allow us to minimize spatial variability, avoid the influence of the ground and
compare different microstructural concepts for scattering coefficients.
Together with available multi-layer models like MEMLS3&a, DMRT-ML
(Picard et al., 2013)Picard, Brucker, Roy, Dupont, Fily, Royer, and Harlow) or the DMRT-QMS package (Chang et al., 2014)Chang, Tan, Lemmetyinen, Tsang, Xu, and Yueh), this will
clarify our understanding of the processes involved in microwave emission and
scattering of snow.

---

M. Proksch, C. Mätzler, A. Wiesmann, J. Lemmetyinen, M. Schwank, H. Löwe, M. Schneebeli (2015). MEMLS3&a: Microwave Emission Model of Layered Snowpacks adapted to include backscattering. Geoscientific Model Development 8, 2611-2626. https://doi.org/10.5194/gmd-8-2611-2015. Licensed under CC-BY-3.0.
