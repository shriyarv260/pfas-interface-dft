from pathlib import Path

import numpy as np
import pytest
from ase import Atoms
from ase.constraints import FixAtoms
from ase.io import read, write

from pfas_dft.structures import build_interface, displaced_endpoint, prepare_neb, validate_endpoints

ROOT = Path(__file__).resolve().parents[1]


def test_formula_and_charge_records():
    from pfas_dft.common import load_json, sha256

    manifest = load_json(ROOT / "data/structures/manifest.json")
    for record in manifest:
        path = ROOT / "data/structures" / record["file"]
        atoms = read(path)
        symbols = atoms.get_chemical_symbols()
        assert symbols.count("C") == 8
        assert symbols.count("F") == (15 if record["name"].startswith("pfoa") else 17)
        assert atoms.info["formal_charge"] == record["formal_charge"]
        assert sha256(path) == record["sha256"]


def test_build_and_vacancy(tmp_path):
    mol = ROOT / "data/structures/pfoa_acid.xyz"
    clean = build_interface(mol, tmp_path / "clean", size=(4, 4, 3))
    top = int(np.where(clean.get_tags() == 1)[0][0])
    defect = build_interface(mol, tmp_path / "defect", size=(4, 4, 3), vacancy=top)
    assert len(defect) == len(clean) - 1
    assert len(clean.constraints[0].get_indices()) == 16
    assert np.all(clean.pbc)
    with pytest.raises(ValueError):
        build_interface(mol, tmp_path / "bad", vacancy=0)


def endpoints():
    a = Atoms("CuF", positions=[[0, 0, 0], [1, 0, 2]], cell=[8, 8, 12], pbc=True)
    a.set_constraint(FixAtoms(indices=[0]))
    b = a.copy()
    b.positions[1] += [0.5, 0, 0]
    return a, b


def test_atom_inventory_and_cell_checks():
    a, b = endpoints()
    validate_endpoints(a, b)
    b[1].symbol = "O"
    with pytest.raises(ValueError):
        validate_endpoints(a, b)
    a, b = endpoints()
    b.cell[0, 0] = 9
    with pytest.raises(ValueError):
        validate_endpoints(a, b)
    a, b = endpoints()
    b.positions[0, 0] = 0.1
    with pytest.raises(ValueError):
        validate_endpoints(a, b)


def test_path_and_atom_preserving_displacement(tmp_path):
    a, b = endpoints()
    write(tmp_path / "a.traj", a)
    write(tmp_path / "b.traj", b)
    shifted = displaced_endpoint(tmp_path / "a.traj", tmp_path / "guess.traj", [1], [0.5, 0, 0])
    assert np.array_equal(a.numbers, shifted.numbers)
    images = prepare_neb(tmp_path / "a.traj", tmp_path / "b.traj", tmp_path / "path", 5)
    assert len(images) == 5
    assert all(np.allclose(x.positions[0], a.positions[0]) for x in images)
    with pytest.raises(ValueError):
        displaced_endpoint(tmp_path / "a.traj", tmp_path / "bad.traj", [0], [1, 0, 0])


def test_identical_endpoints_rejected(tmp_path):
    a, _ = endpoints()
    write(tmp_path / "a.traj", a)
    with pytest.raises(ValueError, match="identical"):
        prepare_neb(tmp_path / "a.traj", tmp_path / "a.traj", tmp_path / "same")
