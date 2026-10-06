# Data and methods - Noah-MP LSM and WCM evaluations

The validation aims at (i) evaluating the performance of Noah-MP in simulating irrigation, soil moisture, and vegetation, and the ability of the WCM to simulate radar σ0, and (ii) unveiling the information about irrigation contained in Sentinel-1 radar σ0 in order to assess its
potential to improve both soil moisture and vegetation representation within Noah-MP.

The evaluation was carried out on both the regional scale (i.e. over the entire study area) and on the two selected sites, Faenza (small district
scale) and Budrio (plot scale), where irrigation data were available. Considering the lack of benchmark data for irrigation evaluation (Foster et al.,
2020), we decided to use in situ data for the small Budrio fields spatial scale (i.e.
0.45–049 ha), even though model simulations are made at a much coarser resolution (i.e. ∼ 1 km). We are aware that differences in the spatial scale can increase the uncertainty of our evaluation, but the 0.01∘ LSM spatial resolution is still a good compromise for an analysis at the regional, small district, and plot scale. Additionally, limitations are partly reduced by the low chance of including non-irrigated fields within the 1 km LIS grid cells within the Po Valley, as the latter is almost entirely irrigated (Salmon et al., 2015). We compared Noah-MP (with and without using the irrigation module) SSM and LAI simulations with satellite SSM from ASCAT and SMAP and LAI from PROBA-V, respectively, during the period 2015–2019. Furthermore, these land surface simulations were compared to Sentinel-1 σ0 to understand how much of the SSM and LAI signal was captured by Sentinel-1.

As the irrigation timing is often driven by the stakeholders' turns to withdraw water and by water availability rather than by the conditions of the
soil and crops themselves, the comparisons between simulated SSM and satellite SSM were carried out by aggregating the two variables over a biweekly time window. On the other hand, the LAI from Noah-MP was aggregated to 10 daily values in order to match the PROBA-V LAI values. We used the Pearson R for SSM and LAI evaluation. For SSM, we also computed the root mean square error (RMSE), calculated considering the original temporal
resolution of the satellite products, while for LAI, we also tested the ratio bias, i.e. the ratio between the long-term mean of the simulations and
the long-term mean of observations. In particular, this additional score for LAI was used to provide a further evaluation of the ability of the
Noah-MP to simulate crop phenology during the irrigated vs. non-irrigated periods so as to not rely solely on the evaluation of temporal dynamics,
which, due to the uncertainty in the Noah-MP crop type parameterization, could be affected by time shifts in the LAI climatology. This
parameterization uncertainty comes from the lack of knowledge of the spatial crop type information and is difficult to reduce without additional
information. Our assumption is that the radar σ0 assimilation can also correct for this with future data assimilation.

Following Vreugdenhil et al. (2018) and Vreugdenhil et al. (2020), Noah-MP LAI and PROBA-V LAI were also compared with the Sentinel-1
σ0VH/σ0VV cross ratio (CR), which was demonstrated to have a high agreement with the vegetation signal. Though the
σ0VH was demonstrated to increase with the vegetation signal (Macelloni et al., 2001), the CR will be more sensitive to vegetation
changes as the ratio is less sensitive to changes in soil moisture and soil–vegetation interaction (Veloso et al., 2017; Vreugdenhil et al., 2020).

To evaluate WCM simulations, we used biweekly values of σ0 simulations and observations considering a 2-year period independent from the
calibration period (i.e. 2015–2016). Statistical metrics, such as grid-based temporal Pearson R, KGE, and bias, were calculated between Sentinel-1
σ0 and calibrated WCM simulations. The analysis of the parameters was restricted to the cropland area as no difference between our
experiment lines exists over other land cover types (i.e. the irrigation module is active only over grid points classified as crop).

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
