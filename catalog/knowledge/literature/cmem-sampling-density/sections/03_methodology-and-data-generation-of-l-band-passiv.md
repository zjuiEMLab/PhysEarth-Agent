# Methodology and data - Generation of L-band passive microwave observations

The radiative transfer model CMEM (de Rosnay et al., 2009) computes the
land emissivity based on a dielectric mixture model for soil moisture, soil
sand and clay fractions, soil surface roughness, vegetation optical
thickness, single scattering albedo, and land surface orientation relative
to the satellite viewing perspective. Depending on the sand and clay
fractions, brightness temperatures may vary by tens of Kelvins, given the
same near-surface soil moisture. Vegetation optical thickness depends on
LAI, which varies in the VR01 with time depending on plant functional type (PFT). Depending on
the particular PFT, CMEM uses different parameters
to calculate the vegetation optical thickness from the respective LAI. Soil
effective temperature is computed with a new scheme introduced by
Lv et al. (2014). The new scheme is a discretization of the
integral formulation and takes advantage of multi-layer soil
temperature and moisture profile information with a broader range of soil
properties. This allows better adaptation of CMEM to the available land surface
model data. Also, soil temperature and snow depth impact the simulated
brightness temperatures. More details can be found in the SMOS global
surface emission model handbook (de Rosnay et al., 2009).

From the 400 m resolution brightness temperatures, virtual satellite
observations are generated with CMEM, taking the satellite antenna function
into account. Figure 2 shows the centers of the ∼320 footprints
corresponding to the SMOS L1 TB data product at a 41∘ incidence
angle for a potential satellite overpass and – on the same scale – the
satellite antenna function for one footprint, which changes shape depending
on the elevation of the individual 400 m model grid areas, orbit altitude,
declination, satellite scanning and incidence angle.

Not each SMOS overflight will cover the whole area in reality. But in our
study, we assume for simplicity that all footprints indicated in Fig. 2
are observed once a day at 06:00 local time, which corresponds to the
approximate ascending and descending overpass time of SMOS and SMAP,
respectively. The satellite footprint is much larger than the nominal
satellite spatial resolution of 40 km that is defined by a 3 dB contour of the
main lobe; thus areas much larger in diameter contribute to one
satellite-observed brightness temperature (i.e., 50 % of one
satellite-observed brightness temperature originates from an area roughly
10 times larger than the nominal satellite footprint).

The virtual reality employed in this study is a physically consistent state
of the terrestrial system in space and time because it has been produced by
a numerical model based on the conservations equations for mass, energy, and
momentum. When applying the satellite observation operator to this model
state, we assume that the model state is correct, as well as the simulated
brightness temperature. Thus, our study only quantifies the impact of the
sampling density of a surface network on the comparison between
area-averaged values and their estimates from the surface network, i.e., we
ignore errors of the dynamic model (TerrSysMP) and the forward operator
(CMEM). Based on the modeling results, we analyze a range of ground-based
network configurations with sampling points at least 400 m apart, and we
assume that all quantities (state of the terrestrial system and brightness
temperature) do not vary within 400 m. While this is an approximation, we
believe that our results and their outcome can be generalized. We will come
back to this point in the discussion section.

Since one SMOS and SMAP footprint covers approximately 106×106 model grid
columns in the VR01, the respective area can be sampled up to a
maximum of 106×106 (virtual) sites. If the footprint area is sampled with
n sites, there are C106×106n sampling combinations (SCs, hereafter)
possible, with
SC=C106×106n=1062!n!(1062-n)!,
which is an unordered, non-overlapping collection of distinct elements of a
prescribed size taken from a given set. For example, with a 10 km distance
between sampling sites, about 6×6 sampling sites are possible within one
footprint, which can be spatially distributed in C106×1066×6≈1.69×10104 ways. It is computationally not feasible to consider
all those combinations. When, however, we first divide each footprint into
equally sized subareas each containing exactly one sampling site (this
assumes a certain degree of homogeneity within the network, which would in
reality also be strived for), the number of potential sampling networks is
drastically reduced. If we set the sampling distance within a 43×43 km2 area to i km, we divide the footprint into 43i2 subareas each containing 106×106/43i2≈6.08×i2 400 m-resolution model columns. When we further select
within each of the equally sized subareas of a satellite footprint the same
model column (i.e., the one with row number k and column number l, both starting at 1 in the upper left column of each subarea), a regular
equidistant observation network within the SMOS–SMAP footprints is enforced
similar to the one used in the study by Famiglietti et al. (2008). For each footprint (subscript f) at a particular time (subscript t) of
a certain sampling distance (i km, subscript d), the number of network
configurations SCftd is
SCftd=106×106/43i2≈i0.4062.
This results for a certain sampling distance (i km) for all 320 footprints
and all 365 d of a year to a sample size of
SCft=106×106/43i2×365×320,
from which we will compute the PDF of the resulting sampling errors. For
each day, given one observation per day for all 320 footprints and summed
over all sampling distances, we get samples of size
SCtd=∑i=0.818106×106/43i2×320,
from which we will compute PDFs of the maximum allowed sampling distances.
For each grid cell with one observation per day taken over 1 year and
summed over all sampling distances, we get
SCfd=∑i=0.818106×106/43i2,×365
from which we determine the spatial distribution of the maximum
allowed sampling distances. For example, for 800 m sampling distance, we determine
the maximum from 0.80.42×365×320=467200 samples, the number of which increases with the square
of the sampling distance.

The sampling described above is applied to soil moisture (brightness
temperature) with (without) considering the satellite weighting function
(Fig. 2b). Since SMAP Cal/Val requires that the nominal accuracy of 0.04 cm3 cm-3 for retrievals should meet with a probability of 70 %,
we take the error at the 70th percentile, if not specified otherwise.
In the following, we mostly use the more intuitive sampling distance (km),
but also the sampling density (sites per square kilometer) when we are qualifying
tendencies. The relationship between the sampling distance and the sampling
density is simply
samplingdensity=1samplingdistance2.
For example, the 15, 5, and 3 sites for grid cells with diameters of 36, 9, and 3 km
recommended by SMAP Cal/Val would be around 0.0116, 0.0617, and 0.3333 sites per
square kilometer and correspond to sampling distances of 9.295, 4.025, and 1.732 km, respectively. We
note here that the grid size of the SMAP passive soil moisture product is 36 km ×36 km per pixel, which is the ISEA-4H9 discrete global grid for SMOS
(43 km ×43 km). The 43 km in all equations shall be exchanged by 36 km when
computing the number of sampling networks by Eqs. (1) to (3).

---

Shaoning Lv, Bernd Schalge, Pablo Saavedra Garfias, Clemens Simmer (2020). Required sampling density of ground-based soil moisture and brightness
temperature observations for calibration and validation of L-band satellite observations based on a virtual reality. Hydrology and Earth System Sciences 24, 1957-1973. https://doi.org/10.5194/hess-24-1957-2020. Licensed under CC-BY-4.0.
