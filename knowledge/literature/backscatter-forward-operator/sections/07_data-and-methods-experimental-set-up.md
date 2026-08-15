# Data and methods - Experimental set-up

An optimal DA system requires long-term unbiased σ0 simulations (with respect to the assimilated observations). The risk, over an
intensively irrigated area, is that an unmodelled irrigation signal would manifest itself as a predominant bias in the σ0 simulations. The
calibration would then inadvertently correct for this supposed bias (i.e. the irrigation signal), thus preventing the DA system from propagating the
missing irrigation signal from the observations into the model. Even though existing irrigation schemes are evidently unrealistic and inaccurate, we
conjecture that using such a scheme when calibrating the WCM will more likely yield optimal WCM parameters than when neglecting irrigation.

To that end, we considered two different experiment lines (referred to as natural and irrigation, respectively) that produced a total of eight different σ0 simulation runs (see Fig. 3). The natural experiment line differs from the irrigation line by
the activation of an irrigation module in Noah-MP, and both are subjected to the calibration algorithms described in Sect. 2.5. The natural
line was used as a diagnostic experiment against which to compare irrigation, which, according to our initial hypothesis, should minimize the
impact of the irrigation signal contained in the σ0 observations on WCM parameters.

As a first step, a model spin up was performed, starting in January 1982 and ending in December 2014. Then, a study period from January 2015 to December 2019 was selected for the different model runs, based on the availability of the processed Sentinel-1 σ0 and reference irrigation
data (see Sect. 2.1 and 2.2). Daily surface model and irrigation outputs were produced. Considering that the main source of irrigation in the Po Valley is related to surface water abstraction, the sprinkler irrigation scheme did not account for groundwater withdrawals (see Nie et al., 2018).

The A, B, C, and D parameters of the WCM (see Sect. 2.4) were fitted separately to Sentinel-1 σ0 VV and σ0 VH observations during the
period of January 2017– December 2019. Following previous literature (Lievens et al., 2017b; De Lannoy et al., 2014, 2013), we performed a grid-cell-based calibration to account for the spatial variability in the simulated and observed σ0 signals that stems from specific features
within the observed footprints and from the soil and vegetation parameterization of Noah-MP. Both the calibration using the SSEs with prior
constraint (Bayesian J) and the KGE were applied to the natural and irrigation runs, providing eight different experiments named
J-VV natural, J-VH natural, J-VV irrigation, J-VH irrigation, KGE-VV natural, KGE-VH natural, KGE-VV irrigation, and KGE-VH irrigation.

Lower and upper boundaries and prior guess values of the WCM parameters were defined based on the work of Lievens et al. (2017b) and on a
sensitivity analysis (not shown here). The selected values are displayed in Table 1. Finally, it should be noted that all the calibration experiments
were realized by considering daily values of σ0 simulations and observations.

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
