# Discussion and conclusions - Predictors and predictability of VOD

The results demonstrate that for the global prediction of VOD, i.e. over
different biomes, a flexible modelling approach such as RF is better suited
than an additive approach like GAM. The lower global performance of GAM
suggests that local factors, e.g. intercepted or standing water or
heterogeneous soil properties, and interactions between factors play a role
in the dynamics of VOD. In contrast, RF is partly able to account for this
due to its ability to flexibly model, which results in higher model
performance. The simpler structure of GAM compared to RF is, in most cases,
insufficient to predict VOD, but within single land cover types a simpler
additive approach like GAM is sufficient. This indicates that the
relationship between VOD and LAI, LFMC, and AGB cannot be easily
captured with global linear, monotonic, and bivariate regressions but
requires accounting for the non-linear interactions between various
ecosystem properties. The results imply that the set of predictors allows for
the estimation of the dynamics of short-wave VODs at a high temporal
resolution (8-daily and monthly) with very good performance, but the set of
used predictors is insufficient to explain the dynamics in L-VOD due to
ignoring local effects or possibly disregarded predictors.

This conclusion is supported by the performance difference between the four
studied regions. For example, Europe has a more fragmented landscape than
most areas in Australia, causing mixed effects on VOD within the coarse
0.25∘ grid cells, leading to a lower predictability in Europe than
Australia. Even if PFT fractions are used as predictors, the mismatch
between the coarse resolution and land cover complexity cannot be resolved.
This is especially pronounced in the long-wave VOD, for which the footprint
is often significantly larger than 0.25∘ (> 40 km).
Local complex effects on VOD are likely related to land cover changes,
intercepted or standing water, or soil properties. For example,
Saleh et al. (2006) showed for a
grassland site that intercepted water could double L-VOD after a rainfall
event. Comparable to this finding, Wigneron et
al. (1996) also reports a possible doubling in C-VOD due to interception at
a wheat field. Although interception has reduced influence on the coarse-resolution data (Baur
et al., 2019; Wigneron et al., 2021) or might not impede temporal VOD
analyses (Feldman et al., 2020), temporary
flooding leads to an evident change in VOD. For example, a decreased L-VOD
signal at flooding was recognized for short-vegetation areas using Ku-VOD
derived from the microwave radiometer of the Chinese satellite FY-3B (Fengyun)
(Liu et al., 2019) as well as for
forests using AMSR-E Ku-VOD (Jones
et al., 2011) or using SMOS-IC L-VOD (Bousquet et al., 2021). The effect of
such local events on VOD implies that large-scale spatial relations between
VOD and e.g. AGB (Liu
et al., 2015; Rodríguez-Fernández et al., 2018; Mialon et al.,
2020) will likely wrongly associate changes in VOD with changes in AGB, which
might result in unrealistic estimates of local AGB dynamics. This conclusion
is supported by the findings of Konings
et al. (2021), who show that regional temporal anomalies of X- and L-VOD are
mostly uncorrelated with temporal anomalies of AGB but show a higher
correlation with root-zone soil moisture, an indicator of water stress and
availability.

The comparison of the global and the land-cover-specific models highlights
the complexity of the relation between VOD and vegetation properties. An
interesting result is that the ALE amplitudes (i.e. sensitivity) increase
with increasing wavelength in the global model but not in the land-cover-specific model. The land-cover-specific models only include pixels
with a coverage of > 55 % of the specific land cover type but do
not use PFT fractions as predictors. This indicates that PFT fractions serve
as a descriptor of vegetation structure and hence as a descriptor of land
cover heterogeneity in the global model. This results in a VOD–LAI
relationship that varies by microwave wavelength. But this
wavelength dependency cannot be resolved within the land-cover-specific
models because those models cannot account for the impact of sub-pixel land
cover heterogeneity. Furthermore, the differences in the VOD–AGB
relationship between the global and the land-cover-specific models also
highlights that a monotonic VOD–AGB relationship is only valid over a large
spatial scale but does not hold within a vegetation type or at smaller
scales. The high model performance in regions with high biomass areas were
enabled using PFT maps as predictors, which compensate for the saturating
effect at high AGB. Similar to the VOD–LAI relationship, the relative
sensitivity of the LFMC ALE increases with increasing wavelength for the
global models, and it also shows that LFMC has relatively more influence on an
8-daily timescale compared to the monthly timescale for the global as well
as the land-cover-specific models.

Both LFMC and LAI are strongly correlated. The temporal and spatial
variation in our global models are dominated by LAI, leading to a lower
influence of LFMC on short-wave VOD than of LAI. Although LFMC appears as the
less important predictor of VOD than LAI in our models, the strong
correlation of LAI and LFMC is nevertheless the reason why in situ measured
LFMC show medium to strong correlations with VOD and can be used to estimate
LFMC from short-wave VOD (Fan
et al., 2018; Forkel et al., 2023).

Globally, the L-band VOD is highly influenced by AGB, which is in agreement
with the ability of long-wave VOD to better penetrate dense vegetation and
its higher sensitivity to the woody plant parts (Liu et al., 2011). However, the much
lower predictability of L-VOD compared to Ku-, X-, and C-VOD indicates that
L-VOD cannot be sufficiently explained by the combination of AGB, LAI, LFMC,
and land cover. The performance in predicting L-VOD is much lower at
the pixel level (Fig. 3) than computed across the full spatial and temporal
extent of the data. Hence, the low performance in predicting L-VOD is mostly
related to the temporal dynamics at the pixel level because our model correctly
explains the spatial patterns. The low performance in predicting SMOS L-VOD
might be caused by a noisy signal of the SMOS sensor (van
der Schalie et al., 2017). Especially the daily raw L-VOD data, as used for
the 8-daily analyses, can be very noisy (Wigneron et al., 2021). Vittucci et al. (2016)
found moderate seasonal differences (but within the standard variation) of
the SMOS L-VOD signal over forests located at latitudes higher than
+20∘, which are partly explainable due to the deciduous
character of the forest but moreover because of random effects. The L-band
signal, as well as the C-band signal, is strongly disturbed by radio-frequency
interference (RFI; Liu et al.,
2019). The spatial and temporal inconsistency of RFI complicates the RFI
correction of the L band (Wigneron et al.,
2021). This indicates a noisy, or until now not fully understood, variation
in the SMOS L-VOD, especially within the lower value range. Due to the
uncertain proportion of noise and short-term changes in water content,
Ebrahimi et al. (2018)
averaged SMOS L-VOD over 15 d and Rodríguez-Fernández
et al. (2018) did so even over 2 years to reduce related uncertainties in the VOD
signal. Vaglio Laurin et al. (2020) found a
time lag of up to 6 months between SMOS L-VOD and ecosystem functional
properties in tree-covered areas in South America and Africa;
Tian et al. (2018) found it between SMOS L-VOD and
LAI in tropical woodlands. This time lag shows that the relationships
between SMOS L-VOD and vegetation properties need further investigation in
densely vegetated regions.

In addition to the possible noisy signal of SMOS L-VOD, which might hamper
the interpretation, errors within the L-VOD values can also be introduced by
the retrieval algorithm itself. With the use of a tau-omega model, soil
moisture and VOD are often retrieved simultaneously, which can introduce
errors in the VOD retrievals. Zwieback et al. (2019) found spurious
correlations of soil moisture and VOD especially for sub-monthly timescales
over forests. Besides that, the correctness of the retrieval product focuses
on soil moisture at the cost of the VOD retrieval. The resulting error
shifts from soil moisture to VOD are more prone to short-term changes and to
higher VOD values (Feldman et al., 2021),
which might contribute to the underestimation of high VOD values of our
models and the reduced performance of the 8-daily models compared to the
monthly models. A more robust L-VOD product might be achieved by analysing
and adjusting the necessary degree of regularization for a VOD retrieval
depending on the timescale and land cover (Zwieback et
al., 2019; Feldman et al., 2021).

An interesting finding is the higher sensitivity of L-VOD to LFMC than to
LAI. This indicates that the L band indeed penetrates deeper into the canopy (low
sensitivity to LAI) but is sensitive to the plant water status (i.e. LFMC).
However, AGB and LFMC are insufficient predictors for reaching high
predictability of L-VOD. This might be caused by the fact that the AGB
dataset used in this study does not contain any temporal information, and
hence changes in AGB are not considered in our model. Using an alternative
dataset (e.g. Xu et al., 2021), which
provides a global time series of AGB, could be a benefit for improving the
understanding of temporal VOD variations. Especially seasonal dynamics of
AGB could contribute to a better prediction of L-band VOD. However, as we
included annual land cover maps as predictors, our models do indeed account
for land cover change such as deforestation, which is strongly related to a
change in AGB (Andela et
al., 2013). The use of LFMC and LAI as predictors might be insufficient for
L-VOD. The used LFMC and LAI data were both derived from optical observation
by MODIS, which is only sensitive to the top of the canopy in closed forest
canopies. Root-zone soil moisture was used as a proxy for water availability
in other studies (e.g. Konings et al.,
2021); however, it is not an ideal predictor of vegetation water content,
as some plants can regulate their water potential or moisture content
independent of soil moisture (Konings and
Gentine, 2017; Hochberg et al., 2018). Therefore, it is necessary to further
investigate the daily to seasonal temporal dynamics of L-VOD with respect to
e.g. local and regional observations of water availability and plant water
status.

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
