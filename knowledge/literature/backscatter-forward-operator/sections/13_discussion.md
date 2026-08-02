# Discussion

## Noah-MP irrigation modelling

The Noah-MP LSM, used as input for the WCM calibration, was evaluated in two configurations, either with a sprinkler irrigation scheme activated or
without irrigation (i.e. irrigation run and natural run). Although not all of the Po Valley is irrigated by sprinkler
systems, it most likely still leads to more realistic LSM simulations than not considering irrigation at all.

The main limitation found in the irrigation simulations was related to the irrigation timing and magnitude that was inconsistent with
observations. Although this finding is based on only a single study site, it is very likely that it is a widespread issue within the study area for
several reasons. In LSMs, the irrigation application is driven by the RZSM availability and, consequently, by the soil type and the rooting depth
parameterizations. Moreover, it is also influenced by the accuracy of the meteorological forcings (especially precipitation), which can determine errors in the soil moisture representation. The main reason, however, is
likely that irrigation is often the result of subjective farmer decisions rather than objective rules based on the soil state and crop conditions. In
theory, the irrigation timing issue could be partly solved by using temporally consistent high-resolution crop maps, which should provide a more
realistic information of crop phenology and rooting depth. However, in practice, this is unfeasible over many areas of the world given the absence of this information on a large scale. Also, given that irrigation applications are mainly linked to unmodelled processes, like rotation schedules for farmers to withdraw water, the correct simulation of the timing can be unsolvable when using models only.

Despite the potential problems related to the unrealistic assumptions in the simulation of irrigation, our results demonstrated that even the use of
simple irrigation schemes within Noah-MP can be beneficial. In the regional evaluation, SSM simulations of the natural and irrigation runs were compared with RS SSM from SMAP and ASCAT (Fig. 4) on a biweekly temporal scale. For both products, we found large improvements in temporal Pearson R when irrigation was simulated, which were confirmed by a decrease in the RMSE values over croplands, suggesting that the activation of irrigation modelling provides more realistic SSM estimates. Our findings further confirm the potential of coarse-resolution data sets for providing irrigation-related information over intensively irrigated and relatively large agricultural areas, as was shown by S. V. Kumar
et al. (2015).

While the impact of irrigation was clear in terms of SSM, the regional evaluation of the simulated LAI against the PROBA-V-based LAI provided
contradicting results. In this case, the Pearson R analysis suggested a deterioration of the Noah-MP-simulated LAI when irrigation was activated
over the cropland area. We interpreted this correlation deterioration from the absence of specific information about the crop phenology in the model
parameterization. In practice, information about the specific crop type is not available, and the rooting depth is the sole parameter controlling water
uptake from the soil layers. Additionally, information on sowing and harvest periods are not included in the current version of Noah-MP, while
irrigated areas are defined based on a global data set (Salmon et al., 2015) which can suffer accuracy limitations. Indeed, the absence of annual dynamic information on irrigated fields, the unknown yearly variability of the crop types, and the impact of the meteorological conditions in the stakeholders' decision-making process (i.e. sowing) make the simulation of Noah-MP prone to LAI peak shifts, as compared to observations, when irrigation is simulated. Another important aspect affecting LAI simulations is its sensitivity to root zone soil moisture, which might be more difficult to simulate than SSM during the irrigation season due to larger impacts of the soil texture and transpiration processes along with the high frequency of the wetting and drying phases caused by irrigation events. This results in a significant performance deterioration (often worse than LAI simulations not including irrigation which are mainly driven by seasonality; see Fig. 7). In contrast, irrigation modeling helps to reduce the bias of the LAI-simulated time series, which, in the cropland area, show a significant underestimation when irrigation is not considered.

The limitations found in simulating LAI and vegetation by Noah-MP, even when irrigation was simulated, could potentially be overcome by assimilating
Sentinel-1 σ0 data. To explore this potential, we compared the LAI from both model runs, and from PROBA-V, with the observed Sentinel-1
σ0 CR (VH/VV), which should provide information about the vegetation dynamics (Vreugdenhil et al., 2018, 2020). We found that the
correlation between σ0 CR and LAI from PROBA-V was much higher than that between σ0 CR and the simulated LAI by Noah-MP (see
Fig. 7), suggesting that Sentinel-1 σ0 DA could help to correct poor LAI model simulations. Additionally, a higher correlation was found
between the σ0 VV observations and the simulated SSM when irrigation was turned on than in the absence of irrigation, suggesting that the assimilation of σ0 VV could improve SSM where irrigation is poorly modelled or not modelled. On the other hand, considering the low correlation between the VH signal and SSM in presence of vegetation (Baghdadi et al. 2017), and its close relation with vegetation (Ferrazzoli et al.,
1992; Macelloni et al., 2001), future data assimilation experiments will investigate the contribution
of VH and CR in improving LAI predictions and irrigation quantification.

Finally, biweekly accumulated irrigation estimates in Fig. 7 agree well with real irrigation applications, suggesting that the large-scale LSM
irrigation scheme is helpful for intensively irrigated areas. On the other hand, the poor soil and crop parameterization, along with other unknown
parameters related to the irrigation management (e.g. the farmers can apply more water than actually needed), can cause large biases in these
irrigation simulations. Again, ingestion of radar backscatter data could correct for unmodelled processes. More specifically, Sentinel-1 σ0
could correct (i) for the magnitude and timing of the irrigation simulations and (ii) for Noah-MP irrigation predictions over regions that are not irrigated.

## WCM backscatter simulation

The purpose of the presented WCM observation operator calibration and evaluation was to optimize the parameters for the future assimilation of the
Sentinel-1 σ0 VV and VH into Noah-MP. Such an optimization would ideally minimize the long-term bias between the simulated and observed
σ0 signals. This can be achieved by calibrating the observation operator with long-term observed σ0 prior to data assimilation,
but in this process, it is crucial to avoid potential error cross-correlation between model observation predictions and observations. Furthermore, a
good observation operator should not already compensate for missing processes in the LSM by accepting effective, but unrealistic, optimized
parameters because it would then lose its physically based ability to accurately convert misfits between observations and simulations to LSM updates during the data assimilation.

One way to avoid parameters compensating for erroneous LSM input into the WCM would be to use observed time series of, e.g., LAI. However, LAI products
from different sensors have different biases themselves, which can add bias to the σ0 simulations, and more importantly, replacing simulated
LAI or SSM with external data sets would undermine the possibility of updating these variables in the future assimilation system. Based on that, we
performed the WCM calibration considering the SSM and LAI model input from two different experiments, i.e. a natural run and an irrigation
run, as well as two cost functions, a Bayesian solution J, and a KGE solution, which resulted in four calibration experiments for each polarization (i.e. eight calibration experiments in total).

The calibration experiments using simulations from the natural run as input showed a limited performance and provided presumably bad vegetation parameter estimates, which resulted in unrealistic peaks in the simulated σ0 during the summer when driven by higher modelled LAI during this period. The inclusion of the irrigation within Noah-MP was very beneficial for all the calibration experiments, helping to reduce the bias, increase the correlation with Sentinel-1 σ0, and remove the anomalous σ0 increase during warm periods, especially for the KGE-based calibration. This corroborates our initial hypothesis that, over intensively irrigated areas, the simulation of
irrigation is a mandatory task for an optimal calibration of the WCM. Irrigation modeling, even if only done approximately and perhaps with inaccurate timing, reduces obvious land surface (soil moisture and vegetation) bias and avoids that the WCM needs to compensate for this bias.

Our results show overall higher performance in terms of KGE and Pearson R scores for the KGE-based calibration, whereas the long-term bias
was better reduced for the J-based calibration, which is beneficial in anticipation of future DA. This is because, in the J cost function, there is (i) a target accuracy term which also takes into account the Sentinel-1 observations, where an error is present, and (ii) a parameter deviation penalty based on the prior parameters constraints is used, which prevents parameters from deviating largely from their prior values.

In terms of polarization, we found σ0 VH simulations much more sensitive to the inclusion of the irrigation (vs. non-inclusion) in Noah-MP,
suggesting that observed σ0 VH might also contain much more information about irrigation (via the influence of the vegetation change due to irrigation) than that contained in σ0 VV, which is normally used for SSM retrieval (Vreugdenhil et al., 2020). We believe that the cause of
this is related to a comparatively larger σ0 of vegetation with respect to that of the soil when the crops are well developed. This was also
corroborated by the better agreement between CR and LAI from PROBA-V in one of the study sites mentioned above. Despite this, further investigations
are required to confirm this hypothesis, and DA will certainly help to test this aspect.

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
