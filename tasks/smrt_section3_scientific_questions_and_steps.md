# Scientific Questions and SMRT Reproduction Steps for Section 3

**Reference paper:** Picard et al. (2018), *Simulation of the microwave emission of multi-layered snowpacks using the Dense Media Radiative transfer theory: the SMRT model*, Geoscientific Model Development, 11, 2763–2788.

**Objective:** Reproduce and verify the numerical experiments in Section 3 using SMRT, while separating differences caused by electromagnetic theory, microstructure representation, radiative-transfer solvers, and numerical implementation.

---

## 1. The Sparse Medium Approximation （Section 3.1.1）

### Scientific question

**Under what snow-density range do Rayleigh theory, IBA, and DMRT converge to the same first-order scattering behavior, and at what density do particle correlation and dense-medium effects cause their predictions to diverge?**

### Key steps using SMRT

1. **Construct the sparse-density experiment**
   - Use a frequency of 37 GHz.
   - Fix the ice-sphere radius at \(100\,\mu\text{m}\).
   - Vary snow density from approximately 1 to 96 kg m\(^{-3}\), preferably in 5 kg m\(^{-3}\) increments.
   - Define independent spheres, nearly non-sticky hard spheres, and sticky hard spheres.

2. **Calculate the electromagnetic scattering coefficients**
   - Run Rayleigh theory with independent spheres.
   - Run IBA with independent spheres.
   - Run IBA with non-sticky and sticky hard-sphere microstructures.
   - Run DMRT QCA-CP with the same hard-sphere microstructures.
   - Extract the scattering coefficient \(k_s\) without introducing radiative-transfer effects.

3. **Verify the common sparse-medium limit**
   - Plot \(k_s\) against density for every configuration.
   - Fit linear regressions over progressively larger low-density ranges.
   - Compare the fitted slopes and verify that the intercepts approach zero.
   - Confirm whether all theories converge to the Rayleigh first-order limit.

4. **Identify the breakdown density**
   - Use the Rayleigh linear solution as the sparse-medium reference.
   - Calculate the relative deviation of each IBA and DMRT result from this reference.
   - Report the densities at which the deviation first exceeds 1%, 5%, and 10%.
   - Examine how stickiness changes the onset and direction of the deviation.

5. **Attribute the observed divergence**
   - Compare IBA and DMRT using identical microstructure parameters to isolate theory differences.
   - Compare different microstructures under the same electromagnetic theory to isolate correlation effects.
   - Determine whether the divergence is predominantly caused by dense-medium corrections, the structure factor, or their interaction.

### Expected outputs

- Scattering coefficient versus density.
- Low-density linear-fit slopes and intercepts.
- Relative deviation from the Rayleigh limit.
- Estimated validity range of the sparse-medium approximation.
- Separate assessment of electromagnetic-theory and microstructure effects.

---

## 2. Comparison of SMRT to DMRT-Based Models

### Scientific question

**Can SMRT reproduce the passive brightness temperatures and active backscatter predicted by DMRT-ML and DMRT-QMS under identical snow and observation conditions, and can the remaining discrepancies be attributed to the electromagnetic formulation, the short-range approximation, or the radiative-transfer solver?**

### Key steps using SMRT

1. **Reconstruct the common reference configuration**
   - Create a homogeneous snow layer approximately 200 m thick to represent a semi-infinite medium.
   - Use a density of 300 kg m\(^{-3}\), temperature of 265 K, sphere radius of \(100\,\mu\text{m}\), and stickiness \(	au=0.5\).
   - Use 37 GHz and incidence angles from approximately \(10^\circ\) to \(60^\circ\).
   - Match the substrate, atmosphere, dielectric model, and interface assumptions used in the reference models.

2. **Run the baseline passive and active comparisons**
   - Compare SMRT `dmrt_qcacp_shortrange` with DMRT-ML.
   - Compare SMRT `dmrt_qca_shortrange` with DMRT-QMS.
   - Calculate passive \(T_{b,V}\) and \(T_{b,H}\).
   - Calculate active \(\sigma^0_{VV}\), \(\sigma^0_{HH}\), and \(\sigma^0_{HV}\), where supported.

3. **Quantify agreement**
   - Preserve each model's native angle grid before interpolation.
   - Calculate polarization-specific bias, RMSD, and maximum absolute difference.
   - Identify the angle at which the maximum discrepancy occurs.
   - Check whether discrepancies increase toward large incidence angles or for cross-polarization.

4. **Map the validity of the short-range approximation**
   - At fixed \(	au=0.5\), vary sphere radius over the range used in the paper.
   - At fixed radius, vary \(	au\) from strongly sticky to nearly non-sticky conditions.
   - Compare short-range QCA, DMRT-QMS, and IBA for passive and active cases.
   - Identify parameter combinations that cause nonphysical results, warnings, or solver failure.

5. **Diagnose the source of discrepancies**
   - Save \(k_s\), \(k_a\), effective permittivity, single-scattering albedo, and phase-function information.
   - Compare electromagnetic coefficients before comparing top-of-snow observables.
   - Test DORT convergence with respect to the number of streams.
   - Where possible, prescribe common electromagnetic coefficients to separate the electromagnetic model from the radiative-transfer solver.

### Expected outputs

- Angular curves of \(T_{b,V}\), \(T_{b,H}\), and radar backscatter.
- Error statistics relative to DMRT-ML and DMRT-QMS.
- Radius-stickiness validity map for the short-range approximation.
- Records of numerical warnings and nonphysical cases.
- Attribution of discrepancies to electromagnetic or radiative-transfer components.

---

## 3. Comparison of SMRT to MEMLS-IBA

### Scientific question

**When SMRT and MEMLS use the same exponential microstructure and snowpack properties, how closely do they reproduce the same electromagnetic coefficients and brightness temperatures, and how much of their difference is caused by the IBA absorption formulation versus the DORT and six-flux radiative-transfer solvers?**

### Key steps using SMRT

1. **Create an equivalent exponential-microstructure snowpack**
   - Use a homogeneous snow layer approximately 200 m thick.
   - Set density to 300 kg m\(^{-3}\), temperature to 265 K, and frequency to 37 GHz.
   - Use an exponential correlation length of \(100\,\mu\text{m}\).
   - Evaluate incidence angles from approximately \(10^\circ\) to \(60^\circ\).
   - Match dielectric, boundary, and atmospheric assumptions between SMRT and MEMLS.

2. **Run the required model configurations**
   - Run MEMLS with its IBA exponential-correlation option.
   - Run SMRT using `iba_original` with DORT.
   - Run SMRT using the current/default `iba` implementation with DORT.
   - Use `iba_original` as the closest electromagnetic comparison with the original MEMLS-IBA formulation.

3. **Compare electromagnetic coefficients first**
   - Extract \(k_s\), \(k_a\), extinction coefficient, effective permittivity, and single-scattering albedo.
   - Compare the SMRT and MEMLS coefficients before running the full brightness-temperature comparison.
   - Determine whether differences originate in scattering, absorption, or both.

4. **Compare brightness temperatures**
   - Calculate \(T_{b,V}\) and \(T_{b,H}\) as functions of incidence angle.
   - Calculate bias, RMSD, and maximum absolute difference for each polarization.
   - Compare `iba_original` and default `iba` to quantify the effect of changes in the absorption formulation.
   - Examine whether the difference is angle- or polarization-dependent.

5. **Separate electromagnetic and solver contributions**
   - Test DORT convergence using increasing numbers of streams.
   - Where possible, run DORT with externally supplied MEMLS electromagnetic coefficients.
   - Interpret similar coefficients but different brightness temperatures as a solver-level difference.
   - Interpret differences between `iba_original` and default `iba` primarily as an absorption-formulation effect.

### Expected outputs

- Comparison of electromagnetic coefficients.
- Angular \(T_b\) curves for MEMLS, SMRT `iba_original`, and SMRT default `iba`.
- Polarization-specific error metrics.
- DORT stream-convergence assessment.
- Quantified contributions from absorption and radiative-transfer formulations.

---

## 4. On the Equivalence of Microstructure Models

### Scientific question

**Can sticky hard spheres, scaled non-sticky spheres, and exponential autocorrelation functions be parameterized to produce equivalent microwave brightness temperatures for snow with the same density and specific surface area, and is that equivalence unique and transferable across densities, frequencies, incidence angles, and polarizations?**

### Key steps using SMRT

1. **Define the operational equivalence experiment**
   - Use SMRT IBA with DORT.
   - Create a homogeneous 200 m snow layer at 265 K.
   - Use a reference sphere radius of \(100\,\mu\text{m}\).
   - Test densities of approximately 200, 250, 300, 350, and 400 kg m\(^{-3}\).
   - Initially define equivalence as matching \(T_{b,V}\) at 37 GHz and \(55^\circ\).

2. **Map scaled non-sticky spheres to equivalent stickiness**
   - Generate reference brightness temperatures using nearly non-sticky hard spheres with systematically scaled radii.
   - Return the radius to \(100\,\mu\text{m}\).
   - Numerically solve for the sticky-hard-sphere parameter \(	au\) that reproduces each reference brightness temperature.
   - Use a sufficiently broad search interval and check that the root is bracketed.

3. **Map sticky hard spheres to the exponential microstructure**
   - Generate target brightness temperatures using sticky hard spheres over a prescribed range of \(	au\).
   - Solve for the exponential correlation-length scaling factor \(\phi_{\exp}\).
   - Use the paper's relation

     \[
     l_{\exp}
     =
     \phi_{\exp}\frac{4}{3}
     \left(1-\frac{\rho}{917}\right)a .
     \]

   - Record the solution residual and whether multiple roots exist.

4. **Evaluate uniqueness and density dependence**
   - Repeat both mappings for every tested density.
   - Record all successful roots, missing brackets, and multiple-solution cases.
   - Determine whether a single mapping applies across densities.
   - Assess whether matching density and specific surface area is sufficient to determine microwave-equivalent microstructure.

5. **Test transferability beyond the calibration channel**
   - Re-evaluate matched parameter pairs at additional frequencies and incidence angles.
   - Test H polarization and, where supported, active VV and HH backscatter.
   - Compare \(k_s\), \(k_a\), single-scattering albedo, and phase-function moments.
   - Reject general equivalence when two models agree only at the channel used for calibration.

### Expected outputs

- Equivalent stickiness versus scaled sphere radius.
- Equivalent exponential correlation length versus stickiness.
- Density-dependent equivalence curves.
- Root residuals and uniqueness diagnostics.
- Cross-frequency, angular, polarization, and active/passive transferability tests.

---

## Suggested Agent Execution Order

1. Reproduce the sparse-medium electromagnetic-coefficient experiment.
2. Validate SMRT against DMRT-ML and DMRT-QMS.
3. Validate SMRT IBA against MEMLS-IBA.
4. Reproduce the microstructure-equivalence inversion.
5. Perform cross-configuration tests to distinguish exact reproduction from general physical equivalence.
