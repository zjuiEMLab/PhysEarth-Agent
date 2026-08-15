# SMRT description - Model architecture

The model is centered around the radiative transfer equation to
compute the propagation of radiative energy in the medium produced by
thermal emission in the medium (passive mode) and received from the
sky (radar beam in active mode and sky thermal emission in passive
mode). In addition to the radiative transfer equation, the other main
components include the electromagnetic model that describes
electromagnetic behavior of snow (i.e., the effective refractive index
or permittivity, absorption and scattering coefficients, and phase
function) and the boundary conditions between layers (called interfaces
hereinafter) and at the bottom interface (called substrate
hereinafter). All these components are well isolated in the code and
various formulations from the literature are available. Here, only the
common elements are presented; the switchable formulations are
described in the following sections and appendix.

The model solves the time-independent
radiative transfer equation assuming a horizontally homogeneous medium with
isotropic snow at the microscopic level this is

μ∂Iμ,ϕ,z∂z=-κeμ,ϕ,zIμ,ϕ,z+14π∬4πP(μ,ϕ;μ′,ϕ′,z)Iμ′,ϕ′,zdΩ′+κaμ,ϕ,zαT(z)1,

where I=(IV,IH,U,V) is the reduced
specific intensity defined as I=I′/n2, where
I′ is the specific intensity and n the refractive index at the
same location (Mobley, 1994). P(μ,ϕ;μ′,ϕ′,z) is the 4×4 phase matrix.
κa and κe are the
absorption and extinction coefficients and the vector
1=(1,1,1,1). The extinction coefficient is given by
κe=κs+κa, where κs is the
scattering coefficient. Directions are defined by the cosine of the zenith
angle μ and by the azimuthal angle ϕ. The associated solid angle is
Ω. The z axis is taken upward (as usual in Earth science), meaning
that the incident beam and downwelling radiation have μ<0, while
upwelling radiation has μ>0. This equation is valid in both active and
passive modes in the microwave range. The brightness temperature
TB,p, with p=H or V, is proportional to the reduced
specific intensity Ip=αTB,p (Rayleigh–Jeans
approximation) with α=2ν2k/c02, where k and c0 are the
Boltzmann constant and speed of light in the vacuum. ν is the wave
frequency. In practice, for the passive mode and by using the linearity of
Eq. (1), Ip can be replaced by the brightness
temperature and α set to 1. This is the case in our code.

Further assuming that (i) the medium is azimuthally symmetric and (ii) the
medium is composed of homogeneous layers (Fig. 1), the
equation becomes

μ∂I(l)μ,ϕ,z∂z=-κs(l)μ+κa(l)μI(l)μ,ϕ,z+14π∬4πP(l)(μ,μ′,ϕ-ϕ′)I(l)μ′,ϕ′,zdΩ′+κa(l)μT(l)1.

Here l=1…L denotes the layer index ranging from the top
(l=1) to the base (l=L).

The continuity conditions at layer interfaces and the boundary
condition at the bottom interface are expressed by

I(l)μ<0,ϕ,zl-1=Rspec,top,(l)(μ)I(l)-μ,ϕ,zl-1+12π∬2π,μ′>0Rdiff,top,(l)(μ,μ′,ϕ-ϕ′)I(l)μ′,ϕ′,zl-1dΩ′+Tspec,bottom,(l-1)(μ,Sl,l-1(μ))I(l-1)Sl,l-1(μ),ϕ,zl-1+12π∬2π,μ′<0Tdiff,bottom,(l-1)(μ,μ′,ϕ-ϕ′)I(l-1)μ′,ϕ′,zl-1dΩ′,

I(l)μ>0,ϕ,zl=Rspec,bottom,(l)(μ)I(l)-μ,ϕ,zl+12π∬2π,μ′<0Rdiff,bottom,(l)(μ,μ′,ϕ-ϕ′)I(l)μ′,ϕ′,zldΩ′+Tspec,top,(l+1)(μ,Sl,l+1(μ))I(l+1)Sl,l+1(μ),ϕ,zl+12π∬2π,μ′>0Tdiff,top,(l+1)(μ,μ′,ϕ-ϕ′)I(l+1)μ′,ϕ′,zldΩ′.

zl is the z
position of the bottom of layer l and conversely zl-1 is the height of
the top of the layer l. R and T are reflectivity and
transmittivity
matrices. The superscript “spec” denotes the specular (a.k.a.
coherent) components and “diff” is the diffuse (a.k.a incoherent)
components. For a perfectly flat interface, the diffuse component is zero and
the specular component is given by the Fresnel coefficients
(Jin, 1994). The “top” superscript denotes the
coefficients from a layer to the one above, and “bottom” denotes
coefficients to the layer below. The function Sl1,l2(μ1) computes
the change of beam incidence angle from layer l1 to layer l2 due to
refraction. This function writes accordingly with the Snell–Descartes law:
Sl1,l2(μ1)=1-nl12nl221-μ12,
where nl denotes the refractive index in layer l. In case of total
reflections, Sl1,l2(μ1) is a purely imaginary complex number. In
this case, for the sake of simplicity, we consider the transmittivity matrix,
is null.

Given the main governing equations (Eqs. 2, 3
and 4) it is instructive to summarize the architecture and
main components of SMRT (Fig. 2). The quantities
κs, κa, and P in the
main equation (Eq. 2) are computed independently for each layer
by the electromagnetic model component
(Fig. 2) using one of the implemented theories (in
version 1.0 IBA, DMRT, independent Rayleigh scattering) and input parameters
characterizing the snow microstructure component. The interlayer
reflectivity and transmittivity coefficients in Eqs. (3)
and (4) are computed with the interface component
(e.g., with Fresnel coefficients for flat interfaces) and with the
substrate component. The effective refractive index needed for these
calculations is given by the electromagnetic model component, which
in turn uses material permittivity formulations of the raw materials
(ice, water, air, etc.). Once fully specified, the equations are
numerically solved with the radiative transfer equation solver
component, which provides a numerical method adapted to the plane-parallel,
multilayer configuration, and the result, that is, the intensity emerging in
all or specific directions from the snowpack, is returned to the user. All
formulations and methods for each component are described in the Appendix,
except the IBA (one of the electromagnetic
models detailed in the next section), which is essential to understand the
representation of snow microstructure in SMRT.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
