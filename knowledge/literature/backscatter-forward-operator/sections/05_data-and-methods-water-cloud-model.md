# Data and methods - Water Cloud Model

The WCM allows us to simulate the top-of-vegetation σ0 as a function of SSM and vegetation, using empirical fitting parameters. σ0 is modelled as the sum of the backscatter from the vegetation (σveg0; in decibels, hereafter dB) and from the bare soil (σsoil0; in dB), attenuated by the t2 coefficient that describes the two-way attenuation from the vegetation layer. Scattering interactions between the ground and the vegetation are not accounted for. As reported in Baghdadi et al. (2017), for a given
polarization pq (i.e. VV and VH), the WCM can be written as follows:
σpq0=σveg,pq0+tpq2σsoil,pq0,
where, in the following,

2σveg,pq0=ApqV1cos⁡θ(1-tpq2)3tpq2=exp⁡-2BpqV2cos⁡θ4σsoil,pq0=Cpq+Dpq⋅SSM.

Equations (2) and (3) describe the vegetation-related terms. V1 and V2 represent two bulk vegetation descriptors, with the first one accounting for the direct vegetation σ0 and the second one representing the attenuation. Apq(-) and Bpq(-) are the two related fitting parameters. Common vegetation descriptors used in previous studies are the vegetation water content (VWC; Paloscia et al., 2013), the NDVI (El Hajj et al., 2016; Li and Wang, 2018), and LAI (K. Kumar et al., 2015; Bai and He, 2015), while θ represents the incidence angle, which is assumed to be 37∘ for Sentinel-1. Following previous studies (see Lievens et al., 2017b; Baghdadi et al. 2017; Li and Wang, 2018), we assumed V1=V2 represented by the dynamically simulated LAI vegetation descriptor.

Equation (4) describes the soil-related term. Following the work by Lievens et al. (2017b), the σsoil0 can be described, in a simple linear approach, as a function of the SSM. There are several semi-empirical models (e.g. the Oh model; Oh et al., 1992) or theoretical models (e.g. the Integral Equation Model – IEM; Fung, 1994), which describe the scattering processes related to the bare soil, but their application as a forward operator coupled to a LSM has two main limitations. The first one lies in the difficulty in retrieving soil roughness values over extended reference areas required to parameterize these models. The second one is their saturation of σ0 in moist conditions, which causes low variability in simulated σ0 if the LSM soil moisture simulations are biased wet (for more information, see Lievens et al., 2017b). Those limitations justify the use of a linear fitted approach. In Eq. (4), the C and D parameters (here fitted in dB and decibels per cubic metre per cubic metre, dBm-3m-3, respectively, but σsoil0 is transformed back to the linear scale in Eq. 1) describe the linear relation between σsoil,pq0 and SSM. Those parameters, together with A and B (–), need to be calibrated separately for each polarization.

---

Sara Modanesi, Christian Massari, Alexander Gruber, Hans Lievens, Angelica Tarpanelli, Renato Morbidelli, Gabrielle J. M. De Lannoy (2021). Optimizing a backscatter forward operator using Sentinel-1 data over irrigated land. Hydrology and Earth System Sciences 25, 6283-6307. https://doi.org/10.5194/hess-25-6283-2021. Licensed under CC-BY-4.0.
