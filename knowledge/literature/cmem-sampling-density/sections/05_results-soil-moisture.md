# Results - Soil moisture

We compare the true (but virtual) spatial arithmetic average of soil
moisture at the SMOS–SMAP resolution with the arithmetic average of soil
moisture at 0.05 m depth computed from the sampling points taken at
distances ranging from 400 m (i.e., each VR01 grid column, no sampling
error) to 18 km (about half the radius of a SMAP or SMOS pixel. First, we
analyze the probability density function of the sampling error as it varies
with the sampling distance, taking the SCft samples for one whole year of
all footprints in the entire model area into account (Eq. 3, Figs. 3 and 6). Then we analyze the evolution over the year of the daily PDF of
the maximum allowed sampling distance (for keeping the sampling error below
the nominal value of 0.04 cm3 cm-3 with 70 % confidence) from
SCtd samples (Eq. 4, Figs. 4 and 7). Finally, we look at the
spatial variability of the maximum allowed sampling distance (for keeping
the sampling error below the nominal value of 0.04 cm3 cm-3 with
70 % confidence) based on all samples of one SMOS–SMAP pixel over the year
SCfd (Eq. 5, Figs. 5 and 8). When we analyze the sampling errors
for brightness temperatures, we use footprint averages weighted by the
antenna function; using the weighting function according to the dB pattern
for soil moisture leads to differences below 0.01 cm3 cm-3; thus,
the averaging procedure does not impact our conclusions for soil moisture.

We compute the maximum sampling error for each sampling distance and each
footprint from the daily observations over 1 year of all network
configurations. The distributions of the corresponding 320 values are
displayed in the box–whisker plots in Fig. 3a. Thus each value
entering the distribution at a given sampling distance (individual
box-whisker plot in Fig. 3) stems from that sampling network for one of
the 320 SMOS footprints, which leads to the largest sampling error, taking
all daily observations over a year into account (Eq. 3). With a
sampling distance of 400 m, we accurately reproduce the true (but virtual)
arithmetic soil moisture average, i.e., the maximum error is zero. Maximum
errors naturally increase with sampling distance, as demonstrated by the
widening of the maximum error distribution. The median of the maximum
sampling error increases almost linearly, with about 0.022 cm3 cm-3
per kilometer increase in sampling distance. The spread of the maximum error
increases from less than 0.01 cm3 cm-3 at 0.8 km to approximately
0.4 cm3 cm-3 at 18 km, with quite some variability between the
sampling steps. To guarantee a sampling error below 0.04 cm3 cm-3
(the assumed accuracy of SMOS–SMAP retrievals) with 100 % confidence
everywhere in the region at any time of the year (Fig. 3a), the
maximum sampling distance should not exceed 2.8 km. With a 4.8 km sampling
distance, for 50 % of the area and/or days of the year, we get sampling
errors above 0.04 cm3 cm-3. At a sampling distance of 4.4 km (about
18 sites within a 43 km ×43 km pixel); the same would hold for only 25 %
of the satellite pixels.

Figure 3c displays the PDF of the maximum sampling error
corresponding to the 70th percentile of the sampling error PDF computed
for each satellite pixel over the year. Thus, to guarantee a sampling error
below 0.04 cm3 cm-3 for all network configurations for only up to
70 % of all pixels and all days of the year, a minimum sampling distance
of 6 km is required. At a sampling distance of 12 km, already only 50 % of
the pixels fulfill this requirement. Overall, about one-quarter of the
stations needed for 100 % confidence is needed, when the requirement to
stay within the 0.04 cm3 cm-3 error margin is relaxed to 70 %.

As outlined above, we can also quantify from the simulations the allowed
maximum sampling distance on a daily basis from the samples with the size
given by Eq. (4). According to Fig. 4b, for 80 % of the
SMOS–SMAP pixels, the maximum allowed sampling distance is between 8.4
and 16 km, which is 7–26 stations for SMOS (43 km) and 5–18 stations for
SMAP passive (36 km) to keep the sampling error below 0.04 cm3 cm-3
with 70 % confidence. A seasonal variation is not apparent, but rainfall
events (Fig. 4a) affect the distributions by increasing the maximum
allowed sampling distances because the surface soil moisture becomes more
homogeneously distributed in space due to the typically quite widespread
precipitation in that region. The opposite occurs during dry periods because
evaporation, draining, and runoff over various soil and land cover types
tend to create spatially heterogeneous soil moisture distributions, which
typically reaches its maximum at intermediate soil moisture levels
(Brocca et al., 2010).

The spatial distribution of the annual maximum sampling distance allowed to
guarantee a sampling error below 0.04 cm3 cm-3 with 70 %
confidence computed from the samples given by Eq. (5) and its RMS for
the year 2015 (Fig. 5) indicates that the southeastern region requires
sampling distances of only below 16 km; thus only nine sites are needed
within a SMOS–SMAP pixel to estimate the footprint-averaged soil moisture
with a sampling error below 0.04 cm3 cm-3. Also, the annual
variation is particularly small (blue). For the rest of the region, maximum
allowed sampling distances range from 7 to 10 km (radius); thus, more
than nine sites are required within one footprint. The annual variation of
the maximum sampling distances for those footprints is larger than in the
southeast. The mean allowed sampling distances and their day-to-day changes
are only weakly correlated (correlation coefficient 0.40), but show
larger-scale common patterns.

---

Shaoning Lv, Bernd Schalge, Pablo Saavedra Garfias, Clemens Simmer (2020). Required sampling density of ground-based soil moisture and brightness
temperature observations for calibration and validation of L-band satellite observations based on a virtual reality. Hydrology and Earth System Sciences 24, 1957-1973. https://doi.org/10.5194/hess-24-1957-2020. Licensed under CC-BY-4.0.
