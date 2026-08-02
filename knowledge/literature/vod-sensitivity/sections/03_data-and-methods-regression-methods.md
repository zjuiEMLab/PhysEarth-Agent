# Data and methods - Regression methods

To assess the influence of the vegetation variables on VOD, we applied two
methods: generalized additive models (GAMs) and a random forest regressor (RF).

The RF algorithm incorporates multiple independent decision trees, where the
final prediction is the average prediction of the individual trees (Breiman,
2001; Hutengs and Vohland, 2016; Liang et al., 2018). Using the scikit-learn
package version 24.1 (Pedregosa et al.,
2011) multiple hyper-parameters can be tuned, which will define the RF model
structure. The optimization of the hyper-parameter combination is crucial to
achieve a well-performing model. The scikit-learn package provides the
grid-search function “RandomizedSearchCV” which enables an automatized
search for an optimized parameter set by splitting the multi-variate space
of the hyper-parameters into a grid of parameter combinations which are then
used to train an RF. During this grid search for an exemplary dataset
(predicting monthly inter-continental Ku-VOD with LAI, LFMC, AGB, and land
cover), the minimum number of samples within a leaf (1 and 4), number of
estimators (100 and 200–2000 with 200 steps), maximum features (functions:
“auto”, “sqrt”, “log2”), maximal depth (10–110 with 20 steps and “None”), and
minimum samples split (2 and 10) were tested. For a detailed description of
the available hyper-parameters and their effect on the result, please refer
to the documentation of the scikit-learn module
sklearn.ensemble.RandomForestRegressor
(https://scikit-learn.org/0.24/modules/generated/sklearn.ensemble.RandomForestRegressor.html, last access: 20 October 2022).
The best combinations were again tested with monthly inter-continental
predictions of X-, C-, SMOS L-VOD and SMAP L-VOD. Some combinations led to partly
improved results compared to the scikit-learn default hyper-parameters but
also partly degraded results. We finally selected the following
hyper-parameters: minimum samples within a leaf = 1, number of
estimators = 100, maximum features = “auto”, maximal depth = None, minimum
samples split = 2, and criterion = mean squared error. This setup provided
the best results across all tested models. The chosen maximum features
parameter leads to the consideration of all features for all splits, thereby
omitting one of the strengths of RF. This parameter may have been selected
due to the low number of our chosen vegetation variables. However, RF is
still able to capture complex relationships, which is our main focus.

GAMs are a progression of standard linear regression models and generalized
linear models (GLMs) (Hastie and
Tibshirani, 1987). In comparison to standard linear regression models, GLMs
use a link function to connect the mean response of the target variable with
the predictors, which can also represent other distributions of the target
variable besides the Gaussian distribution, like binomial, gamma, or Poisson
distributions (Nelder and Wedderburn,
1972). In addition, GAMs incorporate smoothing functions for each predictor
variable (Yee and Mitchell, 1991). This allows
for modelling non-linear and non-parametric relationships between the target and
predictor variables. A general GAM equation can be written as
g(μ)=b+∑i=1nfjxi,
with g() as the link function, μ as the mean response of target variable, b as
the intercept term, f() as smoothing functions, and x as predictor variables.
Thereby, g(μ) represents the target variable, i.e. predicted VOD data,
and f(xi) represents the predictors, i.e. the vegetation variables LAI, AGB, LFMC,
and land cover expressed as PFT datasets. Here the GAM is developed for a
Gaussian distribution with an “identity” link function and spline terms as
smoothing functions using the Python package pyGAM version 0.8.0
(Servén et al., 2018).

Both methods are compared to evaluate if the relationship between the
features and the target variable is additive (adequately captured by GAM) or
more complex (requiring RF). GAM can represent non-linear and non-monotonic
relations with single predictors whereby all predictors have a joint
additive effect. RF can represent more complex relations and interactions
between the single predictors but is not well suited for capturing
additive structures in the data (Hastie et al., 2009). Another
reason to use GAM simultaneously with RF is that models that are designed for
short vegetation use just two predictors (LAI and LFMC). The AGB dataset is
only representative of woody biomass of trees and can therefore not be
included for short vegetation. While GAM can utilize a small number of
predictors, the application of RF with only two predictors will likely
result in overfitting as the random choice of a predictor variable during
the development of decision trees is very limited. Both methods allow for the
qualitative and quantitative assessment of the sensitivities of VOD to the
predictors via accumulated local effects (ALEs; see Sect. 2.5).

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
