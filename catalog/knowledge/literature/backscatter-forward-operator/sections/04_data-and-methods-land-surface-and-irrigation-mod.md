# Data and methods - Land surface and irrigation modelling

## Noah-MP v.3.6

The analysis was carried out using the Noah-MP (Niu et al., 2011) LSM, running within NASA's LIS version 7.2 (Kumar et al., 2008). LIS is a software
framework for terrestrial hydrology modelling and DA, which supports different LSMs that can be conditioned on multiple remote sensing products from active and/or passive microwave sensors. The Noah-MP LSM, which was chosen for this study, is an evolution of the baseline Noah LSM (Mahrt and Ek, 1984; Chen et al., 1996; Chen and Dudhia, 2001), where the main improvements and augmentations are
(1) the presence of four soil layers, (2) up to three snow layers, (3) one canopy layer, which allows us to dynamically simulate the vegetation and to
compute separately the ground surface temperature, (4) a two-stream radiation transfer scheme based on the canopy layer sub-grid scheme, (5) a
Ball–Berry-type stomatal resistance scheme, and, (6) finally, a simple groundwater model with a TOPMODEL-based runoff scheme (Niu et al.,
2005, 2007). The model was set up by selecting four soil layers at depths of 0–10, 10–40, 40–100, and
100–200 cm, a dynamic vegetation model with a Ball–Berry-type canopy stomatal resistance model (Ball et al., 1987), and TOPMODEL-based
runoff.

The parameterization followed the recommended options provided in the LIS documentation
(https://lis.gsfc.nasa.gov/documentation/lis, last access: 30 November 2021). A model
time step of 15 min and a 6 h output interval were selected, together with a spatial resolution of 0.01∘. The meteorological forcings used
for running Noah-MP LSM were obtained from MERRA-2 (Gelaro et al. 2017). The MERRA-2 original spatial resolution of 0.5∘ × 0.625∘ was remapped to 0.01∘ through bilinear interpolation. Land model data and parameters were preprocessed and adapted to the LIS longitude/latitude projection using the Land Surface Data Toolkit (LDT; Arsenault et al., 2018) in order to run Noah-MP at the chosen spatial resolution.

For this study, the default LIS land cover (LC) map from the University of Maryland (UMD) global land cover product (Hansen et al., 2000), based on the
Advanced Very High Resolution Radiometer (AVHRR) data, was replaced with the 2015 global LC map, available from the CGLS at 100 m spatial
resolution (Buchhorn et al., 2020; available at https://land.copernicus.eu/global/products/lc,
last access: 20 May 2021). The CGLS provides dynamic land cover layers at 100 m spatial resolution (CGLS-LC100), obtained by combining
information derived from the vegetation instrument on board the PROBA-V satellite, a database of high-quality LC reference sites, and several
ancillary data sets. For a more detailed explanation of the LC maps generation process we refer to the Algorithm Theoretical Basis Document (ATBD; Buchorn et al., 2020). The 23 classes of the PROBA-V LC map were reclassified to the 14 classes used in the UMD-AVHRR classification supported by LIS. Additionally, the LC map was regridded at 0.01∘ (Fig. 2a) by identifying the most representative class over each LIS grid cell. For
additional information on the reclassification process, we refer the reader to Table S1 in the Supplement. Similarly, the default Food and Agriculture Organization (FAO) Soil Map (FAO, 1971) was replaced by the Harmonized Soil World Database (HWSD v1.21; 1 km; Fig. 2b) and mapped to five soil classes over the study region. Other model preprocessed parameters inputs were (1) the Shuttle Radar Topography Mission elevation data (SRTM30;
30 m spatial resolution); (2) the climatological global Greenness Vegetation Fraction (GVF) data (0.144∘; Gutman and Ignatov, 1998),
derived from 5 years (1985–1989) of normalized difference vegetation index (NDVI) data from the AVHRR (Miller et al., 2006), (3) a snow-free
albedo and a Noah-specific maximum snow albedo product from NCEP (National Centers for Environmental Prediction; original resolution 1∘ and regridded), and, finally, (4) soil, vegetation, and other general parameter tables for Noah-MP from the official LIS Data Portal (https://portal.nccs.nasa.gov/lisdata_pub/data/, last access:
20 May 2021).

## Irrigation modelling

The ability of Noah-MP to dynamically simulate the vegetation and the option to activate irrigation are particularly important when considering an
extensively irrigated area such as the Po Valley. Indeed, in a recent study by Nie et al. (2018), Noah-MP was coupled with a sprinkler
irrigation scheme (Ozdogan et al., 2010; where irrigation is applied as supplementary rainfall), which requires the following three pieces of information:

The irrigation location, which only occurs over potentially irrigated croplands (expanding over grassland if the intensity exceeds the grid cell's total crop fraction). This information is extracted from a LC map associated with an additional data set providing information on the percent of irrigated area per grid cell. In this study, the reclassified PROBA-V LC map was coupled with the information contained in the 500 m global rain-fed, irrigated, and paddy croplands data set (GRIPC; Salmon et al., 2015).
The timing of irrigation, which is determined by checking the start and end of the growing season, based on a GVF threshold, separately at each grid cell. Following Ozdogan et al. (2010), we set this threshold to 40 % of the GVF.
The amount of water which is used for irrigation. This quantity is derived from the root zone soil moisture (RZSM) availability (MA) as MA=(RZSM-SMWP)/(SMFC-SMWP), where RZSM is the current RZSM, SMWP is the wilting point, and SMFC is the field capacity. When the MA falls below a user-defined threshold, irrigation is triggered, and the quantity is defined by calculating the amount of irrigation needed to raise the RZSM to the SMFC. For this study, the MA threshold was defined as the 50 % of SMFC as in Ozdogan et al. (2010). MA is calculated at each time step, but the irrigation is only applied between 06:00 and 10:00 LT. Following Ozdogan et al. (2010), this time frame is typically chosen by farmers to reduce evaporative losses. In this context, the maximum rooting depth becomes a crucial information to compute the amount of irrigation water. This information is related to an assigned crop type, cultivated over the study area, through a maximum rooting depth table. Considering the high crop variability over the Po Valley and the lack of high-resolution dynamic crop maps for the entire study area, a generic crop type with 1 m root depth was selected for the irrigation simulations. The reference rooting depth was verified to be feasible over the study area, based on the European Soil Data Centre (ESDAC; available at https://esdac.jrc.ec.europa.eu/content/european-soil-database-derived-data, last access: 20 May 2021) rooting depths map (Fig. S1 in the Supplement).

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
