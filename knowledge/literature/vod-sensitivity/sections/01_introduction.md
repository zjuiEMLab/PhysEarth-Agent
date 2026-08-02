# Introduction

Vegetation optical depth (VOD) describes the attenuation of microwave
radiation in the vegetation layer. Quantifying this attenuation effect is
important for an accurate retrieval of surface soil moisture from passive microwave satellite observations (Wang, 1985; Njoku and Entekhabi,
1996). In the radiative transfer equation for microwave emissions, the
opacity of the vegetation layer (i.e. the VOD) is also commonly referred to
as τ (Jackson et al., 1982). VOD can be
retrieved e.g. from the passive microwave radiative transfer equation using
measurements of passive microwaves (Jackson
and Schmugge, 1991; Owe et al., 2008; Sawada et al., 2016). However, VOD is
a parameter in these microwave radiative transfer models for vegetation, and
hence it is not directly measurable and verifiable with in situ
measurements. Therefore, different authors have correlated VOD with
different vegetation properties to understand the sensitivity of VOD to
vegetation properties (Jones
et al., 2011; Rodríguez-Fernández et al., 2018; Konings et al.,
2019a). Generally, the opacity of passive microwaves in the vegetation layer
increases with increasing vegetation water content, but this relationship
varies with vegetation structure including leaf and woody components and
wavelength (Jackson
and Schmugge, 1991; Wigneron et al., 1993; Njoku and Entekhabi, 1996). Based
on radiometer measurements over various crops and a wide range of
wavelengths (0.8–30 cm), Jackson and Schmugge (1991) report a clear linear relationship of VOD to vegetation water content
(VWC):
VOD=b⋅VWC,
where the parameter b depends on vegetation type and wavelength. The authors
find that b exponentially decreases with increasing wavelength, which
implies that vegetation opacity (the VOD) is smaller for longer wavelengths
(i.e. L band) than for shorter wavelengths (i.e. Ku, X, and C bands). The
parameter b is usually kept constant for one vegetation type and wavelength,
which might be insufficient due to its possible dependency on polarization.
In addition, neglecting surface soil roughness can lead to an
underestimation of VOD, especially when the vegetation does not completely
cover the ground (Togliatti et al.,
2022).

The vegetation water content can also be expressed as a product of
above-ground biomass (AGB) and a parameter of relative water content, often
referred to as live-fuel moisture content (LFMC)
(Konings et al., 2019b),
VOD=b⋅AGB⋅LFMC,
whereby LFMC is defined as the ratio of water mass in the vegetation to the
dry mass of the vegetation usually expressed in percentage
(Konings et al., 2019b),
LFMC=Mf-MdMd⋅100,
with Mf as the fresh mass of vegetation and Md as the dry mass of vegetation.

Based on these relationships, many studies use VOD to estimate AGB or other
vegetation properties. For example, Liu et al. (2015) use
Ku-band VOD to estimate long-term changes in global AGB, finding a gain of
above-ground biomass carbon considering forest and non-forest vegetation for
1993–2012. Rodríguez-Fernández
et al. (2018) correlate spatial patterns in AGB and yearly averaged values
of L-band VOD from the Soil Moisture and Ocean Salinity (SMOS) mission with
the INRA-CESBIO (Institut National de la Recherche Agronomique Centre d'Etudes Spatiales de la Biosphère) algorithm (SMOS-IC) for Africa with correlation coefficients
up to 0.85. They find linear relationships between VOD and AGB within single
land cover classes, but the relationship across land cover classes is shown
to be non-linear, with a weaker non-linearity for L-band VOD compared to
Ku-/X-/C-band VOD. Chaparro et
al. (2018) use the L band from the Soil Moisture Active Passive mission (SMOS)
derived with the multi-temporal dual-channel algorithm (MT-DCA) to determine
crop biomass of the north-central USA. Both Rodríguez-Fernández
et al. (2018) and Chaparro et
al. (2018) find better results for pixels with higher homogeneity in land
cover types or even plant types, implying that relationships between VOD and
vegetation properties change with land cover and plant types. X. Li et al. (2021) find
a high correlation of L-band VOD and AGB leading to the conclusion that
long-wave VOD is more sensitive to woody parts of the vegetation than
short-wave VOD. However, Konings et al. (2021) show that the relation between L-band VOD and AGB dominates in space
but that short-term temporal dynamics in VOD are dominated by VWC. As a
proxy for vegetation water status, VOD can be related to LFMC or VWC or both (Fan
et al., 2018; Konings et al., 2019b; Frappart et al., 2020) and can be used
to estimate leaf water potential (Konings
and Gentine, 2017; Momen et al., 2017; Zhang et al., 2019).

Furthermore, VOD is frequently compared with other vegetation properties
such as canopy greenness, the leaf area index (LAI), or plant productivity. For
example, VOD shows similar temporal patterns to the normalized difference
vegetation index (NDVI) and LAI (Liu
et al., 2011; Momen et al., 2017; Bousquet et al., 2021). In spatial
comparisons, the vegetation indices and variables tend to saturate over
densely vegetated areas. This saturation is less distinct for VOD (Rodríguez-Fernández
et al., 2018) due to the ability of microwaves to penetrate deeper into the
vegetation layer. Therefore, VOD provides complementary information to the
usually visible–infrared-based metrics (Jones
et al., 2011). For example, metrics sensitive to biomass or water content
shifts can be derived from VOD (Jones
et al., 2011, 2014). VOD can also be used for assessing land surface
phenology (Jones et al., 2011). VOD and temporal changes in VOD are also
correlated with gross primary production (GPP) (Teubner et al.,
2018), which allows VOD to be used as a predictor of GPP (Teubner
et al., 2019, 2021; Wild et al., 2022).

Recently, several new VOD datasets have become available for the X band from the
Advanced Microwave Scanning Radiometer – Earth Observing System sensor
(AMSR-E) and Advanced Microwave Scanning Radiometer 2 (AMSR2) sensors (Du
et al., 2017; Wang et al., 2021) and for the L band from the SMOS (van
der Schalie et al., 2016; Fernandez-Moran et al., 2017; Al Bitar et al.,
2017; Wigneron et al., 2018, 2021) and Soil Moisture Active Passive sensors (SMAP; Konings et al., 2017). VOD was
also retrieved jointly from several sensors (van
der Schalie et al., 2017), and harmonized long-term multi-sensor datasets
have been produced (e.g. Vegetation Optical Depth Climate Archive, VODCA, Moesinger et al., 2020). A
recent comparison study by Li et al. (2021) of
different X-, C-, and L-band VOD datasets and Moderate Resolution Imaging
Spectroradiometer-derived (MODIS) vegetation indices like NDVI and the enhanced
vegetation index (EVI) as well as tree height and AGB showed that X-band VOD
is more suitable to detect temporal variations of the green vegetation
parts, especially for less densely vegetated areas, than C- and L-band VOD.
Additionally, Li et al. (2021) as well as Moesinger et al. (2022) found time lags between VOD and vegetation indices and climate
variables, which are not yet fully understood. This shows the need to
include further ecological parameters or vegetation variables which could
account for a delayed response of VOD to temporal changes in the vegetation
indices. Approaches with the ability to consider VOD variations caused by
vegetation water content have been developed, which are more complex than
simple regression functions (e.g. Momen et al., 2017).
Momen et al. (2017) were able to
estimate VOD by using two predictors, LAI and leaf water potential. Among
others, the studies by Momen et al. (2017) and Teubner et
al. (2019) show that the water content of the vegetation influences VOD
and therefore affects not only the relation between vegetation indices and VOD
but also the relation between VOD and AGB.

The increasing availability of VOD data for vegetation studies also
increases the possibilities for assimilating or integrating VOD with ecosystem or
land surface models (LSMs) (Scholze et al.,
2019; Kumar et al., 2020). Therefore, observation operators are needed that
link the modelled vegetation properties with the satellite-retrieved VOD.
Scholze et al. (2019) use the sum of
an empirical AGB function and a linear term for LAI to describe annual
SMOS-IC L-band VOD within the carbon cycle data assimilation system (CCDAS)
for estimating European carbon fluxes.
Kumar et al. (2020) use cumulative distribution function (CDF) matching to
convert VODCA X- and C-band VOD and SMAP L-band VOD to LAI, which is then
assimilated into the Noah-MP (Multiparameterization) LSM. X- and L-band VOD showed partially
complementary improvements in the modelled land surface variables. Both
studies by Scholze et
al. (2019) and Kumar et al. (2020) find an improvement in the model results
by incorporating passive microwave data, demonstrating the benefits of the
vegetation information contained in VOD. In another model-data-fusion
approach, Liu et al. (2021)
use VOD to derive plant hydraulic parameters for a soil–plant system model
that accounts for the hydraulic state of the vegetation explicitly. However,
as VOD reflects both dynamics in biomass and water content (Jackson and Schmugge, 1991;
Konings et al., 2021), relations between VOD and AGB or LAI as observation
operators are simplifications and demonstrate the need for a more detailed
understanding of the effects of vegetation properties on VOD.

The increasing use of VOD for ecosystem studies (e.g. Dorigo et al., 2021) and land surface modelling
poses the question of how different vegetation properties affect VOD in both
time and space. Hence, a more detailed investigation of the relative effects
of vegetation properties on VOD could improve the understanding of the VOD
signal in terms of interpretation of the corresponding vegetation status.
Such investigations will also help to identify a suitable VOD dataset for a
specific ecological application in addition to the technical aspects of the
datasets like the observation resolution depending on wavelength, errors, and
artefacts induced by the retrieval algorithm or the observation time
depending on overpass times of the satellites.

Furthermore, due to the high temporal resolution and temporal coverage of
VOD datasets (partly since 1987), global analyses of vegetation properties
and status as well as land cover change can be conducted for enhanced
understanding of long-term environmental changes and to improve model
predictions.

Here we aim to assess VOD in response to multiple vegetation properties at
large (i.e. inter-continental) scales. Specifically, our objectives are to
predict VOD from LFMC, LAI, and AGB by using two machine learning regression
approaches and to investigate the relationship between VOD and the
predictors. This objective goes beyond previous empirical studies that
compared VOD with vegetation properties based on bivariate correlations or
regressions but not by estimating VOD within a multi-variate framework.

We use random forests (RFs) and generalized additive models (GAMs) to predict
VOD from LFMC, LAI, AGB, and land cover. Accumulated local effect (ALE)
curves are used to assess the sensitivities of VOD to these properties.
While GAM is suitable to capture non-linear and non-monotonic relationships
with additive effects of the predictors, a random forest (RF) approach can predict more complex
interactions but is less suitable to capture a possible additive behaviour.
Therefore, comparing both machine learning algorithms gives insights into
the structure of the relationship between VOD and vegetation properties and
provides confidence in the findings. Additionally, we inspect how different
temporal resolutions (i.e. 8-daily and monthly data) affect the
relationships between VOD and vegetation properties for identifying the role
of vegetation variables at quasi-weekly and seasonal timescales. The
analyses are carried out for five VOD datasets, which differ in wavelength
but were derived with the same algorithm (Land Parameter Retrieval Model,
LPRM) (van
der Schalie et al., 2016, 2017) to exclude
differences due to retrieval algorithms.

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
