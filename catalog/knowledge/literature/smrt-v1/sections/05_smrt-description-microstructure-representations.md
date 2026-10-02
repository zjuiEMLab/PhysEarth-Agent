# SMRT description - Microstructure representations

Different electromagnetic theories use different microstructure
representations. In the simplest setting of Rayleigh or independent Mie
scattering for a collection of spheres, the microstructure is solely
characterized by the sphere radius. The positions of the scatterers are
random and uncorrelated, meaning that interpenetration is possible. In DMRT
the microstructure is provided in terms of the Fourier transform of the
pair-correlation function (Tsang et al., 2000a) and
analytical developments have been mainly given for the SHS model, which is
determined by two parameters, the sphere radius and the stickiness τ. In
IBA, the microstructure is provided by the ACF as shown in
Sect. 2. Analytical expressions of ACF for independent spheres
and thin shells are given in (Mätzler, 1998) and MEMLS proposes
a generic exponential function (Mätzler and Wiesmann, 1999) parametrized by
the correlation length.

SMRT provides a unified and versatile vision of the microstructure
representation. Any microstructure model is defined by specifying the set of
required and optional parameters and by providing, at least for use with IBA,
an analytical expression of ACF, either for the real-space form or its
Fourier transform (or for both). Though IBA requires only the Fourier
transform, see Eq. (9), some microstructure models suggested in the
literature such as the level-cut Gaussian random field model
(Ding et al., 2010) are rather based on real-space expressions. SMRT handles
these cases using automatic Fourier transformation. Due to isotropy, required
3-D Fourier transforms can be expressed as 1-D Bessel transforms, which are numerically handled as
fast (discrete) sine transforms according to (Lado, 1971):
C̃(|kd|)=4π∫0∞drr2sin⁡(kdr)kdrC(r),
in terms of kd=|kd|.

Overall, the microstructure representation in SMRT closely follows a
library concept as commonly employed for small angle scattering
software such as in (Breßler et al., 2015). In version 1.0, five different
microstructure models are implemented as a starting point. Some
microstructure models are defined by the Fourier transform of the ACF,
and some by the real-space ACF. The most convenient characterization
of a microstructure is in terms of the Fourier transform of the
ACF. Presently the following models are implemented:

exponential:C̃ex(kd)=8πlex3f2(1-f2)[1+(kdlex)2]2,Teubner–Strey:C̃TS(kd)=8πξTS3f2(1-f2)[1+(2πξTS/dTS)2]2+2[1-(2πξTS/dTS)2](kdξTS)2+(kdξTS)4,independent spheres:C̃sph(kd)=f2(1-f2)v(a)P(kda),sticky hard spheres:C̃shs(kd)=f2v(a)P(kda)SFshs(kda)

in terms of the sphere volume v(a)=4/3πa3, the spherical form factor
P(X) defined by
P(X)=3sin⁡(X)-Xcos⁡(X)(X)32.
The SHS structure factor SFshs defined by

SFshs(X)=[A0(X)2+B0(X)2]-1A0(X)=f21-f21-tf2+3f21-f2Φ(X)+3-t(1-f2)Ψ(X)+cos⁡(X)B0(X)=f21-f2XΦ(X)+sin⁡(X)Φ(X)=3sin⁡(X)X3-cos⁡(X)X2Ψ(X)=sin⁡(X)X

with X=kda and t is given by the smallest solution of the
quadratic equation:
f212t2-τ+f21-f2t+1+f2/2(1-f2)2=0
under the additional condition t<(1+2f2)/(f2(1-f2)), which guarantees
SFshs(0) to be positive (Baxter, 1968; Tsang and Kong, 2001).

Note that each microstructure model comes with its own microstructure
parameters. The exponential model (Eq. 19) is indeed
equivalent to a real-space form Cex(r)=f2(1-f2)exp⁡(-r/lex), which is characterized by the
exponential correlation length lex. Other models come with
other parameters, which are the repeat distance dTS and the
correlation length ξTS for the Teubner–Strey (TS) model, the sphere radius
a for the independent spheres (SPH) model, and sphere radius a and stickiness τ for the SHS
model.

The necessity of also including models that are defined via the real-space ACF mainly originates from the use of level-cut Gaussian random
field models in the context commonly termed bi-continuous DMRT
(Ding et al., 2010; Chang et al., 2014). To this end we implemented a
microstructure model that is defined by

Gaussian random field:CGRF(r)=12π∫0Cψ(r)dt11-t2exp⁡-β21+twithCψ(r)=exp⁡(-r/ξGRF)1+rξGRFsin⁡(2πr/dGRF)(2πr/dGRF).

Here r denotes the lag distance from one point to another in the medium. In
the case of level-cut Gaussian random fields, the ACF of the bi-continuous
medium is determined (Teubner, 1991) by the covariance Cψ(r) of
an underlying zero-mean, unit-variance Gaussian random field ψ from
which a two-phase microstructure is obtained by “segmentation” of the
continuous field values with threshold β (cut-level parameter), which is
in one-to-one correspondence with the volume fraction f2. Our particular
choice of the field correlation function Cψ in Eq. (27)
was motivated by the apparent similarity to the Teubner–Strey model
(Eq. 19). This particular form has been investigated
by (Roberts and Torquato, 1999), for example, and involves the microstructure parameters
dGRF and ξGRF, similar to the TS model.
However, other choices for the ACF, as used in (Ding et al., 2010), for example, based
on a gamma spectral density, are possible and can be implemented in the
future.

For running SMRT with DMRT theory, the SHS microstructure must be
selected. In contrast, when using IBA, any of the above microstructure
models can be selected.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
