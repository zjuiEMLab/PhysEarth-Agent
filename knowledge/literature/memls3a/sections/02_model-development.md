# Model development

In MEMLS the snow cover is considered as a stack of n horizontal
layers with planar boundaries at the snow surface and between snow layers.
Each layer is characterized by snow parameters (layer thickness, correlation
length, density, liquid water content and temperature) that determine the
layer-radiative properties. Also the salinity can be taken into account
layerwise. The snow–ground interface is characterized by a reflectivity
s0. A sandwich model is used to combine internal scattering and
reflections at the interfaces. Internal volume scattering is accounted by
a two-flux model (up- and downwelling streams) derived from a six-flux
approach (fluxes in all space directions). The absorption and scattering
coefficients are functions of the six-flux parameters. The absorption
coefficient can be obtained from density, frequency, temperature and
salinity; the scattering coefficient depends on the correlation length,
density and frequency. For a detailed description of MEMLS we refer to the
technical documentation (Mätzler and Wiesmann, 2012). In the following, we focus on
the backscatter model by considering the total backscatter as a sum of
specular and diffuse components. Since the total reflectivity of a snowpack
is related to its emissivity, it can be derived from passive observations
alone. Thereby, active and passive observables can be appropriately combined
to obtain a prediction for the radar backscatter.

## Link between active and passive observables

At any given frequency and polarization of electromagnetic radiation
with incident direction (μn,ϕn) defined by zenith angle
θn (where μn=cos⁡θn) and azimuth angle ϕn
at the snow–air interface (cf. Fig. 1), the reflectivity
r of the surface is related to its emissivity e (in the reciprocal
direction) by Kirchhoff's law:
r=1-e.
For a more general description of Kirchhoff's law, see (Mätzler and Melsheimer, 2006).
Equation (1) relates the emissivity, the key quantity of passive
microwaves, to the reflectivity, a quantity linked to scattering. It is this
relation that allows us to link active and passive microwave remote sensing.
The reflectivity represents the fraction of the incident radiation that is
scattered in the hemisphere above the surface. If the scattered radiation is
diffuse (Lambertian reflectance) we can estimate the fraction in the
backscatter direction. Furthermore, with information about the statistics of
surface slopes, we can determine the contribution of backscatter arising from
specular reflection at surface facets that are normal to the incident
direction. Therefore, we will represent the total reflectivity as a sum of
diffuse and specular components. The reflectivity can be represented as an
integral over scattering directions in the upper hemisphere of the bistatic
scattering function S:
r=14πμn∫2πS(μn,ϕn,μ,ϕ)dΩ=12μn∫01S(μn,μ).dμ
Here, dΩ=dμdϕ is the infinitesimal solid-angle element
in the scattered direction. The azimuth integration extends from 0 to
2π, and the last expression is valid for azimuth-independent
functions. The function S describes the scattering from incident
direction (μn,ϕn) to the scattering direction
(μ,ϕ). Thus, backscattering is determined by
S(μn,ϕn,μn,ϕn). (Chandrasekhar, 1960) introduced
the S function in his monograph on radiative transfer. He showed
that S is reciprocal:
S(μn,ϕn,μ,ϕ)=S(μ,ϕ,μn,ϕn).
Furthermore, S is identical to the bistatic scattering cross section
σ0 introduced by (Ulaby et al., 1981)Ulaby, Moore, and Fung), see their Eqs. (4.186)
and (4.187), more exactly to the sum of the like- and cross-polarization
terms, S=σlike0(θn,ϕn,θ,ϕ)+σcross0(θn,ϕn,θ,ϕ). It is also related to
Peake's (1959) function γ=S/μn; i.e., the 1/μn factor of
Eq. (2) is included inside this function. For completeness, we note
that S is related to but differs from other definitions: the reflection
function R used for instance by (Kokhanovsky, 2001) differs by a factor
π from the bidirectional reflection distribution function (BRDF) used in
optical remote sensing (Kasten and Raschke, 1974), and all quantities are related by

S(μn,ϕn,μ,ϕ)=μnγ(μn,ϕn,μ,ϕ)=4μnμR(μn,ϕn,μ,ϕ)=4πμnμBRDF(μn,ϕn,μ,ϕ).

The S function can be highly complex. However, for diffuse scattering, some
empirical functions are provided in the literature, see e.g.,
(Mätzler and Rosenkranz, 2007), the simplest one for Lambert scattering:
Sd=S0μnμ,
where the subscript d indicates diffuse scattering, and S0 is a constant.
By integration according to Eq. (2), we find that the diffuse
reflectivity rd is independent of the incidence angle, namely
rd=S0/4=R, and thus equal to Kokhanovsky's R. The
normalized backscattering cross section is given by σd0=Sd(μ=μd), which can be expressed by
rd via
σd0=4rdμn2.
Indeed, Lambertian behavior was found by the investigation of the
HPACK model for snow by (Mätzler, 2000). It is an extension of an
earlier one-layer, active–passive model of (Tsang et al., 1982)Tsang, Blanchard, Newton, and Kong) to
include multiple-isotropic scattering in the snow as well as
refraction and reflection at the snow surface. The combined effect led
to Lambert scattering for the diffuse component.

Unspecified in Eq. (6) is the separation of σd0
in its like- and cross-polarized components. For isotropic scatterers
considered in HPACK, the first-order backscattering is like-polarized, and
cross-polarization requires higher-order scattering. However, the structure
of natural snow is highly complex, meaning that cross-polarization occurs for
all scattering orders. Therefore, we introduce an empirical relationship with
a splitting parameter q which defines the cross-polarized part, whereas
(1-q) represents the like-polarized fraction, via
σd,pp′0=(1-q)σd,v0,p=p′=v(1-q)σd,h0,p=p′=hqσd,v0+σd,h0/2,p=v,p′=horp=h,p′=v.
Here we took into account that rd and thus
σd0 are slightly different for horizontal (h) and
vertical (v) polarization (h- and v-pol).
Now, Eq. (6) can be rewritten using the
polarization terms for incident waves at vertical and horizontal
polarization, respectively:

σd,v0=σd,vv0+σd,hv0=4rd,vμn2,σd,h0=σd,hh0+σd,vh0=4rd,hμn2.

An additional contribution to backscattering results from specular reflection
as shown in Fig. 1. By considering only slight undulations, specular
backscattering is limited to near-vertical incidence. For a Gaussian
distribution of surface slopes, the backscattering coefficient of the
specular term can be written as
σs0=rs,0exp⁡-tan⁡2θn/(2m2)2m2μn4,
where m2 is the mean-square slope, and rs,0 refers to
rs at normal incidence (Fig. 1, right). This equation
corresponds to the geometrical-optics solution for undulating surfaces, see
(Ulaby et al., 1982)Ulaby, Moore, and Fung), and (Kong, 1986).
Here we generalize it from surface scattering to specular terms that fit the
observation geometry (i.e., specular reflectivity for local normal incidence
angle). Furthermore, we note that Eq. (9) describes like-polarized
backscatter. For negligible anisotropy in the local surface plane the same
values are obtained for hh (horizontal) and vv
(vertical) polarization, and the cross-polarization terms are zero.

For both v and h polarization the total reflectivity is the sum of the
diffuse and the specular component:
r=rd+rs.
While Eqs. (6) and (8) are valid for rd,
Eq. (9) applies to rs but taken at normal incidence.
With some additional effort described below, MEMLS provides both
rd and rs and the total backscattering
coefficient as the sum:
σ0=σd0+σs0.

## Determination of r

Apart from the physical temperatures of all snow layers including the ground
temperature, the downwelling sky brightness temperature Tsky
must also be provided as input in MEMLS. The output is the brightness temperature
Tb that is observed as upwelling radiation above the snowpack
Tb=rTsky+(1-r)Teff.
Here Teff is the emission-effective temperature of snow and
ground. The reflectivity r can thus be computed via Tb
(Tb1, Tb2) from two arbitrary and different values
of Tsky (Tsky1, Tsky2), such as 100 and
0 K. The reflectivity then follows from
r=Tb1-Tb2Tsky1-Tsky2.

## Determination of rs

According to Fig. 1 we need the specular reflectivities
rs,v and rs,h at vertical and horizontal polarization
at the observation incidence angle as well as rs,0 at normal
incidence. For brevity, we omit subscripts indicating the polarization and
just write rs instead of rs,v and rs,h.
In many situations rs can be identified by the reflectivity of
the snow surface. This is especially true for wet snow and for snowpacks that
consist of a single layer. However, if an old snowpack is covered by fresh
snow, the dominant specular layer may be the interface between the fresh and
the old snow. Also, ice lenses form dominant reflectors inside the snowpack.
Therefore, MEMLS requires a method that estimates incoherent specular
reflectivities for arbitrary stratifications. This derivation is detailed in
the Appendix. As a result, if all layer interfaces are assumed to be smooth
and the corresponding interface reflectivities sj are determined by
Fresnel's equations, the specular reflectivity Rj resulting from layers
below zj can be expressed in terms of a recurrence relation
Rj=sj+[(1-sj)uj]2Rj-11-uj2sjRj-1,j=1,…,n.
where sj is the interface reflectivity on top of layer j and uj=exp⁡(-γe,jdj/μj-1) is the coherent
transmissivity of layer j (Fig. 2). The extinction
coefficient is denoted by γe,j and dj is the
layer thickness. The specular reflectivity of the entire
snowpack–ground system then is given by
rs=Rn
Equation (14) starts with j=1 at the ground as the lowest
layer contributing to specular reflection. In contrast to the smooth
interfaces assumed between snow layers, the ground is regarded as
a rough surface and its reflectivity is additively decomposed into
a diffuse and a specular part according to s0=ss,0+sd,0. Accordingly, the ground reflectivity R0=ss,0 constitutes the initial condition for the
recurrence relation (14).

## Synopsis of the backscatter model

Finally, we briefly recap how specular and diffuse components from the
previous section are practically reassembled in MEMLS3&a for the computation
of the total backscatter.
The total backscatter σ0 is divided into a specular and diffuse component,
σs0 and σd0, respectively
(cf. Eq. 11).The specular component σs0 is derived from Eq. (9) and arises
from the rough soil surface (via ss,0) and the layer interfaces
and the snow–air interface, both of which are assumed to be slightly undulated.The diffuse component of the backscatter σd0 is derived from the diffuse
component rd of the total reflectivity (Eq. 6), which
requires the calculation of the total reflectivity r (Eq. 13) and
its specular component rs (Eqs. 14, 15).
Thus, the model accounts for multiple scattering at the undulated layer interfaces. The diffuse
scattered radiation is assumed to be Lambertian, which allows estimating the fraction scattered in
the backscatter direction. More complex processes such as coherent backscatter enhancement recently
presented by (Tan et al., 2015)Tan, Chang, Tsang, Lemmetyinen, and Proksch) are currently not considered in MEMLS3&a.

## Primary input parameters

For a simulation run at a given frequency f, polarization p and
observation incidence angle θn, all snow physical parameters described
in Table 1 are required for each snow layer (j=1,2,…,n). From these primary input parameters, secondary parameters are computed as
described in the previous version of MEMLS (Wiesmann and Mätzler, 1999).

---

M. Proksch, C. Mätzler, A. Wiesmann, J. Lemmetyinen, M. Schwank, H. Löwe, M. Schneebeli (2015). MEMLS3&a: Microwave Emission Model of Layered Snowpacks adapted to include backscattering. Geoscientific Model Development 8, 2611-2626. https://doi.org/10.5194/gmd-8-2611-2015. Licensed under CC-BY-3.0.
