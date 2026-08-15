# Results - Brightness temperature

We now determine the maximum sampling distances for networks of ground-based
microwave radiometers allowed to estimate SMOS–SMAP footprint brightness
temperatures. To this goal, we transform the target accuracy of SMOS–SMAP
soil moisture retrievals of 0.04 cm3 cm-3 to the accuracy of the
corresponding brightness temperature, which is approximately 10 K for H
polarization and 5 K for V polarization (10 K/5 K) according to CMEM forward
simulations (Sabater et al., 2011; Monerris Belda, 2009). We note that
this brightness temperature accuracy is not the instrument observing error
of the (virtual) microwave radiometer, but the sensitivity of the microwave
forward transfer model to soil moisture. We are aware that the radiometric
accuracies of ground-based and satellite-borne sensors are much better, and
that the accuracy of the soil-moisture–brightness temperature relation is
mainly responsible for the retrieval accuracy; thus, we use the 10 K/5 K uncertainty only as a proxy for the overall error.

By comparing the high-res TB for certain sampling distances with the antenna
pattern TB from the satellite operator, Fig. 6 shows different patterns to
the soil moisture. Even at a sampling distance of 800 m, the sampling error
might exceed the 10 K for H polarization (5 K for V polarization) limit in certain regions and times. If we want
to keep the limit with a probability of only 75 percentiles (the upper
boundary of the boxes in Fig. 6, 100 % confidence panels), the maximum
sampling distance must stay below 4.4 km. For a sampling distance of 5.2 km,
the error may go beyond the nominal 10 K (5 K) with a probability of 50 %.
For 9.2 km sampling distance, and the maximum sampling error is always above
the nominal values for some region and/or a day in the year. Even if we
require that the nominal error is undercut only with a probability of 70 %
for all pixels and days, a sampling distance of 800 m is not enough. If only
50 % of all networks are required to fulfill the 10 K/(5 K) bound, a
sampling distance of 10 km is sufficient.

The time series of the distribution of the maximum sampling distances for
brightness temperature (Fig. 7) is quite similar to the one for the
maximum sampling distances for soil moisture. Figure 7 only illustrates the
periods without freeze–thaw state transformations, and liquid water in the
soil dominates the brightness temperature signal. Values range from 6.8
to 16.4 km for most cases. The spread of the sampling error has, however, a
distinct seasonal variation; e.g., the maximum sampling distance for 90 % of the footprints is 11.6 km from DOY 100 to 275 and 8.8 km for the
rest of the year.

The spatial distribution of the annual maximum sampling distance allowed to
guarantee a sampling error less than 10 K/5 K for H/V polarized brightness
temperatures, and its RMS for the year 2015 (Fig. 8) are similar for H and
V polarizations but shows a substantial spatial contrast compared to the
results for soil moisture (Fig. 5). Again, the southeast corner of the
model region allows for larger maximum sampling distances, but there are now
also other distinct regions with larger allowed maximum sampling distances.
Additional input parameters required – especially LAI – and internal
parameters in CMEM impact the representativeness of sites for
brightness temperatures. LAI dominates the variation of the
representativeness of ground-based observations and also its temporal
variation, as can be inferred from the correlation between large maximum
sampling distances with its variability over the year (correlation
coefficient is 0.84/0.83 for H/V polarization), which is not observed for
soil moisture. LAI is the only input in CMEM, which can lead to such a
temporal variation because other parameters such as air temperature, soil
moisture, and soil properties are either fixed or do not impact the brightness temperature as
strongly.

---

Shaoning Lv, Bernd Schalge, Pablo Saavedra Garfias, Clemens Simmer (2020). Required sampling density of ground-based soil moisture and brightness
temperature observations for calibration and validation of L-band satellite observations based on a virtual reality. Hydrology and Earth System Sciences 24, 1957-1973. https://doi.org/10.5194/hess-24-1957-2020. Licensed under CC-BY-4.0.
