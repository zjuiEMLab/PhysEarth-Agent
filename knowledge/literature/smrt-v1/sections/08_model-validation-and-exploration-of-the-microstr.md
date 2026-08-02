# Model validation and exploration of the microstructure - Comparison with other reference models

## The sparse medium approximation

For a sparse medium, i.e., when density tends to zero, many formulations must
show the same behavior as the independent spheres with Rayleigh or Mie
theory. In SMRT, it is possible to run several combinations of microstructure
and electromagnetic models as shown in Fig. 3. The
results for 100 µm radius spheres show that at the origin (for
f2→0) the linear trend is the same for several microstructures
(independent spheres, non-sticky hard spheres and sticky hard spheres) and
different theories (Rayleigh, DMRT QCA-CP, IBA). These results provide a
first technical validation of the SMRT implementation of several theories.
However, the sparse medium approximation is valid only for very low densities
in the range 10–20 kgm-3 which is unrealistic for the goal of
snow modeling. It is well known that scattering in snow must be treated with
dense media theories such as DMRT or IBA. The results from
Fig. 3 already indicate that the influence of
microstructure on deviations from the sparse medium assumption for the
scattering coefficient at low densities is more severe than the
electromagnetic theory. The next sections therefore consider dense media and
a detailed comparison between different microstructure models.

## Comparison of SMRT to DMRT-based models

We compare SMRT to results produced from original code of several DMRT
variants. Figure 4 shows the angle dependence of the brightness
temperature and backscattering coefficient for SMRT DMRT compared to other
models for a semi-infinite medium with a sphere radius of 0.1 mm,
density of 300 kgm-3, stickiness of τ=0.5, and temperature
of 256 K. The results reveal that the closest implementation to SMRT
DMRT is the model DMRT-ML (Picard et al., 2013). Both use exactly
the same formulation for the scattering and absorption coefficient, namely
DMRT QCA-CP with small, monodisperse spheres in the short-range approximation
(requiring moderate stickiness, i.e., stickiness parameter should not be
small). They also use a similar method to solve the radiative transfer
equation, which explains the small root-mean-square difference in brightness
temperature of about 0.03 K obtained at both polarizations for the
angle range 0–60∘. In contrast, the comparison of SMRT to DMRT-QMS
shows larger differences since the latter computes scattering by DMRT Mie QCA
and implements a different connection of streams between layers in the
interface conditions for solving the radiative transfer equation
(Picard et al., 2013; Liang et al., 2008). Nevertheless, the differences at both
polarizations do not exceed 0.3 K RMS, which is acceptable
considering the implementations are different and fully independent. We
attribute this difference solely to the radiative transfer solvers because we
confirmed that running an SMRT simulation with prescribed scattering and
absorption coefficients and effective permittivity pre-computed from
DMRT-QMS, the brightness temperature difference of 0.3 K RMS remains
unchanged. In active mode (Fig. 4b), the difference is small as
well, 0.65 dB RMS at HH and VV polarizations and 1.4 dB RMS
at HV polarization.

The previous results were obtained for small scatterers and moderate
stickiness, which is compatible with the short-range approximation. It is
therefore of interest to investigate the limits of this implementation. To
this end, Fig. 5 shows two plots for brightness
temperature and backscattering coefficient as a function of sphere radius and
stickiness, respectively. In the first column plot, stickiness is fixed at
0.5 and in the second, the radius is set to 200 µm. DMRT-QMS is
considered here as the reference because it implements DMRT QCA Mie, which
has no theoretical limitations on the size of the particles and on the
stickiness parameter. The results show that for radii larger than
185 µm (285 µm) the error starts to exceed 1 K
(5 K). Translated to surface specific area (SSA) values, this
corresponds to lower bounds of 17 and 11 m2kg-1, respectively,
which is relatively restrictive for most snow types
(Domine et al., 2007)Domine, Taillandier, and Simpson; Roy et al., 2013; Picard et al., 2014), but may still be sufficient for
some applications particularly at lower frequencies. Similarly, stickiness
values lower than 1 (0.3) yield an error larger than 1 K
(5 K). Even though stickiness values for natural snow are strictly
unknown due to the lack of direct measurements, indirect estimates suggest
that values below unity are common (Löwe and Picard, 2015; Roy et al., 2013). For
the active mode, the DMRT QCA short range does not significantly depart from
the reference simulations (less than 1 dB) but the code fails to run
for a radius above 280 µm and for stickiness lower than 5. This is
due to an unrealistically large scattering coefficient compared to the
absorption coefficient, leading to non-real eigenvalues in the
diagonalization for the DORT method.

To overcome the restrictive range of validity of the DMRT QCA short range, and
considering that SMRT version 1.0 does not provide DMRT QCA in the long-range
approximation, an alternative strategy is to combine IBA with the SHS
microstructure model. Figure 5 shows the results, which
are much closer to DMRT QMS than DMRT QCA. The difference always remains
lower than 5 K for the brightness temperature and 0.5 dB for
the backscattering coefficient in the explored range of input parameters. The
brightness temperature becomes larger than 1 K only for radii larger than
285 µm and stickinesses lower than 0.3. The difference in
backscattering coefficient does not show significant dependence on the
parameters varied. This numerical result confirms the quasi-equivalence of
the DMRT and IBA theories when using the same microstructure as shown
theoretically by (Löwe and Picard, 2015). It even extends this work as only the
short-range approximation was considered by (Löwe and Picard, 2015).

## Comparison of SMRT to MEMLS-IBA

Figure 6 shows the brightness temperature predicted
by MEMLS along with SMRT using the original IBA and the default IBA, which
computes the effective permittivity using the Polder–von Santen mixing
formula. For a faithful comparison between SMRT and MEMLS, it is required to
select the IBA formulation in MEMLS among the 12 available scattering
formulations. In addition, MEMLS with IBA allows a choice among different
grain shapes, which controls the mean squared field ratio Y2. As SMRT only
considers spherical scatterers, MEMLS grain type must be set accordingly
(grain type 2 in MEMLS code). The microstructure in SMRT is set to the
exponential autocorrelation function as in MEMLS (Mätzler and Wiesmann, 1999) and
depends on the correlation length, which is set to 100 µm in this
computation. The results show a difference of 1.2 and 1.6 K at V
and H polarization, respectively, between MEMLS and SMRT with the original IBA.
The cause is not the scattering and absorption coefficients, which are very
close in both models (κs=0.2054m-1 and
κa=0.3092m-1 for MEMLS and
κs=0.2056m-1 and
κa=0.3087m-1 for SMRT). Likewise, the effective
permittivities are numerically close, 1.5244 in MEMLS and 1.5236. The
difference is thus likely due to the different methods used to solve the
radiative transfer. MEMLS uses a six-flux solver while SMRT uses the DORT method with 32
streams in the simulations presented in this paper. Similar discrepancies
were observed when comparing MEMLS to DMRT-ML and DMRT-QMS
(Royer et al., 2017). An implementation of the six-flux solver in SMRT
would provide a route to further explore this issue. It is worth noting that
setting a low number of streams in DORT (e.g., two or six) is not recommended and
is not equivalent to the two-flux and six-flux methods, which use specific stream
angles and integrals of the bistatic scattering coefficient.

Figure 6 also highlights the difference between
original IBA and the default IBA in SMRT. The default IBA results in higher
brightness temperature by 1.2 and 1.3 K on average at
V and H polarization, respectively. The reason is a slightly higher absorption of
κa=0.3426m-1 versus
κa=0.3092m-1, while all the other properties remain
the same.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
