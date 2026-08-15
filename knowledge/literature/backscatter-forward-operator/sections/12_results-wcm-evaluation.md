# Results - WCM evaluation

## Regional evaluation

The regional evaluation of the calibration experiments was carried out during the period from January 2015 to December 2016 for agricultural areas within
the study domain (almost 15 000 km2), by comparing biweekly σ0 simulations with Sentinel-1 σ0 in terms of
Pearson R, KGE, and bias. The distribution of the evaluation metrics for the eight experiments is shown in Fig. 10. A comparison of the
metrics for the irrigation and natural runs confirms better results when irrigation is activated, with violin plots skewed towards
more positive values for both KGE and Pearson R. When stratified by the cost function, the Pearson R distribution in Fig. 10a–d indicates a
slightly higher performance for the KGE (Fig. 10a and c) than for J (Fig. 10b and d). In terms of the KGE score, simulations are naturally closer to the observations when the KGE cost function is used. On the other hand, in terms of bias, generally better performances are found when the Bayesian solution is used (Fig. 10i–l). The latter is particularly evident for the VH polarization when comparing the KGE-VH and
J-VH experiments (Fig. 10k and l).

The VH simulations exhibit a better performance in the irrigation run than the VV simulations (Fig. 10c and d and 10a and b). Indeed, considering all the statistical scores, the VV polarization is characterized by more similar distributions between the
natural and irrigation run for both cost functions. This suggests a higher sensitivity of the VH polarization to the change in vegetation introduced by irrigation, confirming the Sentinel-1 σ0 VH to be strongly influenced by irrigation, as witnessed by the larger
score improvement obtained for the calibration experiments KGE-VH irrigation (Fig. 10g) and J-VH irrigation
(Fig. 10h) when compared to the natural run experiments.

In summary, (i) VH polarization is more sensitive to the change in the cost function and input data (irrigation or natural run) than
VV polarization, likely due to its higher sensitivity to vegetation change (Vreugdenhil et al., 2018; Macelloni et al. 2001), which, in the area, is
related to the crop development after irrigation, and (ii) the combination of J with the activation of the irrigation scheme is able to provide the best
unbiased estimates of simulated σ0 for both VV and VH (J-VV irrigation and J-VH irrigation experiments) at the
price of generally lower correlations (compared to the KGE cost function). This is, however, beneficial for DA as it minimizes the chance of
potential error cross-correlation between model estimates and observations. Indeed, the match of the temporal dynamic of the signals induced by the
correlation term is stronger in the KGE than in J, which, additionally, includes a parameter constraint. The higher weight of the correlation
in the KGE cost function can negatively impact the parameter calibration, even when irrigation is turned on in Noah-MP, because the simulated
irrigation applications are, in general, not temporally consistent with those seen by Sentinel-1 (see Fig. 6).

## In situ evaluation

The WCM simulations are further analysed in detail at the Faenza test site (specifically for the San Silvestro field) because it has a larger extent
than the Budrio site (see Fig. 1), although the same overall conclusions were found for Budrio. Figure 11 shows the simulated and observed σ0
time series for the different experiments highlighted in Fig. 3, and Table 2 summarizes the statistics (i.e. Pearson R, KGE and bias) of each
experiment.

The agreement between simulated and observed σ0 measured by the Pearson R and KGE in Table 2 generally gives better performances after calibration with the KGE cost function than with the J cost function. An example is in the higher correlations found for the
KGE-VH irrigation experiment as compared to the J-VH irrigation (Fig. 11b and d, respectively). On the other hand, in
terms of bias, the cost function J significantly outperforms the calibration with KGE in all experiments with surprisingly comparable values between natural and irrigation runs (Table 2).

One undesirable feature of natural runs is the presence of high σ0 peaks during the summer, clearly detectable over the Faenza test
site, especially in the VH polarization, which are less evident in the irrigation run (see Fig. 11b and d). A similar behaviour was found for
Budrio (not shown). These peaks are likely attributed to the poor estimation of model vegetation parameter values, previously discussed in Sect. 3.3,
when the WCM attempts to compensate for bias in SSM and vegetation input, i.e. input that is not consistent with observations over irrigated
areas. This is particularly true for the KGE calibration, which does not use a prior parameter constraint. In contrast, the J calibration
still provides reasonable σ0 simulations that are closer to the ones of the irrigation run due to the Bayesian technique itself.

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
