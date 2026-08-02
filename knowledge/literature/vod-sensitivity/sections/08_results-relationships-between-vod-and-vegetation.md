# Results - Relationships between VOD and vegetation properties

## Global (inter-continental) relationships

The effects of vegetation properties on VOD for all wavelengths on a monthly
or an 8-daily data basis are shown in the ALE plots in
Fig. 5 (Figs. S3 and S4 for all global predictors
and GAM). The amplitude ΔA values of the ALE curves can be used as a
measure of the importance of a predictor of the estimation of VOD. The
amplitude ΔA values are usually higher for monthly data than for
8-daily data (Fig. 6a), except for the
relationship between AGB and SMOS L-VOD (Fig. 6c). This result indicates that the used predictors are of higher importance
for monthly data than for 8-daily data. However, the high ΔA values in the global RF model based on 8-daily data for SMOS L-VOD and the
relative low performance of this model (NSE = 0.41) indicate that the
influence of the used predictors might be overestimated. A predictor that
could reproduce the main temporal dynamics in the 8-daily SMOS L-VOD signal
is indeed missing in the analysis.

The order of ΔA of the predictors within a certain model are
generally similar for 8-daily and monthly models. The coverages of trees are
for all models one of the main contributors to the VOD predictions
(Figs. 7c, S3, and S4). LAI is the second-most
important predictor of Ku-VOD and the most important for X- and C-VOD. For
the L-VODs the importance of LAI is lower than for the short-wave VODs
(Figs. 5 and 7c).
The importance of AGB increases from low to middle importance for the
short-wave VODs to the highest importance for the L-VODs
(Fig. 7c). The coverages of short-vegetation
classes have a middle to low influence on the VOD, decreasing with
increasing wavelength, but as an exception the coverages of shrubs is the
second- and third-most important predictor of monthly and 8-daily SMAP
L-VOD, respectively (Figs. 7c, S3 and S4). The
ΔA values of LFMC increase with wavelength, with low influence
on Ku- and X-VOD and higher influence on L-VOD. An exception here is the
8-daily SMOS L-VOD model, where LFMC also has a low impact on the
predictions, but given the low performance of this model, the estimated
importance of LFMC on SMOS L-VOD might be unreliable (Fig. S3).
Interestingly, the amplitude of the ALE plots varies between wavelengths,
within monthly and 8-daily models, although these results are based on
normalized data (Fig. 6c). For LAI and land
cover a clear decrease in the ALE amplitude with increasing wavelength is
visible, which corresponds to the fact that the magnitude of the VOD value range
decreases with increasing wavelength (Figs. 5a and d and 7c). For AGB and LFMC, the ALE amplitude
increases with increasing wavelength (Figs. 5b and c and 7c).

Given the similar shape of ALEs based on 8-daily and monthly data but with smaller
amplitudes, we will focus on the examination of the monthly ALE curves. All
VOD datasets show a positive relationship with LAI, but all curves saturate
around an LAI value of 2.3, which corresponds approximately to the
95th percentile of LAI in our dataset (Fig. 5a). LAI
has a much stronger effect on Ku-, X-, and C-VOD than on L-VOD.
Interestingly, the relationship between LAI and SMAP L-VOD is more similar
to the relationship of LAI and short-wave VODs (e.g. X-VOD) than the
relationship with SMOS L-VOD (especially shown between the 75th and
95th percentile in Fig. 5a).

The relationship with LFMC is more complex for all VOD datasets
(Fig. 5b). From 0 % to 50 % LFMC, the
relationships are negative with a negative spike at 50 % LFMC. We
hypothesize that this spike is a species-specific behaviour or a poorly captured relation for herbaceous-vegetation pixels in South Africa and
Australia; however, further investigation is required to investigate if this
is a real response of the vegetation. Afterwards, VOD increases with
increasing LFMC, which is most pronounced for SMOS L-VOD. However, SMAP
L-VOD shows a strong negative relationship with LFMC after around 140 %
LFMC. Despite all relations within the 5th and 95th percentile needing to be
interpreted with caution, this is especially the case for the
95th percentile of the LFMC ALE due to the uncertainties of the original
dataset where higher LFMC values also have a higher uncertainty
(Yebra et al., 2018). In addition,
the validation of the LFMC dataset is impeded by uncertainties due to
difficulties of comparison between measurements on the ground and what is
detected by the satellite. Uncertainties in the used LFMC dataset arise from
the temporal matching procedure of in situ samples and MODIS data and from
the canopy closure of the forest cover and the contribution of the understorey to
the measured surface reflectance. However, these factors are difficult to
quantify and can only be discussed in a qualitative manner, but they still
might influence the results presented here.

All VOD datasets show a similar increase with AGB until 120 Mg ha-1
(corresponding to the 95th percentile), but the relationships differ at
higher AGB values (Fig. 5c). Ku-, X-, and C-VOD
show a decrease with increasing AGB above 120 Mg ha-1, but SMOS and SMAP L-VOD
continue to increase.

The relationships with land cover fractions are positive for most VOD
datasets. As an example, we show here the relationship with the fraction of
shrubland cover (Fig. 5d). SMAP L-VOD shows a
nearly monotonic increase with increasing shrubland cover. The short-wave
VODs and SMOS L-VOD show no relation with shrubland cover below 10 %
coverage but show a positive relationship at higher coverage. SMOS L-VOD
shows a non-monotonic relationship with shrubland cover.

Taken together, we find the following effects of vegetation properties on
the different VOD datasets: SMOS L-VOD is most strongly affected by AGB
(positive relationship), followed by tree cover and LFMC (positive
relationship at LFMC > 50 %), short-vegetation cover, and LAI
(positive relationship for LAI < 1.5). SMAP L-VOD is most strongly
affected by AGB (positive relationship), followed by LFMC (negative
relationship) and shrubland cover and LAI (positive relationship for LAI < 2.5). Ku-, X-, and C-VOD show very similar relationships and are
most strongly affected by LAI (positive relationship) and tree cover,
followed by AGB (positive relationship up to 120 Mg ha-1), short-vegetation
cover, and LFMC.

## Relationships within land cover types

In this section, we summarize the results of the RF models for relationships
within a certain land cover type (see Figs. S5 to S8 for land-cover-specific ALE plots based on RF and GAM). The individual predictors in
the land-cover-specific models have a higher influence on the VOD prediction
than in the global model because the land-cover-related predictors are not
used within the land-cover-specific models (Fig. 6d). ALE amplitude ΔA values for monthly data are mostly larger
than for 8-daily data with some exceptions for SMOS L-VOD
(Fig. 6b). The order of ΔA for
the different VODs is in the land-cover-specific models like in the global
model with the highest values for SMOS L-VOD, followed by Ku- and SMAP L-VOD
and X- and C-VOD.

In models for specific tree cover types, AGB has the largest ΔA, followed by LFMC and LAI (Fig. 7a).
The model for deciduous trees for 8-daily SMOS L-VOD data is an exception,
in which LAI has the largest importance, followed by LFMC and AGB (Fig. S5). Due to the poor performance of this model, this result might be
questionable.

Models for short-vegetation types usually have LAI as the most important
predictor, followed by LFMC (Fig. 7b).
Exceptions are the models for the herbaceous vegetation with 8-daily SMAP
L-VOD and 8-daily and monthly SMOS L-VOD, where LFMC has the highest
importance. In general, for the tree cover models AGB and for short-vegetation cover LAI have a higher influence on the predictions than LFMC.
Nevertheless, the ΔA–LFMC regression line in Fig. 6h indicates that LFMC has a similar
effect on both timescales. This is contrary to AGB and LAI, where the effect
is higher for monthly than for 8-daily data. For short vegetation, the ALE
plot between VOD and LFMC shows a similar form as in the global model with a
drop around 50 % LFMC (Fig. S6), which indicates that the global
VOD–LFMC relationship is dominated by dynamics in short-vegetation areas.
Particularly, the drop is based on the herbaceous land cover type, which is
also visible in the 8-daily based models and in the GAM (Figs. S6 and S8).
The importance of LAI in predicting VOD decreases for herbaceous and
shrubland cover models with increasing wavelength. A similar dependence
occurs for LFMC for shrublands and monthly data above 140 % LFMC.
Globally, the positive relationship between VOD and LFMC in the range of
50 % to 140 % LFMC and the negative relationship at higher LFMC
(Figs. 5b and S6) originates from croplands
because this decrease is only visible in the LFMC ALE from the cropland
model.

In tree-covered areas (treeAll model), the ALE shows that VOD marginally
increases with LAI up to LAI = 2 and is then stable or slightly decreases
(Fig. S5). The relation of VOD with LFMC is positive for Ku-, X-, and
C-VOD but non-monotonic for both L-VODs. AGB is the dominant predictor of
all tree-covered models, but the relationship with VOD is highly non-linear
and non-monotonic, especially in comparison to the relationships with LAI
and LFMC.

Comparing the ALEs of the treeAll model with the models for individual
forest types (i.e. treeB, treeN, treeD, treeE, Fig. S5) shows that the
influence of a specific forest type is partially recognizable within the
treeAll ALEs. For example, the relationship between LFMC and VOD in the
treeAll model is highly influenced by the relationship for needleleaf and
evergreen trees. The decline in SMOS L-VOD with LFMC is also pronounced
within most tree types but not within deciduous trees. The relationships
with AGB for needleleaf trees is more linear in comparison to the other
tree cover models. Deciduous and broadleaf trees exhibit a more complex
relationship with AGB than evergreen and needleleaf trees for all VODs.
The amplitudes of ALE curves with AGB are highest for X-VOD for deciduous
trees (treeD ΔA=0.175) and for SMOS L-VOD for broadleaf
trees (treeB ΔA=0.313). These results demonstrate that
biomass is also an important predictor of short-wave VODs but that
this importance varies with wavelength and forest type.

Contrary to the global model, the land-cover-specific models do not exhibit
a clear dependency of the ALE amplitude on the wavelengths.

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
