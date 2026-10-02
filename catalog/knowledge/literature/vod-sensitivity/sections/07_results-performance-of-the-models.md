# Results - Performance of the models

The different regression models showed large differences in model
performance in predicting VOD (-0.04 ≤ NSE ≤ 0.97; 0.004 ≤ RMSE ≤ 0.15) (Figs. 2 and S1 in
Supplement). In summary, these differences were dominated by

the type of regression model (RF or GAM, Fig. 2 left subplots vs. right subplots, Sect. 3.1.1),
the use of 8-daily or monthly VOD data (symbols in
Fig. 2, Sect. 3.1.2),
the inclusion of land cover information as a predictor (Sect. 3.1.3),
the wavelength of the predicted VOD (i.e. from the Ku to the L band, Sect. 3.1.4), and
the vegetation type to which the model is applied (Sect. 3.1.5).

## Effect of the type of regression model used for calibrating the models (RF vs. GAM)

In general, RF performed better than GAM in predicting VOD, except for land-cover-specific models for short-vegetation classes where GAM reached
a slightly higher NSE (Fig. 2a vs. b) and a similar
RMSE compared to RF (Fig. 2c vs. d). Another
exception occurs for SMOS L-VOD where GAM performed better regarding the
land-cover-specific models for cropland and shrubland based on 8-daily data
(see Fig. S1 for all models). While all models tended to underestimate
high VOD values, RF approximated them better than GAM. Based on these
findings, in the following sections, we only refer to the results of RF
models. If not stated otherwise, similar results were found for GAM.

## Effect of the temporal aggregation of the predictor variables (8-daily vs. monthly data)

Regression models based on monthly data usually exhibited a higher NSE and
a lower RMSE than models based on 8-daily data (comparison of circle and
crosses in Figs. 2 and S1). The superior
performance of monthly over 8-daily models increased with increasing
wavelength. For example, the difference was especially large for the
prediction of SMOS L-VOD for which NSE doubled from 8-daily to monthly data
(Fig. 2a). The performance in predicting Ku-, X-,
or C-VOD was similar or monthly data presented slightly higher
performance than 8-daily data. Given the higher performance of models based
on monthly data, the following description of results is based on models
with monthly data, unless mentioned otherwise. Section 3.2 examines the
differences in VOD sensitivities to the predictors based on the considered
timescale.

## Effect of including land cover information as a predictor (global vs. land-cover-specific models)

Considering RF models based on monthly data, the global models (defined as
models including fractional cover of PFTs as predictors; see
Table 2) showed better model performance than the
land-cover-specific models that were trained and applied only to one
specific land cover. The global models performed with an NSE of 0.85 to 0.95
and an RMSE of 0.01 to 0.03 depending on VOD wavelength
(Fig. 2a and c). We also compared the model
performance of a specific land cover type within the global model with the
related land-cover-specific model. The land-cover-specific RF models had a
lower NSE (-0.09 to -0.59) and a higher RMSE (+0.006–0.03) than the global
model within the same land cover. Considering GAM, land-cover-specific
models performed better within a certain land cover type than the global
model for the same land cover type. This applies especially for land cover
types with simpler vegetation structure, e.g. shrubland, herbaceous
vegetation, or broadleaf evergreen trees, and less for more complex land
cover types like the tree cover and short-vegetation classes. These results
indicate that the relationship between vegetation properties and VOD can be
modelled with simpler relationships as represented by GAM only within a land
cover type but that global relationships require more complex relationships
as represented by RF.

## Effect of wavelength

In general, the NSE of predicting short-wave VOD was higher than for
predicting L-VOD and RMSE decreased from long to short wavelengths
(Fig. 2). All SMOS L-VOD models performed with a
lower NSE and a higher RMSE than the other VOD models including SMAP L-VOD.
For RF models based on 8-daily data, NSE was highest for Ku-VOD, followed by
X-VOD and C-VOD. For monthly data and GAM, the order in performance was
slightly different between Ku-, X-, and C-VOD for NSE and RMSE.

In the global model, the land-cover-specific model performance depended on
the different VOD wavelengths. The prediction of monthly Ku-, X-, and C-VOD
using RF reached the highest performance for broadleaf evergreen trees
(0.95 ≤ NSE ≤ 0.97, 0.009 ≤ RMSE ≤ 0.013) and the lowest
performance for croplands (0.82 ≤ NSE ≤ 0.85, 0.015 ≤ RMSE ≤ 0.023). Predicting monthly SMAP L-VOD using RF had the highest
performance in herbaceous vegetation (NSE = 0.93, RMSE = 0.016) and the
lowest performance in deciduous trees (NSE = 0.74, RMSE = 0.031). RF
prediction of monthly SMOS L-VOD attained the highest performance in
herbaceous vegetation (NSE = 0.84, RMSE = 0.023) and the lowest
performance in needleleaf and deciduous trees and croplands (NSE ∼ 0.6, 0.032 ≤ RMSE ≤ 0.059).

## Spatial variability in model performance

The performance in predicting VOD shows large spatial differences
(Fig. 3). Across all VOD datasets, the prediction
of VOD was best in Australia, followed by South Africa, Europe, and the western
USA (Fig. S2). As for the global model results (Sect. 3.1.4), the best
performance was achieved in predicting Ku-, X-, and C-VOD, and the lowest
performance was for SMOS L-VOD. This is indicated by the dominant colour
distribution in Fig. 3 and by the corresponding
histograms (Fig. S2), whereby the more right-skewed and narrower the
distribution, the better the prediction of all pixel time series (e.g. Ku-VOD
for Australia).

Several geographical patterns of high or low model performance appear for
all VOD datasets. High model performance occurs mainly in regions with
croplands (e.g. south-western and south-eastern Australia), large shrublands
(e.g. northern Australia and central South Africa), and grasslands
(north-western and south-eastern South Africa and western Australia) (high
NSE, blue areas in Fig. 3). Regions in the
south-western USA show a poor performance (low NSE, red areas in
Fig. 3).

Higher model performance occurs also more in regions with larger seasonality in
LAI and LFMC (e.g. eastern Europe and the northern part of the western USA)
(Fig. 4c) and in pixels with homogenous land
cover than in pixels with a more heterogeneous land cover distribution
(Fig. 4a and b). With increasing wavelength, the
VOD of areas with less pronounced seasonality was getting more difficult to
predict.

Additionally, regions with mean VOD values less than 0.1 and marginal
changes over time tend to have low or even negative NSE. This is noticeable
in central Australia and central South Africa. Investigating the differences
in the overall NSE based on all values (Sect. 3.1) with the grid-cell-based NSE in
Figs. 3 and S3 allows for insight if the RF models
are able to represent not only spatial patterns but also time series. The
comparison of the high overall NSE (> 1000 data samples) with
the NSE shown here (monthly time series January 2015–July 2017 resulting
in a maximum time series of 31 months, i.e. <32 data samples)
indicates that NSE seems to be sensitive to the data size, leading to a low
NSE when few data points are available. The reference and modelled mean VOD
and the variance of VOD are highly correlated in space (Spearman correlation
coefficient > 0.75), which shows that the models capture the
variability and spatial patterns of VOD. With a higher mean VOD the NSE
increases, e.g. such as for the tree-covered areas dominated by deciduous
broadleaf trees. Whereby this finding is based on the VOD range constrained
by the proceeded data preparation, it might be not valid for very high VOD
values, e.g. in rainforests, which are not considered here.

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
