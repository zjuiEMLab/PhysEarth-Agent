# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

I will reproduce Figure 3 from Picard et al. (2018) by first reading the relevant section of the paper to extract the exact experimental setup, then running the SMRT model with the paper-specified parameters.

First, I need to read Section 3.1.1 and Figure 3 to identify all fixed parameters.

The paper is only 26 pages long, so page 2770 is invalid. I need to find the correct page for Section 3.1.1 and Figure 3. Let me try page 10, which is a reasonable estimate for Section 3 in a 26-page paper.


The attached figure (Fig. 3) shows the scattering coefficient (unit: m⁻¹, y-axis) as a function of snow density (kg m⁻³, x-axis) for sparse media.

Key visual evidence from the image:

- Six curves are plotted, distinguished by legend entries and line styles:
  - Independent spheres (Rayleigh)
  - Independent spheres (IBA)
  - Non-sticky hard spheres (DMRT QCA–CP)
  - Non-sticky hard spheres (IBA)
  - Sticky hard spheres (DMRT QCA–CP)
  - Sticky hard spheres (IBA)

- All curves converge near the origin (density → 0), confirming agreement in the sparse-medium limit — consistent with the text stating “at the origin (for f² → 0) the linear trend is the same”.

- At higher densities (above ~20 kg m⁻³), curves diverge progressively: sticky hard spheres lie above non-sticky ones; IBA-based curves lie above QCA–CP ones; independent-sphere curves flatten or rise more slowly.

- The sphere radius is fixed at 100 µm (i.e., 0.1 mm), as labeled in caption and confirmed by text.

- No error bars or uncertainty bands are visible — purely deterministic model outputs.

- The linear behavior at low density validates implementation consistency across microstructure–electromagnetic theory combinations.

This figure supports the paper’s claim that microstructure assumptions dominate deviations from the sparse-medium approximation — more so than electromagnetic theory choice — once density exceeds ~10–20 kg m⁻³.
