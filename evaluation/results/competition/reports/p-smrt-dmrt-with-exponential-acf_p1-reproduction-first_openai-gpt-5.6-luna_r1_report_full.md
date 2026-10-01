# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

The confirmed partial scope supports only the registered SMRT QCA-CP configuration (`smrt@1.5.1`) and its `tb_h`/`tb_v` outputs. DMRT-ML and DMRT-QMS remain unavailable and will be explicitly excluded—not approximated by the local DMRT options.The image shows a two-panel figure:

- **Panel (a):** brightness temperature in **K** versus incidence angle in **degrees**, with visible x-ticks from 10° to 60° and y-ticks from 240–265 K. The legend distinguishes solid **SMRT QCA-CP V/H**, dashed **SMRT QCA V/H**, square **DMRT-ML Fortran V/H**, and right-pointing triangle **DMRT-QMS V/H**. The supported QCA-CP curves rise toward a broad maximum near 45–50° for V polarization, while H polarization declines increasingly toward 60°. The unavailable reference curves are visibly present but will not be reproduced or treated as validated.
- **Panel (b):** backscattering coefficient in **dB** versus incidence angle, with SMRT QCA and DMRT-QMS VV/HH/HV curves. It is outside the confirmed `tb_h`/`tb_v` partial scope and will be reported as unavailable.
- The figure has panel annotations **(a)** and **(b)** and no additional scientific annotations. The source conditions shown in the caption are semi-infinite snow, density 300 kg m⁻³, sphere radius 100 μm, temperature 265 K, stickiness 0.5, and frequency 37 GHz. No curve values were digitized. [figure:smrt-v1#fig04] [paper-smrt-v1#08]

I will now define the supported reproduction as panel (a), SMRT QCA-CP only, with panel (b), DMRT-ML, and DMRT-QMS explicitly unavailable or out of scope.
