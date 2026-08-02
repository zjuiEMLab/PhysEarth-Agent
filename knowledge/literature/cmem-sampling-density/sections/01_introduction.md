# Introduction

Information on the global soil moisture distribution is required, for example, for
weather forecasting, climate research, and agricultural applications. Due to
the high spatial variability of soil moisture, its in situ observation is
practically impossible on continental scales. Passive microwave satellite
remote sensing at L-band frequencies may achieve this goal because of the
strong dependency of the soil dielectric constant on soil moisture, the –
compared to higher frequencies – reduced sensitivity of the brightness
temperatures to surface roughness and vegetation (Njoku and Kong, 1977;
Ulaby et al., 1986), and the high transparency of the atmosphere at these
wavelengths. The first operational L-band soil moisture detection satellite,
SMOS (Soil Moisture and Ocean Salinity), was launched in 2008 (Kerr et
al., 2010) and was followed in 2015 by SMAP (Soil Moisture Active Passive),
which initially were performing with an active instrument to achieve higher
spatial resolution (Entekhabi et al., 2010); the
active component did fail, however, shortly after the full operation of the
satellite. Both satellites are currently continuously and globally observing
passive microwave brightness temperatures, from which soil moisture products
are derived at a spatial resolution of 36 and 9 km.

Before and after the launch of SMOS and SMAP several soil moisture
monitoring networks for evaluation and retrieval algorithm development were
established, such as ESA's efforts at the Valencia Anchor Station (VAS) in
eastern Spain, SMOSREX (Surface Monitoring Of Soil Reservoir Experiment) in
France, the upper Danube watershed located in southern Germany (Delwart
et al., 2008; de Rosnay et al., 2006; dall'Amico et al., 2012; Kerr et al.,
2016), and the SMAP calibration–validation (Cal/Val) project (Colliander et al., 2017a; Burgin et
al., 2017; Chen et al., 2017, 2018). All those networks have
been established since ground truth should be the only standard to evaluate
these products. According to the Level 1 baseline and the minimum SMAP
science requirements (SMAP Science Data Cal/Val Plan, O'Neill et
al., 2015) the spatial resolution of Level 2 (passive soil moisture product
L2_SM_P) and Level 3 (daily composite
L3_SM_P) soil moisture products is 36 km,
and they have to reach an accuracy for soil moisture of 0.04 cm3 cm-3
with a probability of 70 %. A wide range of measurement techniques and
protocols exist for setting up and performing ground-based observations for
such evaluations. SMAP Cal/Val suggests that volumetric soil moisture should
be observed in situ at 5 and 100 cm depth; optimal sensing and mounting
depths are, however, still debated (Lv et al., 2016a, 2018, 2019). For core validation sites a minimum of six stations should
cover one SMAP grid cell or footprint (O'Neill et al., 2015; Famiglietti
et al., 2008); but this value has not yet been shown to guarantee the
nominal accuracy by a thorough analysis (Jackson et al., 2012; Crow et
al., 2012). More recent results show that the spatial representativeness of
the soil moisture tends to increase with the timescale of data series, but
so does their spread (Molero et al., 2018). For Cal/Val, it is required
to have instantaneous soil moisture values rather than averages in different
timescales. Relevant studies typically use ground-based soil moisture
networks with fixed average sampling distance over rather homogeneous land
surfaces, which are, however, not necessarily representative for all land
surface types. For SMAP core calibration and validation sites, the data product
grid cell should be sampled with at least eight stations to reach with
70 % confidence an estimated soil moisture uncertainty of 0.03 cm3 cm-3 given a spatial soil moisture standard deviation of 0.07 cm3 cm-3 as assessed from field measurements (Colliander et al.,
2017b). According to the same source, grid cells with a dimension of 9 km
(as for downscaled SMAP products) should be sampled with at least five
stations and pixels with 3 km diameter with at least three stations to reach
with 70 % confidence an accuracy of 0.03 and 0.05 cm3 cm-3,
respectively, while assuming a spatial soil moisture standard deviation of
0.05 cm3 cm-3 within the grid cell.

Ochsner et al. (2013) point out that too few resources are currently
devoted to in situ soil moisture monitoring networks, and that despite their
increasing number, a standard for network density and sampling procedures
is missing. The International Soil Moisture Network (ISMN, https://ismn.geo.tuwien.ac.at/en/, last access: 11 April 2020) is an effort to unify global soil
moisture observation networks (Dorigo et al., 2011). Coopersmith et
al. (2016) suggested temporary network extensions around permanent
installations to quantify the representativeness of the latter. Qin et
al. (2013) suggested the use of MODIS-derived apparent thermal inertia to
interpolate between in situ soil moisture measurements. So far, the required
sampling density is discussed only concerning in situ measurements, which
heavily depend on sensor quality and network location (Vereecken et al.,
2008; Brocca et al., 2010; Bhuiyan et al., 2018). Higher station numbers are
necessary, as well as the establishment of general rules for their selection
(Cosh et al., 2017). Chen et al. (2017, 2018, 2019)
suggest the utilization of TC (triple collocation), which is a statistic
method to characterize systematic biases and random errors, or ETC (extended
triple collocation) to analyze the noise component in soil moisture
observations, and to use correlation to evaluate the representativeness of
soil moisture networks. They also suggest that the core validation sites
should allow validation of the retrieved soil moisture to an accuracy of 0.04 cm3 cm-3 with a probability of 70 % in terms of unbiased RMSE
because the bias itself is hard to eliminate.

Establishing ground monitoring networks for calibration and validation of soil
moisture products from satellite L-band observations is challenging partly
due to the different spatial scales between observations from soil moisture
sensors and satellites. Moreover, from a direct comparison between satellite
soil moisture products and ground-based measurements from existing soil
moisture networks, it is impossible to isolate the sampling error, and only
very few studies systematically investigate the station density required to
allow for a given accuracy, taking the land heterogeneity into
account. In our study, we use a 400 m resolution virtual reality
generated with a regional terrestrial modeling system coupled with an
observation operator to estimate such minimum station densities. The virtual
reality contains realistic soil, land cover, and topography variability and
allows us to arbitrarily vary the sampling density and, thus, average
sampling distance in steps of 400 m. Section 2 introduces the virtual
reality, and the observation operator used to transfer the terrestrial
system states into virtual observations. In Sect. 3, we derive the error
growth with increasing average sampling distance for soil moisture and
brightness temperatures. Conclusions and discussion are provided in Sect. 4.

---

Shaoning Lv, Bernd Schalge, Pablo Saavedra Garfias, Clemens Simmer (2020). Required sampling density of ground-based soil moisture and brightness
temperature observations for calibration and validation of L-band satellite observations based on a virtual reality. Hydrology and Earth System Sciences 24, 1957-1973. https://doi.org/10.5194/hess-24-1957-2020. Licensed under CC-BY-4.0.
