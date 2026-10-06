# Conclusion and discussion

We used a virtual reality generated with a fully coupled
subsurface–vegetation–atmosphere model platform over southwestern Germany
with a spatial resolution of 400 m for the land components to quantify the
sampling error for the arithmetic averaged soil moisture and the weighted
average brightness temperatures estimated from in situ ground-based
observation networks covering SMOS–SMAP-like footprints of 43 km diameter
for a wide range of potential sampling distances. By using a virtual reality
at such high resolution, we have a physically consistent three-dimensional
evolution of the terrestrial system at our disposal from which we can
take virtual soil moisture observations and – via the radiative transfer
model CMEM and a satellite antenna function – microwave brightness
temperature observations from the highest resolution at 400 m to any larger
resolution.

As an upper threshold for the sampling error of ground-based
sensor networks when estimating averages over SMOS–SMAP pixels, we adopted the target
SMOS–SMAP soil moisture retrieval accuracy of 0.04 cm3 cm-3. We
quantified the maximum sampling distance, which still keeps the sampling
error below that accuracy either for all or for 70 % of all SMOS–SMAP
pixels in the modeling region over 1 year for all network configurations
possible. A primary assumption in our study is that the estimation of soil
moisture for an area with a diameter of about 400 m is possible, or in other
words that a single station within a 400 m area is representative for its
spatial average, an assumption also discussed in Famiglietti et al. (2008).
Compared to the region analyzed in Famiglietti et al. (2008), our study uses
a much more realistic terrain and excludes subjective factors in selecting
suitable Cal/Val sites. Because of this, the soil moisture error in our
study grows much faster with increasing sampling distance. We also find that
the estimation of area-averaged brightness temperatures from a network of
ground-based stations has a different error growth with increasing sampling
distance compared to soil moisture despite an initial linear growth for both
of them (compare Figs. 3 and 6). Thus, a representative soil moisture
network does not guarantee a representative radiometer network for the
estimation of area-averaged brightness temperature, or that brightness
temperatures computed for the soil moisture stations can be used for that
estimate. But Figs. 3 and 6 also show that sampling distances below 6 km
still fulfill the 70th percentage requirement for keeping the sampling
error below the nominal error.

Besides plant types, there is no apparent pattern similarity between
clay, sand, and elevation (Fig. 1) and spatial sampling distance (Fig. 5).
Soil properties may be related to the regional climate (annual
precipitation, radiation flux balance, etc.). For instance, arid regions
usually contain higher sand fractions, but such areas are seldom the focus
of soil moisture studies because of their low variation. Transition zones like
our model area usually encompass various soil properties, which are often
correlated with land use and vegetation and thus the plant function type
used in the CLM. Topography also affects the soil moisture and TB
distribution, but it is difficult to infer the impact of land use and
vegetation because soil properties determine both the water holding capacity
and the plant cover. In practice, soil moisture monitoring networks avoid
complex terrain. Homogenous terrain and landscape lead to an overestimation
of satellite soil moisture product accuracies.

The statistical results in our study differ from those in Famiglietti et al. (2008) because our focus is on the satellite footprint scale and not the
representativeness of one station within a network. For example, a
particular sensor may not represent the actual 400 m average, but one such
sensor every 400 m may statistically sufficiently represent a much larger
footprint. A similar concept is adapted in ensemble forecasts using members,
e.g., with different physics packages, none of which is expected to be the
truth (Lewis, 2005; Leutbecher and Palmer, 2008). The space detected by a
soil moisture sensor, which is measuring the dielectric constant of the soil
or other media using capacitance/frequency domain technology, is about a
10 cm sphere. Thus, the study by Famiglietti et al. (2008) assumes
soil moisture homogeneity on the scale of meters. We believe that the 400 m
soil moisture homogenous assumption does not interfere with our conclusions
and that our study can be considered as a complement to the study by
Famiglietti et al. (2008).

The calibration and validation of passive satellite-based L-band soil
moisture estimates are difficult due to the large subpixel variability
(Lv et al., 2016b, 2019). Even with a perfect microwave
transfer model and precise sensors, we can hardly find an appropriate
in situ observation to compare with. While soil moisture also varies in the
vertical, sensors are usually mounted at a fixed depth; thus, comparisons
with satellite observations require the knowledge of the microwave
penetration depth, which is, however, unknown in general. Lv et al.
(2018) developed a model based on the soil effective temperature which sheds
light on this fundamental problem. This study isolates the sampling density
issue from other factors and is a test of the current Cal/Val network
standard without previous knowledge of the site. The SMAP team suggests 15 sites
for a 36 km by 36 km grid size (Colliander et al., 2017b), and this study
agrees with this configuration for typical mid-latitude European regions
from the sampling error perspective. For a 36 km by 36 km grid size, the
required sampling sites would range from about 36 (6 km) to 4 (17 km).
However, five sites for 9 km by 9 km and three sites for 3 km by 3 km will
miss the 70 % confidence level requirements over this area. Since SMAP's
9 and 3 km soil moisture products are from a combination of passive and
active microwave signals, which have a lower accuracy than the passive
ones (Entekhabi et al., 2010), their Cal/Val campaigns
shall determine sampling distances with less confidence level.

Our virtual reality contains extensive land cover variability (Fig. 1);
thus, it would be helpful to adapt our approach for less complicated regions
with variabilities closer to the typical Cal/Val station networks. Overall,
we find that a soil moisture sampling distance of ∼3 km is
necessary to always keep the sampling errors below the nominal value. The
allowance for a failure probability of 30 % extends this distance to 10 km. For brightness temperatures, the sampling requirements are much more
strict; already, at 800 m sampling distance, it cannot be guaranteed that
the sampling error remains below the equivalent threshold of 10 K/5 K for H
and V polarization, respectively, even when allowing for a 30 %
probability of failure. The error sources in retrieving soil moisture from
TB data are also large in reality but are not of concern in this study because
VR01 and the TB produced by CMEM exclude the uncertainty, except for the sampling
distance.

Our results are not only useful for the planning of ground-based soil
moisture networks, they also contribute to a better understanding of the
relation between brightness temperatures observed on the ground – or
simulated at high resolution – and the ones observed from satellites, apart
from the non-linearity effects of radiative transfer (e.g., Drusch et
al., 1999). The study allows, for example, to quantify to what extent a bias
between satellites' brightness temperature and forward simulation could be
explained by the spatial sampling (e.g., Figs. 5, 8, and 11), and to
understand the similarities and dissimilarities between observed soil
moisture and brightness temperature time-series (Figs. 4 and 7). Since
ground-based soil moisture networks will always cover only certain parts of
a satellite pixel, a bias must be expected between both. The different
representativeness of the latter can also cause biases in satellite and
ground-based estimates of soil moisture for soil moisture and brightness
temperatures.

While the allowed maximum sampling distances do not change much over the
year for soil moisture – except after large-scale precipitation events which
will enable larger sampling distances – its equivalence for brightness
temperature has a strong seasonal variation because of the blurring effect
of vegetation during the growing season, when brightness temperatures become
more homogeneous. The spatial distribution of the maximum sampling distances
and their local variances behave quite differently between soil moisture and
brightness temperature. The spatial patterns are different, and while the
maximum allowed sampling distance and its variation are firmly related to
brightness temperature, they are barely related to soil moisture; this
unusual behavior is caused by the complexity of other factors influencing
microwave radiative transfer.

Our study strongly suggests that the sampling density of current SMOS–SMAP
ground-based Cal/Val networks and the resulting potential sampling error of
estimated pixel-mean soil moisture and brightness temperatures considered in
such studies should be reviewed carefully. We expect this study will help us to
understand the errors of satellite-derived soil moisture better.

---

Shaoning Lv, Bernd Schalge, Pablo Saavedra Garfias, Clemens Simmer (2020). Required sampling density of ground-based soil moisture and brightness
temperature observations for calibration and validation of L-band satellite observations based on a virtual reality. Hydrology and Earth System Sciences 24, 1957-1973. https://doi.org/10.5194/hess-24-1957-2020. Licensed under CC-BY-4.0.
