# Introduction

Over the last century, the global water withdrawal grew 1.7 times faster than the population (FAO, 2006). This aggravates the concern over the sustainability of water use as the demand for agricultural uses continues to increase (Foley et al., 2011; FAO AQUASTAT http://www.fao.org/nr/water/aquastat/water_use/index.stm, last access: 20 May 2021). The strong impact of irrigation on the global water budget is highlighted by many studies, and it has been estimated that about 87 % of the global fresh water withdrawals have been used for agriculture (Douglas et al., 2009). Accordingly, the quantification of irrigation on a regional to global scale has become a hot research topic.

Correctly quantifying irrigation in Earth system models can serve two purposes. On the one hand, it can help improve water management (Le Page et al., 2020, Bretreger et al., 2020); on the other hand, it allows us to quantitatively assess its effects on the terrestrial water, carbon, and energy cycles (Haddeland et al., 2007; Breña-Naranjo et al., 2014; Hu et al., 2016; Qian et al. 2020). Indeed, results of large-scale irrigation studies using land surface models (LSMs) have demonstrated that irrigation increases soil moisture and evapotranspiration (ET) and, consequently, latent heat flux with a decrease in sensible heat flux (i.e. Badger and Dirmeyer, 2015; Lawston et al., 2015; Ozdogan et al., 2010).

Despite the significant impact of irrigation on the water and energy cycles, its simulation within LSMs is not yet common practice (Girotto et al.,
2017). In earlier studies, attempts to simulate irrigation in LSMs have relied on different
parameterizations of well-known irrigation systems (like sprinkler, flood, and drip systems; Ozdogan et al., 2010; Evans and Zaitchik, 2008), making
simplified assumptions. For instance, in Ozdogan et al. (2010), irrigation water is not withdrawn from a source (such as a river) but instead added
as fictitious rainfall. In contrast, Nie et al. (2018) accounted for source water partitioning, albeit only partially, by considering groundwater
irrigation. Irrigation is normally applied when soil moisture drops below a user-defined threshold (Ozdogan et al., 2010) and is typically dependent on the soil properties obtained via soil texture maps.

Moreover, LSMs equipped with irrigation schemes need to be provided with auxiliary information about crop types and whether or not the crops are
irrigated. This is because different crop types are characterized by different rooting depths, which means they require more or less water to restore root zone field capacity. This information is normally gathered from static maps derived from statistical analysis and/or remote sensing (Ozdogan
et al., 2010; Monfreda et al., 2008; Salmon et al., 2015) collected during specific historical periods, which are normally different to the desired
period of analysis. It is thus clear that the modelling of irrigation is subject to many simplifying assumptions, which span from neglecting the
year-to-year crop variability and the irrigation system used to the definition of irrigation application times based on water availability and crop conditions rather than actual farmer decisions.

Remote sensing (RS) technologies offer the opportunity to observe the Earth's surface and its changes directly and, hence, are potentially able to
monitor irrigated lands worldwide (Ambika et al., 2016; Gao et al., 2018; Bousbih et al., 2018; Bazzi
et al., 2019; Le Page et al., 2020; Dari et al., 2020). In the last decade, some authors used visible and near-infrared RS observations jointly with
in situ data collected from inventories to map areas equipped for irrigation (Ambika et al., 2016; Ozdogan and Gutman, 2008). S. V. Kumar
et al. (2015) were the first to propose the use of coarse resolution satellite microwave (MW) sensors
to detect irrigation. The authors compared different coarse-scale active and passive MW surface soil moisture (SSM) retrievals with SSM simulations
from the Noah LSM (version 3.3; Ek et al., 2003) without activating an irrigation scheme over a continental USA domain. Areas where the distributions of model and RS data sets deviated (based on a Kolmogorov–Smirnov test) were assumed to be irrigated. Even though some of the products showed a potential ability to detect irrigation, the authors concluded that the spatial mismatch between the satellite footprint and the irrigated fields, radio frequency interference (RFI), vegetation, and topography could all deteriorate the accuracy of the results. Similar conclusions were found over the same area by Zaussinger et al. (2019), who compared coarse-scale satellite SSM products with soil moisture predictions from the Modern-Era
Retrospective analysis for Research and Applications, version 2 (MERRA-2) in the absence of precipitation, and Escorihuela and Quintana-Seguí (2016), who
additionally compared a downscaled version of the Soil Moisture and Ocean Salinity (SMOS) mission SSM to SURFEX LSM simulations. Brocca et al. (2018),
Jalilvand et al. (2019), and Dari et al. (2020) used a conceptually different approach, with the same coarse scale MW SSM products, and estimated
irrigation by directly inverting a simple water balance equation (Brocca et al., 2014).

The Copernicus Sentinel-1 satellites (Sentinel-1A and Sentinel-1B) offer a new perspective for agricultural applications thanks to the finer spatial
resolution (up to 10–20 m) of the synthetic aperture radar (SAR) backscatter (σ0) data. For instance, Gao et al. (2018) proposed an
approach to map irrigated lands over the Urgell region in Catalonia (Spain), and Le Page et al. (2020) proposed a methodology to detect irrigation
timing in southwestern France by comparing the SSM signal at the plot scale, derived using Sentinel-1 σ0 and NDVI from Sentinel-2 (El Hajj
et al., 2017), with a water budget model forced by Sentinel-2 optical data for the detection of irrigation timing.

Despite the high potential demonstrated by RS in detecting, mapping, and quantifying irrigation, the uncertainties of the satellite retrievals, the
relatively low revisit time of high-resolution active MW products, and the too coarse spatial resolution of passive MW products with respect to the
mean size of irrigated fields represent main limitations for irrigation information retrieval (Romaguera et al., 2010; La Page et al., 2020). Data assimilation (DA) could reduce some uncertainties by optimally integrating LSM estimates and RS
observations. Indeed, the LSM estimates resolve processes at desired spatiotemporal scales, while the RS observations can track, in a more realistic way, human processes like irrigation and their interactions with the water and energy cycles. Contrasting LSM simulations with RS observations offers an opportunity to correct for unmodelled processes or missed events, such as irrigation (S. V. Kumar et al., 2015; Girotto et al., 2017). More generally, DA of satellite-based observations has shown the potential to update soil moisture (De Lannoy and Reichle, 2016; Kolassa et al., 2017) and vegetation (Albergel et al., 2018; Kumar et al., 2020), and important impacts have been reported over agricultural areas (Kumar et al., 2020).

The assimilation of MW RS observations in LSMs often involves retrieval assimilation. However, assimilating retrievals (i.e. SSM or vegetation
optical depth rather than MW brightness temperature or σ0 measurements) can be problematic as the retrievals may have been produced with ancillary data that are inconsistent with those used in the LSM (De Lannoy et al., 2016). This is particularly true for passive MW retrievals, while active MW retrievals generally rely on change detection methods that lack land-specific ancillary information altogether. An alternative approach,
which we follow in this study, is to directly assimilate MW observations and equip the LSM with an observation operator that links the land surface
variables of interest (e.g. soil moisture and vegetation) with RS data. This allows us to obtain consistent parameters and to reduce the chance of
cross-correlated errors between model states and corresponding geophysical satellite retrievals. The direct assimilation of MW observations has
already been demonstrated successfully for the update of soil moisture by using brightness temperature (Tb) derived from the SMOS and SMAP (Soil Moisture Active Passive) missions (De Lannoy et al., 2016;
Carrera et al., 2019; Reichle et al. 2019), as well as using radar σ0 from ASCAT (Advanced Scatterometer; Lievens et al., 2017b), and σ0 from Sentinel-1 in synergy with SMAP Tb (Lievens et al., 2017a). However, to our knowledge, none of these studies considered the joint updating of soil moisture and vegetation, and none specifically focused on the performance over irrigated areas. The σ0 from Sentinel-1 contains information on both soil moisture (Zribi et al., 2011; Liu and Shi, 2016; Li and Wang, 2018; Bauer-Marschallinger et al., 2018) and vegetation (Vreugdenhil et al., 2018, 2020), and assimilating this data could allow us to update both soil moisture and vegetation in a land data assimilation system and, in doing so, correct for missed irrigation events.

To that end, the LSM needs to be coupled to a backscatter forward model as an observation operator. Different SAR σ0 models have been
proposed to simulate the backscattering contributions of soil and vegetation (Attema and Ulaby, 1978; Oh, 2004; Zribi et al., 2005; Bai et al.,
2015; Baghdadi et al., 2017). Most commonly used, the Water Cloud Model (WCM hereafter) developed by Attema and Ulaby (1978) is a σ0 model
that represents the vegetation canopy as a homogeneous cloud containing randomly distributed water droplets. In order to use the WCM as the forward
operator in a σ0 data assimilation system, it first needs to be calibrated to account for biases between the LSM simulations and the
satellite observations. However, calibrating a WCM to simulate σ0 over irrigated areas is not a straightforward process, and it represents
a key research problem if the same σ0 signal is used for the calibration of WCM parameters and later for assimilation and updating of the state. In fact, if the objective is to assimilate radar σ0 to realistically inform the model about irrigation applications, the WCM parameters have to maintain a certain degree of independence from the irrigation signal contained in the observed σ0 as, otherwise, the assumption of uncorrelated errors between model and observations typical of classical Bayesian-based filters is violated. More specifically, if the LSM provides unrealistic simulations as input (i.e. the absence of irrigation), then the WCM calibration with observed σ0 would compensate for this
bias. This would, in turn, lead to a biased backscatter model with undesirable calibrated parameters for the subsequent data assimilation
experiments. Therefore, different strategies can be adopted, for instance by calibrating the model during non-irrigated periods or over non-irrigated
areas or equipping the LSM with an irrigation module that makes the WCM less constrained by inconsistencies between simulated and observed σ0 during irrigation periods. The efficacy of these strategies has, so far, never been explored.

The main objective of this study is to simulate radar σ0 using a LSM coupled with a WCM and to provide solutions and recommendations for the
optimization of the WCM as an observation operator. This is a major stepping stone towards the development of a reliable system for the assimilation of high-resolution Sentinel-1 σ0 observations over irrigated areas. Additionally, we aim at the following:

testing the ability of a sprinkler irrigation system coupled with a LSM to simulate irrigation so as to highlight the potential and limitations of such a tool to optimize a backscatter forward operator over heavily irrigated areas
demonstrating that Sentinel-1 σ0 observations contain valuable information to improve both SM and vegetation predictions over
irrigated land (i.e. soil moisture and vegetation consistent with human alterations in the water cycle due to intensive irrigation).

The analysis is carried out over the Po Valley, one of the most important agricultural areas in Italy and also one of the more intensively
irrigated areas in Europe (water withdrawal in the Po basin is estimated to be 20.5 billionm3yr-1, of which 16.5 billion m3yr-1 is withdrawn for irrigation; Po River Watershed Authority, 2016). We use the Noah-MP v.3.6 LSM (Noah-MP hereafter) as part of the NASA Land Information System (LIS) framework, together with the WCM from Attema and Ulaby (1978), for the simulation of both σ0 vertical send and receive (VV) and vertical send and horizontal receive (VH) polarization. Level 1 Sentinel-1 σ0 observations are used to calibrate the WCM at 1 km resolution, using simulated SSM and leaf area index (LAI) estimates from Noah-MP. The WCM is calibrated for a total of four calibration experiments for each polarization, namely (1) with or without activating an irrigation scheme within Noah-MP and (2) considering two different cost functions. Specifically, we want to demonstrate that activating an – even poor – irrigation scheme is needed to obtain long-term unbiased σ0 simulations and uncorrelated errors between the WCM and Sentinel-1, and that the calibration process can be sensitive to different cost functions.

The paper is organized as follows. Section 2 provides information on the study area, the selected data sets, and methods used for our analysis. Specifically, Sect. 2.3 and 2.4 provide a detailed description of the Noah-MP LSM and the WCM. Section 2.5 describes the cost functions used for the WCM calibration, while Sect. 2.6 is a description of the experimental set-up designed for the calibration. Finally, Sect. 2.7 provides insights on the Noah-MP and WCM evaluations. Section 3 presents the results, with an assessment of the Noah-MP evaluation, both regional (Sect. 3.1) and over the test sites (Sect. 3.2). The WCM calibration and evaluation results are described in Sect. 3.3 and 3.4, respectively. We provide a discussion in Sect. 4, while conclusions are reported in Sect. 5.

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
