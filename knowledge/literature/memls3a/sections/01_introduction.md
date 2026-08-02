# Introduction

Empirical observations reveal a wide range of different microwave signatures
in active or passive remote sensing over snow covered areas as shown e.g., by
(Mätzler, 1987). The lack of realistic models to understand these
signatures was the motivation for efforts leading to the Microwave Emission
Model of Layered Snowpacks (MEMLS) in the 1990s
(Mätzler, 1996; Wiesmann and Mätzler, 1999). Initially the microwave emission behavior
of single snow layers was investigated by (Weise, 1996) and later by
(Wiesmann, 1997). The measurements led to an empirical approach for the
scattering coefficient of snow in the frequency range 5–100 GHz and
correlation-length range 0.05–0.3 mm (Wiesmann et al., 1998)Wiesmann, Mätzler, and Weise) as well as to
a first version of MEMLS (Wiesmann and Mätzler, 1999). Empirical relations for the
scattering coefficient have also been implemented in the Helsinki University
of Technology (HUT) model developed by (Pulliainen et al., 1999)Pulliainen, Grandell, and Hallikainen) and later adapted
by (Lemmetyinen et al., 2010)Lemmetyinen, Pulliainen, Rees, Kontu, and Derksen). MEMLS was extended to coarse-grained snow for
correlation lengths up to 0.6 mm (Mätzler and Wiesmann, 1999). The snow
microstructure was characterized by an exponential correlation function which
allows computing the scattering coefficient analytically using the improved
Born approximation (IBA) (Mätzler, 1998).

As an advantage of IBA and the characterization of snow in terms of
correlation functions, the most relevant snow input parameters of MEMLS,
correlation length and density, can be measured directly and objectively by
various methods. Other models may require e.g., a conversion of measured
parameters to model-effective ones (Kontu and Pulliainen, 2010; Lemmetyinen et al., 2015)Lemmetyinen, Derksen, Toose, Proksch, Pulliainen, Kontu, Rautiainen, Seppänen, and Hallikainen). The
exponential correlation length could be e.g., obtained by micro-computed
tomography (μCT) (Schneebeli and Sokratov, 2004) from a fit to the reconstructed
three-dimensional microstructure (Löwe et al., 2013)Löwe, Riche, and Schneebeli). Snow density and
correlation length can be also obtained efficiently from field measurements
(Proksch et al., 2015)Proksch, Löwe, and Schneebeli) using high-resolution penetrometry (SnowMicroPen – SMP)
(Schneebeli and Johnson, 1998). Alternatively, optical methods can be used, e.g.,
(Matzl and Schneebeli, 2006; Gallet et al., 2009)Gallet, Domine, Zender, and Picard; Arnaud et al., 2011), to measure the specific surface area
(SSA) and use an empirical relation to compute the exponential correlation
length (Mätzler, 2002). The latter method is appealing since SSA is
commonly available. Accordingly, MEMLS was widely used for various questions
related to passive microwave remote sensing
(Durand et al., 2008)Durand, Kim, and Margulis; Rees et al., 2010)Rees, Lemmetyinen, Derksen, Pulliainen, and English; Toure et al., 2011)Toure, Goïta, Royer, Kim, Durand, Margulis, and Lu; Langlois et al., 2012)Langlois, Royer, Derksen, Montpetit, Dupont, and Goïta; Schwank et al., 2014)Schwank, Rautiainen, Mätzler, Stähli, Lemmetyinen, Pulliainen, Vehviläinen, Kontu, Ikonen, Ménard, Drusch, Wiesmann, and Wegmüller).

In recent years, there was an increasing interest of the snow remote sensing
community in active microwave measurements, which was mainly driven by the
Cold Regions Hydrology High-Resolution Observatory CoReH2O
(Rott et al., 2010)Rott, Yueh, Cline, and Duguay) and related activities. However, single-layer models for the
radar signal as presented in (Rott et al., 2010)Rott, Yueh, Cline, and Duguay) or (Ulaby et al., 1984)Ulaby, Stiles, and Abdelrazik) are mainly
used for efficient operation in retrieval schemes. For the sake of low
complexity, these models are naturally based on strongly simplifying
assumptions, e.g., treating snow as a collection of independent scatterers.
However, scatterers are densely packed in snow and strongly interact with
each other. More realistic models based on dense media radiative transfer
(DMRT) have been developed (Tsang et al., 2007)Tsang, Pan, Liang, Li, Cline, and Tan; Chang et al., 2014)Chang, Tan, Lemmetyinen, Tsang, Xu, and Yueh), including the
possibility of using the numerical solution of Maxwell's equations for the
single-layer scattering coefficients (Ding et al., 2010)Ding, Xu, and Tsang; Xu et al., 2012). The DMRT-based
models however require at least two microstructural input parameters, which
can be presently obtained only by μCT and often require time consuming
casting procedures in the field.

To cope with recent requirements in active microwave remote sensing, while
relying on an established, physical model of intermediate complexity, it is
the aim of the present paper to extend MEMLS and develop a first version of
MEMLS3&a. Thereby, we can build on the description of the microstructure in
terms of the exponential correlation length as a single, objective parameter
which can be derived from in situ field measurements. For the backscattering
model, we shall extend the description of the snowpack in MEMLS to account
for a slightly undulated snow surface as shown in Fig. 1. The
slightly undulated patches should be small enough to leave the emission
largely unaffected but large enough to allow for specular backscattering at
near-vertical incidence.

The paper is organized as follows: in Sect. 2 we present
the development of the model and the calculation of the total backscatter
with its specular and diffuse components. In Sect. 3 the
validation data consisting of active and passive microwave measurements from
Sodankylä, Finland, are described. Section 4 presents
the validation of both MEMLS and MEMLS3&a using the Sodankylä data,
followed by a discussion (Sect. 5) and the conclusions
(Sect. 6). Details about the calculation of the specular
reflectivity are given in the Appendix.

---

M. Proksch, C. Mätzler, A. Wiesmann, J. Lemmetyinen, M. Schwank, H. Löwe, M. Schneebeli (2015). MEMLS3&a: Microwave Emission Model of Layered Snowpacks adapted to include backscattering. Geoscientific Model Development 8, 2611-2626. https://doi.org/10.5194/gmd-8-2611-2015. Licensed under CC-BY-3.0.
