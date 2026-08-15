# Data and methods - Model evaluation

For the evaluation of the models, 5-fold cross-validation is used. The same
randomly computed folds are used for RF and GAM. The results are averages
across all folds. The performance of the models is evaluated using the
Nash–Sutcliffe model efficiency coefficient (NSE):
NSE=1-∑i=1nai-bi2∑i=1nai-a‾2,
with a as the true value, b as the predicted value, and a‾ as the mean
of observed values as well as the root mean squared error (RMSE) between
the satellite-derived and the modelled VOD. NSE commonly ranges
between 1 (perfect agreement) and 0, where the latter is the score for a
model which solely predicts the mean of the reference data. Models that
perform worse than this can also yield negative NSE values. In addition to
the overall evaluation of the models, we evaluate the spatial distribution
of NSE, i.e. NSE of the satellite and modelled VOD time series.

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
