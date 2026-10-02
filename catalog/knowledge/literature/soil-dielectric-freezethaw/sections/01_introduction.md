# Introduction

The current generation of L-band (1–2 GHz) satellite-based radiometers offers a unique opportunity to monitor soil moisture and freeze–thaw cycles
due to its global coverage and revisit time of only a few days (Kerr et al.,
2012; Roy et al., 2015; Rautiainen et al., 2016; Colliander et al., 2017;
Derksen et al., 2017; Wigneron et al., 2017). These satellites include the
European Space Agency Soil Moisture Ocean Salinity mission (SMOS; Kerr et al., 2010), the National Aeronautics and Space Administration (NASA) Soil
Moisture Active Passive mission (SMAP; Entekhabi et al., 2010) and the
NASA/CONAE (Comisión Nacional de Actividades Espaciales) joint Aquarius
mission (Le Vine et al., 2010). Information about the physical state of the
soil is retrieved from microwave observations by using radiative transfer
models to simulate the interaction between electromagnetic waves and the
surface (Attema and Ulaby, 1978; Mo et al., 1982; Ulaby et al., 1990; Bracaglia et al., 1995; Huang et al., 2017). Such models have already been
applied to obtain information on the characteristics of snow cover (Lemmetinen et al., 2016), the state of vegetation (Mo et al., 1982;
Rodríguez-Fernández et al., 2018; Fan et al., 2018), soil moisture
(Kerr et al., 2012; Mialon et al., 2015; Colliander et al. 2017) and soil
freeze–thaw state (Kim et al., 2012; Rautiainen et al., 2016; Derksen et al., 2017; Roy et al., 2017a, 2018, 2020; Prince et al., 2019).

Permittivities of the landscape constituents are crucial components of the
dielectric models used to solve the electromagnetic equations governing the
interaction between microwaves and the surface. The permittivity of a medium (ε, in F m-1) determines its behavior when exposed to an electric field. The relative permittivity is the ratio between a medium's permittivity and that of a vacuum (εr=ε/ε0=ε′-iε′′; unitless; hereafter relative permittivity will stand for permittivity). Permittivity is characterized by a complex number, where the real part (ε′) describes the translation and rotation of molecular dipoles, which drives the wave propagation, and the imaginary part (ε′′) describes the energy loss (absorption) associated with this process (Griffiths, 1999). The real and imaginary parts are linked through the Kramers–Kronig relations (Klingshirn, 2012); therefore, they are not fully independent. A medium that strongly opposes the application of an external electric field displays a high permittivity (e.g., εwater′≈78–79 in the 1–2 GHz frequency range; Pavlov and Baloshin, 2015) and a medium that does not strongly oppose an external electric field displays a low permittivity (e.g., εair′≈1).

Because of water's high permittivity, it dominates the microwave signal observed by satellite-based radiometers. Similarly, soil moisture retrieval
algorithms exploit the high contrast in water–soil–air permittivity differences. However, the water phase also plays an important role in soil
permittivity. When water freezes, the molecules become bound in a crystal
lattice and the permittivity drops drastically compared to liquid water
(i.e., εice′≈3). The permittivity drop observable within freezing soils translates into a higher microwave emission from the ground. This allows for the retrieval of the ground state (freeze or thaw) from passive microwave observations (Zuerndorfer et al., 1990; Judge et al., 1997; Zhao et al., 2011; Rautiainen et al., 2012; Roy et al., 2015; Derksen et al., 2017). Soil permittivity is especially important in radiative transfer models since it acts as a boundary condition in the models. As microwave permittivity is challenging to measure in field settings, it is typically derived from empirical relationships and physical properties. Nonetheless, many uncertainties remain in the relationship between soil permittivity and soil physical parameters (Montpetit et al., 2018; Moradizadeh and Saradjian, 2016). This is especially evident during the winter when, in many cases, fixed values are introduced in data analysis algorithms due to a lack of better estimates or, in other cases, data are simply not available during winter. The difficulty in gathering in situ permittivity data at microwave frequencies represents a major hindrance in the parameterization and validation of soil permittivity models, which induces high uncertainties in soil permittivity estimates. This is further complicated by the frequency dependence of permittivity.

Therefore, there is a need to collect better permittivity estimates for the
validation of microwave observations and models. However, the majority of
instruments deployed to validate microwave permittivity models, such as soil
moisture sensors, use measurement frequencies (50–70 MHz) well outside the
range of the concerned satellite observations (1400–1427 MHz). Until now,
in the absence of a better alternative, the assumption that MHz and L-Band
microwave soil permittivity are equivalent has been widely used to validate
SMAP and SMOS algorithms (Roy et al., 2017a; Lemmetyinen et al., 2016),
although this assumption was never rigorously tested. Furthermore, very few
instruments used in field conditions continuously measure microwave
permittivity in the frequency range of satellite sensors (Demontoux et al.,
2019, 2020). In addition, only a few laboratory studies have used L-Band permittivity measurements, and most of the available studies have focused on thawed soil samples (Bircher et a., 2016a, b; Demontoux et al., 2017).

The goal of this laboratory-based study is to assess OECP L-band permittivity measurements in frozen soils and the implications of substituting them with permittivity estimates taken at lower frequency by (1) evaluating the L-band permittivity of different types of soil in frozen and unfrozen conditions using an open-ended coaxial probe (OECP); (2) comparing the OECP measurements with those from a commercially available soil moisture probes operating at a lower frequency (i.e., the Stevens HydraProbe) to evaluate the potential of these lower cost probes to estimate L-Band permittivity and (3) comparing the soil permittivity measurements captured with both devices against those predicted from soil permittivity models currently used in L-band passive microwave retrieval algorithms. This paper is structured as follows: Sect. 2.1 describes permittivity instruments used in this study, Sect. 2.2 gives an overview of two soil permittivity models used for satellite retrieval and Sect. 3 provides information on the study sites, data collection and laboratory setup. Lastly, in Sects. 4 and 5, we compare and contrast the OECP measurements, commercial probe measurements and model simulations.

---

Alex Mavrovic, Renato Pardo Lara, Aaron Berg, François Demontoux, Alain Royer, Alexandre Roy (2021). Soil dielectric characterization during freeze–thaw transitions using L-band coaxial and soil moisture probes. Hydrology and Earth System Sciences 25, 1117-1131. https://doi.org/10.5194/hess-25-1117-2021. Licensed under CC-BY-4.0.
