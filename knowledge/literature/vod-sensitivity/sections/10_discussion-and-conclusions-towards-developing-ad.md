# Discussion and conclusions - Towards developing advanced approaches to link VOD with vegetation properties

The long time series, global coverage, and multiple frequencies of VOD
retrievals provide valuable information that can be used to derive
vegetation properties at large scales or to evaluate and parametrize land
surface models in data assimilation studies. Yet, those applications of VOD
require a solid understanding of the biophysical controls on VOD. The
relatively high effect of LAI on the short-wave VODs indicates that
data assimilation approaches that only use LAI for estimating the temporal
dynamic of VOD (as they were used by Scholze et al., 2019, and
Kumar et al., 2020) are valid
approximations. However, other studies also found a relationship between
short-wave VOD and plant water status (Konings
et al., 2021) and negative correlation between VOD and LAI
(Tian et al., 2018). This indicates that even models
without an explicit representation of plant water status are suitable for
VOD assimilation, but this might not hold for all vegetation types and needs
further investigation.

LFMC or similar measures for plant water status have only recently been
introduced into land surface models commonly used for global-scale
simulations
(e.g. Kennedy et al., 2019; Niu et al., 2020; Eller et al., 2020; L. Li et al.,
2021). LFMC has therefore not been used in assimilation studies so far. The
long time series of especially Ku-VOD could help to constrain model
simulations of LFMC or support studies of plant water status but requires a
good representation of LAI dynamics.

For observation operators for L-VOD, AGB should be the main predictor of
spatial patterns. Scholze et al. (2019) used the empirical function between VOD and AGB evaluated by Rodríguez-Fernández
et al. (2018) to simulate L-VOD from AGB. Thereby, AGB was replaced with a
function of net primary production and effective turnover time. However,
temporal changes in L-VOD that are caused by changes in plant water status
might result in an overestimation in dynamics of biomass production,
turnover, or biomass loss (Konings et al.,
2021). Scholze et al. (2019) tried to
avoid incorporating short-term changes in VWC and therefore averaged the VOD
simulations to yearly means. The temporal dynamics should include the effect
of plant water status, but further investigations on the drivers of the
temporal dynamics of L-VOD are necessary to make full use of the data.

Including a proxy for VWC and exploring the influence of short-term changes
in vegetation properties on VOD, we assessed the temporal dynamics not only
for L-VOD but also for Ku-, X-, and C-VOD, which will help to make explicit
use of VOD temporal changes within modelling and assimilation studies.

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
