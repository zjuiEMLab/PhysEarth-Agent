# SMRT description - Improved Born approximation

The implementation of the IBA in SMRT closely
follows the original work of (Mätzler, 1998) with slight differences. The
phase function in the 1–2 frame (Mätzler, 1998; Ding et al., 2010) is
calculated for a two-phase medium (subscript 1 denotes the host constituent and
subscript 2 denotes the scattering constituent, e.g., air and ice are used for
light snow) as

p(ϑ,φ)1–2 frame=f2(1-f2)(ϵ2-ϵ1)2Y2(ϵ1,ϵ2)k04M(|kd|)sin⁡2χ,

where the angles (ϑ, φ) denote the scattering direction if
the incident direction is taken as the polar axis. The free-space wave number is
denoted by k0=2πν/c with the wave frequency ν. The volume
fraction of constituent 2 is denoted by f2 and related to the medium
density ρ by f2=ρ/ρ2. The relative permittivities of
phases 1 and 2 are denoted by ϵ1 and ϵ2. The temperature and
frequency dependence of the permittivity is taken into account but not made
explicit in the notation. Polarization information is carried in the
polarization angle χ, which is the angle between the incident electric
field and scattering direction. This angle is given by sin⁡2χ=1-sin⁡2ϑcos⁡2φ (Ishimaru, 1997). The mean
squared field ratio of field Y2 (Mätzler, 1998) accounts for the difference in electric field inside the
scatterers and the background. This can be represented analytically for small
spherical or ellipsoidal scatterers with random orientations as follows
(Sihvola, 1999):
Y2=13∑j=13ϵaϵa+(ϵ2-ϵ1)Aj2,
where Aj are the depolarization factors along the Cartesian directions. In
SMRT version 1.0, only isotropic microstructures are considered, which implies
Aj=1/3. The apparent permittivity is ϵa=13(2ϵeff+ϵ1) (Mätzler, 1998). The
microstructure term M(|kd|) is a function of the difference
of wave vectors in the effective medium in the incident and scattering
directions, so the modulus is given by
|kd|=2k0ϵeffsin⁡Θ2,
where Θ is the scattering angle, i.e., the angle between the incident
and scattering direction, and ϵeff denotes the effective
permittivity, which is by default computed with the Polder–van Santen mixing
formula (Sihvola, 1999). This microstructure term can be determined from
the Fourier transform C̃ of the autocorrelation function of the
medium indicator function as (Löwe and Picard, 2015)
M(|kd|)=14πC̃(|kd|)f2(1-f2).
Due to the assumption of isotropy, the Fourier transform of the correlation
function C̃(kd)=C̃(|kd|)
depends only on the magnitude |kd| of the scattering vector.
Several analytical functions for C̃ are implemented in SMRT,
thus offering different representations of the microstructure to choose from.
This is detailed in Sect. 3.

Equations (6) to (9) fully determine the phase function in
the 1–2 frame. The 4×4 phase matrix in the principal frame is
obtained following the method of (Tsang et al., 2007) and (Ding et al., 2010).
Co-polarization phase function matrix elements can be determined for each
ϑ  through calculation of p11=p1–2 frame(ϑ,φ=π/2), and p22=p1–2 frame(ϑ,φ=π) and cross-polarization terms in the 1–2 frame
vanish, viz. p12=p21=0. Since the structure of the IBA phase matrix
is identical to the phase matrix from Rayleigh and strong fluctuation theory
(SFT)
(Tsang et al., 2007), the last two diagonal elements can be estimated as
p33=p44=p11p22. Finally, the 4×4 phase
matrix P in the principal frame of the radiative transfer equation
(with z axis normal to the Earth surface) is obtained by rotation
(Tsang et al., 2007; Mätzler et al., 2006):

P(μ,ϕ,μ′,ϕ′)=P11P12P130P21P22P230P31P32P330000P44,=cos⁡2αsin⁡2α-12sin⁡2α0sin⁡2αcos⁡2α12sin⁡2α0sin⁡2α-sin⁡2αcos⁡2α00001⋅p110000p220000p330000p44⋅cos⁡2α′sin⁡2α′12sin⁡2α′0sin⁡2α′cos⁡2α′-12sin⁡2α′0-sin⁡2α′sin⁡2α′cos⁡2α00001,

where α (α′) is the angle of rotation from the
1–2 frame to the incident (scattering) frame. It is related to
the incident and scattering zenith and azimuth angles in the principal frame
by

cos⁡α=cos⁡θ′sin⁡θ-cos⁡θsin⁡θ′cos⁡(ϕ-ϕ′)sin⁡Θ

(Mätzler et al., 2006; Tsang et al., 2007).
The scattering angle Θ is given by cos⁡Θ=cos⁡θcos⁡θ′+sin⁡θsin⁡θ′cos⁡(ϕ-ϕ′)
(Mätzler et al., 2006) so that it follows

cos⁡2α=cos⁡θ′sin⁡θ-cos⁡θsin⁡θ′cos⁡(ϕ-ϕ′)21-cos⁡θcos⁡θ′+sin⁡θsin⁡θ′cos⁡(ϕ-ϕ′)2.

The angle α′ is obtained by exchanging primed and
non-primed angles.

Because the IBA phase matrix in the 1–2 frame is diagonal and the fourth
component of the rotation matrix is orthogonal to the three others, the
fourth component of the phase matrix in the main frame is also orthogonal to
the three others. Except if the full Müller matrix is required by the
user, the radiative transfer equation can be solved considering only the
three first components, thus reducing the computational cost. This is the way
it is implemented in SMRT.

The scattering coefficient κs is, by
definition, calculated from the integration of the phase matrix over all
incident directions:
κs(θ,ϕ)=14π∫4πdΩ′P(θ,ϕ;θ′,ϕ′).
Taking into account the isotropy of the medium (Tsang et al., 2007), the
integral can be computed in the 1–2 frame and yields a diagonal matrix with
all elements equal to
κs=π∫0πp11(ϑ)+p22(ϑ)sin⁡ϑdϑ.

For the absorption coefficient, κa is also diagonal
and a multiple of the unit matrix. SMRT provides two different
implementations of IBA. The first one is called “original IBA” and uses the
formulation introduced in (Mätzler, 1998), which is used in MEMLS
(Mätzler and Wiesmann, 1999):
κa=k0f2ℑϵ2Y2,
where ℑ denotes the imaginary part. The second one is called just
“IBA” and uses
κa=2k0ℑϵeff.
based on the Polder–van Santen mixing formula for ϵeff.
The latter is the recommended default in SMRT because the Polder–van Santen
mixing formula has been shown to satisfy formal requirements (e.g., symmetry
in background and inclusion permittivities) and to perform well for snow over
the full range of fractional volumes (Sihvola, 1999). This
allows, in particular, the representation of pure ice lenses and ice crusts
in the snowpack using IBA.

The effective permittivity is not only needed to compute the absorption
coefficient but also implicitly to compute the boundary reflection equations
(Eqs. 3 and 4) to account for the
refraction (Snell's law) and the Fresnel coefficients at the interfaces. The
default formulation in SMRT IBA is the Polder–van Santen mixing formula as
in (Mätzler, 1998) and (Mätzler and Wiesmann, 1999). Compared to
the classical Maxwell–Garnett formula, it is symmetrical between the
scatterers and the background and has been shown to be slightly better for
snow (Mätzler, 1996; Sihvola, 1999).

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
