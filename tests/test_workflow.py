from pathlib import Path

import numpy as np
import pytest
from ase import Atoms
from ase.io import read, write

from pfas_dft.common import load_json
from pfas_dft.dft import validate_config, write_qe_template
from pfas_dft.toy import DoubleWell, run_demo

ROOT = Path(__file__).resolve().parents[1]


def test_analytic_forces_against_finite_difference():
    atom = Atoms("H", positions=[[0.33, 0.17, 0.25]], calculator=DoubleWell())
    forces = atom.get_forces().copy()
    for axis in range(3):
        atom.positions[0, axis] += 1e-6
        plus = atom.get_potential_energy()
        atom.positions[0, axis] -= 2e-6
        minus = atom.get_potential_energy()
        atom.positions[0, axis] += 1e-6
        assert forces[0, axis] == pytest.approx(-(plus - minus) / 2e-6, abs=1e-7)


def test_end_to_end_analytic_neb(tmp_path):
    report = run_demo(tmp_path / "demo")[0]
    assert report["sampled_forward_barrier_ev"] == pytest.approx(1, abs=0.002)
    assert report["reaction_energy_ev"] == pytest.approx(0, abs=1e-10)
    assert (tmp_path / "demo/landscape.png").stat().st_size > 1000
    assert report["status"] == "synthetic"
    with pytest.raises(FileExistsError):
        run_demo(tmp_path / "demo")


def test_qe_template_round_trip(tmp_path):
    cfg = load_json(ROOT / "configs/qe.example.json")
    src = ROOT / "data/structures/pfoa_acid.xyz"
    atom = read(src)
    atom.center(vacuum=12)
    atom.pbc = True
    write(tmp_path / "input.traj", atom)
    write_qe_template(tmp_path / "input.traj", cfg, tmp_path / "qe")
    restored = read(tmp_path / "qe/pw.in", format="espresso-in")
    assert np.array_equal(atom.numbers, restored.numbers)
    assert np.allclose(atom.positions, restored.positions)
    assert load_json(tmp_path / "qe/status.json")["pseudopotentials_verified"] is False


@pytest.mark.parametrize("mutate", ["charge", "cutoff", "ensemble", "kpts", "force"])
def test_invalid_qe_configs(tmp_path, mutate):
    cfg = load_json(ROOT / "configs/qe.example.json")
    atom = Atoms("H")
    if mutate == "charge":
        cfg["input_data"]["system"]["tot_charge"] = -1
        cfg["charge_treatment"] = ""
    elif mutate == "cutoff":
        cfg["input_data"]["system"]["ecutwfc"] = -2
    elif mutate == "ensemble":
        cfg["ensemble"] = "constant_potential"
    elif mutate == "kpts":
        cfg["kpts"] = [0, 2, 1]
    else:
        cfg["fmax_ev_per_angstrom"] = 0
    with pytest.raises(ValueError):
        validate_config(cfg, atom, require_files=False)


def test_production_runner_orchestration_with_analytic_calculator(tmp_path, monkeypatch):
    # Tests orchestration, not QE physics; external engine is intentionally substituted.
    import pfas_dft.dft as dft

    monkeypatch.setattr(dft, "validate_config", lambda *a, **k: None)
    monkeypatch.setattr(dft, "calculator", lambda *a, **k: DoubleWell())
    monkeypatch.setattr(dft, "provenance", lambda *a, **k: {"method_id": "analytic-fixture"})
    config = load_json(ROOT / "configs/qe.example.json")
    config["fmax_ev_per_angstrom"] = 0.005
    atom = Atoms("H", positions=[[-0.8, 0.05, 0]])
    write(tmp_path / "guess.traj", atom)
    relaxed = dft.relax(tmp_path / "guess.traj", config, tmp_path / "relax")
    assert relaxed["converged"]
    images = [Atoms("H", positions=[[x, 0, 0]]) for x in np.linspace(-1, 1, 7)]
    write(tmp_path / "path.traj", images)
    result = dft.run_neb(tmp_path / "path.traj", config, tmp_path / "neb")
    assert result["converged"]
    assert (tmp_path / "neb/energies.csv").is_file()
    # Deliberately bad endpoint must be refused under the same calculator.
    images[0].positions[0, 0] = -0.5
    write(tmp_path / "bad.traj", images)
    with pytest.raises(ValueError):
        dft.run_neb(tmp_path / "bad.traj", config, tmp_path / "bad")
    assert load_json(tmp_path / "bad/run.json")["status"] == "failed"
