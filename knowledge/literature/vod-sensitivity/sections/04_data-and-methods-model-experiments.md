# Data and methods - Model experiments

The parameter b (Eq. 2) and therefore the relationship between
vegetation water content and VOD depends on the vegetation and plant type
(Jackson and Schmugge, 1991). Therefore, we account
for plant types by using two main classes of regression models to predict
VOD. The first class is global models that use the PFTs from the land cover
map in addition to the vegetation predictors LAI, LFMC, and AGB. This means
that the individual maps of treeBE (broadleaf evergreen), treeBD (broadleaf deciduous), treeNE (needleleaf evergreen), treeND (needleleaf deciduous), shrub, crop, and
herb are used as additional predictors. The second model class is comprised
of land-cover-specific models using LAI, LFMC, and AGB as inputs. These
models are only applied to the spatial extent of one dominant land cover
class. In models for short-vegetation classes, AGB is not used as a
predictor because this map is only representative of forest biomass. All
model setups were trained both for GAM and RF and using monthly as well as
8-daily values for each VOD dataset. Table 2 gives
an overview of the models and the input data. We hypothesize a better
performance of global models compared to land-cover-specific models
indicating that including information of the vegetation type (i.e. as a
proxy for vegetation structure) in the model will improve the understanding
of VOD, especially for pixels with heterogeneous land cover.

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
