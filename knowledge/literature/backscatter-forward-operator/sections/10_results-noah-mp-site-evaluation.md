# Results - Noah MP site evaluation

The Noah-MP SSM was evaluated at the Budrio test site field 2 (Fig. 1a), using the daily reference PGR SM for the year 2017. Comparisons between the
SSM simulations of the natural and irrigation runs with in situ PGR SM are shown in Fig. 6a, while daily observed irrigation and
rainfall data are compared with daily irrigation simulations in Fig. 6b. Soil moisture data are plotted at their original temporal resolution (i.e.
daily) to illustrate an issue related to the irrigation timing, namely that SSM simulations in Fig. 6a show the ability of the sprinkler irrigation scheme to simulate irrigation in the summer season, but there is an inevitable problem in reproducing the correct timing and magnitude of irrigation. Indeed, the total amount of simulated irrigation is 604 mm for the 2017 summer season, which overestimates the total amount of observed irrigation that is 349.5 mm. Furthermore, the model simulations not only miss irrigation but also suffer from erroneous precipitation input, such as on the 11 July 2017, where the observed precipitation event in the growing season is not found in the model SSM simulations. In any case, biweekly Pearson R between simulated SSM and in situ PGR SM are higher for the irrigation run than for the natural run (0.54 vs. 0.42), suggesting the benefit of activating irrigation.

For the Budrio field 1 test site (Fig. 1a), two summer seasons of irrigation data were available. To assess the irrigation information contained in
Sentinel-1 σ0 observations (and the potential added value for a forthcoming DA experiment), we compared biweekly values of Sentinel-1
σ0 VV and σ0 VH with SSM estimates from both the natural run and irrigation run (Fig. 7a) for this site. Although the
σ0 VV is generally used to retrieve SSM (Wagner et al., 2013; Gruber et al., 2013;
Bauer-Marschallinger et al., 2018), data at both polarizations were analysed in order to understand the soil contribution contained in the two
signals. Information related to the irrigation periods are shown in Fig. 7c, where irrigation observations and irrigation simulations from Noah-MP are
compared. Figure 7a indicates that the SSM simulations are better reflected in the Sentinel-1 σ0 VV than σ0 VH data, particularly
when irrigation is simulated (orange line). The SSM estimates from the natural run (light blue line) agree poorly with the Sentinel-1 data,
with Pearson R values equal to 0.32 and -0.1 for the σ0 VV (blue dots) and σ0 VH (cyan dots), respectively. When irrigation is
simulated, the σ0 VV data better follow the modelled SSM signal (Pearson R of 0.53), especially during the summer irrigation season when
the backscatter signal remains higher and stable. On the other hand, σ0 VH seems to provide poor performances, also when irrigation is
simulated, with a Pearson R value equal to 0.06, confirming findings by Baghdadi et al. (2017), which highlighted how the use of VH alone to retrieve
SSM is suboptimal when vegetation cover is well developed.

In Fig. 7b, the Sentinel-1 σ0 CR (VH/VV) is compared with Noah-MP LAI from the natural run (light-blue line) and
irrigation run (orange line). The performance in terms of Pearson R decreases from 0.76 to 0.65 when the irrigation is simulated. This
is due to a time shift of the Noah-MP LAI growing season in the irrigation run. PROBA-V LAI (in green) was additionally compared with the
Sentinel-1 CR (blue dots), showing a Pearson R of 0.84. The higher agreement between the RS products (Sentinel-1 and PROBA-V) highlights the strong relation between the σ0 CR and the vegetation signal, suggesting a potential benefit of the Sentinel-1 assimilation for correcting the simulated vegetation phenology.

Finally, Fig. 7c shows a comparison between 15 d accumulated millimetres of simulated irrigation (orange) and observed irrigation (green). The
Pearson R is equal to 0.77, indicating that the sprinkler irrigation scheme can provide acceptable irrigation estimates at this temporal resolution
though absolute irrigation amounts are overestimated.

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
