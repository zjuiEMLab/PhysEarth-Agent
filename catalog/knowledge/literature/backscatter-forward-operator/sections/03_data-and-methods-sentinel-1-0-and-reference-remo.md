# Data and methods - Sentinel-1 σ0 and reference remote sensing products

The Copernicus-ESA Sentinel-1 σ0 observations were used in this study for the calibration of the WCM. The Sentinel-1 constellation consists
of two satellites, Sentinel-1A and Sentinel-1B, launched in 2014 and 2016, respectively. Each satellite carries a synthetic aperture radar (SAR)
operating at the C band (5.4 GHz) in the microwave portion of the electromagnetic spectrum. The processing of the ground-range detected (GRD)
interferometric wide swath (IW) observations in VV and VH polarization was done using Google Earth Engine's Python interface and included standard
techniques, namely precise orbit file application, border noise removal, thermal noise removal, radiometric calibration, and range Doppler terrain
correction. Furthermore, the σ0 observations acquired at 5 m × 20 m resolution were aggregated and projected on the 1 km Equal-Area Scalable Earth version 2 (EASE-2) grid (Brodzik et al., 2012). After applying an orbit bias correction (Lievens et al., 2019), the observations from different orbits, either from Sentinel-1A or Sentinel-1B and ascending or descending tracks, were combined at the daily timescale.

Additionally, RS observations were used for the evaluation of the SSM and LAI simulated in Noah-MP LSM for the period 31 March 2015–December 2019.

The NASA Soil Moisture Active Passive (SMAP; Entekhabi et al., 2010) is an orbiting observatory launched in January 2015 carrying two
instruments, namely a SAR, which suffered a failure in early July 2015, and a radiometer measuring Tb at the L band, with a native spatial resolution of 40 km, a revisit time of 2–3 d, and ascending and descending overpasses at 18:00 and 06:00 LT (local time), respectively. For this study, the 9 km SMAP Enhanced Level-2 SSM version 4 (0–5 cm; SMAP L2 hereafter) product was used (O'Neill et al., 2020; Chan et al., 2018). The product is derived from SMAP Level-1B (L1B) interpolated antenna temperatures using the Backus–Gilbert optimal interpolation technique. Both ascending and descending tracks were collected.
The Metop ASCAT SSM Climate Data Record (CDR) H115 and its extension H116 are provided by the European Organization for the Exploitation of Meteorological Satellites (EUMETSAT) Support to Operational Hydrology and Water Management (H SAF, 2021). The SSM is retrieved from σ0, using a change detection algorithm (Wagner et al., 2013), and is characterized by a spatial sampling of 12.5 km and a temporal resolution of one to two observations per day, depending on the latitude.
The PROBA-V LAI is derived from the PROBA-V satellite mission (Francois et al., 2014; Dierckx et al., 2014) and provided by the Copernicus Global Land Service (CGLS) programme (Copernicus Global Land Service Site, 2021). The CGLS product at 1 km spatial resolution and 10 d temporal resolution is developed based on the work by Verger et al. (2014).

In order to compare Noah-MP simulations and reference data at the same spatial resolution, Sentinel-1 observations (σ0 VV and σ0 VH) and ASCAT SSM, SMAP L2 SSM, and PROBA-V LAI were extracted over the study domain (44∘ N, 10.5∘ W – bottom left; 45.5∘ N, 12.2∘ W – top right) and regridded over the LIS grid domain (0.01∘) using the nearest neighbour approach.

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
