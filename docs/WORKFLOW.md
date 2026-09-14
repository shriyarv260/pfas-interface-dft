# Execution guide

Run commands from the repository root after editable installation. DFT execution requires an external Quantum ESPRESSO installation with its libraries/MPI and valid, compatible pseudopotentials. No DFT engine is bundled. Use paths relative to the shell's working directory; `pseudo_dir` is resolved to an absolute path before the runner creates image directories. The examples use POSIX shells; Windows users may use WSL or adapt activation commands.

## 1. Inputs and audit trail

Read `data/structures/manifest.json` for molecules, charge labels and zero-based atom/bond maps. Regeneration is optional: install `.[geometry]` then run `python scripts/generate_molecules.py`. RDKit version is recorded; version changes may alter geometries. Preserve checksums of the geometries actually used.

`pfas build` places the lowest-z molecular atom above the slab center; this is a geometric guess, not optimized adsorption. Sample orientations/binding sites and inspect periodic-image contacts. `--vacuum 18` adds 18 Å on each side along z. ASE `.traj` retains constraints, unlike many XYZ workflows. `structure.json` records the final global adsorbate indices and the removed top-layer atom index when used. Use the mapping rather than guessing which global F or headgroup atom to move.

To generate a surface defect, first inspect `initial.traj` atom indices and tags, then rebuild with `--vacancy TOP_LAYER_INDEX`. Top-layer substrate atoms have tag 1 and adsorbate atoms tag 0. Freeze indices are rebuilt after deletion. Oxide oxygen vacancies require a reviewed oxide slab and charge/spin treatment prepared outside this simple FCC builder; import its `.traj` directly.

## 2. Choose a physical protocol

Copy `configs/qe.example.json` to a named study config. Choose the actual pseudopotential filenames and directory, cutoff/k-point convergence, XC/dispersion model, charge, spin and environment. Keep all images on the same Hamiltonian. Obtain the QE build/version with `pw.x -h` or the program header and retain it with results. The runner's run manifest stores scientific settings, input hashes, ASE version, and pseudopotential hashes; raw QE output records the engine details.

`pfas write-qe` only serializes inputs and explicitly marks pseudopotentials unverified. `pfas relax` checks actual files, a callable QE command/launcher, and configuration before executing. Atomic forces drive ASE FIRE around successive QE SCF calls, so set `calculation` to `scf`, not `relax` or `vc-relax`.

Spin-polarized runs must carry nonzero initial moments; set them on the structure or pass `initial_magnetic_moments` as a list of length natoms. Choosing a correct electronic state still requires review. The total cell charge is not automatically derived from the adsorbate's formal-charge label.

## 3. Endpoints and reaction hypotheses

For each proposed elementary event, keep the same atoms and ordering. Use `pfas endpoint` to translate explicitly selected fragment indices; it rejects frozen atoms, invalid/duplicate indices and zero displacement. It does not infer chemical products. In decarboxylation the CO2 fragment stays in the cell; in C–F cleavage F stays on the slab or in the solvent. A desulfonation hypothesis must explicitly identify sulfur-containing products.

Relax both endpoints separately. If a product guess returns to the reactant, try a chemically supported alternate endpoint or constrained approach; do not declare a barrier from arbitrary bond stretching. Record the reaction equation and conservation of atoms, charge and spin. For recipes involving external molecules/protons/electrons, build a common closed atom inventory or use a separately justified thermodynamic cycle.

## 4. Path optimization

`pfas prepare-neb` checks atom numbers/order, cell, periodicity, magnetic moments, and frozen coordinates, then performs IDPP interpolation (seven total images by default). Inspect images with `ase gui runs/path/images.traj`. Interpolation may produce collisions or the wrong route; visual review is required.

`pfas neb` recomputes endpoint forces with the selected calculator and refuses unrelaxed endpoints. It preoptimizes a nonclimbing band and then runs CI-NEB. Each image has a unique QE directory and scratch path. The final trajectory, raw image outputs, and `run.json` are retained. Failed/unconverged runs do not produce the successful `energies.csv` export. Re-run into a new directory after fixing the issue; checkpoint resume is not implemented.

Run `pfas analyze` on successful energy CSVs. Record the peak image, then extract it for mode analysis:

```python
from ase.io import read, write
images = read('runs/neb/final_images.traj', index=':')
peak = max(range(len(images)), key=lambda i: images[i].get_potential_energy())
write('runs/peak.traj', images[peak])
```

Use `pfas vibrations --input runs/peak.traj --config YOUR_CONFIG --indices MOBILE_INDICES ... --output runs/modes`. The finite-difference frequency output requires mode inspection. Include all relevant mobile atoms or explicitly report a partial Hessian.

## 5. Compare and validate

The empty `data/templates/screening.csv` is the results inventory. Populate it only from actual paths with the corresponding metadata, convergence and TS evidence. Compare the same reaction/environment across surfaces, report sampling spread, and do not infer complete remediation from one low barrier. Source values in `data/literature/` remain separate from computed results.

Add genuinely matching benchmark predictions and run the validation CLI. Status `not_validated` and exit code 2 are expected until the predefined completeness, independence and tolerance requirements are met. Never copy reference energies into predictions to make the gate pass.

## Storage and compute

Production solvated slabs and NEB are HPC tasks; cost scales with system size, electronic complexity, images and optimization steps. The repository makes no runtime estimate without a pilot. `hpc/neb.slurm` is a configurable template with account/partition settings left to the cluster. Test the MPI invocation and avoid oversubscribing ranks across images.

Large wavefunctions, proprietary potentials and scratch files are gitignored. Store raw results in an appropriate research archive and link checksums and access instructions in the repository. Distinguish reproducibility (same model) from validation against experiment or higher-level theory.
