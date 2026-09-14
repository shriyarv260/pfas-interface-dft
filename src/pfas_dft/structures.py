"""Starting geometries and atom-conserving NEB path preparation."""

import numpy as np
from ase.build import add_adsorbate, fcc111
from ase.constraints import FixAtoms
from ase.io import read, write
from ase.mep import NEB

from .common import new_directory, save_json, sha256


def frozen_indices(atoms):
    indices = []
    for constraint in atoms.constraints:
        if not isinstance(constraint, FixAtoms):
            raise ValueError("Only FixAtoms constraints are supported by this workflow")
        indices.extend(constraint.get_indices().tolist())
    return sorted(set(indices))


def validate_endpoints(initial, final):
    if not np.array_equal(initial.numbers, final.numbers):
        raise ValueError("Endpoints must retain the same atoms in the same order")
    if not np.allclose(initial.cell, final.cell) or not np.array_equal(initial.pbc, final.pbc):
        raise ValueError("Endpoints must have the same cell and periodicity")
    if not np.isfinite(initial.positions).all() or not np.isfinite(final.positions).all():
        raise ValueError("Nonfinite coordinates")
    if frozen_indices(initial) != frozen_indices(final):
        raise ValueError("Endpoint constraints differ")
    fixed = frozen_indices(initial)
    if fixed and not np.allclose(initial.positions[fixed], final.positions[fixed]):
        raise ValueError("Frozen atoms moved between endpoints")
    if not np.allclose(
        initial.get_initial_magnetic_moments(), final.get_initial_magnetic_moments()
    ):
        raise ValueError("Endpoint initial magnetic moments differ")


def build_interface(
    molecule_path, output, metal="Cu", size=(6, 6, 4), vacuum=18.0, height=2.5, vacancy=None
):
    if metal not in {"Cu", "Pd"} or len(size) != 3 or any(x < 1 for x in size):
        raise ValueError("Supported prototype surfaces: Cu(111), Pd(111); positive sizes required")
    if vacuum <= 0 or height <= 0:
        raise ValueError("Positive vacuum and adsorption height required")
    slab = fcc111(metal, size=tuple(size), a={"Cu": 3.615, "Pd": 3.89}[metal], vacuum=vacuum)
    slab.set_pbc((True, True, True))
    if vacancy is not None:
        if vacancy < 0 or vacancy >= len(slab) or slab.get_tags()[vacancy] != 1:
            raise ValueError("Vacancy index must refer to an atom in the top layer")
        del slab[vacancy]
    # ASE surface tags: 1 is top layer; maximum is bottom layer.
    bottom = np.where(slab.get_tags() == max(slab.get_tags()))[0]
    molecule = read(molecule_path)
    molecule.positions -= molecule.positions.mean(axis=0)
    anchor = int(np.argmin(molecule.positions[:, 2]))
    xy = (slab.cell[0, :2] + slab.cell[1, :2]) / 2
    add_adsorbate(slab, molecule, height, position=xy, mol_index=anchor)
    slab.set_constraint(FixAtoms(indices=bottom))
    slab.center(vacuum=vacuum, axis=2)
    slab.info.update(
        provenance="Generated starting guess; no DFT relaxation",
        molecule_sha256=sha256(molecule_path),
    )
    output = new_directory(output)
    write(output / "initial.traj", slab)
    save_json(
        output / "structure.json",
        {
            "status": "unrelaxed_starting_guess",
            "metal": metal,
            "formula": slab.get_chemical_formula(),
            "molecule_sha256": sha256(molecule_path),
            "vacancy_index_before_deletion": vacancy,
            "frozen_indices": bottom.tolist(),
            "adsorbate_indices": list(range(len(slab) - len(molecule), len(slab))),
        },
    )
    return slab


def displaced_endpoint(initial_path, output, indices, shift):
    atoms = read(initial_path)
    if (
        not indices
        or len(indices) != len(set(indices))
        or min(indices) < 0
        or max(indices) >= len(atoms)
    ):
        raise ValueError("Provide unique, valid, zero-based moving atom indices")
    if set(indices) & set(frozen_indices(atoms)):
        raise ValueError("Cannot move frozen substrate atoms")
    if len(shift) != 3 or not np.isfinite(shift).all() or np.linalg.norm(shift) == 0:
        raise ValueError("Provide a finite nonzero three-dimensional displacement")
    atoms.positions[indices] += np.asarray(shift)
    atoms.info["provenance"] = (
        "Displaced product guess; relaxation and chemical inspection required"
    )
    write(output, atoms)
    return atoms


def prepare_neb(initial_path, final_path, output, n_images=7):
    if n_images < 3:
        raise ValueError("At least three total NEB images required")
    initial, final = read(initial_path), read(final_path)
    validate_endpoints(initial, final)
    if np.allclose(initial.positions, final.positions):
        raise ValueError("Reactant and product coordinates are identical")
    images = [initial] + [initial.copy() for _ in range(n_images - 2)] + [final]
    neb = NEB(images, method="improvedtangent")
    neb.interpolate(method="idpp", mic=True, apply_constraint=True)
    output = new_directory(output)
    write(output / "images.traj", images)
    save_json(
        output / "preparation.json",
        {
            "status": "interpolated_not_converged",
            "n_images": n_images,
            "initial_sha256": sha256(initial_path),
            "final_sha256": sha256(final_path),
        },
    )
    return images
