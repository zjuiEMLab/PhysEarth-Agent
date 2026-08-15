# Discussion

The soil temperature offsets from the water freezing point are consistent between the OECP and HP measurements for both the freezing and thawing transitions. The difference ranges from -1.00 to +0.83 ∘C when evaluating the soil temperature offset at maximum transition rate (Tables S1 and S2 in the Supplement). The main difference between the permittivity measured at microwave and MHz frequencies appears to be a permittivity offset and that the temperature span of the freeze–thaw transition is dependent on the soil type. Therefore, based on the offsets seen in Tables 2 and 3 and Fig. 9, a calibration equation between the L-band and MHz permittivity can be obtained for a given soil. This would allow for the use of low-cost and widespread instrumentation in the MHz spectrum, such as the HP, to act as surrogate L-band soil permittivity measurements. This opens up the possibility of studies over large areas through already deployed networks. It should be remembered that MHz permittivity measurements have already been used to test SMAP and SMOS algorithm's permittivity under the assumption that the MHz and L-band permittivity are equivalent (Roy et al., 2017a; Lemmetyinen et al., 2016). As our results showed, MHz and L-band soil permittivity trends are close to each other but not identical; therefore, the previous assumption must be reconsidered because neglecting the frequency dependence of soil permittivity induces a bias in the results.

Ground and satellite-based L-band radiometric measurements are very sensitive to the freezing of the first centimeter of soil (Rowlandson et al., 2018; Roy et al., 2017a, b; Williamson et al., 2018). Therefore, the shallower depth (∼0.4–1 cm) and smaller volume (∼4–10 cm3) probed by the OECP makes it a potentially more suitable instrument to study the freeze–thaw signal observed from L-band radiometers.

The hysteresis effect observed in Figs. 5 to 8 was likely amplified by the
experimental setup because of the fast temperature transition speed used.
Nonetheless, the hysteresis effect is expected to occur because of the
asymmetry between the freezing and thawing processes. The classic Zhang's model only takes into account the ice fraction below 0 ∘C; the resulting liquid water fraction should not be interpreted as actual liquid water at temperatures below the freezing point but rather as an aggregate of the heterogeneous soil temperature. Figure 10 demonstrates the hysteresis effect
simulated by using a modified version of Zhang's model that considers the ice
fraction above and below 0 ∘C. This ice fraction was prescribed
following an exponential function
(esolTesolT+1)
around the freezing point with a ±0.5 ∘C temperature offset for
the freezing and thawing cycles. For a proper estimation of the ice fraction in
soil, the evolution of the soil and boundary conditions should be simulated
using more complex models like CLASSIC (Melton at al., 2020).

We further tested the hypothesis that the hysteresis amplitude is correlated
with the temperature transition speed using an OBS soil sample with a slower
freeze–thaw transition rate. The hysteresis effect displayed in Fig. 11 is
still noticeable (<1 ∘C offset from the freezing point) but not as pronounced as in Figs. 5 to 8 (between 2 and 3 ∘C offset from the freezing point). Since the soil permittivity has an important impact on brightness temperature as observed by satellite-based radiometers (Roy et al., 2017a, b; Jonard et al., 2018; Prince et al., 2019;), it is notable that this hysteresis effect around the freezing point is not taken into account in current soil models used in microwave satellite retrieval algorithms. The omission of this effect may potentially have an impact on freeze–thaw detection products and their validation. It should be noted that this hysteresis effect is not always observed for in situ data due to
the instrumental uncertainty not being precise enough to conclusively separate the hysteresis effect in situ (e.g., Pardo Lara et al., 2020, 2021). The effect might also be mitigated at the pixel scale of modern satellites because of spatial heterogeneity (Roy et al., 2017b).

Based on our simulations, ice fraction representation in Zhang's model results in a more physically appropriate representation of processes around
the freezing point and results in freeze–thaw transitions closer to observations. It should be noted that an ice fraction could be implemented
in TD GRMDM as well. To reproduce the hysteresis effect at freeze–thaw
transition, two approaches are possible. An empirical approach could be used
by implementing a double threshold using distinct ice fraction empirical
relationships for (1) the freezing and (2) the thawing cycle. This empirical
approach would require determining independently for each transition type
the freezing or thawing hysteresis amplitude as a temperature offset between
the state transition and 0 ∘C. This would depend on liquid water
content, textural composition, solute concentration and the pore pressure of the soil (Daanen et al., 2011). The alternative would be to couple dielectric models with soil physical models that integrate the time evolution of soil physical properties (e.g., CLASSIC model; Melton at al., 2020). Soil physical models provide an estimate of the ice fraction through time, which is used by dielectric models to estimate soil permittivity. Such coupling should only impact the freeze–thaw transition where the ice fraction is a relevant parameter.

---

Alex Mavrovic, Renato Pardo Lara, Aaron Berg, François Demontoux, Alain Royer, Alexandre Roy (2021). Soil dielectric characterization during freeze–thaw transitions using L-band coaxial and soil moisture probes. Hydrology and Earth System Sciences 25, 1117-1131. https://doi.org/10.5194/hess-25-1117-2021. Licensed under CC-BY-4.0.
