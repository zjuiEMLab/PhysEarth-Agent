# Data and methods - Datasets

## VOD data

An overview of the datasets is given in Table 1 and
Fig. 1. All used VOD datasets are derived from
passive sensors using the LPRM algorithm (van
der Schalie et al., 2016) to reduce the degrees of freedom of this analysis.
Thereby, for each wavelength a different parametrization was used with the
exception of the retrieval of X- and C-band VOD where an identical implementation of single-scattering albedo was applied. For roughness a constant parametrization is
used for the Ku band, but a dynamical parameter is used for the other
wavelengths. Hence the parametrization essentially differs for the
wavelengths. This can affect the similarity of the datasets but is
necessary to allow for valid retrievals in general.

The VODCA dataset (Moesinger et
al., 2020) provides harmonized long-term records of short-wave VOD for the Ku,
X, and C band (further named Ku-VOD, X-VOD, and C-VOD, respectively), using
data from the AMSR-E, AMSR2, Special Sensor Microwave Imager (SSM/I), Tropical Rainfall Measuring Mission (TRMM)
Microwave Imager (TMI), and WindSat sensors. Unfortunately, Ku-VOD is only
available until 1 August 2017 due to a bias in the AMSR2 Ku-band VOD
causing unexpected low values of the VOD retrievals after this date
(Moesinger et al., 2020), which
is not fixed in version 01.0. Therefore, all datasets are analysed until
31 July 2017.

Two LPRM-derived L-band VOD datasets are used as long-wave VOD, one sensed
with SMAP, the other with SMOS (van
der Schalie et al., 2016; further named SMAP L-VOD and SMOS L-VOD,
respectively). The SMAP satellite was launched in January 2015, and
therefore SMAP L-VOD defines the start date of the analysis of all datasets.

All VOD datasets are provided as daily data with a spatial resolution of
0.25∘ on a global scale. As VOD generally decreases with
increasing wavelength, the five VOD datasets have different dynamic ranges.
As we are not interested in the absolute value but only the temporal
dynamics and spatial patterns, the VOD datasets were globally normalized
using a minimum and maximum value to a range of 0 to 1 based on the available
global data within the time span 2015–2017 to provide comparability. For
normalization we use the scikit-learn function “MinMaxScaler”. The
normalized VOD data form the basis of
Fig. 1d–h. These maps of temporally averaged VOD data
show different patterns and scales even after the normalization process.
This illustrates that VOD data derived from different wavelengths and
sensors are not related to the same vegetation properties, indicating the need
for this study.

## Predictor data

Following the relationship between VOD, LFMC, and AGB as shown in Eq. (2), proxies related to biomass (AGB and LAI), water content (LFMC), and the
structure parameter (plant types) are used as predictors for VOD.

As proxies for woody and non-woody biomass, we used a map of AGB and a time
series of LAI. The ESA Climate Change Initiative (CCI) AGB map (Santoro and Cartus, 2019)
for the year 2017 with a 100 m spatial resolution is used as a predictor of
woody biomass. This AGB map describes the oven-dry mass of woody parts of
living trees per pixel. Thereby only above-ground mass is considered, i.e. stem and bark as well as twigs and branches but not stumps and roots.

LAI is used as a proxy for canopy biomass. Specifically, we use the MOD15A2H
Version 6 dataset from MODIS, which is available at a 500 m spatial and
8-daily temporal resolution on a global scale
(Myneni et al., 2015). We excluded LAI retrievals
under (partial) cloud cover, snow, or a high solar zenith angle.

For LFMC, we used a product derived from MODIS MCD43A2 Collection 6
reflectance data for the western USA, South Africa, and Australia
(Fig. 1b) at a 500 m spatial and 4-daily
temporal resolution using the approach described in
Yebra et al. (2018). The extent
of the western USA region is determined for the purpose of covering California,
wherefor the MODIS tiles h08v04, h08v05, and h09v04 were necessary and the
tile h09v05 was not considered in favour of computational resources. Yebra
et al. (2018) use three radiative transfer models (RTMs) for the simulation
of spectra corresponding to different LFMC values. More specifically, they
use PROSPECT 1 (Platform for Resource Observation and in-Situ Prospecting for Exploration, Commercial exploitation and Transportation) coupled to SAILH 1 (Scattering by Arbitrary Inclined Leaves for homogenous canopies) and GeoSail to simulate the spectra of
grasslands/shrublands and forest, respectively. Based on these simulations
three different lookup tables (LUTs) were generated. For a given location
they use the MODIS land cover product (MCD12Q1 Collection 5) to select the
LUT corresponding to the specific fuel type characterizing that location.
That fuel specific LUT is used to invert the RTM and retrieve LFMC from the
MODIS spectra. The results were evaluated with LFMC field measurements, and
the model achieved an explained variance of 58 % and an RMSE of 40 % for
Australia (Yebra et al., 2018). For Europe, we used the LFMC product
produced by the European Union Joint Research Centre (JRC) and which is
included in the European Forest Fire Information System (EFFIS). This
product follows the same methodology as Yebra et al. (2018) but uses EFFIS's
fuel type map to select the LUT and MODIS MCD43A2 Collection 5 data to
invert the RTM before 2016. Therefore, for those years, the LFMC estimates
are produced with a temporal resolution of 8 d. Following Eq. (3),
LFMC can range from 0 % up to more than 400 %. A value over 100 %
means that the vegetation holds more water compared to the dry mass. This
depends on the part of a plant and on the vegetation type.

The LAI, LFMC, and AGB datasets were resampled to a 0.25∘
resolution to match the VOD spatial extent using a first-order conservative
remapping.

We used the land cover map by the European Space Agency (ESA) Climate Change
Initiative (CCI; ESA, 2017) and its continuation from the
Copernicus Climate Change Service, which provide yearly data for the period
1992–2018 at a 300 m spatial resolution. The land cover classes were converted
to fractions of plant functional types and aggregated to a 0.25∘
spatial resolution using the cross-walking approach as described in
Poulter et al. (2015).
Specifically, we made use of the fractions per 0.25∘ grid cell of
broadleaf evergreen (treeBE), needleleaf evergreen (treeNE), and deciduous
(treeD) trees; shrublands (shrub); croplands (crop); and herbaceous
vegetation (herb). Deciduous trees were not further segregated into broadleaf
and needleleaf trees as especially the latter would result in only a
small sample when intersected with the VOD data. In another test, we also
combined the fractional coverage of all tree plant functional types (PFTs) (treeAll = treeBE + treeNE + treeD) and of short vegetation (short = shrub + herb + crop).

## Data combination

All datasets were cropped to the extent of the LFMC data (Australia, Europe,
western USA, South Africa) for further analyses. This implies that the
“global” models as stated in the following are indeed inter-continental
models restricted to the spatial extent of the LFMC dataset which mainly
cover drylands except for Europe. To provide comparability of the
analyses of the different VOD datasets, only the overlapping time span is
used (January 2015–July 2017). The rather short time period does not impede
the framework of this study because instead of analysing coherent pixel
time series, this approach uses each time step of each pixel as an individual
data point. The ESA CCI AGB map represents the year 2017, but we assume that
the biomass does not dramatically change over 2 years. Therefore, the AGB
values are kept constant for the whole time series. The PFT fractions are
taken from the annual land cover maps for the respective years in 2015 to
2017 without any interpolation. During the analyses, models were trained and
tested for 8-daily and monthly temporal resolutions of the LAI and LFMC time
series. For the 8-daily resolution, only the VOD values matching the same
timestamp of the MODIS LAI and LFMC products are used. For the monthly
resolution, the mean VOD, LAI, or LFMC within the regarding month were
calculated.

As a final step, pixels were excluded when the fractional coverage of bare
ground or water exceeds 5 % to avoid the interpretation of marginal
effects of bare soils or water on VOD. Models were specifically trained for
single land cover classes. A threshold of 55 % was used to discern when a
land cover class was dominant compared to the other classes.

---

Luisa Schmidt, Matthias Forkel, Ruxandra-Maria Zotta, Samuel Scherrer, Wouter A. Dorigo, Alexander Kuhn-Régnier, Robin van der Schalie, Marta Yebra (2023). Assessing the sensitivity of multi-frequency passive microwave vegetation
optical depth to vegetation properties. Biogeosciences 20, 1027-1046. https://doi.org/10.5194/bg-20-1027-2023. Licensed under CC-BY-4.0.
