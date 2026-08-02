# Conclusions

With the specific focus on intensively irrigated land, the main objective of this work was to define the optimal calibration of the WCM as an observation
operator for the future ingestion of Sentinel-1 backscatter into the Noah-MP LSM via DA. In this context, we additionally aimed at (1) unveiling the
strengths and limitations of irrigation simulation in LSMs from the perspective of a calibrating the WCM and (2) identifying the potential
irrigation-related information contained in the Sentinel-1 σ0 observations to improve soil moisture and vegetation states, as well as
irrigation estimates, in a calibrated DA system.

To reach these objectives, we coupled the Noah-MP with a sprinkler irrigation scheme within LIS and performed two different simulation experiments, i.e. one with and one without irrigation (i.e. natural and irrigation runs). Moreover, we coupled a WCM with Noah-MP and tested different
calibration options to prepare for the optimal, future, assimilation of σ0 VV and VH to update both soil moisture and vegetation states.

The main conclusions drawn from our evaluation are as follows:

Over highly irrigated areas, the simulation of irrigation in LSMs helps to provide better soil moisture and vegetation simulations, which can be used with benefit as input for the WCM calibration. However, the performance of the irrigation simulations is limited by the simplistic model parameterization of this human process and the necessity for considering realistic and updated land cover information (e.g. crop types). This results in poor simulations of the irrigation timing and quantities, as well as vegetation dynamics.
The Sentinel-1 σ0 observations contain useful information about SSM and vegetation over highly irrigated areas. This information can be exploited to overcome LSM deficiencies in simulating soil moisture and vegetation over highly irrigated regions, e.g. when irrigation is unmodelled or poorly modelled because of uncertainties due to crop types, irrigation timing, and farmer agricultural practices. In particular, there is a high chance that the assimilation of Sentinel-1 σ0 can help in correcting LAI dynamics.
The optimal assimilation of Sentinel-1 σ0 into a LSM must rely upon a well-calibrated WCM as the observation operator to provide unbiased σ0 simulations with a minimal chance of having error cross-correlations between model and observations, while ensuring a realistic operator controllability or realistic connection between observed signals and land surface state variables. We demonstrated that calibrating the WCM by including irrigation modeling consistently led to a better agreement with Sentinel-1 σ0. The modeling of irrigation in the LSM simulations, even if not done optimally, avoids that the WCM calibration compensates for LSM biases.
We demonstrated that the WCM calibration with a Bayesian cost function, including a prior parameter constraint, provides the optimal WCM parameters, is able to generate the lowest bias in the σ0 simulations for both VV and VH. Although slightly higher correlations are obtained when using a KGE cost function, unbiased estimates are particularly beneficial for DA, as this minimizes the chance of potential error cross-correlation between model estimates and observations.

This study improves the understanding of the LSM limitations in simulating irrigation and highlights the information content in Sentinel-1
σ0 data. A natural follow-up of this study is the assimilation of σ0 observations within Noah-MP, which should enforce our tested
evidence and provide new insights for a more realistic description of the water and carbon cycles over irrigated areas.

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
