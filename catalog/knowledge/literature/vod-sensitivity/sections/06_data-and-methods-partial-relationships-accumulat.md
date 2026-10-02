# Data and methods - Partial relationships: accumulated local effects (ALEs)

The relationships of VOD to the predictors are examined via accumulated
local effect (ALE) plots (Apley and Zhu,
2020). Like the commonly used partial dependence plots
(PDPs; Friedman, 2001), they show the marginal effect
of a single predictor on the model predictions. This marginal effect is
reflected in the local gradient of the ALE plot; for example, a positive
gradient indicates that an increase in the investigated predictor should
lead to an increase in the predicted model outcome, all other predictors
being equal. While both techniques take into account all other predictors to
approximate the underlying relationship with the single investigated
predictor, ALE does not combine each plotted predictor value with all
possible combinations of the other predictors. Especially for correlated
predictors, ALE plots are therefore more robust than PDPs
(Kuhn-Régnier et al., 2021), as unlikely
and unrealistic feature combinations are prevented. This is achieved by
defining evenly spaced quantiles across the range of the examined
predictor. Each quantile is then used with only the closest existing
combinations of the other predictors to calculate the marginal
effects. The ALE plots were generated from the final models, where all
available data were used for training. Thereby, relationships outside of the
5th and 95th percentile have to be interpreted with caution due to the
smaller sample size supporting these results.

To quantify the influence of the predictors on the target variable
(sensitivities), we calculated the amplitude of the ALE curve (ΔA) as the difference between the maximum and minimum of the curve. A
restriction of the ALE plots by the 5th and 95th percentile leads to
slightly smaller ALE amplitudes but to the same conclusions as based on the
maximum–minimum amplitude which offers the opportunity to exploit the
results based on the whole data sample size.

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
