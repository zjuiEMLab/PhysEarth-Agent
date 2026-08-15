# Validation results

## Model initialization

### Snow input parameters

The most crucial snow input parameters required to drive MEMLS3&a are
density and correlation length. We derived these parameters from three
different snow measurement methods in order to illustrate different ways of
acquisition (Fig. 3). First, density and correlation length
were derived according to (Löwe et al., 2011)Löwe, Spiegel, and Schneebeli), using three-dimensional
reconstruction by μCT (Schneebeli and Sokratov, 2004) of snow samples cast in the
field. The sample casting technique is described in detail by
(Heggli et al., 2009)Heggli, Frei, and Schneebeli). Second, we used the SMP ((Schneebeli and Johnson, 1998)), a high resolution penetrometer. The derivation of
density and correlation length from the SMP is detailed in
(Proksch et al., 2015)Proksch, Löwe, and Schneebeli). Finally, the near-infrared photography (NIP) developed by
(Matzl and Schneebeli, 2006) allows measuring the specific surface area (SSA)
of snow which is used to define the length scale:
lc=4(1-ρsnow/ρice)SSA.
The exponential correlation length lex is then obtained from the empirical
relation,
lex=0.75lc,
put forward by (Mätzler, 2002).

As NIP does not provide the snow density, it was measured using a standard
100 cm3 density cutter with a vertical sampling interval of
4 cm. A more detailed comparison of snow measurement methods with
respect to microwave remote sensing can be found in (Proksch and Schneebeli, 2012). The
density and correlation length profiles derived by the different methods are
shown in Figs. 4 and 5. In
general, the different methods are in agreement, besides the correlation length derived from NIP, which
shows very large values in the lowest layer, an artifact of the
preparation process of the profile wall. The snow temperature was assumed to
be constant at -3 ∘C. At this temperature the snow is dry and does
not contain liquid water. The density and correlation length profiles were
averaged to a vertical resolution of 3 cm to avoid any effects of
coherent layers for the wavelength considered by SnowScat.

### Soil contribution

Besides the snow input parameters, the snow–ground reflectivity s0 is
required. Since direct measurements were not possible due to the presence of
the snow cover, this parameter has to be modeled. Here we used the empirical
model of (Wegmüller and Mätzler, 1999), which was previously used in various studies
(e.g., (Lemmetyinen et al., 2010)Lemmetyinen, Pulliainen, Rees, Kontu, and Derksen); (Takala et al., 2011)Takala, Luojus, Pulliainen, Derksen, Lemmetyinen, Kämä, Koskinen, and Bojkov); (Rautiainen et al., 2012)Rautiainen, Lemmetyinen, Pulliainen, Vehviläinen, Drusch, Kontu, Kainulainen, and Seppänen; Kontu et al., 2014)Kontu, Lemmetyinen, Pulliainen, Seppänen, and Hallikainen)). We used
a value for the complex soil permittivity of frozen ground of
ϵg=3.6+0.9i, in line with (Rautiainen et al., 2012)Rautiainen, Lemmetyinen, Pulliainen, Vehviläinen, Drusch, Kontu, Kainulainen, and Seppänen), and
set the standard deviation of the soil surface height rmsg
under the vegetation to 5 mm.

To account for the correct incidence angle at the snow–ground interface, the
following auxiliary procedure is carried out for each model run. First,
MEMLS3&a is run with s0=0 and the incidence angle at the snow–ground
interface is determined. Second, this angle was used in the model of
(Wegmüller and Mätzler, 1999) to calculate s0 which was then used to run MEMLS3&a
again, now accounting for the correct incidence angle on the snow–ground
interface. The resulting values for s0 ranged from 0.025 for
18 GHz at v-pol to 0.037 for 10 GHz at h-pol.

The model of (Wegmüller and Mätzler, 1999) gives the total reflectivity of the
snow–ground interface. To determine its specular component ss0,
we assumed ss0 to be proportional to s0. A constant factor
of 0.75 (ss0=0.75s0, for all polarizations and frequencies)
was chosen to match SnowScat measurements with our simulations.

The soil temperature was measured to be -2.5 ∘C. For the
comparison to SnowScat observations, the cross-polarization fraction q was
chosen to match the microwave measurements, which led to q=0.15. The mean
slope of surface undulations m has no influence for an incidence angle of
50∘ if values are smaller than 0.25. We choose m=0.1 for our
simulations. The sensitivity to both parameters will be discussed in
Sect. 2.

### Sky temperature

A further input to the model is the downwelling brightness temperature
Tsky of the sky. As SnowScat did not measure Tsky, we
estimated Tsky from the SodRad radiometer which measures the sky
brightness temperature Tsky,z at zenith. To fit our frequency
interval of 10–18 GHz used for the simulation, we linearly
interpolated Tsky,z values to match the interval. To convert
Tsky,z to an effective sky brightness temperature
Tsky, which is representative for the whole scenery at the main
test site, we first determined the sky opacity τz at zenith
from Tsky,z (similar to (Mätzler, 1994), their Eq. 7):
τz=-ln⁡Tsky,z-TairTback-Tair,
where Tair=270 K is the air temperature and
Tback=2.7 K is the background radiation. A good
approximation for the effective opacity (τeff) representative
of the whole scenery is given by
τeff=2τz,
as shown by (Mätzler, 2005). The sky brightness temperature is finally computed from
Tsky=2.7e-τeff+(1-e-τeff)Tair.

## Results

### Simulation results

We choose the scattering option of the improved Born approximation
(Mätzler, 1998) to run the model. For the soil, snow and Tsky
parameter settings described in Sect. 1, the results
for MEMLS3&a driven by SMP, CT and NIP input data are shown in
Fig. 6 for an incidence angle of 50∘. CT and SMP
input results in good agreement between model and measurement, with  mean
absolute errors (MAEs) of 4.0×10-3 and 4.3×10-3 for vv
polarization, 3.2×10-3 and 1.6×10-3 for hh
polarization and 4.0×10-4 and 5.3×10-4 for hv
polarization with CT and SMP inputs, respectively. NIP input leads to an
overestimation of σ0, which emerges from the NIP artefact towards the
bottom of the profile (Sect. 1) where the correlation length
values are too large. However, MEMLS3&a driven with CT input data is in good
agreement with SnowScat measurements (Fig. 7).

The dependence on the incidence angle at 10.2 and 16.7 GHz is shown
in Figs. 8 and 9. MEMLS3&a is in
general agreement with SnowScat, with  MEAs of 2.3×10-3 and 9.6×10-3 for vv polarization, 2.1×10-3 and 1.2×10-2 for hh polarization and 6.3×10-4 and 2.6×10-3 for hv polarization at 10.2 and 16.7 GHz, respectively. The
polarization difference is slightly too small at 16.7 GHz. The
SnowScat observations at different incidence angles show a certain amount of
scatter, which we attribute to the heterogeneity of the ground and snow cover
at the test site.

### Sensitivity analysis

In this section, the sensitivity of MEMLS3&a to ss0 as well as to
the two empirical parameters, the cross-polarization ratio q and the
root-mean-square slope of surface undulations m, are shown. For clarity, we
restrict ourselves to those MEMLS3&a runs which were driven with CT input
data and the best fit values mentioned above (q=0.15, m=0.1, and
ss0=0.75s0 for both polarizations), if not indicated
differently.

The specular snow–ground reflectivity ss0 is a crucial
parameter for the simulation because a higher specular snow–ground
reflectivity leads to lower backscatter. This effect is larger at low
frequencies due to the lower attenuation of electromagnetic radiation in
snow. Figure 10 shows that σ0 is significantly
increased with decreasing ss0 values and vice versa, more
pronounced at low frequencies.

The empirical cross-polarization ratio q is the fraction of cross-polarized
backscatter: increasing q lowers co-polarization and increases
cross-polarization by the same magnitude (cf. Eq. 7).
Figure 11 illustrates this by two values of q (0.15 and 0.3,
respectively).

A larger value of m represents a stronger undulated surface and increases
the spectral component of the backscatter, in particular at small incidence
angles. Figure 12 shows this behavior, with increasing
backscatter for increasing values of m and decreasing incidence angles.
Given values smaller than 0.1, m has no effect at incidence angles larger
than 25∘. Furthermore, cross-polarization is in general not affected by
m. Note that these results are only valid for the given snow and soil
conditions, i.e., the sensitivity of parameters might change in different
environmental conditions.

### Comparison with passive simulations

To prove the concept of the MEMLS architecture, which is the fundament for
MEMLS3&a, we compare our active simulations with passive simulations using
the same input data (Sect. 1). The validation data
were measured by the SodRad radiometer (Sect. 3). Similar to SnowScat,
SodRad was also pointed to the location of the in situ measurements (azimuth
angle 140∘). The instrument was operated at an incidence angle of
50∘.

To run MEMLS, 15 SMP measurements inside the main test site in
Sodankylä were used in order to capture the spatial variability of the
snowpack. For each SMP measurement one MEMLS simulation was conducted.
Figure 13 shows the results of the 15 MEMLS runs in
combination with the SodRad measurements.

The agreement between model and observation generally decreased towards
higher frequencies. At 36 GHz the average of all 15 MEMLS runs was at
maximum 22 K too low for v-pol and 12 K too low for h-pol.
Compared to the operational azimuth angle of 190∘, the difference
between model and observation decreased to 16 and 1 K for v-pol and
h-pol, respectively. The differences at 10 GHz are comparably lower,
with 5 K at maximum. The standard deviations of the 15 MEMLS runs,
which are solely due to spatial variability of the snow, increased with
frequency. At 36 GHz, the standard deviation was around 8 K
for both polarizations. The difference in azimuth angles of SodRad was even
larger, with 12 K at 36 GHz h-pol. This underlines the
influence of the spatial variability of the snowpack on modeled and measured
brightness temperatures, which will be discussed in the next section. The
agreement between model and observation should be always interpreted with
respect to the variation in brightness temperatures caused by the spatial
variability of the snowpack.

---

M. Proksch, C. Mätzler, A. Wiesmann, J. Lemmetyinen, M. Schwank, H. Löwe, M. Schneebeli (2015). MEMLS3&a: Microwave Emission Model of Layered Snowpacks adapted to include backscattering. Geoscientific Model Development 8, 2611-2626. https://doi.org/10.5194/gmd-8-2611-2015. Licensed under CC-BY-3.0.
