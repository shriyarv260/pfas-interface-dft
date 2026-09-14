# Scientific protocol and boundaries

## Define each system before computing

Record PFAS identity and protonation, substrate composition, surface termination, defect and coverage, water/ion content, total cell charge, spin state, cell vectors, frozen atoms, and the electrode-potential reference if relevant. Sampling one conformation is insufficient to characterize the full mechanism. The supplied structures are generated starting conformers, not structures from the authors' supporting information.

Cu(111) is a literature-motivated prototype. Pd(111) is a preparation option motivated by the Pd/TiO2 PFOS study; an isolated Pd slab is not a Pd–TiO2 interface. A top-layer metal vacancy is a proposed screening perturbation, not evidence that vacancies improve degradation. For Ti4O7 [112], obtain a verified bulk/slab geometry and terminations before importing endpoints. Distinguish crystallographic plane indices from the original paper's notation. Do not substitute rutile TiO2 for a Magneli phase.

## Reaction families

| Family | Endpoint bookkeeping | Essential qualification |
|---|---|---|
| C–F cleavage | Retain detached F in the same modeled system; sample surface-bound and solvated products | Bond extension alone does not establish fluoride solvation, yield, or complete mineralization |
| Decarboxylation | Break headgroup C–C; retain CO2 and residual chain with the same atom order | Distinguish PFOA acid, carboxylate, and neutral radical; do not silently remove an electron |
| Desulfonation | Prepare a chemically justified C–S cleavage endpoint retaining S/O atoms | Sulfur products, water, protons, and electrons depend on the mechanism; no universal SO3 product assumption |
| Electron transfer | Specify donor/acceptor, charge states, solvent, and electron chemical potential | A single adiabatic NEB at fixed charge is not an electron-transfer rate or a constant-potential calculation |

PFOA: C8HF15O2 (acid), C8F15O2− (anion). PFOS: C8HF17O3S (acid), C8F17O3S− (anion). A neutral carboxyl radical has different electronic structure from both the acid and closed-shell anion. Removing H from a geometry is not a complete spin/charge specification.

## Electronic structure

The included QE runner is a fixed-charge baseline. All images share settings, pseudopotentials, cell, charge, and atom ordering. QE energy cutoffs and electronic thresholds use **Ry**, whereas ASE reports energy in **eV**, distance in **Å**, and force in **eV/Å**. Do not copy a VASP cutoff in eV into a QE input in Ry. The illustrative PBE settings were chosen for workflow setup; validate cutoffs against the selected pseudopotential recommendations and convergence tests.

For electrochemistry, vacuum alignment of the work function can help characterize a slab, but charged periodic cells require an appropriate electrostatic boundary treatment, solvation/countercharge strategy, and potential calibration. A `tot_charge` sweep alone does not impose a fixed potential. The runner requires an explicit `charge_treatment` description for nonzero charge; this is documentation, not automatic physical validation.

Spin polarization is often essential for radical intermediates and reduced/defective oxides. Provide reviewed initial magnetic moments through the ASE structure or a full atom-length list in configuration; test competing spin states. DFT+U, dispersion corrections, implicit solvent and grand-canonical methods are not supplied as validated presets. The neutral PBE vacuum example should not be reported as aqueous electrocatalysis.

## Convergence plan

Independently converge: bulk lattice parameters; plane-wave/density cutoffs; k-points; slab thickness; lateral adsorbate separation/coverage; vacuum and dipole correction; movable substrate layers; solvent extent/configurations; electronic tolerance; endpoints; number of NEB images; and residual NEB forces. A proposed screening budget is ≤0.02–0.05 eV variation in barrier across final numerical tests, tightened when candidates are close. This is a local protocol proposal, not a published accuracy guarantee.

Relax endpoints to the same force threshold and Hamiltonian as the path. Use IDPP as an initial guess only, inspect collisions and atom mapping, then preconverge NEB before climbing-image optimization. The runner uses separate QE calculators/directories per image. It runs images serially, allowing MPI within each QE invocation. It does not distribute images across separate scheduler jobs.

For the peak image, compute vibrational modes, identify the reaction-associated imaginary mode, and verify downhill connectivity to both minima. Do not dismiss all other imaginary modes as numerical noise without testing. Partial Hessians reduce cost but qualify the result. The helper emits frequencies for review, not a transition-state certificate.

## Energy landscapes and comparisons

For a path with a fixed atom inventory and electronic ensemble:

- Reaction energy: E(final) − E(initial).
- Sampled forward barrier: max E(image) − E(initial).
- Sampled reverse barrier: max E(image) − E(final).

A discrete maximum is not necessarily a converged saddle. The analysis retains whether the maximum is internal and warns about this limitation. Each curve uses its own reactant zero. Do not compare absolute slab total energies across composition, pseudopotentials, electron counts, or solvents.

Compare catalytic barriers only for equivalent elementary steps, state definitions, coverage, environment and potential, reporting uncertainties and sampling. A faster isolated C–F step does not establish a faster full catalytic cycle: adsorption, proton transfer, competing hydrogen evolution, fluoride poisoning, catalyst regeneration, and product desorption can control turnover. For defect formation energies include atomic/electronic reservoirs; deleting an atom and subtracting totals is insufficient.

Free energies need justified zero-point, thermal, entropy, solvent and electrochemical terms. A CHE expression or Eyring rate is deliberately not applied indiscriminately to C–F/electron-transfer reactions. Constant-potential or nonadiabatic ET studies require a separately validated implementation, for example a grand-canonical approach or constrained-DFT/Marcus protocol with appropriate assumptions.
