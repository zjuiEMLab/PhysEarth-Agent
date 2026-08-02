# Introduction

The number and diversity of spaceborne observations from passive and active
microwave sensors over snow-covered regions has considerably increased over
the last 3 decades. Due to the demand for global monitoring of the cryosphere
and its change, numerous algorithms have been developed to retrieve
geophysical information on snow cover extent (Grody and Basist, 1996; Nghiem and Tsai, 2001),
snow depth, and snow water equivalent on both land
(Josberger and Mognard, 2002; Kelly and Chang, 2003; Derksen et al., 2003) and sea ice
(Comiso et al., 2003; Cavalieri et al., 2012), snow accumulation on ice sheets
(Abdalati and Steffen, 1998; Vaughan et al., 1999; Drinkwater et al., 2001; Winebrenner et al., 2001; Flach et al., 2005; Arthern et al., 2006; Dierking et al., 2012) wet snow
(Zwally, 1977; Shi and Dozier, 1995; Abdalati and Steffen, 1997; Nagler and Rott, 2000; Steffen, 2004; Picard et al., 2007), snow temperature
(Shuman et al., 1995; Schneider and Steig, 2002; Schneider et al., 2004), snow grain size
(Brucker et al., 2010; Picard et al., 2012), and snow density (Schwank et al., 2015; Champollion et al., 2013). Even though many applications still rely on empirical
approaches to relate snowpack properties (e.g., snow water equivalent, SWE)
and measured signals, it is generally accepted that a physical understanding
of the interaction between snow and electromagnetic waves is necessary to
improve the accuracy and overcome inherent difficulties of the retrieval as
an underdetermined problem. The retrieval of snow properties is therefore
often preceded by forward modeling and data assimilation
((Durand and Margulis, 2007); (Picard et al., 2009);
(Takala et al., 2011); (Toure et al., 2011);
(Huang et al., 2012)) to predict the satellite signal from prescribed
snowpack properties that can be either obtained from measurements
(Rosenfeld and Grody, 2000; Brucker et al., 2011a; Rees et al., 2010; Derksen et al., 2012; Derksen et al., 2014; Kontu et al., 2014) or snow models (Flach et al., 2005; Brucker et al., 2011b; Andreadis and Lettenmaier, 2012; Kang and Barros, 2012; Wójcik et al., 2008; Kontu et al., 2017). The actual
modeling challenge lies in the snowpack and the underlying surface (soil,
ice, or water) where the coupling of various ingredients needs to be
understood with sufficient accuracy to build efficient forward models.
Examples comprise scattering by snow microstructure, liquid water, salinity,
ice lenses (Montpetit et al., 2013), coherent effects
(Mätzler and Wegmüller, 1987; Leduc-Leballeur et al., 2015; Tan et al., 2015a), the underlying
surface, and especially its roughness. All of these effects have to be taken
into account by physically based snow microwave models.

Several physically based models have been developed previously mainly for
passive microwave remote sensing, including HUT
(Lemmetyinen et al., 2010), MEMLS (Wiesmann and Mätzler, 1999), DMRT-QMS
(Tsang et al., 2006; Liang et al., 2008), DMRT-ML
(Picard et al., 2013), and other ones based on dense media
radiative transfer (DMRT) (Macelloni et al., 2001; Grody, 2008; Brogioni et al., 2009). In
addition, several models were tailored to low frequencies (i.e., up to a few
gigahertz), such as 2S (Schwank et al., 2014), CMES
(Drusch et al., 2009), WALOMIS (Leduc-Leballeur et al., 2015), and
others (Tan et al., 2015a), triggered by the inception of spaceborne
L-band radiometry (Barre et al., 2008)Barre, Duesmann, and Kerr). Early models for active microwave
observations include only single scattering mechanisms
(Bingham and Drinkwater, 2000; Flach et al., 2005; Longepe et al., 2009; Lacroix et al., 2008), which is
generally sufficient at low frequencies at which scattering is weak compared
to absorption. Only recently have DMRT-QMS and MEMLS been adapted to an
active mode that accounts for multiple scattering (Tsang et al., 2007; Proksch et al., 2015), which is particularly relevant for high-frequency radar
such as SARAL AltiKa (Verron et al., 2015). The combined active–passive
capability in the same model is particularly relevant for dual-mode missions
such as SMAP (Entekhabi et al., 2010). The large number of different models is
a natural consequence of both the diversity of possible approaches at each
stage of the calculation (e.g., effective snow permittivity, scattering,
solution of the radiative transfer equation) and the wide range of
applications (e.g., research versus operational use). This results in a
practical difficulty of choosing the most suitable model for a given
application. In addition, the scope and comparability of predictions of the
same property from different models must be taken with caution, given the
differences in model ingredients.

As a remedy, more and more studies include predictions from different
models (Wójcik et al., 2008; Rees et al., 2010; Roy et al., 2013; Kwon et al., 2015; Sandells et al., 2017) to draw more general conclusions. Other studies
directly focused on the intercomparison of different models
(Tedesco and Kim, 2006; Tse et al., 2007; Tian et al., 2010; Xiong and Shi, 2013; Pan et al., 2016; Löwe and Picard, 2015; Sandells et al., 2017; Royer et al., 2017)
to quantify the differences. Though insightful and necessary, these
efforts did not lead to a reduction of the number of models as none of
the studies considered the entirety of models and none showed a clear
superiority of a single model. The latter fact was partly explained in
(Löwe and Picard, 2015), who demonstrated the near equivalence of two
approaches, namely improved Born approximation (IBA) (Mätzler, 1998) and DMRT
(Tsang et al., 1985; Shih et al., 1997), which were previously considered to be
different. This was achieved by relating the microstructural
foundations of either approach, demonstrating the necessity to compare
different microstructural formulations.

The representation of snow microstructure is critical since it immediately
constrains the choice of formulation to compute the scattering coefficient.
Several empirical formulations of the scattering coefficient have been
developed as a function of traditional grain size (Hallikainen et al., 1987) or
the exponential correlation length (Wiesmann et al., 1998). These formulations
are available in the HUT and MEMLS models. But as for any empirical approach, the
applicability is not guaranteed beyond the limits of calibration. This makes
formulations based on fundamental principles (Maxwell equations) attractive.
For instance, the DMRT theory
(Tsang et al., 1985; Tsang et al., 2000a; Tsang et al., 2007; West et al., 1993; Shih et al., 1997)
is used by several models (e.g., DMRT-ML, DMRT-QMS, (Longepe et al., 2009),
etc.). DMRT represents snow as a collection of ice spheres whose relative
positions are constrained by the sticky hard sphere (SHS) model. Thereby a
stickiness parameter controls the propensity of the spheres to stick to each
other and form clusters with higher scattering power than uniformly dispersed grains.
The stickiness thus has an impact on the validity of approximations when
computing the scattering coefficient. Some DMRT-based models (Macelloni et al., 2001) are restricted to short-range
approximation, which yields a close-form analytical solution for the
scattering and absorption coefficients and the phase function. However, this
approximation requires that both grain (sphere) size and the cluster size
are small compared to the wavelength. While this is reasonable for snow at
frequencies below 19 GHz, it is more problematic at higher frequencies
(Grody, 2008). The long-range approximation relaxes the constraint
on cluster size. To our knowledge, this approximation is not implemented in any
available model. To additionally relax constraints on grain size, the
DMRT-QCA Mie formulation is needed (Tsang et al., 2000a), allowing
simulations at frequencies higher than 37–89 GHz. DMRT-QMS is the
only model to implement this advanced assumption. Despite the attractive
features of the DMRT theory, the representation of snow microstructure by the
SHS model has a major drawback. The stickiness parameter cannot be easily
retrieved from field measurements yet because microstructures of non-sticky
spheres are not directly applicable to natural snow (Brucker et al., 2011b; Picard et al., 2014; Roy et al., 2013). Furthermore, estimating stickiness from
high-resolution microstructure images – as obtained from X-ray
micro-computed tomography (μCT) – appears to be numerically unstable
(Löwe and Picard, 2015), leading to the conclusion that SHS is likely not a good
representation for natural snow.

The IBA developed by (Mätzler, 1998) is an
alternative approach to compute the scattering coefficient. It uses the same
basic electromagnetic principles (Born approximation) as DMRT but it is not
limited to a particular microstructure model. Instead of employing a particle
model and characterizing their relative positions through the
pair-correlation function as in DMRT, IBA uses the relative position of the
ice material directly, which is mathematically captured by the
autocorrelation function (ACF) of the ice indicator function
(Torquato and Haslach, 2002; Löwe and Picard, 2015). In (Mätzler, 1998) the ACF of
non-sticky overlapping spheres was investigated to obtain an analytical form
for the scattering coefficient. However, in MEMLS (Mätzler and Wiesmann, 1999), the
main model using IBA, the choice of ACF is limited to an exponential function
that is characterized by a single parameter, the correlation length. The
correlation length can be obtained from thin 2-D sections of snow samples
(Wang et al., 1998; Wiesmann et al., 1998) or μCT. Even though the measurements are
time-consuming, the estimation is numerically stable. On the one hand, using only
a single parameter to describe the whole microstructure seems advantageous
over SHS which requires two parameters, size, and stickiness. On the other
hand, (Mätzler, 2002) had to propose different relationships between
correlation length and surface area-to-volume ratio to represent different
snow types, demonstrating the ambiguity of the exponential correlation length
and indicating the necessity of describing snow microstructure by at least
two parameters. This is also reflected by more recent attempts that use
level-cut Gaussian random fields as a microstructure model for a bi-continuous
medium as an alternative to the SHS model (Ding et al., 2010; Chang et al., 2014; Chang et al., 2016). This approach is very flexible, but as for SHS, the link of
model parameters to natural snow microstructure and in situ measurement
techniques remains to be understood (Chang et al., 2016). This requires a
comparison of different microstructure models in the context of a chosen
scattering theory. Due to the near equivalence of IBA and DMRT
(Löwe and Picard, 2015) it seems reasonable then to utilize IBA together with a
library of ACFs as candidates to represent natural snow.

All examples mentioned above indicate a clear demand for a modular and
extensible approach that unifies existing knowledge and facilitates efficient
intercomparisons of model ingredients with particular focus on the
representation of microstructure. To this end we developed the Snow Microwave
Radiative Transfer (SMRT) model as a versatile tool to compute
backscattering and brightness temperature (active–passive mode) from
multilayered media, composed of bi-continuous, random microstructures
(typically snow or bubbly ice), overlying a reflective surface (typically
soil, water, or ice). The originality of this new model is the flexibility for
the user to select among various electromagnetic or microstructure
formulations at different stages of the forward modeling problem. SMRT
includes IBA, DMRT, and independent Rayleigh scattering theories to compute
the scattering and absorption coefficients and the phase function. When using
IBA, it is possible to choose between several representations of isotropic
microstructures that are prescribed by analytical forms of the ACF. This is
complemented by several soil model implementations and permittivity
formulations. Additionally, language bindings are implemented to facilitate a
direct comparison with widely used models (DMRT-QMS, MEMLS, and HUT) using
their original code. In short, SMRT is designed to enable easy and rigorous
intercomparison and exploration of electromagnetic theories, common models,
and microstructure representations. SMRT version 1.0 is written in Python
(https://www.python.org/, last access: 2 July 2018)
and released as open source under the LGPLv3 license
(https://www.gnu.org/licenses/lgpl-3.0.en.html, last access: 2 July 2018).

The paper is organized as follows. The next section gives an overview
about the model architecture, the most important formulations, the
code structure, and basic usage. In the third section we present an
intercomparison of SMRT with other models and explore the equivalence
between different microstructures. The fourth section is dedicated to
the discussion of limitations and perspectives. The last section
concludes the paper.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
