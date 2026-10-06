# SMRT description - Model implementation

The model implementation is highly modular to allow switching among several
formulations at each stage of the computation and adding new formulations
defined by users. Another feature is the extensive use of default behaviors
to facilitate an easy use by beginners but still allow experts to set
advanced formulations for specific investigations or sensitivity
studies, for example. The code is carefully encapsulated; each “science” component
(indicated by the orange color in Fig. 2 and defined
in Sect. 1) is designed as an independent module.
Table 1 summarizes the available formulations for each
component in version 1.0. Additional modules contain input–output components
(green boxes in Fig. 2) and core
infrastructure components (blue boxes in Fig. 2).
Green and blue components do not contain any science and the core
component should not be modified by the users or scientific developers.

To illustrate the mode of operation of the model it is instructive to relate the instructions of a tiny but
fully functioning code snippet to the model operations carried out
in the background:

In the code snippet first a snowpack is built (function
make_snowpack) by providing the
defining properties of each layer, interface, and the substrate. Layer
characteristics always include density and a microstructure model to use
(e.g., microstructure using exponential autocorrelation or SHS). The
specification of temperature is optional, mostly relevant for the passive
mode. Additional parameters depend on the selected microstructure model. For
instance, the exponential function requires the exponential correlation
length while SHS requires the sphere radius and stickiness. In the code
example, a 100 m thick snow layer is used (i.e., to mimic a semi-infinite
medium) with a density of 320 kgm-3, correlation length of
50 µm, and temperature of 270 K. For the interfaces
among snow layers, the choice is presently
limited to a “flat interface”, which does not require any parameter. In the
future rough interfaces could be implemented. The substrate can be selected
from various models of soil, a homogeneous medium with a flat surface (e.g.,
bulk of isothermal ice), or a reflector with reflectivity coefficients
prescribed by the user. Each model has specific parameters and all of them
require temperature for the passive mode.

In the second step, the definition of the model is completed by selecting the
electromagnetic theory (that computes the scattering and absorption
coefficients, phase matrix, and effective permittivity) and the radiative
transfer solver. As mentioned before, some electromagnetic theories are only
compatible with particular microstructure models, e.g., DMRT only works with
SHS and Rayleigh works with any microstructure that defines a radius but
inherently considers independent spheres. For solving the radiative transfer
equation, only the discrete ordinate and eigenvalue (DORT) method is
currently implemented, based on
(Picard et al., 2004; Picard et al., 2013), though two- or six-flux
solvers (Wiesmann and Mätzler, 1999) could be implemented in the future as well. In
the next step the sensor characteristics are specified (active or passive,
frequencies, polarizations, etc.). For convenience, a list of predefined
sensors is available (like here, AMSR-E) but sensors with arbitrary
characteristics can be defined. The last step is to launch the simulation by
combining the prescribed snowpack, the sensor, and the defined “model” to
obtain a result (e.g., brightness temperature, backscattering coefficient, or
Müller matrix). The result of this code shows a brightness temperature of
268.2 and 251.7 K at V and H polarization, respectively.

The model is implemented in Python (2.7+ and 3.4+), which makes it easy to
implement switchable formulations with default and extensible behaviors. This
also avoids the cumbersome step of code compilation, though at the cost of a
computational overhead compared to compiled languages. To limit this
drawback, the model uses common numerical libraries, such as
NumPy and SciPy extensively, allowing fast and numerically accurate calculations. The
code is fully documented. It also entirely uses SI units without prefix to
avoid any ambiguity.

In addition, we provide different tools for convenience: (1) to facilitate
convenient computation of time series or sensitivity study by a few,
clear-cut lines of code the model can be run on lists of different snowpacks.
(2) To foster comparisons between SMRT and other common existing models
(MEMLS, DMRT-QMS, and HUT), we provide language bindings to seamlessly run
these models within SMRT, which use the prescribed snowpack in SMRT and
collect results as if they were produced by SMRT. This requires that the
source code of these models is separately installed (they are not distributed
with SMRT for licensing reasons). Note that this feature is currently limited
to the passive mode.

---

Ghislain Picard, Melody Sandells, Henning Löwe (2018). SMRT: an active–passive microwave radiative transfer model for snow with multiple microstructure and scattering formulations (v1.0). Geoscientific Model Development 11, 2763-2788. https://doi.org/10.5194/gmd-11-2763-2018. Licensed under CC-BY-4.0.
