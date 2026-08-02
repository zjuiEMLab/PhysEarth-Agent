# Results - WCM calibration

The WCM parameters A and B (vegetation parameters) and C and D (soil parameters) were calibrated for each grid cell separately, during the
reference period of January 2017 to December 2019 (Fig. 3), using daily σ0 simulations and observations. The calibrated parameters related to the entire study area for each of the eight experiments are shown in Fig. 8, where the blue (left) parts of the violin plots identify experiments of the
natural run, while the orange (right) parts of the violin plots are related to the irrigation run.

Generally, the J calibration provides parameter distributions closer around their prior guess as compared to the KGE calibration for which
the distributions are often multimodal, especially for the C and D parameters (i.e. Fig. 8d and h). This is due to the prior parameter penalty, which is included in the Bayesian solution but not in the KGE. In general, the calibration of the two functions using the natural run provides wider distributions between the lower and upper boundaries for the A vegetation parameter, with a high number of grid cells characterized by A values higher than 0.1 (see KGE-VV natural and J-VV natural experiments in Fig. 8a and e, respectively). Conversely, the irrigation run provides A distributions more skewed to the lower boundary (being also the guess value in each calibration experiment), with a smaller number of grid cells characterized by high A values compared to the natural run. In a preliminary sensitivity study (not shown), we observed that high values of the vegetation parameters A and B, as obtained for the natural run, have the tendency to generate high peaks in the simulated σ0 during the growing season. Indeed, in the summer, the SSM natural signal is low and not consistent with the Sentinel-1 σ0, which observes irrigation. In order to follow the temporal dynamics of the Sentinel-1 σ0, the calibration algorithms attribute a relatively higher weight (higher A values) to the LAI than to SSM to compensate for the underestimated SSM in the natural run. In contrast, the irrigation run provides vegetation parameter distributions more skewed to the lower boundaries (see also Sect. 3.4.2). The C and D parameter distributions feature a better sensitivity to soil moisture dynamics using the irrigation run input data, which is the expected behaviour, considering that they describe the σsoil0. This is true especially when using the J cost function (see parameters distributions for the J-VV natural and for the J-VV irrigation
experiments in Fig. 8g and h), which results in more spread in the calibrated C and D distributions for the irrigation simulations (especially in VV polarization), whereas the mode of the C and D parameter distributions for the natural experiments is more shifted to the upper and lower boundaries, respectively.

Figure 9 shows the spatial pattern of the parameters over the study area to better understand the differences between the natural and
irrigation calibration runs. We found a connection between the WCM parameters distribution and model parameters, particularly with the HWSD
soil texture map (shown in Fig. 2). For both the J-VV natural and J-VV irrigation experiments, the activation of the irrigation
scheme reduces the dependency of the vegetation-related parameters A and B on soil texture (see Fig. 9a and b for the J-VV natural and
Fig. 9e and f for the J-VV irrigation experiment). This is also shown in the parameter maps of the KGE calibration experiments
(Fig. S5). Additionally, the activation of the irrigation scheme, more realistically, shifts the soil texture dependency towards the
soil parameters C and D (Fig. 9g and h), highlighting another important reason for simulating irrigation.

Finally, the different polarization experiments generally provided similar distributions for the vegetation A and B parameters and the D soil
parameter. The largest differences between the VV and VH polarizations are identified for the C parameter distributions. This is due to the lower
σ0 signal associated with the VH polarization. Indeed, Fig. 8c and g are characterized by higher values of C in the VV polarization, as
compared to the distributions for VH polarization in Fig. 8k and o. In the latter, the C–VH distributions are generally more skewed to the lower
boundary of the parameters, with median values closer to the defined guess parameter value.

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
