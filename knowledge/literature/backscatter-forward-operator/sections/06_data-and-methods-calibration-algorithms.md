# Data and methods - Calibration algorithms

We considered the following two different objective functions to optimize the A, B, C, and D parameters:

A Bayesian solution, which minimizes the sum of squared errors (SSEs) between σ0 observations from Sentinel-1 and WCM simulations. The SSE Bayesian calibration solution aims at identifying the optimal parameter vector α, which maximizes the probability of the resulting σ0 simulations p(y^-)=p(y^-|α)p(α), where p(α) is the prior parameter distribution and p(y^-|α) is the likelihood. Starting from the assumption of an independent and identically distributed normal error model, the posterior probability can be maximized by maximizing the following:p(y^-|α)p(α)=∏iNi1si2πexp⁡-(y^-y^-)i22si2⋅∏jNα1sj2πexp⁡-(α0-α)j22sj2,i.e. the combination of the likelihood and a prior parameter constraint. The latter helps in reducing problems of equifinality. In Eq. (5),
y^ represents the observed σ0, y^- is the simulated σ0, i is the time step, and si is the standard deviation of the residual differences between the observed and simulated σ0 values for Ni time steps. Nα is the number of parameters to be calibrated, α0 is the prior parameter constraint, and the parameter deviation is limited by sj2, which is the variance of a uniform distribution sj2=(αmax⁡,j-αmin⁡,j)2/12, with determined boundaries of the parameters [αmin⁡,αmax⁡]. The maximum likelihood solution is found by minimizing the following cost function J:J=∑iNiln⁡(si)+(y^-y^-)i22si2+∑jNα(α0-α)j22sj2=J0+Jα,where si is assumed to be constant in time and represented by a target accuracy of 1 dB, leaving the SSEs in the first term of J0 to
minimize. The second term (Jα) constrains the optimal solution by avoiding strong deviations from initial parameter guesses.
A solution that maximizes the Kling–Gupta efficiency (KGE; Gupta et al., 2009). Even though this objective function does not ensure Bayesian optimality, it is a widely used metric which could help to better tune the dynamic σ0 behaviour, as follows:KGE=1-(r-1)2+〈y^-〉〈y^〉-12+s[y^-]/〈y^-〉s[y^]/〈y^〉-12.
The KGE formulation embeds three terms. (1) The first term accounts for the Pearson correlation (Pearson R) between the observed
(y^) and simulated (y^-) σ0 time series. (2) A second term accounts for the bias, where the long-term mean is represented
as 〈.〉. Finally, (3) there is a term accounting for the variability in the simulated and observed signal through the use of the
standard deviation s[.]. KGE = 1 indicates a perfect agreement between simulations and observations. Note that KGE
redistributes the weight of the bias, variance, and correlation components compared to J in Eq. (6), which can help in reducing differences between
simulated and observed σ0, and also in terms of temporal dynamics, during the calibration. On the other hand, in the KGE, cost function parameters are not constrained by prior values α0. This could possibly result in overfitting and a larger prediction uncertainty.

The particle swarm optimization (PSO; Kennedy and Eberhart, 1995) was used to minimize J and maximize KGE. For our case study, the PSO
parameters were set as in De Lannoy et al. (2013).

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
